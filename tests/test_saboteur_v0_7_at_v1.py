"""
test_saboteur_v0_7_at_v1.py — test_saboteur_v0_7.py (archive/0.9.0) carried forward against the Saboteur 1.0.0

Function:
    CONSOLIDATION_V1.md §3.2. The live tests of the archived suite
    archive/0.9.0/tests/test_saboteur_v0_7.py, run against the 1.0.0 modules
    (saboteur_v1, mutations_v1, harness_guard_v1, fixture_v1,
    threats_v1). Step 0 decided which tests carry (§3.1).

Functions in this file (pytest-collected):
    1. test_there_are_400_threats
    2. test_first_200_are_threats_v0_6_unchanged
    3. test_every_threat_names_a_layer_failure_and_a_known_mutation
    4. test_no_two_threats_are_the_same_attack
    5. test_end_to_end_type_confusion

Tier:     Tier 2 — The Saboteur, 1.0.0
Spec:     SPEC_V1.md 1.0.0
Version:  1.0.0-dev
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("FORGE_LEGACY_ROOT", str(HERE.parent))

import mutations_v1  # noqa: E402
import saboteur_v1  # noqa: E402
from v1_threats import V1, archived, in_v1  # noqa: E402

FIXTURE = HERE / "fixture_v1"
V06 = archived("0_6")
V07 = archived("0_7")


# 1.
def test_there_are_400_threats():
    names = sorted(p.name for p in V07.glob("*.json"))
    assert [n[:3] for n in names] == [f"{i:03d}" for i in range(1, 401)]
    for p in sorted(V07.glob("*.json")):
        assert in_v1(p), p.name  # 1.0.0: 0001–0400, tool renamed


# 2.
def test_first_200_are_threats_v0_6_unchanged():
    old = sorted(V06.glob("*.json"))
    assert len(old) == 200
    for p in old:
        assert (V07 / p.name).read_bytes() == p.read_bytes(), p.name
        assert in_v1(p), p.name


# 3.
def test_every_threat_names_a_layer_failure_and_a_known_mutation():
    known = set(mutations_v1._PLAIN) | set(mutations_v1._WITH_ARG) | {
        "delete", "reorder_lines", "duplicate_line", "truncate_mid_line", "lf_to_crlf"}
    for path in sorted(V1.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        assert t["tool"].startswith("python legacy_check_v1.py"), path.name
        assert (FIXTURE / t["target_file"]).exists(), path.name
        kw = t["expect_error_contains"]
        assert len(kw) == 1 and kw[0].startswith("failed "), path.name
        if "--layer " in t["tool"]:
            assert f": {t['tool'].split('--layer ')[-1]}." in kw[0], path.name
        head = t["mutation"].partition(":")[0] if ":" in t["mutation"] else t["mutation"]
        assert head in known, (path.name, head)


# 4.
def test_no_two_threats_are_the_same_attack():
    seen = {}
    for path in sorted(V1.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        key = (t["target_file"], t["mutation"], t["tool"])
        assert key not in seen, (path.name, seen.get(key))
        seen[key] = path.name


# 6.
def test_end_to_end_type_confusion(tmp_path, capsys):
    rc = saboteur_v1.main(["--parent", str(tmp_path), "--only", "020"])  # 200–209
    out = capsys.readouterr().out
    assert "PASS 10  FAIL 0  UGLY 0  SKIP 0" in out, out
    assert rc == 0
