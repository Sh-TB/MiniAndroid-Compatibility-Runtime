#!/usr/bin/env python3
# cont102_registry_update.py — register the CONT-102 batch roots (F-NEW-424..434)
# in root_registry.json + mirror to canonical/root_cause_registry.json.
import json, hashlib, datetime

REG = "root_registry.json"
MIRROR = "canonical/root_cause_registry.json"

d = json.load(open(REG))
existing_ids = {r.get("id") for r in d}

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

new_roots = [
    {
        "id": "F-NEW-424",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "ApplicationInfo manifest truthfulness family: packageName null, enabled=false default, targetSdkVersion/minSdkVersion 0, metaData null — the getApplicationInfo singleton carried path-identity seeds only (EXP-043/F-NEW-190 era) and no normalized manifest model fields (issue #364 CONT-98 T2/T7).",
        "layer": "framework/pm (dalvik_engine getApplicationInfo seeding + manifest identity transfer)",
        "root_cause": "The ApplicationInfo singleton seeding predates the manifest component-table plumbing: seed_ai guarded ABSENT-only writes, and no uses-sdk/app-meta-data/packageName/enabled seeds existed. Probe c102b rows M-APP-PKG=null, M-APP-ENABLED=0, M-TARGETSDK=0, M-MINSDK=0, M-META=null.",
        "fix": "New engine fields manifest_requested_permissions_/manifest_activity_attrs_/manifest_target_sdk_/manifest_min_sdk_ populated from a fresh ManifestInfo parse at the stage_execute_application_real_dalvik transfer site (set_manifest_pkg_identity); getApplicationInfo seeds packageName, enabled=true, targetSdkVersion, minSdkVersion and builds the application metaData Bundle (numeric-typing law, same as the F-116 ActivityInfo bundle law).",
        "evidence": {"probe": "fixtures/cont102_b_probe V2 (8c4e10a5e6445d34)", "rows": "M-APP-PKG/M-APP-ENABLED/M-TARGETSDK/M-MINSDK/M-META all law-correct post-fix", "battery": "zero drift at c23d4b1a31acdeef"},
    },
    {
        "id": "F-NEW-425",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "ActivityInfo exported/launchMode never served (always 0/false) + ComponentName(Context, Class) ctor stored no mClass — manifest component defaults were unparsed and the Class-form ComponentName resolved to an empty name (issue #364 CONT-98 T2).",
        "layer": "apk/manifest_reader + framework/pm (dalvik_engine getActivityInfo + ComponentName ctor)",
        "root_cause": "ManifestReader captured per-activity name/theme/actions but not android:exported/android:launchMode; the ComponentName ctor law handled only (String,String)/(Context,String) — args[2] CLASS_REF was dropped, so getActivityInfo resolved an empty bare name (probe [F116-ACTINFO] bare=).",
        "fix": "ManifestReader.ActivityInfo carries exported/exported_declared/launch_mode (AXML bool 0x12 + string forms; launchMode enum 0..3 string+int forms); getActivityInfo serves them verbatim (AOSP-31+ default false when undeclared); the ComponentName ctor flattens the Class descriptor Lcom/pkg/Cls; -> com.pkg.Cls for mClass.",
        "evidence": {"probe": "c102b rows M-MAIN-EXPORTED=true, M-SECOND-EXPORTED=false, M-SECOND-LAUNCHMODE=1 (singleTop)", "aosp_law": "PackageParser.ActivityInfo + ComponentName(Context, Class) -> mClass=cls.getName()"},
    },
    {
        "id": "F-NEW-426",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "PackageManager.getPackageInfo(GET_ACTIVITIES) returned null activities — the GET_PROVIDERS (0x8) and GET_SERVICES (0x20) arms existed but the GET_ACTIVITIES arm was never written (issue #364 CONT-98 T7).",
        "layer": "framework/pm (dalvik_engine getPackageInfo)",
        "root_cause": "Only the provider/service array arms existed; GET_ACTIVITIES (bit 0x1 — AOSP PackageManager.GET_ACTIVITIES = 0x00000001) was absent; probe row PM-ACTIVITY-COUNT=-1 (null array).",
        "fix": "GET_ACTIVITIES arm builds [Landroid/content/pm/ActivityInfo; from the manifest activity table (name + packageName + exported + launchMode per entry, array[N] + __array_length__ convention) and attaches PackageInfo.activities.",
        "evidence": {"probe": "c102b PM-ACTIVITY-COUNT=2 post-fix", "note": "the bit was initially coded 0x2 (GET_RECEIVERS) — probe-diag flags=1 caught it honestly before the final battery"},
    },
    {
        "id": "F-NEW-427",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "PackageManager.getPackageInfo(GET_PERMISSIONS) returned null requestedPermissions — the uses-permission list was parsed (ManifestInfo.permissions) but never served (issue #364 CONT-98 T7).",
        "layer": "framework/pm (dalvik_engine getPackageInfo)",
        "root_cause": "No GET_PERMISSIONS (bit 0x1000) arm; probe row PM-REQUESTED-PERM=0.",
        "fix": "GET_PERMISSIONS arm builds [Ljava/lang/String; from manifest_requested_permissions_ verbatim (no invention) and attaches PackageInfo.requestedPermissions.",
        "evidence": {"probe": "c102b PM-REQUESTED-PERM=1 post-fix (matches the 1 declared uses-permission)"},
    },
    {
        "id": "F-NEW-428",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "checkSelfPermission answered DENIED for the RUNNING package's own manifest-declared normal permission — no install-grant law (issue #364 CONT-98 T8).",
        "layer": "framework/perm (dalvik_engine checkSelfPermission)",
        "root_cause": "The permission model consulted permission_state_ then a static NORMAL table; a custom self-declared permission (e.g. com.probe.c102c.PERM / com.probe.c102b.DECLARED) fell through to DENIED. AOSP DefaultPermissionGrantPolicy: install-time grant for normal/signature protectionLevel.",
        "fix": "Install-grant arm: requested-by-self AND not in the dangerous table (CAMERA/RECORD_AUDIO/location/contacts/sms/storage/calendar/sensors/RECOGNITION — runtime-grant law keeps those DENIED until requestPermissions) -> GRANTED(0).",
        "evidence": {"probe": "c102b R-CHECKSELF-DECL=0, c102c R-SELF-DECL=0; undeclared CAMERA stays -1; checkPermission(declared) stays 0"},
    },
    {
        "id": "F-NEW-429",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "PackageManager.getPackageInfo(unknownPkg, ...) served the RUNNING package's identity instead of throwing NameNotFoundException (issue #364 CONT-98 T7).",
        "layer": "framework/pm (dalvik_engine getPackageInfo)",
        "root_cause": "The mint served versionCode/versionName/packageName unconditionally — any query answered own-identity (silent wrong: callers gating on NameNotFound took present branches). Probe row PM-NOTFOUND=no-exception.",
        "fix": "Package-not-found law: non-empty pkg arg != running package AND != the platform 'android' package -> throw_deferred NameNotFoundException (PM-GETPKG channel). The platform package stays served (pre-existing behavior, honest residual recorded).",
        "evidence": {"probe": "c102b PM-NOTFOUND=NameNotFoundException post-fix", "honest_residual": "'android' package still served own-shaped (recorded, not invented)"},
    },
    {
        "id": "F-NEW-430",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "ApplicationInfo.sourceDir answered the raw host apk_path (relative) instead of the GATE-A logical /data/app/<pkg>/base.apk identity — the documented issue-#370 law was silently defeated by the seed_ai ABSENT-only guard (issue #364 CONT-98 T1/T7).",
        "layer": "framework/pm (dalvik_engine getApplicationInfo seeding order)",
        "root_cause": "seed_ai(sourceDir, apk_path_) ran FIRST; the later GATE-A seed used the same guard, which only fills ABSENT/non-string fields — a STRINGRef apk_path_ seed won forever. resolve_android_path DENIES the relative host spelling -> File(sourceDir).exists()==false (probe rows I-SOURCEDIR-EXISTS=false, LEN=0).",
        "fix": "The GATE-A block now OVERWRITES sourceDir/publicSourceDir with the logical identity (direct set_object_field), keeping hostSourceDir as the private engine-internal field; INSTALLED_APK category maps the logical path back to the store backing.",
        "evidence": {"probe": "c102b V2 rows: I-SOURCEDIR=/data/app/com.probe.c102b/base.apk, I-SOURCEDIR-EXISTS=true, I-SOURCEDIR-LEN=3730 (store-backed run, post7_b)", "honest_law": "exists()==false is the CORRECT absent-store answer for a non-installed data-root (final_b run)"},
    },
    {
        "id": "F-NEW-431",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P2",
        "title": "Resources.getConfiguration().densityDpi answered 0 — the Configuration singleton carried no display identity (issue #364 CONT-98 T9).",
        "layer": "framework/resource (dalvik_engine getConfiguration)",
        "root_cause": "The Configuration singleton was minted empty; the DisplayMetrics shadow serves densityDpi=160 (display_shadow) but the same identity never reached Configuration — cold/warm coherence and resource-selection laws read 0.",
        "fix": "getConfiguration seeds densityDpi from the SAME display identity the DisplayMetrics shadow serves (160 — one identity law, no second value invented).",
        "evidence": {"probe": "c102c C-DENSITY-DPI=160 post-fix; C-DENSITY-STABLE=1 (cold==warm)"},
    },
    {
        "id": "F-NEW-432",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "AdapterView adapter family had ZERO support: setAdapter REC-MISS, getCount()=0, no row materialization, ListView taps dead (claim law required clickable), item-click receiver bound to the AdapterView instead of the listener (issue #364 CONT-99 T8).",
        "layer": "framework/view (dalvik_engine setAdapter/getCount + touch_dispatcher claim/UP arms + view_renderer list stacking + dispatch_item_click receiver law)",
        "root_cause": "Six coupled gaps: (1) no setAdapter law; (2) no AdapterView.getCount delegate; (3) no row materialization (getView invoke + child attach); (4) the touch claim walk required view_touchable (ListView carries no View.OnClickListener) so taps answered target=0; (5) the UP arm aborted at the same gate; (6) dispatch_item_click led its args with the AdapterView object, so every listener body ran on a NULL receiver (iput-null-recv NPE inside MainActivity$2.onItemClick pc=2).",
        "fix": "setAdapter stores the adapter on the ViewShadow node + materializes rows via try_recursive_invoke getView (bounded 64, documented recycler-window simplification) + renderer stacks ListView/GridView children vertically (AOSP AbsListView column law); the claim walk accepts an AdapterView carrying an item listener (AbsListView IS the touch target by contract); the UP arm honors the same self-target law; pointToPosition resolves the tapped child box when the list itself claimed the DOWN; dispatch_item_click binds args[0] to the LISTENER instance.",
        "evidence": {"probe": "c102d LV-COUNT=5, LV-CHILDREN=5, LV rows pixel-true (row0 #CC8811 row1 #1188CC), [C102-LV-CLICK] pos=0 -> LV-LAST-CLICK=0 end-to-end", "scroll": "SV-SCROLLY-300=300 with content rows shifted exactly one row (row4 at viewport y=600 post-scroll, pixel-exact)"},
    },
    {
        "id": "F-NEW-433",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "java.io.FileReader.read(char[]) answered the stub 0 — the F-NEW-241 Reader law gated on BufferedReader/InputStreamReader declaring classes only (issue #364 CONT-98 T10 durable-state face).",
        "layer": "dex/io (dalvik_engine F-NEW-241 read law gate)",
        "root_cause": "FileReader.read fell to the type-aware stub default (0) because the declaring class (Ljava/io/FileReader;) matched neither gate string — the ctor had registered the stream and the read still starved (c102c GEN2: stream=o22 present=1, read returned 0).",
        "fix": "Gate widened to the whole *Reader* family (declaring class contains Reader); unregistered receivers fall through unchanged (StringReader/CharArrayReader keep prior behavior).",
        "evidence": {"probe": "c102c GEN4 T10-FILE-SURVIVED=gen1 (read filled 4 chars)"},
    },
    {
        "id": "F-NEW-434",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "String(char[]) and String(char[], off, len) constructors unimplemented — new String identity object with empty content (issue #364 CONT-98 T10 canonical file-read idiom).",
        "layer": "dex/lang (dalvik_engine String <init> [C arm)",
        "root_cause": "The F-NEW-358 handler covered String(String)/CharSequence and byte[] sources only; the [C source fell to the generic paths (c102c GEN3: identity string Ljava/lang/String;@24 printed from a filled 4-char buffer).",
        "fix": "[C source arm beside the [B arm (array[i] CHAR/INT32 elements, off/len forms, __string_value__ identity law preserved).",
        "evidence": {"probe": "c102c GEN4 T10-FILE-SURVIVED=gen1"},
    },
]

added = 0
for r in new_roots:
    if r["id"] in existing_ids:
        print("SKIP (exists):", r["id"])
        continue
    r["registered_wave"] = "CONT-102"
    r["registered_date"] = datetime.date.today().isoformat()
    d.append(r)
    existing_ids.add(r["id"])
    added += 1

json.dump(d, open(REG, "w"), indent=1, ensure_ascii=False)
json.dump(d, open(MIRROR, "w"), indent=1, ensure_ascii=False)
print(f"registry {len(d)-added} -> {len(d)} roots (+{added})")
print("sha16:", sha16(REG))
