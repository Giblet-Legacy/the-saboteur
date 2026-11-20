"""
mutations_v1.py — The Saboteur 1.0.0 mutations: the whole 0.9.0 chain in one module

Function:
    The 1.0.0 consolidation (CONSOLIDATION_V1.md) of mutations.py (v1),
    mutations_v2.py, mutations_v0_5.py, mutations_v0_8.py and
    mutations_v0_9.py (archive/0.9.0). Every mutation 0.9.0's
    apply_mutation could reach is here with the same behaviour; each
    function's code is copied from the archived module named in its
    section. Functions 0.9.0 never reached (v1's five that v2 replaced)
    are left out. apply_mutation tries, in 0.9.0's order:

      1. a parametrised attack, <name>:<argument> (0.9.0, 0.8.0, 0.5.0);
      2. a plain 0.5.0 attack;
      3. a v2 attack;
      4. a v1 attack;
      else ValueError("Unknown mutation: <name>").

    A mutation that changes nothing raises, so the harness reports SKIP,
    never a pass. The attacks are listed in SPEC_V1.md §4 (and, by the
    version that added them, SPEC_V0_5 §4, SPEC_V0_8 §2, SPEC_V0_9 §2).

Public API:
    1. apply_mutation(filepath, name) -> True

Tier:     Tier 2 — The Saboteur, 1.0.0
Depends:  cryptography; envelope_v2, sign_v2, freeze_v2, substrate_v2
          (forgeries only, found at FORGE_LEGACY_ROOT, else siblings)
Spec:     SPEC_V1.md 1.0.0
Version:  1.0.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import base64
import copy
import importlib
import json
import os
import pathlib
import re
import sqlite3
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_LAYER_DIRS = ("envelope-layer", "sign-layer", "freeze-layer", "ledger-layer", "substrate-layer")


# ===========================================================================
# From mutations.py (v1): the attacks 0.9.0 still reached
# ===========================================================================


def _delete(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)


def _flip_byte(filepath):
    with open(filepath, "rb") as f:
        data = bytearray(f.read())
    if not data:
        raise ValueError("empty file")
    idx = len(data) // 2
    data[idx] ^= 0xFF
    with open(filepath, "wb") as f:
        f.write(data)


def _lf_to_crlf(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    with open(filepath, "wb") as f:
        f.write(data)


def _truncate_mid_line(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    if len(data) < 10:
        raise ValueError("file too small to truncate")
    cut = int(len(data) * 0.6)
    with open(filepath, "wb") as f:
        f.write(data[:cut])


def _json_edit(filepath, editor):
    with open(filepath) as f:
        data = json.load(f)
    editor(data)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def _set_fractional_field(data):
    decl = data.get("declaration", {})
    if isinstance(decl, dict):
        decl["sensitivity"] = 0.6


def _set_old_timestamp(data):
    data["created"] = "2020-01-01T00:00:00Z"


def _set_compute_on_freeze(filepath):
    """Overwrite document_sha256 with the unresolved placeholder."""
    with open(filepath) as f:
        data = json.load(f)
    decl = data.get("declaration", {})
    for key in ("parameters", "constraints"):
        block = decl.get(key)
        if isinstance(block, dict):
            if "document_sha256" in block:
                block["document_sha256"] = "COMPUTE-ON-FREEZE"
            ta = block.get("terminology_authority")
            if isinstance(ta, dict) and "document_sha256" in ta:
                ta["document_sha256"] = "COMPUTE-ON-FREEZE"
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# ===========================================================================
# From mutations_v2.py (0.3.x)
# ===========================================================================


def _read_lines(filepath):
    with open(filepath, "rb") as f:
        return f.read().splitlines(keepends=True)


def _write_lines(filepath, lines):
    with open(filepath, "wb") as f:
        f.write(b"".join(lines))


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

# ===========================================================================
# From mutations_v0_5.py (0.5.0)
# ===========================================================================


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


def _ledger_entry(seq, prev, record, key, signer=None):
    env = _layer("envelope_v2")
    unsigned = {"seq": seq, "prev": prev, "record": record,
                "signer": signer or env.did_key_encode(key.public_key())}
    canon = env.canonical_bytes(unsigned)
    entry = dict(unsigned)
    entry["hash"] = env.sha256_hex(canon)
    entry["signature"] = env.sign_bytes(env.sha256_digest(canon), key).hex()
    return json.dumps(entry, separators=(",", ":")).encode("ascii")


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

# ===========================================================================
# From mutations_v0_8.py (0.8.0)
# ===========================================================================


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

# ===========================================================================
# From mutations_v0_9.py (0.9.0)
# ===========================================================================


def _keep_first_lines(p, arg):
    n = int(arg)
    path = pathlib.Path(p)
    lines = path.read_bytes().splitlines(keepends=True)
    if n < 1 or n >= len(lines):
        raise ValueError(f"keep_first_lines:{n} on {len(lines)} lines is not a rollback")
    path.write_bytes(b"".join(lines[:n]))


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


# ===========================================================================
# Dispatch, in 0.9.0's order
# ===========================================================================
_V1 = {
    "flip_byte": _flip_byte,
    "lf_to_crlf": _lf_to_crlf,
    "delete": _delete,
    "truncate_mid_line": _truncate_mid_line,
    "json_edit_empty_scp_id": lambda p: _json_edit(p, lambda d: d.update({"scp_id": ""})),
    "json_edit_fractional": lambda p: _json_edit(p, _set_fractional_field),
    "json_edit_old_timestamp": lambda p: _json_edit(p, _set_old_timestamp),
    "set_compute_on_freeze": _set_compute_on_freeze,
}


_WITH_ARG = {
    # 0.9.0
    "keep_first_lines": _keep_first_lines,
    "json_reformat": _json_reformat,
    # 0.8.0
    "copy_sibling": _copy_sibling,
    "text_replace": _text_replace,
    # 0.5.0
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
    fn = _V2.get(name)
    if fn is not None:
        fn(filepath)
        return True
    fn = _V1.get(name)
    if fn is None:
        raise ValueError(f"Unknown mutation: {name}")
    fn(filepath)
    return True
