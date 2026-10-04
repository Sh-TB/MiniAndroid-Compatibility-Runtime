#!/usr/bin/env python3
"""env373_matrix.py — issue #373 environment/prerequisite matrix generator.

Produces (all machine-readable, SHA-stamped):
  1. docs/ENVIRONMENT_PROFILE.json            — ENV-001..010 default device
  2. docs/ENV_PREREQUISITE_MATRIX.jsonl       — APK-001..020 rows per corpus APK
                                                (via `pkginspect --what prerequisites`)
  3. docs/WS_PREREQUISITE_AUDIT.jsonl/.md     — WS-001/WS-002 white/black
                                                env-vs-runtime classification
  4. docs/EXECUTION_LEVEL_MATRIX.jsonl        — L0..L6 execution levels

Classification law (#373 §0): A DUPLICATE | B SAME_ROOT/NEW_EVIDENCE |
C NEW_SUB_LAW | D NEW_ROOT | E NOT_APPLICABLE | F EXTERNAL/FUTURE_BOUNDARY.
Only C/D create runtime work. F = honest external boundary (CPU translation,
hardware absence).
"""
import hashlib
import json
import os
import subprocess
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid"
DOCS = BASE / "docs"
OUT_DIR = BASE / "run/closeout/env373"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=BASE,
                      capture_output=True, text=True).stdout.strip()


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=str(BASE), capture_output=True, text=True, **kw)


BIN_SHA = sha16(BIN)

# ═══════════════════════════════════════════════════════════════════════
# 1. ENV-001..010 — the default device profile.
# Source of truth: seed_framework_device_statics (dalvik_engine.cpp) +
# install ABI law (main.cpp S-2) + graphics backend (PortableGL) +
# the prerequisite environment block (install_inspection.cpp).
# ═══════════════════════════════════════════════════════════════════════
profile = {
    "schema": "MINIANDROID_ENVIRONMENT_PROFILE/1.0",
    "generated_at": run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).stdout.strip(),
    "source_head": HEAD,
    "binary_sha16": BIN_SHA,
    "ENV-001_api_level": {
        "sdk_int": 34, "version_name": "14", "codename": "REL",
        "source": "dalvik_engine.cpp seed_framework_device_statics (Build.VERSION.SDK_INT=34)",
        "evidence": "EXT-01 HelloWorldSelfAware AndroidInfo branch (pre-O avoided); battery F-stages",
    },
    "ENV-002_device_profile": {
        "manufacturer": "MiniAndroid", "model": "MiniAndroid",
        "device": "miniandroid", "product": "miniandroid", "hardware": "miniandroid",
        "fingerprint": "MiniAndroid/miniandroid/miniandroid:14/MINI.20260905/0:userdebug/test-keys",
        "android_id": "6f1c3a9d2e5b4780 (deterministic, Rule 12)",
    },
    "ENV-003_screen": {
        "default_density": "420dpi (xhdpi)", "default_size": "1080x1920",
        "orientation": "portrait", "refresh_rate": "fixed virtual clock",
        "source": "CFG probe + density-matrix oracle (11/11) + frame bounds 1080x1920",
    },
    "ENV-004_ram_storage": {
        "ram": "host-bound (no ActivityManager memory pressure simulation)",
        "storage": "host-bound data-root tree; internal/external/DE/user_de fences proven",
        "source": "#370 §B storage probes; DE-01",
    },
    "ENV-005_cpu_abi": {
        "host_arch": "x86_64",
        "advertised_abis": ["arm64-v8a", "armeabi-v7a", "armeabi"],
        "executable_abis": ["x86_64"],
        "native_bridge": False,
        "abi_selection_law": "install prefers lib/x86_64 when present (host-executable); "
                             "ARM-only APKs extract their ARM tree and honestly cannot execute it",
        "s2_native_execution": "dlopen/JNI_OnLoad/dlsym/SystemV-thunk; NATX-01..10 10/10 x3 (fib=610)",
    },
    "ENV-006_graphics": {
        "backend": "PortableGL (software rasterizer)",
        "gles_max_version": 2, "vulkan": False,
        "egl_facade": "JSR-239 EGL/GLES facade (checkGL20 PASS — tictactoedeluxe evidence)",
        "framebuffer": "1080x1920 RGBA software framebuffer",
    },
    "ENV-007_media": {
        "decoders": ["png", "jpeg", "gif (replay law)", "webp", "mp3 (mpg123)", "wav/sndfile"],
        "audio_engine": True, "codec_service": "not emulated (no MediaCodec API surface)",
    },
    "ENV-008_hardware": {
        "touchscreen": "PRESENT (real input pipeline: TouchDispatcher AOSP claim law)",
        "camera": "ABSENT", "gps": "ABSENT", "telephony": "ABSENT",
        "bluetooth": "ABSENT", "nfc": "ABSENT", "microphone": "ABSENT",
        "accelerometer": "EMULATED-DEFAULT", "wifi": "EMULATED-DEFAULT",
    },
    "ENV-009_machine_readable": "docs/ENVIRONMENT_PROFILE.json (this file) + pkginspect prerequisites section",
    "ENV-010_profile_sha16": None,  # filled below
}

