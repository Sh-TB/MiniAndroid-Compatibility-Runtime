# CONT-46 — Revalidate CONT-45 on current HEAD + the DEX↔Bridge object-flow contract

**Umbrella**: Issue #375 (CONT-46 next execution stage). **Directive**: continue
from the latest remote HEAD; revalidate F-NEW-260/261; investigate F-NEW-262 as a
data-flow question; probes before patches; smallest generic fix; real-APK fan-out
x3; line-by-line audit on the issue.

## Phase 0 — current-head reconciliation (all rows measured, not assumed)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| Stale-snapshot recovery | TESTED | local HEAD was 7622e268 (pre-rebase CONT-11-W7 duplicate, NOT an ancestor of origin/main); reset to origin/main 8f2f6aab4f0f54e77f6081de03e483b89b198ccd per directive; tmp/flappycow submodule dirt unaffected | git reset --hard origin/main (this session, scripts/cont46_refetch_apks.sh for the lost tmp/ APKs) |
| APK identities | TESTED | dooz_23 299eab21ac8b3c61, microtimer_8 79c6f730f64886e7, unote_30 be91103f0e7db443, gmdice_8 1621eda11b5dbc0c, opencalc_53 2642613868a8a80f, tananaev_11 294a68bd00debbdc (refetched SHA-exact vs CONT-43 §4), simplecalc_8 68da25fd9fdf54b4 (refetched SHA-exact), composeStopwatch_1009011 dbf937ebbe7c0b3d (refetched SHA-exact), bmi_402 2dbd8ebe2db56801, alexcalc_20 b1383bc950ce8483, notes_secuso_105 71e874f45fa4655f, solitaire base.apk fdfaf7cad18e4416 | sha256sum (Phase-0 records; scripts/cont46_refetch_apks.sh verified all three refetches against the CONT-43 recorded pins) |
| Rebuild | TESTED | incremental rebuild from HEAD → binary 56c045260767ac667f65553275768fbef9296f01d5aa877c868545fbd3abfa95 (rc=0) | run/build_cont46.log |
| Baseline gates (pre-fix binary 56c04526) | TESTED | anchors 27/27 ×3 byte-identical (dooz 31ddd4d5b8e6d18e, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622, tanana 5f7e0114c3bfd6b5); csw target ×3 3442d9a9dc0fa0f9 MATCH (REGAINED face); simplecalc control ×3 e847ca0346708f07 MATCH; probe battery == records exactly (fcol 140/0, f259 49/0, f259g 84/7 — the 7 FAILs are the known F259-L throwing-slot collection row ×7, pre-existing, not a standing gate; f266 42/0 … fnew298 19/0 KEEP=5 corner=PASS); skill self-test 13/13 PASS rc=0 | run/cont46/phase0_gate.log |
| Registry counts | TESTED | 619 roots at start (last IDs …304/305/306/307/308/260/261/262 — CONT-45 append verified present on remote) | root_registry.json |
| Skill self-test | TESTED | 13/13 after rebuilding fixtures/hmap_probe (lost to the container reset; scripts/cont46_build_hmap.sh, sha 9253e818eb530cfb) | run/cont46/skill_selftest.log |
| LAW-001 preflight | TESTED | all Phase-5 targets in ABI scope: BMI pure-java; alexcalc x86_64 present; solitaire/notes/controls pure-DEX or x86_64 | miniandroid/APK_REGISTRY.json + cont45 ledger |

