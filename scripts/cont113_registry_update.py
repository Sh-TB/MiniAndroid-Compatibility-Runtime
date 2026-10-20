#!/usr/bin/env python3
"""cont113_registry_update.py — CONT-113 wave registry update.

Adds:
  F-NEW-459  anchor-set build-pipeline gap (fresh container loses build/anchor_libs
             -> every libGDX-family APK dlopen-fails)          ROOT-CAUSED-FIXED
  F-NEW-460  empty libstdc++ anchor satisfies the Android DT_NEEDED by SONAME and
             blocks glibc's real C++ ABI (__cxa_pure_virtual)  ROOT-CAUSED-FIXED
  F-NEW-461  bionic version-tag strip matched only exact "LIBC"; the LIBC_N/O/P/
             Q/R/S family (e.g. __cxa_pure_virtual@LIBC_O) stayed versioned
                                                              ROOT-CAUSED-FIXED
  F-NEW-462  AndroidGraphics ctor receiver binding: AndroidGraphics field stores
             land on the GLSurfaceView20 shadow object -> config/app read NULL in
             setupGL/updatePpi (tower3d frontier)             CONFIRMED_OPEN_GAP
Also syncs the canonical mirror (id-unique both ways).
"""
import json
import sys

MAIN = "canonical/root_cause_registry.json"
MIRROR = "root_registry.json"

DATE = "2026-10-20"

