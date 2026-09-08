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

} // namespace Storage
