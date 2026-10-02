#!/usr/bin/env python3
"""F-NEW-231 registration: INSTALLED_APK_ACCESS platform capability.

Registers the root and flips it straight to IMPLEMENTED+TESTED only after the
proof script passes; this script only REGISTERS the root (OBSERVED gap state at
registration time — BEFORE evidence captured 2026-10-02: `miniandroid help`
contains no install/list-packages/--package; sourceDir = passed sideload path;
no package store exists).
"""
import json, sys

REG = "/home/z/my-project/root_registry.json"

ENTRY = {
    "id": "F-NEW-231",
    "status": "REGISTERED",
    "priority": "P0",
    "layer": "platform/package-store",
    "title": (
        "INSTALLED_APK_ACCESS GAP: MiniAndroid had NO installation mechanism. "
        "The only execution input was a raw sideload APK path; "
        "ApplicationInfo.sourceDir = whatever path was passed; there was no "
        "package store, no installed-package discovery, no post-install "
        "identity. The agent therefore could not prove the chain "
        "APK -> install -> installed state -> filesystem/manifest/DEX/resource "
        "inspection -> launch from installed state (mega-campaign §3)."
    ),
    "law": (
        "AOSP PackageManagerService install law (android-14): install commits "
        "the APK to a codePath under /data/app as base.apk; "
        "PackageInfo/ApplicationInfo.sourceDir points at the INSTALLED base.apk "
        "and the original sideload path is NOT preserved; "
        "PackageManager.getInstalledPackages() enumerates installed packages; "
        "app-private dirs live under /data/data/<package>/{files,cache,"
        "shared_prefs,databases}. MiniAndroid deviation law (deliberate, "
        "documented): deterministic mapping <data-root>/data/app/<package>/"
        "base.apk instead of AOSP random per-install dirs — the platform-audit "
        "requirement is agent inspectability from package identity alone."
    ),
    "evidence": (
        "BEFORE 2026-10-02: `build/miniandroid help` — no install/list-packages/"
        "--package commands; grep of src/ shows sourceDir seeded from apk_path_ "
        "(sideload path). Capability did not exist."
    ),
    "fix": (
        "Generic package store in main.cpp: (1) `install <apk> --data-root` — "
        "ApkParser manifest read -> SHA-256 -> copy base.apk into "
        "<data-root>/data/app/<pkg>/ -> integrity re-hash -> package.json "
        "(PackageInfo mirror: package/versionName/versionCode/mainActivity/"
        "minSdk/targetSdk/permissions/codePath/hostCodePath/apkSha256/apkSize/"
        "installedAt; origin=sideload with NO original path preserved, AOSP "
        "law) -> /data/data/<pkg>/{files,cache,shared_prefs,databases} created. "
        "(2) `list-packages --data-root` — store scan, JSON records. "
        "(3) `run --package <pkg> --data-root` — resolve installed base.apk "
        "from package identity ALONE and run from the installed codePath "
        "(provenance = installed path via sourceDir law)."
    ),
    "test": (
        "Two-APK installed-state proof (1 app + 1 game): install -> fresh "
        "identity-only discovery (list-packages) -> analyze/dex on the "
        "INSTALLED base.apk -> run --package x3 with byte-identical "
        "screenshots -> sourceDir provenance = installed path -> installed "
        "sha == source sha. All ten platform claims answered per claim."
    ),
    "fanout": "every APK; all future agent workflows; the APK-inspection skill.",
    "aff": "platform capability; not an app-specific fix.",
}


def main():
    with open(REG) as f:
        reg = json.load(f)
    if any(r["id"] == "F-NEW-231" for r in reg["roots"]):
        print("F-NEW-231 already registered")
        return
    reg["roots"].append(ENTRY)
    reg["count"] = len(reg["roots"])
    reg["status_counts"] = {}
    for r in reg["roots"]:
        reg["status_counts"][r.get("status", "?")] = (
            reg["status_counts"].get(r.get("status", "?"), 0) + 1)
    with open(REG, "w") as f:
        json.dump(reg, f, indent=1)
    print(f"registered F-NEW-231; registry count -> {reg['count']}")


if __name__ == "__main__":
    sys.exit(main())