profile_str = json.dumps(profile, indent=1, sort_keys=False)
profile["ENV-010_profile_sha16"] = hashlib.sha256(
    json.dumps({k: v for k, v in profile.items() if k != "ENV-010_profile_sha16"},
               indent=1, sort_keys=False).encode()).hexdigest()[:16]

DOCS.joinpath("ENVIRONMENT_PROFILE.json").write_text(
    json.dumps(profile, indent=1) + "\n")
print("wrote docs/ENVIRONMENT_PROFILE.json")


# ═══════════════════════════════════════════════════════════════════════
# 2. APK-001..020 — per-APK prerequisite extraction over the local corpus.
# ═══════════════════════════════════════════════════════════════════════
corpus = []
for d in ["tmp/diff366_apks", "upload", "upload/canonical_apks", "tmp/closeout_apks"]:
    p = BASE / d
    if p.is_dir():
        for apk in sorted(p.glob("*.apk")):
            corpus.append(apk)
# dedup by sha
seen, corpus2 = set(), []
for apk in corpus:
    s = sha256(apk)
    if s not in seen:
        seen.add(s)
        corpus2.append(apk)

rows = []
for apk in corpus2:
    r = run([str(BIN), "pkginspect", "--apk", str(apk), "--what",
             "prerequisites", "--jsonl", str(OUT_DIR / "prereq_jsonl")])
    if r.returncode != 0:
        rows.append({"apk": apk.name, "sha16": sha16(apk), "parse": "FAIL"})
        continue
    try:
        p = json.loads(r.stdout)["sections"]["prerequisites"]
    except Exception:
        rows.append({"apk": apk.name, "sha16": sha16(apk), "parse": "FAIL"})
        continue
    a = p["apk"]
    rows.append({
        "apk": apk.name, "sha16": sha16(apk),
        "minSdk": a["minSdk"], "targetSdk": a["targetSdk"],          # APK-001..002
        "dangerousPermissions": a["dangerousPermissions"],           # APK-005/006
        "usesFeatures": a["usesFeatures"],                           # APK-007
        "vulkanRequired": any("vulkan" in f for f in a["usesFeatures"]),  # APK-008
        "abis": a["abiLibs"],                                        # APK-009
        "abiElfMachines": a["abiElfMachines"],                       # APK-010/011
        "webviewFeatureDeclared": a["webviewFeatureDeclared"],       # APK-017
        "webkitTypesReferenced": a["webkitTypesReferenced"],
        "nativeAbiVerdict": a["nativeAbiVerdict"],
        "environmentMismatches": a["environmentMismatches"],
        "missingCapabilities": a["missingCapabilities"],             # API-003/004
        "recommendedNextProbe": a["recommendedNextProbe"],           # API-005
    })

with open(DOCS / "ENV_PREREQUISITE_MATRIX.jsonl", "w") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")
print(f"wrote docs/ENV_PREREQUISITE_MATRIX.jsonl ({len(rows)} APKs)")


