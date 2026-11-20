# SPEC V0.5 — the-saboteur (Tier 2: The Saboteur), attacks on the Legacy's own layers

SPEC_V0_5.md — what saboteur_v0_5.py adds over the frozen 0.4.0.

Function:
    James, 2026-11-20: "yes lets a a ton more", answering how many
    attacks the Saboteur runs (none since 0.4.0 cut the-full-stack).
    0.5.0 gives v2's harness a target made of the Legacy's own layers
    and 108 threats against it. SPEC_V2.md stays authoritative for the
    harness (guard, canaries, baseline, judging, exit codes);
    SPEC_V0_4.md for the refusal of the-full-stack. Nothing frozen is
    edited.

Tier:      Tier 2 — The Saboteur
Depends:   saboteur_v2.py, harness_guard_v2.py, mutations_v2.py (unchanged);
           envelope_v2, sign_v2, freeze_v2, ledger_v2, canon_verify_v2,
           genesis_v3, record_v2, hal_v2, store_v2_1, substrate_v4
Version:   SPEC V0.5 0.5.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. saboteur_v0_5.py

    python saboteur_v0_5.py [--target fixture_v0_5] [--threats threats_v0_5] [--only NNN]

- The target defaults to `fixture_v0_5/` (§2). A folder named
  `the-full-stack` is still refused, exit 2.
- The threats default to `threats_v0_5/` (§5).
- For the run, v2's mutation module is replaced by `mutations_v0_5`
  (§4). v2's harness code runs as it is.
- `FORGE_LEGACY_ROOT` is set to the-saboteur's parent folder unless it is
  already set, so the scratch copy (under the system temp folder) can
  find the layers.

## 2. The target: fixture_v0_5/

The layers are libraries with no command line. James's own `~/.forge`
holds his key, so it is never a target. The fixture stands in for both.

**What builds it:** `build_fixture_v0_5.py` makes it with the real
layers, signed by two throwaway Ed25519 keys (owner and attester). Only
the public did:keys are written, to `keys/`. The private keys exist only
in memory during the build.

**What it holds** (14 checked files, listed in `manifest.json`):

| File | Made by | Checked by |
|---|---|---|
| `ledger.jsonl` (genesis + 5) | genesis_v3, ledger_v2 | ledger_v2, canon_verify_v2, genesis_v3 |
| `capsules/*.sc.json` (3) | sign_v2.sign_capsule | sign_v2.verify_capsule |
| `frozen/*.sc.json` (2) | freeze_v2.freeze_capsule | freeze_v2.verify_frozen_capsule |
| `records/*.sc.json` (2) | record_v2.save_signed_record | record_v2.verify_record_file |
| `docs/*.md` + `.sig` (2) | sign_v2.sign_artifact | sign_v2.verify_artifact |
| `seals/*.json` (2, attested) | hal_v2 attest, create, sign | hal_v2.verify_seal (attester pinned) |
| `store.db` (4 rows) | store_v2_1 | store_v2_1.verify_store |
| `substrate.db` (2 entities, 1 subject) | substrate_v4 | substrate_v4.list_entities / list_subjects (verify) |

**Rebuilding:** the fixture is committed. A rebuild makes new keys
(`--force`).

## 3. The tool: fixture_v0_5/legacy_check_v0_5.py

It reads the manifest and hands each file to its layer's public verify
call, under the owner's did. It prints one line per check and exits 1
if any line is not ok:

    ok     <file>  <layer>.<call>
    FAILED <file>: <layer>.<call> said no
    FAILED <file>: <layer>.<call> refused it (<Error>: <message>)
    RAISED <file>: <layer>.<call> raised <Error>: <message>

**The only judgements it makes itself:**

- a listed file that is missing (`manifest.files missing`);
- a file that is not JSON, for the layers that take a dict.

Every other verdict is the layer's.

**RAISED** marks a layer that raised although its spec says it never
raises on content. No threat's keyword matches it, so it shows as UGLY.

**`--layer NAME`** runs one layer module's checks only. Each threat uses
it, so a PASS means that layer said no.

## 4. mutations_v0_5.py

The layer over mutations_v2. Any name it does not know goes to v2. It
adds:

