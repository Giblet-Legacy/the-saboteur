# threats_v0_7

threats_v0_7/README.md — the 400 threats saboteur_v0_7.py runs by default.

Function:
    One JSON file per attack on fixture_v0_5/ (SPEC_V0_7.md §2). Each runs
    `python legacy_check_v0_5.py --layer <layer>` and passes only when a
    new line names that layer saying no to that file
    (`failed <file>: <layer>.<call>`).

    001–200 are threats_v0_6/ copied byte for byte (see its README).
    201–400 are new:

    - 201–268, signature type confusion: sign_v2 capsule, freeze_v2,
      record_v2, hal_v2 and the sign_v2 sidecar.
    - 269–303, ledger type confusion: ledger_v2, canon_verify_v2,
      genesis_v3.
    - 304–315, store_v2_1.
    - 316–328, substrate_v4.
    - 329–350, hal_v2 fields.
    - 351–365, sign_v2 capsule fields.
    - 366–375, freeze_v2 fields.
    - 376–383, record_v2 fields.
    - 384–400, sign_v2 documents and sidecars.

    A new attack is a new file; the mutations it can name are in
    mutations_v0_5.py.
