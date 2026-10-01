#!/usr/bin/env python3
"""FINAL CAMPAIGN item 22 wave A (ADDITIONAL ROOT-CAUSE AUDIT) + wave C —
append the audit-law fix roots + F-NEW-181 wave-C attribution to both
registry copies and the master worklist."""
import json

NEW = [
    {
        "id": "F-NEW-182", "status": "ROOT-CAUSED-FIXED", "priority": "P0",
        "layer": "inflater/lifecycle-order",
        "title": "XML inflation must not measure before window attach (audit P0-1)",
        "law": "AOSP ViewRootImpl.performTraversals: inflation builds the VIEW TREE ONLY; measure belongs to the first traversal AFTER dispatchAttachedToWindow. The eager measure_layout in inflate_layout_resid dispatched REAL DEX onMeasure (custom_view_measure_hook_) on an UNATTACHED tree — the windowRecomposer/isAttachedToWindow death family for any Compose-related custom view in XML.",
        "evidence": "Source proof: inflate_layout_resid measured immediately after inflate_element; setContentView(View) already had the R349 attach-first law but the XML path did not. FIX ARCHITECTURE: inflater creates the tree only; setContentView(int) records pending_inflate_attach; the engine's frame render consumes it (attach wave FIRST, canonical measure SECOND) — traversal timing honors the S43 post-inflate-field-setup lesson. No second DEX onMeasure per traversal (same-spec memo).",
        "implementation": "layout_inflater.cpp: eager measure removed; android_shadows.cpp: record_pending_inflate_attach in the int branch; execution_engine.cpp: consume + dispatch_attached_subtree_from before measure. REGRESSION MICROTIMER (XML custom view with onAttachedToWindow/onMeasure): da73010a37dd0189 x3 byte-identical.",
    },
    {
        "id": "F-NEW-183", "status": "ROOT-CAUSED-FIXED", "priority": "P0",
        "layer": "viewtree/identity",
        "title": "android.R.id.content must be ONE stable object per window (audit P0-2)",
        "law": "AOSP PhoneWindow: the content parent is ONE object per window — findViewById(android.R.id.content) answers the SAME instance every call. The old next_window_content_id_++ allocated a NEW FrameLayout per lookup while claiming idempotence; framework machinery attaching to different synthetic parents = split ViewTree = blank/partial screens.",
        "evidence": "Source proof at android_shadows.cpp (S83-GFX-BASE). FIX: resolution order (1) subtree BFS for existing content node, (2) per-window remembered node (window_content_nodes_), (3) materialize once; add_child edge-dedup; real class descriptor returned.",
        "implementation": "ViewShadow::findViewById 0x01020002 law rewritten; [P0-2-CONTENT] REUSED trace.",
    },
    {
        "id": "F-NEW-184", "status": "ROOT-CAUSED-FIXED", "priority": "P0",
        "layer": "shadows/runtime-class-identity",
        "title": "View-returning bridges answer the REAL runtime class (audit P0-3 + P0-4)",
        "law": "AOSP findViewById/getChildAt/getContentView/getContext return the ACTUAL runtime object; app code check-casts and instance-of-tests it. A correct object id labeled with a generic Landroid/view/View; or Landroid/content/Context; descriptor broke check-cast MaterialButton/Activity dispatch. P0-4: getContext() resolves the heap object's class (DalvikHeapAdapter.get_object_class) so getContext() instanceof Activity is TRUE when the object IS the activity.",
        "evidence": "Table of fixed bridges: ActivityShadow.findViewById, ActivityShadow.getContentView, ViewShadow.findViewById (2 paths), ViewShadow.getChildAt, ViewShadow.getContext (2 paths incl. the never-null activity fallback). real_view_class() helper: node class_desc or honest fallback.",
        "implementation": "android_shadows.cpp real_view_class() + 5 call sites; context_descriptor lambda resolves heap class.",
    },
    {
        "id": "F-NEW-185", "status": "ROOT-CAUSED-FIXED", "priority": "P1",
        "layer": "shadows/state-laws",
        "title": "setVisibility raises requestLayout; image setters enter the real pipeline; explicit black wins (audit P1-1 + P1-2 + P1-10)",
        "law": "AOSP View.setVisibility -> setFlags -> requestLayout+invalidate: GONE changes LAYOUT INPUTS (siblings expand) — the stale-geometry family is fixed by raising layout_dirty (consumed by the canonical traversal, no inline re-measure). AOSP ImageView.setImage{Bitmap,Drawable,Icon,URI} -> one canonical drawee state then requestLayout+invalidate: every setter now routes into the REAL image pipeline (BitmapStore provenance path / icon resid / asset-uri law) or records an EXPLICIT BLOCKED event with evidence — silent handled_void removed. AOSP TextView.setTextColor is EXPLICIT_RUNTIME provenance: the value-guessing black heuristic (M3-007b) is removed; explicit black ALWAYS wins; style colors carry STYLE_RESOLVED provenance from the inflater.",
        "evidence": "[P1-1-VIS] raised-requestLayout trace; [P1-2-IMAGE]/[P1-2-IMAGE-BLOCKED] per-setter pipeline-or-blocked evidence; [M3-SETTEXTCOLOR] provenance trace. BitmapStore source_desc (decodeResource = APK path) is the provenance that connects setImageBitmap(decodeResource(...)) to the path-decode pipeline.",
        "implementation": "android_shadows.cpp setVisibility/image-setters/setTextColor laws; ViewNode.text_color_provenance + image capture fields; layout_inflater.cpp STYLE_RESOLVED marks.",
    },
    {
        "id": "F-NEW-186", "status": "ROOT-CAUSED-FIXED", "priority": "P1",
        "layer": "inflater/class-identity",
        "title": "Material constructor gate = DEX existence; fully-qualified XML class = slashed DEX descriptor (audit P1-3 + P1-4)",
        "law": "Constructor-hook authority is 'does the class exist in the APK DEX' (the hook's class_info_index_ check), never a package-prefix blanket. Lcom/google/android/ + Lcom/google/ removed from the suppression list: bundled Material classes (MaterialButton/TextInputEditText/FAB) keep their real <init>; genuinely absent classes fail cleanly (warning only). A fully-qualified XML tag is a Java binary name: dots normalize to slashes (JVMS 4.2) — 'Lcom.example.MyView;' never matched the DEX; inner-class $ unchanged; KNOWN mappings unchanged.",
        "evidence": "run_custom_view_constructor: class_info_index_ is the real authority (fails cleanly). class_to_descriptor: slashed normalization with the law documented.",
        "implementation": "layout_inflater.cpp is_app_class_descriptor (2 prefixes removed) + class_to_descriptor (dot->slash).",
    },
    {
        "id": "F-NEW-187", "status": "ROOT-CAUSED-FIXED", "priority": "P1",
        "layer": "renderer/frame-truth",
        "title": "Every authoritative render return value checked; frame authenticity recorded (audit P1-5/P1-6 close-out)",
        "law": "A failed stage_render_frame must never let a stale framebuffer become current evidence: the final capture is SKIPPED on failure; frame manifests record render_ok + suppress changed_pixels when the render failed (frame k cannot be derived from frame k-1's buffer); the click-oracle pixel diff is suppressed on render failure with a report counter.",
        "evidence": "9 call sites patched ([P1-6-RENDER] traces): final-pass capture, frame-sequence per-frame + post-gesture + tap pressed, click-seq, long-press, tick-frame, click-test probe. report[render_failures] surfaces suppressed diffs. Wave-A already made render failure explicit (RENDER_FAIL + framebuffer discard + synthetic suppressed) — this wave closes the remaining unchecked-return paths.",
        "implementation": "execution_engine.cpp: stage_render_frame return checked everywhere; manifest f[render_ok]/note law.",
    },
    {
        "id": "F-NEW-188", "status": "IMPLEMENTED+TESTED", "priority": "P1",
        "layer": "webview/js-engine",
        "title": "WebView.evaluateJavascript routes into the REAL QuickJS engine; ValueCallback fires (audit P1-11)",
        "law": "The runtime SHIPS a real WebView/QuickJS subsystem (S109) — the old 'no JS engine' silent drop is wrong for any WebView with a loaded document. Android law: the script evaluates in the page's global scope (same realm, full DOM/canvas access), the callback receives the JSON-encoded result ('null' for undefined/exception — the callback ALWAYS fires), async work drains via the S118 JOB-PUMP law. Shadow/engine split: the shadow records (callback oid, JSON); the ENGINE invokes onReceiveValue via try_recursive_invoke (Room/Thread pattern).",
        "evidence": "WebViewEngine::evaluate_javascript + Impl::eval_json (JS_EVAL_TYPE_GLOBAL + JS_JSONStringify + bounded job drain + exception hygiene); [P1-11-WV] executed/exception/BLOCKED diagnostics; explicit BLOCKED frontier only when no document/engine exists. DOM mutations surface on the next frame render (walk re-composites every frame).",
        "implementation": "webview_engine.h/.cpp + android_shadows.cpp evaluateJavascript + dalvik_engine.cpp post-dispatch ValueCallback drain.",
    },
    {
        "id": "F-NEW-181", "status": "ROOT-ATTRIBUTED", "priority": "P0",
        "layer": "dex/di-lattice",
        "title": "WAVE C: RegularImmutableMap.get() probe livelock attributed to the F-NEW-173 placeholder-materialization family",
        "law": "The compiled get() re-masks every probe step (disasm run/wavec_get_disasm.txt: and-int v1, mask at 0x56) — in-bounds by construction; the ONLY exits are key match or sentinel. Livelock therefore requires a sentinel-FULL conversion table.",
        "evidence": "SPIN-GET probe (permanent): table=o26443 byte[3] sentinels=0 occupied=3 — 100% full; ALL 3 slots -> offset 0 -> alternating[0] = o1659 Integer(33604) — THE EXACT placeholder-Integer of F-NEW-173. size_param=17750 with tableSize=3: guava chooseTableSize(17750) must be 32768 (int path) — the caller's tableSize materialized as 3 from the same placeholder family. alternating len 47425 = builder-growth array (31,616*3/2+1), NOT 2*size=35,500 — the map instance carries fields from different build generations.",
        "implementation": "NEXT: trace the tableSize parameter feed into createHashTable (chooseTableSize execution on placeholder inputs) — one instrumented run; the SPIN-GET probe is permanent evidence. No fake fix: the honest frontier is the upstream key/size materialization.",
    },
    {
        "id": "F-NEW-189", "status": "IMPLEMENTED", "priority": "P1",
        "layer": "gates/determinism",
        "title": "Gate data-root freshness law discovered and documented (simplestopwatch SharedPreferences persistence)",
        "law": "Golden gates must run on a FRESH data root: apps persist state via SharedPreferences (simplestopwatch stores elapsed time) and a reused data-root LAWFULLY loads prior state — a gate, not the runtime, was the nondeterminism source.",
        "evidence": "Same binary (sha 3e21e875bf7c5622): fresh data-root = 10446aaf0cd642cc (golden match), reused data-root = 88377dd328d6e041 (state-restored render) — both byte-identical x3 within their class. Gate script updated to fresh-per-run.",
        "implementation": "scripts/final_campaign_item22_gates.py fresh data-root per run.",
    },
]

