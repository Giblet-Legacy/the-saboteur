# SPEC V1 — the-saboteur (Tier 2: The Saboteur), 1.0.0

SPEC_V1.md — the Saboteur 1.0.0 as it is: the 0.9.0 chain in one version.

Function:
    The 1.0.0 consolidation (CONSOLIDATION_V1.md; James 2026-11-20: "ok
    so this brings us to the point were we consolodate archive and parent
    up to v1.0", then "yes 7").

    One spec for 1.0.0, gathered from SPEC_V2.md, SPEC_V0_4.md,
    SPEC_V0_5.md, SPEC_V0_5_1.md and SPEC_V0_6.md to SPEC_V0_9.md (all in
    archive/0.9.0). It cites them and re-decides nothing. The behaviour
    is exactly that of `python saboteur_v0_9.py` (tag v0.9.0).

Tier:      Tier 2 — The Saboteur
Depends:   the Legacy layers it attacks: envelope_v2, sign_v2, freeze_v2,
           ledger_v2, canon_verify_v2, genesis_v3, record_v2, hal_v2,
           store_v2_1, substrate_v4 (siblings, or FORGE_LEGACY_ROOT)
Version:   SPEC V1 1.0.0-dev
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. What 1.0.0 is

1.0.0 is one module of each kind in place of the 0.9.0 chain:

    saboteur_v0_9 -> v0_7 -> v0_6 -> v0_5_1 -> v0_5 -> saboteur_v2
    mutations_v0_9 -> v0_8 -> v0_5 -> v2 -> mutations (v1)

Nothing is swapped at run time. The behaviour is 0.9.0's:

- the same arguments;
- the same lock;
- the same guard and canaries;
- the same output lines;
- the same exit codes;
- the same 1000 threats;
- the same verdicts.

Nothing is added and nothing is fixed.

| File | What it is |
|---|---|
| `saboteur_v1.py` | The runner. v2's harness (load_threats, run_threat, _run, _key_file, _command) and 0.5.1's lock (acquire, release, _alive, _read, Locked) are copied from the archive. `_run_all` joins 0.5.0's refusal and defaults to v2's main; `main` puts the lock around it. |
| `harness_guard_v1.py` | harness_guard_v2's code, byte for byte, under a 1.0.0 header. |
| `mutations_v1.py` | Every function 0.9.0's apply_mutation could reach, copied from the archived module named in its section, with one dispatch in 0.9.0's order (§4). |
| `fixture_v1/` | fixture_v0_5/ byte for byte, not rebuilt: the same throwaway keys and signatures. The check tool is renamed `legacy_check_v1.py`, with the same code. |
| `build_fixture_v1.py` | build_fixture_v0_5.py under its 1.0.0 name. Only the folder and check-tool names differ. |
| `threats_v1/` | threats_v0_9/ with one change per file: the tool name. |
| `harness_canaries/` | Unchanged, at the top level since v2. |
| `pytest.ini` | Collects `tests/` only, never `archive/`. |

## 2. The run (SPEC_V2 §1, SPEC_V0_4 §1, SPEC_V0_5 §1, SPEC_V0_5_1 §2)

    python saboteur_v1.py [--target fixture_v1] [--threats threats_v1] [--parent DIR] [--only NNNN]

1. **The lock.** `<parent>/saboteur.lock` is created exclusively and
   holds the pid and start time.
   - A run that finds it held by a live process refuses with exit 2 and
     names the holder.
   - A lock whose process is gone is taken over.
   - An unreadable lock counts as held for 60 seconds.
   - The lock is released however the run ends, but only if it is still
     this run's.
   - The default parent is `<system temp>/forge-saboteur`.
2. **The refusal.** A target folder named the-full-stack is refused,
   with exit 2 (James, 2026-11-18: reference only).
   - The lock is taken first, so its parent folder exists by then. That
     is 0.9.0's order, and it is kept.
3. **The layers.** `FORGE_LEGACY_ROOT` is set to the-saboteur's parent
   unless it is already set.
4. **The harness.**
   - The guarded scratch is `<parent>/run`, behind a marker.
   - Five canaries prove `judge` first.
   - The target is hashed before and after the run.
   - For each threat:
     1. a clean copy;
     2. the tool run on it (the baseline);
     3. one mutation;
     4. the tool run again;
     5. `judge`.
   - Tools run from the scratch with a throwaway key in
     `FORGE_KEY_PATH`, with a 120-second timeout.
5. **The verdicts** (SPEC_V2 §3):
   - **PASS:** the tool exits non-zero, and a new line holds a keyword.
   - **FAIL:** a silent pass, or nothing new.
   - **UGLY:** a traceback, or a new failure line with no keyword.
   - **SKIP:** a missing file, or a mutation that could not apply.
6. **Exit codes:**
   - 0: every threat passed;
   - 1: any FAIL, UGLY or SKIP;
   - 2: the harness is invalid, the lock is held, or the target is
     refused.
7. **The output.** It is 0.9.0's, banner included ("THE SABOTEUR v2:
   N threats against …"). The banner's wording is the kind of change
   that comes after a consolidation, not in one.

## 3. The tool: fixture_v1/legacy_check_v1.py (SPEC_V0_5 §3)

It reads `manifest.json` (14 files) and hands each file to its layer's
public verify call, under the owner's did. It prints one line per check
and exits 1 if any line is not ok:

    ok     <file>  <layer>.<call>
    FAILED <file>: <layer>.<call> said no
    FAILED <file>: <layer>.<call> refused it (<Error>: <message>)
    RAISED <file>: <layer>.<call> raised <Error>: <message>

- `--layer NAME` runs one layer module's checks.
- Its only judgements of its own are a missing file
  (`manifest.files missing`) and "not JSON".
- A clean fixture gives 17 checks, 0 not ok.

## 4. mutations_v1 (SPEC_V0_5 §4, SPEC_V0_8 §2, SPEC_V0_9 §2, SPEC_V2 §4)

`apply_mutation(path, name)` tries, in 0.9.0's order:

1. **Parametrised** (`name:arg`):
   - 0.9.0: keep_first_lines, json_reformat;
   - 0.8.0: copy_sibling, text_replace;
   - 0.5.0: json_set, json_drop, json_dup_key_first, line_dup_key,
     line_set, sqlite, resign_attacker_edit, rehash_frozen,
     substrate_forge_last.
2. **Plain, from 0.5.0:**
   - drop_first_line, drop_middle_line, drop_last_line;
   - swap_middle_lines, duplicate_last_line;
   - blank_line, trailing_space, add_bom, empty, non_ascii;
   - reorder_keys_first_line, flip_letter;
   - resign_attacker, resign_keep_key_id, refreeze_attacker;
   - resign_sidecar_attacker, edit_and_resign_sidecar;
   - ledger_append_attacker, ledger_rewrite_last_attacker,
     ledger_rewrite_last_keep_signer.
3. **From v2:** none, reorder_lines, duplicate_line,
   replace_first_prev, inject_placeholder, flip_byte_text,
   re_sign_wrong_key, json_edit_old_as_of.
4. **From v1:** flip_byte, lf_to_crlf, delete, truncate_mid_line,
   json_edit_empty_scp_id, json_edit_fractional,
   json_edit_old_timestamp, set_compute_on_freeze.
5. **Anything else** raises `ValueError("Unknown mutation: …")`.

A mutation that changes nothing raises, and the harness reports SKIP,
never a pass. The forgeries are made with a fresh attacker key, through
the Legacy layers themselves.

## 5. threats_v1/: 1000 threats

| Numbers | Came in | What |
|---|---|---|
| 0001–0108 | 0.5.0 | The first attacks on every layer (SPEC_V0_5 §5) |
| 0109–0200 | 0.6.0 | More fields and files (SPEC_V0_6 §2) |
| 0201–0400 | 0.7.0 | Mostly type confusion (SPEC_V0_7 §2) |
| 0401–0800 | 0.8.0 | Substitution, the signature matrix, the field matrix (SPEC_V0_8 §3) |
| 0801–1000 | 0.9.0 | Each known gap class mapped in full; each has `gap` (SPEC_V0_9 §3) |

Each threat's tool is `python legacy_check_v1.py --layer <layer>`. Its
keyword is `failed <file>: <layer>.<call>`.

## 6. Known gaps (carried forward, all red)

**154 threats are red at 1.0.0, as at 0.9.0.** Each is a real gap in a
Legacy layer, recorded red first (CLAUDE.md discipline 1). A fix is a
new layer in that repository, after James decides. No layer raised on
any threat (UGLY 0), and no threat skipped (SKIP 0).

| Gap class | Red | Threats | First recorded |
|---|---|---|---|
| Rollback: a prefix of the ledger or store is a valid chain | 13 | 0011, 0030, 0043, 0801–0810 | SPEC_V0_5 §7.1, SPEC_V0_9 §4 |
| Duplicate keys accepted (first-wins readers see the forgery) | 29 | 0073, 0811–0822, 0958–0973 | SPEC_V0_5 §7.2, SPEC_V0_9 §4 |
| Self-certifying substrate rows | 2 | 0103, 0104 | SPEC_V0_5 §7.3 |
| Deleted substrate rows unnoticed | 5 | 0107, 0858–0861 | SPEC_V0_5 §7.4, SPEC_V0_9 §4 |
| Unsigned substrate columns (name_key, created_at, memberships) | 28 | 0108, 0324, 0325, 0837–0857, 0984–0987 | SPEC_V0_5 §7.5, SPEC_V0_7 §3, SPEC_V0_9 §4 |
| Non-canonical bytes accepted (same content, other bytes) | 32 | 0140, 0383, 0862–0878, 0988–1000 | SPEC_V0_6 §3, SPEC_V0_7 §3, SPEC_V0_9 §4 |
| Substitution: a valid signed file in another's place | 45 | 0401–0410, 0413, 0414, 0879–0897, 0907, 0912–0923, 0938 | SPEC_V0_8 §4, SPEC_V0_9 §4 |

## 7. What 1.0.0 does not keep

The following entry points stay runnable from a worktree of the tag
`v0.9.0`, not from `archive/0.9.0/`, whose layers import their siblings:

- v1's `saboteur.py`;
- v2's default target of the-full-stack;
- 0.4.0's no-default target;
- the old per-version threat sets (threats_v2 to threats_v0_9).

## 8. Tests

65 tests in eight `tests/test_saboteur_<version>_at_v1.py` suites
carry forward every live test of the archived suites (CONSOLIDATION_V1
§3.1). The 11 replaced tests stay with their versions in the archive.

**What changed in the carried tests:**

- Module and path names are now `_v1`.
- Four-digit `--only` prefixes (`000`, `0001`, `019`, `020`, `042`) run
  the same threats.
- The "first N are the earlier set unchanged" tests also check that
  threats_v1 holds the archived files with only the tool renamed
  (`tests/v1_threats.py`).
- 0.4.0's "the harness is v2's" becomes "the harness is saboteur_v1's
  own code".
- 0.5.1's "the lock is released when the run raises" patches
  `saboteur_v1._run_all`, the run the lock wraps.

---

## Document control

- **SPEC V1 1.0.0-dev**: 2026-11-20, by the VS Code AI on branch
  consolidate-1.0.0 (CONSOLIDATION_V1 §4.5).
