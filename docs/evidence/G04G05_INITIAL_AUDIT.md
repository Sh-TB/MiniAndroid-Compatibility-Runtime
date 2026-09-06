# G04+G05 INITIAL AUDIT — DRAWABLE/IMAGE + LAYOUT/MEASURE/RENDER CAMPAIGN

Recorded 2026-09-06, all values measured THIS session (not inherited).
Campaign: unified G04 (drawable/image) + G05 (layout/measure/render) closure.

## 1. Baseline (measured this session)

```text
HEAD:            cc42a891 (main, clean tree)
Origin/main:     748c4337 — local is 1 commit ahead (cc42a891 = GitHub
                 evidence tooling commit, unpushed; auth unavailable →
                 PUSH_BLOCKED recorded, no PUSHED/PERSISTED claims)
Battery:         BATTERY GATE ALL PASS — 26/26 stages (--skip-build; the
                 27th stage is the build itself, run separately: make rc=0,
                 binary 60,350,448 B)
Fixtures:        EXT-01 re-fetched SHA-256 009b4671…cc41 EXACT MATCH;
                 reference screenshot re-fetched (600×1067, author-published);
                 aapt2 2.20-14304508 restored (Google Maven); corpus 3/3
                 hash-verified re-fetched
Determinism:     EXT-01 3-run byte-identical, SHA 142238fd92b69e11 (frozen
                 G48 golden prefix — unchanged)
```

## 2. G03 baseline confirmation (exact)

| Suite | Result at cc42a891 |
|---|---|
| semantic long/cmp/conv + switch + pass3 | 14 + 25 + 57 = 96/96 |
| MUTF-8 string pool | 14/14 |
| resource-config selection law | 48/48 |
| resource core law (ResId/TypedValue/refs/bags) | 42/42 |
| hostile ARSC safety | 18/18 |
| encoded-value law | 18/18 |
| helloworld_golden | ALL PASS (26 checks incl. resource-chain discriminators) |
| tictactoe_golden | ALL PASS (8 checks, interaction + 10-frame determinism) |
| EXT-01 typography golden | 9/9 |
| EXT-02 interaction golden | 12/12 |
| corpus (stopwatch/gmdice/microtimer) | 3/3 SUCCESS, hash-verified |

G03 resource infrastructure is reproducible from HEAD and is treated as the
canonical foundation (no reopening except for the one concrete defect below).

## 3. Blind-verification findings (§0 discipline)

| ID | Finding | Status |
|---|---|---|
| FIND-G04-AUDIT-001 | Commit d306f1e2's message claims `tools/resource_trace.cpp` but the FILE WAS NEVER COMMITTED — `make resource_trace` FAILS at HEAD ("No such file or directory"). G03 §12 "trace tool" is not reproducible from HEAD. | CONFIRMED DEFECT — repaired in this campaign (§18 trace is rebuilt WITH G04/G05 channels) |
| FIND-G04-AUDIT-002 | `build_device_config()` requests density **480** (res_config.cpp) while `DeviceMetrics.density = 2.625` (**420dpi**) drives all dp→px conversion — TWO different devices in one runtime. AOSP law: ONE DisplayMetrics.densityDpi feeds config selection AND value conversion AND bitmap scaling. | CONFIRMED DEFECT — unified in this campaign (visual goldens prove 420dpi: 22sp→58px = ×2.625) |
| FIND-G04-AUDIT-003 | `RealInflater::drawable_path_for` selects density buckets by ZIP-PATH STRING RANKING (always prefers xxxhdpi), bypassing the G03 canonical config engine. AOSP isBetterThan density law (ResourceTypes.cpp @android-14 L2690–2737) selects: exact bucket > (both-above-requested → smaller) > (straddling → higher) > (both-below → higher). String ranking violates ALL of these except the straddle case. | CONFIRMED DEFECT — replaced with canonical `apk_path_for(id, paths, device)` |
| FIND-G04-AUDIT-004 | No density SCALING exists anywhere: bitmaps are drawn at natural pixel size. AOSP BitmapFactory.cpp native law: `if (inScaled && density!=0 && targetDensity!=0 && density!=screenDensity) scale = targetDensity/density`; Java law (BitmapFactory.java decodeResourceStream): inDensity = selected TypedValue.density (DENSITY_NONE → no scale), inTargetDensity = display densityDpi. Unqualified drawables default to DENSITY_DEFAULT=160 → scaled UP by 2.625 on the 420dpi device. | CONFIRMED DEFECT — implemented in this campaign |
| FIND-G04-AUDIT-005 | Fossify Notes v1.7.0 (F-Droid vC 13, SHA 5a56e0e3…) ships `androidx/compose/**` — its UI is Compose. The instruction's corpus item #4 is NOT APPLICABLE to the classic View pipeline (evidence: DEX class list). Substitute frozen: Markor 2.16.1 (classic Views). | RESOLVED — corpus adjusted with evidence |
| FIND-G04-AUDIT-006 | KISS v3.26.0 + Markor 2.16.1 boot, execute REAL DEX deeply, but render blank windows; Markor log: `drawable paths resolved via canonical resolver: 0/35`. Root cause cluster: AppCompat delegate paths (AppCompatDelegateImpl setContentView/theme subDecor) + drawable resolution misses. The drawable-resolution half is a G04 deliverable; the AppCompat-delegate half is recorded as an explicit boundary. | RECORDED — targeted G04 fix + boundary documentation |

