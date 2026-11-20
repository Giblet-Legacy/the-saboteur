"""
saboteur_v0_6.py — The Saboteur 0.6.0: 200 threats against the Legacy's own layers

Function:
    The layer over saboteur_v0_5_1.py (SPEC_V0_6.md); nothing frozen is
    edited. James, 2026-11-20: "200 tests for saboteur". The run is
    0.5.1's (0.5.0's harness, fixture and mutations, inside the run
    lock). 0.6.0 changes only the default threats: threats_v0_6/, the
    108 of threats_v0_5/ copied unchanged (001-108) and 92 new
    (109-200). The new ones are data only: they use 0.5.0's mutations.

    python saboteur_v0_6.py [--target fixture_v0_5] [--threats threats_v0_6] [--parent DIR] [--only NNN]

Public API:
    1. main(argv=None) -> int

Tier:     Tier 2 — The Saboteur, 0.6.0
Depends:  saboteur_v0_5_1.py
Spec:     SPEC_V0_6.md 0.6.0
Version:  0.6.0-dev
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import saboteur_v0_5_1  # noqa: E402

DEFAULT_THREATS = HERE / "threats_v0_6"


# 1. main
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not any(a == "--threats" or a.startswith("--threats=") for a in argv):
        argv = ["--threats", str(DEFAULT_THREATS)] + argv
    return saboteur_v0_5_1.main(argv)


if __name__ == "__main__":
    sys.exit(main())
