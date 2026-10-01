#!/usr/bin/env python3
"""S129: register R-NEW-425 (VelocityTracker law) + R-NEW-426 (TouchDelegate
+ MOVE-delivery law) in the writable root registry, with the S129 evidence
chain. Idempotent."""
import json

P = '/home/z/my-project/root_registry.json'
rr = json.load(open(P))

if not any(r['id'] == 'R-NEW-425' for r in rr['roots']):
    rr['roots'].append({
        "id": "R-NEW-425",
        "title": "INPUT VelocityTracker law gap (CAP-INPUT-108): the runtime had no velocity tracker — "
                 "android.view.VelocityTracker.obtain/addMovement/computeCurrentVelocity/getXVelocity did not exist, "
                 "and the dispatcher never delivered MOVE events to app code, so every fling/gesture-velocity path "
                 "(ScrollView fling seeding, GestureDetector.onFling) was starved of data.",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "fg": True,
        "app": "INPUT layer — fling/gesture corpus class",
        "evidence": "S129: AOSP android-14 LSQ2 native law ported 1:1 (LeastSquaresVelocityTrackerStrategy degree 2 "
                    "Weighting::NONE; HORIZON 100ms; HISTORY_SIZE 20; ASSUME_POINTER_STOPPED_TIME 40ms; "
                    "solveUnweightedLeastSquaresDeg2 closed form; velocity=coeff[1]; getComputedVelocity clamp "
                    "v*units/1000 — sources committed under docs/upstream/aosp/input_laws/). VelocityTrackerShadow DEX "
                    "bridge (obtain/recycle/clear/addMovement/computeCurrentVelocity/getXVelocity/getYVelocity/"
                    "getAxisVelocity/isAxisSupported). MotionEvent materialization carries __time__ (virtual-clock ms) + "
                    "getEventTime bridge + AXIS_X/Y/SCROLL constants. Generic --swipe driver gesture (DOWN → 12 MOVEs "
                    "@16ms 60Hz → UP through the TouchDispatcher law pipeline). Evidence: velocity_tracker_law_test 17 "
                    "checks ALL PASS; real-DEX fixture VelView computes VY=999;VX=0 (192px/12 MOVEs@16ms, float32 LSQ2 "
                    "precision — same characteristic as AOSP's float solver), 3-run frame-SHA identical; battery ALL "
                    "PASS (114 stages); S129 INPUT wave 11/11 (calc a169346e x3 + flappy menu 13cf4746 x3 goldens "
                    "PRESERVED, ttt b5a7a35d byte-identical, telegram/whatsapp honest NOT-A-RENDER).",
        "missing": "AXIS_SCROLL (axis-26) differential-value strategy not modeled (single-pointer X/Y only — documented "
                   "boundary); VelocityTracker pool semantics (obtain recycle reuse) simplified; historical-sample "
                   "(getHistorical*) API surface absent.",
        "next": "CAP-SCROLLING-126 computeScroll + 127 EdgeEffect — the fling consumer chain (OverScroller/fling seed "
                "from computed velocity) is the next INPUT→SCROLLING handoff.",
        "commit": "S129 (this session)",
    })
    print('R-NEW-425 registered')

if not any(r['id'] == 'R-NEW-426' for r in rr['roots']):
    rr['roots'].append({
        "id": "R-NEW-426",
        "title": "INPUT TouchDelegate law gap + MOVE-delivery law gap (CAP-INPUT-110): android.view.TouchDelegate did "
                 "not exist (no ctor capture, no setTouchDelegate, no View.onTouchEvent consult — View.java "
                 "L17060-17064), and the dispatcher delivered only DOWN/UP to app code (MOVE events never reached "
                 "OnTouchListener/onTouchEvent overrides — every drag-driven app path was starved).",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "fg": True,
        "app": "INPUT layer — expanded-touch-area corpus class (small-button accessibility pattern)",
        "evidence": "S129: AOSP android-14 laws quoted from source (TouchDelegate.java ctor mSlopBounds=mBounds "
                    "inset(-slop); DOWN arm mDelegateTargeted=mBounds.contains EXACT; MOVE/UP arms slopBounds-gated "
                    "with setLocation(w/2,h/2) / setLocation(-2*slop,-2*slop); CANCEL clears; View.onTouchEvent "
                    "consult BEFORE the clickable switch; AOSP ViewGroup fallback arm = delegate consulted when NO "
                    "child claims the DOWN, deepest-visible-view candidate + ancestor unwind). TouchDelegateShadow ctor "
                    "capture + View.setTouchDelegate bridge + ViewNode delegate fields; dispatcher DOWN consult (target "
                    "own delegate + fallback ancestors) with delegate retarget + event translation to delegate center; "
                    "MOVE/UP delegate forwarding; MOVE-delivery law (AOSP dispatchTransformedTouchEvent — every gesture "
                    "event reaches the captured target's listener/onTouchEvent; fixed the S128-arm ACTION_MOVE code to "
                    "the AOSP constant 2). Evidence: touch_delegate_law_test 23 checks ALL PASS; real-DEX fixture: tap "
                    "(900,700) outside the 48dp button inside delegate bounds → DELEGATE-CLICK via the fallback law, "
                    "swipe VY=999;VX=0, 3-run frame-SHA identical; battery ALL PASS (114 stages); S129 INPUT wave 11/11.",
        "missing": "TouchDelegate accessibility hover arm (onTouchExplorationHoverEvent) not modeled; "
                   "requestDisallowInterceptTouchEvent child flag remains a documented boundary; per-pointer delegate "
                   "split (multi-touch) out of the single-pointer model.",
        "next": "M-01 INPUT residuals: CAP-INPUT-107 multi-touch upgrade; intercept wave on sudoku/opencalculator "
                "SlidingUpPanelLayout; then M-03 GAME lockCanvas loop (CAP-SCROLLING-126 computeScroll chain).",
        "commit": "S129 (this session)",
    })
    print('R-NEW-426 registered')

json.dump(rr, open(P, 'w'), indent=1, ensure_ascii=False)
print('roots =', len(rr['roots']))
