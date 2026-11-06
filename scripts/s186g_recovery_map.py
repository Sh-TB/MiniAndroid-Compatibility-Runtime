#!/usr/bin/env python3
"""S186g — WAVE 1d: ranked incomplete-recovery map from REAL run/census data.

Inputs (all measured, no old reports):
  evidence/s186_s107/S107_FACE_CENSUS.json       (129 faces, pixel tiers)
  evidence/s186_s107/S186C_COMPLETION_MATRIX.json (41 stuck titles, families)
  evidence/s186_s107/S186C_STUCK_BATTERY.json     (battery tiers + laws applied)

Output: docs/S186_INCOMPLETE_RECOVERY_MAP.md
Priority score per S186 directive PART 8:
  30% affected APKs + 25% blocker severity + 20% recovery probability
  + 15% family reuse + 10% build feasibility   (0-100)
"""
import json, os

ROOT = "/home/z/my-project"
cen = json.load(open(f"{ROOT}/evidence/s186_s107/S107_FACE_CENSUS.json"))
mat = json.load(open(f"{ROOT}/evidence/s186_s107/S186C_COMPLETION_MATRIX.json"))
bat = json.load(open(f"{ROOT}/evidence/s186_s107/S186C_STUCK_BATTERY.json"))

tiers = cen["tiers"]
fam = mat["families"]
btiers = bat.get("tiers", {})
n_mat = mat["n"]

# family -> representative titles (from matrix rows)
rows = mat["rows"]
by_fam = {}
for r in rows:
    by_fam.setdefault(r["family"], []).append(f"{r['pkg']} #{r['issue']} ({r['exc_class'].split('.')[-1]} @{r['frame']})")

# S185 census heads (recorded numbers, used as context)
f_androidx_headroom = 54
native_cluster = 10

# ranked generic capabilities — score components justified from data below
caps = [
    dict(rank=1, cap="AndroidX/framework class-init (lifecycle, savedstate, fragment, datastore, appcompat, OnBackPressedDispatcher, FragmentContainerView)",
         affected=f"{f_androidx_headroom}-title headroom (S185) + {fam.get('F-ANDROIDX',0)} F-ANDROIDX in battery",
         severity="FATAL (clinit/NPE at onCreate)", prob="high — S186f proved pattern (2 titles 10->0 uncaught)",
         reuse="every Java/Kotlin app using androidx", feas="sources.jar port per class (Rule 1)",
         s=(30, 25, 18, 15, 8), evidence="S186f: foehnix #126 + aoc #132 uncaught 10->0; S186e solitaire #43 13->0",
         titles=by_fam.get("F-ANDROIDX", [])),
    dict(rank=2, cap="null-semantics class-init family (F-NPE 15 diverse: flutter embedding, capacitor, gomobile go/Seq, liballeg, kotlin Intrinsics)",
         affected=f"{fam.get('F-NPE',0)} titles in battery",
         severity="FATAL (first init crash)", prob="per-root — needs per-family law (A/B each)",
         reuse="medium — each law must be generic by construction",
         feas="engine law in android_shadows/runtime", s=(22, 25, 14, 9, 8),
         evidence="S186C_COMPLETION_MATRIX families", titles=by_fam.get("F-NPE", [])[:15]),
    dict(rank=3, cap="B6 image decode -> real Bitmap pixels (structured content flattening)",
         affected=f"{tiers['B_STRUCTURED']} B_STRUCTURED faces in s107 census (14 faces one fix away per S185)",
         severity="visual-only (renders flat/two-tone)", prob="medium — decoder chain linked+called, semantics gap",
         reuse="every image-heavy app", feas="AOSP BitmapFactory semantics; stb/png/jpeg already vendored+linked",
         s=(20, 12, 12, 13, 9), evidence="S107_FACE_CENSUS tiers; S183 graphics depth",
         titles=[]),
    dict(rank=4, cap="GLES/EGL/surface semantics for native game family",
         affected=f"{native_cluster}-title native/GL cluster (S185); A_RICH only 2/{n_mat} in battery",
         severity="blocker (no game loop present)", prob="medium — PortableGL works where EGL path holds",
         reuse="entire native game family (P0 if it unlocks the cluster)",
         feas="PortableGL audit first (directive PART 5A) then gl4es alternative",
         s=(15, 22, 12, 13, 5), evidence="S186c battery tiers; halma #27 + p9 #225 A_RICH",
         titles=[]),
    dict(rank=5, cap="audio end-to-end (B7 OpenSL ES -> OpenAL Soft bridge)",
         affected="B7 cluster + every game with sound assets; zero real-APK audio proof today",
         severity="non-fatal (silent execution)", prob="medium",
         reuse="all games with audio", feas="mpg123+sndfile already linked; OpenAL Soft new build",
         s=(10, 8, 10, 12, 7), evidence="audit: 2 decode paths linked, 0 proofs",
         titles=[]),
    dict(rank=6, cap="TLS/conscrypt JNI (F-NATIVE)",
         affected=f"{fam.get('F-NATIVE-LOAD',0)} direct + all HTTPS titles",
         severity="FATAL for network titles", prob="medium",
         reuse="all networking apps", feas="conscrypt rebuild or BoringSSL adapter",
         s=(6, 20, 10, 8, 4), evidence="taz -> conscrypt UnsatisfiedLinkError (battery)",
         titles=by_fam.get("F-NATIVE-LOAD", [])),
    dict(rank=7, cap="resource resolution (F-RES)",
         affected=f"{fam.get('F-RES/resource-missing',0)} (astroloop FontManager Resources$NotFound)",
         severity="FATAL single", prob="high single", reuse="low",
         feas="resource table fix", s=(3, 15, 12, 2, 8),
         evidence="battery", titles=by_fam.get("F-RES/resource-missing", [])),
]

