"""
saboteur_v2.py — Fault-injection harness for the Forge Stack, v2

Function:
    The layer over saboteur.py (SPEC_V2.md §1). v1 is not edited. For
    each threat in threats_v2/*.json: copy the target repo into a guarded
    scratch directory, run the threat's tool on the CLEAN copy (the
    baseline), apply the one mutation, run the tool again, and judge the
    difference with harness_guard_v2.judge. The harness is proven first
    (five canaries) and the real repo is hashed before and after.

    What v2 fixes in v1 (2026-11-15 audit):
      - v1 never ran the harness guard, the canaries or the baseline it
        promises (SPEC step 0). Three target tools already fail on a
        clean copy, so 7 of v1's 12 threats passed whatever happened.
      - v1 wiped `scratch/` relative to wherever it was started, with
        no guard, and read its target from a fixed ~/forge path.
      - v1 ran "python" from the shell; v2 runs this interpreter.
      - v1 let tools sign with the owner's key (FORGE_KEY_PATH); v2
        points FORGE_KEY_PATH at a throwaway key inside the scratch.
      - v1 exited 0 with UGLY or SKIP results; v2 exits 1 on any FAIL,
        UGLY or SKIP, 2 when the harness is invalid, 0 only when every
        threat passed.

    python saboteur_v2.py [--target ../the-full-stack] [--threats threats_v2] [--only NN]

Public API:
    1. load_threats(directory) -> [threat]
    2. run_threat(threat, target, parent) -> (verdict, reason, detail)
    3. main(argv=None) -> int

Internal helpers:
    4. _command  — a threat's tool string as an argv for this interpreter
    5. _run      — run the tool from the scratch, throwaway key, timeout
    6. _key_file — write a throwaway raw Ed25519 key into the scratch

Tier:     Tier 2 — The Saboteur, v2
Depends:  harness_guard_v2.py, mutations_v2.py
Spec:     SPEC_V2.md 0.3.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import json
import os
import pathlib
import shlex
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_guard_v2 as guard  # noqa: E402
import mutations_v2 as mutations  # noqa: E402

DEFAULT_TARGET = HERE.parent / "the-full-stack"
DEFAULT_THREATS = HERE / "threats_v2"
TIMEOUT = 120


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
# 4. _command
# ---------------------------------------------------------------------------
def _command(tool):
    argv = shlex.split(tool, posix=True)
    if argv and argv[0] in ("python", "python3"):
        argv[0] = sys.executable
    return argv


# ---------------------------------------------------------------------------
# 6. _key_file
# ---------------------------------------------------------------------------
def _key_file(scratch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    path = pathlib.Path(scratch) / "_saboteur_throwaway.key"
    path.write_bytes(Ed25519PrivateKey.generate().private_bytes(
        serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()))
    return path


# ---------------------------------------------------------------------------
# 5. _run
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
#    Clean copy → baseline run → one mutation → run → judge.
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
# 3. main
# ---------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description="The Saboteur v2: prove every tool fails loudly.")
    p.add_argument("--target", default=str(DEFAULT_TARGET), help="repo to attack (a scratch copy is used)")
    p.add_argument("--threats", default=str(DEFAULT_THREATS), help="directory of threat JSON files")
    p.add_argument("--parent", default=str(guard.DEFAULT_PARENT), help="where scratch copies are made")
    p.add_argument("--only", help="run only threats whose file name starts with this")
    args = p.parse_args(argv)
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


if __name__ == "__main__":
    sys.exit(main())
