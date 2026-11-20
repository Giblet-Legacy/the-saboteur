"""
test_saboteur_v0_9_at_v1.py — test_saboteur_v0_9.py (archive/0.9.0) carried forward against the Saboteur 1.0.0

Function:
    CONSOLIDATION_V1.md §3.2. The live tests of the archived suite
    archive/0.9.0/tests/test_saboteur_v0_9.py, run against the 1.0.0 modules
    (saboteur_v1, mutations_v1, harness_guard_v1, fixture_v1,
    threats_v1). Step 0 decided which tests carry (§3.1).

Functions in this file (pytest-collected):
    1. test_keep_first_lines_rolls_back
    2. test_keep_first_lines_refuses_a_non_rollback
    3. test_json_reformat_keeps_the_content
    4. test_json_reformat_refuses_unchanged_bytes
    5. test_unknown_mutation_falls_through_to_v0_8
    6. test_there_are_1000_threats
    7. test_first_800_are_threats_v0_8_unchanged
    8. test_every_threat_names_a_layer_failure_and_a_known_mutation
    9. test_no_two_threats_are_the_same_attack
    10. test_every_new_threat_names_its_gap
    11. test_end_to_end_rollback_depth

Tier:     Tier 2 — The Saboteur, 1.0.0
Spec:     SPEC_V1.md 1.0.0
Version:  1.0.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("FORGE_LEGACY_ROOT", str(HERE.parent))

import mutations_v1  # noqa: E402
import saboteur_v1  # noqa: E402
from v1_threats import V1, archived, in_v1  # noqa: E402

FIXTURE = HERE / "fixture_v1"
V08 = archived("0_8")
V09 = V1  # threats_v1 carries threats_v0_9, four-digit names
GAPS = {"rollback", "dup-key", "unsigned-column", "deleted-row", "non-canonical", "substitution"}


# 1.
def test_keep_first_lines_rolls_back(tmp_path):
    p = tmp_path / "l.jsonl"
    p.write_bytes(b"a\nb\nc\n")
    mutations_v1.apply_mutation(str(p), "keep_first_lines:2")
    assert p.read_bytes() == b"a\nb\n"


# 2.
def test_keep_first_lines_refuses_a_non_rollback(tmp_path):
    p = tmp_path / "l.jsonl"
    p.write_bytes(b"a\nb\n")
    for n in ("0", "2", "3"):
        with pytest.raises(ValueError):
            mutations_v1.apply_mutation(str(p), f"keep_first_lines:{n}")


# 3.
def test_json_reformat_keeps_the_content(tmp_path):
    src = FIXTURE / "records" / "note-boot.sc.json"
    for style in ("compact", "indent4", "sorted", "reversed", "escape_letter"):
        p = tmp_path / f"{style}.json"
        p.write_bytes(src.read_bytes())
        mutations_v1.apply_mutation(str(p), f"json_reformat:{style}")
        assert p.read_bytes() != src.read_bytes(), style
        assert json.loads(p.read_text(encoding="utf-8")) == json.loads(src.read_text(encoding="utf-8")), style


# 4.
def test_json_reformat_refuses_unchanged_bytes(tmp_path):
    p = tmp_path / "c.json"
    p.write_bytes(b'{"a":1}')
    with pytest.raises(ValueError):
        mutations_v1.apply_mutation(str(p), "json_reformat:compact")
    with pytest.raises(ValueError):
        mutations_v1.apply_mutation(str(p), "json_reformat:nonsense")


# 5.
def test_unknown_mutation_falls_through_to_v0_8(tmp_path):
    (tmp_path / "d").mkdir()
    a, b = tmp_path / "d" / "a.txt", tmp_path / "d" / "b.txt"
    a.write_bytes(b"a")
    b.write_bytes(b"b")
    mutations_v1.apply_mutation(str(a), "copy_sibling:b.txt")
    assert a.read_bytes() == b"b"


# 6.
def test_there_are_1000_threats():
    names = sorted(p.name for p in V09.glob("*.json"))
    assert [n[:4] for n in names] == [f"{i:04d}" for i in range(1, 1001)]


# 7.
def test_first_800_are_threats_v0_8_unchanged():
    old = sorted(V08.glob("*.json"))
    assert len(old) == 800
    for p in old:
        assert in_v1(p), p.name  # the same bytes but the tool name


# 8.
def test_every_threat_names_a_layer_failure_and_a_known_mutation():
    known = (set(mutations_v1._PLAIN) | set(mutations_v1._WITH_ARG) | set(mutations_v1._WITH_ARG)
             | set(mutations_v1._WITH_ARG) | {"delete", "reorder_lines", "duplicate_line", "truncate_mid_line", "lf_to_crlf"})
    for path in sorted(V09.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        assert t["tool"].startswith("python legacy_check_v1.py"), path.name
        assert (FIXTURE / t["target_file"]).exists(), path.name
        kw = t["expect_error_contains"]
        assert len(kw) == 1 and kw[0].startswith("failed "), path.name
        if "--layer " in t["tool"]:
            assert f": {t['tool'].split('--layer ')[-1]}." in kw[0], path.name
        head = t["mutation"].partition(":")[0] if ":" in t["mutation"] else t["mutation"]
        assert head in known, (path.name, head)


# 9.
def test_no_two_threats_are_the_same_attack():
    seen = {}
    for path in sorted(V09.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        key = (t["target_file"], t["mutation"], t["tool"])
        assert key not in seen, (path.name, seen.get(key))
        seen[key] = path.name


# 10.
def test_every_new_threat_names_its_gap():
    for path in sorted(V09.glob("*.json")):
        if int(path.name[:4]) > 800:
            assert json.loads(path.read_text(encoding="utf-8"))["gap"] in GAPS, path.name


# 12.
def test_end_to_end_rollback_depth(tmp_path, capsys):
    # 0800 (a field-matrix threat, green) and 0801-0809: the ledger rolled
    # back to 1-4 entries under both ledger checks, and the store to 1 row.
    rc = saboteur_v1.main(["--parent", str(tmp_path), "--only", "080"])
    out = capsys.readouterr().out
    assert "UGLY 0  SKIP 0" in out, out
    assert "PASS 1  FAIL 9" in out, out  # every rollback is a known gap: red
    assert rc == 1
