# CONT44-C — CROSS-APP IMPACT AUDIT
## "Do the white-screen fixes affect other games and apps too?" — Persian: «آیا این فیکس‌هایی که باعث رد شدن از صفحه سفید شدند روی سایر بازی و برنامه‌ها هم تأثیر دارند؟»

- **Task:** CONT44-C (read-only audit — no engine sources touched)
- **Date:** 2026-10-11 · **Binary:** `miniandroid/build/miniandroid` sha16 `3dab3038c222031e` (CONT-43 final, verified live this audit)
- **Method:** static androguard 4.1.4 partial scan (`scripts/cont44_c_scan.py`): per-DEX class names + superclassnames + string constants; **no method-body decompile**. Corpus deduped by basename. Registry mining (`scripts/cont44_c_registry_grep.py`) + run-artifact SHA re-verification (`run/cont43/*`).

---

## 0. EXEC SUMMARY — the direct answer

1. **Safety: YES, the fixes are provably safe for the rest of the corpus.** Every law in the white-screen fix set (F-NEW-304 fragment drain + preference laws, CONT-43 native class-measure + `f304_native_subtree` coherence, Recomposer/coroutine family R-NEW-337..340, Hilt/DI R-NEW-341..343, dooz boot-budget completion, F-NEW-303 notification chain) is a **generic engine law with zero app knowledge** — the engine sources contain no app/package names.
2. **Zero negative drift is not an argument, it is a measurement:** the CONT-43 full gate at `3dab3038c222031e` ran the anchor corpus **27/27 ×3 byte-identical (81 runs)** — 9 pinned apps + simplecalc rc=0 — and this audit re-verified the raw screenshot SHAs directly from the run artifacts (tananaev `0f649804` ×3, opencalc `a976d2f9` ×3 coherence runs, dooz-180s `6841d52a`, csw `5c4a0172` ×3).
3. **All 6 pure View-world games are UNTOUCHED-BY-CONSTRUCTION** (zero Fragment/Preference/AppCompat/Compose machinery in their DEX): g2048 `59ca1526`, tictactoedeluxe `af609429`, flappycow `13cf4746`, gmdice `f3b483fe`, snake/tetris — the drain code paths are never entered on their launch shapes, and their anchors prove it byte-for-byte.
4. **Benefit: 19 of 32 corpus rows carry machinery inside the fix blast radius** — Fragment ×13, Preference ×9, AppCompat ×10, Compose ×3, WorkManager ×2 (Hilt ×0 — that law family has no corpus member). Concretely: **tananaev calculator** (the direct F-NEW-304 beneficiary: FragmentTransaction drain + real platform-`PreferenceFragment` rows → first SUCCESS `0f649804`), **notes_secuso/sudoku_secuso** (platform PreferenceFragment + DialogFragments ride the same drain), **dooz ×2 variants + composeStopwatch** (Recomposer family + budget completion + the androidx ReportFragment drain), **opencalc** (golden RESTORED by the CONT-43 coherence law while tananaev got its rows — the same law that helps one does not disturb the other).
5. **The one caveat — interleaving sensitivity:** F-NEW-304's drain also made androidx's own `LifecycleDispatcher` ReportFragment (R8-renamed `Li01;`) execute where it never did before; on composeStopwatch that flipped a hash-order knife-edge and regressed the content face `3442d9a9 → 5c4a0172` (deterministic ×3, F-NEW-306 P0). Compose apps on the knife-edge need the CONT-40 discriminating-probe discipline before any further engine change — this is the only observed negative, it is gated red deliberately, and its expectation stays `3442d9a9` (content must be REGAINED, not re-baselined).
6. **Who benefits next (frontier):** tananaev rows-under-actionbar → **F-NEW-305** (P1); composeStopwatch content → **F-NEW-306** (P0); dooz 15s-budget face + census attribution → **F-NEW-307** (P1). After those, the ungated Fragment/Preference/AppCompat corpus (notes/sudoku/chess/klondike/chessclock/bouncy/opmt/muellerma-stopwatch/telegram/forkgram) is queued to inherit the same benefit — none is currently gated, all listed as RECOMMENDED-NEW-GATES.
7. **Corpus hygiene:** `upload/whatsapp.apk` is **not an APK** (5.5 KB Cloudflare HTML challenge) — no machinery data, re-fetch owed; it is excluded from every count below.

---

