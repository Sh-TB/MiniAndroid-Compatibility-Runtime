#!/usr/bin/env python3
"""cont156_registry2.py — CONT-156 Trains 3-8 registry updates:
F-NEW-487/488 ROOT-CAUSED-FIXED + honest CLASSIFIED rows for the
remaining WINDOW_ROOT blanks (rico/goodtime/readrops/shizuwall/fdroid-pe)."""
import json

ROWS = [
    {
        "id": "F-NEW-487",
        "title": "F-NEW-487 — filled-new-array type resolution fallback was a DEAD STUB: unresolved type_idx stayed the literal '<unknown>' and the array was ALLOCATED with that heap class_descriptor; the R-NEW-010 aput-object store-check then rejected every typed store of it (false ArrayStoreException at <clinit>) — ghostsq commander dead on arrival",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "dex-arrays",
        "evidence": {
            "root": "com.ghostsq.commander Utils.<clinit> pc=15: builds String[][] via filled-new-array {..}, [Ljava/lang/String; — per-DEX resolution missed and the single-dex/merged fallback was dead code (empty class_info_index_ lookup, result discarded) -> inner arrays carried '<unknown>' -> dalvik_class_assignable('<unknown>','[Ljava/lang/String;') false -> ASC '<unknown> cannot be stored in an array of type [[Ljava/lang/String;' -> NoClassDefFoundError cascade (erroneous class) for Utils and every consumer.",
            "fix": "(1) filled-new-array: after the per-DEX block, resolve through dex_report_->types (same fallback law as resolve_type_for_dex). (2) the store-check's asc_src_known guard now treats the literal '<unknown>' as UNKNOWN (bypass, conservative scope law) — the guard previously let the marker through and rejected.",
            "verify": "ghostsq commander_479: ArrayStoreException GONE, NoClassDefFoundError cascade GONE, face 0.0% -> 99.4% non-white. Wall 9/9 MATCH at 9a36acf0 (later dd2622762 with F-NEW-488).",
            "run": "run/c156/t5_ghost.log (pre-fix ASC-REJECT), run/c156/t5b_ghost.log (post-fix)"
        },
    },
    {
        "id": "F-NEW-488",
        "title": "F-NEW-488 — PackageManager.getApplicationInfo(String,int) was NOT shadowed (REC-MISS -> null): apps reading .metaData off the result NPE'd at onCreate — the Context-variant twin",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework-pm",
        "evidence": {
            "root": "ricochlime Lu0/j;.t pc=10: getPackageManager().getApplicationInfo(pkg, GET_META_DATA=128) -> REC-MISS -> null -> iget-null-recv NPE '.metaData' at pc=16 -> unwind (WINDOW_ROOT blank). AOSP: PackageManager serves the SAME ApplicationInfo as Context; foreign package = NameNotFoundException.",
            "fix": "dalvik_engine.cpp after the Context getApplicationInfo block: PackageManager.getApplicationInfo -> own package: the ApplicationInfo singleton seeded (packageName/sourceDir/publicSourceDir/dataDir/enabled + metaData Bundle from application_meta_data_, absence-guarded); foreign name: raise NameNotFoundException (AOSP contract, honest).",
            "verify": "ricochlime metaData-killer signature GONE (the app then surfaces its NEXT honest frontier: Flutter engine init — FLUTTER-BOUNDARY, needs native Dart VM; classified separately). Generic coverage: any app reading metaData/getApplicationInfo via PM. Wall 9/9 MATCH at dd2622762adb440a.",
            "run": "run/c156/t6_rico.log (pre-fix REC-MISS+pc=16), run/c156/t6b_rico.log (post-fix: killer gone)"
        },
    },
    {
        "id": "F-NEW-489",
        "title": "F-NEW-489 — ricochlime: Flutter app — FlutterEngine/LuaLoader init requires the native Dart VM (libflutter.so) — app-side native runtime boundary beyond DEX interpretation",
        "status": "CLASSIFIED",
        "priority": "P3",
        "layer": "native-boundary",
        "evidence": {
            "decode": "After F-NEW-488 removed the metaData NPE, the next blocker is FlutterLoader: 'Future.get on null' inside FlutterEngine bootstrap (Lz2/d;.a pc=796) -> RuntimeException 'Flutter initialization failed.' -> APP BOUNDARY. ricochlime ships libflutter.so (Dart VM); DEX-level compatibility cannot execute Dart snapshots. Honest APP-BOUNDARY: same category as UPP-001 (telegram/forkgram libjnigraphics).",
            "run": "run/c156/t6b_rico.log"
        },
    },
    {
        "id": "F-NEW-490",
        "title": "F-NEW-490 — goodtime: Constructor.newInstance silent-null family — the Constructor shadow answers null when the token identity fields are missing, and the call was served as REC-MISS at attachBaseContext (Koin DI bootstrap)",
        "status": "CLASSIFIED",
        "priority": "P2",
        "layer": "framework-reflect",
        "evidence": {
            "decode": "GoodtimeApplication.attachBaseContext -> Constructor.newInstance REC-MISS -> null -> getClass() on null (Kotlin null-check shape) -> NPE attributed at Lki0;.<init> pc=0 -> app dead before DI. The existing Constructor.newInstance shadow (FIX-M3-012b, Room lineage) guards class_desc/__reflect_class and returns make_null() silently on miss — the silent-null family. Named lever: getDeclaredConstructor token provenance for this call shape + honest IllegalArgumentException instead of silent null (AOSP: newInstance with wrong token shape throws, never null).",
            "run": "run/c155/t3/com.apps.adrcotfas.goodtime_364.log (pinned stack)"
        },
    },
    {
        "id": "F-NEW-491",
        "title": "F-NEW-491 — readrops: Koin loadModules vararg-null — Intrinsics$Kotlin.toArray casts null to Array<Any?> from DiskLruCache$$ExternalSyntheticLambda0 -> Koin.loadModules (B-type Koin family)",
        "status": "CLASSIFIED",
        "priority": "P2",
        "layer": "compose-di-koin",
        "evidence": {
            "decode": "ReadropsApp.onCreate pc=107 -> Intrinsics.checkNotNull 'null cannot be cast to non-null type kotlin.Array<kotlin.Any?>' <- Intrinsics$Kotlin.toArray <- Koin.loadModules <- coil3 DiskLruCache$$ExternalSyntheticLambda0.invoke. The vararg module array reached the callee as null — on ART a Kotlin vararg array is compiler-allocated, never null. Named lever: lambda-invocation arg marshalling for the Koin module vararg (B-type family with goodtime).",
            "run": "run/c155/t3/com.readrops.app_22.log (pinned stack depth 5)"
        },
    },
    {
        "id": "F-NEW-492",
        "title": "F-NEW-492 — fdroid privileged extension: attach dispatch ok=false with classes_indexed=23 — launcher onCreate never dispatched (A-type variant)",
        "status": "CLASSIFIED",
        "priority": "P2",
        "layer": "lifecycle-attach",
        "evidence": {
            "decode": "org.fdroid.fdroid.privileged_2070: [UC009-ATTACH-DIAG] dex_report=SET classes_indexed=23 nodes=0 depth=0; ComposeView NOT in class index; attach ok=false; zero onCreate entries. Distinct from F-NEW-482 (that fixed the DEX-0 inherited-onCreate skip): this app's class index is tiny and the attach path finds no view nodes — needs its own decode train (class-index build for this APK shape).",
            "run": "run/c155/t3/org.fdroid.fdroid.privileged_2070.log"
        },
    },
    {
        "id": "F-NEW-493",
        "title": "F-NEW-493 — shizuwall: Shizuku SystemServiceHelper.getSystemService -> Method.invoke on null (binder transport absent) — app-side IPC boundary; plus the app's own manifest 'android:exported must be true' ISE (faithful app behavior)",
        "status": "CLASSIFIED",
        "priority": "P3",
        "layer": "ipc-boundary",
        "evidence": {
            "decode": "com.arslan.shizuwall_51: Lrikka/shizuku/SystemServiceHelper;.getSystemService pc=17 Method.invoke null -> NPE. Shizuku requires a running Shizuku server over binder — outside the DEX runtime's model (same boundary class as UPP-001). The earlier ISE 'android:exported must be true' is the APP's own AOSP-12+ validation firing on the real manifest — faithful engine behavior, not a bug.",
            "run": "run/c155/t3/com.arslan.shizuwall_51.log"
        },
    },
]

def load(path):
    with open(path) as f:
        return json.load(f)

def upsert(roots, row):
    for i, r in enumerate(roots):
        if r.get('id') == row['id']:
            merged = dict(r)
            for k, v in row.items():
                if k == 'evidence' and isinstance(v, dict) and isinstance(r.get('evidence'), dict):
                    ev = dict(r['evidence']); ev.update(v); merged[k] = ev
                else:
                    merged[k] = v
            roots[i] = merged
            return 'updated'
    roots.append(row)
    return 'added'

for p in ['root_registry.json', 'canonical/root_cause_registry.json']:
    doc = load(p)
    roots = doc['roots'] if isinstance(doc, dict) and 'roots' in doc else doc
    for row in ROWS:
        print(f'{p}: {row["id"]} {upsert(roots, row)}')
    ids = [r.get('id') for r in roots]
    assert len(ids) == len(set(ids)), 'id uniqueness broken'
    if isinstance(doc, dict) and 'roots' in doc:
        doc['roots'] = roots
    with open(p, 'w') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'{p}: total={len(roots)}')
