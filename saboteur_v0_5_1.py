"""
saboteur_v0_5_1.py — The Saboteur 0.5.1: 0.5.0 with a lock, so two runs cannot clash

Function:
    The layer over saboteur_v0_5.py (SPEC_V0_5_1.md); nothing frozen is
    edited. James, 2026-11-20: "add lock for clashes". Every run shares
    one scratch folder (<parent>/run), so two runs at once wipe each
    other's copy and report false SKIPs and UGLYs (seen 2026-11-20).

    Before the run, a lock file <parent>/saboteur.lock is created with
    O_CREAT|O_EXCL and holds this process's pid and start time. A second
    run that finds it refuses with exit 2 and names the holder. A lock
    whose pid is no longer running (a run killed hard) is stale and is
    taken over. The lock is removed when the run ends, however it ends,
    but only if it is still this run's.

    The arguments are 0.5.0's, passed through unchanged:

    python saboteur_v0_5_1.py [--target fixture_v0_5] [--threats threats_v0_5] [--parent DIR] [--only NNN]

    Only runs through 0.5.1 take the lock. A frozen runner (v2, 0.4.0,
    0.5.0) started at the same time still clashes.

Public API:
    1. acquire(parent) -> pathlib.Path   (the lock; raises Locked)
    2. release(lock) -> bool
    3. main(argv=None) -> int

Internal helpers:
    4. _alive(pid) -> bool
    5. _read(lock) -> dict | None
    6. Locked — another run holds the lock

Tier:     Tier 2 — The Saboteur, 0.5.1
Depends:  saboteur_v0_5.py, harness_guard_v2.py
Spec:     SPEC_V0_5_1.md 0.5.1
Version:  0.5.1-dev
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import datetime
import json
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_guard_v2 as guard  # noqa: E402
import saboteur_v0_5  # noqa: E402

LOCK_NAME = "saboteur.lock"
# A lock with no readable pid is trusted as held for this long (it may be
# mid-write); after that it is stale.
UNREADABLE_GRACE_S = 60


# ---------------------------------------------------------------------------
# 6. Locked
# ---------------------------------------------------------------------------
class Locked(Exception):
    """Another Saboteur run holds the lock."""


# ---------------------------------------------------------------------------
# 4. _alive
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
# 5. _read
# ---------------------------------------------------------------------------
def _read(lock):
    try:
        data = json.loads(pathlib.Path(lock).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and isinstance(data.get("pid"), int) else None


# ---------------------------------------------------------------------------
# 1. acquire
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
# 2. release
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
# 3. main
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
        return saboteur_v0_5.main(argv)
    finally:
        release(lock)


if __name__ == "__main__":
    sys.exit(main())
