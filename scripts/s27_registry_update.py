#!/usr/bin/env python3
"""S27 registry update: append R-NEW-324..331 (S25/S26 debt + S27 session) with honest statuses."""
import json

REG = "/home/z/my-project/root_registry.json"
r = json.load(open(REG))
roots = r["roots"]
have = {x["id"] for x in roots}

new_roots = [
 {
  "id": "R-NEW-324", "status": "VERIFIED-FIXED", "priority": "P0", "fg": True,
  "evidence": "S25 (F-091+F-091b): dooz died at NavController.addEntryToBackStack link loop (getBackStackEntry(parent.id=0)) because backQueue.addAll(hierarchy) copied NOTHING. Two stacked engine gaps: (a) host-interface dispatch matched Iterator.hasNext() to z1/i.isEmpty()Z by descriptor alone (F-091b gate: declared interface must be DEX-defined); (b) z1/i = minified kotlin.collections.ArrayDeque declares NO iterator()/listIterator() in DEX — implemented the AbstractList bidirectional protocol law (hasNext/next/hasPrevious/previous/nextIndex/previousIndex) driving the receiver's OWN DEX size()/get(I) via try_recursive_invoke (F-091). DEX-collection iteration for every R8-minified Kotlin app.",
 },
 {
  "id": "R-NEW-325", "status": "VERIFIED-FIXED", "priority": "P0", "fg": True,
  "evidence": "S25 (F-092): dooz NPE 'activity.getOnBackInvokedDispatcher() must not be null' (androidx.activity OnBackPressedDispatcher.m). Upstream law: getOnBackInvokedDispatcher returns a LAZY proxy on every API level (API<33: inert no-op). ActivityShadow law: non-null placeholder Landroid/window/OnBackInvokedDispatcher; register/unregister degrade to no-ops. Every androidx.activity app benefits.",
 },
 {
  "id": "R-NEW-326", "status": "VERIFIED-FIXED", "priority": "P0", "fg": True,
  "evidence": "S25 (F-093/F-093b): STTT ISE 'You need to use a Theme.AppCompat theme' at AppCompatDelegateImpl.createSubDecor — the runtime had NO obtainStyledAttributes bridge. F-093: ActivityShadow.obtainStyledAttributes(int[]) resolves every styleable attr against the activity theme via the canonical ARSC bag query (parent-chain inheritance + one reference hop) and materializes a theme-backed TypedArray (F-036 heap-array convention); F-093b = engine-side TypedArray positional reader law. Every AppCompatActivity app benefits.",
 },
 {
  "id": "R-NEW-327", "status": "VERIFIED-FIXED", "priority": "P0", "fg": True,
  "evidence": "S25 (F-094): STTT's AndroidManifest.xml is PLAIN-TEXT XML (not binary AXML) — binary reader returned application_theme_resid=0. Law: capture application_theme_ref in parse_plain_xml; resolve_theme_attr_value falls back to the ref string ('@style/AppTheme.NoActionBar') → ArscParser::find_id → resid. Odd-build plain-text-manifest family.",
 },
 {
  "id": "R-NEW-328", "status": "VERIFIED-FIXED", "priority": "P0", "fg": True,
  "evidence": "S26 (F-095): dooz compose draw silently no-oped — AndroidComposeView.dispatchDraw → ViewLayer.drawLayer → DrawChildContainer.drawChild → FRAMEWORK ViewGroup.drawChild had NO law → bridge answered void → the ENTIRE compose ViewLayer content draw never executed (0 canvas ops). F-095: (a) ViewGroup.drawChild(Canvas,View,long) law dispatches the CHILD's real draw (dispatchDraw else onDraw) on the SAME canvas; (b) Canvas.isHardwareAccelerated() → false (software-renderer truth; keeps ViewLayer.dispatchDraw + RenderNodeLayer on the correct software paths per upstream 1.6.7). Verified: dooz draw window now reaches LayoutNode.draw → NodeCoordinator.draw → InnerNodeCoordinator.performDraw node-tree walk.",
 },
 {
  "id": "R-NEW-329", "status": "VERIFIED-FIXED", "priority": "P0", "fg": True,
  "evidence": "S27 (F-096 + F-096b): the compose PLACEMENT gate. ROOT (evidence-grade, static + live): (1) F-096 — the runtime dispatched NO real-DEX View lifecycle for PROGRAMMATIC views: hooks existed for inflate-ctor (G11), leaf onMeasure (F10), onDraw (C013) — but onMeasure/onLayout of androidx AndroidComposeView (created programmatically, overriding BOTH in DEX — verified via androguard: onMeasure(II)V + onLayout(ZIIII)V in dooz classes.dex) never executed → updateRootConstraints/measureOnly + measureAndLayout → root.place(0,0) → placeAt → isPlacedByParent/markNodeAndSubtreeAsPlaced never ran → every LayoutNode isPlaced=false → InnerNodeCoordinator.performDraw skipped all children → 0 canvas ops. F-096: one-time per-node real-DEX lifecycle dispatch (measure EXACTLY(rect) then layout(changed=true,l,t,r,b)) in the render walk, AOSP order. (2) F-096b — View$MeasureSpec.getMode returned the SHIFTED mode (0/1/2); AOSP View.java returns the IN-PLACE masked mode (spec & 0xC0000000: 0/0x40000000/0x80000000) — compose AndroidComposeView.z compares mode == 0x40000000 directly, so the shifted answer hit the else->throw IllegalStateException arm (dooz onMeasure → z pc=31 ISE → app-boundary unwind). POST-FIX: getMode law corrected; dooz compose measure+layout+place chains EXECUTE as real bytecode (F074 super-dispatch walks through node/c, node/l, k0/T placement laws; MSPEC diag evidence); frame SHA UNCHANGED 193466ead8fd21d6 (802px placeholder) — determinism x3 preserved; battery 94/94.",
 },
 {
  "id": "R-NEW-330", "status": "OBSERVED-FAIL", "priority": "P0", "fg": True,
  "evidence": "S27 CURRENT FRONTIER (dooz, honest-open): IllegalStateException 'DepthSortedSet.remove called on an unattached node' at m0/m.c (DepthSortedSet.remove, upstream DepthSortedSet.kt:67 check(node.isAttached)) ← i.h (MeasureAndLayoutDelegate.measureAndLayout popEach) ← AndroidComposeView.onLayout. The compose measure/layout/place chains now run (R-NEW-329 closed); measureAndLayout pops a relayoutNodes entry whose LayoutNode.owner == null (attach incomplete for at least one node — nearby trace shows [M3-19-CYCLE] active-cycle stub on m0/T;.a during the same window). NEXT: identify the unattached node (add bounded receiver/arg evidence to the DepthSortedSet.remove dispatch) and close the attach-propagation/active-cycle law.",
 },
 {
  "id": "R-NEW-331", "status": "OBSERVED-FAIL", "priority": "P1", "fg": True,
  "evidence": "S27 (cross-app, honest-open): the Fragment host wiring family. STTT (nl.hnogame.tictactoesuperttt_20): FragmentManager 'not been attached to a host' + AppCompat subDecor theme ISE at h.R repeated (pre-existing S25/S26 frontier, unchanged). REAL Telegram v10.14.5 golden (sha f5e1192725772960 — RE-ACQUIRED 2026-09-12, K-26 BLOCKER LIFTED: official dl serves the exact pinned build again): parse + ApplicationLoader.onCreate + LifecycleRegistry machinery execute; frontier = SAME FragmentManager.ensureExecReady 'FragmentManager has not been attached to a host' ISE + SafeIterableMap$IteratorWithAdditions.next active-cycle churn (18k+ stubs) + MessagesController ISE 'called wrong accept method'. One generic family (fragment host attach law) blocks BOTH apps.",
 },
]

added = 0
for nr in new_roots:
    if nr["id"] not in have:
        roots.append(nr)
        added += 1

# refresh summary
r["summary"] = {
    "total_roots": len(roots),
    "open_frontiers": [x["id"] for x in roots if x["status"] in ("OBSERVED-FAIL", "OBSERVED-OPEN")][-6:],
    "last_updated": "S27 2026-09-12",
    "note": "R-NEW-324..328 back-filled from S25/S26 worklog records (registry JSON debt); 329 closed in S27 (F-096+F-096b); 330/331 new honest frontiers."
}
json.dump(r, open(REG, "w"), indent=1, ensure_ascii=False)
print(f"registry: +{added} roots -> {len(roots)} total")
