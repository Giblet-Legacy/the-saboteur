# CHANGELOG — the-saboteur (Tier 2: The Saboteur)

CHANGELOG.md — build history for The Saboteur, latest entry at top.
(The v1.0.0 entry below sits above the original title; it is kept as
written. Entries from here on go at the top.)

## [v0.5.0] — 2026-11-20 — frozen

### Good
- Frozen (James: "freeze commit push"). VERSION 0.5.0-dev -> 0.5.0.
  Headers say `0.5.0 (frozen 2026-11-20)`.
- Tests: 31/31. Full run: PASS 100, FAIL 8, UGLY 0, SKIP 0.
- The committed fixture, exported fresh from git, is byte-identical and
  passes its 17 checks.

### Bad
- The eight red threats stand (SPEC_V0_5 §7). Each fix is a new layer in
  its repository, when James decides.
- The VPS check runs the Saboteur's tests, not a 0.5.0 run.

### Ugly
- No ugly items.

## [v0.5.0-dev] — 2026-11-20 — 108 threats against the Legacy's own layers

### Good
- James: "yes lets a a ton more". `saboteur_v0_5.py` (SPEC_V0_5.md) runs
  v2's harness, unchanged, against `fixture_v0_5/`: a small Legacy world
  built by the real layers (`build_fixture_v0_5.py`) and signed with
  throwaway keys. Only public did:keys are kept. The world holds a
  ledger, capsules, frozen capsules, records, signed documents, attested
  HAL seals, a store and a substrate.
- `legacy_check_v0_5.py` hands each file to its layer and prints which
  layer said no.
- `mutations_v0_5.py` adds line and byte attacks, parametrised attacks
  (json_set, json_drop, duplicate keys, line_set, sqlite) and forgeries
  made with a fresh attacker key, so a new attack is a new threat file.
- 108 threats in `threats_v0_5/`, numbered by layer: ledger_v2,
  canon_verify_v2, genesis_v3, store_v2_1, sign_v2, freeze_v2,
  record_v2, hal_v2 and substrate_v4.
- First run: PASS 100, FAIL 8, UGLY 0, SKIP 0, real repo unchanged.
- No layer raised where its spec says it never raises.
- Tests: `tests/test_saboteur_v0_5.py` (13). With the frozen suites,
  31/31.

### Bad
- Eight red threats, each a real gap, logged red first (SPEC_V0_5 §7).
  Fixing them is a new layer in that repository, when James says.
  - **Rollback** (011, 030, 043): dropping the last ledger or store
    entry leaves a valid chain. Nothing remembers the head.
  - **Duplicate key** (073): record_v2 accepts a hidden duplicate key in
    a record.
  - **Self-certifying rows** (103, 104): substrate_v4 accepts a row
    re-signed by another key. It proves integrity, not authorship.
  - **Deleted row** (107): substrate_v4 does not notice a deleted
    entity.
  - **Unsigned lookup key** (108): substrate_v4's `name_key` is not
    signed.
- The tests were written after the code, not run red first.
- The VPS check still runs only the Saboteur's tests, not a 0.5.0 run.

### Ugly
- **v2's `flip_byte_text` could not flip any fixture file.** It starts
  mid-file, often inside a string, so it saw only the gaps between
  strings. It also parses a .jsonl as one JSON document.
  - v2 is frozen. 0.5.0 uses its own `flip_letter`.
  - The green of v2's threat 01 depended on where the middle of that
    file fell.
- **v2's `replace_first_prev` cannot break a genesis.** It sets prev to
  the zero anchor, which a genesis already has.
  - The first 0.5.0 run had three silent "passes" from it: 007, 028
    and 038.
  - 0.5.0 uses `line_set`, which refuses a mutation that changes
    nothing.

## [v0.4.0] — 2026-11-18 — frozen

### Good
- Frozen (James: "freeze"). VERSION 0.3.3 -> 0.4.0. 18/18 on the laptop
  and on the VPS check.
