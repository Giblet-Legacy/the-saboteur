"""
mutations_v0_5.py — the Saboteur 0.5.0's mutations: v2's, plus attacks on the Legacy's own files

Function:
    The layer over mutations_v2.py (SPEC_V0_5.md §4). v2 and v1 are not
    edited; any name this file does not know is handed to v2.

    Line and byte attacks (bytes in, bytes out; line endings kept):
      drop_first_line, drop_middle_line, drop_last_line, swap_middle_lines,
      duplicate_last_line, blank_line, trailing_space, add_bom, empty,
      non_ascii, reorder_keys_first_line, flip_letter (v2's flip_byte_text
      as meant: it scanned from mid-file and could land inside a string,
      so it found no letter in any fixture file; v2 is not edited)

    Parametrised attacks, so a new attack is a new threat file, not new
    code (CLAUDE.md, discipline 2). The argument follows a colon:
      json_set:<dotted.path>=<JSON value>   (NaN and Infinity allowed)
      json_drop:<dotted.path>
      json_dup_key_first:<key>=<JSON value> a duplicate key placed BEFORE
                                            the real one, so a last-wins
                                            parser still sees the original
      line_dup_key:<line>:<key>=<JSON value> the same, inside one .jsonl line
      line_set:<line>:<key>=<JSON value>    one field of one .jsonl line; refused
                                            if it already has that value
      sqlite:<SQL>                          one statement on a database

    Forgeries, made with a fresh attacker key through the Legacy's own
    layers (so each is well formed and only the key is wrong):
      resign_attacker          — re-sign a capsule, attacker key_id
      resign_attacker_edit:<dotted.path>=<JSON value> — edit, then re-sign
      resign_keep_key_id       — new signature value (hex), owner key_id kept
      refreeze_attacker        — re-freeze and re-sign a frozen capsule
      rehash_frozen:<dotted.path>=<JSON value> — edit and recompute
                                 document_sha256; old signature kept
      resign_sidecar_attacker  — re-sign a document's .sig sidecar
      edit_and_resign_sidecar  — add a line to a document, re-sign its .sig
      ledger_append_attacker   — a correctly chained entry, attacker signer
      ledger_rewrite_last_attacker — last entry's record changed, re-hashed,
                                 re-signed, attacker signer
      ledger_rewrite_last_keep_signer — the same with the owner's did kept
      substrate_forge_last:<table> — last row of entities/subjects replaced
                                 by an attacker-signed capsule, same name

Public API:
    1. apply_mutation(filepath, name) -> True

Internal helpers:
    2. _lines / _put — bytes lines in and out
    3. _path_set / _path_drop — dotted paths into JSON
    4. _layer — a Legacy layer module (FORGE_LEGACY_ROOT, else siblings)
    5. _ledger_entry — a v1-shaped ledger entry signed by any key

Tier:     Tier 2 — The Saboteur, 0.5.0
Depends:  mutations_v2.py; envelope_v2, sign_v2, freeze_v2,
          substrate_v2 (forgeries only); cryptography
Spec:     SPEC_V0_5.md 0.5.0
Version:  0.5.0-dev
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import copy
import importlib
import json
import os
import pathlib
import re
import sqlite3
import sys

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import mutations_v2 as _v2  # noqa: E402

_LAYER_DIRS = ("envelope-layer", "sign-layer", "freeze-layer", "ledger-layer", "substrate-layer")


# ---------------------------------------------------------------------------
# 2. _lines / _put
# ---------------------------------------------------------------------------
def _lines(p):
    data = pathlib.Path(p).read_bytes()
    return data.splitlines(keepends=True)


def _put(p, lines):
    pathlib.Path(p).write_bytes(b"".join(lines))


def _nl(line):
    return line[len(line.rstrip(b"\r\n")):] or b"\n"


def _need(lines, n):
    if len(lines) < n:
        raise ValueError(f"need at least {n} lines")


# ---------------------------------------------------------------------------
# 3. _path_set / _path_drop
# ---------------------------------------------------------------------------
def _split_arg(arg):
    path, _, value = arg.partition("=")
    if not path:
        raise ValueError("no path given")
    return path, json.loads(value) if value else None


def _walk(obj, path):
    parts = path.split(".")
    for part in parts[:-1]:
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj, parts[-1]


def _path_set(obj, path, value):
    parent, last = _walk(obj, path)
    if isinstance(parent, list):
        parent[int(last)] = value
    else:
        parent[last] = value


def _path_drop(obj, path):
    parent, last = _walk(obj, path)
    if isinstance(parent, list):
        del parent[int(last)]
    elif last in parent:
        del parent[last]
    else:
        raise ValueError(f"no field {path}")


def _read_json(p):
    return json.loads(pathlib.Path(p).read_bytes().decode("utf-8"))


def _write_json(p, obj):
    pathlib.Path(p).write_bytes((json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8"))


# ---------------------------------------------------------------------------
# 4. _layer
# ---------------------------------------------------------------------------
def _layer(name):
    root = pathlib.Path(os.environ.get("FORGE_LEGACY_ROOT") or _HERE.parent)
    for d in _LAYER_DIRS:
        s = str(root / d)
        if s not in sys.path:
            sys.path.insert(0, s)
    return importlib.import_module(name)


def _attacker():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    return Ed25519PrivateKey.generate()


# ---------------------------------------------------------------------------
# 5. _ledger_entry — ledger.py v1's construction, any key, any signer text
# ---------------------------------------------------------------------------
def _ledger_entry(seq, prev, record, key, signer=None):
    env = _layer("envelope_v2")
    unsigned = {"seq": seq, "prev": prev, "record": record,
                "signer": signer or env.did_key_encode(key.public_key())}
    canon = env.canonical_bytes(unsigned)
    entry = dict(unsigned)
    entry["hash"] = env.sha256_hex(canon)
    entry["signature"] = env.sign_bytes(env.sha256_digest(canon), key).hex()
    return json.dumps(entry, separators=(",", ":")).encode("ascii")


# ---------------------------------------------------------------------------
# line and byte attacks
# ---------------------------------------------------------------------------
def _drop_first_line(p):
    lines = _lines(p); _need(lines, 2); _put(p, lines[1:])


def _drop_middle_line(p):
    lines = _lines(p); _need(lines, 3); del lines[len(lines) // 2]; _put(p, lines)


def _drop_last_line(p):
    lines = _lines(p); _need(lines, 2); _put(p, lines[:-1])


def _swap_middle_lines(p):
    lines = _lines(p); _need(lines, 4)
    lines[1], lines[2] = lines[2], lines[1]
    _put(p, lines)


def _duplicate_last_line(p):
    lines = _lines(p); _need(lines, 1); _put(p, lines + [lines[-1]])


def _blank_line(p):
    lines = _lines(p); _need(lines, 2); lines.insert(1, _nl(lines[0])); _put(p, lines)


def _trailing_space(p):
    lines = _lines(p); _need(lines, 1)
    body = lines[0].rstrip(b"\r\n")
    lines[0] = body + b" " + lines[0][len(body):]
    _put(p, lines)


def _add_bom(p):
    data = pathlib.Path(p).read_bytes()
    pathlib.Path(p).write_bytes(b"\xef\xbb\xbf" + data)


def _empty(p):
    pathlib.Path(p).write_bytes(b"")


def _non_ascii(p):
    data = pathlib.Path(p).read_bytes()
    i = data.find(b"e", len(data) // 2)
    if i < 0:
        raise ValueError("no 'e' past the middle")
    pathlib.Path(p).write_bytes(data[:i] + "é".encode("utf-8") + data[i + 1:])


_STRING = re.compile(rb'"(?:[^"\\]|\\.)*"')


def _flip_letter(p):
    # v2's flip_byte_text starts its string search mid-file, often inside a
    # string, so it sees the gaps between strings and finds no letter.
    # This scans from the start and flips a letter in the first string
    # that begins past the middle (else the last string with a letter).
    data = bytearray(pathlib.Path(p).read_bytes())
    spots = []
    for m in _STRING.finditer(bytes(data)):
        for i in range(m.start() + 1, m.end() - 1):
            if 0x61 <= data[i] <= 0x7A and data[i - 1] != 0x5C:
                spots.append((m.start(), i))
                break
    if not spots:
        raise ValueError("no lowercase letter inside a JSON string")
    i = next((i for start, i in spots if start >= len(data) // 2), spots[-1][1])
    data[i] ^= 0x01  # a<->b, c<->d, …: still a letter, still valid JSON
    pathlib.Path(p).write_bytes(bytes(data))


def _line_set(p, arg):
    n, _, rest = arg.partition(":")
    lines = _lines(p); n = int(n); _need(lines, n + 1)
    key, value = _split_arg(rest)
    obj = json.loads(lines[n].rstrip(b"\r\n"))
    if obj.get(key) == value:
        raise ValueError(f"line {n} already has {key}={value!r}: not a mutation")
    obj[key] = value
    lines[n] = json.dumps(obj, separators=(",", ":")).encode("ascii") + _nl(lines[n])
    _put(p, lines)


def _reorder_keys_first_line(p):
    lines = _lines(p); _need(lines, 1)
    body = lines[0].rstrip(b"\r\n")
    obj = json.loads(body)
    flipped = dict(reversed(list(obj.items())))
    lines[0] = json.dumps(flipped, separators=(",", ":")).encode("ascii") + _nl(lines[0])
    _put(p, lines)


# ---------------------------------------------------------------------------
# parametrised attacks
# ---------------------------------------------------------------------------
def _json_set(p, arg):
    path, value = _split_arg(arg)
    obj = _read_json(p); _path_set(obj, path, value); _write_json(p, obj)


def _json_drop(p, arg):
    obj = _read_json(p); _path_drop(obj, arg); _write_json(p, obj)


def _dup_value(arg):
    key, value = _split_arg(arg)
    return b'"' + key.encode("ascii") + b'":' + json.dumps(value).encode("utf-8") + b","


def _json_dup_key_first(p, arg):
    data = pathlib.Path(p).read_bytes()
    i = data.index(b"{")
    pathlib.Path(p).write_bytes(data[:i + 1] + _dup_value(arg) + data[i + 1:])


def _line_dup_key(p, arg):
    n, _, rest = arg.partition(":")
    lines = _lines(p); n = int(n); _need(lines, n + 1)
    i = lines[n].index(b"{")
    lines[n] = lines[n][:i + 1] + _dup_value(rest) + lines[n][i + 1:]
    _put(p, lines)


def _sqlite(p, sql):
    with sqlite3.connect(p) as conn:
        conn.execute(sql)
        if conn.total_changes == 0 and sql.strip().upper().startswith(("UPDATE", "DELETE")):
            raise ValueError(f"sqlite: no row changed by {sql!r}")
    conn.close()


# ---------------------------------------------------------------------------
# forgeries
# ---------------------------------------------------------------------------
def _body(p):
    obj = _read_json(p)
    obj.pop("signature", None)
    return obj


def _resign_attacker(p):
    _write_json(p, _layer("sign_v2").sign_capsule(_body(p), _attacker()))


def _resign_attacker_edit(p, arg):
    path, value = _split_arg(arg)
    body = _body(p); _path_set(body, path, value)
    _write_json(p, _layer("sign_v2").sign_capsule(body, _attacker()))


def _resign_keep_key_id(p):
    obj = _read_json(p)
    if not isinstance(obj.get("signature"), dict):
        raise ValueError("no signature block")
    forged = _layer("sign_v2").sign_capsule(_body(p), _attacker())
    obj["signature"]["value"] = forged["signature"]["value"]
    _write_json(p, obj)


def _refreeze_attacker(p):
    body = _body(p); body.pop("document_sha256", None)
    _write_json(p, _layer("freeze_v2").freeze_capsule(body, _attacker()))


def _rehash_frozen(p, arg):
    path, value = _split_arg(arg)
    env = _layer("envelope_v2")
    obj = _read_json(p); _path_set(obj, path, value)
    payload = copy.deepcopy(obj); payload.pop("signature", None); payload["document_sha256"] = None
    obj["document_sha256"] = env.sha256_hex(env.canonical_bytes(payload))
    _write_json(p, obj)


def _resign_sidecar_attacker(p):
    _layer("sign_v2").sign_artifact(str(p), _attacker())


def _edit_and_resign_sidecar(p):
    data = pathlib.Path(p).read_bytes()
    pathlib.Path(p).write_bytes(data + b"The Saboteur was here.\n")
    _layer("sign_v2").sign_artifact(str(p), _attacker())


def _ledger_append_attacker(p):
    lines = _lines(p); _need(lines, 1)
    last = json.loads(lines[-1])
    line = _ledger_entry(last["seq"] + 1, last["hash"], {"kind": "claim", "subject": "the saboteur",
                                                          "object": "owns the ledger"}, _attacker())
    _put(p, lines + [line + b"\n"])


def _rewrite_last(p, keep_signer):
    lines = _lines(p); _need(lines, 2)
    last = json.loads(lines[-1])
    record = dict(last["record"]); record["object"] = "was rewritten"
    line = _ledger_entry(last["seq"], last["prev"], record, _attacker(),
                         signer=last["signer"] if keep_signer else None)
    _put(p, lines[:-1] + [line + _nl(lines[-1])])


def _substrate_forge_last(p, table):
    if table not in ("entities", "subjects"):
        raise ValueError("table must be entities or subjects")
    pk = "entity_id" if table == "entities" else "subject_id"
    sub2 = _layer("substrate_v2")
    with sqlite3.connect(p) as conn:
        row = conn.execute(f"SELECT rowid, {pk}, capsule FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
        if not row:
            raise ValueError(f"no rows in {table}")
        body = json.loads(row[2]); body.pop("signature", None)
        new_id, text, signed = sub2._seal(body, _attacker())
        conn.execute(f"UPDATE {table} SET {pk}=?, signer=?, capsule=? WHERE rowid=?",
                     (new_id, signed["signature"]["key_id"], text, row[0]))
    conn.close()


_PLAIN = {
    "drop_first_line": _drop_first_line,
    "drop_middle_line": _drop_middle_line,
    "drop_last_line": _drop_last_line,
    "swap_middle_lines": _swap_middle_lines,
    "duplicate_last_line": _duplicate_last_line,
    "blank_line": _blank_line,
    "trailing_space": _trailing_space,
    "add_bom": _add_bom,
    "empty": _empty,
    "non_ascii": _non_ascii,
    "reorder_keys_first_line": _reorder_keys_first_line,
    "flip_letter": _flip_letter,
    "resign_attacker": _resign_attacker,
    "resign_keep_key_id": _resign_keep_key_id,
    "refreeze_attacker": _refreeze_attacker,
    "resign_sidecar_attacker": _resign_sidecar_attacker,
    "edit_and_resign_sidecar": _edit_and_resign_sidecar,
    "ledger_append_attacker": _ledger_append_attacker,
    "ledger_rewrite_last_attacker": lambda p: _rewrite_last(p, False),
    "ledger_rewrite_last_keep_signer": lambda p: _rewrite_last(p, True),
}
_WITH_ARG = {
    "json_set": _json_set,
    "json_drop": _json_drop,
    "json_dup_key_first": _json_dup_key_first,
    "line_dup_key": _line_dup_key,
    "line_set": _line_set,
    "sqlite": _sqlite,
    "resign_attacker_edit": _resign_attacker_edit,
    "rehash_frozen": _rehash_frozen,
    "substrate_forge_last": _substrate_forge_last,
}


# ---------------------------------------------------------------------------
# 1. apply_mutation
# ---------------------------------------------------------------------------
def apply_mutation(filepath, name):
    head, sep, arg = name.partition(":")
    if sep and head in _WITH_ARG:
        _WITH_ARG[head](filepath, arg)
        return True
    if name in _PLAIN:
        _PLAIN[name](filepath)
        return True
    return _v2.apply_mutation(filepath, name)
