"""
test_saboteur_v0_4_at_v1.py — test_saboteur_v0_4.py (archive/0.9.0) carried forward against the Saboteur 1.0.0

Function:
    CONSOLIDATION_V1.md §3.2. The live tests of the archived suite
    archive/0.9.0/tests/test_saboteur_v0_4.py, run against the 1.0.0 modules
    (saboteur_v1, mutations_v1, harness_guard_v1, fixture_v1,
    threats_v1). Step 0 decided which tests carry (§3.1).

Functions in this file (pytest-collected):
    1. test_no_threats_is_invalid
    2. test_end_to_end_on_a_fake_target
    3. test_harness_is_v2s

Tier:     Tier 2 — The Saboteur, 1.0.0
Spec:     SPEC_V1.md 1.0.0
Version:  1.0.0 (frozen 2026-11-20)
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

import saboteur_v1  # noqa: E402

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






# 3. test_no_threats_is_invalid
def test_no_threats_is_invalid(tmp_path, fake_target, capsys):
    empty = tmp_path / "none"
    empty.mkdir()
    assert saboteur_v1.main(["--target", str(fake_target), "--threats", str(empty),
                             "--parent", str(tmp_path / "parent")]) == 2
    assert saboteur_v1.DEFAULT_THREATS == HERE / "threats_v1"  # 0.4.0 said threats_v0_4


# 4. test_end_to_end_on_a_fake_target
def test_end_to_end_on_a_fake_target(tmp_path, fake_target, capsys):
    rc = saboteur_v1.main(["--target", str(fake_target), "--threats", str(_threat(tmp_path)),
                           "--parent", str(tmp_path / "parent")])
    assert rc == 0
    assert "PASS 1  FAIL 0  UGLY 0  SKIP 0" in capsys.readouterr().out
    assert (fake_target / "data.txt").read_bytes() == b"line one\nline two\n"


# 5. test_harness_is_v2s
def test_harness_is_v2s():
    # 0.4.0 checked it reused v2's harness; in 1.0.0 the harness is saboteur_v1's own code.
    assert saboteur_v1.run_threat.__module__ == "saboteur_v1"
    assert saboteur_v1.load_threats.__module__ == "saboteur_v1"
    code = (HERE / "saboteur_v1.py").read_text(encoding="utf-8").split('"""')[2]
    named = [line for line in code.splitlines() if "the-full-stack" in line]
    assert named == ['_REFERENCE_ONLY = "the-full-stack"']  # only to refuse it
