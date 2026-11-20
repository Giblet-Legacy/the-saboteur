"""
harness_guard_v1.py — Preconditions for a trustworthy Saboteur run, 1.0.0

Function:
    harness_guard_v2.py (archive/0.9.0, SPEC_V2.md §2) brought forward
    unchanged under the 1.0.0 consolidation (CONSOLIDATION_V1.md): the
    code below the header is v2's, byte for byte. It keeps:

      - the scratch parent, passed in (default: the system temp folder);
      - the refusal of an existing directory without the marker;
      - judge(), the one differential judgement (a traceback is a crash,
        UGLY; a tool already failing on a clean copy passes a threat only
        with a NEW failure line);
      - five canaries (harness_canaries/) that prove judge() first.

Public API:
    1. HarnessInvalid
    2. guard_scratch(scratch, parent)
    3. init_scratch(scratch, repo_root, parent) -> Path
    4. repo_hash(repo_root) -> str
    5. judge(returncode, stdout, stderr, keywords=None, baseline=None) -> (verdict, reason)
    6. run_canaries(scratch)
    7. pre_run(scratch, repo_root, parent) -> initial hash
    8. per_invocation(cwd, scratch)
    9. post_run(repo_root, initial_hash)

Internal helpers:
    10. _lines — the non-empty, lower-cased lines of a tool's output

Tier:     Tier 2 — The Saboteur (harness precondition), 1.0.0
Depends:  standard library only
Spec:     SPEC_V1.md 1.0.0
Version:  1.0.0-dev
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

MARKER = ".saboteur-scratch"
DEFAULT_PARENT = pathlib.Path(tempfile.gettempdir()) / "forge-saboteur"
CANARIES = pathlib.Path(__file__).resolve().parent / "harness_canaries"


# ---------------------------------------------------------------------------
# 1. HarnessInvalid
# ---------------------------------------------------------------------------
class HarnessInvalid(Exception):
    """A harness precondition failed. Callers exit 2: nothing reported can be trusted."""


# ---------------------------------------------------------------------------
# 2. guard_scratch
#    The guard on every rmtree. Absolute, strictly under parent, never
#    parent / home / a root, and carrying the marker.
# ---------------------------------------------------------------------------
def guard_scratch(scratch, parent=DEFAULT_PARENT):
    try:
        resolved = pathlib.Path(scratch).resolve()
        top = pathlib.Path(parent).resolve()
    except (OSError, RuntimeError) as e:
        raise HarnessInvalid(f"cannot resolve scratch path {scratch!r}: {e}")
    if resolved == top:
        raise HarnessInvalid(f"scratch path is the parent itself: {resolved}")
    if top not in resolved.parents:
        raise HarnessInvalid(f"scratch not under {top}: {resolved}")
    if resolved in (pathlib.Path.home().resolve(), pathlib.Path(resolved.anchor)):
        raise HarnessInvalid(f"scratch path is a dangerous location: {resolved}")
    if not (resolved / MARKER).exists():
        raise HarnessInvalid(f"scratch marker missing: {resolved / MARKER}")
    return resolved


# ---------------------------------------------------------------------------
# 3. init_scratch
#    Wipe a marked scratch (after the guard), refuse an unmarked one that
#    has anything in it, then copy repo_root in (without .git).
# ---------------------------------------------------------------------------
def init_scratch(scratch, repo_root, parent=DEFAULT_PARENT):
    scratch = pathlib.Path(scratch)
    if scratch.exists():
        if (scratch / MARKER).exists():
            shutil.rmtree(guard_scratch(scratch, parent))
        elif any(scratch.iterdir()):
            raise HarnessInvalid(f"scratch exists, is not empty and has no marker: {scratch}")
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / MARKER).write_text("saboteur-scratch\n", encoding="utf-8")
    guard_scratch(scratch, parent)
    for item in pathlib.Path(repo_root).iterdir():
        if item.name in (".git", MARKER):
            continue
        dest = scratch / item.name
        if item.is_dir():
            shutil.copytree(item, dest, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        else:
            shutil.copy2(item, dest)
    return scratch.resolve()


# ---------------------------------------------------------------------------
# 4. repo_hash
# ---------------------------------------------------------------------------
def repo_hash(repo_root):
    root = pathlib.Path(repo_root)
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or "__pycache__" in path.parts or not path.is_file():
            continue
        h.update(str(path.relative_to(root)).replace(os.sep, "/").encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 10. _lines
# ---------------------------------------------------------------------------
def _lines(text):
    return [ln.strip().lower() for ln in text.splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# 5. judge
#    SPEC_V2 §3. Pass = exits non-zero AND shows a new failure line that
#    names the problem. baseline: the output lines of the same tool on
#    an unmutated copy (None when the clean run exited 0).
# ---------------------------------------------------------------------------
def judge(returncode, stdout, stderr, keywords=None, baseline=None):
    if returncode == 0:
        return "FAIL", "tool exited 0 (silent pass)"
    lines = _lines(stdout + "\n" + stderr)
    if any(ln.startswith("traceback (most recent call last)") for ln in lines):
        return "UGLY", "tool crashed with a traceback (a crash is not a named error)"
    new = [ln for ln in lines if ln not in set(baseline or [])] if baseline is not None else lines
    if not new:
        return "FAIL", "nothing new: the tool already fails this way on a clean copy"
    if keywords:
        hit = next((kw for kw in keywords if any(kw.lower() in ln for ln in new)), None)
        if hit is None:
            return "UGLY", "exited non-zero, but no new line named the problem"
        return "PASS", f"exited non-zero and named it ({hit!r})"
    return "PASS", "exited non-zero with a new failure line"


# ---------------------------------------------------------------------------
# 6. run_canaries
#    Each canary through judge(); any wrong verdict invalidates the run.
# ---------------------------------------------------------------------------
def run_canaries(scratch):
    dest = pathlib.Path(scratch) / "_canaries"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(CANARIES, dest)
    keywords = ["refused", "canary"]
    specs = [
        ("canary_silent.py", "FAIL", None),
        ("canary_loud.py", "PASS", None),
        ("canary_vague.py", "UGLY", None),
        ("canary_crash.py", "UGLY", None),
        ("canary_same.py", "FAIL", ["canary: refused, reason=test"]),
    ]
    for name, expected, baseline in specs:
        r = subprocess.run([sys.executable, str(dest / name)], cwd=str(scratch),
                           capture_output=True, text=True, timeout=10)
        verdict, _ = judge(r.returncode, r.stdout, r.stderr, keywords, baseline)
        if verdict != expected:
            raise HarnessInvalid(f"canary {name}: expected {expected}, got {verdict} "
                                 f"(rc={r.returncode}, out={r.stdout!r}, err={r.stderr!r})")


# ---------------------------------------------------------------------------
# 7. pre_run
# ---------------------------------------------------------------------------
def pre_run(scratch, repo_root, parent=DEFAULT_PARENT):
    initial = repo_hash(repo_root)
    made = init_scratch(scratch, repo_root, parent)
    run_canaries(made)
    return initial


# ---------------------------------------------------------------------------
# 8. per_invocation
#    Every tool runs from inside the scratch copy, never the real repo.
# ---------------------------------------------------------------------------
def per_invocation(cwd, scratch):
    where, top = pathlib.Path(cwd).resolve(), pathlib.Path(scratch).resolve()
    if where != top and top not in where.parents:
        raise HarnessInvalid(f"tool not run from scratch: {where} (scratch={top})")
    if not (top / MARKER).exists():
        raise HarnessInvalid(f"scratch marker missing at run time: {top}")


# ---------------------------------------------------------------------------
# 9. post_run
# ---------------------------------------------------------------------------
def post_run(repo_root, initial_hash):
    current = repo_hash(repo_root)
    if current != initial_hash:
        raise HarnessInvalid(f"real repo changed during run: before={initial_hash[:16]}, after={current[:16]}")
