# SPEC V3 — the-saboteur (Tier 2: The Saboteur), no default target

SPEC_V3.md — what saboteur_v3.py changes over the frozen v2 (0.3.3).

Function:
    James, 2026-11-18: "the forge stack was for reference only and not
    meant to be a layer involved in the legacy program." v2 attacks
    ../the-full-stack by default, and all 15 of its live threats run
    that repository's tools (sign_v3.py, ledger_v2.py, freeze_v3.py,
    hal_v3.py). v3 cuts that tie. SPEC_V2.md stays authoritative where
    this document is silent. v1 and v2 files, threats/ and threats_v2/
    are not edited: they are history.

Tier:      Tier 2 — The Saboteur
Depends:   saboteur_v2.py (its harness, unchanged)
Version:   SPEC V3 0.4.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. saboteur_v3.py

    python saboteur_v3.py --target DIR [--threats threats_v3] [--parent P] [--only NN]

- **`--target` is required.** There is no default target.
- **A target whose folder is named `the-full-stack` is refused**: exit 2
  with "reference only", before any scratch copy is made.
- **Threats default to `threats_v3/`.** No threats yet is an invalid
  harness (exit 2), as in v2.
- Everything else is v2's own code (`load_threats`, `run_threat`, the
  guard, the canaries, the baseline, the exit codes): imported, not
  copied.

## 2. Threats

`threats_v3/` starts empty. Its threats will be written against the
Legacy's own layers (P2 Sign, P3 Freeze, P4 Ledger, P15 HAL, …), one
JSON file per attack. Each must have a clean baseline on that layer
first. That is separate work and will be done when James says.

The 15 threats in `threats_v2/` stay where they are. They record what
was proved against the-full-stack on 2026-11-15 (PASS 15).

## 3. Tests (tests/test_saboteur_v3.py)

`--target` required; the-full-stack refused with nothing made; no
threats is invalid; end to end on a fake target; and the harness is
v2's own objects.

---

## Document control

- **SPEC V3 0.4.0** — 2026-11-18, by the VS Code AI on James's word
  ("yes in the order you stated"). Not frozen.
