"""
test_saboteur_v1_1.py — Proof of the Saboteur 1.1.0: rotation, known gaps and the daily report

Function:
    Executable expression of SPEC_V1_1.md. The harness is 1.0.0's and is
    proven by the _at_v1 suites; these cover what 1.1.0 adds, on a small
    fake target so a run takes seconds.

Functions in this file (pytest-collected):
    1. test_slots_cover_every_threat_once
    2. test_auto_slot_follows_the_utc_hour
    3. test_known_gaps_file_names_154_real_threats
    4. test_known_gap_still_red_is_green
    5. test_new_problem_is_red
    6. test_healed_gap_is_red
    7. test_skip_is_red_even_when_known
    8. test_held_lock_is_refused_with_no_results
    9. test_report_aggregates_and_names_a_missing_slot
    10. test_report_lists_changes_since_the_day_before
    11. test_report_with_no_results_exits_2

Helpers:
    12. fake_target, threats — a target and four threats (two caught, two silent)
    13. _run — one slot through saboteur_v1_1.main
    14. _slot_file — write a slot result by hand, for the report

Tier:     Tier 2 — The Saboteur, 1.1.0
Spec:     SPEC_V1_1.md 1.1.0
Version:  1.1.0-dev
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import hashlib
import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("FORGE_LEGACY_ROOT", str(HERE.parent))

import saboteur_report_v1_1 as report  # noqa: E402
import saboteur_v1  # noqa: E402
import saboteur_v1_1  # noqa: E402

VERIFY = '''import hashlib, sys, pathlib
want = pathlib.Path("data.hash").read_text().strip()
got = hashlib.sha256(pathlib.Path("data.txt").read_bytes()).hexdigest()
if got != want:
    print("FAILED  data.txt: hash mismatch"); sys.exit(1)
print("OK      data.txt")
'''


# 12. fake_target, threats
@pytest.fixture
def fake_target(tmp_path):
    repo = tmp_path / "target"
    repo.mkdir()
    (repo / "data.txt").write_bytes(b"line one\nline two\n")
    (repo / "data.hash").write_text(hashlib.sha256(b"line one\nline two\n").hexdigest())
    (repo / "verify.py").write_text(VERIFY)
    (repo / "silent.py").write_text("print('all good')\n")
    return repo


@pytest.fixture
def threats(tmp_path):
    d = tmp_path / "threats"
    d.mkdir()
    caught = {"target_file": "data.txt", "mutation": "reorder_lines", "tool": "python verify.py",
              "expect_error_contains": ["data.txt"]}
    silent = {"target_file": "data.txt", "mutation": "reorder_lines", "tool": "python silent.py",
              "expect_error_contains": ["data.txt"]}
    for name, spec in (("01-caught.json", caught), ("02-silent.json", silent),
                       ("03-caught.json", caught), ("04-silent.json", silent)):
        (d / name).write_text(json.dumps(dict(spec, name=name)))
    return d


# 13. _run
def _run(tmp_path, target, threats, slot, known, of=2):
    gaps = tmp_path / "gaps.json"
    gaps.write_text(json.dumps({"gaps": {k: "test" for k in known}}))
    results = tmp_path / "results"
    rc = saboteur_v1_1.main(["--slot", str(slot), "--of", str(of), "--target", str(target), "--threats", str(threats),
                             "--parent", str(tmp_path / "parent"), "--results", str(results),
                             "--known-gaps", str(gaps)])
    files = list(results.glob("*/slot-*.json"))
    return rc, (json.loads(files[0].read_text(encoding="utf-8")) if files else None)


# 14. _slot_file
def _slot_file(results, day, slot, verdicts, status="GREEN", of=4):
    d = results / day
    d.mkdir(parents=True, exist_ok=True)
    totals = {k: sum(1 for v in verdicts.values() if v == k) for k in ("PASS", "FAIL", "UGLY", "SKIP")}
    doc = {"version": "1.1.0", "date": day, "slot": slot, "of": of, "started": f"{day}T0{slot}:00:00Z",
           "finished": f"{day}T0{slot}:10:00Z", "threats_total": 8,
           "verdicts": {f: {"verdict": v, "reason": "r"} for f, v in verdicts.items()},
           "totals": totals, "new_problems": [], "healed": [], "status": status}
    (d / f"slot-{slot}.json").write_text(json.dumps(doc))


# 1.
def test_slots_cover_every_threat_once():
    items = [f"{i:04d}" for i in range(1, 1001)]
    slots = [saboteur_v1_1.select(items, k, 4) for k in range(4)]
    assert [len(s) for s in slots] == [250, 250, 250, 250]
    assert sorted(x for s in slots for x in s) == items
    assert slots[0][:3] == ["0001", "0005", "0009"] and slots[1][:2] == ["0002", "0006"]


# 2.
def test_auto_slot_follows_the_utc_hour():
    assert [saboteur_v1_1.slot_for(h, 4) for h in (0, 5, 6, 11, 12, 17, 18, 23)] == [0, 0, 1, 1, 2, 2, 3, 3]
    assert saboteur_v1_1.slot_for(13, 2) == 1


# 3.
def test_known_gaps_file_names_154_real_threats():
    doc = json.loads((HERE / "known_gaps_v1_1.json").read_text(encoding="utf-8"))
    gaps = doc["gaps"]
    assert len(gaps) == 154
    assert all((HERE / "threats_v1" / f).exists() for f in gaps)
    assert set(gaps.values()) == {"rollback", "dup-key", "self-certifying", "deleted-row", "unsigned-column",
                                  "non-canonical", "substitution"}


# 4.
def test_known_gap_still_red_is_green(tmp_path, fake_target, threats):
    rc, res = _run(tmp_path, fake_target, threats, 1, ["02-silent.json", "04-silent.json"])
    assert rc == 0
    assert res["status"] == "GREEN" and res["slot"] == 1
    assert sorted(res["verdicts"]) == ["02-silent.json", "04-silent.json"]
    assert res["totals"]["FAIL"] == 2 and res["new_problems"] == [] and res["healed"] == []
    assert (fake_target / "data.txt").read_bytes() == b"line one\nline two\n"


# 5.
def test_new_problem_is_red(tmp_path, fake_target, threats):
    rc, res = _run(tmp_path, fake_target, threats, 1, ["02-silent.json"])
    assert rc == 1 and res["status"] == "RED"
    assert res["new_problems"] == ["04-silent.json"]


# 6.
def test_healed_gap_is_red(tmp_path, fake_target, threats):
    rc, res = _run(tmp_path, fake_target, threats, 0, ["01-caught.json"])
    assert rc == 1 and res["status"] == "RED"
    assert res["healed"] == ["01-caught.json"] and res["new_problems"] == []


# 7.
def test_skip_is_red_even_when_known(tmp_path, fake_target, threats):
    (threats / "05-missing.json").write_text(json.dumps(
        {"name": "missing", "target_file": "nope.txt", "mutation": "reorder_lines", "tool": "python verify.py"}))
    # with five threats and of=2, slot 0 runs 01, 03, 05
    rc, res = _run(tmp_path, fake_target, threats, 0, ["05-missing.json"])
    assert res["verdicts"]["05-missing.json"]["verdict"] == "SKIP"
    assert rc == 1 and res["status"] == "RED" and "05-missing.json" in res["new_problems"]


# 8.
def test_held_lock_is_refused_with_no_results(tmp_path, fake_target, threats, capsys):
    parent = tmp_path / "parent"
    parent.mkdir()
    (parent / saboteur_v1.LOCK_NAME).write_text(json.dumps({"pid": os.getpid(), "started": "x"}))
    rc, res = _run(tmp_path, fake_target, threats, 0, [])
    assert rc == 2 and res is None
    assert "run one at a time" in capsys.readouterr().err


# 9.
def test_report_aggregates_and_names_a_missing_slot(tmp_path):
    results = tmp_path / "results"
    _slot_file(results, "2026-11-21", 0, {"0001-a.json": "PASS", "0005-b.json": "FAIL"})
    _slot_file(results, "2026-11-21", 1, {"0002-c.json": "PASS", "0006-d.json": "PASS"})
    _slot_file(results, "2026-11-21", 3, {"0004-e.json": "PASS"})
    known = {"0005-b.json": "rollback"}
    text, status = report.build("2026-11-21", results, known, threats_total=8)
    assert status == "RED"
    assert "slot 2: missing" in text
    assert "5 of 8 threats ran" in text
    assert "PASS 4  FAIL 1  UGLY 0  SKIP 0" in text
    assert "rollback: 1" in text


# 10.
def test_report_lists_changes_since_the_day_before(tmp_path):
    results = tmp_path / "results"
    for slot in range(4):
        _slot_file(results, "2026-11-21", slot, {f"000{slot + 1}-x.json": "PASS"})
        _slot_file(results, "2026-11-22", slot, {f"000{slot + 1}-x.json": "FAIL" if slot == 2 else "PASS"},
                   status="RED" if slot == 2 else "GREEN")
    text, status = report.build("2026-11-22", results, {}, threats_total=4)
    assert status == "RED"
    assert "0003-x.json: PASS -> FAIL" in text
    first, _ = report.build("2026-11-21", results, {}, threats_total=4)
    assert "no results for the day before" in first


# 11.
def test_report_with_no_results_exits_2(tmp_path):
    assert report.main(["--day", "2026-01-01", "--results", str(tmp_path / "none")]) == 2
