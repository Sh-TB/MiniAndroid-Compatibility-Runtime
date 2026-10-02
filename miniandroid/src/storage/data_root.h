// data_root.h — M3 FINDING-012: ONE app-data root law for the whole runtime.
//
// ─────────────────────────────────────────────────────────────────────────
// LAW (AOSP frameworks/base, Context / Environment):
//   * Android anchors EVERY app's private storage at /data/data/<pkg>/
//     (getFilesDir, getCacheDir, getDatabasePath, getSharedPreferences
//     all resolve inside it). The anchor belongs to the DEVICE INSTANCE,
//     never to the invoking shell's CWD.
//   * MiniAndroid previously resolved all three storage consumers
//     (DatabaseShadow, SharedPreferences XML store, FileSandbox /
//     ApplicationContext) against the CWD-relative literal
//     "runtime/data". Consequence (observed on microtimer): two runs
//     launched from the same directory silently shared one SQLite file —
//     run 2 loaded run 1's Room rows and rendered a different first
//     frame, breaking the 3-run byte-determinism gate; the prior
//     session's identical runs were an ACCIDENT of launching from
//     different CWDs, not a protocol guarantee.
//   * LAW FIX: a single process-wide app-data root, default
//     "runtime/data" (back-compat), overridable per invocation via
//     --data-root <dir> or MINIANDROID_DATA_ROOT. Storage consumers must
//     NEVER hardcode the root literal again.
// ─────────────────────────────────────────────────────────────────────────
#ifndef MINIANDROID_DATA_ROOT_H
#define MINIANDROID_DATA_ROOT_H

#include <filesystem>
#include <string>