## 4. G04/G05 capability matrix (current HEAD, evidence-based)

### G04 — drawable/image

| Capability | Status | Evidence |
|---|---|---|
| PNG decode (gray/RGB/RGBA/palette/tRNS) | IMPLEMENTED+tested | libpng-backed PNGDecoder; 7,036-image real-APK differential benchmark recorded in source header |
| JPEG/WebP decode | IMPLEMENTED | JPEGDecoder/WebPDecoder wrappers |
| drawable → APK path selection | **DEFECT** (parallel path-string ranker, FIND-003) | real_layout.cpp drawable_path_for |
| density-based config selection for drawables | **ABSENT on the consumption path** (G03 engine exists but is not used by inflate/image path) | — |
| density scaling after selection | **ABSENT** (FIND-004) | — |
| nodpi / DENSITY_NONE | ABSENT | — |
| mipmap | same path-ranker (no canonical law) | real_layout.cpp |
| ImageView scaleType (FIT_CENTER default) | **ABSENT** — two wrong behaviors: view_renderer stretches to view bounds (FIT_XY); execution_engine draws at (left+5,top+5) natural size | view_renderer.cpp L533+, execution_engine.cpp L1624+ |
| ImageView intrinsic-size measure | **ABSENT** — measure assumes 48dp when unknown; never decodes bitmap size | layout_inflater.cpp measure leaf branch |
| adjustViewBounds | ABSENT | — |
| ColorDrawable | PARTIAL (bg color) | view_renderer |
| shape drawable (solid/gradient/angle/corner/stroke) | PARTIAL (subset, no per-corner/ring/sweep) | load_shape_drawable |
| selector / state-list | **ABSENT** | — |
| layer-list | **ABSENT** | — |
| inset drawable | **ABSENT** | — |
| NinePatch | **ABSENT** (corpus ships 110+ .9.png per app — they stretch incorrectly as plain bitmaps) | corpus inventories |
| Vector drawable | ABSENT — boundary (recorded; not required by bootable corpus UIs) | — |
| alias/reference chains → drawable | resolve_full supports chains; consumption path does not use it | arsc_parser resolve_full |
| resource_trace | **BROKEN AT HEAD** (FIND-001) | Makefile → missing file |

### G05 — layout/measure/render

| Capability | Status | Evidence |
|---|---|---|
| MeasureSpec EXACTLY/AT_MOST/UNSPEC + getChildMeasureSpec | IMPLEMENTED (FIX-2 law) — but ZERO focused unit tests | layout_inflater.cpp measure pass |
| resolveSizeAndState | PARTIAL (no state bits) | same |
| LinearLayout weight (horizontal+vertical) | PARTIAL — weighted children forced base 0; AOSP law adds share to measured size for nonzero base; no sequential remainingWeightSum decrement; no weightSum cap check; no useLargestChild; no re-measure pass | layout_inflater.cpp |
| gravity (container + child) | PARTIAL — FIND-GRAVITY-VERTICAL fixed; baseline alignment absent | — |
| FrameLayout | PARTIAL | — |
| RelativeLayout | best-effort subset | — |
| ScrollView UNSPEC child law | IMPLEMENTED | measure pass |
| padding/margins | IMPLEMENTED in measure+layout | — |
| getSuggestedMinimumWidth/Height + android:minWidth/minHeight | ABSENT | — |
| visibility GONE | IMPLEMENTED; INVISIBLE partially | — |
| draw order / z | tree order only (no elevation) — boundary | — |
| deterministic frame capture | IMPLEMENTED (3-run byte-identical) | battery evidence |

## 5. Prioritized gaps (implementation order)

1. **P0 unify device** (FIND-002): one device (1080×1920 @420dpi, density 2.625) for config matching + dim conversion + bitmap scaling. Must not move the 22sp→58px law (2.625 stays).
2. **P0 canonical drawable selection** (FIND-003): replace string-ranker with `apk_path_for(id, paths, device)`/`resolve_full`; add selected-config reporting; DENSITY_NONE law.
3. **P0 density scaling** (FIND-004): selected-entry density → targetDensity scale on decode; ImageView draws scaled; measure uses decoded intrinsic size (AOSP ImageView onMeasure: intrinsic w/h = bitmap dims × target/inSource, FIT_CENTER default).
4. **P1 trace tool rebuilt** (FIND-001) with drawable/density/measure/layout/draw channels (§18) — evidence tool, canonical-resolver-only.
5. **P1 LinearLayout exact weight law** (sequential share, remainingWeightSum decrement, 0dp+weight vs base+share, weightSum, useLargestChild, re-measure pass) + focused MeasureSpec unit battery (§8).
6. **P1 selector/layer-list/inset** minimum per corpus evidence; NinePatch minimal-correct (stretch only patch segments per .9 data) if the corpus UIs reach them.
7. **P2 hostile battery extension** (malformed drawable refs/oversized bitmaps/invalid weights/pathological depth/integer overflow) (§16).
8. **P2 corpus + visual goldens + 3-run determinism** (§13/§15) incl. aapt2-built density-matrix fixture (mdpi/xhdpi/xxxhdpi/nodpi/unqualified) as the differential oracle artifact.
9. **P3 AppCompat-delegate boundary** — documented with evidence; NOT silently dropped.

