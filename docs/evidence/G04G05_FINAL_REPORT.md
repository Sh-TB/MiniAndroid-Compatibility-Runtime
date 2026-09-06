# G04+G05 FINAL REPORT — DRAWABLE/IMAGE + LAYOUT/MEASURE/RENDER CLOSURE

Recorded 2026-09-06. Status vocabulary per Rule 0.1; no "100%"; boundaries explicit.

## A. Baseline

```text
Session-start HEAD: cc42a891 (main, clean) · origin/main 748c4337 (1 local
commit ahead, unpushed; auth unavailable → PUSH_BLOCKED recorded)
Battery at baseline: ALL PASS (26 stages, --skip-build) + make rc=0
G03 baseline: CONFIRMED reproducible (96/96 semantic, 14/14 MUTF-8,
48/48 config, 42/42 core law, 18/18 hostile, 18/18 encoded-value,
26-check helloworld, 8/8 tictactoe, 9/9 EXT-01 typography,
12/12 EXT-02 interaction, corpus 3/3, EXT-01 3-run 142238fd92b69e11)
Fixtures re-frozen after sandbox wipe: EXT-01 SHA 009b4671…cc41 EXACT;
reference screenshot (600×1067); aapt2 2.20-14304508; corpus hash-verified
```

## B. Findings

| ID | Finding | Disposition |
|---|---|---|
| FIND-G04-AUDIT-001 | tools/resource_trace.cpp claimed by d306f1e2 but NEVER COMMITTED — `make resource_trace` failed at HEAD | FIXED (291914c7) |
| FIND-G04-AUDIT-002 | Two devices in one runtime: config matching @480dpi vs dp→px @2.625(420) | FIXED — single 420dpi device (768b1481) |
| FIND-G04-AUDIT-003 | Drawable selection by ZIP-path-string ranking bypassed the canonical config engine (wrong under the isBetterThan density law) | FIXED — canonical select_file (768b1481) |
| FIND-G04-AUDIT-004 | Zero density scaling: bitmaps drawn at natural size; unqualified drawables (default density 160) drawn unscaled | FIXED — BitmapFactory inDensity→inTargetDensity law (768b1481) |
| FIND-G04-AUDIT-005 | Fossify Notes v1.7.0 is a Compose app — instruction's corpus item #4 not applicable to the classic pipeline | RESOLVED with evidence; Markor frozen as substitute |
| FIND-G04-AUDIT-006 | KISS/Markor render blank windows (AppCompatDelegateImpl shell; drawable resolution 0/35 partially symptomatic) | drawable half FIXED (FIND-007); AppCompatDelegate shell recorded as G06+ boundary |
| FIND-G04-AUDIT-007 | resid→R-field-name→basename chain = parallel resolution system; failed whenever R$drawable statics unparsed | FIXED — direct resid→select_file (3d1eba51) |
| MeasureFix-1 | EXACTLY/AT_MOST containers double-counted own padding (1080 EXACTLY + 100 padding measured 1180) | FIXED (894e6ef3), caught by the new law battery |
| MeasureFix-2 | Layout recomputed cross-axis match_parent sizes, ignoring margins the measure pass subtracted | FIXED — layout consumes measured dims (894e6ef3) |
| MeasureFix-3 | Weighted subtrees never re-measured with their EXACTLY share | FIXED — AOSP second pass (894e6ef3) |
| RealImageViewLaw | ImageView drew at (left+5, top+5) natural size (engine) or stretched-to-bounds (FIT_XY semantics) — no AOSP scaleType law | FIXED — FIT_CENTER default + density-scaled intrinsic (768b1481) |

## C. AOSP laws transferred (sources at /home/z/corpus/aosp_laws/, android-14.0.0_r2)

| Law | Source anchor |
|---|---|
| Density scaling: inDensity = selected TypedValue.density (0→160 default; DENSITY_NONE→no scale); inTargetDensity = display dpi; scale = target/source | BitmapFactory.java decodeResourceStream L568+; BitmapFactory.cpp L347-353 |
| Bucket selection: exact > both-above→smaller > straddle→higher > both-below→higher; DENSITY_ANY beats buckets | ResourceTypes.cpp ResTable_config::isBetterThan L2690-2737 |
| ImageView default scaleType = FIT_CENTER | ImageView.java L255 |
| ImageView onMeasure: intrinsic size drives content dims; 48dp only as unresolvable fallback | ImageView.java onMeasure L1141+ |
| LinearLayout weight: remainingExcess; sequential share=(int)(w·excess/sum); sum−=w per child; 0dp→share, else measured+share (shrinkable); weightSum cap; EXACTLY re-measure | LinearLayout.java L985-1045 (vertical), L1385-1445 (horizontal), L855 useExcessSpace, L1031/L1435 re-measure |
| Spec size includes own padding; layout consumes measured dims | View.measure/setMeasuredDimension; View.layout |

