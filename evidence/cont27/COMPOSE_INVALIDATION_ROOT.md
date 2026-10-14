# CONT-27 / TRACK A — INTERFACE DISPATCH EXACT-NAME LAW + THE DRAW-PIPELINE FRONTIER

Wave: CONT-27 (continuation of CONT-26's dual-track directive). Track A resumes
the real-Compose oracle at the divergence CONT-26 recorded as "the next wave's
opening target": the HostDefaultProvider computed-default chain whose lambda
tail never executed.

**VERDICT UP FRONT (no success inflation):** NO real app-owned Compose pixels
are claimed this wave. The concrete advances: (1) the oracle's composition-
local machinery is UNBLOCKED — three new generic laws landed (F-NEW-281 with
its three arms, F-NEW-282, F-NEW-282b), the NavHost ViewModelStoreOwner ISE is
GONE, the ViewModelStoreOwner resolves through the view-tree tag, the
NavControllerViewModel initializer factory matches, and the composition now
runs LaunchedEffect/produceState coroutines and ENTERS the real draw pipeline
(LayoutNode.draw$ui → AndroidComposeView.dispatchDraw → GraphicsLayer
machinery); (2) the next root is precisely named with name+bytecode-level
evidence (GraphicsLayer created without executing its <init>). dooz itself is
untouched and byte-anchored (its delivery link stays PARTIAL at link 2).

---

## 0. TRUTH LOCK (Phase 0)

| item | value |
|---|---|
| git HEAD (start) | `da92a9f68b83138789f9924037712a01f5433709` == origin/main (fetched; local fast-forwarded) |
| baseline binary rebuilt | BYTE-EXACT `1ff06737f7b12ad4cf469082c603b594e2045fc3442316aa1558dfb164201900` (the CONT-26 final) |
| dooz APK | sha256 `299eab21ac8b3c61...` == registry |
| Simple Calculator APK | re-downloaded from the reachable F-Droid archive: vc8 sha256 `68da25fd9fdf54b4...` == CONT-26 record (vc7/vc6 also captured) |
| oracle APK | REBUILT from surviving artifacts (`scripts/cont12_oracle_res2.sh` + `cont12_build_oracle.sh`): 8,233,173 bytes **size-exact**, sha16 `3359ed00e3add03d` (non-byte-identical across rebuilds — recorded honestly in CONT-26; identity = size + id-table + behavior parity: the recorded ISE reproduces at the recorded pc) |
| Issues read | #383 (3 comments), #384 (5 comments — no new directive beyond CONT-26's), #385 (0) via API (not rate-limited this session) |
| root registry at lock | 589 rows; F-NEW-277 CLASSIFIED; F-NEW-278/279/280 present with fix evidence |

## 1. A1 — THE ORACLE BASELINE AT HEAD (reproduction)

The recorded divergence reproduces exactly: ISE "NavHost requires a
ViewModelStoreOwner to be provided via LocalViewModelStoreOwner" at
`NavHostKt.NavHost pc=1780`, plus a second-order escape (LookaheadCapable-
Placeable$layout$1.placeChildren f141-null-recv NPE) after the first unwind.

## 2. F-NEW-281 — THE INTERFACE DISPATCH LAW (three arms)

**Decode (real names, oracle classes.dex/classes2.dex; disassembler
`scripts/cont27_disasm.py` — a bounds-tolerant fork of cont26's):**

```
lambda$0 (17 units, exact bytecode per CONT-26):
  @0x0006 invoke-interface {v2,v0}, CompositionLocalAccessorScope.getCurrentValue
  @0x0009 move-result-object v2
  @0x000a check-cast v2, HostDefaultProvider        ← NEVER EXECUTED
  @0x000c invoke-interface {v2,v1}, HostDefaultProvider.getHostDefault
```

Method trace: the lambda enters, the nested `getCurrentValue` dispatch runs
the RAW map walk (PersistentHashMap.get → TrieNode.get → valueAtKeyIndex),
prints INTERFACE-SIG, and the lambda frame is gone — control back in NavHost.

**Root:** the engine's F-091b descriptor-only walk matched by DESCRIPTOR ONLY
and picked the FIRST same-shape method — the 7-unit `get` override
(`invoke-super PersistentHashMap.get + check-cast ValueHolder + return`).
ART/JVMS 5.4.3.4: an invoke-interface candidate must match the (NAME,
descriptor) pair. The true implementation is the inherited interface DEFAULT
`PersistentCompositionLocalMap.getCurrentValue` (5 units: `read(this)`).

**Fix (dalvik_engine.cpp only, zero app knowledge):**
1. **F-NEW-281 exact arms** inside the f91b block: (a) exact (name, proto)
   walk over the receiver's class chain; (b) exact (name, proto) DEFAULT
   bodies in the interface hierarchy (BFS via class_to_interfaces_, bounded
   16); (c) the legacy descriptor-only walk unchanged as the R8 fallback.
2. **F-NEW-281b token-referent law** in the Class-bridge receiver resolution:
   a heap `Ljava/lang/Class;` token receiver resolves to its
   `__referent_desc` (read-only) — the bridge was querying java.lang.Class
   itself for token receivers (face: `No @Navigator.Name annotation found
   for Class`).
3. **F-NEW-281c strict gate** on the F-068 runtime-class-first arm: with a
   concrete call-site proto, the arm only fires when the runtime class chain
   declares an EXACT (name, proto) non-abstract method — otherwise control
   reaches the declared-interface / interface-default search (live face:
   `Factory.create(KClass, extras)` was dispatched into
   `InitializerViewModelFactory.create(Class, extras)`, re-wrapping the KClass
   via getKotlinClass and killing the initializer match).

**Runtime proof:** the ISE is GONE; `[F281-IFACE-DEFAULT]
PersistentCompositionLocalMap.getCurrentValue ... → REAL DEX dispatched`; the
ViewModelStoreOwner resolves via the view-tree tag
(view_tree_view_model_store_owner=2131034206); NavControllerViewModel's
factory matches; the run advances into compose coroutine machinery and
`LayoutNode.draw$ui` / `AndroidComposeView.dispatchDraw` (205 GraphicsLayer
rows).

## 3. F-NEW-282 — CLASS_REF TOKEN MATERIALIZATION (frame boundary + store)

En route, the ViewModelProvider face exposed a second root: MINIANDROID_PARAM_
TRACE proved `ClassReference.<init>` received `p1={t=CLASS_REF}` at frame
entry while its `iput-object v2, v1, jClass` stored `<unset>` (FIELD-TRACE) —
raw CLASS_REF register values do not survive the frame machinery across
nested DEX calls. Every consumer (getJClass/equals/isInstance/getQualifiedName)
then saw null and the initializer match failed (`No initializer set for given
class null`).

**Fix:** `execute_method_internal` materializes CLASS_REF args to their
heap-backed token OBJECT_REF (F-069 identity map, `__referent_desc` recorded)
before write_p; `execute_iput_object` materializes CLASS_REF sources on the
store side. Post-fix PARAM-TRACE/FIELD-TRACE: two ClassReference objects carry
the SAME token obj#3970 (stable per descriptor) and the initializer match
succeeds. MINIANDROID_F282_TRACE env-gated, bounded 24.

## 4. THE NEXT ROOT — RECORDED, NOT FIXED

After the ViewModel layer, the oracle's first APP BOUNDARY escape sits INSIDE
the draw pipeline: `GraphicsLayer.setPosition` on a NULL `GraphicsLayerImpl`
(f141-null-recv) — `LayoutNode.draw$ui` catches, `rethrowWithComposeStackTrace`
rethrows → APP BOUNDARY. Ground truth: `AndroidGraphicsContext.createGraphics-
Layer` (109 units; SDK>=29 → `new GraphicsLayerV29`) NEVER ENTERED per the
method trace, yet a GraphicsLayer object exists with a null impl field — the
**ctor-skip family** (the same family F-NEW-283 fixed on the inflate side).
This is the named opening target for the next wave, now with the draw pipeline
reached and the name-level instrument fully functional.

## 5. STATUS LEDGER

| item | status |
|---|---|
| Phase-0 truth lock (HEAD/binary/APKs/oracle/issues/registry) | TESTED |
| Oracle baseline divergence reproduced at HEAD | TESTED |
| F-NEW-281 (+281b/281c) root-caused + fixed | IMPLEMENTED+TESTED |
| F-NEW-282 root-caused + fixed | IMPLEMENTED+TESTED |
| ViewModelStoreOwner / ViewModel creation unblocked | TESTED (name-level) |
| Real draw pipeline entered (LayoutNode.draw$ui/dispatchDraw) | OBSERVED |
| GraphicsLayer ctor-skip root fixed | NOT ACHIEVED (recorded, next wave) |
| Real app-owned Compose pixels | NOT ACHIEVED (no claim) |
| dooz delivery link | PARTIAL — unchanged, byte-anchored (F-277 post-fix state) |
| Full regression at final binary | TESTED (REGRESSION_MATRIX.md) |
