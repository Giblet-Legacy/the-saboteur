# threats_v0_6

threats_v0_6/README.md — the 200 threats saboteur_v0_6.py runs by default.

Function:
    One JSON file per attack on fixture_v0_5/ (SPEC_V0_6.md §2). Each runs
    `python legacy_check_v0_5.py --layer <layer>` and passes only when a
    new line names that layer saying no to that file
    (`failed <file>: <layer>.<call>`).

    001–108 are threats_v0_5/ copied byte for byte (see its README).
    109–200 are new, numbered by layer: 109–124 ledger_v2, 125–130
    canon_verify_v2, 131–135 genesis_v3, 136–145 store_v2_1, 146–156
    sign_v2 capsules, 157–164 freeze_v2, 165–172 record_v2, 173–181
    sign_v2 documents, 182–191 hal_v2, 192–198 substrate_v4, 199
    record_v2, 200 hal_v2. A new attack is a new file; the mutations it
    can name are in mutations_v0_5.py.
