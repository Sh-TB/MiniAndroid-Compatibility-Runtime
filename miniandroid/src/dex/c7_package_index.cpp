// c7_package_index.cpp — CODER7 WAVE-5: PMS-LITE implementation.
// See c7_package_index.h for the law text.
//
// Storage law (S185 SQLITE RULE, issue #536): the parse cache is REAL
// libsqlite3 (the same vendored library the SQLiteDatabase shadow runs app
// SQL on) — no hand-rolled binary format. Hash law: EVP SHA-256 (the
// BUILD-TRAIN direct-consumption law; no custom hash).

#include "c7_package_index.h"

#include <dirent.h>
#include <sys/stat.h>

#include <algorithm>
#include <cstdio>
#include <filesystem>  // CODER7 W8-L3: recursive /data/app walk

#include <openssl/evp.h>
#include <sqlite3.h>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"
#include "../apk/apk_parser.h"
#include "../diagnostics/file_io_trace.h"

namespace miniandroid {
namespace dalvik {

using nlohmann::json;

namespace {

// BUILD-TRAIN law: EVP sha256, direct consumption.
std::string sha256_hex(const std::vector<uint8_t>& data) {
    unsigned char md[EVP_MAX_MD_SIZE];
    unsigned int md_len = 0;
    if (!EVP_Digest(data.data(), data.size(), md, &md_len, EVP_sha256(),
                    nullptr))
        return "";
    static const char* hex = "0123456789abcdef";
    std::string out;
    out.reserve(md_len * 2);
    for (unsigned int i = 0; i < md_len; ++i) {
        out.push_back(hex[md[i] >> 4]);
        out.push_back(hex[md[i] & 0x0f]);
    }
    return out;
}

void store_row(const char* tag, const std::string& what, bool ok,
               const std::string& detail) {
    // Loud engine rows: FileIoTrace (machine-readable export) + stderr
    // (run.log). Ingestion failures are NEVER silent.
    diagnostics::FileIoTrace::instance().record(tag, what, ok, detail,
                                                "C7PackageIndex");
    std::fprintf(stderr, "[%s] %s ok=%d %s\n", tag, what.c_str(), ok ? 1 : 0,
                 detail.c_str());
}

std::string basename_of(const std::string& path) {
    size_t p = path.find_last_of("/\\");
    return p == std::string::npos ? path : path.substr(p + 1);
}

// The execution_engine.cpp name-normalization law (AOSP PackageParser class
// resolution): ".Foo" and "Foo" resolve against the package name.
std::string norm_component_class(const std::string& pkg, const std::string& n) {
    if (n.empty()) return n;
    if (n[0] == '.') return pkg + n;
    if (n.find('.') == std::string::npos) return pkg + "." + n;
    return n;
}

// ── JSON (de)serialization of one package record (the cache payload) ──────
json data_spec_json(const C7IdxDataSpec& d) {
    json j = json::object();
    j["m"] = d.mime_type;
    j["s"] = d.scheme;
    j["h"] = d.host;
    j["p"] = d.path_prefix;
    return j;
}

C7IdxDataSpec data_spec_from(const json& j) {
    C7IdxDataSpec d;
    d.mime_type = j.value("m", "");
    d.scheme = j.value("s", "");
    d.host = j.value("h", "");
    d.path_prefix = j.value("p", "");
    return d;
}

json filter_json(const C7IdxFilter& f) {
    json j = json::object();
    j["a"] = f.actions;
    j["c"] = f.categories;
    j["pr"] = f.priority;
    json ds = json::array();
    for (const auto& d : f.datas) ds.push_back(data_spec_json(d));
    j["d"] = ds;
    return j;
}

C7IdxFilter filter_from(const json& j) {
    C7IdxFilter f;
    if (j.contains("a") && j["a"].is_array())
        for (const auto& x : j["a"]) f.actions.push_back(x.get<std::string>());
    if (j.contains("c") && j["c"].is_array())
        for (const auto& x : j["c"])
            f.categories.push_back(x.get<std::string>());
    f.priority = j.value("pr", 0);
    if (j.contains("d") && j["d"].is_array())
        for (const auto& x : j["d"]) f.datas.push_back(data_spec_from(x));
    return f;
}

json package_to_json(const C7IdxPackage& p) {
    json j = json::object();
    j["pkg"] = p.package_name;
    j["apk"] = p.apk_path;
    // CODER7 WAVE-9: the application-level disable rides the cache
    // (x.value("aen", true) default keeps pre-W9 payloads WARM-compatible).
    j["aen"] = p.app_enabled;
    j["perms"] = p.permissions;
    json acts = json::array();
    for (const auto& a : p.activities) {
        json ja = json::object();
        ja["cls"] = a.cls;
        ja["en"] = a.enabled;
        ja["ex"] = a.exported;
        ja["lm"] = a.launch_mode;
        // CODER7 WAVE-12: the parent-chain link (empty = none — the
        // cache payload stays byte-stable for type-less components).
        ja["pan"] = a.parent_activity_name;
        json fs = json::array();
        for (const auto& f : a.filters) fs.push_back(filter_json(f));
        ja["f"] = fs;
        acts.push_back(ja);
    }
    j["acts"] = acts;
    json svcs = json::array();
    for (const auto& s : p.services) {
        json js = json::object();
        js["cls"] = s.cls;
        js["en"] = s.enabled;
        js["ex"] = s.exported;
        // CODER7 WAVE-12: the manifest FGS type bitmask (0 when the
        // component declares none — WARM payloads stay compatible).
        js["fst"] = s.foreground_service_type;
        js["perm"] = s.permission;
        json fs = json::array();
        for (const auto& f : s.filters) fs.push_back(filter_json(f));
        js["f"] = fs;
        svcs.push_back(js);
    }
    j["svcs"] = svcs;
    json rcvs = json::array();
    for (const auto& r : p.receivers) {
        json jr = json::object();
        jr["cls"] = r.cls;
        jr["en"] = r.enabled;
        jr["ex"] = r.exported;
        jr["hex"] = r.has_exported_attr;
        jr["perm"] = r.permission;
        jr["pr"] = r.priority;
        json fs = json::array();
        for (const auto& f : r.filters) fs.push_back(filter_json(f));
        jr["f"] = fs;
        rcvs.push_back(jr);
    }
    j["rcvs"] = rcvs;
    json provs = json::array();
    for (const auto& pr : p.providers) {
        json jp = json::object();
        jp["cls"] = pr.cls;
        jp["pkg"] = pr.package_name;
        jp["auth"] = pr.authorities;
        jp["ex"] = pr.exported;
        jp["en"] = pr.enabled;
        jp["grant"] = pr.grant_uri_permissions;
        // CODER7 WAVE-8 L1: provider read/write permissions ride the cache
        // payload (x.value defaults "" on pre-W8 payloads — WARM-cache
        // backward compatible).
        jp["rp"] = pr.read_permission;
        jp["wp"] = pr.write_permission;
        // CODER7 WAVE-11: provider intent-filters ride the cache payload
        // (x.contains("f") default empty on pre-W11 payloads — WARM-cache
        // backward compatible, the same law as the W8 rp/wp keys).
        json pf = json::array();
        for (const auto& f : pr.filters) pf.push_back(filter_json(f));
        jp["f"] = pf;
        provs.push_back(jp);
    }
    j["provs"] = provs;
    return j;
}

C7IdxPackage package_from_json(const json& j) {
    C7IdxPackage p;
    p.package_name = j.value("pkg", "");
    p.apk_path = j.value("apk", "");
    p.app_enabled = j.value("aen", true);
    if (j.contains("perms") && j["perms"].is_array())
        for (const auto& x : j["perms"])
            p.permissions.push_back(x.get<std::string>());
    if (j.contains("acts") && j["acts"].is_array())
        for (const auto& x : j["acts"]) {
            C7IdxActivity a;
            a.cls = x.value("cls", "");
            a.enabled = x.value("en", true);
            a.exported = x.value("ex", false);
            a.launch_mode = x.value("lm", 0);
            // CODER7 WAVE-12: the parent-chain link (pre-W11 payloads
            // have no "pan" key — default empty, WARM-cache compatible).
            a.parent_activity_name = x.value("pan", "");
            if (x.contains("f") && x["f"].is_array())
                for (const auto& f : x["f"]) a.filters.push_back(filter_from(f));
            p.activities.push_back(std::move(a));
        }
    if (j.contains("svcs") && j["svcs"].is_array())
        for (const auto& x : j["svcs"]) {
            C7IdxService s;
            s.cls = x.value("cls", "");
            s.enabled = x.value("en", true);
            s.exported = x.value("ex", false);
            s.permission = x.value("perm", "");
            // CODER7 WAVE-12: the manifest FGS type bitmask (pre-W11
            // payloads have no "fst" key — default 0, WARM-compatible).
            s.foreground_service_type = x.value("fst", 0);
            if (x.contains("f") && x["f"].is_array())
                for (const auto& f : x["f"]) s.filters.push_back(filter_from(f));
            p.services.push_back(std::move(s));
        }
    if (j.contains("rcvs") && j["rcvs"].is_array())
        for (const auto& x : j["rcvs"]) {
            C7IdxReceiver r;
            r.cls = x.value("cls", "");
            r.enabled = x.value("en", true);
            r.exported = x.value("ex", false);
            r.has_exported_attr = x.value("hex", false);
            r.permission = x.value("perm", "");
            r.priority = x.value("pr", 0);
            if (x.contains("f") && x["f"].is_array())
                for (const auto& f : x["f"]) r.filters.push_back(filter_from(f));
            p.receivers.push_back(std::move(r));
        }
    if (j.contains("provs") && j["provs"].is_array())
        for (const auto& x : j["provs"]) {
            C7IdxProvider pr;
            pr.cls = x.value("cls", "");
            pr.package_name = x.value("pkg", "");
            pr.authorities = x.value("auth", "");
            pr.exported = x.value("ex", false);
            pr.enabled = x.value("en", true);
            pr.grant_uri_permissions = x.value("grant", false);
            pr.read_permission = x.value("rp", "");
            pr.write_permission = x.value("wp", "");
            if (x.contains("f") && x["f"].is_array())
                for (const auto& f : x["f"])
                    pr.filters.push_back(filter_from(f));
            p.providers.push_back(std::move(pr));
        }
    return p;
}

// The SINGLE ManifestInfo → C7IdxPackage conversion (used by store
// ingestion, single-APK ingestion and the own-package registration alike —
// one mapping, no drift).
void fill_package_from_manifest(const apk::ManifestInfo& mi,
                                const std::string& apk_path,
                                C7IdxPackage& out) {
    out.package_name = mi.package_name;
    out.apk_path = apk_path;
    // CODER7 WAVE-9: the application-level disable rides the index.
    out.app_enabled = mi.application_enabled;
    out.permissions = mi.permissions;
    for (const auto& a : mi.activities) {
        C7IdxActivity ia;
        ia.cls = norm_component_class(mi.package_name, a.name);
        ia.enabled = a.enabled;
        ia.exported = a.exported;
        ia.launch_mode = a.launch_mode;
        // CODER7 WAVE-12: the parent-chain link, normalized to the
        // dotted absolute form (".Foo" → pkg.Foo) — the same
        // norm_component_class law every other component name rides.
        ia.parent_activity_name =
            norm_component_class(mi.package_name, a.parent_activity_name);
        for (const auto& f : a.filters) {
            C7IdxFilter ef;
            ef.actions = f.actions;
            ef.categories = f.categories;
            // CODER7 WAVE-8 L4: the activity filter's priority rides the
            // index (the resolution ordering refines by it).
            ef.priority = f.priority;
            for (const auto& d : f.datas) {
                C7IdxDataSpec ds;
                ds.mime_type = d.mime_type;
                ds.scheme = d.scheme;
                ds.host = d.host;
                ds.path_prefix = d.path_prefix;
                ef.datas.push_back(std::move(ds));
            }
            ia.filters.push_back(std::move(ef));
        }
        out.activities.push_back(std::move(ia));
    }
    for (const auto& s : mi.services) {
        C7IdxService is;
        is.cls = norm_component_class(mi.package_name, s.name);
        is.enabled = s.enabled;
        is.exported = s.exported;
        is.permission = s.permission;
        // CODER7 WAVE-12: the manifest FGS type bitmask rides the index.
        is.foreground_service_type = s.foreground_service_type;
        for (const auto& f : s.filters) {
            C7IdxFilter ef;
            ef.actions = f.actions;
            ef.categories = f.categories;
            for (const auto& d : f.datas) {
                C7IdxDataSpec ds;
                ds.mime_type = d.mime_type;
                ds.scheme = d.scheme;
                ds.host = d.host;
                ds.path_prefix = d.path_prefix;
                ef.datas.push_back(std::move(ds));
            }
            is.filters.push_back(std::move(ef));
        }
        out.services.push_back(std::move(is));
    }
    for (const auto& r : mi.receivers) {
        C7IdxReceiver ir;
        ir.cls = norm_component_class(mi.package_name, r.name);
        ir.enabled = r.enabled;
        ir.exported = r.exported;
        ir.has_exported_attr = r.has_exported_attr;
        ir.permission = r.permission;
        ir.priority = r.priority;
        for (const auto& f : r.filters) {
            C7IdxFilter ef;
            ef.actions = f.actions;
            ef.categories = f.categories;
            ef.priority = f.priority;
            for (const auto& d : f.datas) {
                C7IdxDataSpec ds;
                ds.mime_type = d.mime_type;
                ds.scheme = d.scheme;
                ds.host = d.host;
                ds.path_prefix = d.path_prefix;
                ef.datas.push_back(std::move(ds));
            }
            ir.filters.push_back(std::move(ef));
        }
        out.receivers.push_back(std::move(ir));
    }
    for (const auto& pr : mi.providers) {
        C7IdxProvider ip;
        ip.cls = norm_component_class(mi.package_name, pr.name);
        ip.package_name = mi.package_name;
        ip.authorities = pr.authorities;
        ip.exported = pr.exported;
        ip.enabled = pr.enabled;
        ip.grant_uri_permissions = pr.grant_uri_permissions;
        ip.read_permission = pr.read_permission;
        ip.write_permission = pr.write_permission;
        // CODER7 WAVE-11: provider intent-filters into the index (the
        // queryIntentContentProviders match key).
        for (const auto& f : pr.filters) {
            C7IdxFilter ef;
            ef.actions = f.actions;
            ef.categories = f.categories;
            for (const auto& d : f.datas) {
                C7IdxDataSpec ds;
                ds.mime_type = d.mime_type;
                ds.scheme = d.scheme;
                ds.host = d.host;
                ds.path_prefix = d.path_prefix;
                ef.datas.push_back(std::move(ds));
            }
            ip.filters.push_back(std::move(ef));
        }
        out.providers.push_back(std::move(ip));
    }
}

}  // namespace

// ── The WAVE-3 match law (single source of truth) ─────────────────────────

bool C7PackageIndex::mime_matches(const std::string& spec,
                                  const std::string& type) {
    if (spec.empty() || type.empty()) return false;
    if (spec == type) return true;
    if (spec == "*/*") return true;
    if (spec.size() > 1 && spec.back() == '*')
        return type.rfind(spec.substr(0, spec.size() - 1), 0) == 0;
    if (type.size() > 1 && type.back() == '*')
        return spec.rfind(type.substr(0, type.size() - 1), 0) == 0;
    return false;
}

bool C7PackageIndex::filter_matches(
    const std::vector<C7IdxFilter>& filters, const std::string& action,
    const std::vector<std::string>& cats, const std::string& type,
    const std::string& scheme, const std::string& host,
    const std::string& path, bool default_only) {
    if (action.empty()) return false;
    for (const auto& f : filters) {
        // (1) action half: the filter must declare the intent action.
        bool has = false;
        for (const auto& a : f.actions)
            if (a == action) {
                has = true;
                break;
            }
        if (!has) continue;
        // (2) category half: EVERY intent category must be declared
        //     (AOSP IntentFilter.matchCategories).
        bool cats_ok = true;
        for (const auto& ic : cats) {
            bool ok = false;
            for (const auto& fc : f.categories)
                if (fc == ic) {
                    ok = true;
                    break;
                }
            if (!ok) {
                cats_ok = false;
                break;
            }
        }
        if (!cats_ok) continue;
        // (3) MATCH_DEFAULT_ONLY: the MATCHING filter must declare
        //     CATEGORY_DEFAULT (AOSP startActivity resolution law).
        if (default_only) {
            bool dflt = false;
            for (const auto& fc : f.categories)
                if (fc == "android.intent.category.DEFAULT") {
                    dflt = true;
                    break;
                }
            if (!dflt) continue;
        }
        // (4) data half (IntentFilter.matchData): an empty <data> set
        //     matches only intents with no type and no scheme; otherwise
        //     the MIME half and the scheme/authority/path half are each
        //     satisfied by ANY matching <data> element.
        if (f.datas.empty()) {
            if (type.empty() && scheme.empty()) return true;
            continue;
        }
        bool filter_has_host = false;
        for (const auto& ds : f.datas)
            if (!ds.host.empty()) {
                filter_has_host = true;
                break;
            }
        bool scheme_ok = scheme.empty();
        bool type_ok = type.empty();
        bool auth_ok = host.empty() || !filter_has_host;
        for (const auto& ds : f.datas) {
            if (!scheme.empty() && ds.scheme == scheme) scheme_ok = true;
            if (!type.empty() && mime_matches(ds.mime_type, type))
                type_ok = true;
            if (!host.empty() && !ds.host.empty() && ds.host == host)
                auth_ok = ds.path_prefix.empty() ||
                          path.rfind(ds.path_prefix, 0) == 0;
        }
        if (scheme_ok && type_ok && auth_ok) return true;
    }
    return false;
}

namespace {
// Priority-aware candidate collection: AOSP IntentResolver orders matches by
// filter priority (higher first); WAVE-3 documented the refinement. Stable:
// same priority ⇒ ingest order.
void collect_ordered(std::vector<C7IdxMatch>& out, const std::string& pkg,
                     const std::string& cls, bool exported, int launch_mode,
                     int priority) {
    C7IdxMatch m;
    m.package_name = pkg;
    m.cls = cls;
    m.exported = exported;
    m.launch_mode = launch_mode;
    m.priority = priority;
    size_t i = 0;
    for (; i < out.size(); ++i)
        if (out[i].priority < priority) break;
    out.insert(out.begin() + static_cast<long>(i), std::move(m));
}
}  // namespace

std::vector<C7IdxMatch> C7PackageIndex::query_activities(
    const std::string& action, const std::vector<std::string>& cats,
    const std::string& type, const std::string& scheme,
    const std::string& host, const std::string& path,
    bool default_only) const {
    std::vector<C7IdxMatch> out;
    for (const auto& p : packages_) {
        // ── CODER7 WAVE-9 (AOSP ApplicationInfo.isEnabled=false): a
        // disabled APPLICATION hides EVERY component from resolution.
        if (!p.app_enabled) continue;
        for (const auto& a : p.activities) {
            if (!a.enabled) continue;  // disabled-components law
            if (!filter_matches(a.filters, action, cats, type, scheme, host,
                                path, default_only))
                continue;
            // AOSP: the query result priority is the MAX across the
            // component's matching filters.
            int best = 0;
            for (const auto& f : a.filters) best = std::max(best, f.priority);
            collect_ordered(out, p.package_name, a.cls, a.exported,
                            a.launch_mode, best);
        }
    }
    return out;
}

std::vector<C7IdxMatch> C7PackageIndex::query_services(
    const std::string& action, const std::vector<std::string>& cats,
    const std::string& type, const std::string& scheme,
    const std::string& host, const std::string& path,
    bool default_only) const {
    std::vector<C7IdxMatch> out;
    for (const auto& p : packages_) {
        if (!p.app_enabled) continue;  // WAVE-9 application-disable law
        for (const auto& s : p.services) {
            if (!s.enabled) continue;
            if (!filter_matches(s.filters, action, cats, type, scheme, host,
                                path, default_only))
                continue;
            int best = 0;
            for (const auto& f : s.filters) best = std::max(best, f.priority);
            collect_ordered(out, p.package_name, s.cls, s.exported, 0, best);
        }
    }
    return out;
}

std::vector<C7IdxMatch> C7PackageIndex::query_receivers(
    const std::string& action, const std::vector<std::string>& cats,
    const std::string& type, const std::string& scheme,
    const std::string& host, const std::string& path,
    bool default_only) const {
    std::vector<C7IdxMatch> out;
    for (const auto& p : packages_) {
        if (!p.app_enabled) continue;  // WAVE-9 application-disable law
        for (const auto& r : p.receivers) {
            if (!r.enabled) continue;
            if (!filter_matches(r.filters, action, cats, type, scheme, host,
                                path, default_only))
                continue;
            int best = 0;
            for (const auto& f : r.filters) best = std::max(best, f.priority);
            collect_ordered(out, p.package_name, r.cls, r.exported, 0, best);
        }
    }
    return out;
}

std::vector<C7IdxProvider> C7PackageIndex::providers_for_authority(
    const std::string& authority) const {
    std::vector<C7IdxProvider> out;
    if (authority.empty()) return out;
    for (const auto& p : packages_) {
        if (!p.app_enabled) continue;  // WAVE-9 application-disable law
        for (const auto& pr : p.providers) {
            if (!pr.enabled) continue;  // disabled ⇒ not published
            // ProviderInfo.authorities is a space-separated list; every
            // listed authority is resolvable (AOSP PMS provider map law).
            std::string tok;
            const std::string& auths = pr.authorities;
            bool hit = false;
            for (size_t i = 0; i <= auths.size(); ++i) {
                if (i == auths.size() || auths[i] == ' ' ||
                    auths[i] == ';') {
                    if (tok == authority) {
                        hit = true;
                        break;
                    }
                    tok.clear();
                } else {
                    tok.push_back(auths[i]);
                }
            }
            if (hit) out.push_back(pr);
        }
    }
    return out;
}

const C7IdxPackage* C7PackageIndex::find_package(
    const std::string& name) const {
    auto it = by_name_.find(name);
    if (it == by_name_.end()) return nullptr;
    return &packages_[it->second];
}

std::vector<std::string> C7PackageIndex::package_names() const {
    std::vector<std::string> out;
    out.reserve(packages_.size());
    for (const auto& p : packages_) out.push_back(p.package_name);
    return out;
}

std::string C7PackageIndex::ingest_fingerprint() const {
    std::string out;
    for (const auto& p : packages_) {
        if (!out.empty()) out.push_back('|');
        out += p.package_name;
        out.push_back(':');
        out += basename_of(p.apk_path);
    }
    return out;
}

void C7PackageIndex::upsert(C7IdxPackage&& pkg) {
    auto it = by_name_.find(pkg.package_name);
    if (it != by_name_.end()) {
        packages_[it->second] = std::move(pkg);  // insert-or-replace (AOSP)
        return;
    }
    by_name_[pkg.package_name] = packages_.size();
    packages_.push_back(std::move(pkg));
}

// ── Ingestion ─────────────────────────────────────────────────────────────

bool C7PackageIndex::parse_apk_into(const std::string& apk_path,
                                    C7IdxPackage& out) const {
    apk::ApkParser parser;
    std::vector<uint8_t> manifest =
        parser.extract_entry(apk_path, "AndroidManifest.xml");
    if (manifest.empty()) {
        store_row("C7-STORE-ERR", apk_path, false,
                  "no AndroidManifest.xml entry");
        return false;
    }
    apk::ManifestReader reader;
    apk::ManifestInfo mi = reader.parse(manifest);
    if (!mi.parse_success || mi.package_name.empty()) {
        store_row("C7-STORE-ERR", apk_path, false,
                  "manifest parse failed: " + mi.error_message);
        return false;
    }
    fill_package_from_manifest(mi, apk_path, out);
    return true;
}

int C7PackageIndex::cache_load(const std::string& db,
                               const std::string& apk_path,
                               const std::string& manifest_sha, size_t apk_size,
                               long long apk_mtime, C7IdxPackage& out) const {
    sqlite3* handle = nullptr;
    if (sqlite3_open(db.c_str(), &handle) != SQLITE_OK) {
        if (handle) sqlite3_close(handle);
        return -1;  // unreadable db — the caller treats this as a cold miss
    }
    int rc = -1;
    sqlite3_stmt* st = nullptr;
    const char* sql =
        "SELECT apk_size, apk_mtime, manifest_sha, payload FROM pkg_cache "
        "WHERE apk_path = ?1";
    if (sqlite3_prepare_v2(handle, sql, -1, &st, nullptr) == SQLITE_OK) {
        sqlite3_bind_text(st, 1, apk_path.c_str(), -1, SQLITE_TRANSIENT);
        if (sqlite3_step(st) == SQLITE_ROW) {
            size_t sz = static_cast<size_t>(sqlite3_column_int64(st, 0));
            long long mt = sqlite3_column_int64(st, 1);
            const char* sha_c =
                reinterpret_cast<const char*>(sqlite3_column_text(st, 2));
            const char* payload_c =
                reinterpret_cast<const char*>(sqlite3_column_text(st, 3));
            std::string sha = sha_c ? sha_c : "";
            std::string payload = payload_c ? payload_c : "";
            if (sz == apk_size && mt == apk_mtime && sha == manifest_sha &&
                !payload.empty()) {
                try {
                    out = package_from_json(json::parse(payload));
                    if (out.package_name.empty())
                        rc = 0;  // corrupt payload ⇒ cold re-parse
                    else
                        rc = 1;  // warm hit
                } catch (...) {
                    rc = 0;  // corrupt payload ⇒ cold re-parse
                }
            } else {
                rc = 0;  // stale row ⇒ cold re-parse
            }
        } else {
            rc = 0;  // no row ⇒ cold
        }
        sqlite3_finalize(st);
    } else {
        // Missing table = a fresh cache db ⇒ cold (not an error).
        rc = 0;
    }
    sqlite3_close(handle);
    return rc;
}

bool C7PackageIndex::cache_upsert(const std::string& db,
                                  const std::string& apk_path,
                                  const std::string& manifest_sha,
                                  size_t apk_size, long long apk_mtime,
                                  const C7IdxPackage& pkg) const {
    sqlite3* handle = nullptr;
    if (sqlite3_open(db.c_str(), &handle) != SQLITE_OK) {
        if (handle) sqlite3_close(handle);
        store_row("C7-STORE-ERR", db, false, "sqlite open failed (upsert)");
        return false;
    }
    bool ok = false;
    char* err = nullptr;
    if (sqlite3_exec(handle,
                     "CREATE TABLE IF NOT EXISTS pkg_cache("
                     "apk_path TEXT PRIMARY KEY, apk_size INTEGER NOT NULL, "
                     "apk_mtime INTEGER NOT NULL, manifest_sha TEXT NOT NULL, "
                     "payload TEXT NOT NULL)",
                     nullptr, nullptr, &err) == SQLITE_OK) {
        sqlite3_stmt* st = nullptr;
        const char* sql =
            "INSERT OR REPLACE INTO pkg_cache(apk_path, apk_size, apk_mtime, "
            "manifest_sha, payload) VALUES (?1, ?2, ?3, ?4, ?5)";
        if (sqlite3_prepare_v2(handle, sql, -1, &st, nullptr) == SQLITE_OK) {
            json payload = package_to_json(pkg);
            sqlite3_bind_text(st, 1, apk_path.c_str(), -1, SQLITE_TRANSIENT);
            sqlite3_bind_int64(st, 2, static_cast<sqlite3_int64>(apk_size));
            sqlite3_bind_int64(st, 3, apk_mtime);
            sqlite3_bind_text(st, 4, manifest_sha.c_str(), -1,
                              SQLITE_TRANSIENT);
            std::string body = payload.dump();
            sqlite3_bind_text(st, 5, body.c_str(), -1, SQLITE_TRANSIENT);
            ok = (sqlite3_step(st) == SQLITE_DONE);
            sqlite3_finalize(st);
        }
    } else {
        store_row("C7-STORE-ERR", db, false,
                  std::string("schema: ") + (err ? err : "?"));
    }
    if (err) sqlite3_free(err);
    sqlite3_close(handle);
    return ok;
}

bool C7PackageIndex::ingest_apk(const std::string& apk_path,
                                const std::string& cache_db) {
    // stat BEFORE reading (the cache key identity).
    struct stat sb;
    if (::stat(apk_path.c_str(), &sb) != 0) {
        store_row("C7-STORE-ERR", apk_path, false, "stat failed");
        ++last_stats_.packages_failed;
        return false;
    }
    size_t apk_size = static_cast<size_t>(sb.st_size);
    long long apk_mtime = static_cast<long long>(sb.st_mtime);

    // Manifest SHA is part of the cache contract (content identity, not just
    // stat identity) — computed on the raw manifest bytes.
    std::string manifest_sha;
    {
        apk::ApkParser parser;
        std::vector<uint8_t> manifest =
            parser.extract_entry(apk_path, "AndroidManifest.xml");
        if (manifest.empty()) {
            store_row("C7-STORE-ERR", apk_path, false,
                      "no AndroidManifest.xml entry");
            ++last_stats_.packages_failed;
            return false;
        }
        manifest_sha = sha256_hex(manifest);
    }

    C7IdxPackage pkg;
    bool warm = false;
    if (!cache_db.empty() &&
        cache_load(cache_db, apk_path, manifest_sha, apk_size, apk_mtime,
                   pkg) == 1) {
        warm = true;
        ++last_stats_.packages_warm;
    } else {
        if (!parse_apk_into(apk_path, pkg)) {
            ++last_stats_.packages_failed;
            return false;
        }
        if (!cache_db.empty()) {
            if (cache_upsert(cache_db, apk_path, manifest_sha, apk_size,
                             apk_mtime, pkg))
                ++last_stats_.packages_cold;
            else
                ++last_stats_.packages_failed;
        } else {
            ++last_stats_.packages_cold;
        }
    }
    upsert(std::move(pkg));
    store_row("C7-STORE", basename_of(apk_path), true,
              std::string("pkg=") + packages_.back().package_name +
                  (warm ? " cache=WARM" : " cache=COLD"));
    return true;
}

C7PackageIndex::IngestStats C7PackageIndex::ingest_store_dir(
    const std::string& dir, const std::string& cache_db) {
    DIR* d = ::opendir(dir.c_str());
    if (!d) {
        store_row("C7-STORE-ERR", dir, false, "store dir unreadable");
        ++last_stats_.packages_failed;
        return last_stats_;
    }
    std::vector<std::string> apks;
    struct dirent* e;
    while ((e = ::readdir(d)) != nullptr) {
        std::string n = e->d_name;
        if (n.size() > 4 && n.substr(n.size() - 4) == ".apk") apks.push_back(n);
    }
    ::closedir(d);
    std::sort(apks.begin(), apks.end());  // deterministic ingest order
    for (const auto& n : apks) {
        std::string full = dir;
        if (!full.empty() && full.back() != '/') full.push_back('/');
        full += n;
        ingest_apk(full, cache_db);
    }
    store_row("C7-STORE-DONE", dir, true,
              "packages=" + std::to_string(package_count()) +
                  " cold=" + std::to_string(last_stats_.packages_cold) +
                  " warm=" + std::to_string(last_stats_.packages_warm) +
                  " failed=" + std::to_string(last_stats_.packages_failed));
    return last_stats_;
}

// CODER7 WAVE-8 L3: the engine's OWN install store (AOSP /data/app scan
// law — PMS walks /data/app at boot; every installed package's base.apk
// joins the package map). Walk <data_root>/data/app RECURSIVELY for
// *.apk (the deterministic install mapping nests <pkg>/base.apk), sorted
// by full path for a deterministic ingest order, then the SAME per-APK
// cache+ingest contract as the flat store dir. A missing root is NOT an
// error (a fresh engine has no installs) — the loud row says so.
C7PackageIndex::IngestStats C7PackageIndex::ingest_install_store(
    const std::string& data_root, const std::string& cache_db) {
    const std::string app_dir =
        (data_root.empty() ? std::string("runtime/data")
                           : data_root) +
        "/data/app";
    std::error_code ec;
    if (!std::filesystem::exists(app_dir, ec)) {
        store_row("C7-STORE-AUTO", app_dir, true,
                  "install store absent — nothing to auto-index");
        return last_stats_;
    }
    std::vector<std::string> apks;
    for (auto& entry : std::filesystem::recursive_directory_iterator(
             app_dir, std::filesystem::directory_options::skip_permission_denied,
             ec)) {
        if (ec) break;
        if (entry.is_regular_file(ec) && !ec &&
            entry.path().extension() == ".apk")
            apks.push_back(entry.path().string());
    }
    std::sort(apks.begin(), apks.end());  // deterministic ingest order
    for (const auto& apk : apks) ingest_apk(apk, cache_db);
    store_row("C7-STORE-AUTO", app_dir, true,
              "packages=" + std::to_string(package_count()) +
                  " apks=" + std::to_string(apks.size()) +
                  " cold=" + std::to_string(last_stats_.packages_cold) +
                  " warm=" + std::to_string(last_stats_.packages_warm) +
                  " failed=" + std::to_string(last_stats_.packages_failed));
    return last_stats_;
}

void C7PackageIndex::register_own_package(const apk::ManifestInfo& mi,
                                          const std::string& apk_path) {
    // The SAME conversion path as store ingestion (fill_package_from_manifest)
    // — the running package registers under its own name so cross-package
    // resolution sees self too (AOSP: PMS resolves across ALL packages).
    C7IdxPackage pkg;
    fill_package_from_manifest(mi, apk_path, pkg);
    store_row("C7-STORE-OWN", pkg.package_name, true,
              "components: a=" + std::to_string(pkg.activities.size()) +
                  " s=" + std::to_string(pkg.services.size()) +
                  " r=" + std::to_string(pkg.receivers.size()) +
                  " p=" + std::to_string(pkg.providers.size()));
    upsert(std::move(pkg));
}

}  // namespace dalvik
}  // namespace miniandroid
