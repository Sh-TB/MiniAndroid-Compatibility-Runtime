#!/usr/bin/env python3
"""cont61b_registry.py — CONT-61 W2: F-NEW-267 CLASSIFIED -> ROOT-CAUSED-PARTIAL."""
import json, datetime

PATH = "/home/z/my-project/root_registry.json"
d = json.load(open(PATH))
for r in d["roots"]:
    if r.get("id") == "F-NEW-267":
        r["status"] = "ROOT-CAUSED-PARTIAL"
        r["layer"] = "input/touch-target + input/dispatch-arm + framework/view-coordinates"
        r["title"] = (
            "COMPOSE TAP HIT-TEST GAP (CONT-61 update): three stacked legs decoded "
            "at the dooz v23 tap (820,1837) on the New game button. LEG 1 FIXED: the "
            "TouchDispatcher claim walk answered touchable=false for the compose host "
            "(AndroidComposeView Lt4;) — the S122/R-NEW-417 capture only covered "
            "INFLATED custom views' onTouchEvent overrides; compose hosts are created "
            "programmatically and override dispatchTouchEvent (Lt4; measured: "
            "dispatchTouchEvent(MotionEvent)Z size=249, the compose input ENTRY). "
            "LEG 2 FIXED: the dispatch arm always invoked onTouchEvent — the override "
            "wins (AOSP: the framework caller invokes dispatchTouchEvent). LEG 3 "
            "FIXED: the compose hit-test coordinate laws did not exist — "
            "getLocationOnScreen/getLocationInWindow/transformMatrixToGlobal answered "
            "typed-default (int[] zeros, identity matrix). REMAINING LEG (named, "
            "decoded, unfixed): with all three fixed the dispatched walk reaches the "
            "compose pointer-input filter dispatch and finds the filter list EMPTY "
            "([TOUCHWIN-SIZE] obj#2554 -> 0 x3, from Las0.t) — the hit test consults "
            "a -1x-1 never-measured placeholder View (id 479) for its window base "
            "([TOUCHWIN-LOC]) and the LayoutNode-tree bounds walk misses every node; "
            "the compose node-tree bounds materialization is the next decode."
        )
        r["result"] = (
            "MEASURED at 4436cc61+touch-laws: [F117-TAP] DOWN (540,960) target=0 -> "
            "target=1446 (the AndroidComposeView; the tri-state lazy probe via the "
            "engine-bound class-chain walk). [UI-EVENT] arm=dispatchTouchEvent "
            "DISPATCHED consumed=false; the TOUCHWIN-BRIDGE trace shows the FULL "
            "compose input pipeline execute: Lt4.q rawX/rawY/pointerCount -> "
            "isAttachedToWindow=1 -> Lt4.m (obtainNoHistory -> PointerEvent build "
            "(getPointerId/getToolType/getClassification/getButtonState/isFromSource) "
            "-> hit-test walk (Matrix.reset -> transformMatrixToGlobal chain -> "
            "getLocationOnScreen/inWindow) -> filter dispatch (Las0.t)). FIX SITES "
            "(all generic, zero app knowledge): (1) view_touchable dispatchTouchEvent "
            "override law with the lazy tri-state probe (ViewShadow node field, "
            "mutable, engine-bound DexOverrideFn); (2) the DOWN arm gate + the "
            "dispatch_touch_listener arm selection (dispatchTouchEvent when the class "
            "chain defines it, else onTouchEvent S122); (3) the three coordinate "
            "laws (parent-chain (x,y) sum; Matrix pre/post translate laws with the "
            "M33 algebra: pre=+T on the c/f terms, post=bilinear). ZERO-DRIFT: 11/11 "
            "anchors byte-identical (dooz180 4f32f50fd55ccf90, csw d3c26b73ee21e571, "
            "micro/unote/gmdice/opencalc/ttt/flappy/g2048/tanana/simplecalc) + probe "
            "battery == records (f259g 84/7, fnew302 48/24, fnew298 corner PASS)."
        )
        r["evidence"] = (
            "run/cont61/dooz_tap1..t8 (the decode ladder: target=0 -> 1446 -> "
            "DISPATCHED -> the empty-hit-list frontier), evidence/cont61/, "
            "scripts/cont9_dexdump.py disasm (Lt4; method table: "
            "dispatchTouchEvent size=249, q=109, m=387, s=49)."
        )
        break
n = len(d["roots"])
d["total"] = n
d["count"] = n
d["total_roots"] = n
d["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
json.dump(d, open(PATH, "w"), indent=1, ensure_ascii=False)
print("F-NEW-267 updated; roots:", n)