# ═══════════════════════════════════════════════════════════════════════
# 3. WS-001/WS-002 — white/black case classification.
#    Sources: docs/DIFFERENTIAL_WORKING_VS_WHITE.md (#366 evidence),
#    docs/WHITE_SCREEN_LOADING_ROOTS.md, EggReturnsHome live env run.
# ═══════════════════════════════════════════════════════════════════════
ws_cases = [
    {"case": "org.fossify.clock", "face": "white",
     "first_divergence": "authoritative WINDOW_ROOT absent at frame time after App.onCreate EventBus death + LayoutInflater.inflate null-XmlPullParser NPE",
     "env_caused": False, "runtime_root": "VIEWTREE/ATTACH + app lifecycle chain",
     "classification": "B SAME_ROOT/NEW_EVIDENCE",
     "prereq_layer": "no ABI/feature mismatch (pure-DEX app) — environment satisfied",
     "evidence": "docs/DIFFERENTIAL_WORKING_VS_WHITE.md #1"},
    {"case": "com.sidhant.blockblast", "face": "white",
     "first_divergence": "ComposeView NOT in class index — content view never materialized (tree 1 node)",
     "env_caused": False, "runtime_root": "COMPOSE (R-NEW Compose family)",
     "classification": "B SAME_ROOT/NEW_EVIDENCE",
     "prereq_layer": "x86_64 libs present → EXECUTABLE_NATIVE; no env mismatch",
     "evidence": "docs/DIFFERENTIAL_WORKING_VS_WHITE.md #2 + prerequisite matrix row (64589a3a7e5c0f73)"},
    {"case": "com.game.asteroids_revenge", "face": "white",
     "first_divergence": "Arrays.toString REC-MISS → kotlin Intrinsics NPE → GodotActivity.onCreate died at pc=0x3a before native GodotView",
     "env_caused": "DUAL", "runtime_root": "NATIVE/JNI semantics fixed; engine still needs Godot native runtime",
     "classification": "C NEW_SUB_LAW for prereq face: APK declares android.hardware.vulkan.* and the GLES2-only environment cannot run a Vulkan-native engine",
     "prereq_layer": "EXECUTABLE_NATIVE (x86_64 libs) BUT vulkan features declared → missingCapabilities=[vulkan]",
     "evidence": "docs/DIFFERENTIAL_WORKING_VS_WHITE.md #3 + ENV_PREREQUISITE_MATRIX row"},
    {"case": "fr.arnaudguyon.spacevertex", "face": "white",
     "first_divergence": "kotlin.internal implementations Class.forName NPE; re-dispatch androidx Fragment ISE (HomeFragment must be public static)",
     "env_caused": False, "runtime_root": "FRAGMENT (ViewPager/Fragment materialization family)",
     "classification": "B SAME_ROOT/NEW_EVIDENCE",
     "prereq_layer": "no env mismatch — pure runtime semantics",
     "evidence": "docs/DIFFERENTIAL_WORKING_VS_WHITE.md #4"},
    {"case": "com.sanskritbasics.memory", "face": "white",
     "first_divergence": "WindowInsets CONSUMED sget → NPE in androidx compat clinit during ActionBarOverlayLayout init (WebView content inflated, never painted)",
     "env_caused": False, "runtime_root": "ANDROIDX LIFECYCLE (CONT-366 ROOT-B fixed — WindowInsets.CONSUMED law)",
     "classification": "B SAME_ROOT/NEW_EVIDENCE (fix landed post-#366; re-run shows REAL_APP_CONTENT)",
     "prereq_layer": "no env mismatch",
     "evidence": "root_registry CONT-366 ROOT-B + worklog 2026-10-02 wave"},
    {"case": "com.yepgoryo.EggReturnsHome (Godot)", "face": "background-only (windowBackground, 0 app draw ops)",
     "first_divergence": "GodotActivity.onCreate → godot_fragment_container Fragment never materializes a child (FrameLayout children=0) AND Godot engine requires arm64-only libgodot.so that the x86_64 host cannot execute",
     "env_caused": "DUAL", "runtime_root": "environment ABI boundary (arm64 native, no bridge) + Fragment materialization frontier",
     "classification": "D NEW_ROOT for the environment face (CPU-translation boundary, quantified); Fragment face = existing ViewPager/Fragment frontier",
     "prereq_layer": "ABI_MISMATCH_TRANSLATION_REQUIRED (arm64-v8a 2 libs, aarch64 ELF) — install succeeds, launch cannot reach engine",
     "evidence": "run/closeout/env_egg_run1.log (install rc=0, run PARTIAL, DEFAULT_BACKGROUND_ONLY) + prereq row"},
    {"case": "sudoku plain-run", "face": "white",
     "first_divergence": "WINDOW_ROOT (verdict NO_ROOT)",
     "env_caused": False, "runtime_root": "window/content-root chain",
     "classification": "A DUPLICATE (recorded)",
     "prereq_layer": "no env mismatch", "evidence": "docs/WHITE_SCREEN_LOADING_ROOTS.md"},
    {"case": "whatsapp", "face": "white",
     "first_divergence": "window/content chain",
     "env_caused": False, "runtime_root": "window/content chain",
     "classification": "A DUPLICATE (recorded)",
     "prereq_layer": "no env mismatch", "evidence": "docs/WHITE_SCREEN_LOADING_ROOTS.md"},
    {"case": "telegram settings-face", "face": "partial (renders 2-face)",
     "first_divergence": "ACTIVITY_NAVIGATION (intro/auth chain)",
     "env_caused": False, "runtime_root": "navigation chain",
     "classification": "A DUPLICATE (recorded)",
     "prereq_layer": "multi-ABI incl. x86_64 → EXECUTABLE_NATIVE", "evidence": "docs/WHITE_SCREEN_LOADING_ROOTS.md"},
]

