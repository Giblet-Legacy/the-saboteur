"""
legacy_check_v0_5.py — ask the Legacy's own layers about every file in this fixture

Function:
    The tool every Saboteur 0.5.0 threat runs (SPEC_V0_5.md §3). It reads
    manifest.json, then hands each listed file to the layer that owns
    it, through that layer's public verify call, under the owner's
    public did:key (keys/owner.did). It adds no judgement of its own
    beyond "the file is missing" and "the file is not JSON" (for the
    layers that take a dict): every other verdict is the layer's.

    One line per check, then exit 1 if any check is not ok:
        ok     <file>  <layer>.<call>
        FAILED <file>: <layer>.<call> said no
        FAILED <file>: <layer>.<call> refused it (<Error>: <message>)
        RAISED <file>: <layer>.<call> raised <Error>: <message>
    RAISED is for a layer whose spec says it never raises on bad
    content: the raise is itself a broken promise, and no threat
    expects it.

    python legacy_check_v0_5.py [--layer NAME]

    --layer runs only the checks of one layer module (e.g. canon_verify_v2).
    The layers are found at FORGE_LEGACY_ROOT, else two folders up
    (the-saboteur's siblings).

Public API:
    1. checks(fixture, layer=None) -> [(status, file, layer, call, detail)]
    2. main(argv=None) -> int

Internal helpers:
    3. _root, 4. _import, 5. _load_json, 6. _call

Tier:     Tier 2 — The Saboteur, 0.5.0
Spec:     SPEC_V0_5.md 0.5.0
Version:  0.5.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import importlib
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
LAYER_DIRS = ("envelope-layer", "sign-layer", "freeze-layer", "ledger-layer", "genesis-layer",
              "record-layer", "hal-layer", "store-layer", "substrate-layer", "canon-verify-layer")


# ---------------------------------------------------------------------------
# 3. _root / 4. _import
# ---------------------------------------------------------------------------
def _root():
    return pathlib.Path(os.environ.get("FORGE_LEGACY_ROOT") or HERE.parent.parent)


def _import(name):
    for d in LAYER_DIRS:
        p = str(_root() / d)
        if p not in sys.path:
            sys.path.insert(0, p)
    return importlib.import_module(name)


# ---------------------------------------------------------------------------
# 5. _load_json — the fixture's own read, for the layers that take a dict
# ---------------------------------------------------------------------------
def _load_json(path):
    try:
        return json.loads(path.read_bytes().decode("utf-8")), None
    except (ValueError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# 6. _call — one layer call, mapped to a status
#    may_raise: the layer's spec lets it raise on this input (a refusal).
# ---------------------------------------------------------------------------
def _call(fn, args, may_raise):
    try:
        result = fn(*args)
    except Exception as e:  # noqa: BLE001 — every raise is reported, never hidden
        msg = f"{type(e).__name__}: {str(e)[:160]}"
        return ("FAILED", f"refused it ({msg})") if may_raise else ("RAISED", f"raised {msg}")
    return ("ok", "") if result else ("FAILED", "said no")


# ---------------------------------------------------------------------------
# 1. checks
# ---------------------------------------------------------------------------
def checks(fixture, layer=None):
    fixture = pathlib.Path(fixture)
    manifest = json.loads((fixture / "manifest.json").read_text(encoding="utf-8"))
    env = _import("envelope_v2")
    pub = env.did_key_decode((fixture / manifest["owner"]).read_text(encoding="ascii").strip())
    att = env.did_key_decode((fixture / manifest["attester"]).read_text(encoding="ascii").strip())
    owner_did = env.did_key_encode(pub)
    out = []

    def run(rel, mod, call, args, may_raise=False):
        if layer and layer != mod:
            return
        fn = getattr(_import(mod), call)
        status, detail = _call(fn, args, may_raise)
        out.append((status, rel, mod, call, detail))

    def run_dict(rel, mod, call, extra, may_raise=False):
        if layer and layer != mod:
            return
        obj, err = _load_json(fixture / rel)
        if err:
            out.append(("FAILED", rel, mod, call, f"not JSON ({err[:120]})"))
            return
        run(rel, mod, call, (obj,) + extra, may_raise)

    for rel, kind in manifest["files"].items():
        path = fixture / rel
        if not path.exists():
            out.append(("FAILED", rel, "manifest", "files", "missing"))
            continue
        p = str(path)
        if kind == "ledger":
            run(rel, "ledger_v2", "verify_ledger", (p, pub))
            run(rel, "canon_verify_v2", "verify_ledger", (p, owner_did))
            run(rel, "genesis_v3", "verify_genesis", (p, pub))
        elif kind == "capsule":
            run_dict(rel, "sign_v2", "verify_capsule", (pub,))
        elif kind == "frozen":
            run_dict(rel, "freeze_v2", "verify_frozen_capsule", (pub,))
        elif kind == "record":
            run(rel, "record_v2", "verify_record_file", (p, pub))
        elif kind == "artefact":
            # SPEC_V2 §2 of P2: a missing file or sidecar raises.
            run(rel, "sign_v2", "verify_artifact", (p, p + ".sig", pub), may_raise=True)
        elif kind == "seal":
            run_dict(rel, "hal_v2", "verify_seal", (pub, att))
        elif kind == "store":
            run(rel, "store_v2_1", "verify_store", (p, pub))
        elif kind == "substrate":
            for call in ("list_entities", "list_subjects"):
                if layer and layer != "substrate_v4":
                    continue
                try:
                    rows = getattr(_import("substrate_v4"), call)(p, verify=True)
                except Exception as e:  # noqa: BLE001
                    out.append(("FAILED", rel, "substrate_v4", call, f"refused it ({type(e).__name__}: {e})"))
                    continue
                bad = [r for r in rows if not r.get("verified")]
                if bad:
                    out.append(("FAILED", rel, "substrate_v4", call,
                                f"said no to {bad[0].get('id')} ({bad[0].get('verify_error')})"))
                else:
                    out.append(("ok", rel, "substrate_v4", call, f"{len(rows)} rows"))
    return out


# ---------------------------------------------------------------------------
# 2. main
# ---------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description="Check every fixture file through its Legacy layer.")
    p.add_argument("--layer", help="only this layer module's checks (e.g. ledger_v2)")
    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    results = checks(HERE, args.layer)
    bad = 0
    for status, rel, mod, call, detail in results:
        if status == "ok":
            print(f"ok     {rel}  {mod}.{call}" + (f" ({detail})" if detail else ""))
        else:
            bad += 1
            print(f"{status} {rel}: {mod}.{call} {detail}")
    print(f"legacy_check: {len(results)} checks, {bad} not ok")
    if not results:
        print("legacy_check: nothing checked", file=sys.stderr)
        return 2
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
