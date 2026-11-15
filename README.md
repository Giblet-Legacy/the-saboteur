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
