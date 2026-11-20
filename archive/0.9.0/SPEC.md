# SPEC — the-saboteur (Tier 2: The Saboteur)

SPEC.md — specification for The Saboteur's design and execution plan.

## What it does
Applies one mutation at a time to a scratch copy of a target repo,
runs the real tool against it, and reports whether the tool failed
loudly. Two silent passes are already recorded in the-full-stack's
CHANGELOG as the Saboteur's first findings.

## Harness discipline (step 0, PROVEN)
The Saboteur is only as honest as its harness. Before any threat runs,
five guards must pass:
1. Clean baseline — every tool exits 0 on an unmutated clone.
2. Silent canary — a tool that exits 0 must be judged FAIL.
3. Loud canary — a tool that exits 1 with a named error must be judged PASS.
4. Vague canary — a tool that exits 1 vaguely must be judged UGLY.
5. Scratch marker — the scratch path must contain .saboteur-scratch.

Any failure aborts with exit 2. Exit 1 means a threat failed. Exit 0
means everything passed and the harness was proven.

## Status
- [x] Harness guard built (`harness_guard.py`)
- [x] Three canaries built (`harness_canaries/`)
- [x] Five breakages proven in `tests/test_harness_guard.py` (5/5 pass)
- [ ] `saboteur.py` CLI wrapper
- [ ] 21 threats executed end-to-end
- [ ] `ledger_core.py` + `ledger_v2.py`
- [ ] `hal_core.py` + `hal_v2.py`
- [ ] `freeze_v2.py` audit against strict-default register
- [ ] Governance v4 (event taxonomy)
- [ ] Principle capsule (`strict-default`)
- [ ] Consumer audit (the-legacy direct calls to hal/ledger)
- [ ] L3 — Node verifier for forge-c14n-1
