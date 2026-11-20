# CONSOLIDATION V1 — the-saboteur 0.9.0 -> 1.0.0 (plan)

CONSOLIDATION_V1.md — the plan for flattening the Saboteur's layer chain into one clean 1.0.0.

Function:
    James (2026-11-20): "ok so this brings us to the point were we
    consolodate archive and parent up to v1.0". The plan for 1.0.0 under
    his consolidation rule (2026-11-16: "consolidate what is if adding
    more its a new v"):

    - one clean major version;
    - identical behaviour to the last frozen version;
    - old layers archived byte-identical;
    - nothing added, nothing fixed.

    It follows the-legacy's CONSOLIDATION_V2.md (2.0.0, 2026-11-20). The
    work is done on a branch and lands on main in one commit at James's
    "freeze".

Version:  plan, done (2026-11-20: frozen 1.0.0, tag v1.0.0; rotation next, §8)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)

---

## 1. Why now

**The chain is too deep.** Running 0.9.0 goes through every layer
below it:

    saboteur_v0_9 -> saboteur_v0_7 -> saboteur_v0_6 -> saboteur_v0_5_1
                  -> saboteur_v0_5 -> saboteur_v2 (+ harness_guard_v2)
    mutations_v0_9 -> mutations_v0_8 -> mutations_v0_5 -> mutations_v2

Two layers swap the module below them at run time:

- saboteur_v0_5 sets `saboteur_v2.mutations`;
- saboteur_v0_8 and v0_9 set `saboteur_v0_5.mutations_v0_5`.

The rule's triggers were "5+ layers deep, or a layer patches the one
below". The Saboteur passes both.

**The threats are copied five times.** `threats_v0_5/` to
`threats_v0_9/` hold 108 + 200 + 400 + 800 + 1000 = 2,508 files. Each
holds the one before it plus the new threats.

**The names don't say their version.** NAMING.md lists the files from
`saboteur_v2.py` to `threats_v2/` as 0.3.0–0.3.3. The CHANGELOG's old
`[v1.0.0]` is the original `saboteur.py`, made before the 0.x
renumbering. 1.0.0 is where the Saboteur comes into line.

## 2. What 1.0.0 is

**The behaviour of 1.0.0 is exactly what `python saboteur_v0_9.py` does
once 0.9.0 is frozen (§4 step 1).** That means:

- the same arguments;
- the same run lock;
- the same guard and canaries;
- the same output lines;
- the same exit codes;
- the same 1000 threats;
- the same verdict on every one of them.

What 1.0.0 does **not** keep is behaviour that only an older entry
point had:

- v1's `saboteur.py`;
- v2's default target of the-full-stack;
- 0.4.0's no-default target.

Those stay runnable from a worktree of the tag `v0.9.0`, not from the
archive folder. That was the-legacy's lesson: archived layers import
their siblings and don't run from `archive/`.

| 1.0.0 file | Made from |
|---|---|
| `saboteur_v1.py` | saboteur_v2 + v0_5 + v0_5_1 + v0_6 to v0_9, flattened into one module. It holds the lock, the defaults and the full-stack refusal. Nothing is monkeypatched. |
| `harness_guard_v1.py` | `harness_guard_v2.py`, the same code under a new header. |
| `mutations_v1.py` | mutations_v2 + v0_5 + v0_8 + v0_9 as one module. Every mutation name any threat uses keeps its behaviour. |
| `fixture_v1/` | `fixture_v0_5/` byte for byte: the same keys, the same signatures, **not rebuilt**. The only change is that `legacy_check_v0_5.py` becomes `legacy_check_v1.py`. |
| `build_fixture_v1.py` | `build_fixture_v0_5.py` under a new name and header. |
| `threats_v1/` | `threats_v0_9/`, 0001–1000. The only change in each file is the tool name, `legacy_check_v1.py`. |
| `SPEC_V1.md` | One spec for 1.0.0 as it is, gathered from SPEC_V2 to SPEC_V0_9. It cites them and does not re-decide anything. The ledger of known gaps is carried forward. |
| `tests/test_saboteur_v1.py` (plus `_at_v1` suites) | The contract (§3). |

**What stays where it is:**

- `harness_canaries/`;
- `agent_the_saboteur.py`. Its `main` and `watches` point at 1.0.0's
  files. That is a records change, like README.

## 3. The contract

