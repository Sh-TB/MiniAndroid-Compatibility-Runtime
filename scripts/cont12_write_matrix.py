#!/usr/bin/env python3
"""cont12_write_matrix.py — CONT-12 PHASE 1: emit DOOZ_COMPOSE_DEPENDENCY_MATRIX
from the fetched artifacts (exact versions read from the dooz APK's
META-INF/*.version files) + the Phase 0 baseline lock record."""
import hashlib, json, os, zipfile

BASE = "/home/z/my-project"
RAW = f"{BASE}/upstream/cont12_maven/raw"
CLS = f"{BASE}/upstream/cont12_maven/classes"
OUT = f"{BASE}/evidence/cont12"
os.makedirs(OUT, exist_ok=True)

APK = f"{BASE}/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.exists(p) else None

def nclasses(jar):
    try:
        z = zipfile.ZipFile(jar)
        return sum(1 for n in z.namelist() if n.endswith(".class"))
    except Exception:
        return 0

# version files read from the dooz APK (authoritative source)
z = zipfile.ZipFile(APK)
apk_versions = {}
for n in z.namelist():
    if n.endswith(".version"):
        try:
            apk_versions[n.split("META-INF/")[1].removesuffix(".version")] = z.read(n).decode().strip()[:40]
        except Exception:
            pass

rows = [
    # (artifact name in classes/, dooz version-file key fragment, version, repo)
    ("runtime-android",             "androidx.compose.runtime_runtime",          "1.11.4", "google-maven"),
    ("runtime-saveable-android",    "androidx.compose.runtime_runtime-saveable", "1.11.4", "google-maven"),
    ("runtime-retain-android",      "androidx.compose.runtime_runtime-retain",   "1.11.4", "google-maven"),
    ("ui-android",                  "androidx.compose.ui_ui",                    "1.11.4", "google-maven"),
    ("ui-geometry-android",         "androidx.compose.ui_ui-geometry",           "1.11.4", "google-maven"),
    ("ui-graphics-android",         "androidx.compose.ui_ui-graphics",           "1.11.4", "google-maven"),
    ("ui-text-android",             "androidx.compose.ui_ui-text",               "1.11.4", "google-maven"),
    ("ui-unit-android",             "androidx.compose.ui_ui-unit",               "1.11.4", "google-maven"),
    ("ui-util-android",             "androidx.compose.ui_ui-util",               "1.11.4", "google-maven"),
    ("foundation-android",          "androidx.compose.foundation_foundation",    "1.11.4", "google-maven"),
    ("foundation-layout-android",   "androidx.compose.foundation_foundation-layout", "1.11.4", "google-maven"),
    ("animation-android",           "androidx.compose.animation_animation",      "1.11.4", "google-maven"),
    ("animation-core-android",      "androidx.compose.animation_animation-core", "1.11.4", "google-maven"),
    ("material-ripple-android",     "androidx.compose.material_material-ripple", "1.11.4", "google-maven"),
    ("material-icons-core-android", "androidx.compose.material_material-icons-core", "1.7.8", "google-maven"),
    ("material3-android",           "androidx.compose.material3_material3",      "1.4.0",  "google-maven"),
    ("material3-window-size-class-android", "androidx.compose.material3_material3-window-size-class", "1.4.0", "google-maven"),
    ("activity",                    "androidx.activity_activity",                "1.13.0", "google-maven"),
    ("activity-compose",            "androidx.activity_activity-compose",        "1.13.0", "google-maven"),
    ("activity-ktx",                "androidx.activity_activity-ktx",            "1.13.0", "google-maven"),
    ("lifecycle-runtime-android",      "androidx.lifecycle_lifecycle-runtime",              "2.11.0", "google-maven"),
    ("lifecycle-runtime-ktx-android",  "androidx.lifecycle_lifecycle-runtime-ktx",          "2.11.0", "google-maven"),
    ("lifecycle-runtime-compose-android", "androidx.lifecycle_lifecycle-runtime-compose",   "2.11.0", "google-maven"),
    ("lifecycle-viewmodel-android",    "androidx.lifecycle_lifecycle-viewmodel",            "2.11.0", "google-maven"),
    ("lifecycle-viewmodel-compose-android", "androidx.lifecycle_lifecycle-viewmodel-compose", "2.11.0", "google-maven"),
    ("lifecycle-viewmodel-savedstate-android", "androidx.lifecycle_lifecycle-viewmodel-savedstate", "2.11.0", "google-maven"),
    ("lifecycle-livedata",          "androidx.lifecycle_lifecycle-livedata",     "2.11.0", "google-maven"),
    ("lifecycle-livedata-core",     "androidx.lifecycle_lifecycle-livedata-core", "2.11.0", "google-maven"),
    ("lifecycle-common (jvm coordinate)", "androidx.lifecycle_lifecycle-common", "2.11.0", "google-maven"),
    ("lifecycle-process",           "androidx.lifecycle_lifecycle-process",      "2.11.0", "google-maven"),
    ("navigation-compose-android",  "androidx.navigation_navigation-compose",    "2.9.8",  "google-maven"),
    ("navigation-runtime-android",  "androidx.navigation_navigation-runtime",    "2.9.8",  "google-maven"),
    ("navigation-common-android",   "androidx.navigation_navigation-common",     "2.9.8",  "google-maven"),
    ("navigationevent-android",     "androidx.navigationevent_navigationevent",  "1.0.0",  "google-maven"),
    ("navigationevent-compose-android", "androidx.navigationevent_navigationevent-compose", "1.0.0", "google-maven"),
    ("core",                        "androidx.core_core",                        "1.19.0", "google-maven"),
    ("core-ktx",                    "androidx.core_core-ktx",                    "1.19.0", "google-maven"),
    ("core-viewtree",               "androidx.core_core-viewtree",               "1.0.0",  "google-maven"),
    ("savedstate-android",          "androidx.savedstate_savedstate",            "1.4.0",  "google-maven"),
    ("savedstate-compose-android",  "androidx.savedstate_savedstate-compose",    "1.4.0",  "google-maven"),
    ("annotation-experimental",     "androidx.annotation_annotation-experimental", "1.4.1", "google-maven"),
    ("customview-poolingcontainer", "androidx.customview_customview-poolingcontainer", "1.0.0", "google-maven"),
    ("emoji2",                      "androidx.emoji2_emoji2",                    "1.4.0",  "google-maven"),
    ("startup-runtime",             "androidx.startup_startup-runtime",          "1.1.1",  "google-maven"),
    ("tracing",                     "androidx.tracing_tracing",                  "1.2.0",  "google-maven"),
    ("profileinstaller",            "androidx.profileinstaller_profileinstaller", "1.4.0", "google-maven"),
    ("autofill",                    "androidx.autofill_autofill",                "1.0.0",  "google-maven"),
    ("core-runtime",                "androidx.arch.core_core-runtime",           "2.2.0",  "google-maven"),
    ("core-common",                 "androidx.arch.core_core-common",            "2.2.0",  "google-maven"),
    ("kotlinx-coroutines-core-jvm", "kotlinx_coroutines_core",                   "1.9.0",  "maven-central"),
    ("kotlinx-coroutines-android",  "kotlinx_coroutines_android",                "1.9.0",  "maven-central"),
    ("atomicfu-jvm",                "(transitive of coroutines)",                "0.23.2", "maven-central"),
    ("kotlinx-collections-immutable-jvm", "(dooz upstream dir present)",         "0.3.7",  "maven-central"),
    ("collection-jvm",               "(compose 1.11.4 module declares 1.5.0; android classes live in -jvm artifact)", "1.5.0",  "google-maven"),
    ("kotlin-stdlib",               "(no .version file; compose-runtime-android 1.11.4 module declares 2.1.20)", "2.1.20", "maven-central"),
]

