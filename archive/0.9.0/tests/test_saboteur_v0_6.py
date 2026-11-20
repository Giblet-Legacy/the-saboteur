"""
test_saboteur_v0_6.py — Proof of the Saboteur 0.6.0: 200 threats

Function:
    Executable expression of SPEC_V0_6.md. 0.5.0 and 0.5.1 have their
    own tests; these cover the threat set and the default.

Functions in this file (pytest-collected):
    1. test_there_are_200_threats
    2. test_first_108_are_threats_v0_5_unchanged
    3. test_every_threat_names_a_layer_failure_and_a_known_mutation
    4. test_default_threats_are_v0_6
    5. test_run_takes_the_lock
    6. test_end_to_end_ten_new_threats

Tier:     Tier 2 — The Saboteur, 0.6.0
Spec:     SPEC_V0_6.md 0.6.0
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
import saboteur_v0_5_1  # noqa: E402
import saboteur_v0_6  # noqa: E402

FIXTURE = HERE / "fixture_v0_5"
V05 = HERE / "threats_v0_5"
V06 = HERE / "threats_v0_6"


# 1.
def test_there_are_200_threats():
    names = sorted(p.name for p in V06.glob("*.json"))
    assert len(names) == 200
    assert [n[:3] for n in names] == [f"{i:03d}" for i in range(1, 201)]


# 2.
def test_first_108_are_threats_v0_5_unchanged():
    old = sorted(V05.glob("*.json"))
    assert len(old) == 108
    for p in old:
        assert (V06 / p.name).read_bytes() == p.read_bytes(), p.name


# 3.
def test_every_threat_names_a_layer_failure_and_a_known_mutation():
    known = set(mutations_v0_5._PLAIN) | set(mutations_v0_5._WITH_ARG) | {
        "delete", "reorder_lines", "duplicate_line", "truncate_mid_line", "lf_to_crlf"}
    for path in sorted(V06.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        layer = t["tool"].split("--layer ")[-1] if "--layer" in t["tool"] else None
        assert t["tool"].startswith("python legacy_check_v0_5.py"), path.name
        assert (FIXTURE / t["target_file"]).exists(), path.name
        kw = t["expect_error_contains"]
        assert len(kw) == 1 and kw[0].startswith("failed "), path.name
        if layer:
            assert f": {layer}." in kw[0], path.name
        head = t["mutation"].partition(":")[0] if ":" in t["mutation"] else t["mutation"]
        assert head in known, (path.name, head)


# 4.
def test_default_threats_are_v0_6(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(saboteur_v0_5, "main", lambda argv: seen.setdefault("argv", argv) and 0)
    saboteur_v0_6.main(["--parent", str(tmp_path), "--only", "1"])
    argv = seen["argv"]
    assert argv[argv.index("--threats") + 1] == str(V06)
    seen.clear()
    saboteur_v0_6.main(["--threats", "mine", "--parent", str(tmp_path)])
    assert seen["argv"].count("--threats") == 1 and "mine" in seen["argv"]


# 5.
def test_run_takes_the_lock(tmp_path, monkeypatch):
    def check(argv):
        assert (tmp_path / saboteur_v0_5_1.LOCK_NAME).exists()
        return 0
    monkeypatch.setattr(saboteur_v0_5, "main", check)
    assert saboteur_v0_6.main(["--parent", str(tmp_path)]) == 0
    assert not (tmp_path / saboteur_v0_5_1.LOCK_NAME).exists()


# 6.
def test_end_to_end_ten_new_threats(tmp_path, capsys):
    rc = saboteur_v0_6.main(["--parent", str(tmp_path), "--only", "19"])  # 190–199
    out = capsys.readouterr().out
    assert "PASS 10  FAIL 0  UGLY 0  SKIP 0" in out, out
    assert rc == 0