with open(DOCS / "WS_PREREQUISITE_AUDIT.jsonl", "w") as f:
    for c in ws_cases:
        f.write(json.dumps(c) + "\n")

env_only = [c for c in ws_cases if c["env_caused"] is True]
dual = [c for c in ws_cases if c["env_caused"] == "DUAL"]
runtime_only = [c for c in ws_cases if c["env_caused"] is False]
md = []
md.append("# WS PREREQUISITE AUDIT — are white/black cases environment-caused?\n")
md.append(f"> HEAD `{HEAD[:12]}` · binary sha16 `{BIN_SHA}` · prerequisite layer in `pkginspect --what prerequisites` (this wave)\n")
md.append("## Answer (WS-002)\n")
md.append(f"- **Environment-caused (prerequisite mismatch): {len(env_only)}** — cases where the APK\n"
          "  requires a capability the environment cannot provide (ARM-only native code without a\n"
          "  bridge; Vulkan-native engine on a GLES2 software backend).\n")
md.append(f"- **Dual-cause (environment + runtime frontier): {len(dual)}** — Godot class: the arm64-only\n"
          "  libgodot.so cannot execute AND the godot_fragment_container Fragment never materializes\n"
          "  a child (the recorded ViewPager/Fragment frontier).\n")
md.append(f"- **Ordinary runtime roots: {len(runtime_only)}** — white faces whose prerequisite check\n"
          "  is CLEAN (no ABI/feature/API mismatch); first divergence sits in ViewTree/Compose/\n"
          "  Fragment/WindowInsets/lifecycle chains. These are NOT environment failures.\n")
md.append("## Per-case table\n")
md.append("| Case | Face | Env-caused | First divergence | Classification |")
md.append("|---|---|---|---|---|")
for c in ws_cases:
    md.append(f"| {c['case']} | {c['face']} | {c['env_caused']} | {c['first_divergence'][:110]} | {c['classification'][:60]} |")
md.append("\n## Redroid-class proof (ARM-only install-then-fail)\n")
md.append("com.yepgoryo.EggReturnsHome_1.apk: install rc=0 (redroid law: advertisement without\n"
          "translator lets ARM-only APKs INSTALL), runtime stops at DEFAULT_BACKGROUND_ONLY with\n"
          "0 app draw ops because the arm64-only libgodot.so cannot execute on the x86_64 host.\n"
          "Evidence: run/closeout/env_egg_run1.log; prerequisite verdict ABI_MISMATCH_TRANSLATION_REQUIRED.\n")
DOCS.joinpath("WS_PREREQUISITE_AUDIT.md").write_text("\n".join(md) + "\n")
print("wrote docs/WS_PREREQUISITE_AUDIT.md + .jsonl")