- Named for the version it ships (roadmap NAMING.md): built as
  saboteur_v3.py / SPEC_V3.md / tests/test_saboteur_v3.py / threats_v3/,
  renamed before the freeze to saboteur_v0_4.py / SPEC_V0_4.md /
  tests/test_saboteur_v0_4.py / threats_v0_4/. The entry below uses the
  new names. The frozen v1 and v2 files keep theirs.

### Bad
- `threats_v0_4/` is still empty: nothing attacks the Legacy layers yet.

### Ugly
- No ugly items.

## [v0.4.0-dev] — 2026-11-18 — no default target; the-full-stack refused

### Good
- James: "the forge stack was for reference only and not meant to be a
  layer involved in the legacy program." `saboteur_v0_4.py` (SPEC_V0_4.md)
  is v2's harness unchanged, with `--target` required, a `the-full-stack`
  target refused (exit 2, nothing made) and threats read from
  `threats_v0_4/`. `tests/test_saboteur_v0_4.py` (5, run red first). 18/18.

### Bad
- `threats_v0_4/` is empty, so the Saboteur proves nothing about the
  Legacy yet. Threats against P2 Sign, P3 Freeze, P4 Ledger and P15 HAL
  are the next piece of work, when James says.
- The VPS check still runs `saboteur_v2.py` against the-full-stack until
  it is changed (roadmap step 6).

### Ugly
- Every PASS the Saboteur has recorded so far was against the-full-stack,
  not a Legacy layer.

## [v0.3.3] — 2026-11-15 — frozen

### Good
- Frozen (James: "freeze them"). VERSION 0.3.0-dev -> 0.3.3: the v2
  harness (`saboteur_v2.py`, `harness_guard_v2.py`, `mutations_v2.py`),
  its five canaries and the 15 live threats in `threats_v2/`. A change
  from here is a new layer or a new threat file.
- At the freeze: 13/13 tests; main run PASS 15, FAIL 0, UGLY 0 against
  the-full-stack, real repo unchanged.

### Bad
- Frozen before the S24 run; the phone runs it next.

### Ugly
- No ugly items. Nothing but VERSION and this entry changed.

## [v0.3.3-dev] — 2026-11-15 — the old-tool threats retired; first green run

### Good
- Threats 03, 05, 09, 11 and 12 moved to `threats_v2/retired/` (James:
  "retire the old"), with a README naming each original tool's gap and
  the live threat that attacks its layer (13–17, 20). Kept, not deleted;
  `--threats threats_v2/retired` still runs them.
- Full run: PASS 15, FAIL 0, UGLY 0, SKIP 0, real repo unchanged, exit 0:
  the first green run against the-full-stack. Every attack the Saboteur
  knows is caught and named by a live tool.

### Bad
- A green run means every known attack is caught, not that the stack is
  safe. The run is only as wide as `threats_v2/`.

### Ugly
- Retired threats still fail (03 FAIL; 05, 09, 11, 12 UGLY), by design:
  `sign.py`, `ledger.py` and `hal_v2.py` keep their gaps. Anyone calling
  those originals directly gets the old behaviour; the layers are the
  tools to call.

## [v0.3.2-dev] — 2026-11-15 — threats 18–20: pinned hashes, governance-v7

### Good
- Three new threat files attack the-full-stack's hardening 6.3 and 6.4
  layers. 18: change a document a live capsule pins by sha256 (CRLF on
  `docs/glossary.md`), against `freeze_v3.py --check`. 19: put back a
  COMPUTE-ON-FREEZE placeholder, against `freeze_v3.py --check`. 20: a
  fractional number in governance-v7 itself, against `sign_v3.py
  --verify`. All three PASS, named for the right reason; real repo
  unchanged.

### Bad
- Run against the working tree before James signed the new capsules
  (datacube-v2, hal-v2, manifest-v11, changelog-v2, step-spec-v2), so
  the baselines already carried "unsigned" failures. The differential
  judgement still needs the threat's own named line, so the verdicts
  hold; re-run the full set after the signing.

