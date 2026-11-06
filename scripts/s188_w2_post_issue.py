#!/usr/bin/env python3
"""S188 W2: post the route-map + per-app requirements tracker issue (English)."""
import json
import subprocess

TOKEN = subprocess.run(
    ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
    capture_output=True, text=True).stdout
TOKEN = [l.split("=", 1)[1] for l in TOKEN.splitlines()
         if l.startswith("password=")][0]
API = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"


def post(path, payload):
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", "-H", f"Authorization: token {TOKEN}",
         "-H", "Content-Type: application/json", "-d", json.dumps(payload),
         f"{API}/{path}"], capture_output=True, text=True)
    return json.loads(r.stdout)


BODY = """# [S188 W2] ROUTE MAP + PER-APP REQUIREMENTS — what each title actually needs

**Directive:** user order (S188 W2) — at startup the runtime must determine
WHICH ALLEY (route) an app takes. A Java/View app must NEVER pass through the
HTML5 alley. An app that plays MKV must go through the MKV alley — forcing it
through MP4 is a wrong alley and can never be credited. All S188 rules
(#556 / #542) apply.

## 1. What was delivered (code, not reports)

1. **`tools/s188_route_classifier.py`** — static route profiler. Scans DEX
   descriptors, native libs, assets, manifest. Emits
   `reports/apk_routes/<pkg>.json` (schema `S188_APK_ROUTE_PROFILE_V1`):
   routes detected (evidence per route), PRIMARY route, FORBIDDEN routes
   (alley law), substitutions forbidden (MKV≠MP4 law), required capabilities.
2. **`src/runtime/route_law.{h,cpp}`** — the runtime now loads the route
   profile at `run` startup and prints:
   ```
   [ROUTE] DECISION pkg=com.qwde.ccm primary=GODOT routes=GODOT+WEBVIEW_NODE+VIEW forbidden=LIBGDX+SDL
   [ROUTE] REQUIRED_CAPS pkg=com.qwde.ccm caps=GODOT_ENGINE_SUPPORT,WEBVIEW_ENGINE,SQLITE_VEND
   ```
   WebView engagement at runtime is observed against the profile:
   `ROUTE_VIOLATION` (profile forbids) / `ROUTE_SURPRISE` (profile didn't
   predict — classifier must be revised; static analysis is honest, never
   silently corrected). `UNOBSERVED != PASS`.
3. **W2 first-renders battery** — 11 open-source titles (simple clock apps +
   very simple games), S186i protocol (fresh store, real-dalvik, trace,
   screenshot tier): `evidence/s188_w2/`.

## 2. CORPUS ROUTE MAP (41 titles — never one universal pipeline)

| Primary route | Titles | Recovery alley |
|---|---|---|
| COMPOSE | 13 | AndroidComposeView → Composition → LayoutNode → Draw |
| VIEW | 11 | Activity → ViewTree → Measure/Layout → Canvas |
| WEBVIEW_HTML5_PACKAGED | 5 | real HTML5 alley (QuickJS+DOM+canvas) — the LEGITIMATE HTML5 apps |
| FLUTTER | 4 | FlutterJNI → engine bootstrap → flutter_assets |
| GODOT | 2 | GodotApp bootstrap → libgodot_android.so (native engine) |
| LIBGDX | 2 | NativeLoader → JNI → EGL/GLES (both already A_RICH) |
| SDL | 1 | SDLActivity → native lib → event loop |
| NATIVE_GAME_ENGINE (Allegro) | 1 | surgeengine → liballegro |
| WEBVIEW_NODE | 1 | app instantiates WebView as component |
| MEDIA | 1 | ships playable content (assets) |

Ground-truth validation: BOTH A_RICH titles (app.halma, se.tube42.p9.android)
classify LIBGDX. GODOT discovery: `com.qwde.ccm` (a chess clock!) and
`com.simondalvai.ball2box` are Godot engine games — their recovery alley is
NOT View fixes.

Corpus capability demand: WEBVIEW_ENGINE 27, SQLITE_VEND 24, APPCOMPAT 22,
MEDIA_DEMUX_PER_ASSET 17, ADAPTER_RECYCLE 17, COMPOSE_RUNTIME 13,
FLUTTER_ENGINE 4, GODOT_ENGINE_SUPPORT 2.

## 3. W2 FIRST-RENDERS RESULTS (11 titles, current integrated binary)

| Title | Route | W2 tier | S186i | Verdict |
|---|---|---|---|---|
| cos.premy.mines | WEBVIEW | B_STRUCTURED (686 colors) | B_STRUCTURED | HOLD |
| eu.quelltext.memory | WEBVIEW_HTML5_PACKAGED | B_STRUCTURED (256) | B_STRUCTURED | HOLD |
| crypto.o0o0o0o0o.games.blackjack | WEBVIEW_HTML5_PACKAGED | B_STRUCTURED (65) | B_STRUCTURED | HOLD |
| eu.veldsoft.no.thanks | COMPOSE | **FLAT** | B_STRUCTURED | **REGRESSION** |
| tibarj.tranquilstopwatch | VIEW | FLAT | FLAT | hold (divergence found) |
| com.justdeax.composeStopwatch | COMPOSE | FLAT | FLAT | hold (divergence found) |
| com.sidhant.queens | FLUTTER | FLAT | FLAT | hold (divergence found) |
| com.simondalvai.ball2box | GODOT | FLAT | FLAT | hold (divergence found) |
| com.qwde.ccm | GODOT | FLAT | FLAT | hold |
| xyz.deepdaikon.quinb | FLUTTER | FLAT | FLAT | hold |
| org.secuso.privacyfriendlybattleship | VIEW | FLAT | FLAT | hold |

### REGRESSION (blocks — S188 §14)
`eu.veldsoft.no.thanks` B_STRUCTURED → FLAT, **3/3 independent runs** at
current HEAD (not variance). Regression window = S186i binary → HEAD; prime
suspect = F-NEW-491 theme-attr law chain (touches ?attr hops consumed by
Compose/appcompat theming). S186i A/B binary no longer on disk (sandbox
recycle) — **Coder task: rebuild S186i-HEAD binary, A/B no.thanks, flip
F-NEW-491 to confirm first divergence.** Golden anchors bouncy/unote are NOT
affected (verified byte-exact in W1).

## 4. WHAT EACH FLAT TITLE NEEDS (first-divergence, from real runs)

Concrete, actionable — each line is the FIRST wall the app hit:

| Title | First divergence | Needs |
|---|---|---|
| com.sidhant.queens (Flutter) | `CopyOnWriteArraySet.<init>` REC-MISS inside `FlutterJNI.<init>`; RuntimeException unwind h0/j | 1) `java.util.concurrent.CopyOnWriteArraySet` constructors; 2) Flutter JNI bootstrap chain |
| xyz.deepdaikon.quinb (Flutter) | same Flutter alley | same as queens (shared root candidate — requires its own evidence per S188 §11) |
| com.bupkis.tirailleur (Flutter) | same alley | same |
| si.palcka.tarok (Flutter) | FlutterLoader disallowed-flag throw (W1 census) | Flutter engine flag handling |
| com.simondalvai.ball2box (Godot) | `java.lang.Enum.<init>` REC-MISS in `org.godotengine.godot.xr.XRMode.<init>`; GodotApp getWindow OK | 1) `Enum.<init>` reflection-safe ctor; 2) Godot native engine loading (libgodot_android.so) |
| com.qwde.ccm (Godot) | same engine alley | same as ball2box |
| tibarj.tranquilstopwatch (VIEW) | NPE at `NavigationView.<init>` ← `FragmentContainerView.<init>` ← s1/n0.g | Material `NavigationView` constructor (same root as de.tobiasbielefeld.solitaire census — needs per-app evidence) |
| com.justdeax.composeStopwatch (COMPOSE) | CNFE `androidx.compose.ui.platform.AndroidCompositionLocals_androidKt`; CNFE kotlin.reflect ReflectionFactoryImpl | Compose class resolution gap (multi-dex indexing?) + kotlin.reflect |
| org.secuso.privacyfriendlybattleship (VIEW) | flat, 165 colors at S186i — needs its own FDT graph | per Phase B FDT on this APK |

**Coders: pick a line, fix the wall, re-run, post face JPG. No app-specific
branches; fix the shared class with contract tests (S188 §8).**

## 5. LAWS (binding, from #556)

- One shared capability registry; many routes; per-app evidence record.
- Never credit a route because ANOTHER route in the same APK succeeded.
- Never classify an APK broken for not using an irrelevant subsystem.
- FORBIDDEN routes are encoded in profiles; substitutions (MKV→MP4) are
  never creditable.
- Static profile ≠ runtime observation (UNOBSERVED != PASS). ROUTE_SURPRISE
  lines mean: revise the classifier, don't hide the fact.

## 6. Deliverables

- `reports/apk_routes/<pkg>.json` (41 profiles + _SUMMARY.json)
- `evidence/s188_w2/W2_FIRST_RENDERS.json`, `W2_ROUTE_MATRIX.json`, face JPGs
- `scripts/s188_w2_first_renders.py` (re-runnable per-title)
- Runtime: `src/runtime/route_law.{h,cpp}` wired in `cmd_run` + WebView paint
  path; build verified (`make -j2`, "Build complete").

**Next milestone unchanged (#541): ≥5 small apps with REAL app-owned graphics
on ONE integrated binary. Mines/memory/blackjack hold B_STRUCTURED; the first
FLAT→B promotion candidates are listed in §4.**
"""

