"""
test_harness_guard.py — Proof that the harness is honest.

Function:
    Five deliberate breakages. Each must abort with HarnessInvalid
    (which maps to exit code 2 in the CLI). If any of them doesn't
    abort, step 0 isn't done and no threat results can be trusted.

Tier:     Tier 2 — The Saboteur (harness precondition)
Licence:  MSL-1.0
"""

import os
import pathlib
import sys
import tempfile
import pytest

HERE = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(HERE))

import harness_guard


@pytest.fixture
def scratch_dir(tmp_path):
    """A scratch directory with the marker, under HOME/forge by default."""
    # Use a path under HOME/forge so _guard_scratch_path accepts it
    parent = pathlib.Path.home() / "forge"
    parent.mkdir(exist_ok=True)
    d = parent / f".saboteur-test-{os.getpid()}-{id(tmp_path)}"
    yield d
    import shutil
    if d.exists():
        shutil.rmtree(d)


@pytest.fixture
def fake_repo(tmp_path):
    """A minimal repo tree with one file."""
    repo = tmp_path / "fake_repo"
    repo.mkdir()
    (repo / "README.md").write_text("test repo\n")
    (repo / "main.py").write_text("print('hi')\n")
    return repo


# ── Breakage 1: wrong tree ──────────────────────────────────────────────
def test_breakage_1_wrong_tree(scratch_dir, fake_repo):
    """Running a tool from outside scratch must raise HarnessInvalid."""
    harness_guard.pre_run(scratch_dir, fake_repo)
    # Try to invoke a tool that lives in the real repo, not scratch
    real_tool = fake_repo / "main.py"
    with pytest.raises(harness_guard.HarnessInvalid, match="tool not under scratch"):
        harness_guard.per_invocation(real_tool, scratch_dir)


# ── Breakage 2: judgement stuck on PASS ─────────────────────────────────
def test_breakage_2_stuck_on_pass(monkeypatch, scratch_dir, fake_repo):
    """If the pipeline always returns PASS, the silent canary must catch it."""
    original = harness_guard._judge_tool
    monkeypatch.setattr(harness_guard, "_judge_tool", lambda rc, o, e, k=None: "PASS")
    with pytest.raises(harness_guard.HarnessInvalid, match="canary canary_silent.py"):
        harness_guard.pre_run(scratch_dir, fake_repo)
    monkeypatch.setattr(harness_guard, "_judge_tool", original)


# ── Breakage 3: judgement stuck on FAIL ─────────────────────────────────
def test_breakage_3_stuck_on_fail(monkeypatch, scratch_dir, fake_repo):
    """If the pipeline always returns FAIL, the loud canary must catch it."""
    monkeypatch.setattr(harness_guard, "_judge_tool", lambda rc, o, e, k=None: "FAIL")
    with pytest.raises(harness_guard.HarnessInvalid, match="canary canary_loud.py"):
        harness_guard.pre_run(scratch_dir, fake_repo)


# ── Breakage 4: real repo touched during run ────────────────────────────
def test_breakage_4_real_repo_touched(scratch_dir, fake_repo):
    """If the real repo changes during the run, post_run must catch it."""
    initial = harness_guard.pre_run(scratch_dir, fake_repo)
    # Simulate a mutation of the real repo
    (fake_repo / "main.py").write_text("print('changed')\n")
    with pytest.raises(harness_guard.HarnessInvalid, match="real repo changed"):
        harness_guard.post_run(fake_repo, initial)


# ── Breakage 5: scratch path without marker ─────────────────────────────
def test_breakage_5_no_marker(tmp_path):
    """A scratch path without the marker must be refused."""
    parent = pathlib.Path.home() / "forge"
    parent.mkdir(exist_ok=True)
    decoy = parent / ".saboteur-decoy-no-marker"
    decoy.mkdir()
    try:
        with pytest.raises(harness_guard.HarnessInvalid, match="marker missing"):
            harness_guard._guard_scratch_path(decoy)
    finally:
        decoy.rmdir()