namespace Storage {

/// Set the process-wide app-data root (one anchor for sqlite, prefs,
/// files). Forwards to DatabaseShadow::set_databases_dir so the sqlite
/// family obeys the same law. Creates the directory.
void set_app_data_root(const std::string& root);

/// Current app-data root (default "runtime/data" until overridden).
const std::string& app_data_root();

/// True once an explicit --data-root / env override was applied.
bool app_data_root_explicit();

// ═══════════════════════════════════════════════════════════════════════
// F-NEW-234 — PER-PACKAGE CONTEXT LAW (AOSP ContextImpl semantics).
//
// AOSP law (frameworks/base core/java/android/app/ContextImpl.java):
//   * getFilesDir()        → /data/user/0/<package>/files
//   * getCacheDir()        → /data/user/0/<package>/cache
//   * getSharedPreferences → /data/data/<package>/shared_prefs (prefs xml)
//   * getDatabasePath()    → /data/user/0/<package>/databases/<name>
//   * getDir(name, mode)   → /data/user/0/<package>/app_<name>
//   * getExternalFilesDir  → /storage/emulated/0/Android/data/<package>/files
//   * getExternalCacheDir  → /storage/emulated/0/Android/data/<package>/cache
// EVERY Context-anchored directory family is scoped to the RUNNING
// package. Before F-NEW-234 MiniAndroid resolved these from a single flat
// process root with per-site ad-hoc scoping (files/cache flat = cross-
// package contamination; prefs under <root>/<pkg>; the F-NEW-231 install
// created <root>/data/data/<pkg>/* that NO runtime consumer ever read —
// proven live by the IAPK-0 STATE B→C diff).
//
// MiniAndroid mapping (documented deviation, mirrors the F-NEW-231 store
// law): the package data dir is <app-data-root>/data/data/<package>/ and
// the shared external volume is <app-data-root>/storage/emulated/0/.
// ═══════════════════════════════════════════════════════════════════════

/// Bind the RUNNING package identity. All Context-anchored directory
/// families now resolve inside <root>/data/data/<pkg>/. Also re-points
/// DatabaseShadow::set_databases_dir at the package databases dir and
/// creates the AOSP framework dirs (files/cache/shared_prefs/databases/
/// code_cache/no_backup). Empty string resets to the legacy flat root.
void set_context_package(const std::string& package);

/// The bound running package ("" = none bound → legacy flat resolution).
const std::string& context_package();

/// The running package's private data dir:
///   <root>/data/data/<pkg>   (package bound)
///   <root>                   (no package — legacy flat behavior)
std::filesystem::path package_data_dir();

/// Context-anchored subdirectory (files/cache/shared_prefs/databases/
/// app_<name>/...): package_data_dir() / sub. sub may be "" (the dir
/// itself). No-package fallback: <root>/<sub>.
std::filesystem::path context_dir(const std::string& sub);

/// External app-specific directory (AOSP Android/data/<pkg>/<kind>):
///   kind = "files" | "cache" | "media"
/// No-package fallback keeps the legacy flat <root>/external_<leaf> shape.
std::filesystem::path external_app_dir(const std::string& kind);

/// External OBB directory (AOSP Android/obb/<pkg>).
std::filesystem::path external_obb_dir();

// ═══════════════════════════════════════════════════════════════════════
// LOADING-CAMPAIGN (2026-10-03) — ONE CANONICAL ANDROID-PATH LAW.
//
// AOSP law (frameworks/base + libcore): an application-supplied absolute
// path is resolved by the KERNEL inside the app's mount namespace. The
// app can only see:
//   /data/data/<pkg>  ==  /data/user/0/<pkg>   (user-0 alias, same inode)
//   /data/user/<id>/<pkg>                        (per-user homes)
//   /data/user_de/0/<pkg>                        (device-protected)
//   /data/app/.../<pkg>/base.apk                 (its own installed code)
//   /storage/emulated/0/...                      (external volume, FUSE)
//   /system/*, /apex/*, /product/*, /vendor/*    (read-only system image)
//   a handful of device nodes                    (/dev/urandom, /dev/random,
//                                                 /dev/null, /dev/zero)
// ANY OTHER absolute host path (e.g. /etc/passwd, /home, /proc, /tmp on
// the host) is NOT part of the app's namespace and cannot be opened —
// attempts answer ABSENT / EACCES, never silent host access.
//
// MiniAndroid mapping (the ONE authoritative translation; every consumer
// — File family, streams, BitmapFactory, SQLite, prefs, fonts, URI — must
// route through resolve_android_path; no subsystem may invent its own):
//   /data/{data,user/0,user/<id>,user_de/0}/<pkg>/… → <root>/data/data/<pkg>/…
//   /data/app/…base.apk                             → <root>/data/app/<pkg>/base.apk
//   /storage/emulated/0/…                           → <root>/storage/emulated/0/…
//   /system/fonts/<name>                            → <root>/system/fonts/<name>
//   /dev/{urandom,random,null,zero}                 → host node (same semantics)
//   anything else absolute                          → DENIED
// ═══════════════════════════════════════════════════════════════════════

enum class PathCategory {
    RELATIVE_APP_DATA,   // relative path — anchored at the package data dir
    SANDBOX_DATA,        // /data/data|/data/user/<id>|/data/user_de/0 + pkg
    INSTALLED_APK,       // /data/app/**/base.apk (F-NEW-231 store backing)
    VIRTUAL_EXTERNAL,    // /storage/emulated/0/**
    SYSTEM_IMAGE,        // /system/fonts/** (virtual system image backing)
    DEVICE_NODE,         // /dev/urandom|random|null|zero (host node, AOSP-legal)
    DENIED_HOST_PATH     // any other absolute host path — NOT in the namespace
};

struct PathResolution {
    PathCategory category = PathCategory::DENIED_HOST_PATH;
    std::filesystem::path host_path;  // the physical backing path (allowed cases)
    bool allowed = false;             // false → the Android-failure contract
};

/// THE canonical Android-logical → MiniAndroid-physical mapping.
/// `logical` may be relative (anchored to the running package data dir —
/// R-NEW-346/F-NEW-234 sandbox anchor) or absolute (resolved through the
/// category table above; unknown absolute paths come back DENIED).
PathResolution resolve_android_path(const std::string& logical);

} // namespace Storage

#endif // MINIANDROID_DATA_ROOT_H