### Ugly
- Threat 18 is the attack that found a real gap only by reading:
  governance-v2..v6 pinned a glossary hash that never matched, and no
  tool, this harness included, had a threat that could see it. A pinned
  hash nobody compares is a promise nobody keeps.

## [v0.3.1-dev] — 2026-11-15 — threats 13–17: the fixes, attacked

### Good
- Five new threat files aim the same attacks at the-full-stack's
  hardening 6.2 layers (James: "yes to all 3"): 13 deleted .sig and 16
  fractional number against `sign_v2.py --verify`; 14 truncated row and
  15 replayed row against `ledger_v2.py verify`; 17 stale score against
  `hal_v3.py seal`. All five PASS, each named for the right reason.
- Full run: PASS 12, FAIL 1, UGLY 4, SKIP 0, real repo unchanged.

### Bad
- Threats 03, 05, 09, 11 and 12 stay red: they attack the original
  tools (`sign.py`, `ledger.py`, `hal_v2.py`), which keep their gaps by
  the Immutable Rule. The run therefore still exits 1. That is the
  evidence for the layers, not a fault in them.

### Ugly
- Threat 17's clean run already fails: the example score (as_of
  2026-08-08) is older than hal_v3's 30 days. It passes only because the
  mutated run gives a new stale line. A fresh example score would make
  it a cleaner test.

## [v0.3.0-dev] — 2026-11-15 — the honest harness (saboteur_v2)

