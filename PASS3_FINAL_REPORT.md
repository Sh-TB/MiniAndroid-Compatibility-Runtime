# MINIANDROID — FINAL CANONICAL MASTER RECONCILIATION / FORENSIC KNOWLEDGE + FIX AUDIT
Pass 3 (final audit pass) — 2026-09-03 — branch `integration/master-reconciliation`
Remote canonical: `github.com/Sh-TB/MiniAndroid-Compatibility-Runtime` (own master, NOT a fork)
**NO PUSH PERFORMED — remote verified untouched at bbe0ce3 (ls-remote at pass start AND end)**

---

## 1. Baseline

```text
REMOTE:          github.com/Sh-TB/MiniAndroid-Compatibility-Runtime
                 main = bbe0ce3067401211af35402483b96baae69220df (ls-remote: ONLY ref; UNTOUCHED)
STARTING HEAD:   272f216c (Pass-2 reconciled state; SHA-verified ZIP 2e93d27d…)
FINAL HEAD:      ada6f4b9fe45de10d24fba6c7514000a54412a1f
BRANCH:          integration/master-reconciliation (bbe0ce3 verified ANCESTOR → fast-forward path, no force ever)
TAGS:            10 (v0.11-unified-011 … v0.14.0-partial, campaign-012-baseline, pre-integration-local-rescue)
COMMITS:         361 (full non-shallow history from 1c5255a "Initial commit")
WORKTREE:        clean (0 dirty tracked files) · fsck --full: clean · is-shallow: false
```

## 2. Historical sources scanned — counts

```text
ZIPs inspected (hashed + extracted + .git-inspected):   13  (incl. 2 zero-byte: recorded CORRUPT_EMPTY, not ignored)
Git bundles inspected (verify + list-heads):             3  (all "records a complete history")
Archive HEAD commits proven ANCESTOR of canonical HEAD: 10  (388fb45, 340a9cf, 6c9a91e, ea81e00(x3 tags), b9d93cc, 2ede367, 894eae2, 0fd1ad6, 272f216c + shallow boundary a9434de)
Archive tags vs canonical tags:                          superset holds — no tag exists outside canonical
Git commits inspected (rev-list --count --all):        360→361 (log --all == HEAD; nothing outside branch)
Tags inspected:                                          10 (all resolve to commits; all present in archives' subsets)
Dangling/unreachable objects (fsck --full --unreachable): 0
Reflog entries:                                         18 (1 reflog-only commit b5d2140: docs-only draft, superseded by its own amend 0fd1ad6 — content preserved)
Knowledge/claim rows tracked:                           50 (KNOWLEDGE_LEDGER.csv, 8-state vocabulary)
```

## 3. Ledger decisions (KNOWLEDGE_LEDGER.csv, 50 rows)

```text
VERIFIED_IMPLEMENTED          27
VERIFIED_MISSING (fixed this pass)  9  (K-34..K-42)
VERIFIED_PARTIAL               1  (RESULT_014 Canvas matrix composition — open, documented)
REJECTED_WITH_EVIDENCE         2  (TOOL-CLAIM-4A39F1B; f5da664/"v0.12.0")
DUPLICATE                      4  (gap-matrix dedups, preserved with provenance)
BLOCKED_BY_MISSING_ARTIFACT    5  (campaign-014 code, Telegram golden APK, droidify.apk, 2 zero-byte ZIPs)
NEEDS_RUNTIME_PROOF            4  (Compose hook, GLES hook, geometry/fonts/audio boundaries, entry-chain apps)
                                  (ledger also records claim/implementation/verification SEPARATELY for every row)
```

## 4. Newly integrated fixes (each: FAIL-before → PASS-after at the recorded commits)

