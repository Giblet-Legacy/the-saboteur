# SPEC V1.1 — the-saboteur (Tier 2: The Saboteur), rotation

SPEC_V1_1.md — what saboteur_v1_1.py and saboteur_report_v1_1.py add over the frozen 1.0.0.

Function:
    James, 2026-11-20: "this attacks are getting nus now ther taking alot
    of time up how about we pivot slightly and and we test 250 each 6
    hours but not the same 250 and in a 24 hour period we would have
    tested all and can generatea report". His answers to the three
    questions (CONSOLIDATION_V1 §8) were: 1.1.0 after 1.0.0, interleaved
    slices, and RED only for new problems. Then: "start rotation".

    SPEC_V1.md stays authoritative for the harness, the fixture, the tool,
    the mutations and the threats. Nothing frozen is edited.

Tier:      Tier 2 — The Saboteur
Depends:   saboteur_v1.py (load_threats, run_threat, acquire, release),
           harness_guard_v1.py
Version:   SPEC V1.1 1.1.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. saboteur_v1_1.py: one slot

    python saboteur_v1_1.py [--slot auto|K] [--of 4] [--target fixture_v1] [--threats threats_v1]
                            [--parent DIR] [--results results] [--known-gaps known_gaps_v1_1.json]

**The slot.** The threats are taken in 1.0.0's order (sorted file names)
and numbered from 0. Slot K of N runs every threat whose index i has
i mod N = K:

- slot 0 runs 0001, 0005, 0009 and so on;
- slot 1 runs 0002, 0006 and so on.

The N slots together run every threat exactly once, and each run reaches
every layer. With the default N = 4, each slot is 250 of the 1000.

**Choosing the slot.** `auto`, the default, takes the UTC hour at the
start: K = hour × N // 24. With N = 4 that means:

| UTC | Slot |
|---|---|
| 00:00–05:59 | 0 |
| 06:00–11:59 | 1 |
| 12:00–17:59 | 2 |
| 18:00–23:59 | 3 |

A timer firing every 6 hours from any start covers all four slots each
day. `--slot K` overrides the choice.

**The run is 1.0.0's.**

- **The lock:** `saboteur_v1.acquire` on the same
  `<parent>/saboteur.lock`, so a rotation run and a full run never clash.
- **The refusal:** a target folder named the-full-stack is refused,
  exit 2.
- **The layers:** `FORGE_LEGACY_ROOT` is set unless it is already set.
- **The harness:** the guard, the canaries and the hash before and after
  are 1.0.0's, and so is `saboteur_v1.run_threat` per threat.
- **The output:** the per-threat lines are 1.0.0's.

## 2. The results file

Each run writes `<results>/<YYYY-MM-DD>/slot-<K>.json`. The date is the
UTC date at the start, and the default `<results>` is `results/` in the
repository, which is git-ignored. A rerun of the same slot on the same
day replaces the file. The file holds:

    {"version": "1.1.0", "date", "slot", "of", "started", "finished",
     "target", "threats_dir", "threats_total",
     "verdicts": {"<file>": {"verdict": "PASS|FAIL|UGLY|SKIP", "reason": "..."}},
     "totals": {"PASS", "FAIL", "UGLY", "SKIP"},
     "new_problems": [<file>...], "healed": [<file>...], "status": "GREEN|RED"}

It is written to a temporary name and then renamed, so a reader never
sees half a file.

## 3. Known gaps and RED

`known_gaps_v1_1.json` maps each of the 154 threats that were red at the
1.0.0 gate to its gap class (SPEC_V1 §6). A slot's status is:

- **RED, exit 1**, if any of these happens:
  - a threat not in the known gaps is not PASS (a **new problem**);
  - any threat is UGLY or SKIP, known or not;
  - a known gap PASSes (**healed**). That is good news, but it means a
    layer changed, so someone should look and then take it off the list.
- **GREEN, exit 0**, otherwise. The known gaps staying red is expected.
- **Exit 2** if the lock is held, the target is refused, or the harness
  is invalid (SPEC_V2). No results file is written then.

The list changes only by a deliberate edit, recorded in the CHANGELOG:
when James decides a gap is fixed, or a new red is accepted as known.

## 4. saboteur_report_v1_1.py: the daily report

    python saboteur_report_v1_1.py [--day YYYY-MM-DD] [--results results] [--threats threats_v1]
                                   [--known-gaps known_gaps_v1_1.json] [--write]

It reads that day's slot files and prints a Markdown report. `--write`
also saves it as `<results>/<day>/report.md`. The day defaults to
yesterday (UTC), the last whole day. The report holds:

- **Slots:** for each one, whether it ran (its start time and totals) or
  is missing.
- **Coverage:** how many of the threats ran that day.
- **Totals:** across the slots that ran.
- **New problems and healed gaps:** each threat, with its verdict and
  reason.
- **Known gaps still red:** counts by class.
- **Changes since the day before:** every threat whose verdict differs
  from its last verdict on the previous day. If there is no previous
  day, it says so.
- **Status:** RED if any slot was RED or any slot is missing; otherwise
  GREEN.

Exit codes: 0 GREEN, 1 RED, 2 no slot files for that day.

## 5. Where it runs

Starting rotation means running one slot every 6 hours, which is
separate from the code: on the VPS through `check_v2.sh`, or on the
laptop through a scheduled task. James chooses. Either way:

- nothing is signed and no key is used;
- the fixture's keys are throwaway and public only.

## 6. Tests

`tests/test_saboteur_v1_1.py`:

- the slots cover every threat exactly once;
- `auto` follows the UTC hour;
- the known-gaps file names 154 real threats with valid classes;
- on a small fake target, a known gap staying red is GREEN;
- a new problem, a healed gap and a SKIP are each RED;
- a held lock gives exit 2 with no results file;
- the report aggregates the slots, names a missing slot and lists
  changes since the day before.

---

## Document control

- **SPEC V1.1 1.1.0**: 2026-11-20, by the VS Code AI on James's
  "start rotation".
- Frozen 2026-11-20 (James: "freeze commit push"). The first real slot was
  GREEN (slot 3: PASS 212, FAIL 38, all 38 known gaps).