- **Line and byte attacks:**
  - drop_first_line, drop_middle_line, drop_last_line;
  - swap_middle_lines, duplicate_last_line;
  - blank_line, trailing_space, add_bom, empty, non_ascii;
  - reorder_keys_first_line;
  - flip_letter (§6).
- **Parametrised attacks**, so a new attack is a new threat file:
  - json_set, json_drop, json_dup_key_first;
  - line_dup_key, line_set;
  - sqlite.
- **Forgeries**, made with a fresh attacker key through the layers
  themselves, so each is well formed and only the key is wrong:
  - resign_attacker, resign_attacker_edit, resign_keep_key_id;
  - refreeze_attacker, rehash_frozen;
  - resign_sidecar_attacker, edit_and_resign_sidecar;
  - ledger_append_attacker, ledger_rewrite_last_attacker,
    ledger_rewrite_last_keep_signer;
  - substrate_forge_last.

**Refusing a no-op:** a mutation that changes nothing raises, and the
harness reports SKIP. That covers line_set to the same value and an SQL
UPDATE or DELETE of no rows.

## 5. threats_v0_5/: 108 threats

Each threat's tool is `python legacy_check_v0_5.py --layer <layer>`. Its
keyword is `failed <file>: <layer>.<call>`, which only a failure line
from that layer can match. A deletion is the exception: the manifest
catches it, and the keyword says so.

| Layer | Threats |
|---|---|
| ledger_v2 (P4) | 22 |
| canon_verify_v2 (P6) | 15 |
| genesis_v3 (P5) | 3 |
| store_v2_1 (P8) | 10 |
| sign_v2 capsules (P2) | 13 |
| freeze_v2 (P3) | 6 |
| record_v2 (P7) | 9 |
| sign_v2 documents (P2) | 12 |
| hal_v2 (P15) | 12 |
| substrate_v4 (P9) | 6 |

## 6. Found while building (harness, not layers)

- **v2's `flip_byte_text` cannot flip** any fixture file. It starts its
  string search halfway through the file. When that lands inside a
  string, it sees the gaps between strings, which hold no letters. It
  also parses the whole file as JSON, which a .jsonl ledger is not.
  - v2 is frozen. `flip_letter` scans from the start instead.
  - The frozen v2 threat that used it (01) was green against
    the-full-stack. Whether it can flip depends on where a file's middle
    falls, so that green proves less than it seemed to.
- **v2's `replace_first_prev` is a no-op on a genesis row.** It sets
  prev to the zero anchor, which a genesis already has. The ledger
  threats use `line_set` instead, which refuses a no-op.

## 7. First run (2026-11-20)

PASS 100, FAIL 8, UGLY 0, SKIP 0, real repo unchanged, exit 1.

Each FAIL is a real gap in a layer, recorded red first (CLAUDE.md
discipline 1). A fix is a new layer in that repository, after James
decides.

1. **Rollback:** ledger_v2, canon_verify_v2 and store_v2_1 (011, 030,
   043). Dropping the last entry leaves a valid chain. Nothing remembers
   the head, so a rollback is invisible to a chain check.
2. **Duplicate key:** record_v2 (073). A duplicate key placed before the
   real one is accepted. Python keeps the last value, which is the
   signed one, but a first-wins reader would see the forged one.
   canon_verify_v2 already refuses duplicate keys in a ledger.
3. **Self-certifying rows:** substrate_v4 (103, 104). A row re-signed by
   another key, with its id recomputed and its signer column set to
   that key, still verifies. The check proves the row is intact, not
   who made it.
4. **Unchained rows:** substrate_v4 (107). A deleted entity row goes
   unnoticed.
5. **Unsigned lookup key:** substrate_v4 (108). `name_key` is outside
   the signed capsule.

## 8. Tests

`tests/test_saboteur_v0_5.py` has 13 tests:

- the fixture, and that it holds no private key;
- the check's lines;
- the new mutations, and that they refuse a no-op;
- every threat names a layer failure;
- the-full-stack is refused;
- an end-to-end run of 9 threats.

With the frozen suites: 31/31.

---

## Document control

- **SPEC V0.5 0.5.0**: 2026-11-20, by the VS Code AI on James's "yes lets
  a a ton more". Frozen 2026-11-20 (James: "freeze commit push").
