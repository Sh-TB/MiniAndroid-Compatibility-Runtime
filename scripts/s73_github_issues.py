#!/usr/bin/env python3
"""s73_github_issues.py — S73 PART A: canonical GitHub execution ledger.
Creates missing labels + exactly ONE canonical [EXEC] issue per important
application (duplicate-checked against existing issues first).
Requires GH_TOKEN in the environment (never persisted to any file)."""
import json
import os
import sys
import time
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"
TOKEN = os.environ.get("GH_TOKEN")
if not TOKEN:
    print("GH_TOKEN missing", file=sys.stderr)
    sys.exit(1)


def api(method, path, body=None):
    req = urllib.request.Request(f"{API}{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as r:
            return json.load(r) if r.status != 204 else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:300]
        print(f"  ! {method} {path} -> {e.code}: {err}", file=sys.stderr)
        return {}


def main():
    # ---- 0. inventory existing issues (duplicate check)
    existing = api("GET", "/issues?state=all&per_page=100")
    titles = {i["title"] for i in existing if "pull_request" not in i}
    print(f"existing issues: {len(titles)}")

    # ---- 1. labels
    labels = {
        "execution": "0e8a16", "apk": "1d76db", "runtime": "5319e7",
        "rendering": "f9d0c4", "input": "fbca04",
        "state-change": "c2e0c6", "screenshot": "bfe5bf",
        "gameplay": "d4c5f9", "autonomous-gameplay": "006b75",
        "differential": "fef2c0", "regression": "e99695",
        "blocked": "b60205", "p0": "b60205", "p1": "d93f0b",
        "p2": "fbca04",
    }
    for name, color in labels.items():
        api("POST", "/labels", {"name": name, "color": color})
    print(f"labels ensured: {len(labels)}")

    # ---- 2. canonical issues
    LADDER = """### Current execution ladder
* [ ] Source identified
* [ ] APK reproducibly built
* [ ] APK loads
* [ ] Manifest parsed
* [ ] DEX parsed
* [ ] Application instantiated
* [ ] Activity created
* [ ] Lifecycle reaches expected state
* [ ] View hierarchy exists
* [ ] Measure/layout works
* [ ] First meaningful render
* [ ] Meaningful screenshot
* [ ] User input
* [ ] State change
* [ ] State change visible in screenshot
* [ ] 3-run reproducibility
* [ ] Regression corpus passes
* [ ] Evidence package complete
* [ ] Achievement promoted to canonical docs
* [ ] Completion criteria satisfied"""

    def issue(title, body, labels_, close=False):
        if title in titles:
            print(f"  reuse existing issue: {title}")
            return None
        r = api("POST", "/issues", {"title": title, "body": body,
                                    "labels": labels_})
        if r and "number" in r:
            print(f"  created #{r['number']}: {title}")
            if close:
                api("POST", f"/issues/{r['number']}/comments",
                    {"body": close})
                api("PATCH", f"/issues/{r['number']}", {"state": "closed"})
            return r["number"]
        return None

    created = {}

    # ------------------------------------------------ HelloWorld (DONE)
    created["helloworld"] = issue(
        "[EXEC] HelloWorld — APK Execution & Visual Proof",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: HelloWorldSelfAware (canonical control target)
* Package: `com.appliberated.helloworldselfaware` v1.1.0
* Source repository: github.com/Appliberated/HelloWorldSelfAware
* APK SHA256: `009b4671…` (external fixture, re-fetched + SHA-verified at S64)
* Build method: upstream release APK (external fixture)
* Registry ID: EXT-01
* Current MiniAndroid status: **DONE (documented completed state)**

### Historical status
* Previous claim: canonical control target; typography 9/9 + interaction 12/12
* Previous evidence: docs/evidence/GOLDEN_HELLOWORLD.md, helloworld_golden,
  hello_color_golden, EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md
* Previous known blocker: upstream repo deleted (404) — environmental only
* Previous relevant commits: S45/S54/S64 era

### Current execution ladder
* [x] Source identified
* [x] APK loads / manifest parsed / DEX parsed
* [x] Application instantiated / Activity created / lifecycle expected state
* [x] View hierarchy exists / measure+layout works
* [x] First meaningful render / meaningful screenshot
* [x] User input / state change visible in screenshot
* [x] 3-run reproducibility / regression corpus passes
* [x] Evidence package complete / promoted to canonical docs
* [x] Completion criteria satisfied

### Current blocker
* None (EXT-01/02 upstream-availability is environmental, fixture frozen)

### Evidence
* golden records + typography/interaction gates (G48)
* Status: **DONE**

### History
* 2026-09-21: S73 — canonical execution issue created documenting the
  completed state (per PART A: fully-proven apps document completion).""",
        ["execution", "apk", "runtime", "screenshot", "evidence"],
        close="""S73 CLOSING — 2026-09-21

Final status: DONE (documented completed state).
Completion criteria: full ladder satisfied at earlier campaigns and
revalidated at every HEAD since (golden records + G48 typography gates +
interaction gates; EXT fixture SHA-pinned).
Evidence paths: docs/evidence/GOLDEN_HELLOWORLD.md;
docs/evidence/helloworld_golden; docs/evidence/hello_color_golden;
docs/evidence/EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md.
State-change proof: interaction 12/12 checks (real input -> text/state).
Reproducibility: golden gates deterministic x3 (typography gates).
Regression: fixture remains in the 25-fixture pinned battery (25/25 at
S72-W4; re-run at S73 — see S73_REPORT).
Relevant commits: S45/S54/S64 era (recorded in evidence docs).
Canonical documentation: docs/ACHIEVEMENTS.md §3.0.""")
    time.sleep(0.3)

    # ------------------------------------------------ TicTacToe (DONE)
    created["tictactoe"] = issue(
        "[EXEC] TicTacToe — APK Execution & Gameplay Proof",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: TicTacToe (emmanuelmess)
* Package: `com.emmanuelmess.tictactoe` vc3
* Source repository: github.com/EmmanuelMess/TicTacToe (F-Droid)
* APK SHA256: `760fe5acf7b39435…`
* Build method: ECJ + D8 canonical recipe (golden fixture rebuild)
* Registry ID: corpus canonical
* Current MiniAndroid status: **DONE (documented completed state)**

### Historical status
* Previous claim: 9-click real chain, win state, x3 deterministic
* Previous evidence: docs/evidence/visual_forensics/tictactoe/ (initial/mid/
  win frames + metrics x3); TICTACTOE_STATUS.md (ALL PASS 8 groups)
* Previous known blocker: none open (F-120 Button gravity law IMPROVED it)
* Previous relevant commits: S51 golden; S66 visual proof; F-120 era

### Current execution ladder
* [x] Source identified / APK reproducibly built / loads / manifest / DEX
* [x] Application instantiated / Activity created / lifecycle expected
* [x] View hierarchy / measure+layout / meaningful render / screenshot
* [x] User input (9/9 clicks dispatched into real DEX listeners)
* [x] State change (X/O marks; 'X to move'→'O to move'→'X WINS')
* [x] State change visible in screenshot (4X+3O glyphs, >100 ink px each)
* [x] 3-run reproducibility (initial 613cfccc… / mid c6670948… / win
      2e80e8c0… byte-identical x3)
* [x] Regression corpus passes / evidence complete / docs promoted
* [x] Completion criteria satisfied

### Current blocker
* None

### Evidence
* screenshot: docs/evidence/visual_forensics/tictactoe/ (win frame
  2e80e8c0…; anti-diagonal win; end-of-game freeze frames 8/9 identical)
* Status: **DONE**

### History
* 2026-09-21: S73 — canonical execution issue created documenting the
  completed state.""",
        ["execution", "apk", "gameplay", "screenshot", "evidence"],
        close="""S73 CLOSING — 2026-09-21

Final status: DONE.
Completion criteria: real APK + real launch + real View + real input chain
(9/9 clicks into real DEX listeners) + real state machine (turns, win,
freeze) + meaningful screenshots x3 byte-identical + regression clean.
Evidence paths: docs/evidence/TICTACTOE_STATUS.md;
docs/evidence/visual_forensics/tictactoe/.
Screenshot SHA: win frame 2e80e8c0… (x3 byte-identical; see metrics.json).
State-change proof: frame0 'X to move' -> frame1 'O to move' (one X) ->
frame7 'X WINS' (anti-diagonal).
Reproducibility: 3 runs byte-identical (initial/mid/win SHAs recorded).
Regression: TicTacToe remains in the pinned fixture battery (25/25 at
W4; re-run at S73 — see S73_REPORT).
Relevant commits: F-120 (Button gravity) improved mark centering; zero
regressions at every rerun.
Canonical documentation: docs/ACHIEVEMENTS.md (S66 records).""")
    time.sleep(0.3)

    # ------------------------------------------------ ConnectFour (DONE)
    created["connectfour"] = issue(
        "[EXEC] ConnectFour — APK Execution & Gameplay Proof",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: Connect Four (golden fixture)
* Package: fixture `connectfour_golden` (canonical toolchain build)
* Source repository: in-repo golden fixture (ECJ + D8 canonical recipe)
* APK SHA256: pinned in fixture docs (S51 era)
* Build method: real toolchain (ECJ + D8)
* Registry ID: fixture battery
* Current MiniAndroid status: **DONE (documented completed state)**

### Historical status
* Previous claim: L3 AGENT-PLAYABLE — 24-step schema, real hash chain
* Previous evidence: docs/evidence/solved/S51_AGENT_C4.json (24-step:
  observation/detected_state/chosen_action/input/prev-hash/new-hash/
  state_changed; 22/24 real state changes; win at step 22 on diagonal
  (0,3),(1,4),(2,5),(3,6); gameOver frozen tail)
* Previous known blocker: none (fixture doc error already corrected:
  real win at click 22, not 24)
* Previous relevant commits: S51 era

### Current execution ladder
* [x] Source identified / APK reproducibly built / loads / manifest / DEX
* [x] Application instantiated / Activity created / lifecycle expected
* [x] View hierarchy / measure+layout / meaningful render / screenshot
* [x] User input (24-step agent schema, real input each step)
* [x] State change (22/24 steps with real prev->new hash transitions)
* [x] State change visible in screenshot (board fills; win state)
* [x] 3-run reproducibility / battery passes (94/94 era)
* [x] Evidence package complete / docs promoted / criteria satisfied

### Current blocker
* None

### Evidence
* trace: docs/evidence/solved/S51_AGENT_C4.json (continuous hash chain)
* Status: **DONE**

### History
* 2026-09-21: S73 — canonical execution issue created documenting the
  completed state.""",
        ["execution", "apk", "gameplay", "state-change", "evidence"],
        close="""S73 CLOSING — 2026-09-21

Final status: DONE.
Completion criteria: agent-playable multi-step gameplay with real state
hashes — 24-step schema, 22/24 real state changes, win at step 22,
frozen game-over tail.
Evidence paths: docs/evidence/solved/S51_AGENT_C4.json;
validate_connectfour_golden.sh 8/8.
State-change proof: continuous prev-hash/new-hash chain (S51 record).
Reproducibility: golden validator deterministic (battery 94/94 x3 era).
Regression: ConnectFour remains in the pinned fixture battery; re-run at
S73 — see S73_REPORT.
Relevant commits: S51 era.
Canonical documentation: docs/history/campaign-reports/S51_FINAL_REPORT.md
§F (corrected win-at-22 record).""")
    time.sleep(0.3)

    # ------------------------------------------------ Snake (S73 flagship)
    created["snake"] = issue(
        "[EXEC] AndroidGameSnake — Autonomous Gameplay Proof",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: AndroidGameSnake (real-time grid snake)
* Package: `zhangman.github.snake` v1.0 vc1
* Source repository: github.com/zhangman523/AndroidGameSnake @ b4968c39
* APK SHA256: `54cf48a9…`
* Build method: aapt2 8.13.2 / ECJ 3.33.0 / D8 8.13.23 canonical recipe
* Registry ID: S72-W4 target game
* Current MiniAndroid status: **OBSERVED → autonomous gameplay achieved
  (S73)** — SCREENSHOT-PROVEN (S72-W4) + AUTONOMOUS-PLAYED (S73)

### Historical status
* Previous claim: screenshot-proven steering chain (START → Thread game
  loop → direction taps steer cell-by-cell), det x3 (pixel sha
  1a419545419deb3a), commit b84961e6
* Previous evidence: docs/evidence/s72_w4_snake/ + docs/foundation/S72_WAVE4.md
* Previous known blocker: none open (F-148/F-149/F-150 closed for it)
* Previous relevant commits: b84961e6

### Current execution ladder (S73 update)
* [x] Source identified / APK reproducibly built / loads / manifest / DEX
* [x] Application instantiated / Activity created / lifecycle expected
* [x] View hierarchy / measure+layout / meaningful render / screenshot
* [x] User input — 23 scheduled taps through the canonical TouchDispatcher
      DOWN/UP law pipeline (`--tap x,y@frame`; F-117 scheduled-input
      extension)
* [x] State change (snake advances 1 cell/frame; turns; food capture)
* [x] State change visible in screenshot (per-frame snake/food pixel cells)
* [x] 3-run reproducibility (per-frame PNG sha equality across 3 fresh
      full runs; 90 frames each)
* [x] Regression corpus passes (see S73_REPORT)
* [x] Evidence package complete (docs/evidence/s73_snake_autoplay/)
* [ ] Achievement promoted to canonical docs (in progress, S73)
* [x] Completion criteria satisfied (C1/C2: 88 moves, 22 turns, 1 food
      capture, growth 3→4, no state injection, GIF + trace + 3 runs)

### Current blocker
* None for the autonomous objective. Honest observations: the app WRAPS
  at walls ((19,10)→(0,10) observed; no wall death); restart via START
  after game-over NOT observed (possible Dialog-based restart path —
  not exercised; game-over triggered by engineered self-collision).

### Evidence
* screenshots: docs/evidence/s73_snake_autoplay/run_01/frames/ (90 frames)
* screenshot SHA256: per-frame in gameplay_trace.json + SHA256SUMS
* trace: gameplay_trace.json (C5 schema: run_id/frame/input/
  observed_snake/observed_food/head/direction/state_hash/
  screenshot_sha256/event)
* state transition: START-growth tick (frame 2), food capture (frame 34,
  len 3→4, food (0,0)→(9,0) respawn), game-over (frame 94, self-collision)
* frame metrics: autoplay_summary.json + determinism_proof.json
* reproducibility: 3/3 IDENTICAL (90/90 frames byte-identical x3 runs)
* regression: fixtures 25/25 + corpus re-run (S73_REPORT)
* GIF: snake_autoplay.gif (real output frames, 50% scale, 250ms/frame)

### Status
**OBSERVED** (autonomous gameplay chain proven end-to-end)

### History
* 2026-09-21: S73 — issue created; autonomous controller (vision =
  rendered-frame pixels only; actuator = scheduled real taps) achieved
  88 moves / 22 turns / 1 food capture; 3-run byte-identical; C4 probes:
  reverse-guard held, WRAP law discovered, self-collision game-over,
  restart-not-observed (honest).""",
        ["execution", "apk", "gameplay", "autonomous-gameplay",
         "state-change", "screenshot", "evidence"])
    time.sleep(0.3)

    # ------------------------------------------------ Dooz (OPEN/BLOCKED)
    created["dooz"] = issue(
        "[EXEC] Dooz — Runtime/UI Completion",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: Dooz (Tic Tac Toe, Compose) v18 + v23
* Package: `io.github.yamin8000.dooz` (v23: `299eab21…`, v18: `d81292cd…`)
* Source repository: github.com/yamin8000/Dooz (F-Droid)
* APK SHA256: v23 `299eab21ac8b3c61…` / v23 toplevel variant in corpus
* Build method: upstream release APK (F-Droid)
* Registry ID: corpus canonical (dooz_23_toplevel)
* Current MiniAndroid status: **BLOCKED (F-146, F-147; visual frontier
  F-145)** — honest, unchanged by S73

### Historical status
* Previous claim: 197 px placeholder (S66) → 23472 px real content +
  det x3 (S72-W3, F-141 family closure)
* Previous evidence: docs/evidence/s55_dooz/, s56_dooz23/, s57_dooz23/,
  visual_forensics/dooz/; S72_WAVE3.md
* Previous known blocker: F-146 `g8.a@569 → ur.e(J)` null receiver;
  F-147 `onCreate@228 → ViewGroup.getChildAt` on null; F-145
  screenshot/UI surface frontier
* Previous relevant commits: 048b0e31 (F-141 family + F-146/F-147
  registered), b84961e6 (re-probed UNCHANGED)

### Current execution ladder
* [x] Source identified / APK available / loads / manifest parsed / DEX parsed
* [x] Application instantiated / Activity created (create chain closed via
      F-105/F-106 era laws; Hilt factory resolves)
* [x] Lifecycle reaches onCreate/onStart/onResume dispatch
* [x] View hierarchy exists (Compose composition runs)
* [ ] Measure/layout works (F-147: ViewGroup.getChildAt on null @228)
* [x] First meaningful render — PARTIAL (23472 px real content, x3 det)
* [ ] Meaningful screenshot (F-145 surface frontier)
* [ ] User input / state change visible in screenshot
* [x] 3-run reproducibility (dooz det x3 byte-identical, S72-W3 + S73
      re-verified)
* [x] Regression corpus passes (no regression across S72/S73 changes)
* [ ] Evidence package complete / completion criteria

### Current blocker
* First divergence: F-146 `g8.a@569 → ur.e(J)` null receiver;
  F-147 `onCreate@228 → ViewGroup.getChildAt` null
* Method/Class/Caller/Callee: as registered (registry F-146/F-147)
* Upstream/source law: Compose UI pruning/metadata family (F-146);
  ViewGroup child-access contract (F-147)
* Status: **BLOCKED** — preserved as Dooz-independent state; NOT folded
  into any other wave's success

### Evidence
* screenshot: 23472 px real content (deterministic x3; pixel sha
  0e334abe1b10b592 at S73 re-run)
* Status: **BLOCKED**

### History
* 2026-09-21: S73 — canonical execution issue created; F-141 stays CLOSED
  (not reopened); F-146/F-147/F-145 recorded as the exact open frontier;
  S73 re-run confirms 23472 px x3 byte-identical (unchanged).""",
        ["execution", "runtime", "rendering", "blocked", "p1", "evidence"])
    time.sleep(0.3)

    # ------------------------------------------------ Unote (OPEN/PARTIAL)
    created["unote"] = issue(
        "[EXEC] Unote — Runtime/UI Completion",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: Unote (notes app)
* Package: `app.varlorg.unote` vc30
* Source repository: github.com/varlorg/unote (F-Droid)
* APK SHA256: canonical corpus pin
* Build method: upstream release APK (F-Droid)
* Registry ID: corpus canonical
* Current MiniAndroid status: **PARTIAL** — real themed UI renders;
  interaction ladder open

### Historical status
* Previous claim: 11.4% garbage-backed (W1) → 231120 px real theme
  recovered honestly (F-141f getTheme/resolveAttribute law, S72-W3)
* Previous evidence: run/s72_w3 corpus era; S72_WAVE3.md
* Previous known blocker: pre-F-141 silent null theme; now renders
* Previous relevant commits: 048b0e31

### Current execution ladder
* [x] Source identified / APK available / loads / manifest / DEX
* [x] Application instantiated / Activity created / lifecycle expected
* [x] View hierarchy / measure+layout / meaningful render (231120 px)
* [x] Meaningful screenshot (deterministic, corpus canonical recipe)
* [ ] User input / state change visible in screenshot (open)
* [x] 3-run reproducibility (pixel-stable across reruns)
* [x] Regression corpus passes (F-141f improved it; zero regressions)
* [ ] Evidence package complete / completion criteria

### Current blocker
* First divergence: not yet driven — interaction unprobed at S73
* Status: **PARTIAL**

### Evidence
* screenshot: corpus run frames (S73 re-run; current binary)
* Status: **PARTIAL**

### History
* 2026-09-21: S73 — canonical execution issue created; render status
  honest (real themed UI); input/state ladder open.""",
        ["execution", "runtime", "rendering", "evidence"])
    time.sleep(0.3)

    # ------------------------------------------------ Telegram (OPEN/PARTIAL)
    created["telegram"] = issue(
        "[EXEC] Telegram — Runtime Compatibility",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: Telegram v12 (vc70389, 12.10.1)
* Package: `org.telegram.messenger`
* Source repository: telegram.org (upstream APK; not in corpus for legal
  hygiene — heavy-compat stress target)
* APK SHA256: `f5e1192725772960…`
* Build method: upstream release APK
* Registry ID: heavy-compat target
* Current MiniAndroid status: **PARTIAL** (historical checkpoint-M proven;
  current-HEAD re-execution NOT re-run at S73 — honest
  HISTORICAL-CLAIM-UNVERIFIED-AT-CURRENT-HEAD marker)

### Historical status
* Previous claim: EXP-064..071 chain — real login image by pixels,
  multi-DEX semantic audit, generic View inheritance + click dispatch,
  resource resolution + AXML + WebP drawables, phone-number injection +
  Next click, Login → SMS code page transition (CHECKPOINT_M PROVEN)
* Previous evidence: issues #1–#8 (closed records), EXP071_* docs,
  docs/evidence/mc4_telegram/
* Previous known blocker: rlottie/Lottie surface; deeper init (540s real
  init, no full frame)
* Previous relevant commits: S36–S71 era

### Current execution ladder
* [x] Source identified / APK available / loads / manifest / DEX (multi-DEX)
* [x] Application instantiated (MultiDexApplication chain fires, F-137 era)
* [x] Activity created (LoginActivity chain; OutlineTextContainerView)
* [ ] Lifecycle reaches expected state (full init exceeds budget)
* [x] View hierarchy exists (PhoneView rendered; real WebP images)
* [x] Measure/layout works (login UI laid out at checkpoint M)
* [x] First meaningful render / meaningful screenshot (login UI pixels)
* [x] User input (phone number injected; Next clicked)
* [x] State change visible in screenshot (page transition to SMS code)
* [ ] 3-run reproducibility at CURRENT HEAD (not re-run at S73)
* [ ] Regression corpus passes at CURRENT HEAD for the telegram path
* [ ] Evidence package complete / completion criteria

### Current blocker
* First divergence: full-init budget (540s wall at vc70389 era)
* Status: **PARTIAL**

### Evidence
* screenshot: docs/evidence/mc4_telegram/ (EXP-064..071 records)
* Status: **PARTIAL**

### History
* 2026-09-21: S73 — canonical execution issue created consolidating the
  closed experiment issues #1–#8 as history; current-HEAD re-execution
  queued (not claimed).""",
        ["execution", "runtime", "evidence"])
    time.sleep(0.3)

    # ------------------------------------------------ GMDice (OPEN)
    created["gmdice"] = issue(
        "[EXEC] GMDice — APK Execution & Visual Proof",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: GM Dice (dice roller)
* Package: `de.duenndns.gmdice` vc8
* Source repository: github.com/nnUyi/gmdice? (F-Droid de.duenndns.gmdice)
* APK SHA256: canonical corpus pin
* Build method: upstream release APK (F-Droid)
* Registry ID: corpus canonical
* Current MiniAndroid status: **PARTIAL** — runtime-playable battery +
  tap goldens (L2-era records); real UI renders; deterministic x3

### Historical status
* Previous claim: battery + tap goldens pass; getResources x5 converted
  STUBBED→IMPLEMENTED via F-137 ancestry-dispatch law (S71)
* Previous evidence: s71_live traces; S70/S71 reports
* Previous known blocker: none pinned beyond ladder completion
* Previous relevant commits: 1271b869 (F-137)

### Current execution ladder
* [x] Source identified / APK available / loads / manifest / DEX
* [x] Application instantiated / Activity created / lifecycle expected
* [x] View hierarchy / measure+layout / meaningful render
* [x] Meaningful screenshot (deterministic)
* [x] User input (tap goldens, earlier campaigns)
* [ ] State change visible in screenshot (roll transition re-proven at
      current HEAD — open)
* [x] 3-run reproducibility (det x3, S73 re-verified)
* [x] Regression corpus passes
* [ ] Evidence package complete / completion criteria

### Current blocker
* None pinned; ladder completion open
* Status: **PARTIAL**

### Evidence
* screenshot: S73 corpus run (current binary)
* Status: **PARTIAL**

### History
* 2026-09-21: S73 — canonical execution issue created.""",
        ["execution", "gameplay", "evidence"])
    time.sleep(0.3)

    # ------------------------------------------------ MicroTimer (OPEN)
    created["microtimer"] = issue(
        "[EXEC] MicroTimer — APK Execution & Visual Proof",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: MicroTimer
* Package: `dubrowgn.microtimer` vc8
* Source repository: github.com/dubrowgn/MicroTimer (F-Droid)
* APK SHA256: canonical corpus pin
* Build method: upstream release APK (F-Droid)
* Registry ID: corpus canonical
* Current MiniAndroid status: **PARTIAL** — L7-era record (keypad UI;
  click → 00:00:00 timer display appears); deterministic on current binary

### Historical status
* Previous claim: SUCCESS L7 (keypad; click → timer display)
* Previous evidence: S51-era corpus table (docs/ACHIEVEMENTS.md §table)
* Previous known blocker: re-post storm law (64-iteration cap) documented
  for the virtual-clock family (M3 law, general runtime)
* Previous relevant commits: M3 F-ROOM-CHAIN era

### Current execution ladder
* [x] Source identified / APK available / loads / manifest / DEX
* [x] Application instantiated / Activity created / lifecycle expected
* [x] View hierarchy / measure+layout / meaningful render / screenshot
* [x] User input (click → display appears, historical)
* [ ] State change visible in screenshot re-proven at current HEAD (open)
* [x] 3-run reproducibility (det x3, S73 re-verified)
* [x] Regression corpus passes
* [ ] Evidence package complete / completion criteria

### Current blocker
* None pinned; ladder completion open
* Status: **PARTIAL**

### Evidence
* screenshot: S73 corpus run (current binary)
* Status: **PARTIAL**

### History
* 2026-09-21: S73 — canonical execution issue created.""",
        ["execution", "evidence"])
    time.sleep(0.3)

    # ------------------------------------------------ FishRings (OPEN)
    created["fishrings"] = issue(
        "[EXEC] FishRings — APK Execution & Gameplay Proof",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: FishRings (Velbazhd Software LLC)
* Package: `eu.veldsoft.fish.rings` v1.23 vc6
* Source repository: github.com/VelbazhdSoftwareLLC/FishRingsForAndroid
  @ dc3807e
* APK SHA256: `14d7dd80…`
* Build method: upstream release APK (F-Droid)
* Registry ID: corpus canonical
* Current MiniAndroid status: **PARTIAL** — S10 PROVEN (splash → Timer →
  GameActivity → 44-view board → 3 real taps → state change 2,072,211 →
  483,395 → 478,169 → 7,347 px, det x3); F-142 board law fixed S72-W2

### Historical status
* Previous claim: S10 repeatable chain + det x3; F-142
  RelativeLayout MarginLayoutParams + ImageView onMeasure cap laws
* Previous evidence: docs/evidence/s65_spotlight/S65_REPORT.md §4;
  s71/s72 wave docs
* Previous known blocker: none pinned beyond ladder completion
* Previous relevant commits: f8d5e1e2 (F-142), 1271b869 (F-119)

### Current execution ladder
* [x] Source identified / APK available / loads / manifest / DEX
* [x] Application instantiated / Activity created (F-118 ctor law)
* [x] Lifecycle expected (Splash Timer → GameActivity)
* [x] View hierarchy / measure+layout / meaningful render / screenshot
* [x] User input (3 real taps → GameActivity$5/$6 handlers)
* [x] State change visible in screenshot (frame SHA sequence)
* [x] 3-run reproducibility (598ddbfa… byte-identical chain, det x3)
* [x] Regression corpus passes
* [ ] Full gameplay completion (catch-the-fish loop to game end) — open
* [ ] Evidence package complete / completion criteria

### Current blocker
* None pinned; gameplay completion open
* Status: **PARTIAL**

### Evidence
* screenshot: s65/s71 era frames + S73 corpus re-run
* Status: **PARTIAL**

### History
* 2026-09-21: S73 — canonical execution issue created.""",
        ["execution", "gameplay", "evidence"])
    time.sleep(0.3)

    # ------------------------------------------------ TriPeaks (BLOCKED)
    created["tripeaks"] = issue(
        "[EXEC] TriPeaks — APK Execution & Visual Proof",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: TriPeaks Solitaire
* Package: `eu.veldsoft.tri.peaks` v1.2.1 vc4
* Source repository: github.com/VelbazhdSoftwareLLC/TriPeaksSolitaireForAndroid
  @ 62f3609
* APK SHA256: `52272ae6…`
* Build method: upstream release APK (F-Droid)
* Registry ID: corpus canonical
* Current MiniAndroid status: **BLOCKED (visual: R-NEW-388 layout
  geometry family; app-own OBJECT-IDENTITY stopper on deeper play)**

### Historical status
* Previous claim: S7 source-first (splash → lobby 205,638 px → New Game
  tap → GameActivity onCreate 7905 insns → board 2,073,600 px; 52 cards
  bound post-F-118; det x3)
* Previous evidence: docs/evidence/s65_spotlight/S65_REPORT.md §3;
  R-NEW-388 registration (all 31 card ImageViews painted at (0,0))
* Previous known blocker: R-NEW-388 (RL anchor geometry vs
  measured_left wiring) + OBJECT-IDENTITY family (S8+ play)
* Previous relevant commits: b88e09d9, 1271b869

### Current execution ladder
* [x] Source identified / APK available / loads / manifest / DEX
* [x] Application instantiated / Activity created / lifecycle expected
* [x] View hierarchy exists (31 cards + labels)
* [ ] Measure/layout works correctly (R-NEW-388: painted at (0,0))
* [x] First meaningful render (board pixels exist — geometry wrong)
* [ ] Meaningful screenshot (honest PARTIAL visual)
* [x] User input (card tap CLICK dispatched to real handler)
* [ ] State change visible in correct layout (blocked by R-NEW-388)
* [x] 3-run reproducibility (det x3)
* [x] Regression corpus passes
* [ ] Evidence package complete / completion criteria

### Current blocker
* First divergence: card ImageView geometry (0,0) stacking
* Class/Method: activity_game.xml RL anchor idiom vs engine layout replay
* Upstream/source law: RelativeLayout measured_left wiring
* Status: **BLOCKED**

### Evidence
* screenshot: s65/s66 frames (board painted; geometry wrong)
* Status: **BLOCKED**

### History
* 2026-09-21: S73 — canonical execution issue created; R-NEW-388 remains
  the honest visual blocker (demoted from foundation list at S71 after
  re-measure — app-specific).""",
        ["execution", "rendering", "blocked", "evidence"])
    time.sleep(0.3)

    # ------------------------------------------------ Bouncy (OPEN)
    created["bouncy"] = issue(
        "[EXEC] Bouncy — APK Execution & Visual Proof",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: Bouncy (ball physics)
* Package: `com.dozingcatsoftware.bouncy`
* Source repository: github.com/dozingcat/Bouncy (F-Droid)
* APK SHA256: corpus pin (S53-era SHA mismatch noted)
* Build method: upstream release APK (F-Droid)
* Registry ID: corpus canonical
* Current MiniAndroid status: **PARTIAL** — L6 PROVEN (6/6 clicks into
  real DEX XML-onClick handlers; two distinct UI states, frame SHAs
  4219c511… → 52e4ddac…); honest: NOT L7 (no multi-round game-loop proof)

### Historical status
* Previous claim: L6 PROVEN (S62)
* Previous evidence: run/s62_bouncy_l6/; docs/evidence/s62_r381/
* Previous known blocker: L7 multi-round loop interaction unproven
* Previous relevant commits: S62 era

### Current execution ladder
* [x] Source identified / APK available / loads / manifest / DEX
* [x] Application instantiated / Activity created / lifecycle expected
* [x] View hierarchy / measure+layout / meaningful render / screenshot
* [x] User input (6/6 real clicks into real handlers)
* [x] State change visible in screenshot (two-state SHA pair)
* [ ] Physics game-loop state evolution (multi-round) — open
* [x] 3-run reproducibility
* [x] Regression corpus passes (pixel dashboard 100% era)
* [ ] Evidence package complete / completion criteria

### Current blocker
* None pinned; L7 game-loop interaction open
* Status: **PARTIAL**

### Evidence
* screenshot: docs/evidence/s62_r381/bouncy_frame*.png + SHA256SUMS
* Status: **PARTIAL**

### History
* 2026-09-21: S73 — canonical execution issue created.""",
        ["execution", "gameplay", "evidence"])
    time.sleep(0.3)

    # ------------------------------------------------ Stopwatch (BLOCKED)
    created["stopwatch"] = issue(
        "[EXEC] Stopwatch — Service-Launch Family",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: Simple Stopwatch
* Package: `com.github.muellerma.stopwatch` vc6
* Source repository: github.com/muellerma/Stopwatch (F-Droid)
* APK SHA256: `b3ec1a5ec24ce53b…` era pin
* Build method: upstream release APK (F-Droid)
* Registry ID: corpus canonical
* Current MiniAndroid status: **BLOCKED (by design)** — manifest has NO
  launchable Activity (QuickSettings Tile app); engine correctness
  verified via the service-launch family F-143

### Historical status
* Previous claim: L2 by design (no Activity); service-only manifest
  verified as app shape, not engine failure
* Previous evidence: S72-W1 dashboard; F-143 registration
* Previous known blocker: F-143 service-launch family (open, generic)
* Previous relevant commits: acad15fd

### Current execution ladder
* [x] Source identified / APK available / loads / manifest parsed
* [ ] Activity created — N/A (no launchable Activity in manifest; the
      app is a Tile/service app — this is the app's design, not a gap)
* [ ] UI ladder — N/A by design
* [x] Registry honest classification (BLOCKED-by-design documented)
* [ ] F-143 service-launch family law (generic, open)

### Current blocker
* First divergence: no launchable-activity entry (app design)
* Upstream/source law: QuickSettings TileService lifecycle
* Status: **BLOCKED (by design)**

### Evidence
* manifest record in S72-W1 dashboard; corpus re-run rc recorded
* Status: **BLOCKED**

### History
* 2026-09-21: S73 — canonical execution issue created.""",
        ["execution", "blocked", "evidence"])
    time.sleep(0.3)

    # ------------------------------------------------ OPMT (OPEN)
    created["opmt"] = issue(
        "[EXEC] OPMT — APK Execution & Visual Proof",
        f"""## MiniAndroid APK Execution Campaign

### Application
* Name: OPMT (Online/Offline multiplayer tic-tac-toe family)
* Package: `one.scarecrow.games.OPMT` v0.1.2 vc1
* Source repository: github.com/20Nick/OPMT @ 3240c4cf
* APK SHA256: `4f91e380…`
* Build method: upstream release APK + androidx compile-stub + staged
  resources (siggen law)
* Registry ID: corpus canonical
* Current MiniAndroid status: **PARTIAL** — S6 chain-to-GameActivity
  source-first (menu 214,144 px real strings; tap → lambda →
  startActivity → GameActivity onCreate 1756 insns → 461,211 px diff;
  det x3). Honest stopper: app-own nextInt(0) IOOBE via empty move list
  (OBJECT-IDENTITY family)

### Historical status
* Previous claim: S6 EXECUTED+OBSERVED; rc=1 deterministic stopper
* Previous evidence: docs/evidence/s65_spotlight/S65_REPORT.md §5
* Previous known blocker: OBJECT-IDENTITY family (S7+)
* Previous relevant commits: 1271b869 (F-118/F-119 era)

### Current execution ladder
* [x] Source identified / APK available / loads / manifest / DEX
* [x] Application instantiated / Activity created / lifecycle expected
* [x] View hierarchy / measure+layout / meaningful render / screenshot
* [x] User input (menu tap → real lambda handler)
* [x] State change (menu → GameActivity frame diff 461,211 px)
* [ ] In-game interaction loop (blocked by app-own IOOBE stopper)
* [x] 3-run reproducibility (det x3)
* [x] Regression corpus passes
* [ ] Evidence package complete / completion criteria

### Current blocker
* First divergence: app-own nextInt(0) on empty move list (the APP's
  own logic reaches an edge case under the current input state)
* Upstream/source law: OBJECT-IDENTITY family (open)
* Status: **PARTIAL**

### Evidence
* screenshot: opmt_* frames (s65 era) + S73 corpus re-run
* Status: **PARTIAL**

### History
* 2026-09-21: S73 — canonical execution issue created.""",
        ["execution", "gameplay", "evidence"])

    print(json.dumps(created, indent=1))


if __name__ == "__main__":
    main()
