"""
mutations_v2.py — File mutation engine for The Saboteur, v2

Function:
    The layer over mutations.py (SPEC_V2.md §4). v1 is not edited. Each
    v2 mutation changes exactly what its name says and nothing else:

      - Line mutations read and write bytes, so a file keeps its own
        line endings. v1 opened files in text mode, and on Windows that
        rewrote every LF as CRLF, so a "reorder" also broke every line
        ending and a tool could catch the wrong change.
      - flip_byte_text flips one bit of one letter inside a JSON string,
        so the file stays valid UTF-8 and valid JSON and only the
        signature can catch it. v1's flip (xor 0xFF mid-file) usually
        made invalid UTF-8, which tests the JSON parser, not the
        signature.
      - re_sign_wrong_key signs with a fresh key and writes the value in
        base64, as every signature in the stack is stored, keeping the
        original key_id. v1 wrote hex, so the threat tested a malformed
        signature, not a wrong key.
      - json_edit_old_as_of moves a score file's `as_of` back a year.
      - none: no change (a threat on the clean copy itself).
    Everything else is v1's.

Public API:
    1. apply_mutation(filepath, name) -> True

Internal helpers:
    2. _read_lines / _write_lines — bytes in, bytes out
    3. _reorder_lines, _duplicate_line, _replace_first_prev, _inject_placeholder
    4. _flip_byte_text
    5. _re_sign_wrong_key
    6. _json_edit_old_as_of

Tier:     Tier 2 — The Saboteur, v2
Depends:  mutations.py (v1), cryptography (wrong-key only)
Spec:     SPEC_V2.md 0.3.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import base64
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import mutations as _v1  # noqa: E402


# ---------------------------------------------------------------------------
# 2. _read_lines / _write_lines
# ---------------------------------------------------------------------------
def _read_lines(filepath):
    with open(filepath, "rb") as f:
        return f.read().splitlines(keepends=True)


def _write_lines(filepath, lines):
    with open(filepath, "wb") as f:
        f.write(b"".join(lines))


# ---------------------------------------------------------------------------
# 3. line mutations (bytes, so line endings are kept)
# ---------------------------------------------------------------------------
def _reorder_lines(filepath):
    lines = _read_lines(filepath)
    if len(lines) < 2:
        raise ValueError("need at least 2 lines to reorder")
    lines[0], lines[1] = lines[1], lines[0]
    _write_lines(filepath, lines)


def _duplicate_line(filepath):
    lines = _read_lines(filepath)
    if not lines:
        raise ValueError("empty file")
    first = lines[0] if lines[0].endswith((b"\n", b"\r")) else lines[0] + b"\n"
    if not lines[-1].endswith((b"\n", b"\r")):
        lines[-1] += b"\n"
    _write_lines(filepath, lines + [first])


def _replace_first_prev(filepath):
    lines = _read_lines(filepath)
    if not lines:
        raise ValueError("empty ledger")
    body = lines[0].rstrip(b"\r\n")
    ending = lines[0][len(body):]
    first = json.loads(body)
    first["prev"] = "0" * 64
    lines[0] = json.dumps(first, separators=(",", ":")).encode("utf-8") + ending
    _write_lines(filepath, lines)


def _inject_placeholder(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    if not data.endswith(nl):
        data += nl
    with open(filepath, "wb") as f:
        f.write(data + nl + b"COMPUTE-ON-FREEZE: document_sha256" + nl)


# ---------------------------------------------------------------------------
# 4. _flip_byte_text
#    One bit of one ASCII letter inside a JSON string value, past the
#    middle of the file; still valid JSON, still valid UTF-8.
# ---------------------------------------------------------------------------
_STRING = re.compile(rb'"(?:[^"\\]|\\.)*"')


def _flip_byte_text(filepath):
    with open(filepath, "rb") as f:
        data = bytearray(f.read())
    for m in _STRING.finditer(bytes(data), len(data) // 2):
        for i in range(m.start() + 1, m.end() - 1):
            if 0x61 <= data[i] <= 0x7A and data[i - 1] != 0x5C:  # a-z, not escaped
                data[i] ^= 0x01  # a<->b, c<->d, …: still a letter
                with open(filepath, "wb") as f:
                    f.write(data)
                json.loads(bytes(data))  # proves it is still valid JSON
                return
    raise ValueError("no lowercase letter inside a JSON string past the middle")


# ---------------------------------------------------------------------------
# 5. _re_sign_wrong_key
#    A fresh Ed25519 key over the same canonical body, base64, key_id kept.
# ---------------------------------------------------------------------------
def _re_sign_wrong_key(filepath):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    with open(filepath, "rb") as f:
        data = json.loads(f.read())
    if not isinstance(data.get("signature"), dict):
        raise ValueError("no signature block to replace")
    body = {k: v for k, v in data.items() if k != "signature"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    data["signature"]["value"] = base64.b64encode(Ed25519PrivateKey.generate().sign(canon.encode("utf-8"))).decode()
    with open(filepath, "wb") as f:
        f.write(json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8"))


# ---------------------------------------------------------------------------
# 6. _json_edit_old_as_of
# ---------------------------------------------------------------------------
def _json_edit_old_as_of(filepath):
    with open(filepath, "rb") as f:
        data = json.loads(f.read())
    if "as_of" not in data:
        raise ValueError("no as_of field")
    data["as_of"] = "2025-01-01T00:00:00Z"
    with open(filepath, "wb") as f:
        f.write(json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8"))


_V2 = {
    "none": lambda p: None,
    "reorder_lines": _reorder_lines,
    "duplicate_line": _duplicate_line,
    "replace_first_prev": _replace_first_prev,
    "inject_placeholder": _inject_placeholder,
    "flip_byte_text": _flip_byte_text,
    "re_sign_wrong_key": _re_sign_wrong_key,
    "json_edit_old_as_of": _json_edit_old_as_of,
}


# ---------------------------------------------------------------------------
# 1. apply_mutation
# ---------------------------------------------------------------------------
def apply_mutation(filepath, name):
    fn = _V2.get(name)
    if fn is None:
        return _v1.apply_mutation(filepath, name)
    fn(filepath)
    return True
