#!/usr/bin/env python3
"""cont81_registry_update.py — CONT-81 wave registry updates.

1. F-NEW-382 (NEW, ROOT-CAUSED-FIXED P1): the ART-identity System-property
   law gap — java.vm.name answered a self-descriptive value instead of the
   ART truth, and java.specification.name / java.runtime.name were absent.
   libGDX's SharedLibraryLoader.<clinit> classifies the platform by
   java.runtime.name.contains("Android Runtime") (decoded live from
   stack.tower3d's dex, scripts/cont81_decode_loader.py); without it every
   libGDX game fell to the desktop extract path (Class.getResourceAsStream)
   and died with SharedLibraryLoadRuntimeException before any view existed.
   Fix = the property table now carries the ART identity (vm.name=Dalvik,
   specification.name=Dalvik Specification, runtime.name=Android Runtime).
   Probe fixtures/fnew382_props_probe 4/4 (VM/SPEC/RT + absent=null).
2. F-NEW-382b (NEW, ROOT-CAUSED-FIXED P1): lazy G-4 nativeLibraryDir
   derivation — the extracted-lib identity existed only inside the
   getApplicationInfo seed, so a game loading natives BEFORE its first
   getApplicationInfo call (libGDX SharedLibraryLoader.load inside
   onCreate) saw an empty native_lib_dir_host_ and System.loadLibrary fell
   to the "not extracted" branch although install had extracted x86_64.
   Fix = the derivation (the install's own law, x86_64-first) runs on
   demand in the loadLibrary branch ([G-4-LAZY] row).
   Remaining honest boundary (recorded, NOT claimed fixed): the REAL dlopen
   of the extracted x86_64 libgdx.so then fails on Android DT_NEEDED
   sonames (libm.so/liblog.so/libc.so/libstdc++.so/libdl.so) vs host
   ld-scripts/sonames (libm.so = GNU ld script on this host; "invalid ELF
   header") — the F-NEW-157/UPP-001 native-execution domain.
3. Corpus-package reclassification (honest): muellerma.stopwatch (upload
   copy, versionCode 6) contains NO <activity> element and NO Activity
   subclass in its dex — the NO_ROOT/WINDOW_ROOT face is the honest result
   of running an activity-less package, NOT a runtime window-chain defect.
   The CONT-79 P0-C "WINDOW_ROOT pair" therefore dissolves into one
   package artifact + one real libGDX native-bootstrap chain (both now
   explained at current HEAD).
"""
import json

ROOT = "/home/z/my-project"
P1 = f"{ROOT}/root_registry.json"
P2 = f"{ROOT}/canonical/root_cause_registry.json"


