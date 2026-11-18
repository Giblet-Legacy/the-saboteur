# the-saboteur — Tier 2: The Saboteur

README.md — repository purpose and contract for The Saboteur.

Function:
    A fault-injection harness for the Forge Stack. It applies one
    mutation at a time to a scratch copy of a target repo, runs the real
    tools against it, and proves whether the tools fail loudly.

Tier:     Tier 2 — The Saboteur (Adversarial Testing)
Depends:  A target repo (e.g., the-full-stack, scp-substrate)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
Status:   0.1.0-dev (in build, pre-freeze)

## The Challenge
Build a harness that attacks our own stack and proves every tool fails
loudly. The goal is to find the next silent pass before it bites us in
production.

## How it works
1. Copy the target repo to a scratch directory.
2. Apply one mutation (from `threats/*.json`).
3. Run a specific tool against the mutated copy.
4. Check the exit code and the error message.
5. Log the result (Pass / Fail / Ugly) in a Good/Bad/Ugly report.
6. Reset the scratch copy for the next mutation.

## The Mutation Library (minimum 12)
- Flip one byte in a signed capsule
- Convert LF to CRLF in an artefact with a .sig
- Delete a .sig but keep the artefact
- Reorder two ledger rows
- Truncate the ledger mid-row
- Break the root anchor in a consumer ledger
- Put back a `COMPUTE-ON-FREEZE` placeholder
- Use an empty `scp_id`
- Use a fractional number instead of a decimal string
- Feed a past-TTL score file to `hal.py`
- Sign a score file with the wrong key
- Duplicate attestation

## Levels
- **L1:** 12 mutations, all caught or logged as Ugly.
- **L2:** Runs from `the-legacy` as a "Nerves" panel (live health grid).
- **L3 (boss):** An independent Node verifier that agrees with the
  Python verifier byte-for-byte on 50 test vectors. Proves whether
  `forge-c14n-1` is a real spec.

## Win condition
Find at least one real silent pass in the current tools.

## 0.4.0: no default target (2026-11-18)

James: "the forge stack was for reference only and not meant to be a
layer involved in the legacy program." `saboteur_v0_4.py` (SPEC_V0_4.md) is
v2's harness with `--target` required and the-full-stack refused:

    python saboteur_v0_4.py --target ../ledger-layer     # threats from threats_v0_4/

`threats_v0_4/` is empty until threats are written against the Legacy's
own layers. The v2 section below is history: its 15 threats ran
the-full-stack's tools.

## v2: the honest harness (2026-11-15)

v1 (`saboteur.py`) is kept as it was, but its "12/12 PASS" is withdrawn
(CHANGELOG). Run v2:

    python saboteur_v2.py                      # attacks ../the-full-stack
    python saboteur_v2.py --target ../scp-substrate --threats my_threats
    python saboteur_v2.py --only 03            # one threat
    python -m pytest -q tests                  # the harness proves itself

On the phone, from the folder that holds the repos:

    cd the-saboteur && git pull && python -m pytest -q tests && python saboteur_v2.py

v2 proves the harness first (five canaries), copies the target into a
guarded scratch folder under the system temp directory, runs each tool
on the clean copy and again after one mutation, and passes a threat
only if the mutated run shows a NEW failure line that names the
problem. Tools run with a throwaway key, never yours. Exit 0: every
threat passed; 1: a FAIL, UGLY or SKIP; 2: the harness is invalid.
Threats are in `threats_v2/` (SPEC_V2.md §5).

Status: 0.3.0-dev (VERSION). First honest run: PASS 7, FAIL 1, UGLY 4.

Retired threats (old-tool gaps, kept as evidence) are in
`threats_v2/retired/` (2026-11-15); the main run no longer loads them.