```text
FIX-P3-01 (K-34) InputStream.read()/available()/close() — REAL asset bytes (was a 0-returning shadow).
         Evidence: pass3 ST 5/5 vs independent `unzip -p` oracle (6582083 = bytes 43 6f 64 = "Cod").
FIX-P3-02 (K-35) XmlPullParser REAL event machine (START_DOCUMENT→tags/TEXT→END_DOCUMENT,
         next() after END_DOCUMENT THROWS XmlPullParserException) + android.util.Xml.newPullParser
         + StringReader.<init>. Evidence: pass3 X 7/7 (event packing 224331; self-closing 2232433; typed catch).
FIX-P3-03 (K-36) AtomicReference get/set/getAndSet/compareAndSet — reference IDENTITY semantics
         (a class-name-compare fake implementation FAILS the discriminator). Evidence: pass3 AR 7/7.
FIX-P3-04 (K-37) OPCODE TABLE FORENSIC CORRECTION: the Pass-2 "K-31 fix" left lit8 SHIFTED +3
         (real 0xDB div-int/lit8 — ×2361 corpus hits — executed as ADD; 0xE0 shl-lit8 as AND),
         INVENTED opcodes SHL/SHR/USHR_INT_LIT16 at 0xD8..0xDA colliding with real
         add/rsub/mul-int/lit8, and REM_DOUBLE_2ADDR=0xD0 colliding with ADD_INT_LIT16.
         Independent AOSP reference audit: 11 shifted names + 19 byte mismatches → 0 semantic shifts.
FIX-P3-05 (K-38) lit16 (22s) register nibbles one-nibble-off (K-05 bug class) — every lit16 op
         read source/dest wrongly. 7/-2 via div-int/lit16: 0 pre-fix → -3 post-fix.
FIX-P3-06 (K-39) NEW_ARRAY length field inconsistency (__new_array_length__ vs __array_length__).
FIX-P3-07 (K-40) aget-byte/char/short zeroed typed heap elements → typed-element normalization
         (16×1000+67 = 16067 proves count AND content).
FIX-P3-08 (K-41) parseInt("2147483648") wrapped to INT_MIN → now NumberFormatException (Java range law).
FIX-P3-09 (K-42) parseDouble/parseFloat NaN/±Infinity words implemented; non-Java "nan"/"inf" rejected.
Commit: ada6f4b (code + fixture + evidence + docs in one atomic commit).
```

## 5. Semantic validation (runtime evidence at final HEAD)

```text
Pass-3 differential fixture (60 cases): 60/60 — before_fix_FAIL.txt: 20 FAIL on 272f216c (committed)
RESULT_001 long 64-bit (2^32+1):            PASS (legacy 14 + parseLong 2^32)
RESULT_009 cmp-long -1/0/+1:                PASS (3 cases)
RESULT_010 conversion matrix (12 ops + NaN/±Inf/truncation/2^53):  PASS (pass3 CV 14 cases)
12x register encoding (distinct registers, reversed-nibble would fail): PASS
Opcode table vs AOSP:                       0 semantic shifts (PASS3_OPCODE_AUDIT.md)
packed/sparse-switch fwd/backward/non-zero-key/default: PASS (7 legacy + 3 new cases)
div/rem ÷0 ArithmeticException (23x/lit8/lit16/2addr, typed catch + unwind): PASS
neg/not family incl. INT_MIN wrap:          PASS (7 cases)
parseInt/Long/Float/Double boundaries + NFE cases: PASS (MAX/MIN/overflow/empty/whitespace/exponent/NaN/Infinity)
substring boundaries + SIOOBE; concat empty/unicode: PASS
Exception handling typed catch/unwind:      PASS (unified0113 8/8)
ARSC resolution (RESULT_016) on real APK:   c013_arsc_probe: "arsc valid", layouts 3/3 (re-run this pass)
```

## 6. Regression gate — goldens are law

```text
simplestopwatch 2a12587a0acf196c  BASELINE_MATCH ×3 runs (deterministic; also under --click-test)
gmdice 4fd3ce0e · microtimer eb16ab5c · unote d6b854c4 · dooz 31ddd4d5 — byte-identical pre/post
Legacy fixtures after ALL opcode changes: 84/84 (7 suites) — zero regression
Total fixture cases: 144/144
NOTE: dooz wall-time varies with host load (153.5s under load → 0.8s idle); the golden LAW is the
screenshot SHA, which is byte-stable; timing variance recorded, not hidden.
Telegram golden (088ea640): NOT REPRODUCED — golden APK SHA f5e11927 lost in cache wipe (K-26 data
loss, documented since Pass-1; upstream serves newer bytes). Not a code regression.
```

## 7. Multi-frame + real-APK evidence (§15/§16/§20)

```text
run/pass3_click_evidence/click_test_report.json (real simplestopwatch APK, --click-test):
  real click → handler onButtonStart (REAL bytecode) → state_changed=true → second frame
  re-rendered through the REAL pipeline → changed_px=12,439 (matches 011.3 committed oracle);
  onButtonReset likewise; screenshot SHA under click-test = 2a12587a (golden holds).
Corpus (exit 0, screenshot SHA):
  chessclock ba017f51 (real SeekBar UI) · headingcalculator 7d2a6860 (real ListView)
  bgclockhansdezwart 2f85dd74 (themed window) · bouncy dc6a565e · tictactoeemmanuelmess 31ddd4d5
  simplekeyboard/openlauncher eb16ab5c (entry-chain gap, unchanged — documented)
  droidify exit=1 → BLOCKED_BY_MISSING_ARTIFACT (truncated 5 MiB download; recorded, never counted)
  + matrix goldens: simplestopwatch/gmdice/microtimer/unote/dooz (see §6)
```

