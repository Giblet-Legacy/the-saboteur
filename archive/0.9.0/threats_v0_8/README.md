# threats_v0_8

threats_v0_8/README.md — the 800 threats saboteur_v0_8.py runs by default.

Function:
    One JSON file per attack on fixture_v0_5/ (SPEC_V0_8.md §3). Each runs
    `python legacy_check_v0_5.py --layer <layer>` and passes only when a
    new line names that layer saying no to that file.

    001–400 are threats_v0_7/ copied byte for byte. 401–800 are new:

    - 401–418, substitution (copy_sibling);
    - 419–511, signature type confusion on the files 0.7.0 left alone;
    - 512–800, the field matrix (every signed field set to null, 0, [],
      {}, "" and true).

    The mutations they name are in mutations_v0_8.py.
