"""
mutations_v0_8.py — The Saboteur 0.8.0 mutations: mutations_v0_5 plus substitution and text edits

Function:
    The layer over mutations_v0_5.py (SPEC_V0_8.md §2); neither it nor
    v2 is edited. Any name this module does not know goes to
    mutations_v0_5 (and from there to v2). It adds two parametrised
    attacks:

      - copy_sibling:<relative path> — replace the victim with the bytes
        of another fixture file, a valid signed file standing in for
        another (substitution). The path is relative to the victim's
        folder, must not be absolute and must stay inside the fixture
        (at most one level up). Refuses identical bytes.
      - text_replace:<old>=><new> — replace the first <old> in a text
        file with <new>. Refuses when <old> is absent or the result is
        unchanged.

    A mutation that changes nothing raises, so the harness reports SKIP,
    never a pass.

Public API:
    1. apply_mutation(filepath, name) -> True

Internal helpers:
    2. _copy_sibling(p, arg)
    3. _text_replace(p, arg)

Tier:     Tier 2 — The Saboteur, 0.8.0
Depends:  mutations_v0_5.py
Spec:     SPEC_V0_8.md 0.8.0
Version:  0.8.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import pathlib

import mutations_v0_5 as _v05


# ---------------------------------------------------------------------------
# 2. _copy_sibling
# ---------------------------------------------------------------------------
def _copy_sibling(p, arg):
    victim = pathlib.Path(p).resolve()
    rel = pathlib.PurePosixPath(arg)
    if not arg or rel.is_absolute() or ":" in arg:
        raise ValueError(f"copy_sibling needs a relative path, got {arg!r}")
    source = (victim.parent / rel).resolve()
    top = victim.parent.parent
    if top not in source.parents:
        raise ValueError(f"copy_sibling source is outside the fixture: {arg!r}")
    if not source.is_file():
        raise ValueError(f"copy_sibling source missing: {arg!r}")
    data = source.read_bytes()
    if data == victim.read_bytes():
        raise ValueError("copy_sibling: identical bytes, not a mutation")
    victim.write_bytes(data)


# ---------------------------------------------------------------------------
# 3. _text_replace
# ---------------------------------------------------------------------------
def _text_replace(p, arg):
    old, sep, new = arg.partition("=>")
    if not sep or not old:
        raise ValueError("text_replace needs old=>new")
    path = pathlib.Path(p)
    data = path.read_bytes()
    o, n = old.encode("utf-8"), new.encode("utf-8")
    if o not in data:
        raise ValueError(f"text_replace: {old!r} not found")
    out = data.replace(o, n, 1)
    if out == data:
        raise ValueError("text_replace: unchanged, not a mutation")
    path.write_bytes(out)


_WITH_ARG = {
    "copy_sibling": _copy_sibling,
    "text_replace": _text_replace,
}


# ---------------------------------------------------------------------------
# 1. apply_mutation
# ---------------------------------------------------------------------------
def apply_mutation(filepath, name):
    head, sep, arg = name.partition(":")
    if sep and head in _WITH_ARG:
        _WITH_ARG[head](filepath, arg)
        return True
    return _v05.apply_mutation(filepath, name)