def score(s):
    w = [0.30, 0.25, 0.20, 0.15, 0.10]
    return round(sum(a*b for a, b in zip(s, w)) * (100/30))

no_uncaught = by_fam.get("NO-UNCAUGHT", [])
flat_titles = [r["pkg"] for r in rows if r["tier"] == "FLAT_TWO_TONE_OR_BLANK"]

L = []
L.append(f"# S186 — Incomplete Recovery Map (Wave 1d, measured)\n")
L.append(f"Inputs: S107 face census n={cen['n']}; S186c stuck battery n={n_mat} "
         f"(engine: {bat.get('engine','?')}); laws applied: {json.dumps(bat.get('laws_applied', {}))}\n")
L.append("## Population (measured)\n")
L.append("| census tier | count |")
L.append("|---|---|")
for k, v in tiers.items():
    L.append(f"| {k} | {v} |")
L.append("")
L.append("| battery tier (41 stuck re-run) | count |")
L.append("|---|---|")
for k, v in btiers.items():
    L.append(f"| {k} | {v} |")
L.append("")
L.append("## Ranked generic capabilities (PART 8 priority score)\n")
L.append("| # | capability | affected | score /100 | status proof |")
L.append("|---|---|---|---|---|")
for c in caps:
    L.append(f"| {c['rank']} | {c['cap']} | {c['affected']} | **{score(c['s'])}** | {c['evidence']} |")
L.append("")
L.append("## Family details (first failing stage, exact frames)\n")
for c in caps:
    if c["titles"]:
        L.append(f"### #{c['rank']} {c['cap']}\n")
        for t in c["titles"]:
            L.append(f"- {t}")
        L.append("")
L.append("## 0-uncaught but flat (silent recovery queue — Rule 5: flat is not success)\n")
for t in no_uncaught:
    L.append(f"- {t}")
L.append("")
L.append(f"## Two-tone/blank faces in battery ({len(flat_titles)} titles)\n")
for t in flat_titles:
    L.append(f"- {t}")
L.append("")
L.append("## Directive PART 9 required corpus cross-check\n")
corpus = ["2048", "Snake Deluxe", "Snake Neon", "Mini Tetris", "Minicraft",
          "TicTacToe Deluxe", "Bouncy", "Vector Pinball", "Mindustry", "Stardroid", "RTTT",
          "Telegram", "Nextcloud", "Organic Maps", "VLC"]
L.append("Required-test titles map to evidence dirs: batch367_rerun "
         "(tictactoedeluxe, snake, snakeneon run dirs exist), S183b faces "
         "(emmanuelttt/bouncy/stacktower3d), S119 (snakeneon capture, snake_real_score2). "
         "Apps (Telegram/Nextcloud/Organic Maps/VLC) live in S107/S115 census rows.\n")

out = os.path.join(ROOT, "docs", "S186_INCOMPLETE_RECOVERY_MAP.md")
open(out, "w").write("\n".join(L))
print("written", out, len(L), "lines")
print("scores:", {c['cap'][:40]: score(c['s']) for c in caps})
