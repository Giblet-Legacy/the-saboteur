"""
saboteur_v1_1.py — The Saboteur 1.1.0: one rotation slot of the 1000 threats

Function:
    The layer over saboteur_v1.py (SPEC_V1_1.md); 1.0.0 is not edited.
    James, 2026-11-20: test 250 every 6 hours, not the same 250, all of
    them in 24 hours, with a report; then "start rotation".

    One run is one slot.

      - Slot K of N runs the threats whose index (in 1.0.0's sorted
        order, from 0) is K mod N: interleaved, so every slot reaches
        every layer.
      - `--slot auto` takes K from the UTC hour (hour * N // 24).
      - The run is 1.0.0's: the lock, the full-stack refusal,
        FORGE_LEGACY_ROOT, the guard, the canaries, run_threat per
        threat, the hash before and after, and the same per-threat
        lines.
      - It writes <results>/<date>/slot-<K>.json and judges the slot
        against known_gaps_v1_1.json.

    The slot is RED (exit 1) for:
      - a new problem (a threat not in the known gaps is not PASS);
      - any UGLY or SKIP;
      - a healed gap (a known gap PASSes).
    It is GREEN (exit 0) otherwise. Exit 2: the lock is held, the target
    is refused, or the harness is invalid; then no results file is
    written.

    python saboteur_v1_1.py [--slot auto|K] [--of 4] [--target fixture_v1] [--threats threats_v1]
                            [--parent DIR] [--results results] [--known-gaps known_gaps_v1_1.json]

Public API:
    1. select(items, slot, of) -> list
    2. slot_for(hour, of) -> int
    3. judge_slot(verdicts, known) -> (new_problems, healed, status)
    4. main(argv=None, now=None) -> int

Internal helpers:
    5. _write_atomic(path, doc)

Tier:     Tier 2 — The Saboteur, 1.1.0
Depends:  saboteur_v1.py (load_threats, run_threat, acquire, release, Locked),
          harness_guard_v1.py
Spec:     SPEC_V1_1.md 1.1.0
Version:  1.1.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import datetime
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_guard_v1 as guard  # noqa: E402
import saboteur_v1  # noqa: E402

DEFAULT_RESULTS = HERE / "results"
DEFAULT_KNOWN_GAPS = HERE / "known_gaps_v1_1.json"
VERSION = "1.1.0"


# ---------------------------------------------------------------------------
# 1. select
# ---------------------------------------------------------------------------
def select(items, slot, of):
    if not 0 <= slot < of:
        raise ValueError(f"slot {slot} is not in 0..{of - 1}")
    return [x for i, x in enumerate(items) if i % of == slot]


# ---------------------------------------------------------------------------
# 2. slot_for
# ---------------------------------------------------------------------------
def slot_for(hour, of):
    return hour * of // 24


# ---------------------------------------------------------------------------
# 3. judge_slot
# ---------------------------------------------------------------------------
def judge_slot(verdicts, known):
    new = sorted(f for f, v in verdicts.items() if v != "PASS" and (f not in known or v in ("UGLY", "SKIP")))
    healed = sorted(f for f, v in verdicts.items() if v == "PASS" and f in known)
    return new, healed, ("RED" if new or healed else "GREEN")


# ---------------------------------------------------------------------------
# 5. _write_atomic
# ---------------------------------------------------------------------------
def _write_atomic(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_bytes((json.dumps(doc, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    os.replace(tmp, path)


def _stamp(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# 4. main
# ---------------------------------------------------------------------------
def main(argv=None, now=None):
    p = argparse.ArgumentParser(description="The Saboteur 1.1.0: one rotation slot of the threats.")
    p.add_argument("--slot", default="auto", help="auto (from the UTC hour) or 0..of-1")
    p.add_argument("--of", type=int, default=4, help="how many slots make a day (default 4: every 6 hours)")
    p.add_argument("--target", default=str(saboteur_v1.DEFAULT_TARGET))
    p.add_argument("--threats", default=str(saboteur_v1.DEFAULT_THREATS))
    p.add_argument("--parent", default=str(guard.DEFAULT_PARENT))
    p.add_argument("--results", default=str(DEFAULT_RESULTS))
    p.add_argument("--known-gaps", default=str(DEFAULT_KNOWN_GAPS))
    args = p.parse_args(argv)
    start = now or datetime.datetime.now(datetime.timezone.utc)
    if args.of < 1 or 24 % args.of:
        print(f"refused: --of {args.of} does not divide a day into whole hours", file=sys.stderr)
        return 2
    slot = slot_for(start.hour, args.of) if args.slot == "auto" else int(args.slot)
    if not 0 <= slot < args.of:
        print(f"refused: slot {slot} is not in 0..{args.of - 1}", file=sys.stderr)
        return 2
    known = json.loads(pathlib.Path(args.known_gaps).read_text(encoding="utf-8"))["gaps"]

    try:
        lock = saboteur_v1.acquire(args.parent)
    except saboteur_v1.Locked as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    try:
        target = pathlib.Path(args.target).resolve()
        if target.name == saboteur_v1._REFERENCE_ONLY:
            print(f"refused: {saboteur_v1._REFERENCE_ONLY} is reference only, not a Legacy layer "
                  "(SPEC_V0_4 section 1)", file=sys.stderr)
            return 2
        os.environ.setdefault("FORGE_LEGACY_ROOT", str(HERE.parent))
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        verdicts, reasons = {}, {}
        try:
            if not target.is_dir():
                raise guard.HarnessInvalid(f"target is not a directory: {target}")
            everything = saboteur_v1.load_threats(args.threats)
            threats = select(everything, slot, args.of)
            if not threats:
                raise guard.HarnessInvalid("no threats in this slot")
            initial = guard.pre_run(pathlib.Path(args.parent) / "run", target, args.parent)
            print(f"THE SABOTEUR 1.1.0: slot {slot} of {args.of}, {len(threats)} of {len(everything)} threats "
                  f"against {target.name} (harness proven: 5 canaries)\n")
            for i, t in enumerate(threats, 1):
                verdict, reason, detail = saboteur_v1.run_threat(t, target, args.parent)
                verdicts[t["_file"]], reasons[t["_file"]] = verdict, reason
                print(f"[{i:02d}/{len(threats)}] {verdict:<4}  {t['name']}\n          {reason}")
                if detail.get("new_lines") and verdict != "PASS":
                    print(f"          new output: {detail['new_lines'][:2]}")
            guard.post_run(target, initial)
        except guard.HarnessInvalid as e:
            print(f"HARNESS INVALID: {e}", file=sys.stderr)
            return 2
    finally:
        saboteur_v1.release(lock)

    new, healed, status = judge_slot(verdicts, known)
    totals = {k: sum(1 for v in verdicts.values() if v == k) for k in ("PASS", "FAIL", "UGLY", "SKIP")}
    doc = {"version": VERSION, "date": start.strftime("%Y-%m-%d"), "slot": slot, "of": args.of,
           "started": _stamp(start), "finished": _stamp(datetime.datetime.now(datetime.timezone.utc)),
           "target": str(target), "threats_dir": str(pathlib.Path(args.threats).resolve()),
           "threats_total": len(everything),
           "verdicts": {f: {"verdict": verdicts[f], "reason": reasons[f]} for f in sorted(verdicts)},
           "totals": totals, "new_problems": new, "healed": healed, "status": status}
    out = pathlib.Path(args.results) / doc["date"] / f"slot-{slot}.json"
    _write_atomic(out, doc)
    still = sum(1 for f, v in verdicts.items() if f in known and v == "FAIL")
    print(f"\nPASS {totals['PASS']}  FAIL {totals['FAIL']}  UGLY {totals['UGLY']}  SKIP {totals['SKIP']}"
          "  (real repo unchanged)")
    print(f"known gaps still red: {still}; new problems: {len(new)}; healed: {len(healed)}")
    for f in new:
        print(f"  NEW    {f}: {verdicts[f]}: {reasons[f]}")
    for f in healed:
        print(f"  HEALED {f}: a known gap now passes ({known[f]})")
    print(f"slot {slot}: {status} -> {out}")
    return 0 if status == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
