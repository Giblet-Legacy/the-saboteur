# SPEC V2 — the-saboteur (Tier 2: The Saboteur, an honest harness)

SPEC_V2.md — specification for saboteur_v2.py, harness_guard_v2.py,
mutations_v2.py and threats_v2/, the layer over v1.

Function:
    James (2026-11-15): "analise and report and fix". An audit of v1
    found that its harness never ran the guards SPEC.md calls PROVEN,
    and that three of the target tools already fail on a clean copy of
    the-full-stack, so 7 of the 12 threats passed whatever happened and
    the recorded "12/12 PASS" could not have failed. v2 runs the guards,
    judges every threat against a clean baseline, and fixes the
    mutations and threats that tested the wrong thing. SPEC.md stays
    authoritative where this document is silent. saboteur.py,
    harness_guard.py, mutations.py, threats/ and the v1 test are not
    edited.

Tier:      Tier 2 — The Saboteur
Depends:   a target repo (default ../the-full-stack); cryptography (two mutations, the throwaway key)
Version:   SPEC V2 0.3.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. saboteur_v2.py

`python saboteur_v2.py [--target DIR] [--threats DIR] [--parent DIR] [--only NN]`

1. Load `threats_v2/*.json`; a threat missing `name`, `target_file`,
   `mutation` or `tool` makes the harness invalid.
2. `pre_run`: hash the real target, make a guarded scratch copy, run the
   five canaries (§3). Any failure: exit 2.
3. For each threat, on a fresh guarded copy (no `.git`):
   - write a throwaway Ed25519 key into the copy and run every tool with
     `FORGE_KEY_PATH` pointing at it, so nothing is ever signed with the
     owner's key;
   - run the tool on the clean copy: the **baseline**;
   - apply the one mutation (`mutations_v2`);
   - run the tool again, from the copy, with this Python interpreter
     (`python` in a tool string means `sys.executable`), timeout 120 s;
   - judge (§3).
   A missing target file, a delete with nothing to delete, a mutation
   that cannot apply, or a baseline that cannot run is **SKIP**; a tool
   that does not finish is **UGLY**.
4. `post_run`: the real target's hash must be unchanged, else exit 2.
5. Exit 0 only when every threat passed; 1 on any FAIL, UGLY or SKIP
   (a threat that could not run has proved nothing); 2 when the harness
   is invalid.

## 2. harness_guard_v2.py

As v1's guard, with:

- the scratch parent passed in (default `<system temp>/forge-saboteur`),
  never fixed at `~/forge`;
- `init_scratch` refuses an existing directory that has anything in it
  and no marker (v1 copied the target into it);
- `guard_scratch` checked before every wipe and after every creation;
- `per_invocation(cwd, scratch)`: the tool's working directory must be
  the scratch copy (v1 checked a tool *path*, which a shell command
  string does not have).

## 3. One judgement, differential

`judge(returncode, stdout, stderr, keywords, baseline)`; `baseline` is
the clean run's output lines when the clean run exited non-zero, else
None.

- exit 0: **FAIL** (silent pass);
- a Python traceback: **UGLY** (a crash is not a named error);
- no output line that the baseline did not already have: **FAIL**
  (nothing new was caught);
- keywords given and none appears in a new line: **UGLY** (caught,
  but not named);
- otherwise **PASS**.

Keywords match whole new lines, lower-cased. v2's threats drop the
catch-all keyword "fail", which v1 put in 10 of 12 threats and which
any failing tool prints.

Canaries, each run through `judge`, all must give their verdict or the
run is invalid: `canary_silent` FAIL, `canary_loud` PASS,
`canary_vague` UGLY, `canary_crash` (new) UGLY, `canary_same` (new,
judged against a baseline identical to its own output) FAIL.

## 4. mutations_v2.py

v1's mutations, except:

- line mutations (`reorder_lines`, `duplicate_line`,
  `replace_first_prev`, `inject_placeholder`) read and write bytes, so a
  file keeps its own line endings (v1's text mode turned every LF into
  CRLF on Windows);
- `flip_byte_text`: one bit of one lowercase letter inside a JSON
  string past the middle of the file; the file stays valid JSON;
- `re_sign_wrong_key`: a fresh key, the signature in base64 (as the
  stack stores it), `key_id` kept;
- `json_edit_old_as_of`: a score file's `as_of` set to 2025-01-01;
- `none`: no change.

## 5. threats_v2/

The twelve threats of `threats/`, corrected: each names a target that
exists, a tool that exists, and keywords that only the intended
catch would print; each carries a `notes` field saying what v1 got
wrong. 02 and 03 use `docs/glossary.md` and `docs/datacube.md.sig`
(README.md has no `.sig`); 11 is the README's past-TTL threat (v1's
file 11 called `hal.py verify-score`, which does not exist).

## 6. Tests (tests/test_saboteur_v2.py)

All under pytest's tmp_path: the guard's refusals; an unmarked,
non-empty scratch is refused and left intact; the judgement table;
every canary verdict and a judge stuck on any one verdict is caught;
the mutations change exactly what they say; the wrong-key signature is
base64 and keeps key_id; an end-to-end run on a fake target (one PASS,
one silent FAIL, one SKIP, exit 1, target untouched; `--only` exit 0);
a touched real repo is invalid.

---

## Document control

- **SPEC V2 0.3.0** — 2026-11-15, by the VS Code AI on James's
  delegation ("analise and report and fix").