## 6. Authoritative AOSP laws to transfer (fetched this session, exact revisions)

Source set: `android.googlesource.com platform/frameworks/base @ android-14.0.0_r2`
(local mirror `/home/z/corpus/aosp_laws/`):

| Law | Source (file, anchor) | Rule |
|---|---|---|
| Density scaling | BitmapFactory.java `decodeResourceStream` L568+; BitmapFactory.cpp L347–353 | inDensity = TypedValue.density (DENSITY_NONE → no scale); inTargetDensity = display densityDpi; scale = target/source when inScaled |
| Density bucket selection | ResourceTypes.cpp `ResTable_config::isBetterThan` L2690–2737 | exact > both-above→smaller > straddle→higher > both-below→higher; DENSITY_ANY beats buckets; unset candidate/default = 160 |
| ImageView default scaleType | ImageView.java L255 | FIT_CENTER |
| ImageView onMeasure | ImageView.java onMeasure L1141+ | intrinsic size; adjustViewBounds aspect path; resolveAdjustedSize |
| LinearLayout weight | LinearLayout.java L985–1045 (vertical), L1385+ (horizontal) | remainingExcess; share=(int)(childWeight·remainingExcess/remainingWeightSum); remainingWeightSum −= childWeight per child; height=0→share else measured+share; EXACTLY re-measure; weightSum>0 else totalWeight; useLargestChild branch |
| Child measure spec | ViewGroup.java `getChildMeasureSpec` | (already implemented FIX-2; tests added this campaign) |

## 7. External APK test plan (frozen this session)

| ID | APK | Version | SHA-256 | Role |
|---|---|---|---|---|
| EXT-01 | HelloWorldSelfAware | 1.1.0 | 009b4671…cc41 | resource→pixel + typography + interaction goldens |
| EXT-02 | SimpleStopwatch | 26 | (registry, hash-verified) | PNG icons + layout regression |
| EXT-03 | gmdice | 8 | (registry, hash-verified) | list UI regression |
| EXT-04 | MicroTimer | 8 | (registry, hash-verified) | corpus regression |
| NEW EXT-05 | fr.neamar.kiss | 3.26.0 (vC 224) | da6ab0b1…98c9 | 422 drawable configs, 110 ninepatch, AppCompat boundary probe; goal: 0/35→N/35 canonical drawable resolution + honest blank-window boundary record |
| NEW EXT-06 | org.fossify.notes | 1.7.0 (vC 13) | 5a56e0e3…bced | **NOT APPLICABLE — Compose UI** (evidence: androidx.compose classes in DEX); kept frozen for registry completeness |
| NEW EXT-07 | net.gsantner.markor | 2.16.1 (vC 163) | 3f9f260d…84b9 | classic Views substitute: 2110 drawable configs, 110 ninepatch, 1145 PNG; executes real DEX; drawable-resolution fix target (0/35) |
| NEW EXT-FIX | density-matrix fixture (project-built via aapt2) | — | per-build log | differential oracle: same bitmap in mdpi/xhdpi/xxxhdpi/nodpi/unqualified → selected-config + scaled-dimension proof at 160/420/480dpi device overrides |

Cache: `/home/z/corpus/g04_corpus/` (outside repo, zero-APK-in-repo law intact).

## 8. Expected closure gates

1. **Resource/Drawable**: canonical selection only (no path-string ranker anywhere — repo-audited), density law implemented + trace-observable, DENSITY_NONE, alias chains to file resources, decoder safety unchanged.
2. **Layout/Measure**: MeasureSpec unit battery green; LinearLayout weight law = AOSP sequential algorithm; intrinsic-size ImageView measure; weightSum/useLargestChild/second-pass.
3. **Render**: ImageView pixels land in FIT_CENTER geometry; deterministic 3-run byte-identity preserved on ALL existing goldens (hash-protected).
4. **Evidence**: trace tool exists at HEAD and covers request→…→draw for ≥10 scenarios; corpus frozen incl. boundary records; hostile battery green; full prior battery green; GitHub evidence with direct URLs (auth permitting; else payloads prepared + BLOCKED recorded).
5. **Status vocabulary**: only tested/observed/runtime-proven/visually-proven/verified with artifacts; boundaries marked explicitly, never silently omitted.
