#!/usr/bin/env python3
"""T280 — the #707 reconciliation + knowledge-transfer comment."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def get_token():
    p = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise RuntimeError("no token")


TOKEN = get_token()
BODY = """# KODER-YAR-E-KOMAKI — T280 full reconciliation + 3 fixes landed + 2 new foundational findings

**Audit base:** remote `main` HEAD `69ebc96ca` (re-verified in-session; the audit's old base `344774e66` is 6 commits behind). **T280 commit `2bac3a082` pushed to main** (binary `2681b9d978b7b67e`, rebuilt from the pushed tree). Evidence: `evidence/t280/` (probe reports, law-test output, binary SHA).

## 1. Reconciliation table — every previous finding, current-main verified

| Finding | Status @ 69ebc96ca | Disposition @ 2bac3a082 |
|---|---|---|
| KA-KYK-028 Choreographer.getFrameTime ns-instead-of-ms (`choreographer_shadow.cpp:66`) | **CONFIRMED** (both getters grouped, same ns value) | **FIXED ON REMOTE MAIN** (`2bac3a082`): ms = ns/1e6; discriminating test in TEST_LAW (t280 battery asserts 1016 ms vs 1016666667 ns identity) |
| KA-KYK-029 RectF INT bridge (`ui_graphics.cpp:4368`) | **CONFIRMED + UPGRADED**: the cited code was DEAD (see 034); the LIVE copy in `dalvik_engine.cpp:59471` had the same defect — INT32-only reader over FLOAT32-stored fields → every real RectF.width() == 0 | **FIXED ON REMOTE MAIN**: live-path float split (RectF→float fields/float result; Rect→int), mirrored in the dead copy for parity |
| KA-KYK-030 isEmpty AND-vs-OR | **CONFIRMED** (live copy used `&&`; the F-NEW-442c comment MISQUOTES AOSP) | **FIXED ON REMOTE MAIN**: OR law, verified against frameworks/base Rect.java 2026-11-28 |
| KA-KYK-031 ArrayAdapter split-store (`dialog_shadow.cpp`) | **CONFIRMED** (ctor seeds `__ad_objects__`+items_; add/insert push items_ only; notifyDataSetChanged `handled_void()`; F-NEW-650 getView pass-through exists but mutation/notification unchanged) | **PENDING** (not repaired this pass — repair spec from the previous comment stands) |
| KA-KYK-032 TableRow layout_span | **CONFIRMED absent** (`layout_span`: 0 hits vs 2 `layout_columnSpan` in layout_inflater.cpp) | **PENDING** |
| KA-KYK-033 invoke-state leakage | **CONFIRMED** (forName exits ~2079/2141/2161/2201 + direct null-recv 1273 + virtual null-recv bypass the manual restore; brace-depth analysis, no enclosing lambda) | **FIXED ON REMOTE MAIN**: RAII `IsStaticRestore` guards in static/virtual/direct (the interface-handler F-023 pattern); law fixture queued — current discrimination is structural (guard covers EVERY exit) + full gate green |
| KA-007/KA-018 alpha draw consumer | **CONFIRMED absent** (0 alpha consumers in the draw TU) | **PENDING** (local-only claims remain unproven — see §3) |
| KA-008/KA-014 rotation draw + hit-test | **CONFIRMED absent** (0 refs in draw TU AND touch_dispatcher.cpp) | **PENDING** |
| KA-009 textStyle numeric/string mismatch | **PENDING** (partial supersession: Typeface C9-17 family laws landed since; end-to-end TextView draw consumer not re-verified) | **PENDING** |
| KA-KYK-035 (implicit) — audit citations vs live code | the previous pass audited `ui_graphics.cpp` line numbers that are **dead code** | **SUPERSEDED by 034** — all future bridge audits must cite `dalvik_engine.cpp`'s bridge_to_api |

## 2. NEW finding KA-KYK-034 | P0 | TWO bridge_to_api definitions; the whole domain chain is dead code

- `dalvik_engine.cpp:38672` (~54k lines, defined inside an anonymous namespace) and `dalvik_bridge.cpp:82` (with the domain chain: jdk → android_core → ui_graphics → app_runtime → io_lang) both define `DalvikExecutionEngine::bridge_to_api`. The linker keeps ONE; probes prove **the dalvik_engine.cpp copy wins**.
- Discriminating evidence (this session, forced-rebuild probes + `nm`): a probe at the TOP of `bridge_domain_ui_graphics` fires for RectF calls, probes at lines ~300/600/4370 of the same function NEVER fire, and the `[S186I-STUB]` tail print resolves to `dalvik_engine.cpp:93204`. `LOGIN-BRANCH` (io_lang) count = **0** across ALL production run logs checked (pfdicer/gmdice/pfludo T279+T280 runs).
- Consequence: **every law in `dalvik_bridge_domain_*.cpp` is unreachable on current main** (S232 Drawable.draw, F-NEW-563 MotionEvent getters as cited, LOGIN-BRANCH, …). The LIVE equivalents are inside the engine.cpp bridge (e.g., its own MotionEvent law at ~41661). Any Main Coder work routed into the domain chain lands in dead code.
- Repair options (Main Coder decision): (a) delete `dalvik_bridge.cpp`'s definition and move the genuinely-missing domain laws into the live bridge one by one (each with a probe proving reachability), or (b) make the domain chain the single definition and verify the engine.cpp copy's unique laws migrate. Either way: add an ODR/build-time guard (static_assert or link check) so this cannot recur.
- Interim mitigation applied: the T280 RectF/isEmpty fixes were placed in BOTH copies; the LIVE copy is what the new TEST_LAW battery exercises.

## 3. Integration-claim audit (unchanged verdict, re-verified today)

`913ae31b` (#702 alpha), `a04e8f30` (#703), `9de419c9` (#704 rotation), `976f97bc` (#713), `cc514d80` (#714), `156d9cc7` (#638) — **all NOT-REACHABLE** from remote main (`git cat-file -t` fails for every SHA); test files s642/s643/s644 absent from the tree. Every one of those issues' "local fix" claims stays **NOT INTEGRATED**; the underlying defects (alpha/rotation consumers) remain CONFIRMED-absent in current main.

## 4. Compose interaction deep audit (Mission A) — the input-bridge gap named precisely

Pipeline (verified live): tap coordinates → TouchDispatcher walk (`touch_dispatcher.cpp` touchable law incl. F-NEW-267 dispatchTouchEvent-override arm) → `AndroidComposeView.dispatchTouchEvent` (app DEX) → compose PointerInputEventProcessor → hitTest → modifier callbacks → recomposition → rf=COMPOSE renders. Rendering works; **the bridge is severed at stage 2**: the compose host view never materializes as a ViewShadow tree node, so coordinate dispatch has no compose target.

CIP-1 probe results (8 evidence-gated states, `scripts/t280_compose_probe.py`):

| Target | Ceiling | Earliest broken transition |
|---|---|---|
| **pfludo** | **PIXEL_CHANGE_OBSERVED** (full chain) | none — tap Skip → tutorial advances → MainActivity menu ("Play with own dice", 3 new faces) — a View-path interaction success |
| **pfdicer** | RECOMPOSITION_OBSERVED | tap 1 works (Okay → TutorialActivity.finish → MainActivity RESUMED, COMPOSE renders); **MainActivity content FrameLayout has kids=0** → tap 2 hits DrawerLayout (consumed=true) — compose host absent from the ViewShadow tree |
| **itsfrz** | NODE_DISCOVERED | tap dead, target=0: `NavHostFragment.O` NPE (`La4/o;.getValue` on null) unwinds the fragment drain **before onCreateView** → FragmentContainerView kids=0 — the same androidx-navigation family as janken's Navigator-attach frontier |

Compose versions: R8-stripped (no META-INF markers); pfdicer activity 1.8.0 → compose-ui ≈1.5–1.6.x; the engine's touch laws cite 1.6.7; the pipeline architecture is stable across the range.

**Proposed general repair (ranked)**: materialize the compose host (ComposeView/AndroidComposeView) as ViewShadow nodes in the dispatch tree at setContent/fragment-attach time (the DEX view-construction law already handles ordinary views — find why the compose host's addView is dropped), OR wire the compose render root into the TouchDispatcher walk as a synthetic dispatch target. Then the F-NEW-563 MotionEvent law (already live in the engine bridge) carries the event into the app's own DEX pipeline — no compose fabrication needed.

## 5. Regression gate (binary 2681b9d978b7b67e, all pushed-tree source)

f714 9/9 · lifecycle ALL · linear 24/24 · input_pipeline ALL · **t280_rectf_choreo 18/18** · golden anchors byte-identical: gmdice `3891679d` / bouncy `37326cb2` / pfdicer `31ffa499` / pfludo `21ea13e1`. Zero regressions.

## 6. Main Coder ordered queue (evidence-ranked)

1. **KA-KYK-034 dead-domain-chain reconciliation** (P0 architecture) — blocks every future bridge-law landing from being measurable.
2. **Compose host → ViewShadow tree** (P0/P1, unlocks itsfrz/pfdicer MainActivity interaction; needs the fragment-drain NPE fixed first for itsfrz).
3. **NavHostFragment.O `La4/o;.getValue` NPE** (shared with janken's Navigator-attach family).
4. KA-KYK-031 ArrayAdapter canonical backing + observer notify (P0 spec stands).
5. alpha/rotation consumers + KA-KYK-032 TableRow span (P1; local-only patches still not integrable).
6. pfludo: re-classify — the tutorial→menu interaction upgrades its R2 verdict evidence (menu face b8aa5f20 = real menu content; registry note queued).
"""


def main():
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/707/comments", method="POST",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "kyk-agent", "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, data=json.dumps({"body": BODY}).encode()))
    print("posted:", r["html_url"])


if __name__ == "__main__":
    main()
