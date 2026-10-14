#!/usr/bin/env python3
"""CONT-18: append LAW-C/E/F closeout evidence to F-NEW-264d and flip status."""
import json

REG = "/home/z/my-project/root_registry.json"

ADD = (
    " [CONT-18 LAW-C/E/F 2026-10-08] ALL THREE REMAINING LAWS CLOSED at binary "
    "8ee839e718877216 (fcol 10/18 -> 18/18). DETERMINATION EVIDENCE (user directive: "
    "investigate LAW-C/E/F only to definitive determination; fix only a proven generic "
    "root; else REJECT/DEFER; then move directly to F-217 first-divergence):\n"
    "(1) ROOT DISPATCH TRACE (run/cont18/probes_lawcef1..4, env-gated LAWCEF diags in "
    "try_shadow_dispatch + CollectionShadow::dispatch): every missing face reaches the "
    "collection shadow with the CORRECT runtime class and receiver identity "
    "(ArrayList.removeIf recv=73, HashMap.getOrDefault/remove recv=32, merge/computeIfAbsent "
    "recv=92, forEach recv=102, sort recv=78, removeAll/retainAll recv=87, subList recv=20) — "
    "the earlier LAW-E hypothesis 'the virtual-dispatch bridge loses receiver identity for "
    "iface-rewritten calls' is REFUTED (R-NEW-318 runtime-class routing works). The real "
    "root is simpler and fully generic: the faces had NO handlers — the registry declined, "
    "the bridge generic stub answered null/false, every face silently no-op'd.\n"
    "(2) LAW-E FIX A — MAP FALL-THROUGH LAW (dead-code kill): the deque-family block "
    "(s86 F-NEW-165, extended by #371 B1) returned on EVERY path; its map decline "
    "`if (state->is_map) return not_handled();` terminated the ENTIRE "
    "CollectionShadow::dispatch — the real Map.remove law (F-063/R-NEW-287) below it was "
    "UNREACHABLE DEAD CODE for every remove call since the deque family landed. "
    "Map.remove silently no-op'd (K6 remOk=false, got=@33 stale). Fix: wrap the element "
    "path in `if (!state->is_map)` so map receivers FALL THROUGH to the map laws.\n"
    "(3) LAW-C — JAVA-8 DEFAULT-METHOD FAMILY LAW: one machinery, seven faces, all "
    "kind-aware on the 4-store parallel structure, functional arguments (D8-desugared "
    "lambda objects = real DEX code) executed through a new engine-installed invocation "
    "channel `CollectionShadow::dex_invoke_slot()` (same slot discipline as the F-NEW-236d "
    "app_equals channel; installed in install_collection_equality_law; callee runtime "
    "class from the heap; try_recursive_invoke + try_recursive_invoke_on_super; "
    "ok=false -> the law DECLINES loudly, never fakes). Faces: removeIf (descending sweep, "
    "lawa_remove_index 4-store erase), sort (stable insertion, 4-store lockstep swap, "
    "comparator via dex_invoke 'compare'), forEach (Consumer per element / BiConsumer per "
    "entry), removeAll/retainAll (kind-aware membership: string value / int value / "
    "app_equals for objects), Map.merge (absent -> put val; present -> remFunc.apply; "
    "null remap -> REMOVE per OpenJDK), Map.computeIfAbsent (present -> mapping; absent -> "
    "fn.apply(key), null -> no mapping), Map.getOrDefault (verbatim default). Supporting "
    "framework laws: boxed X.compareTo (Integer/Long/Short/Byte/Character — unbox "
    "'value' field, sign compare) and Integer.sum(int,int) (wrapping) in bridge_to_api — "
    "the comparators/accumulators behind Integer::compareTo / Integer::sum.\n"
    "(4) LAW-F — SUBLIST VIEW LAW + STREAM PIPELINE LAW (bounded face set): subList(from,to) "
    "mints a view box (__sublist_parent__/__sublist_off__) with OpenJDK bounds law "
    "(IndexOutOfBoundsException); the redirect serves get/set/add/remove/size/isEmpty "
    "against the PARENT store at the offset (write-through both directions, kind-aware); "
    "unknown view faces decline loudly; CoMod-on-parent-structural-mutation = documented "
    "DEFERRED boundary. Stream: Stream.of(T...) [static] mints a source box from the "
    "varargs array (shadow heap array accessors), Collectors.toList() [static] mints a "
    "collector box, filter(Predicate) eagerly evaluates the stage via dex_invoke (eager = "
    "honest bound: laziness unobservable in a linear of->filter->collect chain), "
    "collect(toList()) materializes a real ArrayList. Static-face gate fix: the shadow's "
    "no-receiver decline (`obj_id == 0 && m != <init>` -> not_handled) killed every STATIC "
    "face — Stream.of/toList are static and receiver-less; exempted via static_stream_face. "
    "Stream classes added to handles_class. The REST of java.util.stream (map/flatMap/"
    "sorted/primitive streams/spliterators) stays DEFERRED with this scope note — not "
    "REJECTED (the absent-family root is generic) but deliberately unimplemented in this "
    "wave per one-law-one-fix discipline.\n"
    "(5) PROOF: fcol 18/18 (K1..K18 incl. K6 remOk=true def=42, K13 size=2, K14 [1,2,3], "
    "K15 stream size=2, K17 n=3/c=9); f266 6/6; f259 7/7; f259g 12/13 honest row-L; "
    "anchors 6/6 x3 BYTE-IDENTICAL (dooz d602648e8e401895, microtimer da73010a37dd0189, "
    "unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, chess "
    "b5a7a35d5fe0564b); negatives 19/19; skill 13/13. Probe artifacts: "
    "run/cont18/probes_lawcef_final/. Env-gated LAWCEF diags retained (bounded 60, "
    "MINIANDROID_LAWCEF_TRACE=1) for the F-217 campaign evidence chain."
)

d = json.load(open(REG))
for r in d["roots"]:
    if r.get("id") == "F-NEW-264d":
        r["evidence"] = r["evidence"].rstrip() + ADD
        r["status"] = "TESTED"
        r["title"] = r["title"].replace(
            "ONE LAW = ONE GENERIC FIX each; no per-method roots.",
            "ONE LAW = ONE GENERIC FIX each; no per-method roots. ALL SIX LAWS CLOSED "
            "A/B/D (prior waves) + C/E/F (this wave): fcol 18/18; stream family beyond "
            "of/filter/collect(toList) DEFERRED with scope.")
d["note"] = d.get("note", "") + ""  # untouched
json.dump(d, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry updated; 264d status:", [r["status"] for r in d["roots"] if r.get("id") == "F-NEW-264d"][0])