## 8. Git integrity

```text
is-shallow: false · fsck --full: clean · fsck --unreachable --dangling: 0 diagnostics
commits: 361 (full history) · tags: 10 · worktree: clean · zero-APK policy: 0 APKs tracked
bbe0ce3 (remote main) is an ANCESTOR of ada6f4b → future main advance = fast-forward, NO force
Push procedure (ONLY on explicit user order):
  git push github integration/master-reconciliation:integration/master-reconciliation
  git push github integration/master-reconciliation:main   # fast-forward
```

## 9. Final handoff

```text
File:    MiniAndroid_CANONICAL_MASTER_RECONCILED_ada6f4b.zip   (157,342,440 bytes)
SHA256:  2bb58e5d91b1b1603791df3e6b38f57ea5ccd93e6229253f8341895e85664b1f
Bundle:  BACKUP_CANONICAL_PASS3_ada6f4b.bundle
SHA256:  1eeec64cebb8d42ce92c1596939c67b6dcfbee26ef278a3a841785374dbc7a30
Contents: repo/ = full tracked tree (source, tests, fixtures, docs, knowledge, evidence)
          + complete non-shallow .git (361 commits, 10 tags, all branches)
CLEAN-EXTRACTION TEST (fresh dir, nothing from the working dir):
  git: HEAD=ada6f4b · non-shallow · 361 commits · fsck clean · 10 tags · bbe0ce3 ancestor ✓
  build: make -j2 → 0 errors ✓
  fixtures from extraction: pass3 60/60 · long_cmp_conv 14/14 · switch_parse_neg 25/25 · typed_catch 8/8 ✓
  golden from extraction: simplestopwatch 2a12587a BASELINE_MATCH · gmdice 4fd3ce0e · unote d6b854c4 ✓
```

## 10. OMISSION AUDIT

| Historical source | Held | Now lives at |
|---|---|---|
| v0.11 → v0.11.4 ZIPs (4) | version commits 388fb45..b9d93cc | canonical history (ancestors + tags) |
| campaign-012-baseline / v0.13.0 ZIPs | ea81e00 / 2ede367 | ancestors + tags |
| v0.14.0_PARTIAL ZIP | 894eae2 + 16-app triage evidence | ancestors + tag + docs/campaign014_evidence/ |
| v0.14.0 + FULL_VALIDATION ZIPs | (interrupted packaging) | RECORDED as 0-byte corrupt — not silently dropped |
| Pass-1 review ZIP + bundle | 0fd1ad6 lineage | ancestors |
| Pass-2 reconciled ZIP | 272f216c lineage | ancestors (start of this pass) |
| 3 backup bundles | bbe0ce3 / 0fd1ad6 complete histories | verified complete; heads present in canonical |
| Reflog commit b5d2140 | docs draft | superseded by amend; diff = 3 doc lines; content preserved |
| K-index K-01..K-33 + gap matrix 38 findings | all prior claims | re-verified at HEAD; ledger LED-001..050 |
| **Pass-2's own K-31 claim** | "AOSP-correct lit8 table" | **FOUND WRONG (+3 shift) — superseded by K-37 with full provenance retained** |

New this pass that NO previous report/README/NOT_DONE mentioned: K-34..K-42 (9 fixes), the
self-consistency failure mode of the Pass-2 fixture (lesson: never validate a table with
constants derived from the same table), and the archive-corpus ancestor proof.

### Verdict
```text
WHAT WAS FOUND:            9 valid missing fixes (K-34..K-42), 1 superseded prior fix claim (K-31),
                           2 empty handoff ZIPs, 1 reflog-only docs commit, 50 ledger rows.
WHAT WAS INTEGRATED+PROVEN: K-34..K-42 with 20-FAIL-before/60-PASS-after discrimination,
                           144/144 fixtures, goldens ×3 byte-identical, real-APK + click/multi-frame
                           evidence, ARSC probe 3/3, clean-extraction build+test from the final ZIP.
WHAT IS STILL NOT PROVEN/BLOCKED: Telegram golden (APK lost), campaign-014 code (lost with workspace),
                           Compose/GLES hooks, entry-chain apps, Canvas matrix composition —
                           each documented with its exact blocker (none is a "lost fix").
OMISSION AUDIT: PASS
```
