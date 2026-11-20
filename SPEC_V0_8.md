# SPEC V0.8 — the-saboteur (Tier 2: The Saboteur), 800 threats and substitution

SPEC_V0_8.md — what saboteur_v0_8.py and mutations_v0_8.py add over 0.7.0.

Function:
    James, 2026-11-20: "400 more" (attacks), after 0.7.0's 400. 0.8.0
    takes the threats to 800 and adds one new attack class,
    substitution, which needs two new parametrised mutations.
    SPEC_V0_7.md stays authoritative for threats 001–400.

Tier:      Tier 2 — The Saboteur
Depends:   saboteur_v0_7.py, saboteur_v0_5.py, mutations_v0_5.py
Version:   SPEC V0.8 0.8.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. saboteur_v0_8.py

    python saboteur_v0_8.py [--target fixture_v0_5] [--threats threats_v0_8] [--parent DIR] [--only NNN]

- The run is 0.7.0's: the run lock, then 0.5.0's harness.
- The default threats are `threats_v0_8/`.
- The mutations are `mutations_v0_8`. saboteur_v0_5 installs its
  mutation module by name on every run, so 0.8.0 rebinds
  `saboteur_v0_5.mutations_v0_5` for the run and puts it back after.

## 2. mutations_v0_8.py

The layer over mutations_v0_5. Any name it does not know falls through.

- **`copy_sibling:<path>`** replaces the victim with another fixture
  file's bytes.
  - The path is relative to the victim's folder.
  - It refuses an absolute path, a path that leaves the fixture (at
    most one level up), a missing source and identical bytes.
- **`text_replace:<old>=><new>`** replaces the first `<old>`.
  - It refuses when `<old>` is absent or nothing changes.

## 3. threats_v0_8/: 800 threats

001–400 are `threats_v0_7/`, copied byte for byte. 401–800 are new:

| Numbers | What |
|---|---|
| 401–414 | Substitution: a valid signed file copied over another. Record over record, seal over seal, capsule over capsule, frozen over frozen, and across kinds. |
| 415–418 | Substitution of documents and sidecars. |
| 419–511 | Signature type confusion on the files 0.7.0 left alone: policy-writes, entity-james, spec-ledger, note-boot, seal-refuse and the charter sidecar. |
| 512–800 | Field matrix: every signed field of every JSON file set to null, 0, [], {}, "" and true. |

**How the set was made:**

- The generator made 424 candidates.
- 22 duplicated an existing attack (the same file, mutation and tool)
  and were dropped.
- The last 2 of the matrix (seal-refuse's ladder and lambda_attestation
  set to true) were cut to land on 400.

## 4. First run of 401–800 (2026-11-20)

PASS 388, FAIL 12, UGLY 0, SKIP 0, real repo unchanged.

**No layer raised on the type-confusion threats.** All 382 of them
were refused cleanly.

**A new gap class: substitution (12 FAILs).** Recorded red first; a fix
is a new layer in each repository, after James decides.

- 401, 402: one valid record copied over the other.
- 403, 404: **the refusal seal copied over the approval, and the other
  way round.**
- 405, 406: one valid capsule over another.
- 407: one frozen spec over another.
- 408, 409: a frozen capsule or a record where a capsule belongs.
- 410: a capsule where a record belongs.
- 413: a seal where a capsule belongs.
- 414: a seal where a record belongs.

Each file proves who signed it and that it is intact. **Nothing binds a
signed file to its name, its place or its kind.** The checks that held
did so because the kinds differ in shape:

- 411: a capsule has no `document_sha256`;
- 412: a capsule is not a seal;
- 415–418: a sidecar names its file's hash.

## 5. Tests

`tests/test_saboteur_v0_8.py` has 12 tests:

- copy_sibling: it copies, and refuses identical bytes and paths
  outside the fixture;
- text_replace: it changes the first match and refuses a no-op;
- unknown mutations fall through;
- there are 800 threats, and 001–400 are threats_v0_7 byte for byte;
- every threat names a layer failure and a known mutation;
- no two threats are the same attack;
- the runner swaps the mutations and puts them back;
- an end-to-end run of 420–429.

---

## Document control

- **SPEC V0.8 0.8.0**: 2026-11-20, by the VS Code AI on James's "400
  more".
- Frozen 2026-11-20 with 0.6.0–0.9.0 together (James: "yes 7", CONSOLIDATION_V1 §7.2).
