# W9 — THE FULL REGISTERED-PROBLEM REVIEW (user directive, 2026-10-23)

Directive (translated): *"Go through the games. Review ALL registered problems of games and apps in one pass. For each with progress, post a comment — write the explanation and the steps. Go forward. Maybe they ALL share a common root."*

This ledger is that review, executed against the merged HEAD `276f7628` (registry **825 roots**, id-unique main==mirror). Per-issue problem-solved comments were posted on #227, #228, #230, #231, #343, #344, #346, #348 (the older root-cause issues whose states had moved without a closing comment).

## 1. Registry totals (one pass, all 825)

| Bucket | Count |
|---|---|
| FIXED family (ROOT-CAUSED-FIXED / VERIFIED-FIXED / ALREADY_FIXED_AND_TESTED / …) | **388** |
| VERIFIED-CORRECT / NOT-APPLICABLE / IMPLEMENTED(±TESTED) | 266 |
| STALE_OR_SUPERSEDED / SUPERSEDED-BY-EVIDENCE / DUPLICATE | 86 |
| INFRA-LANDED / USED_BY_EXECUTION / VERIFIED / TESTED / REJECTED | 15 |
| **TRULY OPEN (CLASSIFIED / PARTIAL / OBSERVED / BLOCKED / ROOT-CAUSED-PARTIAL)** | **70** |

So: **47.0% of every registered problem is root-caused-fixed; 91.5% is resolved-or-honest-closed; the live frontier is 70 rows.**

## 2. THE COMMON ROOT — CONFIRMED, QUANTIFIED

The user's hypothesis («شاید همشون ریشه مشترک دارن») is **TRUE, and it has happened repeatedly at three scales**:

