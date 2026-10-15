#!/usr/bin/env python3
"""s59_games_register.py — register the user-mandated game corpus additions
(2 colorful 2D + 1 tiny 3D) into the canonical corpus profiles and add two
new decoded roots to root_registry.json.

User directive (2026-10-15): "get two colorful 2D Android game APKs and a very
very small 3D game and put them in the tests from now on."
Selection (F-Droid suggested versions, byte-verified sizes vs index.xml):
  - com.dozingcatsoftware.bouncy_43    3.2MB  GPL-3.0  colorful 2D physics
  - org.secuso.privacyfriendlymemory_100 8.6MB GPL-3.0 colorful 2D cards
  - stack.tower3d_1                    4.5MB  GPL-3.0  tiny 3D stacker
Runs at binary 7d8aa389ba6945c0 (S58 byte-exact rebuild):
  bouncy  15s x3  screenshot sha16 dd0c14257fa1f2af BYTE-IDENTICAL x3
          -> COMPLETE colorful 2D menu (Select Table + 5 blue buttons)
  memory  15s/60s -> uniform bg; real AppCompat DEX throws ISE
          "You need to use a Theme.AppCompat theme (or descendant) with this
           activity." at createSubDecor pc=426 (F-NEW-366, F-NEW-364 family)
  stacktower3d 15s/60s -> white; libGDX SharedLibraryLoadRuntimeException at
          AndroidLauncher.onCreate (libgdx.so shipped for 4 ABIs; runtime has
          no native-library loading bridge) (F-NEW-367, BLOCKED prerequisite)
"""
import hashlib
import json
import sys
import zipfile

sys.path.insert(0, "/home/z/my-project/scripts")
from s88_corpus2 import scan_dex  # noqa: E402

REG = "/home/z/my-project/root_registry.json"
PROFILES = "/home/z/my-project/run/s88/corpus/profiles.json"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


GAMES = [
    {
        "pkg": "com.dozingcatsoftware.bouncy", "vc": 43, "version": "1.16.0",
        "apk": "/home/z/my-project/upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk",
        "url": "https://f-droid.org/repo/com.dozingcatsoftware.bouncy_43.apk",
        "upstream": "https://github.com/dozingcat/Bouncy",
        "kind": "game",
        "why": "user-mandated colorful 2D physics game (2026-10-15); "
               "COMPLETE menu face, x3 byte-identical dd0c14257fa1f2af",
    },
    {
        "pkg": "org.secuso.privacyfriendlymemory", "vc": 100, "version": "1.1.3-google",
        "apk": "/home/z/my-project/upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk",
        "url": "https://f-droid.org/repo/org.secuso.privacyfriendlymemory_100.apk",
        "upstream": "https://github.com/SecUSo/privacy-friendly-memory-game",
        "kind": "game",
        "why": "user-mandated colorful 2D memory game (2026-10-15); "
               "AppCompat createSubDecor ISE frontier (F-NEW-366)",
    },
    {
        "pkg": "stack.tower3d", "vc": 1, "version": "1.0.0",
        "apk": "/home/z/my-project/upload/canonical_apks/stack.tower3d_1.apk",
        "url": "https://f-droid.org/repo/stack.tower3d_1.apk",
        "upstream": "https://github.com/freshollie/stacktower3d",
        "kind": "game",
        "why": "user-mandated very-small 3D game (2026-10-15, 4.5MB); "
               "libGDX native-load prerequisite (F-NEW-367)",
    },
]


