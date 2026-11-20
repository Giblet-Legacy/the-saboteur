"""
test_saboteur_v2_at_v1.py — test_saboteur_v2.py (archive/0.9.0) carried forward against the Saboteur 1.0.0

Function:
    CONSOLIDATION_V1.md §3.2. The live tests of the archived suite
    archive/0.9.0/tests/test_saboteur_v2.py, run against the 1.0.0 modules
    (saboteur_v1, mutations_v1, harness_guard_v1, fixture_v1,
    threats_v1). Step 0 decided which tests carry (§3.1).

Functions in this file (pytest-collected):
    1. test_guard_refuses
    2. test_init_scratch_refuses_unmarked
    3. test_judge
    4. test_canaries_prove_the_judge
    5. test_mutations_change_only_what_they_say
    6. test_wrong_key_is_base64_and_keeps_key_id
    7. test_end_to_end_on_a_fake_target
    8. test_real_repo_touched_is_invalid

Tier:     Tier 2 — The Saboteur, 1.0.0
Spec:     SPEC_V1.md 1.0.0
Version:  1.0.0-dev
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import base64
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import harness_guard_v1 as guard  # noqa: E402
import mutations_v1  # noqa: E402
import saboteur_v1  # noqa: E402

VERIFY = '''import hashlib, sys, pathlib
want = pathlib.Path("data.hash").read_text().strip()
got = hashlib.sha256(pathlib.Path("data.txt").read_bytes()).hexdigest()
if got != want:
    print("FAILED  data.txt: hash mismatch"); sys.exit(1)
print("OK      data.txt")
'''


# 9. fake_target
@pytest.fixture
def fake_target(tmp_path):
    import hashlib
    repo = tmp_path / "target"
    repo.mkdir()
    (repo / "data.txt").write_bytes(b"line one\nline two\n")
    (repo / "data.hash").write_text(hashlib.sha256(b"line one\nline two\n").hexdigest())
    (repo / "verify.py").write_text(VERIFY)
    (repo / "silent.py").write_text("print('all good')\n")
    return repo


# 1. test_guard_refuses
def test_guard_refuses(tmp_path):
    parent = tmp_path / "parent"
    (parent / "s").mkdir(parents=True)
    with pytest.raises(guard.HarnessInvalid, match="marker missing"):
        guard.guard_scratch(parent / "s", parent)
    with pytest.raises(guard.HarnessInvalid, match="parent itself"):
        guard.guard_scratch(parent, parent)
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / guard.MARKER).write_text("x")
    with pytest.raises(guard.HarnessInvalid, match="not under"):
        guard.guard_scratch(outside, parent)
    (parent / "s" / guard.MARKER).write_text("x")
    assert guard.guard_scratch(parent / "s", parent) == (parent / "s").resolve()


# 2. test_init_scratch_refuses_unmarked
def test_init_scratch_refuses_unmarked(tmp_path, fake_target):
    parent = tmp_path / "parent"
    victim = parent / "run"
    victim.mkdir(parents=True)
    (victim / "precious.txt").write_text("do not delete")
    with pytest.raises(guard.HarnessInvalid, match="no marker"):
        guard.init_scratch(victim, fake_target, parent)
    assert (victim / "precious.txt").read_text() == "do not delete"
    (victim / "precious.txt").unlink()
    made = guard.init_scratch(victim, fake_target, parent)
    assert (made / guard.MARKER).exists() and (made / "data.txt").exists()


# 3. test_judge
def test_judge():
    assert guard.judge(0, "fine", "")[0] == "FAIL"
    assert guard.judge(1, "", "Traceback (most recent call last):\n  boom")[0] == "UGLY"
    assert guard.judge(1, "FAILED x", "", ["x"], baseline=["failed x"])[0] == "FAIL"
    assert guard.judge(1, "FAILED x\nFAILED y", "", ["y"], baseline=["failed x"])[0] == "PASS"
    assert guard.judge(1, "FAILED x\nFAILED y", "", ["z"], baseline=["failed x"])[0] == "UGLY"
    assert guard.judge(1, "error", "", ["named"])[0] == "UGLY"
    assert guard.judge(1, "named it", "", ["named"])[0] == "PASS"


# 4. test_canaries_prove_the_judge
def test_canaries_prove_the_judge(tmp_path, fake_target, monkeypatch):
    parent = tmp_path / "parent"
    scratch = guard.init_scratch(parent / "run", fake_target, parent)
    guard.run_canaries(scratch)
    for stuck in ("PASS", "FAIL", "UGLY"):
        monkeypatch.setattr(guard, "judge", lambda *a, s=stuck, **k: (s, "stuck"))
        with pytest.raises(guard.HarnessInvalid, match="canary"):
            guard.run_canaries(scratch)


# 5. test_mutations_change_only_what_they_say
def test_mutations_change_only_what_they_say(tmp_path):
    led = tmp_path / "ledger.jsonl"
    led.write_bytes(b'{"n":0,"prev":"a"}\n{"n":1,"prev":"b"}\n{"n":2,"prev":"c"}\n')
    mutations_v1.apply_mutation(str(led), "reorder_lines")
    assert led.read_bytes() == b'{"n":1,"prev":"b"}\n{"n":0,"prev":"a"}\n{"n":2,"prev":"c"}\n'
    mutations_v1.apply_mutation(str(led), "duplicate_line")
    assert led.read_bytes().count(b"\r") == 0 and led.read_bytes().endswith(b'{"n":1,"prev":"b"}\n')
    mutations_v1.apply_mutation(str(led), "replace_first_prev")
    assert json.loads(led.read_bytes().splitlines()[0])["prev"] == "0" * 64
    cap = tmp_path / "c.sc.json"
    original = json.dumps({"scp_id": "x/y-v1", "declaration": {"intent": "hello world and more words"}}, indent=2)
    cap.write_bytes(original.encode("utf-8"))
    mutations_v1.apply_mutation(str(cap), "flip_byte_text")
    after = cap.read_bytes()
    assert after != original.encode() and json.loads(after)
    assert sum(a != b for a, b in zip(after, original.encode())) == 1
    mutations_v1.apply_mutation(str(cap), "none")
    assert cap.read_bytes() == after


# 6. test_wrong_key_is_base64_and_keeps_key_id
def test_wrong_key_is_base64_and_keeps_key_id(tmp_path):
    f = tmp_path / "s.json"
    f.write_text(json.dumps({"a": 1, "as_of": "2026-08-08T15:00:00Z",
                             "signature": {"key_id": "did:key:zKEEP", "algorithm": "Ed25519", "value": "AAAA"}}))
    mutations_v1.apply_mutation(str(f), "re_sign_wrong_key")
    sig = json.loads(f.read_text())["signature"]
    assert sig["key_id"] == "did:key:zKEEP" and len(base64.b64decode(sig["value"], validate=True)) == 64
    mutations_v1.apply_mutation(str(f), "json_edit_old_as_of")
    assert json.loads(f.read_text())["as_of"] == "2025-01-01T00:00:00Z"


# 7. test_end_to_end_on_a_fake_target
def test_end_to_end_on_a_fake_target(tmp_path, fake_target, capsys):
    threats = tmp_path / "threats"
    threats.mkdir()
    specs = {
        "01-caught.json": {"name": "flip caught", "target_file": "data.txt", "mutation": "reorder_lines",
                           "tool": "python verify.py", "expect_error_contains": ["data.txt"]},
        "02-silent.json": {"name": "silent tool", "target_file": "data.txt", "mutation": "reorder_lines",
                           "tool": "python silent.py", "expect_error_contains": ["data.txt"]},
        "03-missing.json": {"name": "missing file", "target_file": "nope.txt", "mutation": "flip_byte",
                            "tool": "python verify.py"},
    }
    for name, spec in specs.items():
        (threats / name).write_text(json.dumps(spec))
    parent = tmp_path / "parent"
    rc = saboteur_v1.main(["--target", str(fake_target), "--threats", str(threats), "--parent", str(parent)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "PASS 1  FAIL 1  UGLY 0  SKIP 1" in out
    assert (fake_target / "data.txt").read_bytes() == b"line one\nline two\n"
    one = saboteur_v1.main(["--target", str(fake_target), "--threats", str(threats), "--parent", str(parent),
                            "--only", "01"])
    assert one == 0


# 8. test_real_repo_touched_is_invalid
def test_real_repo_touched_is_invalid(tmp_path, fake_target):
    parent = tmp_path / "parent"
    initial = guard.pre_run(parent / "run", fake_target, parent)
    (fake_target / "data.txt").write_text("changed")
    with pytest.raises(guard.HarnessInvalid, match="real repo changed"):
        guard.post_run(fake_target, initial)