## Phase 1 — F-NEW-260 / F-NEW-261 revalidation on the rebased tree

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| F-NEW-260 implementation present | TESTED | dex_parser.cpp:540-600 captures the SYSTEM Ldalvik/annotation/InnerClass; accessFlags into ClassInfo.inner_class_flags; dalvik_engine.cpp:28351+ prefers them in Class.getModifiers | source inspection at 8f2f6aab |
| F-NEW-260 positive/negative probe | TESTED | fixtures/fnew260_probe (real aapt2/ECJ/D8): **13/13 PASS** on 56c04526 — public/protected/package/private × static/non-static member classes, nested interface, anonymous, top-level, isMemberClass predicates, framework-token negatives (Handler/String answer PUBLIC, never typed-zero) | run/cont46/probe_fnew260/run.log |
| Anonymous-class law | TESTED | OpenJDK 21 host-JVM oracle: `new Runnable(){}.getClass().getModifiers()` = **0x0** (InnerClasses access_flags verbatim); ECJ emits accessFlags=0 in the SYSTEM annotation; the engine's 0x0 answer MATCHES the law (initial probe row wrongly asserted FINAL — fixed to assert the oracle law) | /tmp ModTest run (OpenJDK 21.0.12.1) + run/cont46/probe_fnew260 |
| F-NEW-260 runtime face | TESTED | BMI BackStackRecord.doAddOp getModifiers gauntlet executes (Class.getModifiers/isMemberClass/Modifier.isPublic/isStatic rows) on 56c04526/a63bf3b5 | run/cont46/bmi_post/run.log:688-691 |
| F-NEW-261 implementation present | TESTED | dalvik_engine.cpp:6821-6880 S83 gate with the F-NEW-261 family-level DEX-body fall-through (Landroid/support/ prefix + class_info_index_ hit) | source inspection |
| F-NEW-261 support fall-through live | TESTED | BMI FragmentActivity.onCreate executes REAL DEX on current HEAD (TRY-ENTRY + attachHost chain); FragmentManagerImpl executes end-to-end after F-058-R (enqueueAction → Handler.post → EXP090-DRAIN → ensureExecReady → generateOps → executeOps → moveToState) | run/cont46/bmi_post/run.log |
| F-NEW-261 androidx scope | OBSERVED | androidx stays on the S83 bypass (unchanged this wave; notes untouched — the fall-through arm is a separate bounded A/B, see F-NEW-262 m3) | dalvik_engine.cpp:6874-6876 |

**F-NEW-260/261 verdict: LIVE INCREMENTS on the rebased tree** — the remote
lineage (F-NEW-286/289/302/304 + CONT-43/44 laws) did NOT subsume either; both
revalidated by probe + runtime rows at the current HEAD.

## Phase 2 — F-NEW-262 as a register/data-flow question (per-manifestation)

### Manifestation 1 — BMI FragmentHostCallback.mHandler (RE-ROOTED + FIXED)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| Static decode | TESTED | FragmentActivity.<init>: `mHandler = new FragmentActivity$1(this)` (pc3-8); FragmentHostCallback(FragmentActivity): `iget-object v0, v3, FragmentActivity.mHandler` then `invoke-direct {v2,v3,v3,v0,v1}` into the 4-arg ctor; 4-arg ctor: `checkNotNull(v4, "handler == null")` → move-result-object v2 → `iput v2 → mHandler` | scripts/cont46_disasm.py on bmi_402.apk (2dbd8ebe2db56801) |
| PRE runtime trace (56c04526) | OBSERVED | FIELD-TRACE: `put-obj FragmentActivity.<init> FragmentActivity.mHandler obj#12 value=obj#29` ✓; `get-obj FragmentHostCallback.<init> FragmentActivity.mHandler obj#12` ✓; **`put-obj FragmentHostCallback.<init> FragmentHostCallback.mHandler obj#30 value=<unset>`** ← first divergence; getHandler reads <unset>-null; NO execPendingActions/moveToState rows; screenshot = action-bar band + empty content (2 colors, 57159cc2293be8b0) — NOT REAL_APP_CONTENT | run/cont46/bmi_trace/run.log:386-401 |
| Exact first divergence | TESTED | `invoke-static {v4, v2}, Landroid/support/v4/util/Preconditions;->checkNotNull:(Object;Object;)Object` was refused DEX dispatch by the EXP-058-era blanket name gate (dalvik_engine.cpp:8797-8804: `class_descriptor.find("Preconditions") && method == "checkNotNull"` → STUB-ONLY return false) → bridge_to_api → ActivityShadow 4-level hierarchy walk (EXP088-B rows) → not_handled → **no result-slot write** → move-result-object read <unset> | dalvik_engine.cpp:8797-8804 + EXP088-B-DISPATCH rows (bmi_trace log:397-400) |
| Provenance | TESTED | R-NEW-365 (S47) root-caused this EXACT gate and F-058 removed it ("check* helpers are identity-on-non-null; a stub must never destroy a checked reference", VERIFIED-FIXED); the cross-campaign recovery import commit d7427016 (2026-09-04) resurrected the stub while the docs survived — a documented regression re-introduction | docs/evidence/s47/S47_EVIDENCE_MANIFEST.md:74-95 + `git log -S"overload loop"` |