1. **Step 0, before any new code:**
   - Run every current suite against 0.9.0 to see which tests describe
     live behaviour.
   - Tests of v1, v2's the-full-stack default and 0.4.0's no-default
     describe replaced behaviour. They stay with their archive.
   - Write the table into this plan for James.
   **Step 0 result (2026-11-20, on branch consolidate-1.0.0):**

   - **How it was run:** a throwaway pytest plugin in the scratchpad
     ran all 76 tests against 0.9.0. No file in the repository changed.
     In each suite:
     - the runner's `main` went to `saboteur_v0_9.main`;
     - `apply_mutation` went to `mutations_v0_9`;
     - v1's `harness_guard` went to `harness_guard_v2`.
   - **First pass:** 58 passed and 18 failed.
   - **The harness's own fault:** pytest's monkeypatch, undoing a test,
     wrote the plugin's stand-in `main` back into the real
     saboteur_v0_5. That poisoned the tests after it.
   - **Second pass:** every failure was rerun alone, in its own process.
   - **One test left unrun:** 0.4.0's `test_target_is_required` was
     not rerun. Run under 0.9.0 it calls `main()` with no target, and
     0.9.0 has a default, so it starts a full 1000-threat run.

   | Suite (tests) | Live as is | Carried with a change | Replaced |
   |---|---|---|---|
   | test_harness_guard (5) | | | 5: v1's guard (scratch under ~/forge). 0.9.0 uses harness_guard_v2, tested by test_saboteur_v2. |
   | test_saboteur_v2 (8) | 8 (the end-to-end test failed first only through the harness fault) | | |
   | test_saboteur_v0_4 (5) | 3 | | 2: `test_target_is_required` (0.4.0 had no default target). `test_refuses_the_full_stack`: 0.9.0 still refuses with exit 2, but it takes the run lock first, which creates the parent folder, and 0.4.0's test says nothing is touched. 1.0.0 keeps 0.9.0's order. |
   | test_saboteur_v0_5 (13) | 12 | 1: end-to-end `--only 00` becomes `000`, which is still 0001–0009 and PASS 9 | |
   | test_saboteur_v0_5_1 (9) | 8 | 1: end-to-end `--only 001` becomes `0001`. Under four digits, `001` catches 0010–0019, which includes the red 0011. | |
   | test_saboteur_v0_6 (6) | 4 | 1: end-to-end `19` becomes `019` | 1: the default threats are threats_v0_6 |
   | test_saboteur_v0_7 (6) | 4 | 1: end-to-end `20` becomes `020` | 1: the default threats are threats_v0_7 |
   | test_saboteur_v0_8 (12) | 10 | 1: end-to-end `42` becomes `042` (`42` matches nothing under four digits) | 1: the runner swaps in mutations_v0_8. 1.0.0 has no swap. |
   | test_saboteur_v0_9 (12) | 11 (the end-to-end test failed first only through the harness fault) | | 1: the runner swaps in mutations_v0_9. 1.0.0 has no swap; one module holds every mutation. |
   | **Total (76)** | **60** | **5** | **11** |

   The 11 replaced tests stay in `archive/0.9.0/` with their versions,
   runnable from a worktree of the tag `v0.9.0`.

2. **Carry every live test forward against 1.0.0:**
   - as `tests/test_saboteur_v1.py`, plus `<suite>_at_v1.py` where a
     suite needs a change;
   - nothing added.
3. **The 1.0.0 gate:**
   - every carried test passes against 1.0.0;
   - the full 1000-threat run of 0.9.0 and of 1.0.0, each in its own
     scratch parent, gives the same verdict for every threat number and
     the same totals;
   - real repo unchanged both times.

   **Gate result (2026-11-20):** 0.9.0 from a worktree of the tag
   `v0.9.0` and 1.0.0 from the branch each ran all 1000 threats, each in
   its own scratch parent, with FORGE_LEGACY_ROOT pointing at the real
   layers.
   - Both: PASS 846, FAIL 154, UGLY 0, SKIP 0, real repo unchanged.
   - Threats with a different verdict or name: **0**.
   - The red set is the 154 recorded at 0.9.0.
   - GATE: PASS.

## 4. The order of work

1. **Finish and freeze 0.6.0–0.9.0 as they are.** All four are
   unfrozen today.
   - Run 0801–1000 (it has not run yet, see §6).
   - Write SPEC_V0_8, SPEC_V0_9, test_saboteur_v0_9 and the CHANGELOG
     entries.
   - Freeze on James's word, then commit and push.
   - **Tag `v0.9.0`.** It is the repo's first tag, and the archive and
     the tag point at the same bytes.
2. **Branch `consolidate-1.0.0`.** main stays on 0.9.0, so the VPS keeps
   testing it.
