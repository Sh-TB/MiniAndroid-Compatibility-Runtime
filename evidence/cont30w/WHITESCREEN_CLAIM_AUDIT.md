# CONT-30W — Resumable White-Screen Claim Audit, Lightweight APK Reproduction, and R-NEW-466 ServiceLoader Verification

Wave: CONT-30W (the user's "CONT-30" white-screen-audit directive + the R-NEW-466
test request; suffixed **W** because the repo's `CONT-30` label is already taken
by the F-NEW-286/287 GapComposer wave — no identifier collision).
Scope discipline: existing issues (#381/#382/#383/#384) and existing root IDs
reused; no new root registered (none was warranted — see §6).

## 0. RESUMABLE STATE BLOCK

```text
Current HEAD and branch:  b473c69b (main, 1 commit ahead of origin/main at
                          audit start — tmp-artifacts commit only; engine source
                          identical to pushed 4d302cfa)
origin/main:              4d302cfa (CONT-30 GapComposer wave push)
Working tree:             tmp/flappycow submodule dirty flag = run-artifact noise
                          (pointer unchanged); all wave changes committed at wave end
Runtime binary SHA:       b84114cd6f8bad1d (build/miniandroid, 134,708,912 bytes —
                          byte-identical to the CONT-30 record; built from HEAD
                          source with ZERO engine edits this wave)
Build command:            timeout 570 make -j1 BUILD_DIR=build (miniandroid/) —
                          NOT rebuilt this wave (no engine change; existing
                          binary verified against record)
Test APK SHA(s):          Simple Calculator vc8 68da25fd9fdf54b4 (re-supplied from
                          F-Droid archive this wave); dooz 299eab21ac8b3c61
                          (registry-exact); fnew252 probe rebuilt (see §5)
Commit lineage reconciled: YES (see §1 — 5 of 6 claimed commits NOT FOUND)
Current checkpoint:       A–I all executed (see §9 next-checkpoint)
Last completed command:   fnew252 fixed-script rebuild ×3 = SUMMARY|PASS 7/0
Verified claims:          R445-substance, R446-substance, R447, R448 (as
                          registered roots F-NEW-273/F-064/F-103/F-NEW-249);
                          R-NEW-466 "before" behavior REJECTED on this lineage
Rejected claims:          R-NEW-466 defect claims (a)/(b) do not reproduce on
                          current main; R461 "render root 0" rejected for this
                          lineage (FULL SUCCESS ×3)
Partial/unverified:       R460 (gap real, no failing app → no patch);
                          composeStopwatch claims UNVERIFIED (APK NOT FOUND)
First confirmed divergence: fnew252 SLPOS hasNext=false — ROOT: probe APK
                          packaging gap (META-INF/services omitted by the w4
                          rebuild script), NOT an engine defect
Exact source location:    scripts/w4_build_probes.sh (fixed this wave); engine
                          law src/dex/dalvik_engine.cpp:45779-45869 +
                          cached_asset_bytes apk-entry law :4753-4769
Current APK and SHA:      tmp/cont30w_apks/simplecalc_8.apk 68da25fd9fdf54b4
Build/binary SHA:         b84114cd6f8bad1d (unchanged)
Last screenshot path/SHA: run/cont30w/sc_r{1,2,3}/screenshot.png 7960bce447ac6d8f ×3
Metrics:                  sc runs rc=0, Errors 0/Warnings 0; f252 packed runs
                          7 pass/0 fail ×3; dooz anchor byte-identical
Changes made:             scripts/w4_build_probes.sh (META-INF packaging);
                          scripts/cont30w_probe_pkg.sh (new, discriminator);
                          evidence/cont30w/* (this file); NO engine changes
Tests run and results:    see §4/§5/§7
Regressions:              none (binary unchanged; anchors spot-checked byte-exact)
Next exact command:       see §9
Known blockers:           composeStopwatch APK unavailable; 9.6 MB "Simple
                          Calculator" variant NOT FOUND in this repo (§2)
```

## 1. PART 0 — REPOSITORY RECONCILIATION

| check | result |
|---|---|
| HEAD == b473c69b (main) | 1 unpushed tmp-artifacts commit over origin/main 4d302cfa; engine source identical |
| commit `cabecf21` | **NOT FOUND** (all local + remote branches) |
| commit `06d51505` | **NOT FOUND** |
| commit `4cfb0828` | **NOT FOUND** |
| commit `bf73a383` | **NOT FOUND** |
| commit `3d29366e` | **NOT FOUND** |
| commit `562ff2cb` | FOUND on main — UNRELATED (machine-named tmp/evidence snapshot commit `4d8a4981-…`, touches probe_store/f259/f266/f268 tmp files) |
| R445/R446/R447/R448/R460/R431/R461/R-NEW-466 as named roots | NONE of these identifiers exist in this repo's registry (594→597 rows audited; `R4xx`/`R-NEW-466` absent). The FUNCTIONALITY each describes exists under DIFFERENT registered roots (see §3) |
| worktrees | `/tmp/base_371` prunable detached — not used |

**Conclusion**: the reports describe a SEPARATE worktree/lineage. Their commit
SHAs and root IDs do not belong to this repo's history. Per the directive, the
claims were audited against CURRENT SOURCE SYMBOLS + runtime reproduction, not
against the reports' say-so.

## 2. LIGHTWEIGHT APK (CHECKPOINT B) — BASELINE REPRODUCTION, SOURCE UNCHANGED

The directive's "Simple Calculator APK, reportedly about 9.6 MB" — **NOT FOUND**
in this repo. The repo's existing Track B Simple Calculator is
`com.simplemobiletools.calculator` vc8 (899,994 bytes, Java/support-library era,
NO androidx.startup, NO kotlin, NO materialAlertDialogTheme/colorSurface in
resources — DEX+arsc string census this wave). Provenance: F-Droid archive,
sha16 `68da25fd9fdf54b4` == the CONT-26/27/28/29 record. Re-supplied this wave
from `https://f-droid.org/archive/com.simplemobiletools.calculator_8.apk` and
SHA-verified. The 9.6 MB figure belongs to the other lineage's app and remains
**UNVERIFIED** here.

Baseline on the current binary (`b84114cd6f8bad1d`), command:
`timeout 300 miniandroid/build/miniandroid run <apk> --width 1080 --height 1920 --frames 5 --max-seconds 15 -o <out>`

| run | rc | screenshot sha16 | errors/warnings |
|---|---|---|---|
| sc_r1 | 0 | `7960bce447ac6d8f` | 0 / 0 |
| sc_r2 | 0 | `7960bce447ac6d8f` | 0 / 0 |
| sc_r3 | 0 | `7960bce447ac6d8f` | 0 / 0 |

**The app is NOT white on this lineage**: ×3 byte-identical to the CONT-27/28/29
FULL SUCCESS record (app-owned keypad: display TextView '0', Buttons
mod/^/√/C, 7-8-9-÷, 4-5-6-*, 1-2-3 at the 270x262 grid, 121 unique colors —
F-NEW-283 DEX-existence constructor authority lineage). `RESUMED`/
`setContentView`/root-ID claims are NOT the proof here — the pixel record is.

## 3. CLAIM AUDIT TABLE

Verdicts per the directive's vocabulary. "Substance" = the behavior the claim
describes; on this lineage each substance is carried by an ALREADY-REGISTERED
root, so the claims are audited as SUPERSEDED/ACCEPTED-AS-CARRIED rather than
re-implemented.

| Claim | Verdict | Evidence | Source location | Runtime test | Next action |
|---|---|---|---|---|---|
| **R445** getProviderInfo missing/insufficient metaData; fix returns manifest-declared metadata | SUPERSEDED (substance PRESENT as **F-NEW-273**, CONT-21/#384) | manifest_provider_identity_/component_meta_data_ lookup, NameNotFoundException contract, GET_META_DATA flag gate, metaData seeded from manifest parse | dalvik_engine.cpp:40288-40430 | Simple Calculator + anchor battery render (startup chain works); dooz/opencalc F-273 evidence in registry | none — reuse F-NEW-273 |
| **R446** Bundle.keySet() missing/incorrect | SUPERSEDED (substance PRESENT as **F-064 / R-NEW-288** map-view family) | keySet/values/entrySet → live Set/Collection views (HashSet/ArrayList-backed, typed view_elements, obj:/string key decode) | android_shadows.cpp:2794-2862 | dooz anchor byte-identical (`d602648e8e401895` this wave) — F-064's original frontier app | none — reuse F-064 |
| **R447** isAssignableFrom compared generic `Ljava/lang/Class;` descriptor instead of `__referent_desc` | ACCEPTED-AS-CARRIED (substance PRESENT as **F-103**, S58/R-NEW-378) | heap Class token resolved via `__referent_desc` (27044-27054); OpenJDK assignability walk `dalvik_class_assignable` (24587+); null→false law | dalvik_engine.cpp:27002-27081, 24587+ | dooz ACCEPTABLE_CLASSES 29-element loop = F-103's original proof; anchors byte-identical | none — reuse F-103 |
| **R448** Class.forName ref_id used `instruction_sequence_` (collision risk); fix = `make_stable_class_token` | ACCEPTED-AS-CARRIED (substance PRESENT as **F-NEW-249**, CONT-6) | `make_stable_class_token` keyed by descriptor in `class_token_ids_`, mints `Ljava/lang/Class;` + `__referent_desc` exactly like const-class F-069; pre-fix comment documents the instruction_sequence_ behavior | dalvik_engine.cpp:19470-19499, call sites 47300-47333 | anchors byte-identical; fnew286 probe battery (Class-token-heavy) 10/0 per CONT-30 record | none — reuse F-NEW-249 |
| getDeclaredConstructor claim (exact token/represented class/interface-vs-impl/ctor result; dependency iteration yielding null) | SUPERSEDED (substance PRESENT as **F-106**, S60/R-NEW-380) | getDeclaredConstructor/getConstructor consult app DEX ctor tables (26094-26210) | dalvik_engine.cpp:26094+ | Simple Calculator FULL SUCCESS ×3; startup chain of all anchors | none — reuse F-106 |
| **R460** getPackageInfo(...).applicationInfo absent; fix populates it | PARTIAL / **gap REAL, patch NOT warranted here** | `applicationInfo` = **0 hits in src/**; getPackageInfo serves versionCode/Name/packageName + GET_PROVIDERS (#370 Gate A) + GET_SERVICES (F-NEW-275); `Context.getApplicationInfo` separately served (EXP-043 + F-NEW-190) | dalvik_engine.cpp:40575-40684, 43928-43975 | NO failing app on current main reproduces the gap (Simple Calculator FULL SUCCESS ×3; dooz anchor byte-identical) | PENDING: implement ONLY when a reproducible first divergence requires PackageInfo.applicationInfo (directive: no speculative fixes) |
| **R431** Window.setContentView + render-root registration for ordinary View apps | SUPERSEDED (substance PRESENT; multiple registered laws) | setContentView: android_shadows.cpp:4119/4173, dalvik_engine.cpp:38945/42350; render-root selection `effective_content_root_()` = ActivityShadow.content_view_id() with `android.R.id.content` (0x01020002) fallback | execution_engine.cpp:7688-7702 (+ 2981/6533/6633/7127/7828 consumers) | **Simple Calculator FULL SUCCESS ×3 byte-identical** (real ViewTree, measure/layout, draw, framebuffer) | none |
| **R461** capture-time render root was 0; probe measured the right root | REJECTED for this lineage | `effective_content_root_()` resolves Activity registration OR the 0x01020002 content fallback at render/tap/swipe/capture time | execution_engine.cpp:7688+ | Simple Calculator renders app-owned pixels ×3 — capture-time root cannot be 0/absent for this app on this binary | none |
| 41435-41545 dalvik_engine.cpp region | SUPERSEDED (lines shifted) | that region is now SharedPreferences typed getters (F-114 era); audited via current symbols instead | dalvik_engine.cpp:41435-41545 (current) | n/a | none |
| **R-NEW-466 (a)** ServiceLoader.iterator() register descriptor `Iterator` vs heap runtime class `ServiceLoader` caused dispatch failure | **REJECTED as a defect on current main** — the shape EXISTS by design (self-as-iterator "house pattern") but dispatch handles it | iterator() returns same sl_id typed `Ljava/util/Iterator;` + stamps `__sld_service__`; hasNext/next dispatch accepts BOTH `Iterator`- and `ServiceLoader`-typed entries, keyed on receiver heap fields, never static type | dalvik_engine.cpp:45779-45831 | fnew252 packed probe: SLPOS PASS ×3 (hasNext=true → SvcImpl materialized, tag=svcimpl) — the dispatch provably reaches the law ([S102-SL] diag) | none |
| **R-NEW-466 (b)** CollectionShadow claimed java/util/Iterator and answered hasNext()=false | **REJECTED on current main** | F-NEW-252 wave-2 DECLINE law: iterator/hasNext/next on a receiver holding the `service` marker → `not_handled()` so the engine's META-INF/services law runs; generic (marker-keyed, no app names) | android_shadows.cpp:441-459 | same SLPOS ×3 runtime proof (shadow did NOT swallow the iteration) | none |
| **R-NEW-466 fix**: dedicated `Iterator` heap object with `__sld_service__`/`__sld_pos__`/`__sld_loader__` markers + try_shadow_dispatch skip gate | **NOT PRESENT on current main** (`__sld_loader__` = 0 hits in src/; commits absent) | current main carries the F-NEW-252-wave architecture instead (self-as-iterator + shadow decline); the claimed patch is from the other lineage | search records §0/§1 | n/a — cannot transplant ("do not transplant a patch merely because its report says it worked") | record; do NOT port without a reproducing divergence |
| **R-NEW-466 runtime claims** (Main-dispatcher ISE gone; `l5`=AndroidDispatcherFactory/`t5`=AndroidExceptionPreHandler materialized; subsequent DataStore exception) | **UNVERIFIED** on this lineage | target APK `com_justdeax_composeStopwatch.apk` **NOT FOUND** anywhere in this repo (125 APKs inventoried); provider-name claims are the other lineage's R8 map | APK inventory §0 | cannot run | re-supply APK from its public source if desired; then reproduce before/after on THIS binary |
| **R-NEW-466 generic value** (ordinary ArrayList/HashSet iterators unchanged) | SUPPORTED | CollectionShadow decline is marker-keyed only; LAW-B iterator write-back law separate; F-237 real-iterator box unchanged | android_shadows.cpp:441-459, 461-540 | fcol probe battery (140/0 per CONT-29/30 records — iterator-heavy) unchanged at the same binary | none |

## 4. CHECKPOINT F RUNTIME EVIDENCE — SERVICELOADER ON CURRENT MAIN

Probe: `fixtures/fnew252_probe` (synthetic, real aapt2/ECJ/D8 toolchain;
`F252Core.serviceLoaderPositive` = `ServiceLoader.load(Svc.class).iterator()`
→ hasNext must be true → next() must materialize `SvcImpl` with tag
"svcimpl"; `serviceLoaderNegative` = provider-less service must answer
hasNext=false with no crash).

### 4.1 The first divergence found this wave (probe as-built by `w4_build_probes.sh`)

```
F252|SLPOS|FAIL|hasNext=false          ← provider NOT discovered
F252|SLNEG|PASS|no provider → hasNext=false
F252|SUMMARY|FAIL|6 pass, 1 fail
[S102-SERVICELOADER] load com.probe.f252.Svc (lazy ServiceLoader obj#30)
[S102-SL] reached method=iterator recv=30
[S102-SL] reached method=hasNext recv=30
```

Dispatch REACHED the engine law — so R-NEW-466's claimed dispatch/shadow
defects are NOT the cause. Root cause of the FAIL:

```
unzip -l fnew252_probe.apk  →  AndroidManifest.xml, resources.arsc, classes.dex
                               (NO META-INF/services entry)
```

The w4 rebuild script never packaged the fixture's `META-INF/services/` tree
into the APK. The engine's `apk-entry:` law then answered honest-empty
(`[S102-APK-ENTRY] MISS … (honest empty — no fabrication)`) — correct for a
provider-less APK. This is a **probe-packaging gap**, and it also explains why
fnew252 silently dropped out of the recent probe batteries (CONT-28/29/30
batteries list fcol/f259/f259g/f266/f268/fnew253/fnew286 — no f252).

### 4.2 Discriminator (scripts/cont30w_probe_pkg.sh)

Same APK + the fixture's `META-INF/services/com.probe.f252.Svc`
(content `com.probe.f252.SvcImpl`) added as a ROOT ZIP entry:

```
F252|SLPOS|PASS|hasNext=true   (×3 runs, deterministic)
F252|SLNEG|PASS
F252|SUMMARY|PASS|7 pass, 0 fail
```

`asset_entry_bytes()` (in-process ZIP law, dalvik_engine.cpp:4761-4769) reads
the entry; the OpenJDK-LazyIterator-shaped engine law parses the provider line,
Class.forName's it (stable token), constructs it, and `tag()` answers
"svcimpl". **End-to-end ServiceLoader provider materialization WORKS on current
main when the APK actually carries the services entry.**

## 5. MINIMAL GENERIC FIX (CHECKPOINT H) — TEST-INFRASTRUCTURE ONLY

One semantic root: the probe build law must package fixture META-INF trees
(ServiceLoader discovery reads the APK's own entry table — libcore classpath
law). Fix: `scripts/w4_build_probes.sh` step 4b — if the fixture has
`META-INF/`, `zip -r` it into the built APK verbatim. Fixture-driven and
generic: any probe shipping a META-INF tree gets packaged; no per-probe or
per-app special case; no engine change; no package-name branching.

Post-fix proof (script-built APK, `df3baa2eeb14fdc98fbf`):

| run | rc | result |
|---|---|---|
| f252_fixed_r1 | 1 (frame-truth verdict, expected for probes) | `SLPOS\|PASS`, `SUMMARY\|PASS\|7 pass, 0 fail` |
| f252_fixed_r2 | 1 | same |
| f252_fixed_r3 | 1 | same |

The probe's rc=1 is the F-NEW-233 frame-truth gate verdict
(VIEWTREE_NO_APP_PIXELS — the probe asserts via `|PASS|` log markers + the
results file, per the long-standing battery convention; prior battery rows are
counted the same way). Engine binary: `b84114cd6f8bad1d`, UNCHANGED.

**No engine patch was warranted this wave**: every R-NEW-466 engine-behavior
claim either already exists under a registered root (F-NEW-252 family) or does
not reproduce. Implementing the other lineage's dedicated-iterator patch would
be a transplant without a reproducing divergence — forbidden by the directive.

## 6. REGRESSION / SPOT-CHECKS AT THE UNCHANGED BINARY

| check | result |
|---|---|
| Simple Calculator ×3 | byte-identical `7960bce447ac6d8f`, rc=0 (FULL SUCCESS retained; APK re-supplied SHA-exact) |
| dooz anchor ×1 | byte-identical `d602648e8e401895` (frozen record), rc=1 known frame-truth verdict; zero S102 traffic at its frontier |
| fnew252 probe (fixed build) ×3 | 7/0 PASS deterministic |
| engine binary | unchanged `b84114cd6f8bad1d` — full 24-anchor battery not re-run this wave (no engine source edit; spot-checks byte-exact) |

## 7. HONEST NON-CLAIMS

- composeStopwatch was NOT tested (APK NOT FOUND). The R-NEW-466 report's
  runtime claims remain UNVERIFIED on this lineage — neither confirmed nor
  rejected. Provider-name identifications (`l5`, `t5`) are that report's R8 map
  and are NOT adopted as evidence here.
- The "9.6 MB Simple Calculator" variant was NOT found; all Simple Calculator
  numbers in this file are vc8 `68da25fd9fdf54b4`.
- No Compose content-pixel claims are made this wave; Track A state is
  unchanged from the CONT-30 record (F-NEW-288 TextUnit spin P0, named not
  fixed).
- R460's `PackageInfo.applicationInfo` gap is REAL in this repo's source but
  has NO failing app here; it stays PENDING, unimplemented, honestly.
- "Ordinary iterator behavior independently regression-tested": supported by
  the unchanged fcol battery record at the same binary + SLNEG behavior; a
  dedicated new iterator probe was not added this wave.

## 8. CROSS-TRACK GENERICITY NOTE

The one semantic law this wave adds to the test infrastructure is generic
across ALL probes: **a synthetic APK must carry its fixture's META-INF tree for
ServiceLoader/classpath discovery to observe it** — the same law real APKs obey
(their services entries live in the APK ZIP). It explains a false-NEGATIVE
probe row (silent coverage loss), not a runtime failure, and belongs to the
probe-build law family (real-toolchain recipes), matching how fnew253/fnew286
probes are built.

## 9. NEXT RESUMABLE CHECKPOINT

Exact next action for the following session (in priority order):

1. (optional re-supply) fetch `com_justdeax_composeStopwatch.apk` from its
   public source, SHA-pin it, reproduce the R-NEW-466 before/after on THIS
   binary; only then can that report's runtime claims be upgraded from
   UNVERIFIED. Do NOT transplant its engine patch without a reproducing
   first divergence on this lineage.
2. Consider adding fnew252 (now correctly packaged) permanently to the probe
   battery in the next regression script so the coverage cannot silently drop
   again (done for this wave's record in §5/§6; battery scripts are per-wave).
3. Carry over the standing next-wave targets from the CONT-30 record:
   F-NEW-288 (TextUnit value-class spin, P0) for Track A; Simple Calculator
   input-pump interactions for Track B; R460's PackageInfo.applicationInfo
   ONLY if a failing app appears.
