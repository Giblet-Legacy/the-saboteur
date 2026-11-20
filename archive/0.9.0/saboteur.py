"""
saboteur.py — Fault-injection harness for the Forge Stack

Function:
    Takes a target repo, copies it to a scratch directory, applies one
    mutation from threats/*.json, runs the target tool from inside the
    scratch directory, and checks whether the tool failed loudly.

Tier:     Tier 2 — The Saboteur
Licence:  MSL-1.0
"""

import os
import sys
import json
import glob
import shutil
import subprocess
import tempfile
from pathlib import Path

import mutations

TARGET_REPO = Path("~/forge/the-full-stack").expanduser()
THREATS_DIR = Path("threats")
SCRATCH_DIR = Path("scratch")


def load_threats():
    threats = []
    for path in sorted(glob.glob(str(THREATS_DIR / "*.json"))):
        with open(path) as f:
            threats.append(json.load(f))
    return threats


def run_tool(tool_cmd, cwd):
    """Runs the shell command in cwd, returns (exit_code, stdout, stderr)."""
    # Split the command so we can pass cwd to subprocess
    result = subprocess.run(
        tool_cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def setup_scratch():
    """Cleans and re-populates the scratch directory from the target."""
    if SCRATCH_DIR.exists():
        shutil.rmtree(SCRATCH_DIR)
    shutil.copytree(TARGET_REPO, SCRATCH_DIR, symlinks=True)
    # Also copy our mutations.py into the scratch so tools that import it work
    # (Though the-full-stack has its own forge_core, not mutations.py)


def run_single_threat(threat):
    """Applies one threat and evaluates the tool's response."""
    setup_scratch()

    target_file = SCRATCH_DIR / threat["target_file"]
    if not target_file.exists() and threat["mutation"] != "delete":
        return "SKIP", f"target file missing: {threat['target_file']}"

    try:
        mutations.apply_mutation(str(target_file), threat["mutation"])
    except Exception as e:
        return "UGLY", f"mutation failed: {e}"

    exit_code, stdout, stderr = run_tool(threat["tool"], cwd=SCRATCH_DIR)
    combined = (stdout + "\n" + stderr).lower()

    # Evaluate the result
    if exit_code == 0:
        return "FAIL", "tool exited 0 (silent pass)"

    # It failed. Did it name the problem?
    expected_keywords = threat.get("expect_error_contains", [])
    if expected_keywords:
        if any(kw.lower() in combined for kw in expected_keywords):
            return "PASS", "exited non-zero, named the problem"
        else:
            return "UGLY", "exited non-zero, but error did not match expected keywords"

    return "PASS", "exited non-zero"


def main():
    print("=" * 60)
    print("🔍 THE SABOTEUR — Fault-Injection Run")
    print("=" * 60)

    threats = load_threats()
    print(f"Loaded {len(threats)} threats against {TARGET_REPO.name}\n")

    results = {"PASS": 0, "FAIL": 0, "UGLY": 0, "SKIP": 0}
    failures = []

    for i, threat in enumerate(threats, 1):
        name = threat.get("name", "unnamed")
        print(f"[{i:02d}/{len(threats)}] {name}...")
        status, reason = run_single_threat(threat)
        results[status] += 1

        if status == "PASS":
            print(f"       ✅ PASS ({reason})")
        elif status == "FAIL":
            print(f"       ❌ FAIL — SILENT PASS! ({reason})")
            failures.append((name, reason))
        elif status == "UGLY":
            print(f"       ⚠️  UGLY ({reason})")
            failures.append((name, reason))
        else:
            print(f"       ⏭  SKIP ({reason})")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  PASS: {results['PASS']}")
    print(f"  FAIL: {results['FAIL']}")
    print(f"  UGLY: {results['UGLY']}")
    print(f"  SKIP: {results['SKIP']}")

    if failures:
        print("\nProblems found:")
        for name, reason in failures:
            print(f"  - {name}: {reason}")

    return 0 if results["FAIL"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
