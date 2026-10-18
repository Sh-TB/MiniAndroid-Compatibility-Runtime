#!/usr/bin/env python3
"""cont103_registry_update.py — register the CONT-103 roots (F-NEW-435..441)
into root_registry.json + mirror canonical/root_cause_registry.json."""
import json
import sys

REG = "root_registry.json"
MIRROR = "canonical/root_cause_registry.json"

WAVE = "CONT-103"
DATE = "2026-10-18"

ROOTS = [
    {
        "id": "F-NEW-435",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "ComponentName.createRelative static factory unimplemented — REC-MISS'd static left a nameless ComponentName and the PM consumer laws MISS'd with an EMPTY name (issue #364 CONT-103 telegram-first batch; probe c103a R3 reproduced the death).",
        "layer": "framework (dalvik_engine ComponentName.createRelative arm)",
        "root_cause": "Firebase ComponentDiscovery-family callers build their ComponentDiscoveryService ComponentName through ComponentName.createRelative(pkg, cls) (API 26+); the runtime had no handler, the static REC-MISS'd, and getServiceInfo/getActivityInfo/getProviderInfo then extracted an empty class name (stderr face: '[F275-SVCINFO] MISS  →' with an empty name), threw NameNotFoundException uncaught at the app boundary.",
        "fix": "createRelative(String pkg, String cls) / (Context, String) arm: leading-dot cls is relative (pkg+cls), otherwise pkg+'.'+cls; empty cls → AOSP NPE contract. Object minted with mPackage/mClass so every consumer law resolves.",
        "evidence": {
            "probe": "c103a S-REL pre=MISS-empty-death (NameNotFoundException uncaught at pc=70) post=com.probe.c103a.MyService; telegram Lkg/i;.P consumer alive post-fix",
        },
        "registered_wave": WAVE,
        "registered_date": DATE,
    },
    {
        "id": "F-NEW-436",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P2",
        "title": "Service/Provider meta-data seeding missed raw-manifest-name keys ('.Foo') — getServiceInfo(cn, GET_META_DATA).metaData answered null while the activity law answered the same manifest (issue #364 CONT-103).",
        "layer": "framework (dalvik_engine getServiceInfo/getProviderInfo meta-data lookup)",
        "root_cause": "The manifest parser keys component_meta_data_ by the RAW manifest component name ('.MyService'); the consumer looked up only the resolved dotted name (norm/bare) — the activity law (F-116) already had a containment fallback, the service/provider laws did not.",
        "fix": "Same containment fallback as the activity law added to BOTH the getServiceInfo and getProviderInfo meta-data lookups.",
        "evidence": {
            "probe": "c103a S-META pre=NO-META post=hello",
        },
        "registered_wave": WAVE,
        "registered_date": DATE,
    },
    {
        "id": "F-NEW-437",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P2",
        "title": "GET_SERVICES gate bit coding error (0x20 vs AOSP 0x4) — getPackageInfo(pkg, GET_SERVICES).services answered null (issue #364 CONT-103; same error class F-NEW-426 caught for GET_ACTIVITIES).",
        "layer": "framework (dalvik_engine getPackageInfo GET_SERVICES arm)",
        "root_cause": "The services array gate tested bit 0x20 (GET_SHARED_LIBRARY_FILES) instead of PackageManager.GET_SERVICES = 0x00000004; the probe requested the documented constant and got services == null.",
        "fix": "Gate bit corrected to 0x4.",
        "evidence": {
            "probe": "c103a PI-SVC-COUNT pre=-1 post=1",
        },
        "registered_wave": WAVE,
        "registered_date": DATE,
    },
    {
        "id": "F-NEW-438",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P2",
        "title": "ComponentName string-identity family unimplemented — flattenToString answered null (issue #364 CONT-103).",
        "layer": "framework (dalvik_engine ComponentName flatten/unflatten arms)",
        "root_cause": "No handler for flattenToString/flattenToShortString/unflattenFromString; the probe's CN-FLAT row printed 'null' (REC-MISS fallback) where AOSP returns 'pkg/cls'.",
        "fix": "flattenToString = pkg+'/'+cls; flattenToShortString collapses a leading 'pkg.' prefix keeping the dot; unflattenFromString splits at the first '/', expands a leading-dot class, null on malformed.",
        "evidence": {
            "probe": "c103a CN-FLAT pre=null post=com.probe.c103a/com.probe.c103a.MyService",
        },
        "registered_wave": WAVE,
        "registered_date": DATE,
    },
    {
        "id": "F-NEW-439",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "ComponentName(Context, Class) missed the HEAP Class-token face — firebase Class.forName-sourced Class objects (Object-field round-trip) left mClass unset and telegram's Lkg/i;.P getServiceInfo died NameNotFoundException uncaught (issue #364 CONT-103 telegram-first batch; the CONT-102 'pre-existing component-resolution death').",
        "layer": "framework (dalvik_engine ComponentName <init> Class-token arm)",
        "root_cause": "The (Context, Class) ctor law covered STRING_REF and const-class CLASS_REF args; firebase's MetadataComponentDiscovery obtains its Class via Class.forName, stores it through an Object field (Lv5/i;->b in telegram) and hands the engine an OBJECT_REF heap token — the law's cls_v stayed empty, the consumer MISS'd with an empty name, and the deferred NameNotFoundException escaped at Lkg/i;.P pc=39.",
        "fix": "OBJECT_REF Class-token arm in the ctor law: resolve __referent_desc from the heap record (F-069 class-token law) and set mClass; honest [F-NEW-439] diagnostic when a Class arg is still unresolvable.",
        "evidence": {
            "run": "telegram_official pre: 2× F275-SVCINFO MISS-empty → APP BOUNDARY; post: 0 MISS, [F-NEW-435]/[F-NEW-439] silent resolution, Lkg/i;.P consumer alive",
        },
        "registered_wave": WAVE,
        "registered_date": DATE,
    },
    {
        "id": "F-NEW-440",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "Class.isAssignableFrom probe-side heap Class-token resolution — every query asked assignable(Class→target) instead of assignable(actual→target) and answered FALSE; protobuf-lite factory selection threw 'No factory is available for message type' uncaught at LaunchActivity.onCreate pc=46 (issue #364 CONT-103 telegram-first batch).",
        "layer": "framework (dalvik_engine F-103 Class law probe-arg face)",
        "root_cause": "The F-103 handler resolved the RECEIVER token's __referent_desc but took the PROBE arg's class_desc verbatim — for a heap Class token that is the token's own type ('Ljava/lang/Class;'), so t1.zzc (= GeneratedMessageLite.class.isAssignableFrom(p3)) answered false, i2.zzb threw, and BillingController.<init> died in ApplicationLoader.postInitApplication.",
        "fix": "Probe-side heap-token resolution mirroring the receiver face: OBJECT_REF probe whose heap record is Ljava/lang/Class; → __referent_desc; non-token objects keep class_desc.",
        "evidence": {
            "run": "telegram_official post: 'No factory' count 0 (pre: thrown at i2.zzb pc=36, uncaught at pc=46)",
        },
        "registered_wave": WAVE,
        "registered_date": DATE,
    },
    {
        "id": "F-NEW-441",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "Direct-APK runs had no native-library extraction — System.loadLibrary always died 'present in the installed APK but extracted a different primary ABI' although the APK carries the host ABI (issue #364 CONT-103 telegram-first batch).",
        "layer": "framework (dalvik_engine GATEA-NATIVE loadLibrary on-demand arm)",
        "root_cause": "AOSP has no 'run an uninstalled APK': the device installs first and the install's ABI-scoped extraction is what makes loadLibrary work. miniandroid run <apk> skips the store install, the G-4 extracted tree is absent, and the load failed before any real dlopen (telegram_official: lib/x86_64/libtmessages.49.so present, forkgram: arm64-only).",
        "fix": "On-demand extraction at first loadLibrary, x86_64-first (the install law's host-executable order), into the sandbox-backed store path <data_root>/data/app/<pkg>/lib/<abi>/; the REAL dlopen + REAL dlerror honesty is unchanged (a refused ELF still reports the real refusal).",
        "evidence": {
            "run": "telegram_official: F-NEW-441 extract lib/x86_64/libtmessages.49.so 21084524 bytes → real dlopen → REAL dlerror (libjnigraphics.so dependency absent — UPP-001-family frontier, honest); forkgram: arm64 ELF extracted 18847608 bytes sha16=6175edf792986029 → real dlopen refusal recorded",
        },
        "registered_wave": WAVE,
        "registered_date": DATE,
    },
]


