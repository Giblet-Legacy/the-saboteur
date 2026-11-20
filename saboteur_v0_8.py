"""
saboteur_v0_8.py — The Saboteur 0.8.0: 800 threats, with substitution attacks

Function:
    The layer over saboteur_v0_7.py (SPEC_V0_8.md); nothing earlier is
    edited. James, 2026-11-20: "400 more" (attacks). The run is 0.7.0's
    (0.5.1's lock, 0.5.0's harness and fixture) with two changes:

      - the default threats are threats_v0_8/: the 400 of threats_v0_7/
        copied unchanged (001-400) and 400 new (401-800);
      - the mutations are mutations_v0_8 (0.5.0's plus copy_sibling and
        text_replace). saboteur_v0_5 installs its mutation module by name
        on each run, so this layer rebinds that name for the run and puts
        it back afterwards.

    python saboteur_v0_8.py [--target fixture_v0_5] [--threats threats_v0_8] [--parent DIR] [--only NNN]

Public API:
    1. main(argv=None) -> int

Tier:     Tier 2 — The Saboteur, 0.8.0
Depends:  saboteur_v0_7.py, saboteur_v0_5.py, mutations_v0_8.py
Spec:     SPEC_V0_8.md 0.8.0
Version:  0.8.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import mutations_v0_8  # noqa: E402
import saboteur_v0_5  # noqa: E402
import saboteur_v0_7  # noqa: E402

DEFAULT_THREATS = HERE / "threats_v0_8"


# 1. main
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not any(a == "--threats" or a.startswith("--threats=") for a in argv):
        argv = ["--threats", str(DEFAULT_THREATS)] + argv
    before = saboteur_v0_5.mutations_v0_5
    saboteur_v0_5.mutations_v0_5 = mutations_v0_8
    try:
        return saboteur_v0_7.main(argv)
    finally:
        saboteur_v0_5.mutations_v0_5 = before


if __name__ == "__main__":
    sys.exit(main())
