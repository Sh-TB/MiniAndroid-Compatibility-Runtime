# KNOWLEDGE_RECONCILIATION — FINAL CANONICAL MASTER RECONCILIATION (Pass 3)

Date: 2026-09-03 · Branch: `integration/master-reconciliation` · Base: 272f216c · NO PUSH performed
Machine-readable ledger: `KNOWLEDGE_LEDGER.csv` (50 rows, decision vocabulary enforced)
Companion audits: `PASS3_OPCODE_AUDIT.md`, `PASS3_STUB_AUDIT.md`, `run/pass3_evidence/`

## 1. Mission

Prove that no valid fix, discovery, regression fix, semantic correction, runtime
improvement, test, evidence, or knowledge created in ANY past version, ZIP, Git
history, backup, or campaign of MiniAndroid is missing from the Canonical Master
(`Sh-TB/MiniAndroid-Compatibility-Runtime` — the project IS its own upstream; not
a fork). Every historical claim was treated as CANDIDATE and independently
re-verified at the current HEAD. Claim ≠ implementation ≠ verification.

## 2. Historical sources scanned (omission-audit input)

| Source | Provenance | What it held | Where it lives NOW |
|---|---|---|---|
| MiniAndroid_v0.11-unified-011_GIT_HANDOFF.zip | campaign UNIFIED_011 | HEAD 388fb45, 100 commits (shallow) | ancestor of canonical HEAD; tag v0.11-unified-011 |
| MiniAndroid_v0.11.1-unified-011-1_…zip | UNIFIED_011.1 | 340a9cf, 103 commits | ancestor; tag v0.11.1-unified-011-1 |
| MiniAndroid_v0.11.2-unified-011-2_…zip | UNIFIED_011.2 | 6c9a91e, 109 commits | ancestor; tag v0.11.2-unified-011-2 |
| MiniAndroid_v0.11.3-unified-011-3_…zip | UNIFIED_011.3 | ea81e00, 72+ commits, 4 tags | ancestor; tag v0.11.3-unified-011-3 |
| MiniAndroid_v0.11.4-fix-01_GAP-RECONCILIATION_…zip | 011.4 (ARSC value path) | b9d93cc, 115 commits | ancestor; tag v0.11.4-fix-01 |
| MiniAndroid_CAMPAIGN-012-baseline_…zip | campaign-012 (never ran) | ea81e00 (= v0.11.3 = v0.13.0 baseline) | ancestor; tags campaign-012-baseline, v0.13.0-baseline |
| MiniAndroid_v0.13.0_GIT_HANDOFF.zip | campaign 013 | 2ede367, 120 commits | ancestor; tag v0.13.0 (branch campaign-013) |
| MiniAndroid_v0.14.0_GIT_HANDOFF.zip | campaign 014 attempt | **0 bytes — interrupted packaging** | recorded CORRUPT_EMPTY (archive_scan.json) |
| MiniAndroid_v0.14.0_PARTIAL_GIT_HANDOFF.zip | campaign 014 partial | 894eae2, 121 commits + triage evidence | ancestor; tag v0.14.0-partial = pre-integration-local-rescue |
| MiniAndroid_FULL_VALIDATION_HANDOFF_6c9a91e.zip | 011.2 era | **0 bytes** | recorded CORRUPT_EMPTY |
| MiniAndroid_MASTER_INTEGRATION_REVIEW_0fd1ad6.zip | Pass-1 reconciliation | 0fd1ad6, 356 commits | ancestor (pass-1 integration head) |
| MiniAndroid_CANONICAL_MASTER_RECONCILED_272f216c.zip | Pass-2 reconciliation | 272f216c, 360 commits | THIS pass's starting point (SHA-verified 2e93d27d…) |
| MiniAndroid_CAMPAIGN013_REPORTS_bundle.zip | c013 reports | 13 knowledge MDs | committed at repo root (docs history) |
| BACKUP_GITHUB_MASTER_FULL.bundle / _bbe0ce3.bundle | GitHub master backup | bbe0ce3 complete history + pre-integration-github-baseline tag | verified: complete history, heads = bbe0ce3 |
| BACKUP_LOCAL_INTEGRATION_0fd1ad6.bundle | Pass-1 backup | 0fd1ad6 lineage, all branches | verified: complete history |
| Legacy coder ZIPs / bundles (12 recovery archives audited in 011.2) | UNIFIED_000-010 era | TOOL-LOST-SUITE verdict | gap matrix row TOOL-LOST-SUITE (revived in-repo) |

**Forensic cross-check:** every archive HEAD commit (`git cat-file -t` +
`merge-base --is-ancestor`) is an ANCESTOR of the canonical HEAD → **no commit
exists in any archive outside the canonical lineage**. Every archive tag is a
subset of the canonical tag set. `git fsck --full --unreachable --dangling` on
the canonical repo: **0 diagnostics**. `git log --all` = 360 = rev-list HEAD.
Reflog: 18 entries; the single reflog-only commit b5d2140 is a docs draft
superseded by its own amend (0fd1ad6) — content preserved (LED-036).

## 3. Campaign timeline (where knowledge was created)

