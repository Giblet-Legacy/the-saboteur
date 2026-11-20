"""
mutations.py — File mutation engine for The Saboteur

Function:
    Applies one mutation at a time to a scratch copy of a target file.
    All mutations are local file operations. No network.

Tier:     Tier 2 — The Saboteur
Licence:  MSL-1.0
"""

import os
import json


def apply_mutation(filepath, mutation_name):
    """Applies the named mutation to filepath in place."""
    dispatch = {
        "flip_byte": _flip_byte,
        "lf_to_crlf": _lf_to_crlf,
        "delete": _delete,
        "reorder_lines": _reorder_lines,
        "truncate_mid_line": _truncate_mid_line,
        "replace_first_prev": _replace_first_prev,
        "inject_placeholder": _inject_placeholder,
        "json_edit_empty_scp_id": lambda p: _json_edit(p, lambda d: d.update({"scp_id": ""})),
        "json_edit_fractional": lambda p: _json_edit(p, _set_fractional_field),
        "json_edit_old_timestamp": lambda p: _json_edit(p, _set_old_timestamp),
        "re_sign_wrong_key": _resign_wrong_key,
        "duplicate_line": _duplicate_line,
        "set_compute_on_freeze": _set_compute_on_freeze,
    }
    fn = dispatch.get(mutation_name)
    if fn is None:
        raise ValueError(f"Unknown mutation: {mutation_name}")
    fn(filepath)
    return True


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


def _reorder_lines(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    if len(lines) < 2:
        raise ValueError("need at least 2 lines to reorder")
    lines[0], lines[1] = lines[1], lines[0]
    with open(filepath, "w") as f:
        f.writelines(lines)


def _replace_first_prev(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    if not lines:
        raise ValueError("empty ledger")
    first = json.loads(lines[0])
    first["prev"] = "0" * 64
    lines[0] = json.dumps(first, separators=(",", ":")) + "\n"
    with open(filepath, "w") as f:
        f.writelines(lines)


def _duplicate_line(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    if not lines:
        raise ValueError("empty ledger")
    lines.append(lines[0])
    with open(filepath, "w") as f:
        f.writelines(lines)


def _inject_placeholder(filepath):
    with open(filepath) as f:
        content = f.read()
    if not content.endswith("\n"):
        content += "\n"
    content += "\nCOMPUTE-ON-FREEZE: document_sha256\n"
    with open(filepath, "w") as f:
        f.write(content)


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


def _resign_wrong_key(filepath):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    import hashlib
    with open(filepath) as f:
        data = json.load(f)
    if "signature" in data and isinstance(data["signature"], dict):
        key = Ed25519PrivateKey.generate()
        body = {k: v for k, v in data.items() if k != "signature"}
        canon = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        sig = key.sign(canon.encode("utf-8"))
        data["signature"]["value"] = sig.hex()
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)



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
