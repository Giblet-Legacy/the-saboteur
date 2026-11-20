"""
test_saboteur_v0_5_at_v1.py — test_saboteur_v0_5.py (archive/0.9.0) carried forward against the Saboteur 1.0.0

Function:
    CONSOLIDATION_V1.md §3.2. The live tests of the archived suite
    archive/0.9.0/tests/test_saboteur_v0_5.py, run against the 1.0.0 modules
    (saboteur_v1, mutations_v1, harness_guard_v1, fixture_v1,
    threats_v1). Step 0 decided which tests carry (§3.1).

Functions in this file (pytest-collected):
    1. test_committed_fixture_is_clean
    2. test_fixture_holds_no_private_key
    3. test_build_makes_a_clean_fixture
    4. test_check_names_the_layer_that_said_no
    5. test_check_reports_a_missing_file
    6. test_flip_letter_changes_one_letter
    7. test_line_set_refuses_a_no_op
    8. test_dup_key_first_keeps_the_last_wins_value
    9. test_sqlite_refuses_a_change_of_nothing
    10. test_unknown_mutation_falls_through_to_v2
    11. test_every_threat_names_a_layer_failure
    12. test_refuses_the_full_stack
    13. test_end_to_end_nine_threats

Tier:     Tier 2 — The Saboteur, 1.0.0
Spec:     SPEC_V1.md 1.0.0
Version:  1.0.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("FORGE_LEGACY_ROOT", str(HERE.parent))

import build_fixture_v1  # noqa: E402
import mutations_v1  # noqa: E402
import saboteur_v1  # noqa: E402

FIXTURE = HERE / "fixture_v1"
THREATS = HERE / "threats_v1"  # holds threats_v0_5 as 0001–0108


# 14. _check
def _check(folder, *args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, str(pathlib.Path(folder) / "legacy_check_v1.py"), *args],
                          cwd=str(folder), env=env, capture_output=True, text=True, encoding="utf-8")


@pytest.fixture
def copy(tmp_path):
    dest = tmp_path / "fx"
    shutil.copytree(FIXTURE, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


# 1.
def test_committed_fixture_is_clean(copy):
    r = _check(copy)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "17 checks, 0 not ok" in r.stdout


# 2.
def test_fixture_holds_no_private_key():
    for p in FIXTURE.rglob("*"):
        if p.is_file() and p.suffix != ".db":
            text = p.read_bytes()
            assert b"PRIVATE KEY" not in text, p
    assert sorted(x.name for x in (FIXTURE / "keys").iterdir()) == ["attester.did", "owner.did"]


# 3.
def test_build_makes_a_clean_fixture(tmp_path):
    out = tmp_path / "built"
    out.mkdir()
    shutil.copy2(FIXTURE / "legacy_check_v1.py", out)
    files = build_fixture_v1.build(out)
    assert len(files) == 14
    r = _check(out)
    assert r.returncode == 0, r.stdout + r.stderr


# 4.
def test_check_names_the_layer_that_said_no(copy):
    mutations_v1.apply_mutation(str(copy / "seals" / "seal-approve.json"), 'json_set:validator_tier="AUTHORITY"')
    r = _check(copy, "--layer", "hal_v2")
    assert r.returncode == 1
    assert "FAILED seals/seal-approve.json: hal_v2.verify_seal said no" in r.stdout
    assert "ok     seals/seal-refuse.json  hal_v2.verify_seal" in r.stdout


# 5.
def test_check_reports_a_missing_file(copy):
    (copy / "records" / "note-boot.sc.json").unlink()
    r = _check(copy)
    assert r.returncode == 1
    assert "FAILED records/note-boot.sc.json: manifest.files missing" in r.stdout


# 6.
def test_flip_letter_changes_one_letter(copy):
    p = copy / "capsules" / "claim-forge.sc.json"
    before = p.read_bytes()
    mutations_v1.apply_mutation(str(p), "flip_letter")
    after = p.read_bytes()
    diff = [i for i in range(len(before)) if before[i] != after[i]]
    assert len(before) == len(after) and len(diff) == 1
    json.loads(after)


# 7.
def test_line_set_refuses_a_no_op(copy):
    with pytest.raises(ValueError, match="not a mutation"):
        mutations_v1.apply_mutation(str(copy / "ledger.jsonl"), 'line_set:0:prev="' + "0" * 64 + '"')


# 8.
def test_dup_key_first_keeps_the_last_wins_value(copy):
    p = copy / "records" / "note-morning.sc.json"
    before = json.loads(p.read_bytes())
    mutations_v1.apply_mutation(str(p), 'json_dup_key_first:text="forged"')
    assert b'"text":"forged"' in p.read_bytes()
    assert json.loads(p.read_bytes()) == before


# 9.
def test_sqlite_refuses_a_change_of_nothing(copy):
    with pytest.raises(ValueError, match="no row changed"):
        mutations_v1.apply_mutation(str(copy / "store.db"), "sqlite:DELETE FROM ledger WHERE seq=999")


# 10.
def test_unknown_mutation_falls_through_to_v2(copy):
    p = copy / "docs" / "charter.md"
    mutations_v1.apply_mutation(str(p), "lf_to_crlf")
    assert b"\r\n" in p.read_bytes()
    with pytest.raises(ValueError):
        mutations_v1.apply_mutation(str(p), "no_such_mutation")


# 11.
def test_every_threat_names_a_layer_failure():
    threats = sorted(THREATS.glob("*.json"))
    assert len(threats) >= 100
    for path in threats:
        t = json.loads(path.read_text(encoding="utf-8"))
        assert t["tool"].startswith("python legacy_check_v1.py"), path.name
        assert all(k.lower().startswith("failed ") for k in t["expect_error_contains"]), path.name
        assert (FIXTURE / t["target_file"]).exists(), path.name


# 12.
def test_refuses_the_full_stack(tmp_path, capsys):
    target = tmp_path / "the-full-stack"
    target.mkdir()
    assert saboteur_v1.main(["--target", str(target), "--parent", str(tmp_path)]) == 2
    assert not (tmp_path / "run").exists()


# 13.
def test_end_to_end_nine_threats(tmp_path, capsys):
    rc = saboteur_v1.main(["--parent", str(tmp_path), "--only", "000"])  # 0001–0009 (four digits since 0.9.0)
    out = capsys.readouterr().out
    assert "PASS 9  FAIL 0  UGLY 0  SKIP 0" in out, out
    assert rc == 0
