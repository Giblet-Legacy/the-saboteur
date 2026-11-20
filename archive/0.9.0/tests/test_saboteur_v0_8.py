"""
test_saboteur_v0_8.py — Proof of the Saboteur 0.8.0: 800 threats, substitution and text mutations

Function:
    Executable expression of SPEC_V0_8.md. Earlier versions have their
    own tests; these cover mutations_v0_8, the threat set and the
    runner's mutation swap.

Functions in this file (pytest-collected):
    1. test_copy_sibling_replaces_the_bytes
    2. test_copy_sibling_refuses_identical_bytes
    3. test_copy_sibling_refuses_outside_the_fixture
    4. test_text_replace_changes_the_first_match
    5. test_text_replace_refuses_a_no_op
    6. test_unknown_mutation_falls_through_to_v0_5
    7. test_there_are_800_threats
    8. test_first_400_are_threats_v0_7_unchanged
    9. test_every_threat_names_a_layer_failure_and_a_known_mutation
    10. test_no_two_threats_are_the_same_attack
    11. test_runner_swaps_mutations_and_puts_them_back
    12. test_end_to_end_type_confusion_matrix

Tier:     Tier 2 — The Saboteur, 0.8.0
Spec:     SPEC_V0_8.md 0.8.0
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

import mutations_v0_5  # noqa: E402
import mutations_v0_8  # noqa: E402
import saboteur_v0_5  # noqa: E402
import saboteur_v0_8  # noqa: E402

FIXTURE = HERE / "fixture_v0_5"
V07 = HERE / "threats_v0_7"
V08 = HERE / "threats_v0_8"


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "one.txt").write_bytes(b"one\n")
    (tmp_path / "a" / "two.txt").write_bytes(b"two\n")
    (tmp_path / "b" / "three.txt").write_bytes(b"three\n")
    return tmp_path


# 1.
def test_copy_sibling_replaces_the_bytes(tree):
    victim = tree / "a" / "one.txt"
    mutations_v0_8.apply_mutation(str(victim), "copy_sibling:two.txt")
    assert victim.read_bytes() == b"two\n"
    mutations_v0_8.apply_mutation(str(victim), "copy_sibling:../b/three.txt")
    assert victim.read_bytes() == b"three\n"


# 2.
def test_copy_sibling_refuses_identical_bytes(tree):
    (tree / "a" / "two.txt").write_bytes(b"one\n")
    with pytest.raises(ValueError):
        mutations_v0_8.apply_mutation(str(tree / "a" / "one.txt"), "copy_sibling:two.txt")


# 3.
def test_copy_sibling_refuses_outside_the_fixture(tree):
    victim = str(tree / "a" / "one.txt")
    for arg in ("../../outside.txt", str(tree / "b" / "three.txt"), "C:/x", "", "missing.txt"):
        with pytest.raises(ValueError):
            mutations_v0_8.apply_mutation(victim, f"copy_sibling:{arg}")


# 4.
def test_text_replace_changes_the_first_match(tree):
    victim = tree / "a" / "one.txt"
    victim.write_bytes(b"aa aa\n")
    mutations_v0_8.apply_mutation(str(victim), "text_replace:aa=>bb")
    assert victim.read_bytes() == b"bb aa\n"


# 5.
def test_text_replace_refuses_a_no_op(tree):
    victim = str(tree / "a" / "one.txt")
    for arg in ("zz=>yy", "one=>one", "one", "=>x"):
        with pytest.raises(ValueError):
            mutations_v0_8.apply_mutation(victim, f"text_replace:{arg}")


# 6.
def test_unknown_mutation_falls_through_to_v0_5(tree):
    victim = tree / "a" / "one.txt"
    mutations_v0_8.apply_mutation(str(victim), "empty")
    assert victim.read_bytes() == b""


# 7.
def test_there_are_800_threats():
    names = sorted(p.name for p in V08.glob("*.json"))
    assert [n[:3] for n in names] == [f"{i:03d}" for i in range(1, 801)]


# 8.
def test_first_400_are_threats_v0_7_unchanged():
    old = sorted(V07.glob("*.json"))
    assert len(old) == 400
    for p in old:
        assert (V08 / p.name).read_bytes() == p.read_bytes(), p.name


# 9.
def test_every_threat_names_a_layer_failure_and_a_known_mutation():
    known = (set(mutations_v0_5._PLAIN) | set(mutations_v0_5._WITH_ARG) | set(mutations_v0_8._WITH_ARG)
             | {"delete", "reorder_lines", "duplicate_line", "truncate_mid_line", "lf_to_crlf"})
    for path in sorted(V08.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        assert t["tool"].startswith("python legacy_check_v0_5.py"), path.name
        assert (FIXTURE / t["target_file"]).exists(), path.name
        kw = t["expect_error_contains"]
        assert len(kw) == 1 and kw[0].startswith("failed "), path.name
        if "--layer " in t["tool"]:
            assert f": {t['tool'].split('--layer ')[-1]}." in kw[0], path.name
        head = t["mutation"].partition(":")[0] if ":" in t["mutation"] else t["mutation"]
        assert head in known, (path.name, head)


# 10.
def test_no_two_threats_are_the_same_attack():
    seen = {}
    for path in sorted(V08.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        key = (t["target_file"], t["mutation"], t["tool"])
        assert key not in seen, (path.name, seen.get(key))
        seen[key] = path.name


# 11.
def test_runner_swaps_mutations_and_puts_them_back(tmp_path, monkeypatch):
    seen = {}

    def fake(argv):
        seen["argv"] = argv
        seen["mutations"] = saboteur_v0_5.mutations_v0_5
        return 0
    monkeypatch.setattr(saboteur_v0_5, "main", fake)
    assert saboteur_v0_8.main(["--parent", str(tmp_path)]) == 0
    assert seen["mutations"] is mutations_v0_8
    assert saboteur_v0_5.mutations_v0_5 is mutations_v0_5
    assert seen["argv"][seen["argv"].index("--threats") + 1] == str(V08)


# 12.
def test_end_to_end_type_confusion_matrix(tmp_path, capsys):
    rc = saboteur_v0_8.main(["--parent", str(tmp_path), "--only", "42"])  # 420–429
    out = capsys.readouterr().out
    assert "UGLY 0  SKIP 0" in out, out
    assert "PASS 10  FAIL 0" in out, out
    assert rc == 0