def main() -> int:
    reg = json.load(open(REG))
    roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg
    existing = {r["id"] for r in roots}
    added = 0
    for entry in ROOTS:
        if entry["id"] in existing:
            print("already present:", entry["id"])
            continue
        roots.append(entry)
        added += 1
    if isinstance(reg, dict) and "roots" in reg:
        reg["roots"] = roots
        json.dump(reg, open(REG, "w"), ensure_ascii=False, indent=1)
    else:
        json.dump(roots, open(REG, "w"), ensure_ascii=False, indent=1)
    # mirror
    mir = json.load(open(MIRROR))
    mroots = mir["roots"] if isinstance(mir, dict) and "roots" in mir else mir
    ids = {r["id"] for r in mroots}
    for entry in ROOTS:
        if entry["id"] not in ids:
            mroots.append(entry)
    if isinstance(mir, dict) and "roots" in mir:
        mir["roots"] = mroots
        json.dump(mir, open(MIRROR, "w"), ensure_ascii=False, indent=1)
    else:
        json.dump(mroots, open(MIRROR, "w"), ensure_ascii=False, indent=1)
    # uniqueness check
    all_ids = [r["id"] for r in roots]
    assert len(all_ids) == len(set(all_ids)), "duplicate ids!"
    print("added %d roots; registry now %d roots; mirror synced" %
          (added, len(roots), ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
