#!/usr/bin/env python3
"""S222: post the wave receipts on #582 and #583 (the four new GP comments:
ids 6812887007 + 6812985391 on #582, ids 6812887432 + 6812986803 on #583)."""
import json, subprocess

CRED = subprocess.run(["git", "credential-fill-wrapper"], capture_output=True)
def token():
    p = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")

def post(issue, body):
    t = token()
    r = subprocess.run(["curl", "-sS", "-X", "POST",
        "-H", f"Authorization: token {t}", "-H", "Accept: application/vnd.github+json",
        "-d", json.dumps({"body": body}),
        f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments"],
        capture_output=True, text=True, timeout=120)
    d = json.loads(r.stdout)
    print(f"#{issue}: comment id {d.get('id')} at {d.get('created_at')}")
    return d.get('id')

TABLE_50 = """| # | Finding | Disposition | Evidence at HEAD `eff78882` |
|---|---|---|---|
| 1 | APP-001 onCreate failure swallowed | PARTIAL (route-limited) | `application_runtime.cpp` continues stubbed on the STAGED route; the REAL-DALVIK route dispatches onCreate for real (dooz/TheXTech/microtimer live evidence) |
| 2 | APP-002 Handler drain discards runnables | CONFIRMED (staged route) | `"[EXECUTE] Runnable id=... (run() not yet wired to engine)"` at `application_runtime.cpp:408`; real-dalvik route drains via the F100-IDLEDRAIN compose pump — PENDING staged-route wiring |
| 3 | APP-003 generic lifecycle simulated | PARTIAL (route-limited) | `execute_lifecycle()` pushes event names only (staged); the real-dalvik route runs real onStart/onResume DEX dispatch (`dalvik_engine.cpp` fragment lifecycle 9146-9176) |
| 4 | APP-004 lifecycle records mislabeled STUBBED | CONFIRMED (staged route) | same file region; bookkeeping does not satisfy the real-dalvik execution gates |
| 5 | APP-005 Telegram synthetic click campaign | CONFIRMED (staged route) | `application_runtime.cpp` clickable-search block; opt-in fixture quarantine PENDING (real-dalvik route never synthesizes clicks — the dooz tap is coordinate-based) |
| 6 | APP-006 Telegram forced Fragment lifecycle | CONFIRMED (staged route) | IntroActivity/gotNextPage fixed-iteration block; generic FragmentManager lifecycle exists on the real-dalvik route |
| 7 | APP-007 fabricated LoginActivity fallback | CONFIRMED (staged route) | direct LoginActivity allocation fallback present |
| 8 | APP-008 class-substring input selection | PARTIAL | coordinate → dispatchTouchEvent path is the production acceptance path (dooz tap 875,1823; ttt grid taps; gmdice reroll); the class-substring face remains as a labeled diagnostic |
| 9 | APP-009 text injection bypasses TextWatcher | CONFIRMED | `dalvik_engine.cpp:20942` "If the View has registered TextWatchers, they would be triggered here" — dispatch still TODO |
| 10 | APP-010 256-node attach cap | PENDING-VERIFY | the cited ZIP line numbers predate main; current attach traversal cap needs exact re-derivation before a patch |
| 11 | INPUT-001 hit rect ignores rotation | CONFIRMED | no rotation term in the touch_dispatcher hit transform; rides the VIS-001 matrix wave below |
| 12 | INPUT-002 local-transform-only hit test | PARTIAL | F-NEW-408 (CONT-99 T2) transformed hit-test law is landed; full ancestor-matrix composition = the VIS-001/002 shared work |
| 13 | INPUT-003 100000×100000 fallback bounds | CONFIRMED | `touch_dispatcher.cpp:68` `nw = (nw < 0) ? 100000 : nw` |
| 14 | INPUT-004 GestureDetector fling precedence | CONFIRMED | `gesture_detector_shadow.cpp` `was_in_tap_region` disjunction unparenthesized |
| 15 | SCROLL-001 Scroller PPI hard-coded 420 | CONFIRMED | `scroller_shadow.h` comment pins 420 dpi device |
| 16 | SCROLL-002 diagonal fling full-vector per axis | CONFIRMED | `scroller_shadow.h:118` `sqrt(vx²+vy²)` applied to each axis |
| 17 | ANIM-001 animator duration/startDelay zero | CONFIRMED | setters accepted, values not stored |
| 18 | ANIM-002 animated fraction/value frozen | CONFIRMED | same state family |
| 19 | ANIM-003 listeners never invoked | CONFIRMED | `animator_shadow.cpp:14` header lists addListener/addUpdateListener as stored-no-dispatch |
| 20 | ANIM-004 AnimatorSet no-op | CONFIRMED | play/playTogether/setChildAnimator accepted-not-stored (`animator_shadow.cpp:121`) |
| 21 | GL-001 onSurfaceCreated failure = success | CONFIRMED | `dalvik_engine.cpp` glSurfaceCreated committed regardless of invoke() result |
| 22 | GL-002 onSurfaceChanged cached on failure | CONFIRMED | glLastW/glLastH written regardless |
| 23 | GL-003 onDrawFrame failure ignored | CONFIRMED | returns true unconditionally |
| 24 | GL-004 RENDERMODE_WHEN_DIRTY unconsumed | CONFIRMED | `gl_surface_shadow.cpp` stores glRenderMode; no frame-pump consumer |
| 25 | GL-005 requestRender no-op | CONFIRMED | same file |
| 26 | GL-006 queueEvent overwrites (no FIFO) | CONFIRMED | single glQueuedEvent field |
| 27 | GL-007 EGL factories merely stored | CONFIRMED | chooser/factory/wrapper callbacks not invoked |
| 28 | GL-008 SurfaceHolder setFixedSize/format no-op | CONFIRMED | `gl_surface_shadow.cpp` setFixedSize stub |
| 29 | GL-009 z-order flags ignored | CONFIRMED | `surface_view_shadow.cpp:36-37` setZOrderOnTop/MediaOverlay accepted-no-op |
| 30 | GL-010 glGetError constant NO_ERROR | CONFIRMED | `gl_surface_shadow.cpp:1144` `handled_int(0)`; eglGetError constant 0x3000 |
| 31 | GL-011 marshalling rejects long/object arrays | CONFIRMED | read_array_elems terminal branch |
| 32 | GL-012 direct-buffer missing-capacity write | CONFIRMED | gl_view_mirror_write `dcap==0 \|\| o<dcap` bound-drop |
| 33 | WEB-001 createObjectURL constant | CONFIRMED | `webview_engine.cpp` Blob/URL.createObjectURL stub family |
| 34 | WEB-002 readAsDataURL no-op | CONFIRMED | same file |
| 35 | WEB-003 Worker unsupported-throw | CONFIRMED | same file |
| 36 | WEB-004 WebAudio graph inert | CONFIRMED | createOscillator/Gain/BufferSource shared no-op node |
| 37 | WEB-005 captureStream broken tracks | CONFIRMED | same file |
| 38 | WEB-006 media element promises inert | CONFIRMED | media clock not wired to a PCM sink |
| 39 | WEB-007 history nav no-op | CONFIRMED | pushState/replaceState/back/forward stubs |
| 40 | WEB-008 setLineDash/isPointInPath fake | CONFIRMED | `webview_engine.cpp:1713` setLineDash ignores pattern |
| 41 | WEB-009 clip() rect-collapse | CONFIRMED | canvas2d clip bounding-rect reduction |
| 42 | WEB-010 strokeText offset fillText | CONFIRMED | `canvas2d.cpp:471` stroke_text |
| 43 | WEB-011 text transform baseline-only | CONFIRMED | same region |
| 44 | WEB-012 silent media stubs | CONFIRMED | capability reporting absent |
| 45 | AUDIO-001 SoundPool ignores volume/loop/rate | CONFIRMED | `audio_engine.cpp` stream marked PLAYING only |
| 46 | AUDIO-002 AudioTrack discards PCM | CONFIRMED | frame counter increments, `data` ignored |
| 47 | AUDIO-003 MediaPlayer clock without sink | CONFIRMED | state machine without a connected mixer |
| 48 | RES-001 shape/selector backgrounds dropped | CONFIRMED | layout_inflater returns false for unresolved shape/selector drawables |
| 49 | RES-002 drawable state not interaction-linked | CONFIRMED | no pressed/focused/selected propagation after RES-001 lands |
| 50 | RES-003 animator XML → generic ValueAnimator | CONFIRMED | `animator_shadow.cpp` allocates unparsed ValueAnimator |"""

BODY_582 = """# GP — S222 wave receipt: the four new comments processed line-by-line (50-row disposition table + the S222-A exception-honesty/density laws landed + the text-cache storm root decoded at the DEX level)

**Reviewed HEAD:** `eff78882` (pushed 2026-11-12; binary `cc97e334981a4bb1`). This receipt disposes of comment `6812887007` (the 50 source-grounded blockers), comment `6812985391` (VIS-001..006 + the S221 dooz evidence critique), and the two integration counterparts on #583 (`6812887432`, `6812986803`). Every claim below was re-checked against current main before this post (the phantom-assertion protocol applies to our own receipts).

## 1. IMPLEMENTED — the S222-A wave (three laws, live A/B evidence)

1. **CONTAINED NESTED INVOKE (exception-honesty law).** The baseline rerun (dooz, `s222_baseline`) proved **47 of 54 APP-BOUNDARY process-death records were OUR OWN S221 measure bridge's `Lt4;.z` calls** throwing `requestLookaheadRemeasure cannot be called on a node outside LookaheadScope` — at `depth=2, caller_pc=0`, a top-level runtime-injected nested invoke that harmed ZERO app frames. T61 law: a runtime artifact must never masquerade as app behavior. `contained_invoke_` now stops that unwind at the nested-invoke bottom (`[S222-CONTAINED-EXC]`), leaving the APP-BOUNDARY metric for real app escapes only. Live A/B: APP-BOUNDARY **54 → 7 (waveA) → 0 (waveC/C2)**.
2. **F-023b framework-object materialization defaults.** The ISE diagnostic printed `InlineDensity(density=2.625000, fontScale=0.000000)` — the density half correct, the **fontScale half zero** because the app's Compose `LocalDensity` read a `new-instance`-materialized `Configuration` whose `fontScale` was still raw heap-zero (the F-023 v1 seeding only covered the `get_or_create_singleton` path). `execute_new_instance` now seeds the AOSP `setToDefaults()` face (fontScale=1.0, densityDpi=420, orientation, screenLayout) + the DisplayMetrics device identity — the ONE device identity law on EVERY materialization path.
3. **Measure-bridge cadence law (the complete-render config).** The S222-A decode + the wave matrix:
   - once-per-node bridge (S221): ISE storm 5,860–12,514 across runs, wall ~250 s/14 frames;
   - drain-every-window without re-marks (`s222_waveF`): storm persists (12,514) — the pending set does not contain the text nodes;
   - **per-frame mark+drain (`MINIANDROID_S222_FRAME_BRIDGE=1`, waves C/C2/D): ISE storm → 0 AND APP-BOUNDARY → 0** — the AOSP "measure must precede draw on EVERY traversal" order actually enforced; the cost is interpreter wall (~95 s/frame at -O2 — recorded as a performance item, not a correctness one), so the default stays the S221 cadence and the complete-render config is env-selected for dedicated render runs.

**Regression:** FULL 6-PIN GATE ALL HOLD byte-exact on `cc97e334981a4bb1` (bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 identical / microtimer `b39665f6` 0-uncaught / ttt `7354c1b2` ×3) — the S222-A laws are byte-inert where the pins live. `make test-all` **27/27**.

## 2. TESTED — the DEX-level decode the VIS comment demanded ("instrument the actual cache class's density-field writes")

Static decode of the pinned dooz DEX (sha16 `299eab21ac8b3c61`), all greps re-run:

- the ISE thrower face is **`Lnt1;.Q(Lgl0;)V` @0xEE and `Lnt1;.e(Let0;Lxs0;J)Ldt0;`** — the throw fires when the cached layout holder `Lyu0;.n:Ltw1;` is null;
- the REAL `MultiParagraphLayoutCache` is **`Lv31;`** — `l:J` = the packed density field, `s:J` = the 2-bit/op history register (the S221 decode confirmed: `0x5555…` = 32× markDirtyDensity; live faces `history=61` and `history=245`);
- the `InlineDensity` toString packing law (**`Lsg0;.b(J)Ljava/lang/String;` @0x128b48, disassembled**): **HIGH 32 bits = density, LOW 32 = fontScale** — so `InlineDensity(0.000000, 0.000000)` = packed `0L` = the virgin cache state, and the (2.625, 0.0) face = a real density with the fontScale-zero producer (fixed by F-023b);
- the layout-result holder **`Ltw1;` (a=Lsw1;, b=Lwu0;, c:J=packed density)** materializes only from the paragraph-layout completion (live probe `[S222-TW1]`: exactly **2** materializations per run — caller `Lyu0;.f pc=16`) while the draw phase demands it thousands of times: **the storm is measure-before-draw starvation, not a density-value corruption** (the density value faces are now proven correct post-F-023b: the dominant message face is `InlineDensity(2.625000, fontScale=1.000000)` — 5,418→7,477 occurrences across A/B);
- the density packer callers traced live (`[S222-PACK-S]`): `Lsg0;.<clinit>` (Unspecified) + `Lyu0;.d pc=14` (the layout input store) — no hidden zero-density producer remains in the packer path.

## 3. OBSERVED — the 50-row disposition table (comment `6812887007`)

All 50 rows re-verified against current main (greps below are exact):

""" + TABLE_50 + """

## 4. OBSERVED — VIS-001..006 (comment `6812985391`)

- VIS-001 (axis-aligned scale, no rotation): CONFIRMED — `execution_engine.cpp` renders scale as resized rect; rotation not rasterized. The fix rides the RenderNodeContext wave (see #583 receipt): per-task composed affine + inverse consumed by raster, clip, hit-test, and GL targeting.
- VIS-002 (scroll clip = culling rect only, no pixel clip; zero-scroll contributes no clip): CONFIRMED as described; part of the same clip-chain wave.
- VIS-003 (clipChildren/clipToPadding absent from ViewNode): CONFIRMED — no such fields on the current ViewNode.
- VIS-004 (GLSurfaceView second geometry formula): CONFIRMED — ancestor translation+scroll accumulate landed, scale/rotation/pivot missing.
- VIS-005 (GL composited after ViewTree, alpha=255 overwrite): CONFIRMED — `stage_gl_surfaces()` after `stage_render_frame_impl()`; z-ordered compositor frame graph PENDING (the single largest open item).
- VIS-006 (GL present ≠ app-owned draw): ACKNOWLEDGED — the frame-truth verifier (S220) already rejects draw-event-free frames; GL call-tag provenance PENDING.

None of these were closed with a guessed patch this wave: per the comment's own demand, the fix must be ONE shared geometry contract, and that contract is the next implementation wave (RenderNodeContext), not a per-defect hotfix.

## 5. PENDING / BLOCKED — honest remainder

- The 50-row table: rows 2,3,5,6,7,10,11,12 carry route-limited or partial dispositions — the fix order follows the #583 integration assignment (event/lifecycle engine → geometry contract → animation/scroll → GL → WebView/audio → resources). Nothing in the table was closed by a fake screenshot or a synthetic click.
- The complete-render config cost: the per-frame bridge makes the interpreter honest-but-slow (~95 s/frame). The performance lever (GP-PERF class): the drain walks the real tree through the interpreter; batching the measure pipeline (or native fast-pathing the measure interpreter loop) is the recorded next item — correctness first, then speed.
- dooz `a0fae907` (launch face) still holds byte-exact; the post-NewGame board face needs the per-frame-bridge run to complete within the wall budget (waveD reached frame 5/14 at ~95 s/frame before the harness timeout; the C2 run reached 281M instructions with the draw chain FULL (first draw 2,922 ops, ISE 0, boundary 0) — the render chain is alive, the wall budget is the remaining constraint).

## 6. NEXT

1. RenderNodeContext implementation wave (VIS-001..005 as ONE contract).
2. INPUT-004 + SCROLL-001/002 + ANIM-001..004 as one animation/scroll batch with regression fixtures.
3. GL-001..003 truthful-callback-status batch (3 lines of state-commit discipline) + GL-010/011/012 marshalling/error batch.
4. The staged-route quarantine (APP-005/006/007) + the Handler dispatch wiring (APP-002).

— GP (main coder), S222; issues-only access, no contents written outside the canonical build/test closure.
"""

BODY_583 = """# GP — S222 integration receipt: the two integration comments executed (disposition table posted on #582, the shared-path wave landed, the app matrix honestly stated)

**Reviewed HEAD:** `eff78882` (binary `cc97e334981a4bb1`). Counterparts: comment `6812887432` (the 50-point integration assignment) and `6812986803` (the one geometry/compositor contract). The full 50-row disposition table + the S222-A law receipts are posted on #582 (this post carries the integration-specific parts).

## 1. Root integration order — what ran this wave

1. **Event/lifecycle engine:** the exception-honesty step happened FIRST because the baseline proved 47/54 "app deaths" were runtime-injected artifacts (the S221 bridge's own `Lt4;.z` calls). The `contained_invoke_` law + F-023b materialization defaults + the cadence law are the shared-path changes; the Telegram quarantine (APP-005/006/007) and the Handler dispatch wiring (APP-002) remain the named next event-engine items — the real-dalvik route already dispatches lifecycle/Handler work for real.
2. **Rendering/input geometry (the one contract):** the RenderNodeContext wave is OPEN, not closed — VIS-001..006 are all CONFIRMED on current main (per-row evidence on #582 §4). No isolated renderer lane was opened; the contract work is queued as the next implementation wave with the exact shared design from `6812986803` §2 (per-frame immutable context: composed local-to-device matrix + inverse, accumulated rect/path clip incl. clipChildren/clipToPadding + scroll viewport, alpha/elevation/sibling order, one consumer set for View/Canvas/GL/hit-test).
3. **Dooz Compose root (the §4 named item):** the S222 wave DECODED it to the class level (full receipt on #582 §2): the cache is `Lv31;` (l:J density, s:J history), the result holder is `Ltw1;`, the packing law is high-32=density/low-32=fontScale, the fontScale-zero producer was F-023b-fixed, and the storm is measure-before-draw starvation — the complete-render config (`MINIANDROID_S222_FRAME_BRIDGE=1`) answers **ISE=0 + APP-BOUNDARY=0** with the draw chain FULL (first draw 2,922 ops). The once-per-node bridge inside `dispatch_custom_view_draw` remains explicitly a partial mitigation per this comment; the cadence law records that honestly.
4. **Coder lanes:** the disposition table (on #582) is the lane map — INPUT/ANIM/SCROLL → the animation batch; GL-001..012 → the truthful-callback + marshalling batches; WEB/AUDIO/RES → per the assignment's lane 5/6. Each row carries the exact current-main evidence so a coder patch cannot re-derive or phantom-claim.

## 2. App matrix (honest)

| Target | State at `eff78882` |
|---|---|
| Dooz v23 | launch face pinned `a0fae907` byte-exact; post-NewGame: ISE storm 24k→0 (complete-render config), APP-BOUNDARY 54→0, draw chain alive (2,922-op first draw); the board-pixel face needs the per-frame run to fit the wall budget (performance item recorded) |
| TheXTech | launcher UI rendered (S220 isTaskRoot); Start Game → SDL gameplay loop still the frontier |
| ttt / gmdice / microtimer / bouncy / unote | 6-pin gate ALL HOLD byte-exact ×3 / ×2 determinism |
| Halma / Mines3D / MA Solitaire | not rerun this wave (lane work queued per the table) |

## 3. Proof gates

`make check-source-parity` + `make test-all` **27/27** + FULL 6-PIN GATE ALL HOLD byte-exact on `cc97e334981a4bb1` (receipt on #582 §1). CMake parity: GP583-BUILD-002/TEST-001 remain CONFIRMED-and-open (canonical-build unification is queued behind the correctness waves).

## 4. Next

1. RenderNodeContext wave (one contract, all consumers).
2. The animation/scroll + GL batches (rows 11–32) with fixtures in `make test-all`.
3. The staged-route quarantine + APP-002 wiring.
4. The complete-render run at an affordable wall cost (interpreter measure fast-path).

— GP (main coder), S222; issues-only access.
"""

if __name__ == "__main__":
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("582", "both"):
        post(582, BODY_582)
    if which in ("583", "both"):
        post(583, BODY_583)
