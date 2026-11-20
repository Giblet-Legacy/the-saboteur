"""
mutations_v0_9.py — The Saboteur 0.9.0 mutations: mutations_v0_8 plus rollback depth and re-formatting

Function:
    The layer over mutations_v0_8.py (SPEC_V0_9.md §2); nothing earlier
    is edited. Any name this module does not know goes to mutations_v0_8
    (then v0_5, then v2). It adds two parametrised attacks, made for
    mapping the known gaps (SPEC_V0_9 §1):

      - keep_first_lines:<N> — keep only the first N lines (a rollback
        N entries deep). Refuses N < 1 or N >= the line count.
      - json_reformat:<style> — rewrite a JSON file with the same content
        in other bytes. Styles: compact, indent4, sorted, reversed (top
        level key order), escape_letter (the first ASCII letter inside a
        string value written as a \\u escape). Refuses unchanged bytes.

Public API:
    1. apply_mutation(filepath, name) -> True

Internal helpers:
    2. _keep_first_lines(p, arg)
    3. _json_reformat(p, arg)

Tier:     Tier 2 — The Saboteur, 0.9.0
Depends:  mutations_v0_8.py
Spec:     SPEC_V0_9.md 0.9.0
Version:  0.9.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import pathlib
import re

import mutations_v0_8 as _v08


# ---------------------------------------------------------------------------
# 2. _keep_first_lines
# ---------------------------------------------------------------------------
def _keep_first_lines(p, arg):
    n = int(arg)
    path = pathlib.Path(p)
    lines = path.read_bytes().splitlines(keepends=True)
    if n < 1 or n >= len(lines):
        raise ValueError(f"keep_first_lines:{n} on {len(lines)} lines is not a rollback")
    path.write_bytes(b"".join(lines[:n]))


# ---------------------------------------------------------------------------
# 3. _json_reformat
# ---------------------------------------------------------------------------
def _escape_first_letter(text):
    # Inside the first string value (after a colon), write one ASCII
    # letter as \u00XX. The JSON content is unchanged.
    m = re.search(r':\s*"([^"\\]*?)([A-Za-z])', text)
    if not m:
        raise ValueError("json_reformat:escape_letter found no letter in a string value")
    i = m.start(2)
    return text[:i] + "\\u%04x" % ord(text[i]) + text[i + 1:]


def _json_reformat(p, style):
    path = pathlib.Path(p)
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    obj = json.loads(text)
    end = "\n" if text.endswith("\n") else ""
    if style == "compact":
        out = json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + end
    elif style == "indent4":
        out = json.dumps(obj, indent=4, ensure_ascii=False) + end
    elif style == "sorted":
        out = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + end
    elif style == "reversed":
        if not isinstance(obj, dict):
            raise ValueError("json_reformat:reversed needs an object")
        out = json.dumps(dict(reversed(list(obj.items()))), indent=2, ensure_ascii=False) + end
    elif style == "escape_letter":
        out = _escape_first_letter(text)
    else:
        raise ValueError(f"json_reformat: unknown style {style!r}")
    data = out.encode("utf-8")
    if data == raw:
        raise ValueError(f"json_reformat:{style} left the bytes unchanged, not a mutation")
    if json.loads(out) != obj:
        raise ValueError(f"json_reformat:{style} changed the content")
    path.write_bytes(data)


_WITH_ARG = {
    "keep_first_lines": _keep_first_lines,
    "json_reformat": _json_reformat,
}


# ---------------------------------------------------------------------------
# 1. apply_mutation
# ---------------------------------------------------------------------------
def apply_mutation(filepath, name):
    head, sep, arg = name.partition(":")
    if sep and head in _WITH_ARG:
        _WITH_ARG[head](filepath, arg)
        return True
    return _v08.apply_mutation(filepath, name)