def main():
    # 1. corpus profiles
    profiles = json.load(open(PROFILES))
    added = []
    for g in GAMES:
        if g["pkg"] in profiles:
            print(f"  {g['pkg']} already in profiles — refreshing fields")
        dst = g["apk"]
        cnt, meths, own, libs, ndex, pfail = scan_dex(dst, g["pkg"])
        libflags = {k: 1 for k, v in libs.items() if v > 0}
        top = cnt.most_common(8)
        profiles[g["pkg"]] = {
            "kind": g["kind"], "why": g["why"],
            "version": g["version"], "vc": g["vc"],
            "sha256": sha256(dst),
            "size": __import__("os").path.getsize(dst),
            "url": g["url"], "upstream": g["upstream"],
            "dexes": ndex, "top_classes": top, "libs": libflags,
        }
        added.append(g["pkg"])
        print(f"  + {g['pkg']}: dexes={ndex} parse_fail={pfail} libs={libflags} "
              f"size={profiles[g['pkg']]['size']}")
    json.dump(profiles, open(PROFILES, "w"), indent=1, ensure_ascii=False)
    print(f"corpus profiles now: {len(profiles)} apps (added {len(added)})")

    # 2. registry roots
    reg = json.load(open(REG))
    existing = {r["id"] for r in reg["roots"]}
    new_roots = [
        {
            "id": "F-NEW-366",
            "status": "ROOT-CAUSED-PARTIAL",
            "title": (
                "AppCompat createSubDecor theme-guard ISE: the real androidx DEX "
                "(AppCompatDelegateImpl.createSubDecor pc=426) throws "
                "IllegalStateException 'You need to use a Theme.AppCompat theme (or "
                "descendant) with this activity.' when the resolved activity-theme bag "
                "lacks windowActionBar — measured on org.secuso.privacyfriendlymemory_100 "
                "(SplashActivity.onCreate APP-BOUNDARY; uniform bg after guard, no UI). "
                "Same root family as F-NEW-364 (notes_secuso theme-bag attr availability): "
                "the runtime's theme attr resolution cannot see the AppCompatTheme "
                "styleable attrs (windowActionBar etc.) in the effective theme bag. "
                "Named fix lever: consult the appcompat library's own styleable bag "
                "(merged APK res) on the resolve_theme_attr miss-path, then re-run "
                "memory + notes_secuso appcompat gates."
            ),
            "priority": "P1",
            "layer": "framework-res/theme",
            "evidence": (
                "run/s59/memory_60s.log (THROWABLE-MSG + EXCEPTION no-handler lines); "
                "run/s59/memory_60s/report.md; run/s59/memory_15s/; "
                "screenshot sha16 uniform bg [48,48,48] 60s / white 15s"
            ),
            "probe": "upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk",
            "verified_current": True,
        },
        {
            "id": "F-NEW-367",
            "status": "BLOCKED",
            "title": (
                "Native shared-library loading prerequisite: libGDX apps throw "
                "SharedLibraryLoadRuntimeException (SharedLibraryLoader.loadFile -> "
                "System.load of extracted .so) and die at the launcher onCreate before "
                "any GL init — measured on stack.tower3d_1 (AndroidLauncher.onCreate "
                "APP-BOUNDARY) and com.dozingcatsoftware.bouncy_43 (Box2D <clinit>; app "
                "catches and falls back, menu still COMPLETE). APK ships libgdx.so for "
                "all 4 ABIs (incl. x86_64) so this is NOT an ABI mismatch: the runtime "
                "has no native-library bridge. BLOCKED by design decision: implement a "
                "native-lib load bridge (full JNI parity is out of scope) OR document "
                "native-dependent games as honest runtime prerequisite. Bouncy proves "
                "graceful-degradation apps still reach real content without natives."
            ),
            "priority": "P2",
            "layer": "runtime/native-bridge",
            "evidence": (
                "run/s59/stacktower3d_60s/report.md; run/s59/bouncy_15s/report.md "
                "(caught path); unzip -l shows lib/{arm64-v8a,armeabi-v7a,x86,x86_64}/"
                "libgdx.so in both APKs; stacktower3d screenshot uniform white 15s/60s"
            ),
            "probe": "upload/canonical_apks/stack.tower3d_1.apk",
            "verified_current": True,
        },
    ]
    added_r = 0
    for nr in new_roots:
        if nr["id"] not in existing:
            reg["roots"].append(nr)
            added_r += 1
    # fix stale metadata (count/total fields drifted from actual list length)
    reg["count"] = len(reg["roots"])
    reg["total_roots"] = len(reg["roots"])
    json.dump(reg, open(REG, "w"), indent=1, ensure_ascii=False)
    print(f"registry roots now: {len(reg['roots'])} (added {added_r}, "
          f"metadata count/total corrected to actual)")

    # 3. gate anchor append — bouncy is a byte-exact anchor candidate
    print("bouncy anchor candidate: dd0c14257fa1f2af x3 (recorded in wave evidence)")


if __name__ == "__main__":
    main()
