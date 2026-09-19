#!/usr/bin/env python3
"""S62+ registry update: F-110 family implemented + F-111/F-112 registered.

Follows the S58/S62 registry-update pattern: load root_registry.json,
patch/add the specific roots with evidence-anchored entries, save.
"""
import json

REG = "root_registry.json"

with open(REG) as f:
    reg = json.load(f)

roots = reg["roots"]
by_id = {}
for r in roots:
    by_id.setdefault(r.get("id"), []).append(r)


def find(rid):
    return by_id.get(rid, [None])[0]


def add(entry):
    if entry["id"] in by_id:
        raise SystemExit(f"{entry['id']} already present — refusing to duplicate")
    roots.append(entry)
    by_id[entry["id"]] = [entry]


EV = "docs/evidence/s62plus_spotlight/S62PLUS_REPORT.md"

# ── F-110: REGISTERED (S62) → IMPLEMENTED+TESTED with measured A/B ──────
f110 = find("F-110")
if f110 is None:
    add({
        "id": "F-110",
        "title": "Per-invoke/per-exit constant-cost lever (registered S62, measured)",
        "status": "IMPLEMENTED+TESTED",
        "family": "S62+ spotlight unblock push",
        "note": (
            "F-110a result-snapshot deferral: execute_method_internal deep-copied "
            "result.call_stack + result.heap at EVERY (incl. nested) method exit — "
            "O(N x heap) quadratic; gprof anuto 25s startup: 387,639,677 "
            "pair<string,string> copies. Outermost-only snapshot preserves the exact "
            "final result content. A/B same APK same 25s budget: 128,076 -> 7,400,000+ "
            "instructions (57.8x), RSS 41MB -> 335MB (deeper reach). "
            "F-110b THREAD-SLEEP YIELD: Thread.sleep inside a run-to-completion "
            "drained body = deterministic yield (virtual clock advance + frame-chain "
            "suspend at drain boundary); first hit anuto GameLoop.run 50K-visit spin "
            "-> APP BOUNDARY unwind. "
            "F-110c ArrayList add(int,E)/remove(int)/remove(Object) heap-backed laws "
            "(upstream shift semantics + deferred IOOBE); first hit anuto "
            "MessageQueue.processMessages drain loop could never remove the head "
            "(infinite loop + 2.1GB balloon). "
            "F-110d CURRENT-THREAD IDENTITY: Thread.currentThread() returns the "
            "drained thread's heap object while its body runs (save/restore, "
            "nested-safe); main singleton unchanged outside. First hit anuto "
            "isThreadChangeNeeded gating (loadMap re-post forever). "
            "F-110e TOUCH-TARGET + MotionEvent: view_touchable includes "
            "touch_listener_id (AOSP dispatchTouchEvent listener gate before "
            "clickability); dispatch_touch_listener onTouch(View,MotionEvent)Z with "
            "consumed semantics; MotionEvent materialization + getAction/getX/getY "
            "bridge; framework static INT constant table (MotionEvent.ACTION_*). "
            "Evidence: " + EV
        ),
        "consumers": [
            "ch.logixisland.anuto (GameLoop.run yield + currentThread identity)",
            "ch.logixisland.anuto (MessageQueue drain via ArrayList remove laws)",
            "ch.logixisland.anuto (GameView touch target + onTouch dispatch)",
            "generic: any drained thread body with a sleep loop",
            "generic: any ArrayList insert/remove/indexed-add drain pattern",
        ],
    })
else:
    f110["status"] = "IMPLEMENTED+TESTED"
    f110["note"] = (
        "S62 registered the lever (per-invoke constants + DalvikValue copy cost). "
        "S62+ implemented as the F-110a..e family with measured A/B: F-110a "
        "result-snapshot deferral (57.8x instruction rate on the same 25s anuto "
        "startup budget: 128,076 -> 7,400,000+ insns; 387.6M pair<string,string> "
        "copies removed per gprof); F-110b thread-sleep yield; F-110c ArrayList "
        "add(int,E)/remove(int)/remove(Object); F-110d current-thread identity; "
        "F-110e touch-target law + MotionEvent family + framework static-int table. "
        "Evidence: " + EV
    )

# ── F-111: LayoutInflater <view class=...> namespace law ────────────────
add({
    "id": "F-111",
    "title": "LayoutInflater <view class=...> no-namespace class attribute law",
    "status": "ROOT-CAUSED-FIXED",
    "note": (
        "AOSP LayoutInflater.createViewFromTag reads the custom-view class via "
        "getAttributeValue(null, \"class\") — NO namespace. The AXML parser gives "
        "no-namespace attributes ns=\"\"; the inflater's el.attr(\"class\") defaulted "
        "to ns=\"android\" and missed, degrading <view class=\"FQCN\"> to a generic "
        "Landroid/view/View; and bypassing the G11 DEX-constructor hook (the app's "
        "real game board was a hollow placeholder). Fix: namespace-agnostic lookup. "
        "First hit: anuto GameView (ch.logixisland.anuto.view.game.GameView) — after "
        "the fix the G11 (Context,AttributeSet) ctor law constructs the REAL view and "
        "the C013 draw path dispatches its REAL onDraw. Evidence: " + EV
    ),
    "consumers": ["ch.logixisland.anuto (GameView)", "any app using <view class=...>"],
})

# ── F-112: manifest Application buildClassName law ───────────────────────
add({
    "id": "F-112",
    "title": "Manifest <application> android:name buildClassName law (leading-dot join)",
    "status": "ROOT-CAUSED-FIXED",
    "note": (
        "AOSP PackageParser.buildClassName: leading '.' joins the manifest package; "
        "a name with no dot also joins; otherwise as-is. application_name was taken "
        "raw: '.AnutoApplication' degraded to 'L/AnutoApplication;' -> 'not present "
        "in DEX' -> default Application fallback -> the app's real "
        "Application.onCreate never ran (no app singleton; custom-view ctor "
        "depending on it fails). Fix: same three-branch law the main-activity name "
        "already applies. Post-fix: [R341-APP] instantiating Application "
        "Lch/logixisland/anuto/AnutoApplication; onCreate OK ins=14751. "
        "Evidence: " + EV
    ),
    "consumers": ["ch.logixisland.anuto", "any app declaring a relative Application class"],
})

# ── summary counters ─────────────────────────────────────────────────────
reg["summary"]["total_roots"] = len(roots)

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
    f.write("\n")

print("registry updated:",
      {r.get("id"): r.get("status") for r in roots
       if r.get("id") in ("F-110", "F-111", "F-112")})
