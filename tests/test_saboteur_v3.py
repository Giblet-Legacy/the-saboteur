"""
test_saboteur_v3.py — Proof that v3 never attacks the-full-stack by default

Function:
    Executable expression of SPEC_V3.md. Written before saboteur_v3.py
    and run red first. v3 is v2's harness unchanged; only the entry
    point changes: --target is required, a the-full-stack target is
    refused, and the threats default to threats_v3/.

Functions in this file (pytest-collected):
    1. test_target_is_required
    2. test_refuses_the_full_stack
    3. test_no_threats_is_invalid
    4. test_end_to_end_on_a_fake_target
    5. test_harness_is_v2s

Helpers:
    6. fake_target — a repo whose verify.py checks one file's hash

Tier:     Tier 2 — The Saboteur, v3
Spec:     SPEC_V3.md 0.4.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import hashlib
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import saboteur_v2  # noqa: E402
import saboteur_v3  # noqa: E402

VERIFY = '''import hashlib, sys, pathlib
want = pathlib.Path("data.hash").read_text().strip()
got = hashlib.sha256(pathlib.Path("data.txt").read_bytes()).hexdigest()
if got != want:
    print("FAILED  data.txt: hash mismatch"); sys.exit(1)
print("OK      data.txt")
'''


# 6. fake_target
@pytest.fixture
def fake_target(tmp_path):
    repo = tmp_path / "target"
    repo.mkdir()
    (repo / "data.txt").write_bytes(b"line one\nline two\n")
    (repo / "data.hash").write_text(hashlib.sha256(b"line one\nline two\n").hexdigest())
    (repo / "verify.py").write_text(VERIFY)
    return repo


def _threat(tmp_path):
    threats = tmp_path / "threats"
    threats.mkdir()
    (threats / "01-caught.json").write_text(json.dumps(
        {"name": "flip caught", "target_file": "data.txt", "mutation": "reorder_lines",
         "tool": "python verify.py", "expect_error_contains": ["data.txt"]}))
    return threats


# 1. test_target_is_required
def test_target_is_required(capsys):
    with pytest.raises(SystemExit):
        saboteur_v3.main([])
    assert not hasattr(saboteur_v3, "DEFAULT_TARGET")


# 2. test_refuses_the_full_stack
def test_refuses_the_full_stack(tmp_path, capsys):
    ref = tmp_path / "the-full-stack"
    ref.mkdir()
    parent = tmp_path / "parent"
    rc = saboteur_v3.main(["--target", str(ref), "--threats", str(_threat(tmp_path)), "--parent", str(parent)])
    assert rc == 2
    assert "reference only" in capsys.readouterr().err
    assert not parent.exists()


# 3. test_no_threats_is_invalid
def test_no_threats_is_invalid(tmp_path, fake_target, capsys):
    empty = tmp_path / "none"
    empty.mkdir()
    assert saboteur_v3.main(["--target", str(fake_target), "--threats", str(empty),
                             "--parent", str(tmp_path / "parent")]) == 2
    assert saboteur_v3.DEFAULT_THREATS == HERE / "threats_v3"


# 4. test_end_to_end_on_a_fake_target
def test_end_to_end_on_a_fake_target(tmp_path, fake_target, capsys):
    rc = saboteur_v3.main(["--target", str(fake_target), "--threats", str(_threat(tmp_path)),
                           "--parent", str(tmp_path / "parent")])
    assert rc == 0
    assert "PASS 1  FAIL 0  UGLY 0  SKIP 0" in capsys.readouterr().out
    assert (fake_target / "data.txt").read_bytes() == b"line one\nline two\n"


# 5. test_harness_is_v2s
def test_harness_is_v2s():
    assert saboteur_v3.run_threat is saboteur_v2.run_threat
    assert saboteur_v3.load_threats is saboteur_v2.load_threats
    code = (HERE / "saboteur_v3.py").read_text(encoding="utf-8").split('"""')[2]
    named = [line for line in code.splitlines() if "the-full-stack" in line]
    assert named == ['_REFERENCE_ONLY = "the-full-stack"']  # only to refuse it
