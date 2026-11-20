"""
saboteur_v0_7.py — The Saboteur 0.7.0: 400 threats against the Legacy's own layers

Function:
    The layer over saboteur_v0_6.py (SPEC_V0_7.md); nothing earlier is
    edited. James, 2026-11-20: "200 more" (attacks). The run is 0.6.0's
    (0.5.1's lock, 0.5.0's harness, fixture and mutations). 0.7.0
    changes only the default threats: threats_v0_7/, the 200 of
    threats_v0_6/ copied unchanged (001-200) and 200 new (201-400),
    mostly type confusion: a layer must say no, never raise.

    python saboteur_v0_7.py [--target fixture_v0_5] [--threats threats_v0_7] [--parent DIR] [--only NNN]

Public API:
    1. main(argv=None) -> int

Tier:     Tier 2 — The Saboteur, 0.7.0
Depends:  saboteur_v0_6.py
Spec:     SPEC_V0_7.md 0.7.0
Version:  0.7.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import saboteur_v0_6  # noqa: E402

DEFAULT_THREATS = HERE / "threats_v0_7"


# 1. main
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not any(a == "--threats" or a.startswith("--threats=") for a in argv):
        argv = ["--threats", str(DEFAULT_THREATS)] + argv
    return saboteur_v0_6.main(argv)


if __name__ == "__main__":
    sys.exit(main())