NEW = [
    {
        "id": "F-NEW-459",
        "title": "F-NEW-387 anchor set is a build artifact a fresh container loses (libGDX family dlopen-fails)",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0-CRITICAL",
        "layer": "NATIVE_JNI",
        "date": DATE,
        "root_cause": (
            "CONT-113: the #366 matrix revalidation at fresh-container HEAD showed stack.tower3d "
            "NO_ROOT/WINDOW_ROOT with [SYNTH-EXC] UnsatisfiedLinkError 'gdx' extracted but 'dlopen "
            "failed: /lib/x86_64-linux-gnu/libm.so: invalid ELF header'. Root: the F-NEW-387 law "
            "(native_dep.cpp prepare_dependencies) pre-loads first-party ELF anchors carrying the "
            "ANDROID sonames so the app lib's DT_NEEDED matches by SONAME; the anchor set "
            "(build/anchor_libs/libm.so,liblog.so,libc.so,libdl.so,libstdc++.so) is a BUILD ARTIFACT "
            "the host libm.so is a GNU ld script (text), never an ELF. Cross-proof: bouncy "
            "libgdx-box2d.so fails with the IDENTICAL dlopen error (its REAL_APP_CONTENT face was the "
            "menu rendered despite dead physics). Fix: miniandroid/Makefile wires an `anchors` target "
            "that runs scripts/cont83_build_anchors.sh and `all` depends on it (.DEFAULT_GOAL := all "
            "pinned) - the anchor set can never go stale/missing again. Bracket: tower3d pre (no "
            "anchors) NO_ROOT/WINDOW_ROOT 0/3 -> post (anchors rebuilt) DEFAULT_BACKGROUND_ONLY/"
            "APP_DRAW_OPS 3/3 deterministic (11a38a5aeeff45a6); box2d on bouncy dlopen-fail -> "
            "[S2-NATIVE] load gdx-box2d: dlopen ok after the full fix pair."),
    },
    {
        "id": "F-NEW-460",
        "title": "Empty libstdc++ anchor satisfies the Android DT_NEEDED and blocks the host C++ ABI",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0-CRITICAL",
        "layer": "NATIVE_JNI",
        "date": DATE,
        "root_cause": (
            "CONT-113: after F-NEW-459 rebuilt the anchor set, bouncy's libgdx-box2d.so advanced to "
            "'undefined symbol: __cxa_pure_virtual, version LIBC_O'. Root: the CONT-83 libstdc++.so "
            "anchor was deliberately EMPTY (comment: 'satisfies the DT_NEEDED so the loader error "
            "names the real missing C++ symbol') - but satisfying the Android DT_NEEDED by SONAME "
            "PREVENTS glibc from loading the real libstdc++.so.6, so every Itanium-ABI symbol the "
            "NDK C++ libs need (__cxa_pure_virtual, operator new/delete, ...) has no provider. Fix: "
            "the anchor is linked against -lstdc++ so its dependency chain carries the REAL host C++ "
            "ABI (same law as the libm/libc anchors: layout-free Itanium-ABI symbols are "
            "SysV-stable; ABI caveat recorded). Anchor sha16 5dd95f611a38a7ce -> 7a9b37148a5a1edb."),
    },
    {
        "id": "F-NEW-461",
        "title": "Bionic version-tag strip matched only exact LIBC; the LIBC_* API-level family stayed versioned",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0-CRITICAL",
        "layer": "NATIVE_JNI",
        "date": DATE,
        "root_cause": (
            "CONT-113: with the anchor chain fixed, glibc still rejected 'undefined symbol: "
            "__cxa_pure_virtual, version LIBC_O'. Root: strip_bionic_version_tags (native_dep.cpp) "
            "matched verneed Vernaux names with strcmp(name,\"LIBC\")==0 ONLY - bionic tags its C/C++ "
            "ABI symbols per API level (LIBC_N/O/P/Q/R/S...); __cxa_pure_virtual is tagged LIBC_O, "
            "so every LIBC_* symbol version stayed in the extracted copy and glibc (GLIBC_* "
            "versions) rejected the versioned lookup. Fix: family test strcmp(name,\"LIBC\")==0 || "
            "strncmp(name,\"LIBC_\",5)==0 (GLIBC_* never matches the prefix); bounded, recorded, "
            "APK untouched (runtime-owned extracted copy only). Bracket: bouncy box2d "
            "undefined-symbol fail -> [S2-NATIVE] load gdx-box2d: dlopen ok; uncaught exceptions "
            "21 -> 10; face dd0c14257fa1f2af -> 8a6c24ac8a7d718e (adjudicated per F-NEW-443 "
            "precedent: natives dead -> live, richer face, not a wall row)."),
    },
    {
        "id": "F-NEW-462",
        "title": "AndroidGraphics ctor field stores land on the GLSurfaceView20 shadow object (config/app read NULL)",
        "status": "CONFIRMED_OPEN_GAP",
        "priority": "P1-HIGH",
        "layer": "DEX_SHADOW_HEAP",
        "date": DATE,
        "root_cause": (
            "CONT-113 honest decode: tower3d post-anchor-fix dies at NPE 'read field "
            "AndroidApplicationConfiguration.useGL30 on null' (AndroidGraphics.setupGL pc=29) and "
            "'invoke AndroidApplicationBase.getWindowManager on null' (AndroidGraphics.updatePpi "
            "pc=7), while the real config obj#43 exists and AndroidApplication.init reads it fine "
            "(IGET-MISS-DIAG keys: R8-renamed a/b/g/depth/disableAudio). Evidence: [IGET-MISS-DIAG] "
            "on obj#138 (runtime class GLSurfaceView20) lists AndroidGraphics;->eglContext/glVersion/"
            "height/width/lastFrameTime/synch/deltaTime among its field slots - the AndroidGraphics "
            "ctor's field stores were attributed to the GLSurfaceView20 object (AndroidGraphics ctor "
            "creates the GLSurfaceView20 internally; the shadow heap bound the ctor receiver to the "
            "view object). The graphics object therefore has NULL config/app when setupGL runs. "
            "Next lever: receiver binding through the nested view-construction inside a ctor "
            "(fixture-first: minimal two-class ctor-calls-ctor probe; law belongs to the shadow "
            "heap's this-binding, not to libGDX)."),
    },
]


def main() -> int:
    main_roots = json.load(open(MAIN))
    mirror_roots = json.load(open(MIRROR))

    def sync(roots):
        have = {r["id"] for r in roots}
        added = []
        for entry in NEW:
            if entry["id"] not in have:
                roots.append(entry)
                added.append(entry["id"])
        ids = [r["id"] for r in roots]
        assert len(ids) == len(set(ids)), "duplicate ids after add"
        return added

    added_main = sync(main_roots)
    added_mirror = sync(mirror_roots)
    json.dump(main_roots, open(MAIN, "w"), indent=1, ensure_ascii=False)
    json.dump(mirror_roots, open(MIRROR, "w"), indent=1, ensure_ascii=False)
    print(f"main: +{added_main} -> {len(main_roots)} roots")
    print(f"mirror: +{added_mirror} -> {len(mirror_roots)} roots")
    assert len(main_roots) == len(mirror_roots)
    return 0


if __name__ == "__main__":
    sys.exit(main())
