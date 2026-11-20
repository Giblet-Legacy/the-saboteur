# threats_v0_5

threats_v0_5/README.md — the 108 threats saboteur_v0_5.py runs by default.

Function:
    One JSON file per attack on fixture_v0_5/ (SPEC_V0_5.md §5). Each runs
    `python legacy_check_v0_5.py --layer <layer>` and passes only when a
    new line names that layer saying no to that file
    (`failed <file>: <layer>.<call>`). Numbered by layer: 001–022
    ledger_v2, 023–037 canon_verify_v2, 038–040 genesis_v3, 041–050
    store_v2_1, 051–063 sign_v2 capsules, 064–069 freeze_v2, 070–078
    record_v2, 079–090 sign_v2 documents, 091–102 hal_v2, 103–108
    substrate_v4. A new attack is a new file; the mutations it can name
    are in mutations_v0_5.py.