### Manifestation 2 — solitaire Window.getCallback (SUPERSEDED on current lineage)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| Re-run on current HEAD | TESTED | rc=1, **0 uncaught** (the recorded 28-IAE face no longer reproduces); `[S134-GCB] bridge getCallback … act=21` answered and the wrapper wrapped successfully | run/cont46/sol_head/run.log |
| New first divergence | OBSERVED | `IllegalArgumentException "View AppBarLayout@209 is not a drawer"` at DrawerLayout.j pc=34 (isDrawerView via g(View): LayoutParams gravity g.a:I resolved 0) — frame = single-color 0x5d80f0 theme face ba50a4d28ea62fe7 → **F-NEW-309 appended (CLASSIFIED)** | run/cont46/sol_head/run.log + static decode of j/g |
| Static decode | TESTED | i.<init> (WindowCallbackWrapper) does its OWN inline null check (IAE string inside the ctor) — the old IAE required a null ARG; on current HEAD the arg is non-null, so the check passes and the machine advances to DrawerLayout | scripts/cont46_disasm.py on solitaire base.apk fdfaf7cad18e4416 |

### Manifestation 3 — notes mFragmentLifecycleRegistry (BLOCKED for tracing)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| Static decode | TESTED | androidx FragmentActivity.<init>: `mFragments = FragmentController.createController(new HostCallbacks(this))` (shadow-bridge + move-result-object shape) and `mFragmentLifecycleRegistry = new LifecycleRegistry(this)` (pure DEX shape) — both candidate loss shapes identified | scripts/cont46_disasm.py on notes_secuso_105.apk |
| Runtime trace | BLOCKED | the androidx family stays on the S83 bypass (F-NEW-261 measured scope law) — the init chain never executes on current HEAD; classification requires the EXPERIMENTAL androidx fall-through arm (a bounded A/B, not a ship change). Exact next command: build an experimental binary with `f261_support_family` extended to androidx (single-line gate change), run notes + probes, record BEFORE/AFTER, revert | dalvik_engine.cpp:6874-6876 |

## Phase 3 — semantic probe matrix (BEFORE patching)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| fnew262_probe (PRE arm) | TESTED | 16 PASS + **3 FAIL (CK-1/2/3)** on 56c04526: checkNotNull(nonNull) lost identity, result lost through move-result-object, null NEGATIVE did not throw — the gate suppresses both the identity law AND the throw law; BR-1..4 / NI-1..5 / AM-1..2 / WV-1..3 / MR-1 / EX-1 all PASS (the abstract object-flow contract is sound for non-gated shapes) | run/cont46/probe_fnew262/run.log |
| fnew260_probe | TESTED | 13/13 PASS after oracle-correcting 3 expectation rows | run/cont46/probe_fnew260/run.log |
| Probe APKs | TESTED | fnew262_probe.apk 320f3f2f55d5dd16 (CK build), fnew260_probe.apk 2a47b0351822ad54 (13/13 build); built via scripts/cont46_build_probes.sh (real toolchain) | scripts/cont46_build_probes.sh |

## Phase 4 — the fix (F-058-R)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| Smallest generic fix | TESTED | DELETE the resurrected EXP-058 Preconditions.checkNotNull stub-only gate (8 lines); NO package-name conditions, NO new class allowlists, NO fake objects — the DEX body executes; genuine loops remain covered by F-056 descriptor-aware cycle keys + M3-19/F-017 active-cycle law + MAX_RECURSION_DEPTH | dalvik_engine.cpp F-058-R comment block (lines ~8797-8822) |
| Rebuild | TESTED | rc=0 → binary a63bf3b53ac3c082 (16-prefix) | run/cont46/post_fix_gate.log |
| POST probe arm | TESTED | fnew262_probe: **19/19 PASS** (CK-1/2/3 flipped FAIL→PASS at the same APK) | run/cont46/probe_fnew262_post/run.log |
| POST runtime face | OBSERVED | FIELD-TRACE `put-obj …mHandler obj#30 value=obj#29` (identity restored); Handler.post enqueues Runnable id=38 → dequeued → EXP090-DRAIN invoked → ensureExecReady/generateOps/executeOps/moveToState execute; BMIMain.onStart/onResume + ReportFragment lifecycle rows land; 0 uncaught | run/cont46/bmi_post/run.log |

