# CONT-18 LAW-C/E/F DETERMINATION + FIX (2026-10-08)

Directive: investigate LAW-C/E/F **only to definitive determination**; fix only a proven
generic root; otherwise REJECT/DEFER explicitly; then move **directly** to F-217 as the
first-divergence target.

Binary under test: HEAD `b3a5fe6b` lineage, binary sha16 `8ee839e718877216`
(prior CONT-17 binary `a8761a482a186eac` unchanged until this wave's law implementation).

## 1. Determination method

Env-gated bounded diagnostics (`MINIANDROID_LAWCEF_TRACE=1`, ≤60 lines each) at two
dispatch layers:

- `[LAWCEF-ENG]` in `try_shadow_dispatch` — which class the engine routes, with which
  receiver.
- `[LAWCEF-COL]` in `CollectionShadow::dispatch` — whether the collection shadow sees
  the call.

Artifacts: `run/cont18/lawcef_diag1..4/`, `run/cont18/probes_lawcef1..4/`.

### Live trace (before the fix)

```
[LAWCEF-ENG] Ljava/util/ArrayList;.removeIf   recv=73 cls=Ljava/util/ArrayList;
[LAWCEF-COL] Ljava/util/ArrayList;.removeIf   recv=73 rcls=Ljava/util/ArrayList; nargs=1
[LAWCEF-ENG] Ljava/util/HashMap;.getOrDefault recv=32 cls=Ljava/util/HashMap;
[LAWCEF-COL] Ljava/util/HashMap;.getOrDefault recv=32 rcls=Ljava/util/HashMap; nargs=2
[LAWCEF-ENG] Ljava/util/HashMap;.remove       recv=32 ...
[LAWCEF-COL] Ljava/util/HashMap;.remove       recv=32 rcls=Ljava/util/HashMap; nargs=1
[LAWCEF-ENG] Ljava/util/ArrayList;.sort|removeAll|retainAll|forEach / HashMap;.merge|computeIfAbsent  (all correct recv)
```

**Determination 1 (generic, proven):** every missing face reaches the collection shadow
with the CORRECT runtime class and receiver identity. The LAW-E wave's earlier
hypothesis — "the virtual-dispatch bridge loses receiver identity for D8-rewritten
interface calls" — is **REFUTED** (R-NEW-318 runtime-class routing works). The actual
root: **the faces had no handlers**; the registry declined and the bridge generic stub
answered null/false — every face silently no-op'd.

**Determination 2 (generic, proven):** `F089-REMOVE` (0 hits) explained by a dead-code
kill, not dispatch loss: the deque-family block (`s86` F-NEW-165 + `#371` B1) returns on
every path; its map decline `if (state->is_map) return not_handled();` terminated the
ENTIRE dispatch, leaving the real Map.remove law (F-063/R-NEW-287) **unreachable dead
code** for every remove call. Live proof: `[LAWCEF-DEQUE] remove recv=32 is_map=1 …`
fires, `[LAWCEF-REM]` (handler entry) never fires.

**Determination 3 (generic, proven):** static stream faces never reached the laws at
all — the shadow's no-receiver gate (`obj_id == 0 && m != "<init>"` → `not_handled`)
declines every STATIC call; `Stream.of` / `Collectors.toList` are static and
receiver-less (`[LAWCEF-ENG] …Stream;.of recv=83 cls=[Ljava/lang/String; caller=
…$$ExternalSyntheticStaticInterfaceCall0;.m` → COL → gate → generic stub null →
`.filter` NPE).

## 2. Fixes (all generic; java.util/OpenJDK family keys; zero app names)

| Law | Fix | Probe rows |
|-----|-----|------------|
| LAW-C | Java-8 default-method family on the shadow channel: removeIf (descending sweep, 4-store erase), sort (stable insertion, comparator via callback), forEach (Consumer/BiConsumer), removeAll/retainAll (kind-aware membership + app equals), Map.merge (null remap → remove per OpenJDK), Map.computeIfAbsent, Map.getOrDefault. Functional args run via NEW engine-installed `dex_invoke_slot()` (same channel discipline as F-NEW-236d `app_equals_slot`; callee = runtime class; ok=false → loud decline). Supporting framework laws: boxed `X.compareTo` + `Integer.sum`. | K13 K14 K16 K17 K18 |
| LAW-E | (A) Map fall-through: deque block wrapped in `!is_map` so map receivers reach the map remove law (dead-code revival). (B) getOrDefault map law (verbatim default). | K6 |
| LAW-F | (A) SubList VIEW law: mint box (`__sublist_parent__`/`__sublist_off__`) + OpenJDK bounds law; redirect serves get/set/add/remove/size/isEmpty against the parent store at the offset (write-through both ways). (B) Stream pipeline law (bounded faces): of [static] / Collectors.toList [static] / filter (eager via dex_invoke) / collect(toList) → real ArrayList; static-face gate exemption; stream classes claimed. Rest of java.util.stream: **DEFERRED with scope** (not REJECTED — absent-family root is generic). | K3 K15 |

Callback channel: `DexCallOutcome {ok, kind, …}`; engine lambda converts
`CallContext::Arg → DalvikValue`, invokes `try_recursive_invoke(_on_super)`, converts
back. Reentrancy identical to `app_object_equals`.

## 3. Proof / regression (zero drift at every checkpoint)

| Gate | Result |
|------|--------|
| fcol | **18/18** (was 10/18): K6 remOk=true def=42 got=null sz2=1; K13 size=2; K14 [1,2,3]; K15 stream size=2; K17 n=3 c=9; K18 f1;f2;/mf |
| f266 | 6/6 |
| f259 | 7/7 |
| f259g | 12/13 (row-L honest legacy, unchanged) |
| Anchors ×3 | 18/18 BYTE-IDENTICAL: dooz d602648e8e401895 · microtimer da73010a37dd0189 · unote 4f1a9e4e8f64fae8 · gmdice f3b483fe7b7cf51b · opencalc a976d2f9fb675cb3 · chess b5a7a35d5fe0564b |
| Negatives | 19/19 |
| Skill | 13/13 |

Artifacts: `run/cont18/probes_lawcef_final/probe_report.json`, `run/cont18/anchors/`.

Registry: F-NEW-264d → status **TESTED** (6/6 laws closed; stream family rest DEFERRED
with scope), evidence appended, sha16 `2043002891facf8b`.
