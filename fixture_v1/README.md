# fixture_v1

fixture_v1/README.md — the small Legacy world the Saboteur 1.0.0 attacks.

Function:
    fixture_v0_5/ (archive/0.9.0) byte for byte, not rebuilt
    (CONSOLIDATION_V1.md §7.6): the same throwaway keys, the same
    signatures. Made by the Legacy's own layers, signed by two throwaway
    Ed25519 keys (owner and attester); only their public did:keys are
    kept, in keys/. The one change is the check tool's name.

    legacy_check_v1.py asks each file's layer about it (SPEC_V1.md §3):

        python legacy_check_v1.py            # 17 checks, exit 0 when clean
        python legacy_check_v1.py --layer hal_v2

    The Saboteur never touches this folder; it attacks a scratch copy.
    Rebuild with `python build_fixture_v1.py --force` only when a layer's
    format changes: every signature changes.
