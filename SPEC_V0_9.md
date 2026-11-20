# SPEC V0.9 — the-saboteur (Tier 2: The Saboteur), 1000 threats, the known gaps mapped

SPEC_V0_9.md — what saboteur_v0_9.py and mutations_v0_9.py add over 0.8.0.

Function:
    James, 2026-11-20: "fill the known gaps to add 200 more to bring us
    to 1000". 0.9.0 takes the threats to 1000. The 200 new ones map each
    known gap class in full, so that a fix can be judged against all of
    its cases. SPEC_V0_8.md stays authoritative for threats 001–800.
    0.9.0 is the last version before the 1.0.0 consolidation
    (CONSOLIDATION_V1.md).

Tier:      Tier 2 — The Saboteur
Depends:   saboteur_v0_7.py, saboteur_v0_5.py, mutations_v0_8.py
Version:   SPEC V0.9 0.9.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. saboteur_v0_9.py

    python saboteur_v0_9.py [--target fixture_v0_5] [--threats threats_v0_9] [--parent DIR] [--only NNNN]

- The run is 0.8.0's.
- The default threats are `threats_v0_9/`.
- The mutations are `mutations_v0_9`, installed the way 0.8.0 installs
  its own.
- Threat numbers have four digits, so `--only` takes up to four.

## 2. mutations_v0_9.py

The layer over mutations_v0_8. Any name it does not know falls through.

- **`keep_first_lines:<N>`** keeps the first N lines: a rollback that
  many entries deep. It refuses N < 1 and N at or past the end.
- **`json_reformat:<style>`** keeps the same JSON content in other
  bytes. It refuses unchanged bytes, and changed content. The styles:
  - compact;
  - indent4;
  - sorted;
  - reversed (top-level key order);
  - escape_letter (one ASCII letter in a string value written as a
    `\u` escape).

## 3. threats_v0_9/: 1000 threats

0001–0800 are `threats_v0_8/` with the same bytes. Only the file names
gain a leading 0, so that 1000 sorts last.

0801–1000 are new. Each has a `gap` field naming its class:

| Gap class | Threats |
|---|---|
| rollback | 10 |
| dup-key | 52 |
| unsigned-column | 25 |
| deleted-row | 4 |
| non-canonical | 30 |
| substitution | 79 |

**How the set was made:**

- The generator made 216 candidates.
- 16 duplicated an existing attack and were dropped, leaving exactly
  200.
- One deleted-row threat (deleting James's entity, asked of the
  subjects) was dropped as a duplicate. The run judges a threat by its
  file, mutation and tool, and the `--layer` filter names only the
  layer, not the call.

## 4. First run of 0801–1000 (2026-11-20)

PASS 70, FAIL 130, UGLY 0, SKIP 0, real repo unchanged.

| Gap class | PASS | FAIL |
|---|---|---|
| rollback | 0 | 10 |
| dup-key | 24 | 28 |
| unsigned-column | 0 | 25 |
| deleted-row | 0 | 4 |
| non-canonical | 0 | 30 |
| substitution | 46 | 33 |

**What holds:**

- **Duplicate keys in the ledger** (0823–0836, 0974–0979). The P4 line
  format is strict, so a duplicate breaks the row. canon_verify_v2
  refuses duplicates by name.
- **Duplicate keys in substrate capsules** (0980–0983). The id is the
  hash of the stored text.
- **Substitution across kinds into freeze_v2, hal_v2 and the
  sidecars.** A frozen capsule needs `document_sha256`, a seal needs
  its own fields, and a sidecar names its file's hash.

**What is red, and is new knowledge:**

- **Rollback at every depth:** the ledger, canon_verify_v2 and the store
  accept any prefix of themselves.
- **Duplicate keys** are accepted in records, capsules, frozen
  capsules, seals and stored records. The value that wins is the signed
  one, but a first-wins reader would see the Saboteur's.
- **Unsigned columns:** every way of changing `name_key` and
  `created_at` passes. So does every change to a membership, because
  list_entities and list_subjects never read memberships.
- **Non-canonical bytes:** records and stored records accept any
  re-formatting that keeps the content.
- **Substitution:**
  - sign_v2 capsules and record_v2 accept any file the owner signed in
    place of any other.
  - One frozen spec over the other passes (0907).
  - The store copied over the substrate reads as an empty substrate,
    "ok 0 rows" (0938).

Recorded red first. Fixes are new layers in each repository, after
James decides.

## 5. Tests

`tests/test_saboteur_v0_9.py` has 12 tests:

- keep_first_lines: it rolls back, and refuses a non-rollback;
- json_reformat: it keeps the content, and refuses unchanged bytes and
  unknown styles;
- unknown mutations fall through;
- there are 1000 threats, and 0001–0800 are threats_v0_8 byte for byte;
- every threat names a layer failure and a known mutation;
- no two threats are the same attack;
- every new threat names its gap;
- the runner swaps the mutations and puts them back;
- an end-to-end run of 0800–0809.

---

## Document control

- **SPEC V0.9 0.9.0**: 2026-11-20, by the VS Code AI on James's "fill
  the known gaps to add 200 more to bring us to 1000".
- Frozen 2026-11-20 with 0.6.0–0.9.0 together (James: "yes 7", CONSOLIDATION_V1 §7.2).
