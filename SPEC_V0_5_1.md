# SPEC V0.5.1 — the-saboteur (Tier 2: The Saboteur), the run lock

SPEC_V0_5_1.md — what saboteur_v0_5_1.py adds over the frozen 0.5.0.

Function:
    James, 2026-11-20: "add lock for clashes". SPEC_V0_5.md stays
    authoritative for the run (target, tool, mutations, threats);
    SPEC_V2.md for the harness. Nothing frozen is edited.

Tier:      Tier 2 — The Saboteur
Depends:   saboteur_v0_5.py, harness_guard_v2.py (unchanged)
Version:   SPEC V0.5.1 0.5.1-dev
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. The clash (red, 2026-11-20)

Every run makes its scratch copy in the same folder, `<parent>/run`
(by default `%TEMP%\forge-saboteur\run`). Each threat wipes that folder
and copies the target in again. Two runs at once wipe each other's copy:

- James's run, overlapping one of the AI's: [31] SKIP "target file
  missing: ledger.jsonl" and [39] UGLY "can't open legacy_check_v0_5.py".
  Both were false.
- Reproduced with two 0.5.0 runs started 2 seconds apart:
  - one finished with a false SKIP on 002, "target file missing";
  - the other crashed with a PermissionError (WinError 32) on the
    scratch folder.

Nothing in the output says a second run caused it.

## 2. saboteur_v0_5_1.py

    python saboteur_v0_5_1.py [--target fixture_v0_5] [--threats threats_v0_5] [--parent DIR] [--only NNN]

The arguments are 0.5.0's, passed through unchanged.

1. **Taking the lock:** before anything else, the run creates
   `<parent>/saboteur.lock` with O_CREAT|O_EXCL. Only one process can
   create it. It holds `{"pid": ..., "started": ...}`.
2. **A run already going:** if the lock exists and its pid is running,
   the new run refuses: `refused: another Saboteur run (pid N, started
   T) holds <lock>; run one at a time`. It exits 2 and touches nothing.
3. **A stale lock:** if the lock's pid is not running (a run killed
   hard), the lock is removed and taken.
4. **An unreadable lock:** a lock with no readable pid may be
   mid-write, so it counts as held. Once it is older than 60 seconds it
   counts as stale.
5. **Releasing:** when the run ends, however it ends, the lock is
   removed, but only if it still names this process.

**Checking the pid:** on Windows the check is OpenProcess and
GetExitCodeProcess, never `os.kill`, which ends the process there. On
POSIX (the VPS, Termux) it is `os.kill(pid, 0)`.

**Limits:**

- Only runs through 0.5.1 take the lock. A frozen runner (v2, 0.4.0,
  0.5.0) started alongside still clashes.
- Two runs that both find the same stale lock in the same instant could
  both take it. That needs a crashed run and two new starts within
  milliseconds.
- A pid reused by an unrelated process keeps a stale lock held. The
  refusal names the lock file, so it can be deleted by hand.

## 3. Tests

`tests/test_saboteur_v0_5_1.py` has 9 tests:

- the pid check;
- refusal while a live process holds the lock;
- taking over a stale lock;
- unreadable locks, fresh and old;
- release when the run raises;
- not removing another run's lock;
- an end-to-end run;
- two real runs started together: the second is refused and the first
  gives PASS 9.

---

## Document control

- **SPEC V0.5.1 0.5.1-dev**: 2026-11-20, by the VS Code AI on James's
  "add lock for clashes".
