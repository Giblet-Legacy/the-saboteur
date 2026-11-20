"""
saboteur_report_v1_1.py — The Saboteur 1.1.0: the daily rotation report

Function:
    SPEC_V1_1.md §4. Reads one UTC day's slot files
    (<results>/<day>/slot-<K>.json, written by saboteur_v1_1.py) and
    prints a Markdown report:

      - each slot that ran (start time, totals, status), and each slot
        that is missing;
      - how many of the threats ran that day;
      - the totals;
      - new problems and healed gaps;
      - the known gaps still red, by class;
      - every threat whose verdict changed since the day before.

    The day is RED if any slot was RED or any slot is missing; otherwise
    GREEN. --write also saves the report as <results>/<day>/report.md.

    python saboteur_report_v1_1.py [--day YYYY-MM-DD] [--results results]
                                   [--threats threats_v1] [--known-gaps known_gaps_v1_1.json] [--write]

    The day defaults to yesterday (UTC), the last whole day. Exit codes:
    0 GREEN, 1 RED, 2 no slot files for that day.

Public API:
    1. load_day(results, day) -> {slot: doc}
    2. build(day, results, known, threats_total) -> (markdown, status)
    3. main(argv=None) -> int

Tier:     Tier 2 — The Saboteur, 1.1.0
Depends:  saboteur_v1_1.py (its results files)
Spec:     SPEC_V1_1.md 1.1.0
Version:  1.1.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import collections
import datetime
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# 1. load_day
# ---------------------------------------------------------------------------
def load_day(results, day):
    out = {}
    for path in sorted((pathlib.Path(results) / day).glob("slot-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        out[int(doc["slot"])] = doc
    return out


def _verdicts(slots):
    return {f: v["verdict"] for doc in slots.values() for f, v in doc["verdicts"].items()}


# ---------------------------------------------------------------------------
# 2. build
# ---------------------------------------------------------------------------
def build(day, results, known, threats_total):
    slots = load_day(results, day)
    of = max((doc["of"] for doc in slots.values()), default=4)
    verdicts = _verdicts(slots)
    totals = collections.Counter(verdicts.values())
    lines = [f"# Saboteur rotation report — {day}", ""]

    lines += ["## Slots", ""]
    missing = []
    for k in range(of):
        doc = slots.get(k)
        if doc is None:
            missing.append(k)
            lines.append(f"- slot {k}: missing")
        else:
            t = doc["totals"]
            lines.append(f"- slot {k}: {doc['status']}, started {doc['started']}, {len(doc['verdicts'])} threats, "
                         f"PASS {t['PASS']} FAIL {t['FAIL']} UGLY {t['UGLY']} SKIP {t['SKIP']}")
    lines += ["", "## Coverage", "", f"{len(verdicts)} of {threats_total} threats ran.", ""]
    lines += ["## Totals", "",
              f"PASS {totals['PASS']}  FAIL {totals['FAIL']}  UGLY {totals['UGLY']}  SKIP {totals['SKIP']}", ""]

    new = sorted({f for doc in slots.values() for f in doc["new_problems"]})
    healed = sorted({f for doc in slots.values() for f in doc["healed"]})
    reason = {f: v["reason"] for doc in slots.values() for f, v in doc["verdicts"].items()}
    lines += ["## New problems", ""] + ([f"- {f}: {verdicts[f]}: {reason[f]}" for f in new] or ["None."]) + [""]
    lines += ["## Healed known gaps", ""] + ([f"- {f} ({known.get(f, '?')}): now passes" for f in healed]
                                             or ["None."]) + [""]

    still = collections.Counter(known[f] for f, v in verdicts.items() if f in known and v == "FAIL")
    lines += ["## Known gaps still red", ""]
    lines += [f"- {cls}: {n}" for cls, n in sorted(still.items())] or ["None ran today."]
    lines.append("")

    prev_day = (datetime.date.fromisoformat(day) - datetime.timedelta(days=1)).isoformat()
    prev = _verdicts(load_day(results, prev_day))
    lines += ["## Changes since the day before", ""]
    if not prev:
        lines.append(f"There are no results for the day before ({prev_day}).")
    else:
        changes = [f"- {f}: {prev[f]} -> {v}" for f, v in sorted(verdicts.items()) if f in prev and prev[f] != v]
        lines += changes or ["None."]
    lines.append("")

    status = "RED" if missing or any(doc["status"] != "GREEN" for doc in slots.values()) else "GREEN"
    why = []
    if missing:
        why.append(f"missing slot{'s' if len(missing) > 1 else ''} {', '.join(map(str, missing))}")
    if new:
        why.append(f"{len(new)} new problem{'s' if len(new) > 1 else ''}")
    if healed:
        why.append(f"{len(healed)} healed gap{'s' if len(healed) > 1 else ''}")
    lines += ["## Status", "", status + (f": {'; '.join(why)}" if why else ""), ""]
    return "\n".join(lines), status


# ---------------------------------------------------------------------------
# 3. main
# ---------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description="The Saboteur 1.1.0: the daily rotation report.")
    yesterday = (datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=1)).isoformat()
    p.add_argument("--day", default=yesterday)
    p.add_argument("--results", default=str(HERE / "results"))
    p.add_argument("--threats", default=str(HERE / "threats_v1"))
    p.add_argument("--known-gaps", default=str(HERE / "known_gaps_v1_1.json"))
    p.add_argument("--write", action="store_true", help="also save <results>/<day>/report.md")
    args = p.parse_args(argv)
    if not load_day(args.results, args.day):
        print(f"no rotation results for {args.day} in {args.results}", file=sys.stderr)
        return 2
    known = json.loads(pathlib.Path(args.known_gaps).read_text(encoding="utf-8"))["gaps"]
    total = len(list(pathlib.Path(args.threats).glob("*.json")))
    text, status = build(args.day, args.results, known, total)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(text)
    if args.write:
        (pathlib.Path(args.results) / args.day / "report.md").write_bytes(text.encode("utf-8"))
    return 0 if status == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
