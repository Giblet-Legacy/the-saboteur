# fixture_v0_5

fixture_v0_5/README.md — the small Legacy world the Saboteur 0.5.0 attacks.

Function:
    Made by build_fixture_v0_5.py with the Legacy's own layers, signed by
    two throwaway keys whose private halves were never written. keys/ holds
    only their public did:keys. manifest.json lists every checked file.
    legacy_check_v0_5.py asks each file's layer about it (SPEC_V0_5.md §3):

        python legacy_check_v0_5.py            # 17 checks, exit 0 when clean
        python legacy_check_v0_5.py --layer hal_v2

    Never hand-edit the signed files: the Saboteur's baseline is that this
    folder is clean. Rebuild with `python build_fixture_v0_5.py --force`
    (new keys) only when a layer's format changes.
