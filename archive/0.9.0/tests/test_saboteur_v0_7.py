"""
test_saboteur_v0_7.py — Proof of the Saboteur 0.7.0: 400 threats

Function:
    Executable expression of SPEC_V0_7.md. Earlier versions have their
    own tests; these cover the threat set and the default.

Functions in this file (pytest-collected):
    1. test_there_are_400_threats
    2. test_first_200_are_threats_v0_6_unchanged
    3. test_every_threat_names_a_layer_failure_and_a_known_mutation
    4. test_no_two_threats_are_the_same_attack
    5. test_default_threats_are_v0_7
    6. test_end_to_end_type_confusion

Tier:     Tier 2 — The Saboteur, 0.7.0
Spec:     SPEC_V0_7.md 0.7.0
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

import mutations_v0_5  # noqa: E402
import saboteur_v0_5  # noqa: E402
import saboteur_v0_7  # noqa: E402

FIXTURE = HERE / "fixture_v0_5"
V06 = HERE / "threats_v0_6"
V07 = HERE / "threats_v0_7"


# 1.
def test_there_are_400_threats():
    names = sorted(p.name for p in V07.glob("*.json"))
    assert [n[:3] for n in names] == [f"{i:03d}" for i in range(1, 401)]


# 2.
def test_first_200_are_threats_v0_6_unchanged():
    old = sorted(V06.glob("*.json"))
    assert len(old) == 200
    for p in old:
        assert (V07 / p.name).read_bytes() == p.read_bytes(), p.name


# 3.
def test_every_threat_names_a_layer_failure_and_a_known_mutation():
    known = set(mutations_v0_5._PLAIN) | set(mutations_v0_5._WITH_ARG) | {
        "delete", "reorder_lines", "duplicate_line", "truncate_mid_line", "lf_to_crlf"}
    for path in sorted(V07.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        assert t["tool"].startswith("python legacy_check_v0_5.py"), path.name
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
    for path in sorted(V07.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        key = (t["target_file"], t["mutation"], t["tool"])
        assert key not in seen, (path.name, seen.get(key))
        seen[key] = path.name


# 5.
def test_default_threats_are_v0_7(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(saboteur_v0_5, "main", lambda argv: seen.setdefault("argv", argv) and 0)
    saboteur_v0_7.main(["--parent", str(tmp_path)])
    argv = seen["argv"]
    assert argv.count("--threats") == 1
    assert argv[argv.index("--threats") + 1] == str(V07)


# 6.
def test_end_to_end_type_confusion(tmp_path, capsys):
    rc = saboteur_v0_7.main(["--parent", str(tmp_path), "--only", "20"])  # 200–209
    out = capsys.readouterr().out
    assert "PASS 10  FAIL 0  UGLY 0  SKIP 0" in out, out
    assert rc == 0
