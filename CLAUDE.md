# Forge Stack Context — The Saboteur

CLAUDE.md — Context briefing for AI assistants working in this repository.

## What this repo is
Tier 2 — The Saboteur. A fault-injection harness. It takes a fresh clone
of a target repo (e.g., `the-full-stack` or `scp-substrate`), applies
one mutation at a time to a scratch copy, runs the real tools against
it, and checks whether the tools fail loudly.

## The Discipline (non-negotiable)
1. **Red first, then fix.** A guard that fails to catch a mutation is
   logged as Ugly. We do not fix it until the Saboteur proves it is
   broken.
2. **Mutations are data, not code.** Every attack is a JSON spec in
   `threats/`. A new attack is a new file, not a new Python function.
3. **Layer fixes only.** If a target tool needs fixing, it is a NEW LAYER
   (e.g., `sign_v2.py`), never an edit to the frozen original.
4. **No network.** The harness runs entirely on local file copies.

## Pass/Fail Contract
- **Pass** = the tool exits non-zero AND names the problem.
- **Fail** = the tool exits zero, OR exits non-zero with a vague error.

A silent pass is the worst outcome. It is recorded as Ugly.

## Dual-Device Workflow
S24/Termux and laptop/VS Code. State is confirmed, never assumed. LF-only.
British English (-ise, artefact). Good/Bad/Ugly CHANGELOG, latest at top.
Header discipline on every file and function.