UNIFIED_000–004 (workstreams, corpus) → 005 (audio/3D) → 006 (EXP-117..120) →
007 (real ARSC/AXML pipeline) → 008 (external libs; GLES investigation) → 009
(demand matrix) → 010 (libpng pipeline) → 011–011.1 (recovery, matrix anchor) →
011.2 (FNA nibbles, AGET OOB, image E2E) → 011.3 (typed catch, EXC-PROPAGATE,
EXC-TAIL, click-stage fixes, oracle) → 011.4 (ARSC value path, v0.11.4-fix-01)
→ campaign-012 (NEVER EXECUTED — provenance UNKNOWN, closed LED-035) → 013
(dialogs, hierarchy, onDraw, ARSC probe, scoreboard) → 014 (partial; code lost,
evidence archived) → Pass-1 reconciliation (K-01..K-05 semantic fixes; 6fda28d) →
Pass-2 (switch/neg/div-zero/parse/lit8-claim; 9d095f9..272f216c) → **Pass-3
(this pass: K-34..K-41 below + full forensic audit)**.

## 4. Pass-3 new findings and fixes (each discriminated FAIL-before / PASS-after)

| ID | Finding | Pre-fix truth at 272f216c | Evidence | Decision |
|---|---|---|---|---|
| K-34 | InputStream.read()/available()/close() returned 0 (old shadow comment) | only readLine bypassed the stub | pass3 ST 5/5 vs independent `unzip -p` oracle (6582083 = real bytes 43 6f 64) | VERIFIED_MISSING→FIXED |
| K-35 | XmlPullParser absent; android.util.Xml.newPullParser absent; StringReader.<init> absent | zero source hits | pass3 X 7/7 (event seq 224331, self-closing 2232433, next-after-END_DOCUMENT throws XmlPullParserException via typed catch) | VERIFIED_MISSING→FIXED |
| K-36 | AtomicReference absent (get/set/getAndSet/compareAndSet) | zero source hits | pass3 AR 7/7 incl. identity discriminators (class-name-match fake would fail) | VERIFIED_MISSING→FIXED |
| K-37 | **lit8 opcode table STILL shifted +3** after the Pass-2 "K-31 fix" (its fixture reused the shifted header constants → self-consistent); PLUS three INVENTED opcodes SHL/SHR/USHR_INT_LIT16 at 0xD8..0xDA colliding with real add/rsub/mul-int/lit8; PLUS REM_DOUBLE_2ADDR=0xD0 colliding with ADD_INT_LIT16 | real 0xDB (div-int/lit8, ×2361 corpus hits) executed as ADD; 0xE0 (shl-lit8, ×3399) as AND; real D8 bytecode mis-dispatched | `scripts/audit_opcode_table.py` (independent AOSP reference): 11 shifted names + 19 byte mismatches → after fix: 0 shifted; residual 5 = cosmetic aliases (USHR vs USHRT spelling; RSUB_INT_LIT16 naming; MOVE_WIDE_16 alias absent — no dispatch impact) | VERIFIED_MISSING→FIXED |
| K-38 | lit16 (22s) register nibbles decoded ONE NIBBLE OFF (vA=(>>8), vB=(>>4)) — the K-05 bug class again | every lit16 op read source/dest from wrong fields | pass3 DR: 7/-2 via div-int/lit16 = 0 pre-fix, -3 post-fix | VERIFIED_MISSING→FIXED |
| K-39 | NEW_ARRAY stored length as `__new_array_length__` while aget/aput/read read `__array_length__` | bulk byte reads saw length 0 | st_bulk_read count=16 after fix | VERIFIED_MISSING→FIXED |
| K-40 | aget-byte/char/short zeroed typed heap elements (`make_int(0)` for non-INT32); typed registers (BYTE/CHAR/SHORT) carry values in separate union members that int_val arithmetic cannot see | aget-byte[0] = 0 on array filled with 'C' | after typed-element normalization: 16067 (16×1000 + 67) | VERIFIED_MISSING→FIXED |
| K-41 | parseInt("2147483648") wrapped to INT_MIN instead of NumberFormatException (acc == 2^31 accepted on the positive side) | FIX-05 boundary bug | ps_parseInt_overflow PASS post-fix | VERIFIED_MISSING→FIXED |
| K-42 | parseDouble/parseFloat rejected the Java words NaN / ±Infinity (strtof would also accept non-Java "nan"/"inf") | documented FIX-05 residual TODO | ps_parseDouble_nan_word + infinity PASS post-fix | VERIFIED_MISSING→FIXED |

Discriminating evidence committed: `run/pass3_evidence/before_fix_FAIL.txt`
(**20 FAIL** on pre-fix engine 272f216c) vs `after_fix_PASS.txt` (**60 PASS**).

## 5. Re-verification of prior claims at this HEAD (nothing accepted blindly)

- RESULT_001/009/010 (long 64-bit, cmp-long, conversions): fixtures 14/14; the
  Pass-3 conversion matrix (14 more cases incl. NaN/±Inf/truncation/2^53) also
  green — engine CONV macros were correct; the earlier failures were fixture
  constants, corrected and documented.
