// data_root.cpp — M3 FINDING-012 implementation (see data_root.h for the law).
#include "data_root.h"
#include "sqlite_shadow.h"

#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <vector>

namespace fs = std::filesystem;

namespace Storage {

namespace {
std::string g_app_data_root = "runtime/data";
bool g_explicit = false;
// F-NEW-234: the running package identity ("" = none bound).
std::string g_context_package;
} // namespace

void set_app_data_root(const std::string& root) {
    if (root.empty()) return;
    std::string abs = root;
    try {
        std::error_code ec;
        fs::path p = fs::absolute(fs::path(root), ec);
        if (!ec) abs = p.string();
        fs::create_directories(abs, ec);
        if (ec) {
            std::cerr << "[DATA-ROOT] warning: cannot create " << abs
                      << ": " << ec.message() << "\n";
        }
    } catch (const fs::filesystem_error& e) {
        std::cerr << "[DATA-ROOT] warning: " << e.what() << "\n";
    }
    g_app_data_root = abs;
    g_explicit = true;
    // One law for every storage consumer: sqlite obeys immediately.
    miniandroid::storage::DatabaseShadow::set_databases_dir(abs);
    std::cout << "[DATA-ROOT] app data root = " << abs << "\n";
}

const std::string& app_data_root() { return g_app_data_root; }

bool app_data_root_explicit() { return g_explicit; }

// ── F-NEW-234 per-package context law ──────────────────────────────────
void set_context_package(const std::string& package) {
    g_context_package = package;
    if (package.empty()) {
        // Legacy flat root reset (tool paths without a package identity).
        miniandroid::storage::DatabaseShadow::set_databases_dir(g_app_data_root);
        std::cout << "[DATA-ROOT] context package = (none — legacy flat root)\n";
        return;
    }
    // Create the AOSP framework directory family eagerly: AOSP creates
    // files/cache/shared_prefs/databases (+ code_cache, no_backup) at
    // first Context use; eager creation here makes the installed-package
    // filesystem inspectable from the moment the identity binds.
    fs::path base = fs::path(g_app_data_root) / "data" / "data" / package;
    std::error_code ec;
    for (const char* sub : {"files", "cache", "shared_prefs", "databases",
                            "code_cache", "no_backup"}) {
        fs::create_directories(base / sub, ec);
        if (ec) {
            std::cerr << "[DATA-ROOT] warning: cannot create " << (base / sub)
                      << ": " << ec.message() << "\n";
        }
    }
    // One law for every storage consumer: sqlite obeys immediately.
    miniandroid::storage::DatabaseShadow::set_databases_dir(
        (base / "databases").string());
    std::cout << "[DATA-ROOT] context package = " << package
              << " (data dir " << base.string() << ")\n";
}

const std::string& context_package() { return g_context_package; }

std::filesystem::path package_data_dir() {
    if (g_context_package.empty()) return fs::path(g_app_data_root);
    return fs::path(g_app_data_root) / "data" / "data" / g_context_package;
}

std::filesystem::path context_dir(const std::string& sub) {
    if (sub.empty()) return package_data_dir();
    return package_data_dir() / sub;
}

std::filesystem::path external_app_dir(const std::string& kind) {
    if (g_context_package.empty()) {
        // Legacy flat shape (pre-F-NEW-234 tool paths).
        std::string leaf = "external_" + kind;
        return fs::path(g_app_data_root) / leaf;
    }
    // AOSP Environment.getExternalStorageDirectory + Android/data/<pkg> law.
    return fs::path(g_app_data_root) / "storage" / "emulated" / "0" /
           "Android" / "data" / g_context_package / kind;
}

std::filesystem::path external_obb_dir() {
    if (g_context_package.empty())
        return fs::path(g_app_data_root) / "obb";
    return fs::path(g_app_data_root) / "storage" / "emulated" / "0" /
           "Android" / "obb" / g_context_package;
}

// ── LOADING-CAMPAIGN: the ONE canonical Android-path law ────────────────
// See data_root.h for the AOSP source law. Every consumer routes here.
PathResolution resolve_android_path(const std::string& logical) {
    PathResolution r;

    if (logical.empty()) return r;

    // Relative → the running package's data dir (F-NEW-234 sandbox anchor).
    if (logical[0] != '/') {
        r.category = PathCategory::RELATIVE_APP_DATA;
        r.host_path = package_data_dir() / logical;
        r.allowed = true;
        return r;
    }

    // ── /dev device nodes Android explicitly exposes to apps (sepolicy
    // appdomain: urandom_device r_file_perms). Pass through as-is: the
    // host node has the same semantics. Everything else under /dev DENIED.
    if (logical.rfind("/dev/", 0) == 0) {
        static const char* kAllowedDev[] = {"/dev/urandom", "/dev/random",
                                            "/dev/null", "/dev/zero"};
        for (const char* dev : kAllowedDev) {
            if (logical == dev) {
                r.category = PathCategory::DEVICE_NODE;
                r.host_path = fs::path(logical);
                r.allowed = true;
                return r;
            }
        }
        return r;  // DENIED
    }

    // ── /data family. Shape: /data/<flavor>/<pkg>/<rest…> where flavor ∈
    // {data, user/<id>, user_de/<id>}. /data/user/0/<pkg> ≡ /data/data/<pkg>
    // (user-0 alias — the SAME backing directory, AOSP inode law).
    if (logical.rfind("/data/", 0) == 0) {
        // Installed-APK code path: /data/app/**/base.apk → F-NEW-231 store.
        if (logical.rfind("/data/app/", 0) == 0) {
            // Accept any /data/app/…/base.apk shape; back it with the store
            // law <root>/data/app/<pkg>/base.apk when the running package
            // matches, else with the literal pkg segment extracted from the
            // path (the store dir IS named by package).
            std::string rest = logical.substr(strlen("/data/app/"));
            // strip "~~random~~/" and "<pkg>-<rand>/" style segments: the
            // last component is the apk file; the one before carries the pkg.
            std::vector<std::string> segs;
            size_t pos = 0;
            while (pos < rest.size()) {
                size_t nxt = rest.find('/', pos);
                if (nxt == std::string::npos) { segs.push_back(rest.substr(pos)); break; }
                segs.push_back(rest.substr(pos, nxt - pos));
                pos = nxt + 1;
            }
            std::string pkg;
            if (segs.size() >= 2) {
                // e.g. ["~~abc~~", "com.foo-1", "base.apk"] or ["com.foo","base.apk"]
                for (const auto& s : segs) {
                    if (s == "base.apk") continue;
                    if (!s.empty() && s[0] == '~') continue;
                    std::string cand = s;
                    size_t dash = cand.rfind('-');
                    if (dash != std::string::npos && dash > 0) cand = cand.substr(0, dash);
                    if (cand.find('.') != std::string::npos) { pkg = cand; break; }
                }
            }
            if (!pkg.empty()) {
                r.category = PathCategory::INSTALLED_APK;
                r.host_path = fs::path(g_app_data_root) / "data" / "app" / pkg / "base.apk";
                r.allowed = true;
                return r;
            }
            return r;  // unrecognized /data/app shape → DENIED
        }
        if (logical.rfind("/data/data/", 0) == 0) {
            std::string rest = logical.substr(strlen("/data/data/"));
            size_t slash = rest.find('/');
            std::string pkg = (slash == std::string::npos) ? rest : rest.substr(0, slash);
            std::string tail = (slash == std::string::npos) ? "" : rest.substr(slash + 1);
            if (!pkg.empty() && pkg.find('.') != std::string::npos) {
                r.category = PathCategory::SANDBOX_DATA;
                fs::path base = fs::path(g_app_data_root) / "data" / "data" / pkg;
                r.host_path = tail.empty() ? base : base / tail;
                r.allowed = true;
                return r;
            }
            return r;
        }
        if (logical.rfind("/data/user/", 0) == 0 ||
            logical.rfind("/data/user_de/", 0) == 0) {
            // /data/user/<id>/<pkg>/rest  (user_de: device-protected)
            std::string rest = logical.substr(logical.rfind("/data/user", 0) == 0
                                                  ? strlen("/data/user/")
                                                  : strlen("/data/user_de/"));
            size_t uslash = rest.find('/');
            if (uslash == std::string::npos) return r;  // just an id → DENIED
            std::string user_id = rest.substr(0, uslash);
            std::string after = rest.substr(uslash + 1);
            size_t pslash = after.find('/');
            std::string pkg = (pslash == std::string::npos) ? after : after.substr(0, pslash);
            std::string tail = (pslash == std::string::npos) ? "" : after.substr(pslash + 1);
            if (!pkg.empty() && pkg.find('.') != std::string::npos) {
                // User-0 alias law: user 0 (both credential/device-protected
                // spellings) maps to the SAME /data/data backing (AOSP: one
                // inode, two path spellings). Other users map to a sibling
                // namespace (user/<id>) — deterministic and isolated.
                r.category = PathCategory::SANDBOX_DATA;
                fs::path base = fs::path(g_app_data_root) / "data" / "data" / pkg;
                if (user_id != "0") base = fs::path(g_app_data_root) / "data" / "users" / user_id / pkg;
                r.host_path = tail.empty() ? base : base / tail;
                r.allowed = true;
                return r;
            }
            return r;
        }
        return r;  // other /data/* (system, tombstones…) → DENIED
    }

    // ── external volume (F-NEW-223 virtual mount law).
    if (logical.rfind("/storage/emulated/0", 0) == 0) {
        std::string rest = logical.size() > strlen("/storage/emulated/0")
                               ? logical.substr(strlen("/storage/emulated/0"))
                               : "";
        r.category = PathCategory::VIRTUAL_EXTERNAL;
        fs::path backing = fs::path(g_app_data_root) / "storage" / "emulated" / "0";
        std::error_code mk_ec;
        fs::create_directories(backing, mk_ec);  // mount point exists from boot
        r.host_path = rest.empty() ? backing : fs::path(backing.string() + rest);
        r.allowed = true;
        return r;
    }

    // ── system image (read-only). Fonts are the consumed face today: the
    // runtime serves them from <root>/system/fonts (virtual system image,
    // ST-9 namespace). Unknown system files answer ABSENT honestly.
    if (logical.rfind("/system/fonts/", 0) == 0) {
        r.category = PathCategory::SYSTEM_IMAGE;
        r.host_path = fs::path(g_app_data_root) / "system" / "fonts" /
                      logical.substr(strlen("/system/fonts/"));
        r.allowed = true;
        return r;
    }

    // /system/framework/framework-res.apk → the runtime's copy when present.
    if (logical == "/system/framework/framework-res.apk") {
        r.category = PathCategory::SYSTEM_IMAGE;
        r.host_path = fs::path(g_app_data_root) / "system" / "framework" / "framework-res.apk";
        r.allowed = true;
        return r;
    }

    // EVERYTHING ELSE (host /etc, /home, /proc, /tmp, /var, other /dev,
    // unknown /system subtrees…) is OUTSIDE the app namespace → DENIED.
    return r;
}

} // namespace Storage