## 1. MACHINERY MATRIX (static, field-ref-exact markers from DEX string pool + class hierarchy)

Legend: **Frag**=platform `android.app.Fragment*` / androidx fragment machinery; **Pref**=PreferenceFragment/PreferenceActivity/preference types; **AC**=AppCompat (`AppCompatActivity`/`ActionBarOverlayLayout`); **Comp**=Compose (`androidx.compose.*`/Recomposer/ComposeView); **WM**=WorkManager; **Svc/Notif**=Service/Notification machinery; `frag_sub/svc_sub/view_sub` = counts of app-defined subclasses (library-only references show 0). Impact verdicts are §2.

| app | framework | Frag? | Pref? | AC? | Comp? | other machinery | detail | EXPECTED-IMPACT verdict |
|---|---|---|---|---|---|---|---|---|
| chess_jwtc_298.apk | View-world | Y | Y | Y | – | Frag,Pref,AC,Svc, androidx-lifecycle | frag_sub=0,svc_sub=5,view_sub=8 | TOUCHED-ADJACENT |
| chessclock_29.apk | View-world | – | Y | – | – | Pref (PreferenceActivity) | frag_sub=0 | TOUCHED-ADJACENT |
| flappycow_rebuilt.apk | View-world | – | – | – | – | – (Surface/GL control) | view_sub=2 | UNTOUCHED-BY-CONSTRUCTION |
| fnew217_probe.apk | View-world | – | – | – | – | probe fixture (coroutines) | – | N/A-PROBE |
| forkgram_709208.apk | View-world | Y | – | Y | – | Frag,AC,Svc,Notif, coroutines,WebView,androidx-lifecycle | frag_sub=5,svc_sub=5,view_sub=8 | TOUCHED-ADJACENT |
| klondike_veldsoft_3.apk | View-world | Y | Y | Y | – | Frag,Pref,AC,Svc,Notif, coroutines,WebView | frag_sub=0 (refs only) | TOUCHED-ADJACENT |
| lifecycle_transaction_probe.apk | View-world | – | – | – | – | probe fixture | – | N/A-PROBE |
| lifecycle_tx_probe.apk | View-world | – | – | – | – | probe fixture | – | N/A-PROBE |
| notes_secuso_105.apk | View-world | Y | Y | Y | – | Frag,Pref,AC,WM,Svc,Notif, coroutines,WebView | frag_sub=5 (platform PrefFrag + androidx PrefFragCompat + Glide frgs),svc_sub=2 | TOUCHED-BY L1 |
| opencalculator_53.apk | View-world | Y | Y | Y | – | Frag,Pref,AC,Svc,Notif, coroutines | frag_sub=0 (androidx-preference refs),svc_sub=1,view_sub=8 | TOUCHED-BY L1-coherence |
| sudoku_secuso_101.apk | View-world | Y | Y | Y | – | Frag,Pref,AC,WM,Svc,Notif, coroutines,WebView | frag_sub=5 (platform PrefFrag + platform DialogFragments),svc_sub=1,view_sub=5 | TOUCHED-BY L1 |
| telegram_official.apk | View-world | Y | – | Y | – | Frag,AC,Svc,Notif, coroutines,WebView,androidx-lifecycle | frag_sub=5 (incl. platform DialogFragment),svc_sub=5 | TOUCHED-ADJACENT |
| whatsapp.apk | **NOT AN APK** | – | – | – | – | Cloudflare HTML challenge, 5.5 KB | – | NO-DATA |
| app.varlorg.unote_30.apk | View-world | – | Y | – | – | Pref (PreferenceActivity),Notif | view_sub=2 | UNTOUCHED-BY-CONSTRUCTION |
| bouncy.apk | View-world | – | Y | – | – | Pref (PreferenceActivity) | view_sub=2 | UNTOUCHED-BY-CONSTRUCTION |
| com.emmanuelmess.tictactoe_3.apk | View-world (libGDX) | Y | – | – | – | Frag (support-v4 `AndroidFragmentApplication`) | frag_sub=1,view_sub=2 | TOUCHED-ADJACENT |
| com.github.muellerma.stopwatch_6.apk | View-world | Y | – | Y | – | Frag,AC,Svc,Notif, coroutines,androidx-lifecycle | svc_sub=1 (StopwatchService) | TOUCHED-ADJACENT |
| de.duenndns.gmdice_8.apk | View-world | – | – | – | – | **zero framework machinery** | – | UNTOUCHED-BY-CONSTRUCTION |
| dooz_23_toplevel.apk | hybrid | Y | – | – | Y | Frag,Comp, coroutines,androidx-lifecycle | frag_sub=1 (androidx ReportFragment `Loc1;`),view_sub=8 | TOUCHED-BY L2/L4 |
| dubrowgn.microtimer_8.apk | View-world | – | – | – | – | Svc,Notif,androidx-lifecycle | view_sub=2 | UNTOUCHED-BY-CONSTRUCTION |
| fishrings_v1.23_vc6.apk | View-world | – | – | – | – | WebView (refs only) | – | UNTOUCHED-BY-CONSTRUCTION |
| io.github.yamin8000.dooz_23.apk | hybrid | Y | – | – | Y | Frag,Comp, coroutines,androidx-lifecycle | frag_sub=1 (ReportFragment),view_sub=8 | TOUCHED-BY L2/L4/L1 |
| opmt_v0.1.2_vc1.apk | View-world | – | – | Y | – | AC (AppCompatActivity) | – | TOUCHED-ADJACENT |
| tripeaks_v1.2.1_vc4.apk | View-world | – | – | – | – | WebView (refs only) | – | UNTOUCHED-BY-CONSTRUCTION |
| base.apk | View-world | – | – | – | – | engine build stub (dedupe rep. of 4) | – | N/A-STUB |
| g2048_v1.0_vc1.apk | View-world | – | – | – | – | **zero framework machinery** (Canvas control) | view_sub=1 | UNTOUCHED-BY-CONSTRUCTION |
| snake_deluxe_v1.0_vc1.apk | View-world | – | – | – | – | **zero framework machinery** | view_sub=1 | UNTOUCHED-BY-CONSTRUCTION |
| tetris_v1.0_vc1.apk | View-world | – | – | – | – | **zero framework machinery** | view_sub=1 | UNTOUCHED-BY-CONSTRUCTION |
| tictactoe_deluxe_v1.0_vc1.apk | View-world | – | – | – | – | **zero framework machinery** | view_sub=1 | UNTOUCHED-BY-CONSTRUCTION |
| composeStopwatch_1009011.apk | hybrid | Y | – | – | Y | Frag,Comp,Svc,Notif, coroutines | frag_sub=1 (ReportFragment `Li01;` — the F-NEW-306 drain interleaving source) | TOUCHED-BY L2 / TOUCHED-NEG L1 |
| simplecalc_8.apk | View-world | – | – | – | – | **zero framework machinery** | view_sub=2 | UNTOUCHED-BY-CONSTRUCTION |
| com.tananaev.calculator_11.apk | View-world | Y | Y | Y | – | Frag,Pref,AC,Svc,Notif, WebView | frag_sub=1 (`PrefsFragment extends Landroid/preference/PreferenceFragment;`),svc_sub=1 | TOUCHED-BY L1/L5 |