## D. Implementation (commit-by-commit)

| Commit | Content |
|---|---|
| e98cf4b0 | Initial audit (blind-verified baseline, FIND-001..006) + corpus registry (KISS/Notes/Markor) |
| 768b1481 | C2: unified 420dpi device; select_file canonical drawable selection (chain-safe, selected-config reporting); density scaling; FIT_CENTER; ImageSizeProbe (PNG/WebP/JPEG header-only); intrinsic measure |
| 291914c7 | C3: resource_trace recreated — id→decomposition→device→per-step configs→typed value→file/XML/BINARY→density→intrinsic; --bag; --layout inflate+measure+geometry dump; JSON evidence |
| 894e6ef3 | C4: EXACT LinearLayout weight law (sequential shares, 0dp+weight skip+from-scratch, base+share shrinkable, weightSum cap, subtree re-measure) + 2 MeasureSpec fixes + 24-check law battery |
| e7e6ec1b | C5: density-matrix differential oracle — real aapt2-built fixture, 11-check gate (selection+scaling+nodpi+alias+FIT_CENTER+determinism) |
| ae37abf4 | C6: hostile battery — probe/decoder/fit/resolver-cycles/layout-depth/child-count/weights/missing-drawable (24 checks) |
| 3d1eba51 | C7: DIRECT resid→drawable resolution (FIND-007) + corpus boundary record |

## E. Tests

```text
BATTERY GATE: ALL PASS (31 stages) at 3d1eba51 (pre-report commit)
  semantic long/cmp/conv 14 · switch parse-neg 25 · pass3 bridge 57 (96/96)
  MUTF-8 14/14 · resource-config 48/48 · resource core law 42/42
  resource hostile 18/18 · LinearLayout/MeasureSpec law 24/24 (NEW)
  G04 hostile 24/24 (NEW) · encoded-value 18/18
  helloworld_golden ALL PASS (26) · tictactoe_golden ALL PASS (8)
  EXT-01 run + typography golden 9/9 · EXT-02 interaction golden 12/12
  density-matrix oracle 11/11 (NEW) · corpus fetch + 3/3 runs
```

## F. External APKs

| APK | SHA-256 | Capabilities exercised |
|---|---|---|
| HelloWorldSelfAware 1.1.0 | 009b4671…cc41 | resource→pixel, typography, interaction (goldens) |
| SimpleStopwatch 26 / gmdice 8 / MicroTimer 8 | registry, hash-verified | boot+render regression; density-scaled icon intrinsic (72×105 ImageButton observed) |
| fr.neamar.kiss 3.26.0 (vC 224) | da6ab0b1…98c9 | 422 drawable configs, 110 ninepatch; boots, real DEX; AppCompat boundary |
| org.fossify.notes 1.7.0 (vC 13) | 5a56e0e3…bced | NOT APPLICABLE — Compose UI (evidence in DEX); frozen |
| net.gsantner.markor 2.16.1 (vC 163) | 3f9f260d…84b9 | classic Views; real DEX execution (deep app logic); AppCompat boundary |
| density-matrix fixture (project, aapt2) | per-build log (7a899a31… at freeze) | density law differential oracle |

Cache: /home/z/corpus/g04_corpus + miniandroid/download (zero-APK-in-repo intact).

## G. Runtime proof

Real APK → real DEX → canonical ARSC resolution (resolve_full, chain-safe)
→ selected config reporting → TypedValue semantics → drawable file boundary
(value-IS-path incl. AGP obfuscation) → density scaling → inflation →
measure (spec law) → layout (weight law, gravity) → render → deterministic
PNG. Observed: ImageButton measured 72×105 = 27×40 mdpi intrinsic × 420/160;
alias chain drew the xxxhdpi variant at 26×13 @420dpi and the xhdpi variant
at 40×20 @320dpi (same request, different devices — selection law visible).