issue = post("issues", {
    "title": "[S188 W2] Route map + per-app requirements: which alley each title takes, what each needs",
    "body": BODY,
    "labels": [],
})
print("issue:", issue.get("number"), issue.get("html_url"))

comment = post("issues/556/comments", {
    "body": ("S188 W2 executed (user directive: alley law + first renders). "
             "Route classifier shipped (`tools/s188_route_classifier.py`), "
             "41 route profiles committed (`reports/apk_routes/`), runtime now "
             "prints `[ROUTE] DECISION` at launch and logs ROUTE_VIOLATION/"
             "ROUTE_SURPRISE on WebView engagement (src/runtime/route_law.cpp). "
             "Corpus map: COMPOSE 13 / VIEW 11 / WEBVIEW_HTML5_PACKAGED 5 / "
             "FLUTTER 4 / GODOT 2 / LIBGDX 2 / SDL 1 / Allegro 1 / WEBVIEW_NODE 1 "
             "/ MEDIA 1. W2 battery on 11 open-source clocks+games: mines/memory/"
             "blackjack hold B_STRUCTURED; 1 regression found "
             "(eu.veldsoft.no.thanks, 3/3 runs, queued A/B); first-divergence "
             "needs per FLAT title documented. Full matrix + per-app "
             "requirements: see the [S188 W2] tracker issue. UNOBSERVED != PASS.")})
print("comment on 556:", comment.get("id"))