WORKLIST_ITEM = {
    "id": "FINAL-CAMPAIGN-22",
    "title": "ADDITIONAL ROOT-CAUSE AUDIT (17 items: P0-1..P0-4, P1-1..P1-11) + wave C (F-NEW-181) + item-21 P1-2",
    "status": "WAVE-A COMPLETE (15/17 audit items IMPLEMENTED+TESTED this wave; P1-5/P1-7 verified wave-A coverage; item-21 P1-2 unification = own wave; phases 4-20 continue)",
}

def main():
    # canonical registry
    for path in ["canonical/root_cause_registry.json", "root_registry.json"]:
        try:
            with open(path) as f:
                reg = json.load(f)
        except FileNotFoundError:
            continue
        roots = reg.setdefault("roots", [])
        ids = {r.get("id") for r in roots}
        added = 0
        for n in NEW:
            if n["id"] in ids:
                # update existing entry (F-NEW-181 attribution upgrade)
                for i, r in enumerate(roots):
                    if r.get("id") == n["id"]:
                        roots[i] = n
                        added += 1
                        break
            else:
                roots.append(n)
                added += 1
        counts = {}
        for r in roots:
            counts[r.get("status", "?")] = counts.get(r.get("status", "?"), 0) + 1
        reg["status_counts"] = counts
        reg["total_roots"] = len(roots)
        with open(path, "w") as f:
            json.dump(reg, f, indent=2)
        print(f"{path}: +{added} -> {len(roots)} roots")
    # worklist
    try:
        with open("canonical/master_worklist.json") as f:
            wl = json.load(f)
        items = wl.setdefault("items", [])
        if not any(i.get("id") == "FINAL-CAMPAIGN-22" for i in items):
            items.append(WORKLIST_ITEM)
            wl["counts"] = wl.get("counts", {})
            wl["counts"]["items"] = len(items)
            with open("canonical/master_worklist.json", "w") as f:
                json.dump(wl, f, indent=2)
            print(f"worklist: item 22 registered -> {len(items)} items")
    except FileNotFoundError:
        print("worklist not found")

if __name__ == "__main__":
    main()