def main():
    r = json.load(open(P1))
    roots = r["roots"] if isinstance(r, dict) and "roots" in r else r
    ids = [x.get("id") for x in roots]
    assert len(ids) == len(set(ids)), "duplicate root ids"
    by_id = {x["id"]: x for x in roots if "id" in x}
    assert "F-NEW-382" not in by_id and "F-NEW-382b" not in by_id

    roots.append({
        "id": "F-NEW-382",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": (
            "ART-IDENTITY SYSTEM-PROPERTY LAW GAP (libGDX native-bootstrap "
            "family, CONT-81): System.getProperty answered a "
            "self-descriptive java.vm.name and NO java.specification.name / "
            "java.runtime.name, so libGDX's SharedLibraryLoader.<clinit> "
            "mis-classified the platform as desktop and every libGDX game "
            "died with SharedLibraryLoadRuntimeException before any view."
        ),
        "layer": "runtime/system-properties (dalvik_engine F-080 table)",
        "root_cause": (
            "Decoded live from stack.tower3d's dex (scripts/cont81_decode_loader.py): "
            "SharedLibraryLoader.<clinit> reads moe.platform.name (iOS probe), then "
            "java.runtime.name.contains(\"Android Runtime\") — the ART identity "
            "string on every real device — to pick Os.Android; the desktop fallback "
            "then reads os.name (\"Linux\" here) and calls "
            "Class.getResourceAsStream(\"/libgdx64.so\") for extraction, which can "
            "never succeed inside an installed-APK runtime. AOSP/ART truth: "
            "java.vm.name=\"Dalvik\", java.specification.name=\"Dalvik "
            "Specification\", java.runtime.name=\"Android Runtime\". Fix: the "
            "F-080 property table now carries all three (generic platform "
            "identity, no app-specific branch)."
        ),
        "evidence": (
            "CONT-81 at c2b649586357a84e: pre-fix stack.tower3d x3 NO_ROOT "
            "(SharedLibraryLoadRuntimeException at SharedLibraryLoader.readFile "
            "pc=50 -> AndroidLauncher.onCreate APP-BOUNDARY unwind; "
            "run/cont81/tower3d_post/); post-fix the loader's <clinit> stores "
            "os=Os.Android (SGET obj_id=117 trace) and takes the "
            "System.loadLibrary branch. Probe fixtures/fnew382_props_probe "
            "(apk 493d081ce592c8c6): [F382-VM] Dalvik, [F382-SPEC] Dalvik "
            "Specification, [F382-RT] Android Runtime android-law=1, "
            "[F382-NEG] absent=null (4/4). Zero drift: wall 12/12 MATCH "
            "(dooz 31ddd4d5 x3 + opencalc f25b754c x3 + unote 90a67cc1 x3 + "
            "microtimer bbd350b6 x3), negatives 19/19, reinstall 8/8, "
            "goldens 4/4, MG-310 7/7, MG-150 3/3."
        ),
        "fix_surface": (
            "dalvik_engine.cpp t_kSystemProps: java.vm.name=\"Dalvik\", "
            "+java.specification.name, +java.specification.vendor, "
            "+java.runtime.name=\"Android Runtime\" (the ART identity set). "
            "The old self-descriptive vm.name row had no reader anywhere in "
            "the repo (verified) — pure platform-contract alignment."
        ),
        "honest_note": (
            "This fix moves the libGDX family to the REAL dlopen boundary; it "
            "does NOT make GL games render. The next law is F-NEW-382b's "
            "lazy lib-dir derivation (same wave) and then the DT_NEEDED "
            "soname frontier (libm.so/liblog.so/libc.so/libstdc++.so/"
            "libdl.so vs host ld-scripts) — the F-NEW-157/UPP-001 "
            "native-execution domain, explicitly out of this wave."
        ),
    })

    roots.append({
        "id": "F-NEW-382b",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": (
            "LAZY G-4 NATIVELIBRARYDIR DERIVATION (CONT-81): "
            "System.loadLibrary's extracted-tree check depended on the "
            "getApplicationInfo seed having run, so apps loading natives "
            "before any getApplicationInfo call saw an empty "
            "native_lib_dir_host_ and a false 'not extracted' refusal."
        ),
        "layer": "runtime/native-loading (dalvik_engine loadLibrary law)",
        "root_cause": (
            "The G-4 identity (store_root + /data/app/<pkg>/lib/<abi>) was "
            "derived only inside the Context/Activity.getApplicationInfo "
            "shadow seed. libGDX SharedLibraryLoader.load runs inside "
            "AndroidLauncher.onCreate BEFORE any getApplicationInfo, so the "
            "lookup skipped the extracted tree and threw the synthetic "
            "UnsatisfiedLinkError 'extracted a different primary ABI' "
            "(stack.tower3d live log) although native_libs.json recorded "
            "primaryAbi=x86_64 with both .so files extracted."
        ),
        "evidence": (
            "CONT-81 at c2b649586357a84e: post-fix run prints "
            "[G-4-LAZY] nativeLibraryDir derived on demand: "
            "/data/app/stack.tower3d/lib/x86_64 and the load reaches the "
            "REAL dlopen of the extracted x86_64 libgdx.so "
            "(run/cont81/tower3d_post/run4.log). Wall 12/12 MATCH zero "
            "drift after the change."
        ),
        "fix_surface": (
            "The loadLibrary branch derives the same install law on demand "
            "(x86_64-first order matching the installer's kAbiOrder) when "
            "native_lib_dir_host_ is still empty — identical result to the "
            "seed, no app cooperation needed."
        ),
        "honest_note": (
            "The remaining boundary is the host dlopen of Android-linked "
            ".so files: libgdx.so DT_NEEDED = libm.so/liblog.so/libc.so/"
            "libstdc++.so/libdl.so; this host's /lib/x86_64-linux-gnu/"
            "libm.so is a GNU ld script, dlopen fails 'invalid ELF header'. "
            "An ELF dependency-shim (LD_LIBRARY_PATH symlink farm at process "
            "start, or DT_NEEDED rewrite at extraction) is the F-NEW-157/"
            "UPP-001 native-execution domain — named, not claimed."
        ),
    })

    r["roots"] = roots if isinstance(r, dict) and "roots" in r else roots
    json.dump(r, open(P1, "w"), indent=1)
    c = json.load(open(P2))
    if isinstance(c, dict) and "roots" in c:
        c["roots"] = roots
        json.dump(c, open(P2, "w"), indent=1)
    print(f"registry: {len(roots)} roots (F-NEW-382, F-NEW-382b appended)")
    ids2 = [x.get("id") for x in roots]
    assert len(ids2) == len(set(ids2)), "duplicate after append"


if __name__ == "__main__":
    main()