**Scale 1 — per-APK cascade:** every batch-20 crash family collapsed to ONE root each time:
- 145 uncaught exceptions across 10 APKs (solitaire 35, andstatus2048 27, deskclock 23, etar 37, …) → **one** root: F-NEW-509 (prefs-guard matched receivers by class-name substring → NULL prefs → each app's own PreferenceManager NPE-cascade). One fix → 20/20 zero uncaught.
- "androidx.startup discovers ZERO initializers in EVERY androidx-startup app" → **one** root: F-NEW-510 (keySet wrapper iteration read the shadow's empty parallel state).
- PackageManager getDeclaredConstructor NPE cascade → **one** root: F-NEW-511a (Class.forName aliased the instruction counter as a heap oid).

**Scale 2 — per-title families:** the blank-render L0 family (klondike/tripeaks-class) was one root (F-NEW-167, FIXED — tripeaks now crosses at `e2a290ab98762eea` ×3); the appcompat decor-toolbar family was one root (F-NEW-170, FIXED).

**Scale 3 — the live frontier itself:** of the 70 open rows, the biggest cluster (25 rows) is the **Compose content/draw chain** — and those 25 are NOT 25 independent problems: they are decoded faces of ONE pipeline (composition → measure → draw-block chain → canvas bridge), anchored at F-NEW-265 (first divergence) with F-NEW-473/477/478/479/480/481 as consecutive links of the same draw-walk and F-NEW-277/288/378/381 as the frame-clock/value-class/control-flow/throughput faces. That is the common root of the modern corpus: **the last mile from a materialized compose tree to real canvas ops**.

## 3. Per-problem table (all 70 open rows, grouped)


### A. The Compose content/draw chain — ONE pipeline, many faces — 25 rows

dooz (Compose 1.11.4 + navigation 2.9.8) is the reference consumer; compose_stopwatch (1.11.3) + fossify_math (1.9.2) are the independent ones. Every row below is a decoded face of the SAME pipeline: composition → measure/layout → draw-block chain → AndroidCanvas bridge → framebuffer. Progress this lineage: F-NEW-259/259b (iterator/addAll) → F-NEW-264 (exception integrity) → F-NEW-265 re-root → destination LayoutNodes MATERIALIZED (tree 1→5+); the frontier is now strictly the draw/measure decoding (472/473/477–481/378) + the throughput wall (381).

| root | status | what it is |
|---|---|---|
| F-NEW-262 | ROOT-CAUSED-FIXED (manifestation 1) / SUPERSEDED (2) / BLOCKED (3) | Framework/API-bridge RETURN VALUE lost across specific shadow->DEX dispatch shapes — three independent manifestations at the same root family, all run… |
| F-NEW-264d | TESTED | COLLECTION SEMANTIC-LAW AUDIT (directive sec 8): plain-Java probe (fixtures/fcol_audit_probe, real toolchain, apk d607406c23fb205b) exercises 15 colle… |
| F-NEW-265 | CLASSIFIED | DOOZ FIRST DIVERGENCE RE-ROOTED (supersedes the W6 'canvas bridge never constructed' reading as a downstream consequence): the compose DRAW machinery … |
| F-NEW-267 | ROOT-CAUSED-PARTIAL | COMPOSE TAP HIT-TEST GAP (CONT-61 update): three stacked legs decoded at the dooz v23 tap (820,1837) on the New game button. LEG 1 FIXED: the TouchDis… |
| F-NEW-267-LEVER1 | ROOT-CAUSED-PARTIAL | F-NEW-267 FIX LEVER ATTEMPT #1 (CONT-65): the composition-time measure-ordering law — Lzs0;.s (setRootConstraints) marks the delegate constraints-init… |
| F-NEW-277 | CLASSIFIED | RECOMPOSITION STARVATION AT THE FRAME-PUMP QUIESCENCE BOUNDARY (dooz F6 content frontier, CONT-23): the Compose Recomposer runner's withFrameNanos awa… |
| F-NEW-288 | CLASSIFIED | TEXT-MEASUREMENT VALUE-CLASS (TextUnit) PACKED-VALUE SPIN: after F-NEW-286/287 the oracle's frame-1 composition advances past the deleted-content face… |
| F-NEW-314 | CLASSIFIED | Dooz v23 F084 "stall" judged — NOT a stall: boot composition is budget-bound, not defect-bound. Measured A/B on the same binary: 15 s = 4.7M instrs, w… |
| F-NEW-316 | CLASSIFIED | Compose ImageVector icon paths render EMPTY on the 120s dooz face: 1721/1721 PATH ops have zero contours (op trace), so no vector icon pixel ever land… |
| F-NEW-317 | CLASSIFIED | One solid-black 24dp-icon-bounding RECT per icon slot on the dooz 120s face (4 slots: two top-bar actions, bottom-left circle button, bottom-right pil… |
| F-NEW-343 | ROOT-CAUSED-PARTIAL | The compose text pipeline's SpannableString source never reached StaticLayout: compose wraps its text in Landroid/text/SpannableString; before StaticL… |
| F-NEW-362 | ROOT-CAUSED-PARTIAL | DIGIT-INPUT CHAIN DECODE (CONT-66, the 'in-app calculator typing' lane): the tap pipeline is LIVE end-to-end through 5 verified hops — --tap hit-test … |
| F-NEW-368 | PARTIAL | Deferred synthesized exceptions do not deliver to the SAME-FRAME catch — LAWS IMPLEMENTED (CONT-71, env-gated MINIANDROID_F368_LAW): the subtype-table… |
| F-NEW-370 | PARTIAL | CoordinatorLayout.onMeasure DEX-COMPLETION measure chain — LAWS IMPLEMENTED (CONT-71, env-gated MINIANDROID_MCM_LAW) after full first-divergence decod… |
| F-NEW-374 | CLASSIFIED | PER-CONTAINER DEX-MEASURE TRUST LAW (CONT-71 named lever): the F-NEW-368 delivery + the F-NEW-370 measure laws (negotiation measureChildWithMargins + … |
| F-NEW-378 | CLASSIFIED | FLOW-ABORT CONTROL FLOW DECODED THROUGH THE MEASURE PASS (dooz current first divergence, CONT-76 decode-complete; supersedes the CONT-75 'cancellation… |
| F-NEW-381 | CLASSIFIED | INTERPRETER THROUGHPUT WALL: the dooz first content composition is ~10-12M interpreted instructions while the engine sustains ~310K ins/s (linear PROG… |
| F-NEW-472 | CLASSIFIED | F-NEW-472 — dooz place-then-reset poison: placement recompute reads kotlin EmptyMap default; state-map publish path never executes |
| F-NEW-473 | PARTIAL | F-NEW-473 — dooz blank-face draw-walk gate: root-layer flag never marked -> compose AndroidCanvas bridge (Ljt1;) never constructed -> 0 canvas primiti… |
| F-NEW-477 | CLASSIFIED | F-NEW-477 — dooz content-draw terminal: T0(4) registry query NULL 12/12 -> Lpz0;.M0 skips content step; Lqz0; insert(hash-keys 65x) vs query(key 4) ke… |
| F-NEW-478 | CLASSIFIED | F-NEW-478 — Lwt0; draw-block chain law: T0(4) g-bit-test FALSE + chain walk returns candidates whose kind-ints never match kind 4 -> NULL -> content s… |
| F-NEW-479 | CLASSIFIED | F-NEW-479 — draw-block chain re-termination at bind: Lel0;.c padChain deliberately re-terminates the obj#2708 chain (pc400 v7=0 law, head re-point pc4… |
| F-NEW-480 | CLASSIFIED | F-NEW-480 — kind-4 provenance SOLVED: M0 pc0 hard-coded const #4 -> T0; acceptance (h&kind)&&(g&kind) verified; T0-null -> h1 overlay fallthrough; nex… |
| F-NEW-481 | PARTIAL | F-NEW-481 — dooz-family draw frontier: the compose lambda-replay leg never executes; root-chain kind-4 walk over the frozen early chain is the only dr… |
| F-NEW-491 | CLASSIFIED | F-NEW-491 — readrops: Koin loadModules vararg-null — Intrinsics$Kotlin.toArray casts null to Array<Any?> from DiskLruCache$$ExternalSyntheticLambda0 -… |

### B. App-framework faces (per-app decode rows) — 10 rows

each is a named generic law waiting for its wave; none is app-keyed work — they are the next base-strengthening candidates in priority order.

| root | status | what it is |
|---|---|---|
| F-NEW-166 | PARTIAL | WhatsApp_next_face (F-NEW-156 family): onCreate dies BEFORE any setContentView — NPE 'INVOKE_RETURN must not be null' at LX/00i;.A0F pc=19 (obfuscated… |
| F-NEW-168 | PARTIAL | WhatsApp next faces (F-NEW-156 chain continues): (a) androidx FragmentManager host law — 'FragmentManager has not been attached to a host' ISE at LX/0… |
| F-NEW-197 | PARTIAL | V10 five-app gate white/black frontier (fresh census attribution): Dame (blidraughts), Droidify, OpenCalculator all reach auth_root_valid + measure + … |
| F-NEW-483 | CLASSIFIED | F-NEW-483 — AppCompat theme-gate false-negative family (3/17 WINDOW_ROOT apps): createSubDecor hasValue(windowActionBar-slot)=false because the materi… |
| F-NEW-485 | CLASSIFIED | F-NEW-485 — ch.bailu.aat kills its own view build: WindowManager.getCurrentWindowMetrics (API 30) has no engine shadow and answers null — Kotlin check… |
| F-NEW-490 | CLASSIFIED | F-NEW-490 — goodtime: Constructor.newInstance silent-null family — the Constructor shadow answers null when the token identity fields are missing, and… |
| F-NEW-492 | CLASSIFIED | F-NEW-492 — fdroid privileged extension: attach dispatch ok=false with classes_indexed=23 — launcher onCreate never dispatched (A-type variant) |
| F-NEW-493 | CLASSIFIED | F-NEW-493 — shizuwall: Shizuku SystemServiceHelper.getSystemService -> Method.invoke on null (binder transport absent) — app-side IPC boundary; plus t… |
| F-NEW-499 | CLASSIFIED | F-NEW-499 — activity-RELAUNCH theme rebind gap (CLASSIFIED): secuso memory's own restart flow startActivity(MainActivity) inside the F-NEW-497 drain r… |
| R-NEW-331 | PARTIAL | R-NEW-331: S27 (cross-app, honest-open): the Fragment host wiring family. STTT (nl.hnogame.tictactoesuperttt_20): FragmentManager 'not been attached t… |

### C. Native/GL/Flutter boundary — 3 rows

the honest external-engine boundary: Flutter needs libflutter.so (native Dart VM); libGDX needs the GL/native path (F-NEW-387/388/389 family landed for tower3d; F-NEW-498 tracks tictactoe libgdx.so).

| root | status | what it is |
|---|---|---|
| F-NEW-162 | PARTIAL | C013-CUSTOMVIEW inline placeholder contaminates visible frames and can stand in for unimplemented renderer families: (a) headingcalc_1 — pink "custom … |
| F-NEW-489 | CLASSIFIED | F-NEW-489 — ricochlime: Flutter app — FlutterEngine/LuaLoader init requires the native Dart VM (libflutter.so) — app-side native runtime boundary beyo… |
| F-NEW-498 | CLASSIFIED | F-NEW-498 — tictactoe libGDX GL/native boundary (CLASSIFIED, not engine-fixed): GATEA-NATIVE libgdx.so extracted (260696B, sha16 553c8769776ff741) but… |

### D. Audit/corpus mechanics (R-NEW residue) — 23 rows

trace/corpus availability rows — each re-opens automatically when its artifact or trace is re-supplied; no engine work hidden behind them.

| root | status | what it is |
|---|---|---|
| R-NEW-040 | CLASSIFIED | R-NEW-040: no trace (RESEARCHED, audit M-family) |
| R-NEW-062 | PARTIAL | R-NEW-062: partial via 061 |
| R-NEW-079 | PARTIAL | R-NEW-079: corpus |
| R-NEW-080 | PARTIAL | R-NEW-080: corpus |
| R-NEW-083 | CLASSIFIED | R-NEW-083: no signature verification law |
| R-NEW-084 | CLASSIFIED | R-NEW-084: no scheme matrix |
| R-NEW-140 | BLOCKED | R-NEW-140: no resource-shrunk trace |
| R-NEW-151 | CLASSIFIED | R-NEW-151: no FileProvider trace |
| R-NEW-161 | CLASSIFIED | R-NEW-161: no /proc passthrough |
| R-NEW-196 | PARTIAL | R-NEW-196: partial via fixtures |
| R-NEW-200 | PARTIAL | R-NEW-200: partial |
| R-NEW-206 | PARTIAL | R-NEW-206: canvas_shadow.cpp |
| R-NEW-216 | PARTIAL | R-NEW-216: paint flags partial |
| R-NEW-246 | PARTIAL | (title backfilled CONT-17) R-NEW-246 — live re-verified at HEAD, see evidence |
| R-NEW-247 | CLASSIFIED | R-NEW-247: no RecyclerView corpus demand |
| R-NEW-253 | PARTIAL | R-NEW-253: partial |
| R-NEW-256 | PARTIAL | R-NEW-256: composition constructs deep into Material3 (1.13M trace lines, M13); state→tree law partial |
| R-NEW-279 | PARTIAL | (title backfilled CONT-17) R-NEW-279 — live re-verified at HEAD, see evidence |
| R-NEW-281 | CLASSIFIED | R-NEW-281: Known gap (M9-B analysis) |
| R-NEW-285 | PARTIAL | (title backfilled CONT-17) R-NEW-285 — live re-verified at HEAD, see evidence |
| R-NEW-340 | PARTIAL | R-NEW-340: S39 OBSERVED (dooz23 runs r339f/r340): (a) F-050 launch frame pump ran at log:242402 with pending_cb=0 -> quiescence at tick=0; (b) the Rec… |
| R-NEW-441 | PARTIAL | SlidingUpPanelLayout runtime-state family: View.getLeft/getTop/getRight/getBottom had NO bridge (umano dimChildToDimen cover test read degenerate boun… |
| R-NEW-456 | BLOCKED | LIVE z.ai residual: the Svelte-5 runtime inside the minified app bundle rejects the boot ('TypeError: value is not iterable', twice, unhandled) at bun… |

### E. Residual/mixed rows — 9 rows

small honest-open rows; each names its own next decode.

| root | status | what it is |
|---|---|---|
| F-NEW-172 | PARTIAL | F-NEW-172 |
| F-NEW-192 | ROOT-CAUSED-PARTIAL | PHASE 10 draw/z-order audit residue: AOSP View.draw order (drawBackground -> onDraw -> dispatchDraw -> decorations) is enforced in the frame walk (21-… |
| F-NEW-204 | OBSERVED | DEEP-AUDIT P1-7 (CONT-71 census): unconditional std::cerr/std::cout noise audit — full src census at binary 86e4ebd4a2c30592: 2,616 sites total; top f… |
| F-NEW-206 | PARTIAL | DEEP-AUDIT P1-9: cross-check the traversal order against AOSP ViewRootImpl — attach -> measure -> layout -> pre-draw/state checks -> draw -> capture; … |
| F-NEW-217 | CLASSIFIED | kotlinx-coroutines virtual-concurrency frontier: MutexImpl.unlock F084 spin (50,001 visits, bytecode_size=66) with owner$volatile=NO_OWNER + _availabl… |
| F-NEW-221 | OBSERVED | R8-MERGED CLASS CONSTRUCTOR/DISPATCH MISMATCH: LA/h; is a horizontal class merge (field `a` mode int + packed-switch ctor paths: SparseIntArray pair /… |
| F-NEW-229 | OBSERVED | CL MATCH_PARENT SPEC LAW: a ConstraintLayout child with width/height=MATCH_PARENT and NO anchors on that axis falls back to child_spec → AT_MOST(avail… |
| F-NEW-250 | CLASSIFIED | kotlinx.serialization reflective serializer chain (serializerOrNull -> Companion/INSTANCE reflection -> @Serializable(with=) element dispatch -> KClas… |
| F-NEW-508 | CLASSIFIED | F-NEW-508 (CONT-159 tower3d decode wave: honest frontier) |

## 4. Steps already executed this session (W9)

1. **Context resync**: local tree was 307 commits stale; fast-forwarded to `276f7628`; registry re-read (566→825).
2. **Full sweep scripts** (`scripts/cont11_full_sweep.py`, `cont11_w9_review.py`): status census, open-row extraction, family clustering — outputs committed.
3. **Per-issue comments posted** (the directive's «کامنت بکن» duty): #227 F-NEW-156 ALREADY_FIXED_AND_TESTED; #228 F-NEW-157 SUPERSEDED; #230 F-NEW-161 SUPERSEDED (solved via F-NEW-363); #231 F-NEW-162 partial-progress; #343 F-NEW-166 partial (artifact-bound); #344 F-NEW-167 **ROOT-CAUSED-FIXED**; #346 F-NEW-169 NOT-APPLICABLE (corrupt artifact); #348 F-NEW-170 **ROOT-CAUSED-FIXED**.
4. **W9 development frontier confirmed** (inherited from W8, unchanged): F-NEW-511b + chess `Toolbar.setSubtitle`→x0 decode + getColorStateList family — container reset lost the binary, rebuild queued as the wave's first act.

## 5. W9 next steps (the named queue)

| # | Step | Why |
|---|---|---|
| 1 | Rebuild engine from source; reproduce `060fdbefd3e9f9d2` lineage byte-identically | container reset (established pattern) |
| 2 | Land **F-NEW-511b** (singletonList container materialization) TOGETHER with the chess Toolbar/x0 decode | the W8 A/B proved 511b alone flips chess; the pair is the coupled fix |
| 3 | getColorStateList family (survivalmanual FAB + alexcalc Toolbar share the signature) | the Resources family behind the batch-20 content gates |
| 4 | Batch 3 of 20 (fresh LAW-001-clean APKs) | the ۲۰-تا-۲۰ directive continues |
| 5 | Then the Compose draw chain (F-NEW-473 → 477..481 decode order) | the common root of the biggest open family |

*Honesty notes: all counts from `root_registry.json` at `276f7628`; no root re-classified without evidence; the 70 open rows are the honest set — nothing hidden, nothing inflated.*