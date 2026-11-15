# CHANGELOG — the-saboteur (Tier 2: The Saboteur)

CHANGELOG.md — build history for The Saboteur, latest entry at top.

## [v0.2.0] — Real silent pass found in hal.py

### Good
- Ran the full 12-threat suite against the-full-stack.
- 11 threats PASS. 0 FAIL. 1 UGLY (which turned out to be a real silent pass).
- Found a genuine silent pass in `hal.py seal`.
- Fixed `freeze.py --check` (which didn't exist) by building `freeze_v2.py`.

### Bad
- The Saboteur's exit-code detection was too lenient. When `hal.py seal`
  printed `FAILED` but exited 0, it was logged as UGLY, not FAIL. The
  harness must treat any non-zero exit code as a FAIL when the tool
  prints a failure message.
- The threat 10 spec was calling `verify-score` (a subcommand that
  doesn't exist). Corrected to call `seal` with real arguments.

### Ugly
- **BUG FOUND (Target: `the-full-stack/hal.py`):**
  Mutation 11 (wrong-key signature) — actually the *baseline* test,
  which uses the wrong signature already. Wait, let me re-check.
  The original run was against `verify-score` (bad command). When we
  manually ran `hal.py seal` with a wrong signature, it printed
  `FAILED  authoriser score file signature is invalid` and then
  exited **0**.
  The tool detects the failure, prints it clearly, and then proceeds
  as if it succeeded. An automated pipeline calling `hal.py seal`
  would believe a seal was created when it wasn't.
  - **Fix needed:** `hal.py seal` must exit non-zero when the
    signature check fails.
