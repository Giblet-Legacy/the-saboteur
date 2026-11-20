"""
saboteur_v0_9.py — The Saboteur 0.9.0: 1000 threats, the known gaps mapped

Function:
    The layer over saboteur_v0_8.py (SPEC_V0_9.md); nothing earlier is
    edited. James, 2026-11-20: "fill the known gaps to add 200 more to
    bring us to 1000". The run is 0.8.0's with two changes:

      - the default threats are threats_v0_9/: the 800 of threats_v0_8/
        copied unchanged (001-800) and 200 new (801-1000) that map each
        known gap class in full;
      - the mutations are mutations_v0_9 (0.8.0's plus keep_first_lines
        and json_reformat), installed the way 0.8.0 installs its own.

    python saboteur_v0_9.py [--target fixture_v0_5] [--threats threats_v0_9] [--parent DIR] [--only NNN]

Public API:
    1. main(argv=None) -> int

Tier:     Tier 2 — The Saboteur, 0.9.0
Depends:  saboteur_v0_8.py, saboteur_v0_7.py, saboteur_v0_5.py, mutations_v0_9.py
Spec:     SPEC_V0_9.md 0.9.0
Version:  0.9.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import mutations_v0_9  # noqa: E402
import saboteur_v0_5  # noqa: E402
import saboteur_v0_7  # noqa: E402

DEFAULT_THREATS = HERE / "threats_v0_9"


# 1. main
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not any(a == "--threats" or a.startswith("--threats=") for a in argv):
        argv = ["--threats", str(DEFAULT_THREATS)] + argv
    before = saboteur_v0_5.mutations_v0_5
    saboteur_v0_5.mutations_v0_5 = mutations_v0_9
    try:
        return saboteur_v0_7.main(argv)
    finally:
        saboteur_v0_5.mutations_v0_5 = before


if __name__ == "__main__":
    sys.exit(main())
