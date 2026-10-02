// data_root.cpp — M3 FINDING-012 implementation (see data_root.h for the law).
#include "data_root.h"
#include "sqlite_shadow.h"

#include <cstdlib>
#include <filesystem>
#include <iostream>

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

} // namespace Storage
