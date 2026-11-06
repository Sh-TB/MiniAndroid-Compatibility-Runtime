#!/usr/bin/env python3
"""S185: post THE SQLITE RULE as a GitHub issue so all Coders see the law."""
import subprocess, json, urllib.request, sys

out = subprocess.run(["git", "credential", "fill"],
    input="protocol=https\nhost=github.com\n\n",
    capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = None
for line in out.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    sys.exit("NO TOKEN")

HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "s185-sqlite-rule"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

BODY = """# THE SQLITE RULE (S185) — VEND, DON'T REWRITE

User directive 2026-11-06, now a standing law for **all Coders**. Full text: `docs/SQLITE_RULE.md` · applicability survey: `evidence/s185_sqlite_rule/S185_APPLICABILITY.md`.

> "100% of the tools exist as free open-source Android sources — whatever the app calls, bring the real thing in. The most important part is that the program FIRST fully loads. If it gets bulky, fine — once execution is complete we trace where everything loaded from and keep only the required roots."

## Four clauses

1. **VEND, DON'T REWRITE** — need a component? First move = find the real open-source implementation, build it for the host, load it. Hand-written shims/synthetic stubs are FORBIDDEN where a real library exists. Precedents: real sqlite3; real libGDX host-native rebuild (S183b: 398 JNI symbols, #11 uncaught 8→0, real freetype fonts, render loop live).
2. **LOAD-FIRST** — milestone 0 = full load with zero uncaught exceptions. Bulk is acceptable at this stage. Never optimize size before the load is real.
3. **TRACER, THEN PRUNE** — only after full load: trace actual file/path usage, keep required roots. Never prune blind (S183: that is how white screens happen).
4. **NOTHING BULKY IN GIT** — run dirs / logs / traces / built .so / vend source trees never in git. Scripts + pinned upstream URLs instead (fetch-if-missing). Evidence = verdict JSON + face JPG ≤100 KB. S185 enforcement: pack 139→82 MB, tree 260→163 MB, /tmp 860→59 MB, ~3 GB stale run dirs deleted.

## Per-blocker playbook (sqlite-law move per family)

| blocker | move | open-source vend |
|---|---|---|
| B1 bionic DT_NEEDED vs glibc dlopen | rebuild SAME upstream source for host | libGDX done; SDL2 (opensurge #70, thextech #58), gnubg #72, boxcars #76, mupdf #224 |
| B2 GL/EGL surface | software GL behind GLSurfaceView | **PortableGL** or **gl4es** (#225 p9, #222 stardroid, TG) |
| B3/B4 androidx clinit storms | port real androidx class from vendored sources jars | savedstate (18 titles) → lifecycle (14) → coordinatorlayout (13) → constraint (9) |
| B5 missing framework classes | port from AOSP / vend kotlin-reflect | Insets (#532 in flight) |
| B6 image assets decode flat (~14 B_STRUCTURED faces) | real decoder behind BitmapFactory | **stb_image** or libpng+libjpeg-turbo |
| B7 OpenSL ES audio | bridge to real host audio | **OpenAL soft** |

## Priority (max full-loads per work unit)

1. B6 real image decode (flips ~14 faces at once)
2. B2 PortableGL (whole GL game cluster)
3. B1 generalized rebuild recipe per native title
4. androidx ports by fan-out (54-title headroom)
5. B7 audio bridge

## Hard requirements

- No synthetic engine shim where a real library exists.
- No "loaded" claim without a full-load trace (uncaught = not loaded).
- No bulk in git; no pruning before the tracer has run.
- Every vend records: upstream URL, pinned revision, build script path, output .so names, JNI symbol count.

**This issue is the reference Coder 2–9 cite when applying the rule. Close only by user order.**
"""

def api(path, body, method="POST"):
    req = urllib.request.Request(f"https://api.github.com{path}",
        data=json.dumps(body).encode(), headers=HDRS, method=method)
    with urllib.request.urlopen(req) as r:
        return json.load(r)

iss = api(f"/repos/{REPO}/issues", {
    "title": "S185 — THE SQLITE RULE (standing law for all Coders): VEND, DON'T REWRITE · LOAD-FIRST · TRACER-THEN-PRUNE · NOTHING BULKY IN GIT",
    "body": BODY,
    "labels": ["compatibility", "open-source", "common-runtime"],
})
print(f"POSTED issue #{iss['number']}: {iss['html_url']}")