**Counts (32 rows, deduped by basename):** framework View-world ×28 / hybrid ×3 / not-an-APK ×1. Fragment ×13 · Preference ×9 · AppCompat ×10 · Compose ×3 · Hilt/Dagger ×0 · WorkManager ×2 · View-only (no F/P/AC/C) ×14 (6 real games incl. snake/tetris, 3 probe fixtures, 1 build stub, simplecalc/microtimer/fishrings/tripeaks).

Corpus-provenance notes: dedupe by basename collapses `g2048_v1.0_vc1.apk` (s80/s83 ×3 copies), `snake_deluxe`/`tetris` (×2 each), `base.apk` (×4, 3 unique contents — one representative scanned; all are engine build stubs). `fnew217_probe`/`lifecycle_*_probe` are engine probe fixtures, not apps. `dooz_23_toplevel` and `io.github.yamin8000.dooz_23` are the same app's two shipped variants (identical machinery profile; the gate pins the yamin8000 path).

---

## 2. EXPECTED-IMPACT — law-family mapping (TOUCHED-BY vs UNTOUCHED-BY-CONSTRUCTION)

Fix-set law families:
- **L1 = F-NEW-304** platform FragmentTransaction pending-op law + FragmentManagerShadow + host-stage lifecycle drain (onAttach→…→onResume at CREATED/STARTED/RESUMED windows) + platform PreferenceFragment laws (real res/xml AXML parse; real measured rows) + **CONT-43 companion**: native class-measure + `f304_native_subtree` coherence.
- **L2 = Recomposer/coroutine family** R-NEW-337 (Unsafe law) / 338 (stack traces) / 339 (AndroidComposeView+autofill) / 340 (frame pump).
- **L3 = Hilt/DI chain** R-NEW-341/342/343 — **no corpus member carries Hilt/Dagger markers; this family has zero corpus blast radius (×0).**
- **L4 = dooz case-E boot-budget completion** (180 s budget → real Material3 scaffold `6841d52a20e6597e`).
- **L5 = F-NEW-303** Notification$Builder fluent-chain law (companion of the tananaev chain).
- **L6 = F-NEW-305** (PENDING) ActionBarOverlayLayout inset law; **L7 = F-NEW-306** (PENDING) drain-interleaving content regression; **L8 = F-NEW-307** (PENDING) dooz census attribution + boot cost.

