"""
build_fixture_v0_5.py — build fixture_v0_5/, the small Legacy world the Saboteur 0.5.0 attacks

Function:
    The Legacy's layers are libraries with no command line, and James's
    own ~/.forge holds his key, so neither can be a Saboteur target
    (SPEC_V0_5.md §2). This builds a stand-in made by the real layers:
    a P5/P4 ledger, P2 capsules and signed documents, P3 frozen
    capsules, P7 records, P15 seals with a λ attestation, a P8 store
    and a P9 substrate. Two throwaway Ed25519 keys sign it (owner and
    attester); only their public did:keys are kept, the private keys
    are never written. manifest.json lists every file and what checks
    it. legacy_check_v0_5.py (already in the folder) is the tool the
    threats run.

    python build_fixture_v0_5.py [--out fixture_v0_5] [--force]

    The fixture is committed. Rebuilding makes new keys, so every
    signature changes; do it only when a layer's format changes.

Public API:
    1. build(out) -> dict   (the manifest)
    2. main(argv=None) -> int

Internal helpers:
    3. _layers(root) — put the Legacy layer folders on sys.path

Tier:     Tier 2 — The Saboteur, 0.5.0
Depends:  envelope_v2, sign_v2, freeze_v2, ledger_v2, genesis_v3,
          record_v2, hal_v2, store_v2_1, substrate_v4 (siblings of
          the-saboteur, or FORGE_LEGACY_ROOT)
Spec:     SPEC_V0_5.md 0.5.0
Version:  0.5.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import json
import os
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
LAYER_DIRS = ("envelope-layer", "sign-layer", "freeze-layer", "ledger-layer", "genesis-layer",
              "record-layer", "hal-layer", "store-layer", "substrate-layer", "canon-verify-layer")
# Files the builder writes; legacy_check_v0_5.py and README.md are source, kept on a rebuild.
_KEEP = {"legacy_check_v0_5.py", "README.md"}


# ---------------------------------------------------------------------------
# 3. _layers
# ---------------------------------------------------------------------------
def _layers(root):
    for d in LAYER_DIRS:
        p = str(pathlib.Path(root) / d)
        if p not in sys.path:
            sys.path.insert(0, p)


def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("ascii"))


# ---------------------------------------------------------------------------
# 1. build
# ---------------------------------------------------------------------------
def build(out):
    root = os.environ.get("FORGE_LEGACY_ROOT") or str(HERE.parent)
    _layers(root)
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    import envelope_v2
    import freeze_v2
    import genesis_v3
    import hal_v2
    import ledger_v2
    import record_v2
    import sign_v2
    import store_v2_1
    import substrate_v4

    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for item in out.iterdir():
        if item.name in _KEEP:
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()

    owner, attester = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    owner_did = envelope_v2.did_key_encode(owner.public_key())
    attester_did = envelope_v2.did_key_encode(attester.public_key())
    (out / "keys").mkdir()
    (out / "keys" / "owner.did").write_bytes((owner_did + "\n").encode("ascii"))
    (out / "keys" / "attester.did").write_bytes((attester_did + "\n").encode("ascii"))
    manifest = {}

    # P5 genesis + P4 ledger: six entries.
    ledger = str(out / "ledger.jsonl")
    genesis_v3.mint_genesis(ledger, {"kind": "genesis", "name": "saboteur fixture"}, owner)
    for i, (s, o) in enumerate([("the forge", "is in Wales"), ("the legacy", "outlasts its maker"),
                                ("the field", "shows the claims"), ("the voice", "speaks in polarity"),
                                ("the saboteur", "attacks a copy")], 1):
        ledger_v2.append_entry(ledger, {"kind": "claim", "n": i, "subject": s, "object": o, "face": "FACT"}, owner)
    manifest["ledger.jsonl"] = "ledger"

    # P2 capsules.
    for name, body in [("claim-forge", {"type": "claim", "subject": "the forge", "object": "is in Wales",
                                        "face": "FACT", "created": "2026-11-20T00:00:00Z"}),
                       ("entity-james", {"type": "entity", "name": "James Gilbert", "kind": "person",
                                         "created": "2026-11-20T00:00:00Z"}),
                       ("policy-writes", {"type": "policy", "rule": "every write is signed",
                                          "declaration": {"sensitivity": "0.6", "scope": "the legacy"}})]:
        _write_json(out / "capsules" / f"{name}.sc.json", sign_v2.sign_capsule(body, owner))
        manifest[f"capsules/{name}.sc.json"] = "capsule"

    # P3 frozen capsules.
    for name, body in [("spec-sign", {"type": "spec", "layer": "P2", "version": "2.0.0",
                                      "text": "every signature goes through sign.py"}),
                       ("spec-ledger", {"type": "spec", "layer": "P4", "version": "2.0.0",
                                        "text": "LF only, compact lines, six typed fields"})]:
        _write_json(out / "frozen" / f"{name}.sc.json", freeze_v2.freeze_capsule(body, owner))
        manifest[f"frozen/{name}.sc.json"] = "frozen"

    # P7 records (record_v2 writes them itself).
    (out / "records").mkdir()
    for name, body in [("note-morning", {"type": "note", "text": "the morning voice ran", "day": "2026-11-20"}),
                       ("note-boot", {"type": "note", "text": "boot_v2 started three services", "day": "2026-11-20"})]:
        record_v2.save_signed_record(body, str(out / "records" / f"{name}.sc.json"), owner)
        manifest[f"records/{name}.sc.json"] = "record"

    # P2 signed documents with .sig sidecars.
    (out / "docs").mkdir()
    for name, text in [("charter.md", "# Charter\n\nThe Legacy is meant to outlast its maker.\n"
                                      "Never rewrite a primitive. Add a layer.\n"),
                       ("glossary.md", "# Glossary\n\nclaim: a signed statement with a face.\n"
                                       "seal: a signed HAL decision.\n")]:
        p = out / "docs" / name
        p.write_bytes(text.encode("ascii"))
        sign_v2.sign_artifact(str(p), owner)
        manifest[f"docs/{name}"] = "artefact"

    # P15 seals, each with an attester-signed λ attestation.
    for name, (decision, lam) in [("seal-approve", ("approve", 0.82)), ("seal-refuse", ("refuse", 0.64))]:
        att = hal_v2.attest_lambda(owner_did, lam, 1795000000, attester)
        seal = hal_v2.create_seal(decision, "claim.commit", f"claim-{name}", "fixture decision", lam,
                                  1795000100, attestation=att, attester_public_key=attester.public_key())
        _write_json(out / "seals" / f"{name}.json", hal_v2.sign_seal(seal, owner))
        manifest[f"seals/{name}.json"] = "seal"

    # P8 store: four entries.
    store = str(out / "store.db")
    store_v2_1.init_db(store)
    for i in range(4):
        store_v2_1.append_entry(store, {"kind": "mirror", "n": i, "text": f"stored entry {i}"}, owner)
    manifest["store.db"] = "store"

    # P9 substrate: two entities, one subject, one membership.
    sub = str(out / "substrate.db")
    substrate_v4.init_db(sub)
    james = substrate_v4.add_entity(sub, "James Gilbert", owner, kind="person")
    substrate_v4.add_entity(sub, "The Forge", owner, kind="place")
    legacy = substrate_v4.add_subject(sub, "The Legacy", owner)
    substrate_v4.add_member(sub, legacy, james, owner)
    manifest["substrate.db"] = "substrate"

    _write_json(out / "manifest.json", {"owner": "keys/owner.did", "attester": "keys/attester.did",
                                        "files": manifest})
    return manifest


# ---------------------------------------------------------------------------
# 2. main
# ---------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description="Build the Saboteur 0.5.0 fixture (throwaway keys).")
    p.add_argument("--out", default=str(HERE / "fixture_v0_5"))
    p.add_argument("--force", action="store_true", help="rebuild even if a manifest exists")
    args = p.parse_args(argv)
    if (pathlib.Path(args.out) / "manifest.json").exists() and not args.force:
        print(f"fixture exists at {args.out}; --force rebuilds it with new keys", file=sys.stderr)
        return 2
    files = build(args.out)
    print(f"built {len(files)} checked files in {args.out} (private keys discarded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
