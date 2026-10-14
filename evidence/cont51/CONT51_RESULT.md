# CONT-51 RESULT — solitaire past the onCreate wall: two generic identity laws (F-NEW-322, F-NEW-323)

Binary: `f11d542108cd611b` (HEAD `533ecf61` = origin/main at wave start; two
coordinated generic laws on top of the byte-exact CONT-50 rebuild). No
APK-specific hacks, no fake objects, no forced lifecycle transitions. Probe
FIRST on both laws (PRE faces deterministic ×3 before any engine edit).

## Phase 0 — reconciliation per directive (latest remote HEAD, not a stale snapshot)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | local container was the pre-CONT-28 snapshot `e99c2fbd` AGAIN (the CONT-50 commit message predicted exactly this); `git fetch` + `reset --hard origin/main` → HEAD `533ecf61` (90 commits pulled: CONT-42..CONT-50 closeouts, BMI past the white screen, Dooz past the white screen, solitaire two waves) | git log |
| TESTED | binary REBUILT from HEAD == `d19d5ba63c47a19f` (byte-exact CONT-50 record — build reproducibility held); solitaire original bytes `fdfaf7cad18e4416` (the CONT-46 pin) reproduce the recorded face on this binary | sha256sum |
| TESTED | solitaire baseline face reproduced: `ay$w.q` null-recv NPE at `ay$h.a pc=8` ×5/run, `[EXC-PROPAGATE] NPE uncaught at GameSelector.onCreate invoke_pc=120 → APP BOUNDARY unwind`, verdict DEFAULT_BACKGROUND_ONLY, screenshot `ba50a4d28ea62fe7` | run/cont51/sol_r0 |

## Phase 1 — the decode: one identity split, then a family of no-op bridges

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED (static) | `ay.e(View)` = AOSP `getChildViewHolderInt` verbatim (`if (child==null) return null; return ((ay$i) child.getLayoutParams()).c`); `ay$h.a(View,I,Z)` = `LayoutManager.measureChildWithMargins` (pc=2 `ay.e`, pc=8 `holder.q()`); `ay$5.c(I)` = the ChildHelper.Callback detach with the DEX-side `isTmpDetached` defense (`throw IAE("called detach on an already detached child " + vh)` before `addFlags(256)`); `ay$i` extends MarginLayoutParams = RecyclerView.LayoutParams, field `c` = mViewHolder | scripts/cont46_disasm.py runs |
| TESTED (runtime — F-NEW-322 root) | FIELD-TRACE `ay$i.c` shows FIVE put/get pairs: put obj#1802 value=obj#1794 (caller `ay$o;.a` = tryGetViewHolderForPositionByDeadline) vs get obj#1805 (caller `ay;.e`) — the WRITE and the READ landed on DIFFERENT heap objects; the identity split is at the getLayoutParams bridge | run/cont51/sol_ft2.err |
| TESTED (engine) | `getLayoutParams` bridge answers `lp_node->layout_params_object` when set (F-NEW-309 precedence) else allocates a FRESH parent-type LP on EVERY call (silent — the ROOT-055 log line only prints for CoordinatorLayout receivers); the `setLayoutParams` bridge recorded only semantic w/h, never the object identity | android_shadows.cpp:7255..7377 |
| TESTED (runtime — F-NEW-323 root) | after F-NEW-322 the next divergence surfaced at the SAME caller: IAE `"called detach on an already detached child c$a;@1787"` at `ay$5.c pc=45`; FIELD-TRACE `ay$w.n` obj#1787: `1 → 257` (the FIRST detach's `b(256)` FLAG_TMP_DETACHED write) and the second detach's `r()` (isTmpDetached) reading 257 → throw; THROWABLE-STACK #0 `ay$5.c` #1 `ah.e(I)` (ChildHelper.detachViewFromParent) #2 `ay$h.a(I,View)` (LayoutManager.detachViewAt) #6 `LinearLayoutManager.c` #7 `ay.N` #8 `ay.onMeasure` | run/cont51/sol_post/r1.err; run/cont51/sol_ftn.err |
| TESTED (engine) | grep `detachView` in the engine = ZERO hits — the whole ViewGroup detach/attach family (detachViewFromParent, attachViewToParent, removeDetachedView) was a silent no-op; DEX census (androguard + scoped scan) confirms exactly two call sites drive it from real DEX: `ay.detachViewFromParent(I)` and `ay.attachViewToParent(V,I,LP)` | scripts/cont51_detach_census.py |

## Phase 2 — probe FIRST (fixtures/fnew322_probe, fnew323_probe — real aapt2/ECJ/D8)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | fnew322 probe APK `56de7a4ef25cf4f9`: DEX `LpTag extends MarginLayoutParams` carrying a String field written BEFORE `setLayoutParams`; PRE ×3 deterministic: P1-LP-IDENTITY FAIL (`back=LayoutParams/<no-tag>/100x200` — a FRESH plain LP, the exact obj#1805 face), P2-LP-OVERWRITE FAIL; N1/N2/N3 (ROOT-055 fallback + w/h semantic) PASS | run/cont51/f322_pre/r1..r3 |
| TESTED | fnew323 probe APK `634ebf19d04ab00d`: DEX `Detacher extends LinearLayout` exposing detachIdx/attachIdx/removeDet; PRE ×3 deterministic: P1-DETACH-COUNT FAIL (`count=2` after detach(0) — the children-table-stays-full face), P2 slot FAIL, P5-ATTACH-LP-IDENTITY FAIL, N1-REMOVEDETACHED FAIL; P3/P4 PASS only vacuously (both calls no-op) | run/cont51/f323_pre/r1..r3 |

## Phase 3 — the fixes (minimal, generic, evidence-backed)

