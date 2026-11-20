"""
saboteur_v0_5.py — The Saboteur 0.5.0: v2's harness against the Legacy's own layers

Function:
    The layer over saboteur_v0_4.py and saboteur_v2.py (SPEC_V0_5.md);
    neither is edited. James, 2026-11-20: "yes lets a a ton more". The
    harness (guard, canaries, clean baseline, one mutation, judge, exit
    codes) is v2's own code. 0.5.0 changes only what it is given:

      - the target defaults to fixture_v0_5/, a small Legacy world made
        by the real layers with throwaway keys (build_fixture_v0_5.py),
        whose legacy_check_v0_5.py asks each layer about each file;
      - the threats default to threats_v0_5/;
      - the mutations are mutations_v0_5 (v2's, plus attacks on the
        Legacy's own files), put in place of v2's for this run;
      - FORGE_LEGACY_ROOT tells the scratch copy where the layers are
        (the-saboteur's siblings unless already set).

    A target folder named the-full-stack is still refused (0.4.0).

    python saboteur_v0_5.py [--target fixture_v0_5] [--threats threats_v0_5] [--only NN]

Public API:
    1. main(argv=None) -> int

Tier:     Tier 2 — The Saboteur, 0.5.0
Depends:  saboteur_v2.py, harness_guard_v2.py, mutations_v0_5.py
Spec:     SPEC_V0_5.md 0.5.0
Version:  0.5.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_guard_v2 as guard  # noqa: E402
import mutations_v0_5  # noqa: E402
import saboteur_v2  # noqa: E402

DEFAULT_TARGET = HERE / "fixture_v0_5"
DEFAULT_THREATS = HERE / "threats_v0_5"
_REFERENCE_ONLY = "the-full-stack"


# 1. main
def main(argv=None):
    p = argparse.ArgumentParser(description="The Saboteur 0.5.0: prove every Legacy layer says no, by name.")
    p.add_argument("--target", default=str(DEFAULT_TARGET), help="folder to attack (a scratch copy is used)")
    p.add_argument("--threats", default=str(DEFAULT_THREATS), help="directory of threat JSON files")
    p.add_argument("--parent", default=str(guard.DEFAULT_PARENT), help="where scratch copies are made")
    p.add_argument("--only", help="run only threats whose file name starts with this")
    args = p.parse_args(argv)
    if pathlib.Path(args.target).resolve().name == _REFERENCE_ONLY:
        print(f"refused: {_REFERENCE_ONLY} is reference only, not a Legacy layer (SPEC_V0_4 section 1)", file=sys.stderr)
        return 2
    os.environ.setdefault("FORGE_LEGACY_ROOT", str(HERE.parent))
    saboteur_v2.mutations = mutations_v0_5
    rest = ["--target", args.target, "--threats", args.threats, "--parent", args.parent]
    if args.only:
        rest += ["--only", args.only]
    return saboteur_v2.main(rest)


if __name__ == "__main__":
    sys.exit(main())