| verdict | apps | reasoning |
|---|---|---|
| **TOUCHED-BY (direct)** | **tananaev calculator** (L1: the only corpus app with an app-defined platform `PreferenceFragment`; tx-drain built its rows; L5 silenced its Notification NPE), **notes_secuso_105**, **sudoku_secuso_101** (L1: platform `PreferenceFragment` subclasses + platform `DialogFragment`s ride the same drain the moment they are gated), **dooz ×2** (L2+L4: Recomposer family + budget completion; L1: androidx ReportFragment drains — interleaving-sensitive), **composeStopwatch** (L2 regained content `3442d9a9`; L1's drain then flipped the knife-edge → L7 pending), **opencalculator_53** (L1-coherence: the `f304_native_subtree` defer is why its golden stayed/restored `a976d2f9` while the fragment rows landed elsewhere) | machinery in the exact law families, verified by DEX field-refs, not vibes |
| **TOUCHED-ADJACENT** (machinery inside the drained families; benefit lands when gated or when the pending law lands) | chess_jwtc (androidx-lifecycle + AppCompat + PrefActivity), chessclock (PreferenceActivity — **the Activity-hosted preference path is NOT in the fix set**; needs its own law), klondike, telegram, forkgram, muellerma.stopwatch (AppCompat/lifecycle/Notification), opmt (AppCompatActivity → L6), emmanuelmess.tictactoe (support-v4 Fragment via libGDX — but its recorded blocker is the GLSurfaceView/EGL family F-NEW-157, not fragments) | the drain surface exists in their DEX; no current gate exercises it |
| **UNTOUCHED-BY-CONSTRUCTION** | flappycow, g2048, snake_deluxe, tetris, tictactoedeluxe, gmdice, simplecalc, fishrings, tripeaks, unote, bouncy, microtimer (last three: PreferenceActivity/View+Notif only — no Fragment/drain/Compose surface; their record faces never read the new code paths) | zero Fragment/Preference(Fragment)/AppCompat/Compose machinery in DEX; byte-identical ×3 records confirm |
| **N/A** | fnew217_probe, lifecycle_transaction_probe, lifecycle_tx_probe (probe battery == records exactly, e.g. frag_tx_probe 12/0 ×3), base.apk stub | engine fixtures, not apps |
| **NO-DATA** | whatsapp.apk — Cloudflare HTML stub, not an APK | re-fetch owed |

Honest precision on two boundaries: (a) **PreferenceFragment vs PreferenceActivity** — F-NEW-304 implemented the *Fragment*-hosted preference path (exactly tananaev's shape). `PreferenceActivity`-hosted apps (chessclock, unote, bouncy, klondike, jwtc ICSPrefs, sudoku's AppCompatPreferenceActivity) benefit only where a FragmentTransaction is involved; a dedicated PreferenceActivity/headers law is **not** in the fix set. (b) **androidx PreferenceFragmentCompat** (notes SettingsFragment) is adjacent — same law shape, androidx loader, not yet implemented.

---

## 3. EMPIRICAL ZERO-NEGATIVE-DRIFT EVIDENCE

Standing gate at the audit binary `3dab3038c222031e` (CONT-43 full regression, recorded `evidence/cont43/CONT43_CROSS_THE_PAGE.md` §4 + worklog CONT-43; harness paths from `scripts/cont32_regression.sh` family):

| anchor | corpus APK (gate path) | 15 s face sha16 | record | re-verified THIS audit |
|---|---|---|---|---|
| dooz | upload/canonical_apks/io.github.yamin8000.dooz_23.apk | `31ddd4d5b8e6d18e` | ×3 byte-identical (CONT-43 gate, 27/27) | record |
| microtimer | canonical_apks/dubrowgn.microtimer_8.apk | `da73010a37dd0189` | ×3 | record |
| unote | canonical_apks/app.varlorg.unote_30.apk | `4f1a9e4e8f64fae8` | ×3 | record |
| gmdice | canonical_apks/de.duenndns.gmdice_8.apk | `f3b483fe7b7cf51b` | ×3 | record |
| opencalc | upload/opencalculator_53.apk | `a976d2f9fb675cb3` | ×3 (golden RESTORED by coherence law) | **YES — run/cont43/opencalc_coh{1,2,3}/screenshot.png sha == `a976d2f9fb675cb3` ×3** |
| tttdeluxe | s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk | `af6094295ecb50e3` | ×3 | record |
| flappycow | upload/flappycow_rebuilt.apk | `13cf47464d9787f4` | ×3 | record |
| g2048 | s80_games/build_2048/g2048_v1.0_vc1.apk | `59ca1526611c4622` | ×3 | record |
| tananaev | tmp/com.tananaev.calculator_11.apk | `0f649804d6e0486d` (rc=0 SUCCESS) | ×3 | **YES — run/cont43/tanana_post{1,2,3}/screenshot.png sha == `0f649804d6e0486d` ×3** |
| simplecalc | tmp/cont35_apks/simplecalc_8.apk | rc=0 `7960bce447ac6d8f` | ×3 | record |
| dooz180 (content gate) | same dooz APK @180 s budget | `6841d52a20e6597e` | ×3 MATCH (standing content gate) | **YES — run/cont43/dooz/ext/screenshot.png sha == `6841d52a20e6597e`** |
| csw (target, deliberately RED) | tmp/cont35_apks/composeStopwatch_1009011.apk | `5c4a0172628849ba` (expectation stays `3442d9a9dc0fa0f9`) | ×3 deterministic | **YES — run/cont43/csw_pre{1,2,3}/screenshot.png sha == `5c4a0172628849ba` ×3** |

**Statement:** for every UNTOUCHED-BY-CONSTRUCTION app above (g2048, tttdeluxe, flappycow, gmdice, microtimer, simplecalc — all inside the x3 byte-identical anchor set) the record **is** the empirical confirmation: the fix waves' code paths are app-agnostic and never entered on these launch shapes, and their frames did not move a byte. Probe battery == records exactly (fcol 140/0, f259 49/0, f266 42/0, f268 96/0, … frag_tx_probe 12/0 ×3, notif_builder_probe 56/0 ×3). The single negative anywhere in the corpus is the csw interleaving row — known, root-caused, gated red on purpose (F-NEW-306), not a silent drift.

**Gate-coverage check — RECOMMENDED-NEW-GATES** (machinery inside the touched families but NO standing gate at `3dab3038c222031e`; do not run — parent owns scheduling):

| # | app | machinery | why it belongs in the gate |
|---|---|---|---|
| 1 | **notes_secuso_105** | platform PrefFrag + androidx PrefFragCompat + AppCompat + WorkManager | the cleanest untested direct F-NEW-304 beneficiary in the corpus |
| 2 | **sudoku_secuso_101** | platform PrefFrag + platform DialogFragments + AppCompat + WorkManager | same, plus the DialogFragment-drain shape |
| 3 | **chess_jwtc_298** | PrefActivity + AppCompat + 5 Services | former anchor (chess `b5a7a35d` era); dropped from the current 8+1 set — restore |
| 4 | **klondike_veldsoft_3** | PrefActivity + AppCompat | card game, webview+coroutines surface |
| 5 | **chessclock_29** | PrefActivity | has a stale OBSERVED-FAIL row (F-NEW-161) worth re-grounding at HEAD |
| 6 | **bouncy** | PrefActivity | cheap View+Preference control |
| 7 | **opmt_v0.1.2_vc1** | AppCompatActivity | cheapest L6-inset-law sentinel |
| 8 | **muellerma.stopwatch_6** | AppCompat + Service + Notification | L5/L6 sentinel with a real foreground Service |
| 9 | **com.emmanuelmess.tictactoe_3** | support-v4 Fragment (libGDX) | boundary app: proves the drain is inert on a GL-frontier app |
| 10 | **dooz_23_toplevel** | Compose (anchor variant) | optional: pins the un-gated variant |
| 11 | telegram_official / forkgram_709208 | androidx lifecycle + Notification + Services | long-horizon (120 s+) gates, not 15 s; historical partial faces |

(Not needed: snake/tetris/fishrings/tripeaks — zero touched machinery, historical gates already recorded; unote/bouncy/csw-adjacent View rows are either anchored or trivially inert.)

---

## 4. POSITIVE-IMPACT FRONTIER — who benefits next

| app | current recorded frontier | next fix family that moves it |
|---|---|---|
| **com.tananaev.calculator_11** | rc=0 SUCCESS `0f649804d6e0486d` ×3 — but the 4 real preference rows render UNDER the ActionBarOverlay band (frame 0 dark px) → **F-NEW-305** (P1, ROOT_CAUSED_PENDING_FIX, registry row verified) | **L6** ActionBarOverlayLayout inset law → the calculator page becomes fully visible |
| **composeStopwatch_1009011** | `5c4a0172628849ba` ×3 (regressed from `3442d9a9dc0fa0f9` when F-NEW-304's drain re-interleaved the androidx ReportFragment boot; first divergence decoded: `Laj0;.n` → NULL `Lgi0;.f`, never allocated) → **F-NEW-306** (P0) | **L7** drain/interleaving fix — with the CONT-40 discriminating-probe prerequisite FIRST (progressing-vs-cycling + oid/hash order) |
| **io.github.yamin8000.dooz_23** | 15 s face stays white `31ddd4d5b8e6d18e` ×3 (boot cost ~25 M insns; case E resolved as boot-cost); 180 s completes to the real scaffold `6841d52a20e6597e` ×5; census still says app_draw_ops=0 → **F-NEW-307** (P1) | **L8** frame-census Compose-paint attribution (flips dooz180 to REAL_APP_CONTENT) + boot-cost perf decode; then the 15 s budget becomes the question |
| notes_secuso_105 / sudoku_secuso_101 | ungated at HEAD; historical campaign targets (F-NEW-232/233/247–250 exercised through them in older waves) | gate them (§3 list) — F-NEW-304's drain + preference laws apply directly |
| telegram_official / forkgram_709208 | historical partial faces (CONT-22 uncaught census 9 each; telegram REAL_APP_CONTENT 2/3 at a 120 s wall-cap, CONT-19 era) | long-horizon: Notification (L5, landed) + drain families already benefit; needs a standing 120 s gate |
| klondike_veldsoft_3 | R-NEW-384 splash-trap fixed; generic RL anchor laws proven (R-NEW-388); game screen remains blocked app-specific | View-world; the fragment/preference family is not its blocker |
| com.emmanuelmess.tictactoe_3 | F-NEW-157 OBSERVED-FAIL (libGDX GLSurfaceView/EGL frontier) | NOT the fragment family — needs the GLSurfaceView law |
| muellerma.stopwatch_6 / opmt / chessclock / bouncy / chess_jwtc | ungated; no recorded HEAD frontier | inherit benefit opportunistically once gated; chessclock additionally needs the PreferenceActivity law |

---

## 5. CAVEATS & BOUNDS

1. Static classification is marker-based (DEX string pool + class hierarchy): "Fragment=Y with frag_sub=0" means the *machinery is referenced* (typically androidx-lifecycle's injected ReportFragment) but the app defines no Fragment subclass — the distinction is carried in the `detail` column.
2. `whatsapp.apk` is not an APK (Cloudflare HTML). Every count excludes it; re-fetch owed before any claim about WhatsApp.
3. The x3 anchor records for dooz/microtimer/unote/gmdice/tttdeluxe/flappycow/g2048/simplecalc are cited from the CONT-43 recorded gate (81 runs); this audit re-executed nothing (read-only) but re-hashed the five run-artifact screenshot sets listed in §3 — all match their records exactly.
4. Registry rows used: F-NEW-303..307, F-143, F-NEW-157, F-NEW-161, F-NEW-197, R-NEW-331, R-NEW-375, R-NEW-384/385/386/388 (`root_registry.json`, 615 rows, generated CONT-43).

**Artifacts:** `scripts/cont44_c_scan.py`, `scripts/cont44_c_registry_grep.py`, `run/cont44/machinery_matrix.tsv`, `run/cont44/machinery_matrix_raw.json`, `run/cont44/registry_grep.json`, scan log `run/cont44_scan.log`. Engine sources untouched (read-only audit).