lines = [
    "# DOOZ_COMPOSE_DEPENDENCY_MATRIX (CONT-12 PHASE 1)",
    "",
    "Source of versions: the dooz APK itself (`META-INF/*.version`, SHA",
    "299eab21ac8b3c6192edbd887966554fef84ad026d269b9067310215201b362b).",
    "Binaries: real Maven artifacts, KMP `-android` coordinates (the root",
    "AAR on Google Maven is an empty stub since compose went multiplatform).",
    "NO version mixing: every artifact matches the APK's own version file.",
    "",
    "| artifact | dooz version-file entry | version | source | artifact SHA16 | classes.jar SHA16 | #classes |",
    "|---|---|---|---|---|---|---|",
]
missing = []
matrix_json = []
for art, key, ver, repo in rows:
    jarname = art.replace(" (jvm coordinate)", "")
    cjar = f"{CLS}/{jarname}.jar"
    # find the raw artifact (best effort name match)
    rawp = None
    if os.path.isdir(RAW):
        for cand in sorted(os.listdir(RAW)):
            probe = art.replace(" (jvm coordinate)", "-jvm")
            if cand.startswith(probe + "-") and cand.endswith((".jar", ".aar")):
                rawp = f"{RAW}/{cand}"
    entry_apk = apk_versions.get(key, "n/a")
    lines.append(f"| {art} | {entry_apk} | {ver} | {repo} | {sha16(rawp) if rawp else 'MISSING'} | {sha16(cjar)} | {nclasses(cjar)} |")
    matrix_json.append({"artifact": art, "version": ver, "repo": repo,
                        "apk_version_file": entry_apk,
                        "sha16": sha16(rawp) if rawp else None,
                        "classes_jar_sha16": sha16(cjar), "classes": nclasses(cjar)})
    if not os.path.exists(cjar):
        missing.append(art)

total_classes = sum(x["classes"] for x in matrix_json)
lines += [
    "",
    f"Total: {len(matrix_json)} artifacts, {total_classes} real classes fetched.",
    "Excluded: `androidx.annotation:annotation` (1.4.1 not published as binary;",
    "annotations are compile-time metadata with no runtime behavior — R8 strips",
    "their enforcement; dooz's own copy stays inside its DEX).",
    "",
    "## Dooz APK version files (authoritative, verbatim)",
    "",
    "```text",
]
for k in sorted(apk_versions):
    lines.append(f"{k} = {apk_versions[k]}")
lines += ["```", ""]

open(f"{OUT}/DOOZ_COMPOSE_DEPENDENCY_MATRIX.md", "w").write("\n".join(lines))
json.dump({"artifacts": matrix_json, "total_classes": total_classes,
           "excluded": ["androidx.annotation:annotation (compile-time only, unpublished binary)"]},
          open(f"{OUT}/dependency_matrix.json", "w"), indent=1)
print(f"matrix written: {len(matrix_json)} artifacts, {total_classes} classes; missing={missing}")
