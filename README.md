# the-saboteur — Tier 2: The Saboteur

README.md — repository purpose and contract for The Saboteur.

Function:
    A fault-injection harness for the Forge Stack. It applies one
    mutation at a time to a scratch copy of a target repo, runs the real
    tools against it, and proves whether the tools fail loudly.

Tier:     Tier 2 — The Saboteur (Adversarial Testing)
Depends:  The Legacy layers it attacks (siblings, or FORGE_LEGACY_ROOT)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
Status:   1.0.0 (frozen 2026-11-20; the 0.9.0 consolidation)

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

## 1.1.0-dev: rotation (2026-11-20)

    python saboteur_v1_1.py                 # this 6-hour slot: 250 of the 1000 (every 4th)
    python saboteur_v1_1.py --slot 2        # a chosen slot
    python saboteur_report_v1_1.py --write  # yesterday's report -> results/<day>/report.md

The four slots of a day cover all 1000 threats. A slot is RED only for
something new: a new failure, any UGLY or SKIP, or a known gap that
starts passing (`known_gaps_v1_1.json`). See SPEC_V1_1.md.

## 1.0.0 (frozen 2026-11-20): one version, the same 1000 attacks

    python saboteur_v1.py                   # 1000 threats against fixture_v1/, inside the run lock
    python saboteur_v1.py --only 08         # 0800–0899
    python -m pytest -q                     # 65 tests (archive/ is never collected)

1.0.0 consolidates the 0.9.0 chain (CONSOLIDATION_V1.md, SPEC_V1.md). It
has one module of each kind, `saboteur_v1`, `mutations_v1` and
`harness_guard_v1`, and nothing is swapped at run time. It does exactly
what 0.9.0 did, with the same verdict on every threat:

- `fixture_v1/` is the same fixture;
- `threats_v1/` holds the same 1000 threats;
- 154 are red, in 7 gap classes (SPEC_V1.md §6).

Every older file is in `archive/0.9.0/`, byte-identical. To run an old
version, use a worktree of the tag `v0.9.0`: archived layers import
their siblings, so they don't run from `archive/`. Next is rotation, in
1.1.0 (CONSOLIDATION_V1.md §8).

## 0.9.0 (frozen 2026-11-20): 1000 threats, the known gaps mapped

    python saboteur_v0_9.py                 # 1000 threats, inside the run lock
    python saboteur_v0_9.py --only 08       # 0800–0899

0.8.0 added substitution: a valid signed file copied over another
(SPEC_V0_8.md). 0.9.0's 200 new threats map every known gap class
(SPEC_V0_9.md §4): 154 threats are red. Next is the 1.0.0
consolidation (CONSOLIDATION_V1.md), then rotation in 1.1.0.

## 0.7.0 (frozen 2026-11-20): 400 threats

    python saboteur_v0_7.py                 # 400 threats, inside the run lock
    python saboteur_v0_7.py --only 2        # 200–299

`threats_v0_7/` is the 200 threats of 0.6.0 plus 200 new ones, mostly
type confusion. No layer raised on any of them. Three new gaps:
substrate's unsigned `created_at` (324, 325) and a record whose lines
were swapped (383, meaning unchanged). See SPEC_V0_7.md §3.

## 0.6.0 (frozen 2026-11-20): 200 threats

    python saboteur_v0_6.py                 # 200 threats, inside the run lock
    python saboteur_v0_6.py --only 1        # 100–199

`threats_v0_6/` is the 108 threats of 0.5.0 plus 92 new ones, against
the same fixture. First run: PASS 191, FAIL 9. The ninth gap is new: the
store accepts a stored record with a trailing space (SPEC_V0_6.md §3).

## 0.5.1 (frozen 2026-11-20): one run at a time

    python saboteur_v0_5_1.py               # 0.5.0's run, inside a lock

Every run uses the same scratch folder, so two at once spoil each
other's results. 0.5.1 takes `%TEMP%\forge-saboteur\saboteur.lock`
first. A second run refuses (exit 2) and names the run holding it.
SPEC_V0_5_1.md.

## 0.5.0 (frozen 2026-11-20): 108 attacks on the Legacy's own layers (2026-11-20)

    python saboteur_v0_5.py                 # 108 threats against fixture_v0_5/
    python saboteur_v0_5.py --only 09       # 091–099 (the HAL seals)
    python -m pytest -q tests

`fixture_v0_5/` is a small Legacy world made by the real layers with
throwaway keys. Its `legacy_check_v0_5.py` asks each layer about each
file. Each threat changes one thing in a scratch copy and passes only
when the right layer says no, by name.

First run: PASS 100, FAIL 8. The eight are real gaps, recorded and not
yet fixed (SPEC_V0_5.md §7): ledger and store rollback, a duplicate key
in a record, and four substrate rows that are not tied to their owner.

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