| Law | Change | Scope guard |
|-----|--------|-------------|
| F-NEW-322 | the `setLayoutParams` bridge records the EXACT object identity + heap class into the SAME node slot `getLayoutParams` already answers first (`layout_params_object`/`layout_params_class`); AOSP View.java stores ONE mLayoutParams reference — set writes it, get reads the same object, a later set replaces it. Views never given params keep the ROOT-055 fallback; XML-inflated F-NEW-309 objects keep their precedence | android_shadows.cpp:7346..7373; no reader/writer semantics changed elsewhere |
| F-NEW-323 | three bridges: `detachViewFromParent` compacts `n->children` (idx from int arg or indexOf(object arg)) WITHOUT clearing child parent_id (AOSP detach keeps mParent — transient state); `attachViewToParent` re-inserts (clamped index, index<0 → append, no double-add, parent_id kept) and records the params object into the child's layout_params_object slot (F-NEW-322 cooperation — AOSP attachViewToParent sets child.mLayoutParams = params); `removeDetachedView` delegates to remove_child (full removal + R-NEW-302 requestLayout) | android_shadows.cpp:5862..5951; no other bridge touched |

## Phase 4 — POST verification (final binary `f11d542108cd611b`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **fnew322 probe 5/0 ×3** (P1 identity, P2 overwrite, N1 no-set fallback, N2 w/h round-trip, N3 no-set semantic — all PASS) | run/cont51/f322_post/r1..r3 |
| TESTED | **fnew323 probe 6/0 ×3** (P1 detach-count, P2 slot compaction, P3 parent kept, P4 attach round-trip, P5 attach LP identity, N1 removeDetached full removal — all PASS) | run/cont51/f323_post/r1..r3 |
| TESTED | solitaire ×3 on the fix binary: **ay$w.q NPE 0** (was 5/run), **detach-IAE 0**, **0 uncaught ×3** (only the two historical benign deferreds remain); **GameSelector.onCreate SURVIVES** (was: APP BOUNDARY unwind at invoke_pc=120) and **GameSelector.onResume dispatches via DEX `ok=1` (22361 insns) ×3** | run/cont51/sol_post2/r1..r3 |
| TESTED | NavigationMenuView.onMeasure now measures with REAL specs (`0x40000000`/`0x40000780`) and **writes back 0x1920** (was: spec=0 FAILED no write-back); NavigationView.onMeasure first pass gets real specs too | run/cont51/sol_post2/r1.err |
| TESTED | zero-drift regression gate on the FINAL binary: **11/11 canonical anchors ×3 byte-identical** (dooz `31ddd4d5b8e6d18e` / micro `da73010a` / unote `4f1a9e4e` / gmdice `f3b483fe` / opencalc `a976d2f9` / tttdeluxe `af609429` / flappycow `13cf4746` / g2048 `59ca1526` / tanana `5f7e0114c3bfd6b5` / csw `3442d9a9dc0fa0f9` / simplecalc `e847ca0346708f07`) | run/cont51/gate/gate.log + cont37_full.log |
| TESTED | probe battery == records exactly (fcol 140/0, f259 49/0, f259g 84/7 known, f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, ckey 105/0, cpipe 119/0, fnew302 48/24 known, fnew252 56/0, fnew290..297 56/56/70/56/77/49/42/42, fnew298 19/0 KEEP=5 corner=PASS) plus **fnew309 8/0 ×3** (rebuilt `dd1c2d239da37c7c`), **fnew320 7/0 ×3** (rebuilt `2cfc3d768dd7dce5`) | run/cont51/gate/ |
| TESTED | support group ×3 byte-identical to the CONT-46/47 records on ONE binary: **BMI `b52252c2de19b03a`** (REAL_APP_CONTENT held), **alex `c8d69f811b23f245`**, **notes `eb5ebd559cad1028`** | run/cont51/gate/ |
| TESTED | gate APKs lost to the container reset were REFETCHED SHA-exact (tananaev_11 `294a68bd00debbdc`, simplecalc_8 `68da25fd9fdf54b4`, composeStopwatch `dbf937ebbe7c0b3d`) — the recovery class CONT-43/46/49 performed | scripts/cont46_refetch_apks.sh runs |

## Cross-app impact + honest bounds

One binary carries two generic identity laws; the whole canonical corpus is
byte-identical ×3 — the laws touch exactly the `setLayoutParams`/
`getLayoutParams` identity surface (every view that programmatically swaps
params) and the detach/attach family (RecyclerView/ChildHelper consumers;
both bridge-shaped, zero app conditions). BMI's REAL_APP_CONTENT face held
through both; dooz's white anchor `31ddd4d5` held (Dooz passed the white
screen in CONT-48 by measurement and its anchor is the recorded face).
Honest bounds: (1) solitaire's screenshot face is UNCHANGED `ba50a4d2` ×3 —
the MACHINE moved from "onCreate dies at invoke_pc=120" to "onResume
dispatches with the menu machinery measured at real specs" (two divergence
layers + the app-lifecycle wall), but the frame is still
DEFAULT_BACKGROUND_ONLY / first_missing_stage=APP_PIXELS; (2) the NEW first
divergence is the menu-content render pipeline itself (NavigationMenuView's
second measure pass runs at spec=0; the menu items never paint app-owned
pixels) — recorded in the F-NEW-309 row for the next wave, NOT fixed this
wave (no fix without its own decode cycle); (3) NavigationView.onMeasure
"no write-back" persists on some passes and is part of the same decode.

**Registry 632→634** (F-NEW-322, F-NEW-323 appended ROOT-CAUSED-FIXED;
F-NEW-309 next_wave refreshed). Evidence: `evidence/cont51/CONT51_RESULT.md`.
