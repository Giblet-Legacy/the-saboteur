# SPEC V0.6 — the-saboteur (Tier 2: The Saboteur), 200 threats

SPEC_V0_6.md — what saboteur_v0_6.py adds over the frozen 0.5.1.

Function:
    James, 2026-11-20: "200 tests for saboteur". 0.6.0 takes the
    threats from 108 to 200. SPEC_V0_5.md stays authoritative for the
    fixture, the check tool and the mutations; SPEC_V0_5_1.md for the
    run lock; SPEC_V2.md for the harness. Nothing frozen is edited.

Tier:      Tier 2 — The Saboteur
Depends:   saboteur_v0_5_1.py (and through it 0.5.0 and v2, unchanged)
Version:   SPEC V0.6 0.6.0-dev
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. saboteur_v0_6.py

    python saboteur_v0_6.py [--target fixture_v0_5] [--threats threats_v0_6] [--parent DIR] [--only NNN]

- The run is 0.5.1's: the run lock, then 0.5.0's harness, fixture and
  mutations.
- 0.6.0 only changes the default threats, to `threats_v0_6/`.
- No new mutation code. Every new threat is data that names one of
  0.5.0's mutations (CLAUDE.md discipline 2).

## 2. threats_v0_6/: 200 threats

- **001–108:** `threats_v0_5/`, copied byte for byte.
- **109–200:** new. They reach the fixture files 0.5.0 never attacked:
  the glossary and its sidecar, `spec-ledger`, `note-boot` and
  `seal-refuse`. They also reach the fields 0.5.0 left alone.

| Layer | New | Numbers | Total |
|---|---|---|---|
| ledger_v2 (P4) | 16 | 109–124 | 38 |
| canon_verify_v2 (P6) | 6 | 125–130 | 21 |
| genesis_v3 (P5) | 5 | 131–135 | 8 |
| store_v2_1 (P8) | 10 | 136–145 | 20 |
| sign_v2 capsules (P2) | 11 | 146–156 | 24 |
| freeze_v2 (P3) | 8 | 157–164 | 14 |
| record_v2 (P7) | 9 | 165–172, 199 | 18 |
| sign_v2 documents (P2) | 9 | 173–181 | 21 |
| hal_v2 (P15) | 11 | 182–191, 200 | 23 |
| substrate_v4 (P9) | 7 | 192–198 | 13 |

**What the new threats attack:**

- **Ledger rows:** seq (renumbered, negative, a string), prev, hash,
  signature and signer (zeroed, null, foreign), the record rewritten,
  an extra field, and hidden duplicate keys.
- **Genesis:** the world renamed, a foreign signer, a zero signature, a
  zero hash, seq 1.
- **Store rows:** prev, hash, signature, case, a replayed record,
  whitespace, the genesis deleted, a junk row, a record that is not
  JSON.
- **Capsules, frozen capsules, records:** each signed field changed or
  removed, unsigned fields added, signature shape broken, re-signed by
  an attacker.
- **The glossary and its sidecar:** CRLF, a non-ASCII letter, lines
  swapped or dropped, the sidecar's value and algorithm, an empty
  sidecar, a re-signed sidecar.
- **Seals:** subject, action, rationale, version, lambda (negative, a
  string), the ladder, the attestation's validator and time, signature
  removed, re-signed.
- **Substrate rows:** subjects renamed or given another signer, an
  entity's id, kind and capsule, a copied entity, id case.

**Dropped while building:**

- Two threats that flipped a letter of `keys/owner.did` and
  `keys/attester.did` could not apply: `flip_letter` only flips inside
  JSON strings, and a did file is plain text.
- They would also prove little. Changing the did that the check itself
  trusts fails every signature at once, and no layer is asked anything
  new.
- A glossary `flip_letter` threat failed the same way and became a line
  swap (175).

## 3. First run (2026-11-20)

PASS 191, FAIL 9, UGLY 0, SKIP 0, real repo unchanged, exit 1.

- **The 8 known gaps** (SPEC_V0_5 §7): 011, 030, 043, 073, 103, 104, 107
  and 108.
- **One new gap, 140** (store_v2_1): a stored record with a trailing
  space is accepted.
  - store_v2 parses the record column (`json.loads`) and rebuilds the
    canonical P4 bytes before checking the hash. Whitespace in the
    stored text never reaches the check.
  - The meaning cannot change this way, but the bytes on disk are no
    longer the bytes that were signed.
  - The P4 ledger file refuses the same thing (013).

Recorded red first. A fix is a new layer in store-layer, after James
decides.

## 4. Tests

`tests/test_saboteur_v0_6.py`:

- there are 200 threats;
- 001–108 are threats_v0_5 byte for byte;
- every threat names a layer failure and a known mutation;
- the default threats are threats_v0_6;
- the run takes the lock;
- an end-to-end run of the ten new threats 190–199.

---

## Document control

- **SPEC V0.6 0.6.0-dev**: 2026-11-20, by the VS Code AI on James's
  "200 tests for saboteur".
