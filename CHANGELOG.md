# CHANGELOG — the-saboteur (Tier 2: The Saboteur)

CHANGELOG.md — build history for The Saboteur, latest entry at top.

## [v0.1.0] — Initial fault-injection run

### Good
- Built `mutations.py` with 12 threat types.
- Verified the mutation engine works: `duplicate_line` correctly adds
  one line to `scratch/ledger.jsonl` (124 → 125).
- Confirmed `ledger.py verify` exits 1 on a corrupted ledger when run
  from the correct directory.

### Bad
- No real silent pass found yet. The Saboteur has not yet proven any
  guard in the tools is weak.

### Ugly
- **First false alarm.** Initial run appeared to show `ledger.py verify`
  exiting 0 while printing "1 entries FAILED." That would have been a
  silent pass — the win condition of the challenge. It turned out to be
  a Saboteur bug: the harness ran `ledger.py` from the repo root (where
  the real `ledger.jsonl` lives) instead of from the scratch directory
  (where the mutated ledger lives). The tool correctly verified the
  real ledger and exited 0.
- **Lesson:** The Saboteur must run tools from inside the scratch
  directory. If it doesn't, every threat will silently pass because
  the tool reads the clean original.
- **Second lesson:** `/tmp` is not writable in Termux. All test
  output must go to a file inside the repo or be piped directly.
