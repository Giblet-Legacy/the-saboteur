"""
saboteur_v0_4.py — The Saboteur 0.4.0: v2's harness with no default target

Function:
    The layer over saboteur_v2.py (SPEC_V0_4.md). v2 is not edited. James,
    2026-11-18: the-full-stack is reference only, never a layer of the
    Legacy. v2 attacked it by default; 0.4.0 needs --target, refuses a
    folder named for it, and reads its threats from threats_v0_4/. The
    harness itself (guard, canaries, baseline, judging, exit codes) is
    v2's own code.

    python saboteur_v0_4.py --target DIR [--threats threats_v0_4] [--only NN]

Public API:
    1. main(argv=None) -> int
    Re-exported from saboteur_v2: load_threats, run_threat

Tier:     Tier 2 — The Saboteur, 0.4.0
Depends:  saboteur_v2.py, harness_guard_v2.py
Spec:     SPEC_V0_4.md 0.4.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_guard_v2 as guard  # noqa: E402
import saboteur_v2  # noqa: E402
from saboteur_v2 import load_threats, run_threat  # noqa: E402,F401

DEFAULT_THREATS = HERE / "threats_v0_4"
_REFERENCE_ONLY = "the-full-stack"


# 1. main
def main(argv=None):
    p = argparse.ArgumentParser(description="The Saboteur 0.4.0: prove every tool fails loudly.")
    p.add_argument("--target", required=True, help="repo to attack (a scratch copy is used)")
    p.add_argument("--threats", default=str(DEFAULT_THREATS), help="directory of threat JSON files")
    p.add_argument("--parent", default=str(guard.DEFAULT_PARENT), help="where scratch copies are made")
    p.add_argument("--only", help="run only threats whose file name starts with this")
    args = p.parse_args(argv)
    if pathlib.Path(args.target).resolve().name == _REFERENCE_ONLY:
        print(f"refused: {_REFERENCE_ONLY} is reference only, not a Legacy layer (SPEC_V0_4 section 1)", file=sys.stderr)
        return 2
    rest = ["--target", args.target, "--threats", args.threats, "--parent", args.parent]
    if args.only:
        rest += ["--only", args.only]
    return saboteur_v2.main(rest)


if __name__ == "__main__":
    sys.exit(main())