### Good
- `saboteur_v2.py`, `harness_guard_v2.py`, `mutations_v2.py`,
  `threats_v2/`, `SPEC_V2.md`, `tests/test_saboteur_v2.py` (8 tests,
  13/13 with v1's 5). v1's files are not edited. v2 proves the harness
  first (5 canaries), judges every threat against a clean baseline,
  runs tools with a throwaway key, and checks the real repo is
  unchanged afterwards. Built on James's delegation ("analise and
  report and fix").
- First honest run against the-full-stack (`c2ff81e`), real repo
  unchanged: PASS 7, FAIL 1, UGLY 4, SKIP 0. Findings in the target
  (the Saboteur only reports them; fixes there are new layers):
  - **03 FAIL — a real silent pass in `sign.py --verify`.** Delete
    `docs/datacube.md.sig` and the verifier simply stops mentioning
    the artefact: it checks the `.sig` files that exist, not the
    artefacts that must have one (its own header's ratified rule).
  - **05 UGLY — `ledger.py verify` crashes** (traceback in
    `parse_entries`) on a ledger cut mid-row, instead of naming it.
  - **09, 11, 12 UGLY — caught only by the broken signature or chain.**
    No tool names the fractional-number rule; HAL has no score
    freshness rule at all (a score dated 2025-01-01 is refused only
    because the edit broke its signature); the ledger has no replay
    check (a duplicated row is caught as a broken chain).
  - Passing for the right reason: 01, 02, 04, 06, 07, 08 (sign.py names
    the scp_id rule), 10.
- Found on a clean copy of the-full-stack (the baselines):
  `sign.py --verify` fails 3 (Nova-bot `hardware-manifest-v1`,
  keystone_gate `step-spec-v1` scp_id with underscores, and
  `CHANGELOG.md`); `freeze_v2.py --check` fails on
  `consumer/Long Con Generator/full_stack/changelog.sc.json`
  (COMPUTE-ON-FREEZE never resolved).

### Bad
- **v1's "12/12 PASS" (v1.0.0 below) is withdrawn.** v1's saboteur.py
  never ran harness_guard (no canaries, no baseline, no repo hash),
  although SPEC.md marks step 0 PROVEN. On a clean copy, `sign.py
  --verify` and `freeze_v2.py --check` already exit 1 and `hal.py
  verify-score` does not exist (argparse prints "invalid choice"), so
  threats 01, 02, 03, 07, 08, 09 and 11 passed whatever the mutation
  did. Threats 02 and 03 targeted `README.md.sig`, which does not
  exist (03 deleted nothing). Threat 10's wrong-key signature was hex,
  not base64, so it tested a malformed signature. The keyword "fail"
  sat in 10 of 12 threats and matches any failing tool.
- v1 wiped `scratch/` relative to wherever it was started, with no
  guard, read its target from a fixed `~/forge/the-full-stack`, ran
  "python" from the shell, and exited 0 with UGLY or SKIP results.
- v1's line mutations wrote text mode: on Windows every LF became CRLF,
  so a "reorder" also rewrote every line ending.
- v1 let tools sign with the owner's key: threat 10 runs `hal_v2.py
  seal`, which signs with `FORGE_KEY_PATH`. v2 points it at a throwaway
  key in the scratch copy.
- v1's tests create and write under `~/forge` in the home folder.

### Ugly
- **Threat 02 happened for real.** `CHANGELOG.md` in the-full-stack was
  signed on 2026-11-14 while stored with CRLF; commit `c2ff81e` (the
  phone, 2026-11-15) converted it to LF with no other change, and its
  `.sig` no longer verifies. It needs James's signature again. Four
  more signed docs are stored with CRLF (`docs/AXIOM.md`,
  `docs/hal-implementation-definition.md`,
  `docs/leighton-loop-observation.md`, `docs/leighton-weight-engine.md`)
  and will break the same way the first time anything normalises them.
- The v0.2.0 entry's Ugly section keeps a thinking-aloud line ("Wait,
  let me re-check."); left as written (append-only).

## [v1.0.0] — 12/12 PASS

### Good
- All 12 threats pass cleanly.
- 0 FAIL. 0 UGLY.
- Two real silent passes found and fixed by layering:
  - `freeze.py --check` didn't exist (fixed by `freeze_v2.py`).
  - `hal.py seal` printed FAILED but exited 0 (fixed by `hal_v2.py`).

### Bad
- The Saboteur depends on specific paths and commands in the target repo.
  If the target repo restructures, threat specs must be updated.

### Ugly
- The first run had a false positive (the `ledger.py` silent pass) because
  the harness ran the tool from the wrong directory. The Saboteur is only
  as honest as its own test harness.

# CHANGELOG — the-saboteur (Tier 2: The Saboteur)

CHANGELOG.md — build history for The Saboteur, latest entry at top.

## [v0.2.0] — Real silent pass found in hal.py

### Good
- Ran the full 12-threat suite against the-full-stack.
- 11 threats PASS. 0 FAIL. 1 UGLY (which turned out to be a real silent pass).
- Found a genuine silent pass in `hal.py seal`.
- Fixed `freeze.py --check` (which didn't exist) by building `freeze_v2.py`.

### Bad
- The Saboteur's exit-code detection was too lenient. When `hal.py seal`
  printed `FAILED` but exited 0, it was logged as UGLY, not FAIL. The
  harness must treat any non-zero exit code as a FAIL when the tool
  prints a failure message.
- The threat 10 spec was calling `verify-score` (a subcommand that
  doesn't exist). Corrected to call `seal` with real arguments.

### Ugly
- **BUG FOUND (Target: `the-full-stack/hal.py`):**
  Mutation 11 (wrong-key signature) — actually the *baseline* test,
  which uses the wrong signature already. Wait, let me re-check.
  The original run was against `verify-score` (bad command). When we
  manually ran `hal.py seal` with a wrong signature, it printed
  `FAILED  authoriser score file signature is invalid` and then
  exited **0**.
  The tool detects the failure, prints it clearly, and then proceeds
  as if it succeeded. An automated pipeline calling `hal.py seal`
  would believe a seal was created when it wasn't.
  - **Fix needed:** `hal.py seal` must exit non-zero when the
    signature check fails.
