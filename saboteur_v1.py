"""
saboteur_v1.py — The Saboteur 1.0.0: prove every Legacy layer says no, by name

Function:
    The 1.0.0 consolidation (CONSOLIDATION_V1.md) of the 0.9.0 chain
    saboteur_v0_9 -> v0_7 -> v0_6 -> v0_5_1 -> v0_5 -> saboteur_v2
    (archive/0.9.0), in one module with no module swapped at run time.
    It does exactly what `python saboteur_v0_9.py` did:

      1. take the run lock, <parent>/saboteur.lock (0.5.1): a second run
         refuses with exit 2 and names the holder; a lock whose process
         is gone is taken over; the lock is released however the run ends;
      2. refuse a target folder named after the reference-only repo,
         exit 2 (0.4.0);
      3. point FORGE_LEGACY_ROOT at the-saboteur's parent unless set, so
         the scratch copy finds the Legacy layers (0.5.0);
      4. run v2's harness: guard, five canaries, then for each threat a
         clean baseline run, one mutation (mutations_v1), a second run,
         and harness_guard_v1.judge; the real target is hashed before and
         after (SPEC_V2.md).

    Exit codes: 0 every threat passed; 1 any FAIL, UGLY or SKIP; 2 the
    harness is invalid, the lock is held, or the target is refused. The
    banner still reads "THE SABOTEUR v2", as 0.9.0's did: 1.0.0 changes no
    output.

    python saboteur_v1.py [--target fixture_v1] [--threats threats_v1] [--parent DIR] [--only NNNN]

Public API:
    1. load_threats(directory) -> [threat]
    2. run_threat(threat, target, parent) -> (verdict, reason, detail)
    3. acquire(parent) -> Path   (raises Locked)
    4. release(lock) -> bool
    5. main(argv=None) -> int

Internal helpers:
    6. _command  — a threat's tool string as an argv for this interpreter
    7. _run      — run the tool from the scratch, throwaway key, timeout
    8. _key_file — write a throwaway raw Ed25519 key into the scratch
    9. _alive, _read, Locked — the lock's process check, reader and error
    10. _run_all — steps 2-4 above, without the lock

Tier:     Tier 2 — The Saboteur, 1.0.0
Depends:  harness_guard_v1.py, mutations_v1.py, harness_canaries/,
          fixture_v1/ (default target), threats_v1/ (default threats)
Spec:     SPEC_V1.md 1.0.0
Version:  1.0.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import datetime
import json
import os
import pathlib
import shlex
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_guard_v1 as guard  # noqa: E402
import mutations_v1 as mutations  # noqa: E402

DEFAULT_TARGET = HERE / "fixture_v1"
DEFAULT_THREATS = HERE / "threats_v1"
TIMEOUT = 120
_REFERENCE_ONLY = "the-full-stack"
LOCK_NAME = "saboteur.lock"
# A lock with no readable pid is trusted as held for this long (it may be
# mid-write); after that it is stale.
UNREADABLE_GRACE_S = 60


# ---------------------------------------------------------------------------
# 1. load_threats
# ---------------------------------------------------------------------------
def load_threats(directory):
    out = []
    for path in sorted(pathlib.Path(directory).glob("*.json")):
        threat = json.loads(path.read_text(encoding="utf-8"))
        threat["_file"] = path.name
        for key in ("name", "target_file", "mutation", "tool"):
            if not isinstance(threat.get(key), str) or not threat[key].strip():
                raise guard.HarnessInvalid(f"{path.name}: missing or empty {key!r}")
        out.append(threat)
    return out

# ---------------------------------------------------------------------------
# 6. _command
# ---------------------------------------------------------------------------
def _command(tool):
    argv = shlex.split(tool, posix=True)
    if argv and argv[0] in ("python", "python3"):
        argv[0] = sys.executable
    return argv

# ---------------------------------------------------------------------------
# 8. _key_file
# ---------------------------------------------------------------------------
def _key_file(scratch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    path = pathlib.Path(scratch) / "_saboteur_throwaway.key"
    path.write_bytes(Ed25519PrivateKey.generate().private_bytes(
        serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()))
    return path

# ---------------------------------------------------------------------------
# 7. _run
# ---------------------------------------------------------------------------
def _run(tool, scratch, key):
    guard.per_invocation(scratch, scratch)
    env = dict(os.environ, FORGE_KEY_PATH=str(key), PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    try:
        r = subprocess.run(_command(tool), cwd=str(scratch), env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return None, "", f"timed out after {TIMEOUT}s"
    except OSError as e:
        return None, "", f"could not start: {e}"
    return r.returncode, r.stdout, r.stderr

# ---------------------------------------------------------------------------
# 2. run_threat
#    Clean copy -> baseline run -> one mutation -> run -> judge.
# ---------------------------------------------------------------------------
def run_threat(threat, target, parent):
    scratch = guard.init_scratch(pathlib.Path(parent) / "run", target, parent)
    key = _key_file(scratch)
    base_rc, base_out, base_err = _run(threat["tool"], scratch, key)
    if base_rc is None:
        return "SKIP", f"baseline did not run: {base_err}", {}
    baseline = None if base_rc == 0 else guard._lines(base_out + "\n" + base_err)
    victim = scratch / threat["target_file"]
    if not victim.exists() and threat["mutation"] != "delete":
        return "SKIP", f"target file missing: {threat['target_file']}", {}
    if threat["mutation"] == "delete" and not victim.exists():
        return "SKIP", f"nothing to delete: {threat['target_file']}", {}
    try:
        mutations.apply_mutation(str(victim), threat["mutation"])
    except Exception as e:  # a mutation that cannot apply is reported, not hidden
        return "SKIP", f"mutation {threat['mutation']} could not apply: {e}", {}
    rc, out, err = _run(threat["tool"], scratch, key)
    if rc is None:
        return "UGLY", f"tool did not finish: {err}", {}
    verdict, reason = guard.judge(rc, out, err, threat.get("expect_error_contains"), baseline)
    new = [ln for ln in guard._lines(out + "\n" + err) if baseline is None or ln not in set(baseline)]
    return verdict, reason, {"baseline_rc": base_rc, "rc": rc, "new_lines": new[:6]}

# ---------------------------------------------------------------------------
# 9. Locked
# ---------------------------------------------------------------------------
class Locked(Exception):
    """Another Saboteur run holds the lock."""

# ---------------------------------------------------------------------------
# 9. _alive
#    Is a process with this pid running? Never os.kill on Windows: there
#    any signal but CTRL_C/CTRL_BREAK terminates the process.
# ---------------------------------------------------------------------------
def _alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.restype = ctypes.c_void_p
        handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ctypes.get_last_error() == 5  # access denied: it exists
        try:
            code = ctypes.c_ulong()
            if not k32.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code)):
                return True
            return code.value == 259  # STILL_ACTIVE
        finally:
            k32.CloseHandle(ctypes.c_void_p(handle))
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True

# ---------------------------------------------------------------------------
# 9. _read
# ---------------------------------------------------------------------------
def _read(lock):
    try:
        data = json.loads(pathlib.Path(lock).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and isinstance(data.get("pid"), int) else None

# ---------------------------------------------------------------------------
# 3. acquire
# ---------------------------------------------------------------------------
def acquire(parent):
    parent = pathlib.Path(parent)
    parent.mkdir(parents=True, exist_ok=True)
    lock = parent / LOCK_NAME
    for _ in range(2):  # once, and once more after clearing a stale lock
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            held = _read(lock)
            if held is not None and _alive(held["pid"]):
                raise Locked(f"another Saboteur run (pid {held['pid']}, started {held.get('started', '?')}) "
                             f"holds {lock}; run one at a time")
            if held is None:
                try:
                    age = time.time() - lock.stat().st_mtime
                except OSError:
                    continue  # gone already: try again
                if age < UNREADABLE_GRACE_S:
                    raise Locked(f"{lock} is being written by another run; run one at a time")
            try:
                lock.unlink()  # stale: its run is no longer going
            except FileNotFoundError:
                pass
            continue
        started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"pid": os.getpid(), "started": started}) + "\n")
        return lock
    raise Locked(f"could not take {lock}; another run keeps replacing it")

# ---------------------------------------------------------------------------
# 4. release
#    Remove the lock only if it is still this process's.
# ---------------------------------------------------------------------------
def release(lock):
    held = _read(lock)
    if held is None or held["pid"] != os.getpid():
        return False
    try:
        pathlib.Path(lock).unlink()
    except FileNotFoundError:
        return False
    return True

# ---------------------------------------------------------------------------
# 10. _run_all
#     0.5.0's refusal and defaults, then v2's main, as one parse.
# ---------------------------------------------------------------------------
def _run_all(argv=None):
    p = argparse.ArgumentParser(description="The Saboteur 1.0.0: prove every Legacy layer says no, by name.")
    p.add_argument("--target", default=str(DEFAULT_TARGET), help="folder to attack (a scratch copy is used)")
    p.add_argument("--threats", default=str(DEFAULT_THREATS), help="directory of threat JSON files")
    p.add_argument("--parent", default=str(guard.DEFAULT_PARENT), help="where scratch copies are made")
    p.add_argument("--only", help="run only threats whose file name starts with this")
    args = p.parse_args(argv)
    if pathlib.Path(args.target).resolve().name == _REFERENCE_ONLY:
        print(f"refused: {_REFERENCE_ONLY} is reference only, not a Legacy layer (SPEC_V0_4 section 1)", file=sys.stderr)
        return 2
    os.environ.setdefault("FORGE_LEGACY_ROOT", str(HERE.parent))
    target = pathlib.Path(args.target).resolve()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        if not target.is_dir():
            raise guard.HarnessInvalid(f"target is not a directory: {target}")
        threats = [t for t in load_threats(args.threats) if not args.only or t["_file"].startswith(args.only)]
        if not threats:
            raise guard.HarnessInvalid("no threats to run")
        initial = guard.pre_run(pathlib.Path(args.parent) / "run", target, args.parent)
        print(f"THE SABOTEUR v2: {len(threats)} threats against {target.name} (harness proven: 5 canaries)\n")
        counts, problems = {"PASS": 0, "FAIL": 0, "UGLY": 0, "SKIP": 0}, []
        for i, t in enumerate(threats, 1):
            verdict, reason, detail = run_threat(t, target, args.parent)
            counts[verdict] += 1
            print(f"[{i:02d}/{len(threats)}] {verdict:<4}  {t['name']}\n          {reason}")
            if detail.get("new_lines") and verdict != "PASS":
                print(f"          new output: {detail['new_lines'][:2]}")
            if verdict != "PASS":
                problems.append((t["_file"], verdict, reason))
        guard.post_run(target, initial)
    except guard.HarnessInvalid as e:
        print(f"HARNESS INVALID: {e}", file=sys.stderr)
        return 2
    print(f"\nPASS {counts['PASS']}  FAIL {counts['FAIL']}  UGLY {counts['UGLY']}  SKIP {counts['SKIP']}"
          "  (real repo unchanged)")
    for f, v, r in problems:
        print(f"  {v:<4} {f}: {r}")
    return 0 if not problems else 1


# ---------------------------------------------------------------------------
# 5. main
#    The lock first (0.5.1), then the run.
# ---------------------------------------------------------------------------
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--parent", default=str(guard.DEFAULT_PARENT))
    known, _ = p.parse_known_args(argv)
    try:
        lock = acquire(known.parent)
    except Locked as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    try:
        return _run_all(argv)
    finally:
        release(lock)


if __name__ == "__main__":
    sys.exit(main())
