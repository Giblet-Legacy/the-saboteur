"""
test_saboteur_v0_5_1_at_v1.py — test_saboteur_v0_5_1.py (archive/0.9.0) carried forward against the Saboteur 1.0.0

Function:
    CONSOLIDATION_V1.md §3.2. The live tests of the archived suite
    archive/0.9.0/tests/test_saboteur_v0_5_1.py, run against the 1.0.0 modules
    (saboteur_v1, mutations_v1, harness_guard_v1, fixture_v1,
    threats_v1). Step 0 decided which tests carry (§3.1).

Functions in this file (pytest-collected):
    1. test_alive_knows_this_process_and_a_finished_one
    2. test_second_run_is_refused_while_a_run_holds_the_lock
    3. test_stale_lock_is_taken_over
    4. test_fresh_unreadable_lock_is_respected
    5. test_old_unreadable_lock_is_taken_over
    6. test_lock_is_released_when_the_run_raises
    7. test_release_leaves_another_runs_lock
    8. test_end_to_end_run_takes_and_releases_the_lock
    9. test_two_real_runs_cannot_clash

Tier:     Tier 2 — The Saboteur, 1.0.0
Spec:     SPEC_V1.md 1.0.0
Version:  1.0.0-dev
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import pathlib
import subprocess
import sys
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("FORGE_LEGACY_ROOT", str(HERE.parent))

import saboteur_v1  # noqa: E402
import saboteur_v1 as s  # noqa: E402


# 10. _dead_pid
def _dead_pid():
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


# 11. _hold
def _hold(parent, pid):
    lock = pathlib.Path(parent) / s.LOCK_NAME
    lock.write_text(json.dumps({"pid": pid, "started": "2026-11-20T00:00:00Z"}) + "\n", encoding="utf-8")
    return lock


# 1
def test_alive_knows_this_process_and_a_finished_one():
    assert s._alive(os.getpid())
    assert not s._alive(_dead_pid())
    assert not s._alive(0) and not s._alive(None)


# 2
def test_second_run_is_refused_while_a_run_holds_the_lock(tmp_path, capsys):
    holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        lock = _hold(tmp_path, holder.pid)
        assert s.main(["--parent", str(tmp_path), "--only", "001"]) == 2
        err = capsys.readouterr().err
        assert f"pid {holder.pid}" in err and "run one at a time" in err
        assert json.loads(lock.read_text(encoding="utf-8"))["pid"] == holder.pid  # untouched
        assert not (tmp_path / "run").exists()  # its scratch was never touched
    finally:
        holder.kill()
        holder.wait()


# 3
def test_stale_lock_is_taken_over(tmp_path):
    _hold(tmp_path, _dead_pid())
    lock = s.acquire(tmp_path)
    assert json.loads(lock.read_text(encoding="utf-8"))["pid"] == os.getpid()
    assert s.release(lock) and not lock.exists()


# 4
def test_fresh_unreadable_lock_is_respected(tmp_path):
    (tmp_path / s.LOCK_NAME).write_bytes(b"")
    with pytest.raises(s.Locked):
        s.acquire(tmp_path)


# 5
def test_old_unreadable_lock_is_taken_over(tmp_path):
    lock = tmp_path / s.LOCK_NAME
    lock.write_bytes(b"")
    old = time.time() - s.UNREADABLE_GRACE_S - 5
    os.utime(lock, (old, old))
    assert s.acquire(tmp_path) == lock
    s.release(lock)


# 6
def test_lock_is_released_when_the_run_raises(tmp_path, monkeypatch):
    def boom(argv):
        assert (tmp_path / s.LOCK_NAME).exists()
        raise RuntimeError("run failed")
    monkeypatch.setattr(saboteur_v1, "_run_all", boom)
    with pytest.raises(RuntimeError):
        s.main(["--parent", str(tmp_path)])
    assert not (tmp_path / s.LOCK_NAME).exists()


# 7
def test_release_leaves_another_runs_lock(tmp_path):
    lock = _hold(tmp_path, os.getpid() + 1_000_000)
    assert not s.release(lock)
    assert lock.exists()


# 8
def test_end_to_end_run_takes_and_releases_the_lock(tmp_path):
    assert s.main(["--parent", str(tmp_path), "--only", "0001"]) == 0
    assert not (tmp_path / s.LOCK_NAME).exists()


# 9
def test_two_real_runs_cannot_clash(tmp_path):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    cmd = [sys.executable, str(HERE / "saboteur_v1.py"), "--parent", str(tmp_path), "--only", "000"]
    first = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8")
    try:
        deadline = time.time() + 30
        while not (tmp_path / s.LOCK_NAME).exists() and time.time() < deadline:
            time.sleep(0.05)
        second = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
        assert second.returncode == 2
        assert f"pid {first.pid}" in second.stderr
    finally:
        out, _ = first.communicate(timeout=300)
    assert first.returncode == 0, out
    assert "PASS 9" in out
    assert not (tmp_path / s.LOCK_NAME).exists()
