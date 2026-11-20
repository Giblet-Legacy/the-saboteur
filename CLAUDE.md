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

## 0.5.1 (frozen 2026-11-20)
Run `python saboteur_v0_5_1.py` (SPEC_V0_5_1.md): 0.5.0 inside a lock,
`<parent>/saboteur.lock`. Every run shares `<parent>/run`, so two at
once corrupt each other. Never stop a Saboteur process you did not start.
If a run is refused, someone else's run is going: wait for it.

## 0.5.0 (frozen 2026-11-20)
Run `python saboteur_v0_5.py` (SPEC_V0_5.md).

- **Target:** `fixture_v0_5/`, built by `build_fixture_v0_5.py` with the
  real layers and throwaway keys. Never ~/.forge: it holds James's key.
- **Tool:** `legacy_check_v0_5.py --layer X`.
- **Threats:** 108 in `threats_v0_5/`.
- **Mutations:** `mutations_v0_5.py`, which falls through to v2.
- **Adding an attack:** write a new threat file using a parametrised
  mutation (json_set, sqlite, line_set and so on). A mutation that
  changes nothing must raise, so the harness reports it as SKIP and
  never as a pass.
- **Rebuilding the fixture** changes every signature. Do it only when a
  layer's format changes.

## 0.4.0 (2026-11-18)
the-full-stack is reference only, never a target or a layer (James,
2026-11-18). Run `python saboteur_v0_4.py --target DIR` (SPEC_V0_4.md): no
default target, the-full-stack refused, threats in `threats_v0_4/`
(written against the Legacy's own layers). v2 and threats_v2/ are
history, never edited.

## v2 (2026-11-15)
`saboteur_v2.py`, `harness_guard_v2.py`, `mutations_v2.py` and
`threats_v2/` (SPEC_V2.md) are the layer over v1, which is never edited.
Run `python saboteur_v2.py`. Rules learned from the v1 audit:
- **A threat is judged against a clean baseline.** A tool that already
  fails on an unmutated copy proves nothing unless the mutation adds a
  new failure line that names the problem.
- **Never sign with the owner's key.** Tools run with `FORGE_KEY_PATH`
  set to a throwaway key in the scratch copy.
- **Scratch only through the guard**, under the system temp directory;
  tests use tmp_path, never the home folder.
- **No catch-all keywords** ("fail") in `expect_error_contains`.
- Findings in a target repo are reported here; fixing them is a new
  layer in that repo, after James decides.
