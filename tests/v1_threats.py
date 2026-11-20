"""
v1_threats.py — the one rule that makes threats_v1/ from the archived threat folders (test helper)

Function:
    CONSOLIDATION_V1.md §2: threats_v1/ is threats_v0_9/ with one change
    per file, the tool's name (legacy_check_v0_5.py -> legacy_check_v1.py).
    threats_v0_9/ holds threats_v0_8/ byte for byte under four-digit
    names, and so on down to threats_v0_5/. So an archived threat from
    any 0.x folder appears in threats_v1/ under its four-digit name with
    the tool renamed. The carried suites use this to keep their
    "the first N are the earlier set unchanged" tests. Not collected by
    pytest (no test_ prefix).

Public API:
    1. archived(version) -> Path      e.g. archived("0_6") -> archive/0.9.0/threats_v0_6
    2. v1_name(path) -> str           "017-x.json" -> "0017-x.json"
    3. as_v1(path) -> bytes           the archived file's bytes, tool renamed
    4. in_v1(path) -> bool            threats_v1/ holds exactly as_v1(path)

Tier:     Tier 2 — The Saboteur, 1.0.0
Spec:     SPEC_V1.md 1.0.0
Version:  1.0.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
V1 = ROOT / "threats_v1"
OLD_TOOL = b"legacy_check_v0_5.py"
NEW_TOOL = b"legacy_check_v1.py"


# 1. archived
def archived(version):
    return ROOT / "archive" / "0.9.0" / f"threats_v{version}"


# 2. v1_name
def v1_name(path):
    name = pathlib.Path(path).name
    return name if len(name.split("-")[0]) == 4 else "0" + name


# 3. as_v1
def as_v1(path):
    return pathlib.Path(path).read_bytes().replace(OLD_TOOL, NEW_TOOL)


# 4. in_v1
def in_v1(path):
    target = V1 / v1_name(path)
    return target.exists() and target.read_bytes() == as_v1(path)
