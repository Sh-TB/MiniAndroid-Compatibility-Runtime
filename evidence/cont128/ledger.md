# CONT-124..128 Ledger — «۵ تا قطار هر قطار کلی واگن، تغییرات اسری روی دوز تلگرام و غیره»

**۵ قطار (5 trains), all SOURCE-level, every train zero-drift-walled and pushed.**

Base at wave start: HEAD `d6484d1d`, binary `04a89c52`, registry 783.
Final: HEAD `0d6dbe1c`, binary `25578933`, registry **786**, all trains HEAD==origin/main verified after push.

## Train 1 — CONT-124 (`be350cee`) — F-NEW-469 SUPERINTERFACE CLOSURE LAW, ROOT-CAUSED-FIXED
- **Decode (dooz v23 live)**: the aput-object store-check threw a BOGUS `ArrayStoreException` ×9 (`Lf6; cannot be stored in [Lxt0;`) at `Liw0;.b pc=16`. The exception escaped `Lr;.g`'s catch-all recovery re-throw and unwound the **LayoutNode placement pass** (`Lel0;.c/.d`) at `MainActivity.onCreate` — the deepest proven reason **zero `Placeable.position` writes landed at HEAD** (dooz = bare themed background).
- **DEX byte truth** (new tool `scripts/c124_dex_classdef.py`): `Lxt0;`/`Lvt0;`/`Lbu0;` are **interfaces** with `Lbu0; extends Lvt0; extends Lxt0;`, and `Lf6; implements Lbu0;` ⇒ **the store is JVMS-legal**. The engine walk checked only DIRECTLY declared interfaces — no iface→iface transitivity.
- **Fix**: superinterface closure BFS (DEX tables + F-NEW-236 framework tables, visited-bounded) at all three walk points. Only previously-FALSE answers can flip TRUE.
- **Verified**: ASC-REJECT 9→0, AIOOBE 27→0; **180s dooz writes REAL packed positions (`Ld61;.i0`, value 2319282340800) — the placement pass survives for the first time in the current lineage**. Honest residuals named: place-then-reset poison + draw-op frontier (anchor face `d602648e` byte-identical at 30s AND 180s — zero unadjudicated drift).
- Wall: 9/9 anchors, selftest rc=0, negatives 19/19.

## Train 2 — CONT-125 (`84a978e1`) — F-NEW-470 STALE-UNWIND CLINIT ATTRIBUTION, ROOT-CAUSED-FIXED
- 12-app fan-out sweep: F-NEW-469 passes **every** corpus store-check (aioobe=0 all); 6 faces match records; memory `807a0cca` = new dialog state recorded OBSERVED (no false fan-out claim); opmt first evidence; tictactoe SIGSEGV stays fixed.
- **Decode (tictactoe v3)**: `AndroidApplication.<clinit>` was marked ERRONEOUS by F-NEW-395 because its diag inherited the **stale in-flight** `GdxRuntimeException` (SharedLibraryLoader.load fault unwinding in an OUTER frame). JVMS 5.5: only a clinit whose OWN bytecode throws marks erroneous.
- **Fix**: entry-snapshot attribution at the clinit consumer. Verified: `[CLASS_INIT] AndroidApplication result=OK`; onResume executes its real body. Residual: the invoke-super `AndroidApplication.onCreate` gap → F-NEW-471.
- Wall: 9/9 anchors, selftest, negatives 19/19.

## Train 3 — CONT-126 (`0844430f`) — F-NEW-469 PROBE LANDED + FIELD-TRACE STATICS
- Probe `fixtures/cont124_iface_chain` (real aapt2/ECJ/D8): **4/4 PASS** — transitive-store (the law), direct-store, **negative-store (an unrelated class through an array-covariance alias STILL raises AIOOBE — the check keeps its teeth)**, chain-dispatch (id()=42).
- FIELD-TRACE now covers sget/sget-object/sput/sput-object (4 read-only hooks) — immediate payoff: `Gdx.app` put-static pinned in `AndroidApplication.onResume` (late) vs the null read in `preserveEGLContextOnPause` (early).
- Wall: 9/9 anchors, selftest, negatives 19/19.

## Train 4 — CONT-127 (`9ad8b422`) — F-NEW-471 SLICE 1: RESOLUTION-GAP LOUD LAW
- A super-call whose target exists in `method_ids` (byte truth) but has no parsed DEX body now **names the gap at the call site**: `[F-NEW-471-RES-GAP] AndroidApplication.onCreate method_id=1184 … caller=AndroidLauncher.onCreate` — fires exactly once, live-verified.
- F-NEW-471 CLASSIFIED with the full chain (method_ids byte truth vs the 52-method parsed table vs the class_data blob desync at vm[10]) + named levers (alignment-repair walker / method_ids-guided lazy recovery).
- Wall: 9/9 anchors, selftest, negatives 19/19.

## Train 5 — CONT-128 (`0d6dbe1c`) — close-out
- Worklog (4 sections), ledger, registry 783→786 id-unique main==mirror at every step (no inflation).

**Overall: 4 source-level engine laws landed + 1 probe fixture + 2 diagnostic tools + 3 registry roots; 4× zero-drift walls (9/9 anchors incl. dooz `d602648e` + telegram `20ac8cbbbb` byte-identical at every push); the dooz placement pass is UNBLOCKED with first-ever position writes in this lineage. Next train owns F-NEW-471's class_data alignment repair and the dooz place-then-reset poison law.**
