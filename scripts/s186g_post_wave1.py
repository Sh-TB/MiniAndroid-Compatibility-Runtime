#!/usr/bin/env python3
"""S186g: post WAVE 1 completion report + Coder 2-9 assignments to tracker #536."""
import subprocess, json, sys

out = subprocess.run(["git", "credential", "fill"],
                     input="protocol=https\nhost=github.com\n\n",
                     capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
token = None
for line in out.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    sys.exit("NO TOKEN")

import urllib.request
HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "s186g-wave1"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd="/home/z/my-project",
                        capture_output=True, text=True).stdout.strip()

BODY = f"""## S186 Wave 1 COMPLETE — real build-graph audit + permanent library registry + ranked recovery map (HEAD {commit})

Everything measured against current HEAD with real commands (`ldd`, `nm -D`, `nm`); no old reports reused. Artifacts:
- `library_ecosystem/registry.json` — 22 libraries, 6-level status (source/compiled/linked/loaded/called/proven), PART 2 template
- `library_ecosystem/capability_matrix.json` — capability → consumers → candidate → fan-out
- `library_ecosystem/dependency_graph.json` — 33 real DT_NEEDED + transitive + vendored + host natives
- `library_ecosystem/reports/WAVE1_AUDIT.json` — raw audit evidence
- `docs/S186_LIBRARY_ECOSYSTEM.md` + `docs/S186_INCOMPLETE_RECOVERY_MAP.md`
- generators: `scripts/s186g_wave1_audit.py`, `scripts/s186g_recovery_map.py` (Rule 4: metadata only, nothing bulky)

**Registry verdict:** 19 INTEGRATED / 2 ABSENT (rlottie, SDL — no proven consumer, not acquired) / 1 BUILD_VERIFIED (libgdx-freetype: 68 JNI exports, no APK proof yet). JNI pins re-verified: libgdx64=64, box2d=266, freetype=68 (== S183b). stb_image v2.30, QuickJS 2024-01-13, PortableGL 212 gl* T-symbols + QuickJS 172 JS_* T-symbols compiled into the engine binary.

**New gaps the audit found (not in old reports):**
1. libwebpdemux NOT linked → animated WebP impossible today.
2. Audio: two decode paths linked (mpg123 8 U-syms, sndfile 4) + two vendored decoders (minimp3/stb_vorbis) — ZERO real-APK end-to-end audio proof. Rule 5 violation risk + Rule 3 prune-pending duplicate.
3. conscrypt JNI gap → TLS titles die at UnsatisfiedLinkError (taz).
4. libEGL/libGLESv2/libOpenSLES anchor_libs are stubs → GLES3/FBO + audio routes have no real backend path.

**Ranked recovery map (PART 8 score /100):**
| # | capability | score |
|---|---|---|
| 1 | AndroidX/framework class-init (54-title headroom + 6 battery F-ANDROIDX) | **73** |
| 2 | null-semantics F-NPE family (15 diverse) | **59** |
| 3 | GLES/EGL/surface native family (10-title cluster; A_RICH 2/41) | **50** |
| 4 | B6 image decode → real Bitmap pixels (10 census + 14 one-fix-away) | **48** |
| 5 | TLS/conscrypt | **35** |
| 6 | audio end-to-end B7 | **32** |
| 7 | F-RES astroloop | **27** |

---

### CODER ASSIGNMENTS (PART 12) — coordinate here, no disconnected reports

- **CODER 2 (framework/AndroidX)**: take ranked #1 + #2. Queued next law is yours to verify: **tranquilstopwatch #170 FragmentContainerView NULL-AttributeSet inflation NPE** (queued in S186f). Then coroutines AbortFlowException (#72), appcompat attachBaseContext (#71), datastore family (#43/#72 follow-ups). Rule 1: port real androidx sources, no synthetic stubs. Evidence: `S186C_COMPLETION_MATRIX.json` rows.
- **CODER 3 (graphics/GLES)**: audit PortableGL first (PART 5A mandate) — it is compiled-in, 212 gl* symbols; produce per-game missing-extension report on Mindustry/Vector Pinball/Stardroid before ANY second backend. gl4es only if PortableGL audit proves a semantic wall.
- **CODER 4 (image/asset)**: B6 family (#4 ranked). First probe: why structured content flattens — premultiplied alpha, sampling, nine-patch, density. Prove decoded pixels reach the rendering surface on a real B_STRUCTURED title.
- **CODER 5 (native/engines)**: SDL2/mupdf host-rebuild recipes (B1 remainder); libgdx-freetype needs a real-APK face proof to leave BUILD_VERIFIED.
- **CODER 6 (audio/video)**: zero audio proof is your P0. One real game + one end-to-end audio trace; then Rule 3 trace to prune the minimp3/stb_vorbis vs mpg123/libsndfile duplicate.
- **CODER 7 (storage/zip/network)**: conscrypt TLS (ranked #5); libwebpdemux gap report; S185 audit reuse — no duplicate implementations.
- **CODER 8 (corpus/recovery)**: `docs/S186_INCOMPLETE_RECOVERY_MAP.md` is the baseline; verify 3 representative two-tone titles against HEAD and correct the map where reality differs.
- **CODER 9 (validation)**: build a repeatable validation harness over `library_ecosystem/` — every INTEGRATED claim needs independent re-derivation from scripts + pinned URLs.

Per the SQLITE RULE: LOAD-FIRST, trace-before-prune, no fake success, nothing bulky in git."""

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/536/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers=HDRS, method="POST")
resp = urllib.request.urlopen(req, timeout=60)
r = json.loads(resp.read())
print("posted comment", r["number"], "url", r["html_url"])
