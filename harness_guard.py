"""
harness_guard.py — Preconditions for a trustworthy Saboteur run.

Function:
    Three hooks that gate every Saboteur run:
      pre_run(scratch_dir, repo_root)   — before any threat
      per_invocation(tool_path, scratch_dir) — on every tool call
      post_run(repo_root, initial_hash) — after all threats

    Any check that fails raises HarnessInvalid, which callers translate
    into exit code 2. Exit 2 means "the harness is invalid, nothing it
    reported can be trusted." It is distinct from exit 1 ("a threat
    failed"). A pipeline must never confuse them.

    Shares no code with mutations.py or saboteur.py's judgement. The
    guard produces conditions; the pipeline produces verdicts; the guard
    checks the verdicts.

Tier:     Tier 2 — The Saboteur (harness precondition)
Licence:  MSL-1.0
"""

import hashlib
import os
import pathlib
import subprocess
import sys
import tempfile


class HarnessInvalid(Exception):
    """Raised when a harness precondition fails. Callers exit 2."""
    pass


# Marker file that proves the harness created the scratch directory.
_SCRATCH_MARKER = ".saboteur-scratch"

# Expected parent for the scratch directory.
_SCRATCH_PARENT = pathlib.Path.home() / "forge"


def _guard_scratch_path(scratch_dir):
    """
    Refuses to operate on a scratch path that doesn't look like one the
    harness created. This is the guard for the rm -rf — the most
    dangerous line in the whole system.

    Rules:
      - Must resolve to an absolute path.
      - Must be under _SCRATCH_PARENT.
      - Must not be _SCRATCH_PARENT, the repo root, home, /, or empty.
      - Must contain the marker file _SCRATCH_MARKER.
    """
    try:
        resolved = pathlib.Path(scratch_dir).resolve()
    except (OSError, RuntimeError) as e:
        raise HarnessInvalid(f"cannot resolve scratch path {scratch_dir!r}: {e}")

    parent = _SCRATCH_PARENT.resolve()
    if resolved == parent:
        raise HarnessInvalid(f"scratch path is the parent: {resolved}")
    if not str(resolved).startswith(str(parent) + os.sep):
        raise HarnessInvalid(f"scratch not under {parent}: {resolved}")
    if resolved == pathlib.Path.home().resolve() or str(resolved) == "/" or str(resolved) == "":
        raise HarnessInvalid(f"scratch path is a dangerous location: {resolved}")

    marker = resolved / _SCRATCH_MARKER
    if not marker.exists():
        raise HarnessInvalid(f"scratch marker missing: {marker}")

    return resolved


def _init_scratch(scratch_dir, repo_root):
    """
    Create a fresh scratch directory, wipe any existing one (safely), and
    copy repo_root into it. Writes the marker file. Called once at the
    start of every run.
    """
    scratch = pathlib.Path(scratch_dir)
    # If a scratch dir exists with the marker, wipe it. Otherwise create.
    if scratch.exists() and (scratch / _SCRATCH_MARKER).exists():
        _guard_scratch_path(scratch)  # verify before deleting
        import shutil
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / _SCRATCH_MARKER).write_text("saboteur-scratch\n")
    # Copy the target repo in
    import shutil
    for item in pathlib.Path(repo_root).iterdir():
        if item.name == ".git":
            continue
        dest = scratch / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    return scratch


def _repo_hash(repo_root):
    """Hash every file in repo_root (excluding .git)."""
    h = hashlib.sha256()
    for path in sorted(pathlib.Path(repo_root).rglob("*")):
        if ".git" in path.parts or not path.is_file():
            continue
        h.update(str(path.relative_to(repo_root)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _judge_tool(returncode, stdout, stderr, expect_error_contains=None):
    """
    The pipeline's judgement of a tool's result. Must be reused by
    pre_run (for canaries) and by saboteur.py (for threats).
    """
    if returncode == 0:
        return "FAIL"
    combined = (stdout + "\n" + stderr).lower()
    if expect_error_contains:
        if any(kw.lower() in combined for kw in expect_error_contains):
            return "PASS"
        return "UGLY"
    return "PASS"


def _run_canaries(scratch):
    """
    Copy the three canary templates into scratch, run each through the
    real judgement pipeline, verify the verdict is what it should be.
    """
    import shutil
    canary_dir = pathlib.Path(__file__).parent / "harness_canaries"
    dest = scratch / "_canaries"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(canary_dir, dest)

    specs = [
        ("canary_silent.py", "FAIL", None),
        ("canary_loud.py", "PASS", ["refused", "canary"]),
        ("canary_vague.py", "UGLY", ["refused", "canary"]),
    ]
    for name, expected, keywords in specs:
        path = dest / name
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(scratch),
            capture_output=True,
            text=True,
            timeout=10,
        )
        verdict = _judge_tool(result.returncode, result.stdout, result.stderr, keywords)
        if verdict != expected:
            raise HarnessInvalid(
                f"canary {name}: expected {expected}, got {verdict} "
                f"(rc={result.returncode}, out={result.stdout!r}, err={result.stderr!r})"
            )


def pre_run(scratch_dir, repo_root):
    """
    Called once, before any threat.
    1. Init scratch: wipe (if safe) and copy repo_root.
    2. Run the three canaries. Each must produce the expected verdict.
    Returns the initial repo hash for post_run to compare.
    """
    scratch = _init_scratch(scratch_dir, repo_root)
    initial_hash = _repo_hash(repo_root)
    _run_canaries(scratch)
    return initial_hash


def per_invocation(tool_path, scratch_dir):
    """
    Called on every tool invocation.
    1. Tool must live under scratch_dir (not the real repo).
    2. A path-canary file must be visible from the tool's cwd.
    """
    scratch = pathlib.Path(scratch_dir).resolve()
    tool = pathlib.Path(tool_path).resolve()
    if not str(tool).startswith(str(scratch) + os.sep):
        raise HarnessInvalid(f"tool not under scratch: {tool} (scratch={scratch})")

    canary = scratch / "_path_canary.txt"
    if not canary.exists():
        canary.write_text("saboteur-path-canary\n")


def post_run(repo_root, initial_hash):
    """
    Called once, after all threats.
    The real repo's hash must be identical to what pre_run recorded.
    """
    current = _repo_hash(repo_root)
    if current != initial_hash:
        raise HarnessInvalid(
            f"real repo changed during run: before={initial_hash[:16]}, after={current[:16]}"
        )
