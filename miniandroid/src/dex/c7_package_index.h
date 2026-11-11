// c7_package_index.h — CODER7 WAVE-5: PMS-LITE (cross-package component index)
//
// ─────────────────────────────────────────────────────────────────────────────
// LAW (AOSP frameworks/base PackageManagerService + IntentResolver):
//
// The engine before WAVE-5 was a ONE-package engine: every resolution
// candidate came from the running APK's own manifest, and
// getInstalledPackages / getInstalledApplications / queryContentProviders
// answered a FABRICATED always-empty list. On a real device the package
// manager resolves across ALL installed packages: browser pickers, choosers,
// share flows, plugin/discovery flows and cross-app provider lookups are all
// cross-package resolutions. This module is the generic (no per-app
// special-casing) fix: a multi-package component index with the SAME WAVE-3
// match law, plus a REAL-SQLite parse cache — the S185 SQLITE RULE move
// (issue #536): vend the real libsqlite3 (already linked) instead of
// hand-rolling a storage format; the AOSP pattern implemented is PMS's
// package cache: parse each APK's manifest once, then load the cached
// normalized tables on every boot (⇒ faster app load; cache=HIT/MISS rows
// are machine-checkable evidence).
//
// Honesty laws carried over from the WAVE-2/3 work:
//   * disabled components (android:enabled=false) are invisible to every
//     query (PackageItemInfo.isEnabled);
//   * MATCH_DEFAULT_ONLY requires the MATCHING filter to declare
//     android.intent.category.DEFAULT (AOSP startActivity resolution);
//   * MIME matching is AOSP MimeUtils.mimeMatches (exact, "type/*", "*/*");
//   * exported/enabled are served verbatim from the manifest;
//   * ingestion failures are LOUD (C7-STORE-ERR trace rows) — never silent.
// ─────────────────────────────────────────────────────────────────────────────
#ifndef MINIANDROID_C7_PACKAGE_INDEX_H
#define MINIANDROID_C7_PACKAGE_INDEX_H

#include <cstddef>
#include <map>
#include <string>
#include <vector>

#include "../apk/manifest_reader.h"

namespace miniandroid {
namespace dalvik {

// The <data> match dimensions of one <intent-filter> (IntentFilter.matchData).
struct C7IdxDataSpec {
    std::string mime_type;
    std::string scheme;
    std::string host;
    std::string path_prefix;
};

// One <intent-filter> record (the matchable unit — AOSP PackageParser keeps
// every filter element as its own matchable entity).
struct C7IdxFilter {
    std::vector<std::string> actions;
    std::vector<std::string> categories;
    std::vector<C7IdxDataSpec> datas;
    int priority = 0;
};

struct C7IdxActivity {
    std::string cls;               // dotted class name
    bool enabled = true;
    bool exported = false;
    int launch_mode = 0;           // 0 standard .. 3 singleInstance
    // CODER7 WAVE-12 (AOSP ActivityInfo.parentActivityName): the parent
    // chain link the TaskStackBuilder.addParentStack walk follows.
    std::string parent_activity_name;
    std::vector<C7IdxFilter> filters;
};

struct C7IdxService {
    std::string cls;
    bool enabled = true;
    bool exported = false;
    std::string permission;
    // CODER7 WAVE-12 (AOSP ServiceInfo.foregroundServiceType): the
    // manifest-declared FGS type bitmask (0 = none declared).
    int foreground_service_type = 0;
    std::vector<C7IdxFilter> filters;
};

struct C7IdxReceiver {
    std::string cls;
    bool enabled = true;
    bool exported = false;
    bool has_exported_attr = false;
    std::string permission;
    int priority = 0;              // receiver-level MAX (dispatch union law)
    std::vector<C7IdxFilter> filters;
};

struct C7IdxProvider {
    std::string cls;
    std::string package_name;   // OWNING package (ProviderInfo.packageName)
    std::string authorities;
    bool exported = false;
    bool enabled = true;
    bool grant_uri_permissions = false;
    // CODER7 WAVE-8 L1: android:readPermission / android:writePermission
    // (AOSP ProviderInfo; the CRUD transport gates each op on them —
    // checkContentProviderAccess law).
    std::string read_permission;
    std::string write_permission;
    // CODER7 WAVE-11 (AOSP ProviderIntentResolver): the provider's
    // intent-filters — the matchable unit for
    // PackageManager.queryIntentContentProviders (the W3 match law
    // reused verbatim; empty filters ⇒ the provider never matches an
    // intent — the AOSP shape for filter-less providers).
    std::vector<C7IdxFilter> filters;
};

struct C7IdxPackage {
    std::string package_name;
    std::string apk_path;
    // CODER7 WAVE-9 (AOSP ApplicationInfo.isEnabled): the application-
    // level disable — false hides EVERY component from resolution and
    // delivery (the effective-enabled law below).
    bool app_enabled = true;
    std::vector<std::string> permissions;
    std::vector<C7IdxActivity> activities;
    std::vector<C7IdxService> services;
    std::vector<C7IdxReceiver> receivers;
    std::vector<C7IdxProvider> providers;
};

// One matched candidate (the AOSP IntentResolver result shape).
struct C7IdxMatch {
    std::string package_name;
    std::string cls;
    bool exported = false;
    int launch_mode = 0;
    int priority = 0;
};

class C7PackageIndex {
public:
    struct IngestStats {
        int packages_cold = 0;    // AXML-parsed + written to the SQLite cache
        int packages_warm = 0;    // loaded from the SQLite cache payload
        int packages_failed = 0;  // loud C7-STORE-ERR rows (never silent)
    };