## Phase 5 — real-APK fan-out and honest remaining frontier

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| BMI pre-fix | OBSERVED | action-bar shell face: 2 colors (225,225,225 content bg + 48,48,48 bar band), NO fragment content — F-NEW-262 m1 live | run/cont46/bmi_head/screenshot.png 57159cc2293be8b0 |
| BMI post-fix | PARTIAL | past the recorded first divergence (transaction machine executes; 0 uncaught) but NOT yet REAL_APP_CONTENT: the app layout root 78 never attached under the delegate's id-swapped ContentFrameLayout 163 (`[P0-1-ORDER] first-traversal attach wave root=78 attached=0`; ViewTree = ActionBarOverlayLayout 146 → ContentFrameLayout 163 kids=[] + ActionBarContainer 166) — the AOSP `mLayoutInflater.inflate(resId, mContentParent)` leg of the v7 delegate setContentView path; NEXT bounded decode (delegate content-parent attach law) | run/cont46/bmi_post_vt/view_tree.json |
| Solitaire | PARTIAL | 0 uncaught on current HEAD; new first divergence F-NEW-309 (drawer gravity) — CLASSIFIED, fix next wave | run/cont46/sol_head |
| notes | BLOCKED | masked by the androidx S83 bypass (see m3) | — |
| AlexCalc | BLOCKED | androidx family bypassed; first blocker on the fall-through arm = FitWindowsLinearLayout.makeOptionalFitsSystemWindows NoSuchMethod (F-NEW-219 deferred family) + androidx attach — same experimental-arm prerequisite as m3 | cont45 ledger + static decode this wave |
| Post-fix regression gate | TESTED | 33/33 MATCH on a63bf3b5 (anchors ×3 + csw ×3 + simplecalc ×3 byte-identical); probe battery == records exactly (f259g 84/7, fnew302 48/24 = the documented counts, zero probe drift); skill 13/13 rc=0 | run/cont46/post_fix_gate.log |
| Fan-out ×3 (fixed binary) | TESTED | bmi 57159cc2293be8b0 ×3 (deterministic shell face), sol ba50a4d28ea62fe7 ×3, notes **eb5ebd559cad1028 ×3 = its recorded anchor byte-identical** (the S83 androidx scope law held through the fix), alex c8d69f811b23f245 ×3 (first stable recorded face), dooz 31ddd4d5b8e6d18e ×3, micro da73010a37dd0189 ×3, unote 4f1a9e4e8f64fae8 ×3 — 21/21 runs, 0 uncaught everywhere, zero drift | run/cont46/fanout.log (scripts/cont46_fanout.sh) |

## Honest bounds

1. The F-058-R fix moves BMI past its recorded first divergence and restores the
   check* identity/throw contract corpus-wide (the gate matched ANY
   "*Preconditions*" class — support AND androidx AND app-local), but BMI is NOT
   at REAL_APP_CONTENT yet: the delegate content-parent attach leg is the next
   root, precisely located with runtime rows and ViewTree evidence.
2. F-NEW-262 manifestation 2 is SUPERSEDED on the true lineage; manifestation 3
   is BLOCKED behind the androidx fall-through A/B (deliberately NOT run this
   wave — the F-NEW-261 scope law is a measured, standing decision; changing it
   without its own bounded A/B would violate the same discipline).
3. The checkNotNull stub's sibling EXP-058 gates (SkippingHelper19,
   HelperInternal, AppCompatTextViewAutoSizeHelper) were audited but LEFT
   UNTOUCHED — no evidence of current harm, and each removal needs its own
   probe + A/B (minimal-fix discipline).
