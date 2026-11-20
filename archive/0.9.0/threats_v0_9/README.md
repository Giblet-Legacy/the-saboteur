# threats_v0_9

threats_v0_9/README.md — the 1000 threats saboteur_v0_9.py runs by default.

Function:
    One JSON file per attack on fixture_v0_5/ (SPEC_V0_9.md §3), numbered
    with four digits, 0001–1000. 0001–0800 are threats_v0_8/ with the
    same bytes; only the file names gain a leading 0.

    0801–1000 map the known gaps. Each carries a `gap` field naming its
    class:

    - rollback;
    - dup-key;
    - unsigned-column;
    - deleted-row;
    - non-canonical;
    - substitution.

    The mutations they name are in mutations_v0_9.py.