- 12x register encoding: distinct-register cases (add-long/2addr, neg/not
  vA≠vB) — reversed nibbles would fail. PASS.
- Opcode table vs AOSP: audit script, 0 shifted names (§ PASS3_OPCODE_AUDIT.md).
- packed/sparse-switch: forward + BACKWARD targets, non-zero first_key, default
  fallback — 3 new cases green.
- div/rem: ÷0 throws ArithmeticException via lit16/23x/2addr forms too; negative
  divisors correct on int/long/23x/lit16.
- parse/string: MAX/MIN boundaries, NFE on overflow/empty/whitespace, exponent,
  NaN/Infinity words, substring boundaries + SIOOBE, concat empty/unicode.
- AtomicReference / XmlPullParser / InputStream: new runtime bridges, tested.
- ARSC (RESULT_016): c013_arsc_probe on real simplestopwatch APK → "arsc valid",
  layouts 3/3 (re-run this pass).
- Real onDraw + multi-frame (§15/§16): `--click-test` on real simplestopwatch APK
  → real handler `onButtonStart` dispatched → state changed → second frame
  re-rendered with **12,439 changed px** (`run/pass3_click_evidence/`).
- Golden regression (goldens are law): simplestopwatch **2a12587a** BASELINE_MATCH
  ×3 runs (deterministic, pixel-exact, also under --click-test); gmdice 4fd3ce0e,
  microtimer eb16ab5c, unote d6b854c4, dooz 31ddd4d5 — all byte-identical. The
  lit8/lit16 table corrections did NOT move any golden (golden-critical paths use
  opcode forms whose corrected dispatch produces identical results — verified by
  byte-comparison, not assumed).
- Fixtures: 7 legacy suites 84/84 + Pass-3 suite 60/60 = **144 fixture cases**.

## 6. Real APK validation (corpus, §20)

chessclock ba017f51 (real SeekBar UI) · headingcalculator 7d2a6860 (real
ListView) · bgclockhansdezwart 2f85dd74 (themed window) · bouncy dc6a565e ·
tictactoeemmanuelmess 31ddd4d5 (libGDX boundary) · simplekeyboard/openlauncher
eb16ab5c (documented entry-chain gap, unchanged) · droidify exit=1 —
**BLOCKED_BY_MISSING_ARTIFACT** (truncated download; never counted as code
failure). Telegram golden APK f5e11927 remains lost (K-26) → NOT REPRODUCED,
documented; not a code regression.

## 7. Rejected / duplicate / superseded knowledge (preserved, never deleted)

- TOOL-CLAIM-4A39F1B ("176-176"): absent from every ref/archive → REJECTED_WITH_EVIDENCE.
- f5da664 / "v0.12.0": never existed in any recoverable artifact → REJECTED_WITH_EVIDENCE (three-way evidence).
- Pass-2 K-31 claim "AOSP-correct lit8 table": found WRONG (+3 residual shift) → superseded by K-37 this pass; the historical claim is retained in K-31 with this correction appended.
- exp018 "NATIVE_CPP parse*" report-only claim: implemented for real in Pass-2 (K-19/20) and now boundary-corrected (K-41/42) — claim→implementation→verification chain closed.
- RESULT_003 virtual-clock determinism proposal: ANALYSIS ONLY; determinism is
  achieved by staged reruns + hash pinning (design note retained).

## 8. OMISSION AUDIT answer to the §32 question

"Would my method find a major fix in an old campaign/ZIP/commit that the latest
NOT_DONE or README does not mention?" — YES, because this pass: (a) hashed and
git-inspected EVERY archive including both 0-byte ones (recorded, not ignored);
(b) proved every archive HEAD is an ancestor of the canonical lineage and every
tag is present; (c) ran fsck unreachable/dangling (0), reflog (1 superseded
docs-only commit), log --all (360 = HEAD); (d) re-derived the opcode table from
an INDEPENDENT AOSP reference instead of trusting the repo's own constants —
which is exactly the method that caught the Pass-2 self-consistent lit8 shift
(K-37), the lit16 nibble bug (K-38), and five more missing fixes (K-34..K-42);
(e) demanded FAIL-before/PASS-after discrimination for every new claim.

## 9. Remaining open items (honest, none is a lost fix)

Compose hook (K-24), GLES dispatch hook (K-25), layout geometry/fonts/audio
(NOT_DONE #7-9), WhatsApp/Signal entry chains, entry-chain gap apps
(simplekeyboard/openlauncher), Canvas matrix exhaustive composition (NOT_DONE
#15), Telegram golden APK re-acquisition (K-26), true v0.14.0 (needs campaign-014
re-run), DEX-APUT-BOUNDS auto-grow (deferred), MOVE_WIDE_16 (0x06) alias not
present in the engine's constant table (cosmetic; opcode unused by dispatch),
cosmetic USHR/USHRT + RSUB_INT_LIT16 naming deltas.

## 10. Verdict

`OMISSION AUDIT: PASS` — under the evidence standard defined in §2/§8: every
lineage is closed into the canonical history, every claim in the ledger carries
one of the eight required decisions with provenance, and every fix newly
integrated this pass has discriminating runtime evidence at the final HEAD.