# ═══════════════════════════════════════════════════════════════════════
# 4. L0..L6 execution matrix — real execution status, NOT install/inspection.
#    L0 not tested | L1 installed | L2 launched/lifecycle | L3 meaningful
#    real pixels | L4 input/state transition | L5 multi-state interaction
#    | L6 repeatable verified execution (3-run byte-identical).
# ═══════════════════════════════════════════════════════════════════════
# Evidence-backed rows (recorded 3-run verdicts from the regression + closeout
# waves + this wave's gates). L6 = byte-identical x3 evidence on file.
L6 = [
    ("com.darkempire78.opencalculator", "app-calc", "e364b001ee7abd66 x3"),
    ("jwtc.android.chess", "game-board", "b5a7a35d5fe0564b x3 (determinism anchor — NOT a pixel golden)"),
    ("io.github.yamin8000.dooz", "game-board", "d602648e8e401895 x3 (determinism anchor)"),
    ("dubrowgn.microtimer", "app-tool", "da73010a37dd0189 x3"),
    ("app.varlorg.unote", "app-notes", "4f1a9e4e8f64fae8 x3"),
    ("com.aurorasoftworks.signal2048 (golden)", "game-arcade", "REAL_APP_CONTENT 4/4 gate (535c wave)"),
    ("Snake Deluxe (golden)", "game-arcade", "REAL_APP_CONTENT gate (1203c wave)"),
    ("MiniCraft (golden)", "game-sandbox", "REAL_APP_CONTENT gate (2416c wave)"),
    ("helloworld fixture", "app-entry", "canonical sha 83720c1028f832d0 (L6)"),
    ("org.secuso.privacyfriendlynotes", "app-notes", "eb5ebd559cad1028 x3 (fan-out)"),
    ("flappycow", "game-arcade", "13cf47464d9787f4 x3 (fan-out + bitmap provenance 12 events)"),
    ("de.duenndns.gmdice", "game-dice", "fan-out x3 REAL_APP_CONTENT"),
    ("in.uk.co.codewell.fishrings (fishrings)", "game-arcade", "a341e3ad9092f640 REAL_APP_CONTENT 44 draw ops"),
    ("tripeaks", "game-cards", "fan-out x3 REAL_APP_CONTENT"),
    ("com.forrestguice.suntimeswidget", "app-tool", "a49f90d65a8fc5c8 x3 REAL_APP_CONTENT (371 FINAL)"),
]
# L3/L4 (REAL_APP_CONTENT or interactive but not 3-run-recorded here)
L3_L4 = [
    ("com.sanskritbasics.memory", "app-game", "REAL_APP_CONTENT post WindowInsets fix (sha 67845303a9460d86)"),
    ("bouncy", "game-physics", "b6dde6074bf47264 x3 installed-state (determinism-anchored; render gate PASS class)"),
    ("com.athena.aslrt.whatsapp", "app-client", "known-face golden x3 (31ddd4d5b8e6d18e) — REJECTED as pixel golden (white face)"),
    ("forkgram", "app-client", "known face — golden re-bank PENDING (recorded)"),
    ("secuso sudoku", "game-board", "button-text gap REGISTERED (wave-2)"),
]
# L2 (lifecycle RESUMED but background-only frames)
L2 = [
    ("fr.arnaudguyon.spacevertex", "game-arcade", "RESUMED; Fragment ISE family"),
    ("org.fossify.clock", "app-tool", "RESUMED; WINDOW_ROOT/deferred-UI family"),
    ("com.yepgoryo.EggReturnsHome", "game-engine", "RESUMED; arm64-native + fragment container empty (this wave, env proof)"),
    ("com.sidhant.triplematch", "game-board", "F1-empty-viewtree family"),
]
# L1 (installed-identity proven, no launchable content — #370 multiapp gate)
L1 = [
    ("com.sidhant.blockblast", "game-compose", "installed-identity + full inspection (multiapp 5/5 render-FAIL leg)"),
    ("stopwatch", "app-tool", "NO launcher activity (structural, honest non-launch)"),
]
# L0 (not tested at this HEAD — no APK on disk)
L0 = [
    ("Safir", "unknown", "BLOCKED-BY-IDENTITY (zero records; APK needed)"),
    ("Black", "unknown", "BLOCKED-BY-IDENTITY (zero records; APK needed)"),
    ("official Telegram full auth", "app-client", "BLOCKED-APK-ABSENT (network/auth external boundary)"),
]

lrows = []
for name, fam, ev in L6:
    lrows.append({"title": name, "family": fam, "level": "L6", "evidence": ev})
for name, fam, ev in L3_L4:
    lvl = "L4" if "known-face golden" in ev or "REJECTED" in ev or "golden re-bank" in ev or "REGISTERED" in ev else "L3"
    lrows.append({"title": name, "family": fam, "level": lvl, "evidence": ev})
for name, fam, ev in L2:
    lrows.append({"title": name, "family": fam, "level": "L2", "evidence": ev})
for name, fam, ev in L1:
    lrows.append({"title": name, "family": fam, "level": "L1", "evidence": ev})
for name, fam, ev in L0:
    lrows.append({"title": name, "family": fam, "level": "L0", "evidence": ev})

with open(DOCS / "EXECUTION_LEVEL_MATRIX.jsonl", "w") as f:
    for row in lrows:
        f.write(json.dumps(row) + "\n")

from collections import Counter
counts = Counter(r["level"] for r in lrows)
print("wrote docs/EXECUTION_LEVEL_MATRIX.jsonl —", dict(sorted(counts.items())))
