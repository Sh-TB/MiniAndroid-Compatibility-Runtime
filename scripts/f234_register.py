#!/usr/bin/env python3
"""Register F-NEW-234 (per-package context-root law) in root_registry.json."""
import json

path = "/home/z/my-project/root_registry.json"
reg = json.load(open(path))
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

entry = {
    "id": "F-NEW-234",
    "status": "IMPLEMENTED+TESTED",
    "priority": "P0",
    "layer": "platform/package-store/storage",
    "title": "PER-PACKAGE CONTEXT-ROOT LAW GAP: MiniAndroid had THREE incompatible "
             "app-storage layouts and none was the AOSP package sandbox. The "
             "F-NEW-231 install created <data-root>/data/data/<pkg>/{files,cache,"
             "shared_prefs,databases} that NO runtime consumer ever read (decorative); "
             "the engine resolved Context files/cache/databases/getDir/external-* "
             "against a FLAT process root (cross-package contamination — two packages "
             "in one store share one sandbox; proven live: Telegram wrote cache4.db + "
             "account1-3 into <store>/files/ shared with every other package); prefs "
             "used a third shape <root>/<pkg>/shared_prefs. Installed-APK copy was "
             "real; the installed-app FILESYSTEM model was partial path simulation.",
    "law": "AOSP ContextImpl (frameworks/base core/java/android/app/ContextImpl.java): "
           "getFilesDir -> /data/user/0/<package>/files; getCacheDir -> cache; "
           "getSharedPreferences dir -> /data/data/<package>/shared_prefs; "
           "getDatabasePath -> databases/<name>; getDir(name) -> app_<name>; "
           "getExternalFilesDir(type) -> /storage/emulated/0/Android/data/<package>/"
           "files[/<type>]; getExternalCacheDir -> .../cache; getObbDirs -> "
           "Android/obb/<package>. EVERY Context-anchored dir is scoped to the "
           "RUNNING package identity. MiniAndroid mapping (documented deviation, "
           "F-NEW-231 store law): <data-root>/data/data/<package>/ internal + "
           "<data-root>/storage/emulated/0/ shared volume.",
    "evidence": "BEFORE (IAPK-0 live STATE B->C diff, run/iapk/evidence): opencalc "
                "installed run wrote <store>/<pkg>/shared_prefs (shape 3); "
                "bouncy+telegram+chess wrote cache4.db family + prefs into FLAT "
                "<store>/files|cache|<pkg>/shared_prefs; <store>/data/data/<pkg>/* "
                "stayed EMPTY (decorative). AFTER (F-NEW-234, run/iapk/after): "
                "12 installed runs (4 targets x3, source APKs PHYSICALLY QUARANTINED "
                "in run/iapk/quarantine during every run, restored after with SHAs "
                "verified) — ALL 23 runtime-created files landed under "
                "<store>/data/data/<pkg>/ (telegram: 22 files/10.6MB incl. "
                "cache4.db account1-3 + mainconfig/userconfig/themeconfig; chess: "
                "ChessPlayer.xml; opencalc: prefs THEME=2). FILE-IO PROVENANCE "
                "(MINIANDROID_FILE_IO): 100 traced ops for telegram r1 (3 honest "
                "failures = benign first-launch theme-extract misses), asset reads "
                "resolve 'assets/bluebubbles.attheme @ apk=<store>/data/app/<pkg>/"
                "base.apk' with app DEX callers — the installed package IS the byte "
                "source. 3-RUN: opencalc rc=0 e364b001ee7abd66 x3 (= F-NEW-228 "
                "golden); bouncy b6dde6074bf47264 x3; chess b5a7a35d5fe0564b x3; "
                "telegram bbb6cd10a834963d x3 — all byte-identical from installed "
                "identity only. PERSISTENCE: opencalc prefs THEME=2 written once, "
                "read back across runs; reinstall cycle (remove pkg dir -> "
                "reinstall -> clean shared_prefs -> run -> prefs re-created -> "
                "golden face). INSTALLED-vs-SIDELOAD: opencalc and bouncy faces "
                "byte-identical across both modes. REGRESSION: dooz d602648e8e401895 "
                "x3, microtimer da73010a37dd0189 x3, unote 4f1a9e4e8f64fae8 x3, "
                "opencalc sideload e364b001ee7abd66 x3 — ALL MATCH under the new "
                "law. RANDOM LEDGER row 2 (seed 20261003, pool 33): unote installed "
                "= 4f1a9e4e8f64fae8 rc=0 (= golden, notes.db per-package); "
                "WhatsApp installed = 31ddd4d5b8e6d18e PARTIAL (known white-face "
                "frontier, F-NEW-233 honest verdict — no regression).",
    "fix": "storage/data_root.{h,cpp}: set_context_package()/context_package()/"
           "package_data_dir()/context_dir(sub)/external_app_dir(kind)/"
           "external_obb_dir() — one law function family; binding creates the AOSP "
           "dir family (files/cache/shared_prefs/databases/code_cache/no_backup) "
           "and re-points DatabaseShadow::set_databases_dir. dalvik_engine.cpp: all "
           "16 Context-dir call sites re-anchored (getFilesDir/getCacheDir x2/"
           "getDir/getDatabasePath/4 prefs sites/AndroidUtilities.getCacheDir/"
           "getExternalFilesDir(+type subdir law)/getExternalCacheDir/plural "
           "external family/getObbDirs/5 relative-path sandbox anchors). Wired at "
           "execution_engine.cpp set_package_info site (before any app code, "
           "sideload AND --package runs). main.cpp: install creates code_cache + "
           "no_backup; new reusable `pkgaudit` command (identity + integrity "
           "re-hash + recursive code/data inventory, machine-readable). "
           "Instrumentation: diagnostics/file_io_trace.h (MINIANDROID_FILE_IO "
           "JSONL, op/path/result/caller/package, bounded 4000 events) wired into "
           "prefs writes, F104 streams, File exists/STAT/mkdirs/createNewFile, "
           "AssetManager.open; gfx_provenance gains byte_source classification "
           "(INSTALLED_APK | APP_DATA_FILE | EXTERNAL_APP_FILE | OTHER).",
    "test": "scripts/iapk_after.sh + scripts/iapk_manifest.py: 12 installed runs "
            "x3 byte-identical; state B/C/D manifests + diffs; quarantine check "
            "HIDDEN for all 4 sources; file_io.jsonl per run; regression battery "
            "x3 all MATCH; pkgaudit on 4 targets + unote; reinstall cycle proof.",
    "fanout": "every Context-storage API consumer (files/cache/prefs/db/getDir/"
              "external) in every APK; multi-package stores (cross-package "
              "isolation); installed-vs-sideload equivalence; persistence/reinstall "
              "semantics; Telegram large-app filesystem scaling.",
    "aff": "storage law core + dalvik_engine Context family + main.cpp package "
           "store + evidence instruments (file_io_trace, gfx byte_source). No "
           "rendering change; goldens byte-identical.",
    "apk": "opencalculator_53 / bouncy / telegram_official / chess_jwtc_298 / "
           "unote_30 (random) / WhatsApp_real (random)",
    "date": "2026-10-03",
}

if isinstance(roots, list):
    roots = [r for r in roots if r.get("id") != "F-NEW-234"]
    roots.append(entry)
    reg["roots"] = roots
else:
    for r in roots:
        if isinstance(r, dict) and r.get("id") == "F-NEW-234":
            r.update(entry)
            break
    else:
        roots.append(entry)

json.dump(reg, open(path, "w"), indent=1, ensure_ascii=False)
ids = [r.get("id") for r in (reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg)]
print("registry updated; total roots:", len(ids))
print("F-NEW-234 present:", "F-NEW-234" in ids)
