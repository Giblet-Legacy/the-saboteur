# CHANGELOG — the-saboteur (Tier 2: The Saboteur)

CHANGELOG.md — build history for The Saboteur, latest entry at top.

## [v0.1.0] — Initial fault-injection run

### Good
- Built `mutations.py` with 12 threat types.
- Built `saboteur.py` harness to run against a scratch copy of a target.
- Found the first silent pass in `the-full-stack`.

### Bad
- (none yet)

### Ugly
- **BUG FOUND (Target: `the-full-stack/ledger.py`):**
  Mutation 12 (`duplicate_line`) duplicated the first line of `ledger.jsonl`.
  The `ledger.py verify` tool printed `FAILED (chain) #00` to stdout,
  but **exited 0** (success).
  This is a silent pass. Any automated pipeline using `ledger.py verify`
  would treat the corrupt ledger as valid.
  - **Fix needed:** `ledger.py verify` must exit non-zero if any entry fails.
