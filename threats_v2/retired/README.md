# Retired threats

Retired 2026-11-15 (James: "retire the old"). Kept, not deleted: each one
is the evidence for a gap in an original the-full-stack tool, which by the
Immutable Rule is never edited.

| Threat | Original tool | Its gap | Same attack, live, on the layer |
|---|---|---|---|
| 03 delete a .sig | `sign.py --verify` | silent pass | 13, `sign_v2.py` |
| 05 truncate the ledger | `ledger.py verify` | traceback | 14, `ledger_v2.py` |
| 09 fractional number | `sign.py --verify` | not named | 16, `sign_v2.py`; 20, `sign_v3.py` |
| 11 stale score | `hal_v2.py seal` | not named | 17, `hal_v3.py` |
| 12 replayed row | `ledger.py verify` | not named | 15, `ledger_v2.py` |

`saboteur_v2.py` loads `threats_v2/*.json` only, so these no longer run.
To see the old gaps again:

    python saboteur_v2.py --target ../the-full-stack --threats threats_v2/retired

Last run (2026-11-15): 03 FAIL, 05/09/11/12 UGLY, as above.