    // Ingest every *.apk in `dir` (deterministic: sorted by file name).
    // `cache_db` empty ⇒ no cache (pure parse). Each APK: cache key is
    // (apk_path, apk_size, apk_mtime); a matching cached payload whose
    // manifest_sha equals the current manifest bytes' SHA-256 loads from
    // SQLite without re-parsing the AXML.
    IngestStats ingest_store_dir(const std::string& dir,
                                 const std::string& cache_db);

    // CODER7 WAVE-8 L3: the engine's OWN install store (AOSP /data/app
    // scan law) — <root>/data/app/<pkg>/*.apk, discovered RECURSIVELY
    // (the deterministic install mapping <data-root>/data/app/<pkg>/
    // base.apk nests one level deeper than the flat store dir). Same
    // cache + loud-row contract as ingest_store_dir.
    IngestStats ingest_install_store(const std::string& data_root,
                                     const std::string& cache_db);

    // Ingest one APK (with the same cache contract).
    bool ingest_apk(const std::string& apk_path, const std::string& cache_db);

    // Register the RUNNING package from its already-parsed ManifestInfo so
    // cross-package resolution sees self too (AOSP: PMS resolves across ALL
    // installed packages, including the caller's own). Insert-or-replace by
    // package name (AOSP: one live record per package).
    void register_own_package(const apk::ManifestInfo& mi,
                              const std::string& apk_path);

    // ── Queries (WAVE-3 match law, cross-package) ────────────────────────
    // The law: action must be declared; every intent category must be
    // declared by the filter; MATCH_DEFAULT_ONLY requires CATEGORY_DEFAULT
    // on the MATCHING filter; data matching follows IntentFilter.matchData
    // (MIME half + scheme/host/pathPrefix half). Disabled components are
    // invisible. Ordering: higher filter priority first (stable within the
    // same priority — ingest order), matching the AOSP IntentResolver
    // priority refinement that WAVE-3 documented as the best-match law.
    std::vector<C7IdxMatch> query_activities(const std::string& action,
                                             const std::vector<std::string>& cats,
                                             const std::string& type,
                                             const std::string& scheme,
                                             const std::string& host,
                                             const std::string& path,
                                             bool default_only) const;
    std::vector<C7IdxMatch> query_services(const std::string& action,
                                           const std::vector<std::string>& cats,
                                           const std::string& type,
                                           const std::string& scheme,
                                           const std::string& host,
                                           const std::string& path,
                                           bool default_only) const;
    std::vector<C7IdxMatch> query_receivers(const std::string& action,
                                            const std::vector<std::string>& cats,
                                            const std::string& type,
                                            const std::string& scheme,
                                            const std::string& host,
                                            const std::string& path,
                                            bool default_only) const;

    // AOSP PackageManagerService provider map: resolveContentProvider maps
    // ONE authority to the provider that declared it. ProviderInfo.authorities
    // can be a space-separated list; the map records every authority. Only
    // ENABLED providers are published (WAVE-3 disabled-components law).
    std::vector<C7IdxProvider> providers_for_authority(
        const std::string& authority) const;

    const C7IdxPackage* find_package(const std::string& name) const;
    std::vector<std::string> package_names() const;  // insertion order
    size_t package_count() const { return packages_.size(); }
    bool empty() const { return packages_.empty(); }
    // CODER7 WAVE-8 L4: read-only package view (the launch drain's
    // foreign launchMode law reads C7IdxActivity.launch_mode per store
    // package; insertion order = ingest order, deterministic).
    const std::vector<C7IdxPackage>& packages() const { return packages_; }

    // ── Evidence ─────────────────────────────────────────────────────────
    // Deterministic ingest fingerprint for the probe verdicts: one row per
    // package "pkg:apk basename:cold/warm" in ingest order.
    std::string ingest_fingerprint() const;
    int last_ingest_cold() const { return last_stats_.packages_cold; }
    int last_ingest_warm() const { return last_stats_.packages_warm; }
    int last_ingest_failed() const { return last_stats_.packages_failed; }

    // The shared match law — also used by the engine wiring (single source
    // of truth for the cross-package and single-package paths alike).
    static bool mime_matches(const std::string& spec, const std::string& type);
    static bool filter_matches(const std::vector<C7IdxFilter>& filters,
                               const std::string& action,
                               const std::vector<std::string>& cats,
                               const std::string& type,
                               const std::string& scheme,
                               const std::string& host,
                               const std::string& path,
                               bool default_only);

private:
    std::vector<C7IdxPackage> packages_;          // insertion order
    std::map<std::string, size_t> by_name_;       // package → index
    IngestStats last_stats_;

    bool parse_apk_into(const std::string& apk_path, C7IdxPackage& out) const;
    // Returns: 1 = loaded from cache, 0 = cache miss, -1 = cache error.
    int cache_load(const std::string& db, const std::string& apk_path,
                   const std::string& manifest_sha, size_t apk_size,
                   long long apk_mtime, C7IdxPackage& out) const;
    bool cache_upsert(const std::string& db, const std::string& apk_path,
                      const std::string& manifest_sha, size_t apk_size,
                      long long apk_mtime, const C7IdxPackage& pkg) const;
    void upsert(C7IdxPackage&& pkg);
};

}  // namespace dalvik
}  // namespace miniandroid

#endif  // MINIANDROID_C7_PACKAGE_INDEX_H
