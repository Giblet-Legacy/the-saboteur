"""
test_saboteur_v0_5.py — Proof of the Saboteur 0.5.0: the fixture, the check, the new mutations, the threats

Function:
    Executable expression of SPEC_V0_5.md. The harness is v2's and has
    its own tests; these cover what 0.5.0 adds.

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

Helpers:
    14. _check — run legacy_check_v0_5.py in a folder

Tier:     Tier 2 — The Saboteur, 0.5.0
Spec:     SPEC_V0_5.md 0.5.0
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

import build_fixture_v0_5  # noqa: E402
import mutations_v0_5  # noqa: E402
import saboteur_v0_5  # noqa: E402

FIXTURE = HERE / "fixture_v0_5"
THREATS = HERE / "threats_v0_5"


# 14. _check
def _check(folder, *args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, str(pathlib.Path(folder) / "legacy_check_v0_5.py"), *args],
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
    shutil.copy2(FIXTURE / "legacy_check_v0_5.py", out)
    files = build_fixture_v0_5.build(out)
    assert len(files) == 14
    r = _check(out)
    assert r.returncode == 0, r.stdout + r.stderr


# 4.
def test_check_names_the_layer_that_said_no(copy):
    mutations_v0_5.apply_mutation(str(copy / "seals" / "seal-approve.json"), 'json_set:validator_tier="AUTHORITY"')
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
    mutations_v0_5.apply_mutation(str(p), "flip_letter")
    after = p.read_bytes()
    diff = [i for i in range(len(before)) if before[i] != after[i]]
    assert len(before) == len(after) and len(diff) == 1
    json.loads(after)


# 7.
def test_line_set_refuses_a_no_op(copy):
    with pytest.raises(ValueError, match="not a mutation"):
        mutations_v0_5.apply_mutation(str(copy / "ledger.jsonl"), 'line_set:0:prev="' + "0" * 64 + '"')


# 8.
def test_dup_key_first_keeps_the_last_wins_value(copy):
    p = copy / "records" / "note-morning.sc.json"
    before = json.loads(p.read_bytes())
    mutations_v0_5.apply_mutation(str(p), 'json_dup_key_first:text="forged"')
    assert b'"text":"forged"' in p.read_bytes()
    assert json.loads(p.read_bytes()) == before


# 9.
def test_sqlite_refuses_a_change_of_nothing(copy):
    with pytest.raises(ValueError, match="no row changed"):
        mutations_v0_5.apply_mutation(str(copy / "store.db"), "sqlite:DELETE FROM ledger WHERE seq=999")


# 10.
def test_unknown_mutation_falls_through_to_v2(copy):
    p = copy / "docs" / "charter.md"
    mutations_v0_5.apply_mutation(str(p), "lf_to_crlf")
    assert b"\r\n" in p.read_bytes()
    with pytest.raises(ValueError):
        mutations_v0_5.apply_mutation(str(p), "no_such_mutation")


# 11.
def test_every_threat_names_a_layer_failure():
    threats = sorted(THREATS.glob("*.json"))
    assert len(threats) >= 100
    for path in threats:
        t = json.loads(path.read_text(encoding="utf-8"))
        assert t["tool"].startswith("python legacy_check_v0_5.py"), path.name
        assert all(k.lower().startswith("failed ") for k in t["expect_error_contains"]), path.name
        assert (FIXTURE / t["target_file"]).exists(), path.name


# 12.
def test_refuses_the_full_stack(tmp_path, capsys):
    target = tmp_path / "the-full-stack"
    target.mkdir()
    assert saboteur_v0_5.main(["--target", str(target), "--parent", str(tmp_path)]) == 2
    assert not (tmp_path / "run").exists()


# 13.
def test_end_to_end_nine_threats(tmp_path, capsys):
    rc = saboteur_v0_5.main(["--parent", str(tmp_path), "--only", "00"])  # 001–009
    out = capsys.readouterr().out
    assert "PASS 9  FAIL 0  UGLY 0  SKIP 0" in out, out
    assert rc == 0