3. **Step 0 (§3.1); the table goes to James.**
4. **Move the old files into `archive/0.9.0/` with `git mv`.** They stay
   byte-identical. That covers:
   - every `saboteur*.py`, `harness_guard*.py`, `mutations*.py`,
     `build_fixture_v0_5.py`, `SPEC*.md`;
   - `threats*/` and `fixture_v0_5/`;
   - `tests/test_*.py`.

   A `pytest.ini` keeps `archive/` out of collection, as the Cockpit's
   does. That matters because the VPS runs this repo's pytest.
5. **Write the contract tests first and run them red.** Then write the
   1.0.0 files until they're green.
6. **Run the gate (§3.3).**
7. **Update the documents:**
   - README, CLAUDE.md and the agent's paths;
   - CHANGELOG (Good/Bad/Ugly);
   - roadmap NAMING.md: the-saboteur leaves the old-names table;
   - roadmap STATUS and VPS.md.
8. **Freeze on James's word:**
   - headers say `1.0.0`;
   - VERSION is 1.0.0;
   - merge to main in **one** commit;
   - tag `v1.0.0`;
   - push.

## 5. The VPS

- `check_v2.sh` pulls the-saboteur and runs its tests every 6 hours.
- On main nothing changes until the merge, so it keeps going GREEN on
  0.9.0.
- After the merge it runs 1.0.0's tests, with archive/ excluded.
- If it goes RED, `git revert` of the merge puts 0.9.0 back.
- No key is involved: the fixture's keys are throwaway, and only their
  public did:keys are stored.

## 6. Found while planning

- **`saboteur_v2.py` was renamed in the working tree.**
  - It became `saboteur_v0_2.py`, and the deletion is staged. This
    happened outside the AI's session, about 21:39 on 2026-11-20.
  - The contents are byte-identical.
  - Six files still import `saboteur_v2`, so every runner from 0.4.0 to
    0.9.0 stops with `No module named 'saboteur_v2'`.
  - That is why 0801–1000 has not run.
  - NAMING.md also says the file is 0.3.x, not 0.2.
- **The rename is not committed.** If it were pushed, the frozen 0.5.0
  and 0.5.1 would break on the VPS.

## 7. Decisions for James

1. Behaviour is what `saboteur_v0_9.py` does, with 1000 threats.
2. Freeze 0.6.0–0.9.0 as they are and tag `v0.9.0`, then consolidate.
   That is the-legacy's order.
3. **The rename:** put `saboteur_v2.py` back under its own name.
   - Frozen files are never renamed; they come into line at the
     consolidation (NAMING.md).
   - In 1.0.0 the whole chain goes into `archive/0.9.0/` under its
     frozen names, and the clean names are the new `_v1` files.
   - `saboteur_v0_2.py` is an identical copy and is removed.
4. **The old `[v1.0.0]`** CHANGELOG entry stays as written. NAMING.md
   records that it was the pre-renumbering original (`saboteur.py`).
   The new 1.0.0 entry says so.
5. **One archive folder, `archive/0.9.0/`,** including the 2,508 copied
   threat files.
6. **The fixture is not rebuilt.** The keys and signatures stay the
   same, and only the check tool's name changes.
7. **Branch `consolidate-1.0.0`,** merged once at the freeze.

James, 2026-11-20: "yes 7". Yes to all seven.

## 8. After 1.0.0: rotation (1.1.0)

James, 2026-11-20: "this attacks are getting nus now ther taking alot
of time up how about we pivot slightly and and we test 250 each 6 hours
but not the same 250 and in a 24 hour period we would have tested all
and can generatea report". His answers to the three questions:

1. **Order:** rotation is new behaviour, so it is 1.1.0 over the
   consolidated 1.0.0, not part of it.
2. **Slices:** interleaved. Slot k runs threats k+1, k+5, k+9 and so on,
   so every 6-hour run touches every layer.
3. **RED:** a `known_gaps` list holds the red threats (154 at 0.9.0).
   A run is RED only for:
   - a new FAIL;
   - any UGLY or SKIP;
   - a known gap that starts passing.

   Otherwise the VPS stays GREEN.

**What 1.1.0 would hold:**

- **The slot:** each run picks its slot from the UTC hour (hour // 6).
  `--slot N` overrides it.
- **The results:** each run writes the verdict for every threat it ran
  to a results file for its day and slot.
- **The daily report:**
  - totals;
  - every non-PASS by gap class;
  - any slot that did not run;
  - what changed since the previous day.
- **The VPS:** check_v2.sh runs one slot every 6 hours. Wiring that in
  is a separate step, in roadmap VPS.md.