## H. Visual proof

| Golden | Reference | MiniAndroid | Result |
|---|---|---|---|
| EXT-01 typography | author-published phone screenshot (600×1067) | 1080×1920 | 9/9 static checks; 3-run byte-identical 142238fd92b69e11 (unchanged through all G04/G05 commits) |
| EXT-02 interaction | before/after self-difference | frames 000/001 | 12/12 checks |
| density-matrix @420 | AOSP isBetterThan + BitmapFactory law (source-derived expectation) | exact bbox 26×13 yellow @ (40,40); nodpi 40×20 @ (40,73) | 8/8 pixel asserts; 3-run 351340a7a92e645c |
| density-matrix @320 | exact-bucket + no-scale law | 40×20 blue @ (40,40); nodpi y=80 | exact |
| helloworld / tictactoe | project fixtures | byte-identical goldens | ALL PASS |

Intentional dynamic differences: none introduced; EXT-01 golden bytes unchanged.

## I. Hostile proof

24 new checks (g04_hostile_test) + prior 18 (resource_hostile_test):
truncated/zero/0xFFFFFFFF-dim PNG, truncated WebP, garbage JPEG, empty
buffer → probe/decoder fail-safe (60000×60000 decode attempt bounded, 0ms);
fit_center degenerate inputs finite; A→B→A CYCLE, dangling →
MISSING_REFERENCE_TARGET, pkg-0 → INVALID_ID, 20-hop → DEPTH_EXCEEDED(16);
select_file on cycle → nullopt; 150-deep tree bounded; 10000 children 10ms;
negative/huge weights finite; unknown lp sentinel → wrap; missing drawable →
48dp fallback. No OOM/OOB/hang/corruption.

## J. Regression

Complete battery (31 stages) ALL PASS after every implementation unit;
all prior golden hashes byte-identical; G03 correctness strengthened
(FIND-001 repair; no G03 behavior weakened — the two G03-visible changes,
device density unification and select_file, are covered by 48/48 config
+ 42/42 core-law batteries and leave every frozen golden unchanged).

## K. GitHub evidence

Auth state: no gh token / credential helper in this sandbox (verified this
session) → PUSH_BLOCKED and COMMENT_BLOCKED. Payloads prepared, publishing
blocked honestly; direct URLs will be appended to scripts/comment_urls.json
by the same poster flow used for G31–G48/GOLDEN-01..03 (19 comments already
published on issue #8, incl. GOLDEN-03 evidence comment 5555733283).

| Type | Title | URL | Status |
|---|---|---|---|
| Issue comment (prepared) | G04+G05 closure evidence | PENDING AUTH — payload scripts/issue_comment_g0405.md | BLOCKED |
| Commits (7, local) | e98cf4b0…3d1eba51 | PENDING PUSH (fast-forward on origin/main 748c4337) | BLOCKED |

## L. Remaining gaps

**Blocking:** none for this campaign's closure gate.

**Non-blocking boundaries (explicit, evidence-backed):**
1. AppCompatDelegateImpl shell emulation — KISS/Markor boot + execute real
   DEX but their AppCompatActivity content assembly never materializes a
   ViewShadow tree (blank window). G06+ scope.
2. Nearest-neighbour image resampling (Skia decodes with filtering) —
   documented; law-level geometry identical.
3. NinePatch: .9.png currently stretch as plain bitmaps (corpus ships 110+
   per app; they live inside the AppCompat shell, so not reachable pre-G06).
   Minimal-correct patch-segment stretching queued behind the shell.
4. RealInflater (real_layout.cpp) is unreferenced dead code kept
   law-consistent; deletion queued for the duplicate-implementation ledger.

**Researched only:** NinePatch chunk laws, BitmapDrawable tileMode,
adjustViewBounds aspect path — source laws cited in the audit, not needed
by any reachable UI at this HEAD.

**Future G06+:** AppCompat shell, vector drawables (no in-app vector use in
the bootable corpus), Compose (explicitly out of classic-pipeline scope).

**Not applicable:** Fossify Notes v1.7.0 as a classic-pipeline corpus item
(Compose evidence: FIND-G04-AUDIT-005); launcher adaptive icons (not drawn
by any exercised path).
