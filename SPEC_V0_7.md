# SPEC V0.7 — the-saboteur (Tier 2: The Saboteur), 400 threats

SPEC_V0_7.md — what saboteur_v0_7.py adds over 0.6.0.

Function:
    James, 2026-11-20: "200 more" (attacks), after 0.6.0's 200. 0.7.0
    takes the threats to 400. SPEC_V0_5.md stays authoritative for the
    fixture, check tool and mutations; SPEC_V0_5_1.md for the run lock;
    SPEC_V0_6.md for threats 001–200; SPEC_V2.md for the harness.

Tier:      Tier 2 — The Saboteur
Depends:   saboteur_v0_6.py (and through it 0.5.1, 0.5.0 and v2)
Version:   SPEC V0.7 0.7.0-dev
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. saboteur_v0_7.py

    python saboteur_v0_7.py [--target fixture_v0_5] [--threats threats_v0_7] [--parent DIR] [--only NNN]

- The run is 0.6.0's: the run lock, then 0.5.0's harness.
- 0.7.0 only changes the default threats, to `threats_v0_7/`.
- No new mutation code. Every new threat is data.

## 2. threats_v0_7/: 400 threats

001–200 are `threats_v0_6/`, copied byte for byte. 201–400 are new.

**Type confusion.** Most of the new threats put the wrong type where a
layer expects one: a number, list, object, null or empty string. A
layer must answer no and never raise. A raise would show as RAISED and
judge UGLY.

| Numbers | What | Layer |
|---|---|---|
| 201–268 | the signature's value, key_id, algorithm and whole object, wrong-typed or wrong-sized | sign_v2 capsule, freeze_v2, record_v2, hal_v2, sign_v2 sidecar |
| 269–288 | ledger row fields wrong-typed | ledger_v2 |
| 289–298 | half of those again | canon_verify_v2 |
| 299–303 | genesis row fields wrong-typed | genesis_v3 |
| 304–315 | blobs, wrong JSON types, case, gaps, a record too deep to decode, a reused hash | store_v2_1 |
| 316–328 | capsules empty, a list or a blob; signatures renamed; ids; copies; created_at | substrate_v4 |
| 329–350 | decision, separation, tier, lambda, ladder, timestamp, attestation | hal_v2 |
| 351–365 | fields; offsets; padded decimals; homoglyphs; zero-width and decomposed Unicode | sign_v2 capsules |
| 366–375 | hash, version, layer, text and type | freeze_v2 |
| 376–383 | fields; a look-alike letter; line order | record_v2 |
| 384–400 | byte and line attacks on both documents; sidecar shape | sign_v2 documents |

**Trimmed while building:** the first draft had 212 threats. The
signature value as an object and a key_id of a bare `did:key:` were
dropped for all five containers, along with an empty subject signer and
a blank line in the charter. Each overlapped a threat that stayed.

## 3. First run (2026-11-20)

The 200 new threats on their own gave PASS 197, FAIL 3, UGLY 0, SKIP 0.

**No layer raised.** Every type-confusion threat was refused cleanly.

**The three FAILs**, recorded red first. A fix is a new layer in that
repository, after James decides.

1. **324, 325 (substrate_v4): unsigned `created_at`.**
   - Backdating an entity or subject row's `created_at` goes unnoticed.
   - The column is outside the signed capsule. It is the same class as
     `name_key` (108).
2. **383 (record_v2): non-canonical bytes.**
   - Two key lines of a record file swapped still verify.
   - The meaning is unchanged, because record_v2 checks the parsed
     capsule.
   - The bytes on disk are no longer the bytes record_v2 wrote. It is
     the same class as 140 in the store.
   - Low severity.

The full run of 400 is in §4.

## 4. Full run

All 400, 2026-11-20: PASS 388, FAIL 12, UGLY 0, SKIP 0, real repo
unchanged, exit 1.

The 12 FAILs are the 8 from SPEC_V0_5 §7, 140 (SPEC_V0_6 §3), and 324,
325 and 383 (§3 above). Nothing else.

## 5. Tests

`tests/test_saboteur_v0_7.py` has 6 tests:

- there are 400 threats, numbered 001–400;
- 001–200 are threats_v0_6 byte for byte;
- every threat names a layer failure and a known mutation;
- no two threats are the same attack;
- the default is threats_v0_7;
- an end-to-end run of 200–209.

---

## Document control

- **SPEC V0.7 0.7.0-dev**: 2026-11-20, by the VS Code AI on James's
  "200 more".
