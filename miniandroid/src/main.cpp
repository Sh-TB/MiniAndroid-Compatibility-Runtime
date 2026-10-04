/*
 * MiniAndroid Runtime v0.1 - Main Entry Point
 * EXP-001: HelloWorld Loader
 * 
 * Command-line interface for the MiniAndroid runtime.
 */

#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>
#include <ctime>
#include "diagnostics/crash_forensics.h"
#include <filesystem>
#include <cstdlib>
// ─── S61 PERF: poor-man's sampling profiler (env MINIANDROID_SAMPLE=1) ───
#include <execinfo.h>
#include <dlfcn.h>
#include <signal.h>
#include <sys/time.h>
#include <unistd.h>
#include <vector>
#include <algorithm>
namespace {
struct SampleProfiler {
    static SampleProfiler& inst() { static SampleProfiler s; return s; }
    std::vector<std::vector<void*>> samples;
    static void handler(int) {
        void* bt[24];
        int n = backtrace(bt, 24);
        std::vector<void*> s(bt, bt + n);
        auto& sp = inst();
        if (sp.samples.size() < 100000) sp.samples.push_back(s);
    }
    void start() {
        struct sigaction sa{};
        sa.sa_handler = &SampleProfiler::handler;
        sigemptyset(&sa.sa_mask);
        sa.sa_flags = SA_RESTART;
        sigaction(SIGPROF, &sa, nullptr);
        struct itimerval timer{};
        timer.it_interval.tv_usec = 10000;  // 10ms
        timer.it_value.tv_usec = 10000;
        setitimer(ITIMER_PROF, &timer, nullptr);
    }
    void stop_and_report() {
        struct itimerval zero{};
        setitimer(ITIMER_PROF, &zero, nullptr);
        fprintf(stderr, "[SAMPLES] total=%zu\n", samples.size());
        // top unique innermost-frame PCs
        std::vector<void*> tops;
        for (auto& s : samples) if (!s.empty()) tops.push_back(s[1] ? s[1] : s[0]);
        std::sort(tops.begin(), tops.end());
        // count contiguous runs
        size_t i = 0;
        std::vector<std::pair<void*, size_t>> counts;
        while (i < tops.size()) {
            size_t j = i;
            while (j < tops.size() && tops[j] == tops[i]) ++j;
            counts.push_back({tops[i], j - i});
            i = j;
        }
        std::sort(counts.begin(), counts.end(),
                  [](auto& a, auto& b){ return a.second > b.second; });
        for (size_t k = 0; k < counts.size() && k < 40; ++k) {
            char* dem = nullptr;
            char buf[128];
            void* addr = counts[k].first;
            Dl_info info{};
            if (dladdr(addr, &info) && info.dli_sname)
                fprintf(stderr, "[SAMPLE-TOP] %5zu  %s (+%p)\n", counts[k].second,
                        info.dli_sname, (void*)((char*)addr - (char*)info.dli_saddr));
            else
                fprintf(stderr, "[SAMPLE-TOP] %5zu  %p\n", counts[k].second, addr);
            (void)dem; (void)buf;
        }
        fflush(stderr);
    }
};
}
#define S61_SAMPLE 1
#include <cstring>
#include <pthread.h>

#include "runtime/execution_engine.h"
#include "apk/apk_parser.h"

// S108 ROOT-018: the `miniandroid run` CLI path NEVER registered the JNI
// bridge — only ApplicationRuntime::execute_on_create did (a different
// pipeline). Every native method in every APK therefore degraded to
// fail-soft defaults ("no handler registered"). Registering both the
// default stubs AND the real org.telegram.SQLite sqlite3 surface here.
#include "jni/jni_bridge.h"
#include "jni/telegram_sqlite_jni.h"
// F-NEW-231 INSTALLED_APK_ACCESS: the package store (AOSP PackageManagerService
// install law — /data/app/<package>/base.apk + PackageInfo metadata + app data
// dirs). Lets the agent install an APK once and then discover/inspect/launch it
// FROM THE INSTALLED STATE (package identity only), never needing the original
// sideload path again.
#include <openssl/evp.h>
// EXP-086 Phase 7 (B4 FIX): ShadowRegistry + HandlerShadow for Runnable queue
#include "framework/android_shadows.h"
#include "framework/dialog_shadow.h"
// GATE A (issue #370): installed-environment inspection surface.
#include "diagnostics/install_inspection.h"
#include "framework/clipboard_shadow.h"
#include "framework/canvas_shadow.h"
#include "dex/dex_parser.h"

using namespace miniandroid;

void print_version() {
    std::cout << "MiniAndroid Runtime v0.1" << std::endl;
    std::cout << "EXP-001: HelloWorld Loader" << std::endl;
    std::cout << "Evidence-driven Android compatibility runtime" << std::endl;
}

void print_usage(const char* program_name) {
    print_version();
    std::cout << "\nUsage:\n";
    std::cout << "  " << program_name << " <command> [options] <apk_path>\n\n";
    std::cout << "Commands:\n";
    std::cout << "  analyze   Parse APK and display information\n";
    std::cout << "  dex       Parse DEX files and show class/method info\n";
    std::cout << "  run       Execute APK and generate output\n";
    std::cout << "  install   Install an APK into the package store (--data-root required)\n";
    std::cout << "  list-packages  List installed packages from the package store\n";
    std::cout << "  uninstall  Remove an installed package completely: codePath,\n";
    std::cout << "             record, internal + external data trees (--package + --data-root)\n";
    std::cout << "  pkgaudit  Audit an installed package: identity, integrity re-hash,\n";
    std::cout << "            recursive code+data inventory (--package + --data-root)\n";
    std::cout << "  pkginspect  GATE A installed-environment inspection: identity,\n";
    std::cout << "            manifest/components, APK entries, DEX, resources, assets,\n";
    std::cout << "            native libs, data/external trees, databases, preferences,\n";
    std::cout << "            provenance (--package + --data-root, or --apk <path>;\n";
    std::cout << "            --what identity,manifest,... selects sections; --jsonl <out>\n";
    std::cout << "            writes the full-fidelity machine-readable stream)\n";
    std::cout << "  version   Show version information\n";
    std::cout << "  help      Show this help message\n\n";
    std::cout << "Options:\n";
    std::cout << "  -o, --output <dir>     Output directory (default: ./run)\n";
    std::cout << "  -v, --verbose          Enable verbose output\n";
    std::cout << "  --width <pixels>       Screen width (default: 1080)\n";
    std::cout << "  --height <pixels>      Screen height (default: 1920)\n";
    std::cout << "  --text <text>          Override displayed text\n";
    std::cout << "  --click-test           Dispatch real clicks on clickable views after the first frame\n";
    std::cout << "  --trace                S135 runtime event backbone: trace.jsonl + trace_summary.json\n";
    std::cout << "  --trace-ui             S135 visual trace overlay: trace_overlay.png (semantic boot panel)\n";
    std::cout << "                         MINIANDROID_TRACE_UI=1|header|expanded selects the panel mode\n";
    std::cout << "  --max-seconds <s>      Wall-clock soft budget for the run (graceful evidence stop)\n";
    std::cout << "  --long-press <x>,<y>   Long-press gesture at coordinates after the first frame\n";
    std::cout << "  --tap <x>,<y>         Canonical tap gesture (DOWN/UP law pipeline) after the first frame\n";
    std::cout << "                         (hit test -> 500ms timeout -> onLongClick; consumed\n";
    std::cout << "                          long press suppresses the UP click — AOSP law)\n";
    std::cout << "  --execution-mode <mode> Execution mode: legacy | real-dalvik (default: real-dalvik)\n";
    std::cout << "  --data-root <dir>       App private storage root (Android /data/data analog).\n";
    std::cout << "                          Determinism/persistence drivers MUST set this per run.\n";
    std::cout << "  --package <pkg>         Run an INSTALLED package: resolve\n";
    std::cout << "                          <data-root>/data/app/<pkg>/base.apk (F-NEW-231).\n";
    std::cout << "                          Package identity is the only input — no APK path.\n\n";
    std::cout << "Examples:\n";
    std::cout << "  " << program_name << " analyze HelloWorld.apk\n";
    std::cout << "  " << program_name << " run -o ./output HelloWorld.apk\n";
    std::cout << "  " << program_name << " run --text \"Custom Text\" HelloWorld.apk\n";
    std::cout << "  " << program_name << " run --execution-mode=real-dalvik HelloWorld.apk\n";
    std::cout << "  " << program_name << " run --execution-mode=legacy HelloWorld.apk\n";
}

int cmd_analyze(const std::string& apk_path, bool verbose) {
    std::cout << "[*] Analyzing APK: " << apk_path << std::endl;
    
    runtime::ExecutionEngine engine;
    
    // Use APK parser directly
    apk::ApkParser parser;
    parser.set_verbose(verbose);
    
    auto result = parser.parse(apk_path);
    
    if (!result.is_valid) {
        std::cerr << "[ERROR] Failed to parse APK: " << result.validation_error << std::endl;
        return 1;
    }
    
    // Output JSON-like report
    std::cout << "\n=== APK Analysis Report ===\n\n";
    std::cout << "{\n";
    std::cout << "  \"apk_name\": \"" << result.apk_name << "\",\n";
    std::cout << "  \"package_name\": \"" << result.package_name << "\",\n";
    std::cout << "  \"version_name\": \"" << result.version_name << "\",\n";
    std::cout << "  \"version_code\": " << result.version_code << ",\n";
    std::cout << "  \"min_sdk\": \"" << result.min_sdk_version << "\",\n";
    std::cout << "  \"target_sdk\": \"" << result.target_sdk_version << "\",\n";
    std::cout << "  \"main_activity\": \"" << result.main_activity << "\",\n";
    std::cout << "  \"main_activity_full\": \"" << result.main_activity_full << "\",\n";
    
    std::cout << "  \"permissions\": [\n";
    for (size_t i = 0; i < result.permissions.size(); i++) {
        std::cout << "    \"" << result.permissions[i] << "\"";
        if (i < result.permissions.size() - 1) std::cout << ",";
        std::cout << "\n";
    }
    std::cout << "  ],\n";
    
    std::cout << "  \"dex_files\": [\n";
    for (size_t i = 0; i < result.dex_files.size(); i++) {
        std::cout << "    \"" << result.dex_files[i] << "\"";
        if (i < result.dex_files.size() - 1) std::cout << ",";
        std::cout << "\n";
    }
    std::cout << "  ],\n";
    
    std::cout << "  \"native_libraries\": [\n";
    for (size_t i = 0; i < result.native_libraries.size(); i++) {
        std::cout << "    \"" << result.native_libraries[i] << "\"";
        if (i < result.native_libraries.size() - 1) std::cout << ",";
        std::cout << "\n";
    }
    std::cout << "  ],\n";
    
    std::cout << "  \"total_entries\": " << result.all_entries.size() << ",\n";
    std::cout << "  \"file_size\": " << result.file_size << "\n";
    std::cout << "}\n\n";
    
    // Save to file
    std::ofstream out("run/apk_info.json");
    if (out.is_open()) {
        // Would use proper JSON library here
        out << "// APK Info for: " << result.apk_name << "\n";
        out << "// Package: " << result.package_name << "\n";
        out.close();
        std::cout << "[+] Saved to run/apk_info.json\n";
    }
    
    return 0;
}

int cmd_dex(const std::string& apk_path, bool verbose) {
    std::cout << "[*] Analyzing DEX from: " << apk_path << std::endl;
    
    // First parse APK to extract DEX
    apk::ApkParser apk_parser;
    auto apk_info = apk_parser.parse(apk_path);
    
    if (!apk_info.is_valid) {
        std::cerr << "[ERROR] Failed to parse APK: " << apk_info.validation_error << std::endl;
        return 1;
    }
    
    if (apk_info.dex_files.empty()) {
        std::cerr << "[ERROR] No DEX files found in APK" << std::endl;
        return 1;
    }
    
    // Extract and parse DEX
    dex::DexParser dex_parser;
    dex_parser.set_verbose(verbose);
    
    auto dex_data = apk_parser.extract_entry(apk_path, "classes.dex");
    if (dex_data.empty()) {
        std::cerr << "[ERROR] Failed to extract classes.dex" << std::endl;
        return 1;
    }
    
    auto report = dex_parser.parse_data(dex_data, "classes.dex");
    
    if (!report.is_valid) {
        std::cerr << "[ERROR] DEX parsing failed: " << report.validation_error << std::endl;
        return 1;
    }
    
    // Output DEX report
    std::cout << "\n=== DEX Analysis Report ===\n\n";
    std::cout << "DEX Version: " << report.dex_version << "\n";
    std::cout << "Strings: " << report.strings_count << "\n";
    std::cout << "Types: " << report.types_count << "\n";
    std::cout << "Prototypes: " << report.prototypes_count << "\n";
    std::cout << "Fields: " << report.fields_count << "\n";
    std::cout << "Methods: " << report.methods_count << "\n";
    std::cout << "Classes: " << report.classes_count << "\n\n";
    
    // Class details
    std::cout << "--- Classes ---\n\n";
    for (const auto& cls : report.classes) {
        std::cout << "Class: " << cls.name << "\n";
        if (!cls.superclass_name.empty()) {
            std::cout << "  Extends: " << cls.superclass_name << "\n";
        }
        
        auto methods = cls.all_methods();
        if (!methods.empty()) {
            std::cout << "  Methods (" << methods.size() << "):\n";
            for (const auto& method : methods) {
                std::cout << "    - " << method.name << method.descriptor;
                if (method.is_constructor) std::cout << " [constructor]";
                if (method.is_static) std::cout << " [static]";
                if (method.is_native) std::cout << " [native]";
                std::cout << "\n";
            }
        }
        std::cout << "\n";
    }
    
    return 0;
}

#include "storage/data_root.h"

// ────────────────────────────────────────────────────────────────────
// F-083 (S55, R-NEW-361): the DEX interpreter recurses once per invoked
// method (fetch_decode_execute → execute_invoke_* → try_recursive_invoke
// → fetch_decode_execute). EXP-053 measured ~80KB of C++ stack per DEX
// frame, which capped MAX_RECURSION_DEPTH at 80 under the process's 8MB
// stack. Deep-but-LEGITIMATE initialization recursion (Compose node and
// SlotTable setup, androidx.collection ScatterMap init) exceeded 80 and
// every frame past the cap was SILENTLY dropped onto the API bridge —
// the dropped void initializer Ln/a;.r left a ScatterMap with ghost
// metadata bytes (no EMPTY 0x80) and its probe spun forever (the
// R-NEW-361 HALT-LOOP face). ART's contract: app recursion is bounded
// by the THREAD STACK, not a fixed frame count. Restore that contract
// by running the engine on a dedicated thread whose stack is large
// (virtual reservation — Linux commits pages on touch) and raising the
// DEX frame budget to match. No interpreter frame layout is changed.
// ────────────────────────────────────────────────────────────────────
namespace {
struct F083Invoke {
    runtime::ExecutionEngine* engine;
    const std::string* apk;
    const runtime::ExecutionConfig* config;
    runtime::ExecutionResult result;
};
void* f083_tramp(void* arg) {
    auto* inv = static_cast<F083Invoke*>(arg);
    inv->result = inv->engine->execute(*inv->apk, *inv->config);
    return nullptr;
}
runtime::ExecutionResult run_on_art_sized_stack(
    runtime::ExecutionEngine& engine,
    const std::string& apk_path,
    const runtime::ExecutionConfig& config) {
    F083Invoke inv{&engine, &apk_path, &config, {}};
    pthread_attr_t attr;
    int rc = pthread_attr_init(&attr);
    if (rc == 0) {
        // 1GB VIRTUAL stack ≈ 12k DEX frames at the measured 80KB/frame
        // (ART main-thread budgets are thousands of frames). Virtual
        // reservation only; resident cost stays proportional to the
        // real depth actually reached.
        rc = pthread_attr_setstacksize(&attr, (size_t)1 << 30);
    }
    pthread_t tid;
    if (rc == 0) rc = pthread_create(&tid, &attr, f083_tramp, &inv);
    if (rc == 0) {
        pthread_attr_destroy(&attr);
        pthread_join(tid, nullptr);
        return inv.result;
    }
    pthread_attr_destroy(&attr);
    // Deep-stack thread unavailable (rlimit): fall back to the caller
    // stack — the pre-F-083 behavior — rather than fail the run.
    inv.result = engine.execute(apk_path, config);
    return inv.result;
}
} // namespace

// ════════════════════════════════════════════════════════════════════
// F-NEW-231 INSTALLED_APK_ACCESS — the MiniAndroid package store.
//
// AOSP LAW (android-14 source, PackageManagerService / PackageInstaller):
//  * An install commits the APK into the package code path under /data/app
//    as `base.apk` (PMS: preparePackageLI → rename to codePath; split APKs
//    become base.apk + split_*.apk siblings).
//  * PackageInfo/ApplicationInfo.sourceDir points at the installed base.apk
//    (NOT the original sideload path — the installer does not preserve it).
//  * PackageManager.getInstalledPackages() enumerates installed packages
//    from the package settings (our scan of the store metadata).
//  * App-private storage lives under /data/data/<package>/{files,cache,
//    shared_prefs,databases} (Environment.getDataDirectory + package).
//
// MINIANDROID DEVIATION LAW (deliberate, documented): AOSP randomizes the
// per-install directory (/data/app/~~rand==/<pkg>-rand==/base.apk). MiniAndroid
// uses the DETERMINISTIC mapping <data-root>/data/app/<package>/base.apk —
// the platform-audit requirement is agent inspectability ("agent can discover
// the installed package from package identity alone"), which a randomized
// path would defeat. Recorded in every package.json.
// ════════════════════════════════════════════════════════════════════
namespace pkgstore {

std::string sha256_file(const std::string& path, bool* ok) {
    *ok = false;
    FILE* f = fopen(path.c_str(), "rb");
    if (!f) return "";
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int dlen = 0;
    std::string hex;
    if (ctx && EVP_DigestInit_ex(ctx, EVP_sha256(), nullptr) == 1) {
        char buf[65536];
        size_t n;
        bool stream_ok = true;
        while ((n = fread(buf, 1, sizeof(buf), f)) > 0) {
            if (EVP_DigestUpdate(ctx, buf, n) != 1) { stream_ok = false; break; }
        }
        if (stream_ok && !ferror(f) &&
            EVP_DigestFinal_ex(ctx, digest, &dlen) == 1) {
            static const char* H = "0123456789abcdef";
            for (unsigned int i = 0; i < dlen; i++) {
                hex += H[digest[i] >> 4];
                hex += H[digest[i] & 0xf];
            }
            *ok = true;
        }
    }
    if (ctx) EVP_MD_CTX_free(ctx);
    fclose(f);
    return hex;
}

std::string json_escape(const std::string& s) {
    std::string out;
    for (char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    char b[8]; snprintf(b, sizeof(b), "\\u%04x", c);
                    out += b;
                } else out += c;
        }
    }
    return out;
}

std::filesystem::path store_root(const std::string& data_root) {
    return std::filesystem::path(data_root) / "data" / "app";
}

std::filesystem::path package_dir(const std::string& data_root,
                                  const std::string& package) {
    return store_root(data_root) / package;
}

std::filesystem::path package_json(const std::string& data_root,
                                   const std::string& package) {
    return package_dir(data_root, package) / "package.json";
}

// One installed-package record. Fields mirror the PackageInfo the AOSP
// PackageParser produces (package, versionName, versionCode, main activity,
// requested permissions) + the integrity/provenance fields the evidence
// laws require (apk sha256, size, install timestamp).
struct PackageRecord {
    std::string package;
    std::string version_name;
    long long version_code = 0;
    std::string main_activity;
    std::vector<std::string> permissions;
    std::string apk_sha256;
    unsigned long long apk_size = 0;
    std::string installed_at;
    std::string min_sdk;
    std::string target_sdk;
};

bool write_record(const PackageRecord& rec, const std::string& data_root) {
    std::error_code ec;
    auto dir = package_dir(data_root, rec.package);
    std::filesystem::create_directories(dir, ec);
    if (ec) return false;
    // App-private dirs (AOSP /data/data/<pkg> family law; F-NEW-234 aligns
    // the runtime Context family with this exact layout — code_cache and
    // no_backup are created at first Context use on AOSP; eager here).
    for (const char* sub : {"files", "cache", "shared_prefs", "databases",
                            "code_cache", "no_backup"}) {
        std::filesystem::create_directories(
            std::filesystem::path(data_root) / "data" / "data" / rec.package / sub, ec);
    }
    std::ofstream out(package_json(data_root, rec.package).string(),
                      std::ios::binary | std::ios::trunc);
    if (!out.is_open()) return false;
    out << "{\n";
    out << "  \"package\": \"" << json_escape(rec.package) << "\",\n";
    out << "  \"versionName\": \"" << json_escape(rec.version_name) << "\",\n";
    out << "  \"versionCode\": " << rec.version_code << ",\n";
    out << "  \"mainActivity\": \"" << json_escape(rec.main_activity) << "\",\n";
    out << "  \"minSdk\": \"" << json_escape(rec.min_sdk) << "\",\n";
    out << "  \"targetSdk\": \"" << json_escape(rec.target_sdk) << "\",\n";
    out << "  \"requestedPermissions\": [";
    for (size_t i = 0; i < rec.permissions.size(); i++) {
        out << "\n    \"" << json_escape(rec.permissions[i]) << "\"";
        if (i + 1 < rec.permissions.size()) out << ",";
    }
    out << (rec.permissions.empty() ? "" : "\n  ") << "],\n";
    // NOTE (AOSP law): the original sideload path is deliberately NOT recorded —
    // the installer does not preserve it; post-install identity = package only.
    out << "  \"origin\": \"sideload\",\n";
    out << "  \"codePath\": \"" << json_escape("/data/app/" + rec.package + "/base.apk")
        << "\",\n";
    out << "  \"hostCodePath\": \"" << json_escape((package_dir(data_root, rec.package)
              / "base.apk").string()) << "\",\n";
    out << "  \"apkSha256\": \"" << rec.apk_sha256 << "\",\n";
    out << "  \"apkSize\": " << rec.apk_size << ",\n";
    out << "  \"installedAt\": \"" << rec.installed_at << "\",\n";
    out << "  \"installLayout\": \"MiniAndroid deterministic package store "
           "(F-NEW-231; AOSP /data/app law, deterministic mapping deviation)\"\n";
    out << "}\n";
    return out.good();
}

} // namespace pkgstore

int cmd_install(const std::string& apk_path, const std::string& data_root,
                bool verbose) {
    std::cout << "[*] Installing APK: " << apk_path << "\n";
    if (data_root.empty()) {
        std::cerr << "[ERROR] install requires --data-root <dir> (the MiniAndroid "
                     "package store root)\n";
        return 1;
    }
    apk::ApkParser parser;
    parser.set_verbose(verbose);
    auto info = parser.parse(apk_path);
    if (!info.is_valid) {
        std::cerr << "[ERROR] Failed to parse APK: " << info.validation_error << "\n";
        return 1;
    }
    if (info.package_name.empty()) {
        std::cerr << "[ERROR] Manifest has no package name — cannot install\n";
        return 1;
    }
    bool sha_ok = false;
    std::string sha = pkgstore::sha256_file(apk_path, &sha_ok);
    if (!sha_ok) {
        std::cerr << "[ERROR] SHA-256 of APK could not be computed\n";
        return 1;
    }
    std::error_code ec;
    unsigned long long size = std::filesystem::file_size(apk_path, ec);
    if (ec) size = 0;
    std::time_t now = std::time(nullptr);
    char ts[32];
    std::strftime(ts, sizeof(ts), "%Y-%m-%dT%H:%M:%SZ", std::gmtime(&now));

    pkgstore::PackageRecord rec;
    rec.package = info.package_name;
    rec.version_name = info.version_name;
    rec.version_code = info.version_code;
    rec.main_activity = info.main_activity_full;
    rec.permissions = info.permissions;
    rec.apk_sha256 = sha;
    rec.apk_size = size;
    rec.installed_at = ts;
    rec.min_sdk = info.min_sdk_version;
    rec.target_sdk = info.target_sdk_version;

    // Commit: copy the APK into the store as base.apk (AOSP commit law),
    // then write the package record. Copy FIRST, record SECOND — a record
    // without base.apk must never exist (PMS ordering law).
    auto dst = pkgstore::package_dir(data_root, rec.package) / "base.apk";
    std::filesystem::create_directories(pkgstore::package_dir(data_root, rec.package), ec);
    std::filesystem::copy_file(apk_path, dst,
                               std::filesystem::copy_options::overwrite_existing, ec);
    if (ec) {
        std::cerr << "[ERROR] Copy into package store failed: " << ec.message() << "\n";
        return 1;
    }
    // Integrity: the installed bytes must equal the source bytes.
    bool dst_ok = false;
    std::string dst_sha = pkgstore::sha256_file(dst.string(), &dst_ok);
    if (!dst_ok || dst_sha != sha) {
        std::cerr << "[ERROR] Installed base.apk integrity check FAILED (sha mismatch)\n";
        std::filesystem::remove_all(pkgstore::package_dir(data_root, rec.package), ec);
        return 1;
    }
    if (!pkgstore::write_record(rec, data_root)) {
        std::cerr << "[ERROR] package.json write failed\n";
        return 1;
    }
    // ── #371 PHASE B2 (G-4 closure): ABI-scoped native library extraction.
    // AOSP PMS law (PackageManagerService.installNativeLibraries): install
    // extracts ONE ABI's lib/ tree into the codePath's lib dir
    // (nativeLibraryDir); the ABI is the device's preferred ABI present in
    // the APK (Build.SUPPORTED_ABIS order). #371 CLOSEOUT (S-2): this
    // device profile's SUPPORTED_ABIS = [x86_64 (host-EXECUTABLE),
    // x86, arm64-v8a, armeabi-v7a (extraction-only — the runtime has no
    // binary translation, so arm libs are extracted for provenance but a
    // load attempt reports the REAL dlopen refusal)]. Preferring the
    // host-executable ABI is what makes native execution REAL for
    // multi-ABI APKs, matching real x86_64 Android devices. Extracted
    // bytes are REAL (entry-extracted + SHA-verified); the manifest lives
    // in native_libs.json beside package.json so pkginspect/pkgrecord can
    // serve the identity without re-parsing the APK.
    std::string primary_abi;
    std::vector<std::pair<std::string, unsigned long long>> extracted;
    {
        static const char* kAbiOrder[] = {"x86_64", "x86", "arm64-v8a",
                                          "armeabi-v7a"};
        std::vector<std::string> libs = info.native_libraries;
        if (libs.empty()) {
            for (const auto& e : info.all_entries)
                if (e.rfind("lib/", 0) == 0 && e.size() > 3 &&
                    e.compare(e.size() - 3, 3, ".so") == 0)
                    libs.push_back(e);
        }
        for (const char* abi : kAbiOrder) {
            std::string prefix = std::string("lib/") + abi + "/";
            std::vector<std::string> sel;
            for (const auto& l : libs)
                if (l.rfind(prefix, 0) == 0) sel.push_back(l);
            if (sel.empty()) continue;
            primary_abi = abi;
            auto lib_dir = pkgstore::package_dir(data_root, rec.package) /
                           "lib" / abi;
            std::error_code lex;
            std::filesystem::create_directories(lib_dir, lex);
            bool extract_ok = true;
            for (const auto& entry : sel) {
                std::vector<uint8_t> bytes =
                    parser.extract_entry(apk_path, entry);
                if (bytes.empty()) { extract_ok = false; continue; }
                auto slash = entry.rfind('/');
                std::string fname = slash == std::string::npos
                                        ? entry
                                        : entry.substr(slash + 1);
                auto dstp = lib_dir / fname;
                FILE* of = fopen(dstp.string().c_str(), "wb");
                if (!of) { extract_ok = false; continue; }
                size_t wn = fwrite(bytes.data(), 1, bytes.size(), of);
                fclose(of);
                if (wn != bytes.size()) { extract_ok = false; continue; }
                extracted.emplace_back(entry, (unsigned long long)bytes.size());
            }
            if (!extract_ok)
                std::cerr << "[WARN] native lib extraction incomplete for "
                          << abi << "\n";
            break;  // AOSP: ONE ABI per install
        }
        // Machine-readable extraction manifest (native_libs.json).
        auto nl_path = pkgstore::package_dir(data_root, rec.package) /
                       "native_libs.json";
        std::ofstream nl(nl_path.string());
        if (nl) {
            nl << "{\n  \"primaryAbi\": \""
               << pkgstore::json_escape(primary_abi) << "\",\n";
            nl << "  \"nativeLibraryDir\": \"/data/app/"
               << pkgstore::json_escape(rec.package) << "/lib/"
               << pkgstore::json_escape(primary_abi) << "\",\n";
            nl << "  \"extracted\": [\n";
            for (size_t i = 0; i < extracted.size(); ++i) {
                nl << "    {\"entry\": \""
                   << pkgstore::json_escape(extracted[i].first)
                   << "\", \"size\": " << extracted[i].second << "}"
                   << (i + 1 < extracted.size() ? "," : "") << "\n";
            }
            nl << "  ],\n  \"count\": " << extracted.size() << "\n}\n";
        }
    }
    std::cout << "\n=== Install Result ===\n\n";
    std::cout << "{\n";
    std::cout << "  \"install\": \"SUCCESS\",\n";
    std::cout << "  \"package\": \"" << pkgstore::json_escape(rec.package) << "\",\n";
    std::cout << "  \"versionName\": \"" << pkgstore::json_escape(rec.version_name)
              << "\",\n";
    std::cout << "  \"versionCode\": " << rec.version_code << ",\n";
    std::cout << "  \"codePath\": \"/data/app/"
              << pkgstore::json_escape(rec.package) << "/base.apk\",\n";
    std::cout << "  \"hostCodePath\": \"" << pkgstore::json_escape(dst.string()) << "\",\n";
    std::cout << "  \"apkSha256\": \"" << sha << "\",\n";
    std::cout << "  \"apkSize\": " << size << ",\n";
    std::cout << "  \"installedAt\": \"" << ts << "\"\n";
    std::cout << ", \"nativePrimaryAbi\": \""
              << pkgstore::json_escape(primary_abi) << "\"\n";
    std::cout << ", \"nativeLibsExtracted\": " << extracted.size() << "\n";
    std::cout << "}\n";
    std::cout << "\n[+] Installed. Post-install identity = package name + data-root only.\n";
    return 0;
}

// UNINSTALL SEMANTICS (AOSP PackageManager.deletePackage law): the package
// leaves the store COMPLETELY — codePath (base.apk), its package record, the
// internal data tree (/data/data/<pkg>) and the external app dirs
// (/storage/emulated/0/Android/<data|media|obb>/<pkg>). Any OTHER package's
// trees must remain byte-identical (package isolation). Generic: no package
// conditionals; the package identity comes from --package alone.
struct UninstallReport {
    bool found = false;
    std::vector<std::string> removed;
    std::vector<std::string> absent;   // legal: tree never created by any run
    std::vector<std::string> errors;
};

static void uninstall_remove_tree(const std::filesystem::path& p,
                                  const char* label, UninstallReport& rep) {
    std::error_code ec;
    if (!std::filesystem::exists(p, ec)) {
        rep.absent.push_back(std::string(label) + "=" + p.string());
        return;
    }
    std::filesystem::remove_all(p, ec);
    if (ec) {
        rep.errors.push_back(std::string(label) + "=" + ec.message());
        return;
    }
    if (std::filesystem::exists(p, ec)) {
        rep.errors.push_back(std::string(label) + "=still-present-after-remove_all");
        return;
    }
    rep.removed.push_back(std::string(label) + "=" + p.string());
}

int cmd_uninstall(const std::string& package, const std::string& data_root) {
    namespace fs = std::filesystem;
    if (data_root.empty() || package.empty()) {
        std::cerr << "[ERROR] uninstall requires --package <pkg> --data-root <dir>\n";
        return 1;
    }
    // Identity honesty: only a package that is actually installed (record or
    // codePath present) may be uninstalled — mirrors PMS NAME_NOT_FOUND.
    auto code_dir = pkgstore::package_dir(data_root, package);
    std::error_code ec;
    bool has_record = fs::exists(pkgstore::package_json(data_root, package), ec);
    bool has_code = fs::exists(code_dir / "base.apk", ec);
    if (!has_record && !has_code) {
        std::cout << "{\n  \"uninstall\": \"NOT_INSTALLED\",\n  \"package\": \""
                  << pkgstore::json_escape(package) << "\"\n}\n";
        return 2;
    }
    UninstallReport rep;
    rep.found = true;
    uninstall_remove_tree(code_dir, "codePath", rep);                       // /data/app/<pkg>
    uninstall_remove_tree(pkgstore::package_json(data_root, package),
                          "packageRecord", rep);                            // package.json
    uninstall_remove_tree(fs::path(data_root) / "data" / "data" / package,
                          "internalData", rep);                             // /data/data/<pkg>
    // External app dirs (all three AOSP families under the virtual external
    // root; absent trees are legal and reported as such).
    for (const char* fam : {"Android/data", "Android/media", "Android/obb"}) {
        uninstall_remove_tree(fs::path(data_root) / "storage" / "emulated" / "0" /
                              fs::path(fam) / package, fam, rep);
    }
    std::cout << "{\n  \"uninstall\": \""
              << (rep.errors.empty() ? "SUCCESS" : "ERROR") << "\",\n";
    std::cout << "  \"package\": \"" << pkgstore::json_escape(package) << "\",\n";
    std::cout << "  \"removed\": [";
    for (size_t i = 0; i < rep.removed.size(); i++)
        std::cout << (i ? ", ":"") << "\"" << pkgstore::json_escape(rep.removed[i]) << "\"";
    std::cout << "],\n";
    std::cout << "  \"absent\": [";
    for (size_t i = 0; i < rep.absent.size(); i++)
        std::cout << (i ? ", ":"") << "\"" << pkgstore::json_escape(rep.absent[i]) << "\"";
    std::cout << "]\n}\n";
    return rep.errors.empty() ? 0 : 1;
}

int cmd_list_packages(const std::string& data_root) {
    if (data_root.empty()) {
        std::cerr << "[ERROR] list-packages requires --data-root <dir>\n";
        return 1;
    }
    std::error_code ec;
    auto root = pkgstore::store_root(data_root);
    if (!std::filesystem::exists(root, ec)) {
        std::cout << "[]\n";
        return 0;
    }
    std::vector<std::string> packages;
    for (auto it = std::filesystem::directory_iterator(root, ec);
         it != std::filesystem::directory_iterator(); ++it) {
        if (it->is_directory(ec)) packages.push_back(it->path().filename().string());
    }
    std::sort(packages.begin(), packages.end());
    std::cout << "[\n";
    for (size_t i = 0; i < packages.size(); i++) {
        std::ifstream in(pkgstore::package_json(data_root, packages[i]).string());
        std::stringstream ss; ss << in.rdbuf();
        std::cout << "  {\"package\": \"" << pkgstore::json_escape(packages[i])
                  << "\", \"record\": ";
        std::string body = ss.str();
        while (!body.empty() && (body.back() == '\n' || body.back() == '\r'))
            body.pop_back();
        std::cout << (body.empty() ? "null" : body) << "}";
        if (i + 1 < packages.size()) std::cout << ",";
        std::cout << "\n";
    }
    std::cout << "]\n";
    return 0;
}

// ═══════════════════════════════════════════════════════════════════════
// IAPK CAMPAIGN — pkgaudit: reusable INSTALLED-APP AUDIT capability.
// Takes --package <pkg> --data-root <dir> and produces a machine-readable
// audit of the installed state — identity, codePath, integrity re-hash,
// and a recursive inventory of the package-owned filesystem. Generic for
// ANY installed APK; no package-specific logic anywhere.
// ═══════════════════════════════════════════════════════════════════════
int cmd_pkg_audit(const std::string& package, const std::string& data_root) {
    if (data_root.empty() || package.empty()) {
        std::cerr << "[ERROR] pkgaudit requires --package <pkg> --data-root <dir>\n";
        return 1;
    }
    namespace fs = std::filesystem;
    auto code_dir = pkgstore::package_dir(data_root, package);
    auto base_apk = code_dir / "base.apk";
    auto data_dir = fs::path(data_root) / "data" / "data" / package;
    if (!fs::exists(base_apk)) {
        std::cerr << "[ERROR] Package not installed: " << package << " (looked for "
                  << base_apk.string() << ")\n";
        return 1;
    }

    std::cout << "{\n";
    std::cout << "  \"audit\": \"INSTALLED_APP_AUDIT\",\n";
    std::cout << "  \"package\": \"" << pkgstore::json_escape(package) << "\",\n";

    // Identity: the package.json record (verbatim) + integrity re-hash.
    std::ifstream rec(pkgstore::package_json(data_root, package).string());
    if (rec.is_open()) {
        std::stringstream ss; ss << rec.rdbuf();
        std::string body = ss.str();
        while (!body.empty() && (body.back() == '\n' || body.back() == '\r'))
            body.pop_back();
        std::cout << "  \"record\": " << body << ",\n";
    } else {
        std::cout << "  \"record\": null,\n";
    }
    bool sha_ok = false;
    std::string live_sha = pkgstore::sha256_file(base_apk.string(), &sha_ok);
    std::cout << "  \"codePath\": \"/data/app/"
              << pkgstore::json_escape(package) << "/base.apk\",\n";
    std::cout << "  \"hostCodePath\": \"" << pkgstore::json_escape(base_apk.string())
              << "\",\n";
    std::cout << "  \"liveBaseApkSha256\": \"" << live_sha << "\",\n";

    // Recursive inventory of both package-owned trees.
    auto audit_tree = [&](const char* label, const fs::path& root) {
        unsigned long long files = 0, dirs = 0, bytes = 0;
        std::map<std::string, unsigned long long> exts;
        std::vector<std::pair<unsigned long long, std::string>> largest;
        if (fs::exists(root)) {
            std::error_code walk_ec;
            for (auto it = fs::recursive_directory_iterator(
                     root, fs::directory_options::skip_permission_denied, walk_ec);
                 it != fs::recursive_directory_iterator();
                 it.increment(walk_ec)) {
                std::error_code ec;
                if (it->is_directory(ec)) { dirs++; continue; }
                if (!it->is_regular_file(ec)) continue;
                files++;
                unsigned long long sz = it->file_size(ec);
                if (!ec) bytes += sz;
                largest.emplace_back(sz, it->path().string());
                std::string ext = it->path().extension().string();
                for (auto& c : ext) c = std::tolower(static_cast<unsigned char>(c));
                exts[ext.empty() ? "<none>" : ext]++;
            }
        }
        std::sort(largest.rbegin(), largest.rend());
        std::cout << "  \"" << label << "\": {\n";
        std::cout << "    \"root\": \"" << pkgstore::json_escape(root.string())
                  << "\",\n";
        std::cout << "    \"exists\": " << (fs::exists(root) ? "true" : "false")
                  << ",\n";
        std::cout << "    \"files\": " << files << ", \"dirs\": " << dirs
                  << ", \"bytes\": " << bytes << ",\n";
        std::cout << "    \"extHistogram\": {";
        bool first = true;
        for (const auto& [e, n] : exts) {
            if (!first) std::cout << ", ";
            std::cout << "\"" << pkgstore::json_escape(e) << "\": " << n;
            first = false;
        }
        std::cout << "},\n";
        std::cout << "    \"largestFiles\": [";
        first = true;
        for (size_t i = 0; i < largest.size() && i < 5; i++) {
            if (!first) std::cout << ", ";
            bool ok = false;
            std::string h = pkgstore::sha256_file(largest[i].second, &ok);
            std::cout << "\n      {\"path\": \""
                      << pkgstore::json_escape(largest[i].second)
                      << "\", \"size\": " << largest[i].first
                      << ", \"sha256\": \"" << h << "\"}";
            first = false;
        }
        std::cout << (first ? "" : "\n    ") << "]\n";
        std::cout << "  }";
    };
    audit_tree("codeTree", code_dir);
    std::cout << ",\n";
    audit_tree("dataTree", data_dir);
    std::cout << "\n}\n";
    return 0;
}

int cmd_run(const std::string& apk_path, const runtime::ExecutionConfig& config) {
    std::cout << "[*] Running APK: " << apk_path << std::endl;
    std::cout << "[*] Output directory: " << config.output_directory << std::endl;
    
    // S108 ROOT-018: register the JNI bridge on THIS path too (previously
    // only ApplicationRuntime::execute_on_create did it — a different
    // pipeline; here every native call was "no handler registered").
    miniandroid::jni::JNIBridge::instance().register_default_stubs();
    miniandroid::jni::telegram_sqlite::register_all();
    
    // M3 FINDING-012: apply the app-data root law BEFORE any storage
    // consumer initializes. Precedence: --data-root > MINIANDROID_DATA_ROOT
    // > process default ("runtime/data", CWD-relative, back-compat).
    if (!config.data_root.empty()) {
        Storage::set_app_data_root(config.data_root);
    } else if (const char* env_root = std::getenv("MINIANDROID_DATA_ROOT");
               env_root && *env_root) {
        Storage::set_app_data_root(env_root);
    }
    runtime::ExecutionEngine engine;
    // EXP-086 Phase 7 (B4 FIX): Set up ShadowRegistry so Handler/Looper
    // dispatch is wired up. Without this, Handler.post() calls during
    // onCreate are silently dropped.
    // EXP-087 Phase 3 (B2 FIX): Also set APK path on ActivityShadow so
    // setContentView(int) can find layout_cache.json.
    // EXP-092+ FIX: Register CollectionShadow so HashMap.put/get actually
    // store and retrieve entries. Without CollectionShadow, HashMap.put is
    // a silent no-op and HashMap.get always returns null. This breaks
    // Telegram's PhoneView.setCountry which calls HashMap.get("US") to
    // look up the country code — without CollectionShadow, the get returns
    // null, setCountry returns early, countryState stays at 1, and
    // onNextPressed takes the needShowAlert side path instead of reaching
    // auth.sendCode.
    framework::ShadowRegistry shadow_registry;
    // MASTER CAMPAIGN FIX (F20 §23): ONE canonical platform shadow list.
    // This registry previously held a REDUCED shadow set (no ThreadShadow,
    // LooperShadow, ArchTaskExecutorShadow) while ApplicationRuntime built a
    // FULL one — whichever registry won DalvikExecutionEngine::
    // set_shadow_registry left the other's shadows invisible. On this path
    // the androidx main-thread identity chain
    // (Looper.getMainLooper().getThread() == Thread.currentThread()) then
    // fell to the legacy bridge with mismatching object ids and every
    // LifecycleRegistry.enforceMainThreadIfNeeded call threw
    // IllegalStateException (fr.neamar.kiss v224 = motivating failure).
    framework::register_platform_shadows(shadow_registry);
    auto* handler_shadow = shadow_registry.find_as<framework::HandlerShadow>();
    auto* view_shadow = shadow_registry.find_as<framework::ViewShadow>();
    auto* dialog_shadow = shadow_registry.find_as<framework::DialogShadow>();
    auto* array_adapter_shadow = shadow_registry.find_as<framework::ArrayAdapterShadow>();
    auto* canvas_shadow = shadow_registry.find_as<framework::CanvasShadow>();
    auto* activity_shadow = shadow_registry.find_as<framework::ActivityShadow>();
    auto* collection_shadow = shadow_registry.find_as<framework::CollectionShadow>();
    if (activity_shadow) {
        activity_shadow->set_apk_path(apk_path);
    }
    (void)handler_shadow; (void)view_shadow; (void)collection_shadow; (void)dialog_shadow; (void)array_adapter_shadow; (void)canvas_shadow;
    engine.set_shadow_registry(&shadow_registry);
    // F-083: execute on the ART-sized stack (see the runner's comment).
    auto result = run_on_art_sized_stack(engine, apk_path, config);
    
    std::cout << "\n=== Execution Result ===\n\n";
    
    switch (result.status) {
        case runtime::ExecutionStatus::SUCCESS:
            std::cout << "Status: SUCCESS ✅\n";
            break;
        case runtime::ExecutionStatus::PARTIAL_SUCCESS:
            std::cout << "Status: PARTIAL SUCCESS ⚠️\n";
            break;
        case runtime::ExecutionStatus::FAILURE:
            std::cout << "Status: FAILURE ❌\n";
            break;
        case runtime::ExecutionStatus::CRASH:
            std::cout << "Status: CRASH 💥\n";
            break;
    }
    
    std::cout << "\nMessage: " << result.status_message << "\n\n";
    std::cout << "--- Metrics ---\n";
    std::cout << "API Calls: " << result.metrics.api_calls_count << "\n";
    std::cout << "Frames Rendered: " << result.metrics.frames_rendered << "\n";
    std::cout << "Execution Time: " << result.metrics.duration_ms << "ms\n";
    std::cout << "Errors: " << result.metrics.errors_count << "\n";
    std::cout << "Warnings: " << result.metrics.warnings_count << "\n\n";
    
    if (!result.screenshot_path.empty()) {
        std::cout << "Screenshot: " << result.screenshot_path << "\n";
    }
    if (!result.report_path.empty()) {
        std::cout << "Report: " << result.report_path << "\n";
    }
    
    return (result.status == runtime::ExecutionStatus::SUCCESS) ? 0 : 1;
}

int main(int argc, char* argv[]) {
    // S100 §3/§7 (issue #345): every signal death must leave an evidence
    // block (signal, fault addr, last DEX ops, native frames) — never a
    // silent mystery. Installed before any runtime work.
    CrashForensics::install();
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }
    
    std::string command = argv[1];
    
    // Handle version/help immediately
    if (command == "version" || command == "--version" || command == "-v") {
        print_version();
        return 0;
    }
    
    if (command == "help" || command == "--help" || command == "-h") {
        print_usage(argv[0]);
        return 0;
    }
    
    // Parse options
    runtime::ExecutionConfig config;
    if (std::getenv("MINIANDROID_SAMPLE")) {
        SampleProfiler::inst().start();
        atexit([] { SampleProfiler::inst().stop_and_report(); });
    }
    std::string apk_path;
    bool verbose = false;
    // F-NEW-231: run-by-package (installed state; package identity only).
    std::string run_package;
    // GATE A (issue #370): pkginspect options.
    std::string inspect_what = "all";
    std::string inspect_jsonl;
    std::string inspect_file_io;   // #371 PHASE C: runtime file-IO trace
    std::string inspect_api_trace; // #371 PHASE C: runtime API trace

    // F-107b2 (R-NEW-381, S61): per-instruction tracing is OFF by default
    // (trace_cap=0). The gprof profile showed the always-on InstructionTrace
    // machinery (Clock::now() ×2 per instruction + ring-buffer erase O(n))
    // is a top-2 interpreter cost while its output is a forensic artifact,
    // not primary evidence. Opt in per run: MINIANDROID_TRACE_CAP=<n>.
    if (const char* tc = std::getenv("MINIANDROID_TRACE_CAP"); tc && *tc) {
        unsigned long v = std::strtoul(tc, nullptr, 10);
        config.trace_cap = static_cast<size_t>(v);
        std::cout << "[*] TRACE-CAP enabled (" << v << " instruction traces)" << std::endl;
    }
    if (const char* ac = std::getenv("MINIANDROID_API_TRACE_CAP"); ac && *ac) {
        unsigned long v = std::strtoul(ac, nullptr, 10);
        config.api_call_trace_cap = static_cast<size_t>(v);
        std::cout << "[*] API-TRACE-CAP set to " << v << std::endl;
    }
    
    for (int i = 2; i < argc; i++) {
        std::string arg = argv[i];
        
        if ((arg == "-o" || arg == "--output") && i + 1 < argc) {
            config.output_directory = argv[++i];
        } else if (arg == "-v" || arg == "--verbose") {
            verbose = true;
            config.verbose_logging = true;
        } else if (arg == "--width" && i + 1 < argc) {
            config.screen_width = std::stoi(argv[++i]);
        } else if (arg == "--height" && i + 1 < argc) {
            config.screen_height = std::stoi(argv[++i]);
        } else if (arg == "--text" && i + 1 < argc) {
            config.simulated_text = argv[++i];
        } else if (arg == "--click-test") {
            // UNIFIED_011.2 CLICK-TEST: probe every clickable view, verify
            // touch → callback → state change → second frame (§10).
            config.click_test = true;
            std::cout << "[*] CLICK-TEST enabled (dispatch real clicks after first frame)\n";
        } else if (arg == "--trace-ui") {
            // S135 VISUAL RUNTIME BOOT/TRACE LOGGER: render the runtime
            // boot/trace panel onto a COPY of the authoritative frame →
            // trace_overlay.png (the authoritative screenshot stays clean).
            // Default panel; MINIANDROID_TRACE_UI=header/expanded overrides.
            setenv("MINIANDROID_TRACE_UI",
                   getenv("MINIANDROID_TRACE_UI") ? getenv("MINIANDROID_TRACE_UI") : "1",
                   0);
            setenv("MINIANDROID_BOOT_TRACE", "1", 0);
            std::cout << "[*] TRACE-UI enabled (S135 visual runtime trace overlay)\n";
        } else if (arg == "--trace") {
            // S135 machine-readable trace only (trace.jsonl + summary, no UI).
            setenv("MINIANDROID_BOOT_TRACE", "1", 0);
            std::cout << "[*] BOOT-TRACE enabled (S135 runtime event backbone)\n";
        } else if (arg == "--dump-api-trace") {
            // S69 SOURCE-LINKED CAMPAIGN: dump the engine's ApiCallTrace
            // ring to <output>/api_calls.json (live dispatch surface:
            // class.method + descriptor + IMPLEMENTED/STUBBED/MISSING/ERROR
            // status per call). Data source of the API coverage matrix.
            config.dump_api_trace = true;
            std::cout << "[*] DUMP-API-TRACE enabled (api_calls.json after execution)\n";
        } else if (arg == "--dump-view-tree") {
            // S67 FOUNDATION: dump the live ViewShadow tree to
            // <output>/view_tree.json (canonical view→pixel provenance
            // artifact; x/y/w/h/class/text/visibility per node).
            config.dump_view_tree = true;
            std::cout << "[*] DUMP-VIEW-TREE enabled (view_tree.json after final capture)\n";
        } else if (arg == "--max-seconds" && i + 1 < argc) {
            // S60 (R-NEW-380): wall-clock soft budget for the DEX dispatch.
            // Graceful stop identical to the instruction budget — the
            // end-of-run evidence pipeline (screenshot/trace/report) still
            // runs. 0 (default) = disabled.
            config.max_wall_seconds = static_cast<uint64_t>(std::stoul(argv[++i]));
            std::cout << "[*] MAX-SECONDS enabled (" << config.max_wall_seconds
                      << " s wall-clock soft budget)\n";
        } else if (arg == "--max-instructions" && i + 1 < argc) {
            // F-NEW-084 closeout (cont375): session INSTRUCTION BUDGET knob.
            // This is a RESOURCE budget (like --max-seconds), NOT the
            // semantic loop-visit guard — the 50k stale-branch forward-
            // progress law is untouched. Rationale: fairymahjong's
            // Lw4;.<init> tile-atlas scan is a legitimately bounded
            // computation that needs >100M interpreter instructions
            // (progress proven: branch operands advance, full-body PC
            // cycling 145..178/257, RSS grows with real decode; recorded
            // [PROGRESS] evidence). The default 100M budget must remain
            // for ordinary runs; long-running games opt in explicitly.
            config.max_instructions = static_cast<uint64_t>(
                std::stoull(argv[++i]));
            std::cout << "[*] MAX-INSTRUCTIONS enabled ("
                      << config.max_instructions
                      << " instruction budget; loop-visit law unchanged)\n";
        } else if (arg == "--click-count" && i + 1 < argc) {
            // DEMO-CLICK-SEQUENCE: dispatch N sequential clicks (round-robin
            // over all clickable views), re-rendering and saving a PNG frame
            // after each click into <output>/frames/. The state transitions
            // in those frames come from the APK's own DEX logic.
            config.click_count = std::stoi(argv[++i]);
            std::cout << "[*] CLICK-SEQUENCE enabled (" << config.click_count
                      << " clicks, frames saved to <output>/frames/)\n";
        } else if (arg == "--frames" && i + 1 < argc) {
            // TIME-DRIVEN FRAME CAPTURE: advance the Handler virtual clock by
            // --frame-delay per frame, fire every due postDelayed Runnable
            // (self-reposting animation tickers step here), re-render, save.
            // State transitions come from the APK's DEX logic reacting to
            // Looper time. Mutually exclusive with --click-count.
            config.frame_count = std::stoi(argv[++i]);
            std::cout << "[*] FRAME-SEQUENCE enabled (" << config.frame_count
                      << " frames @ +" << config.frame_delay_ms
                      << "ms virtual each, saved to <output>/frames/)\n";
        } else if (arg == "--long-press" && i + 1 < argc) {
            // GOLDEN-02: coordinate-anchored long-press gesture. After the
            // launch frame: hit_test(x,y) → target → 500ms long-press
            // timeout → performLongClick → onLongClick dispatch; consumed
            // long press suppresses the UP click (AOSP View.java law).
            std::string spec = argv[++i];
            auto comma = spec.find(',');
            if (comma == std::string::npos) {
                std::cerr << "[ERROR] --long-press expects <x>,<y> (got \""
                          << spec << "\")\n";
                return 1;
            }
            config.long_press_enabled = true;
            config.long_press_x = std::stoi(spec.substr(0, comma));
            config.long_press_y = std::stoi(spec.substr(comma + 1));
            std::cout << "[*] LONG-PRESS gesture enabled at ("
                      << config.long_press_x << "," << config.long_press_y
                      << ") — frame saved to <output>/frames/\n";
        } else if (arg == "--tap" && i + 1 < argc) {
            // G06 §4/§6: canonical tap gesture through the TouchDispatcher
            // law pipeline: DOWN → pressed frame → UP → queued PerformClick
            // (one-MessageQueue law) → UnsetPressedState → post-click frame.
            std::string spec = argv[++i];
            // S73 F-117 extension: `x,y@frame` fires the tap after frame
            // `frame` renders (scheduled-input cadence). All-or-none: if any
            // tap carries '@', every tap must (validated below).
            int tap_at_frame = -1;
            auto at_sign = spec.rfind('@');
            if (at_sign != std::string::npos) {
                tap_at_frame = std::stoi(spec.substr(at_sign + 1));
                spec = spec.substr(0, at_sign);
            }
            auto comma = spec.find(',');
            if (comma == std::string::npos) {
                std::cerr << "[ERROR] --tap expects <x>,<y> or <x>,<y>@<frame> (got \""
                          << spec << "\")\n";
                return 1;
            }
            config.tap_enabled = true;
            config.tap_sequence.emplace_back(std::stoi(spec.substr(0, comma)),
                                             std::stoi(spec.substr(comma + 1)));
            if (tap_at_frame >= 0)
                config.tap_at_frames.push_back(tap_at_frame);
            if (!config.tap_at_frames.empty() &&
                config.tap_at_frames.size() != config.tap_sequence.size()) {
                std::cerr << "[ERROR] --tap '@frame' is all-or-none: "
                          << config.tap_sequence.size() << " taps but "
                          << config.tap_at_frames.size()
                          << " scheduled frames\n";
                return 1;
            }
            std::cout << "[*] TAP gesture " << config.tap_sequence.size()
                      << " queued at (" << config.tap_sequence.back().first
                      << "," << config.tap_sequence.back().second
                      << (tap_at_frame >= 0
                              ? (") after frame " + std::to_string(tap_at_frame))
                              : "")
                      << ") — frames + touch trace saved to <output>/frames/\n";
        } else if (arg == "--swipe" && i + 1 < argc) {
            // S129 (R-NEW-425/426): generic swipe/drag gesture through the
            // TouchDispatcher law pipeline. DOWN at (x1,y1), N MOVEs at 16ms
            // virtual intervals (60Hz) (linear interpolation), UP at (x2,y2).
            // `x1,y1,x2,y2@frame` schedules the fire frame (F-117 cadence).
            std::string spec = argv[++i];
            int swipe_at_frame = 2;
            auto at_sign = spec.rfind('@');
            if (at_sign != std::string::npos) {
                swipe_at_frame = std::stoi(spec.substr(at_sign + 1));
                spec = spec.substr(0, at_sign);
            }
            std::vector<int> vals;
            size_t pos = 0;
            while (vals.size() < 4) {
                auto comma = spec.find(',', pos);
                if (comma == std::string::npos) {
                    vals.push_back(std::stoi(spec.substr(pos)));
                    break;
                }
                vals.push_back(std::stoi(spec.substr(pos, comma - pos)));
                pos = comma + 1;
            }
            if (vals.size() != 4) {
                std::cerr << "[ERROR] --swipe expects x1,y1,x2,y2[@frame] (got \""
                          << argv[i] << "\")\n";
                return 1;
            }
            config.swipe_enabled = true;
            config.swipe_x1 = vals[0];
            config.swipe_y1 = vals[1];
            config.swipe_x2 = vals[2];
            config.swipe_y2 = vals[3];
            config.swipe_at_frame = swipe_at_frame;
            std::cout << "[*] SWIPE gesture queued (" << vals[0] << "," << vals[1]
                      << ") -> (" << vals[2] << "," << vals[3] << ") after frame "
                      << swipe_at_frame << " — frames + touch trace saved to <output>/frames/\n";
        } else if (arg == "--frame-delay" && i + 1 < argc) {
            config.frame_delay_ms = std::stoi(argv[++i]);
            std::cout << "[*] frame delay: " << config.frame_delay_ms << "ms virtual\n";
        } else if ((arg == "--data-root" || arg.rfind("--data-root=", 0) == 0) ) {
            // M3 FINDING-012: per-invocation app private storage root.
            std::string root;
            if (arg.rfind("--data-root=", 0) == 0) {
                root = arg.substr(strlen("--data-root="));
            } else if (i + 1 < argc) {
                root = argv[++i];
            }
            if (root.empty()) {
                std::cerr << "[ERROR] --data-root expects a directory\n";
                return 1;
            }
            config.data_root = root;
        } else if (arg == "--package" && i + 1 < argc) {
            run_package = argv[++i];
        } else if (arg == "--what" && i + 1 < argc) {
            // GATE A: section filter for pkginspect (comma-separated).
            inspect_what = argv[++i];
        } else if (arg == "--jsonl" && i + 1 < argc) {
            // GATE A: full-fidelity machine-readable JSONL output path.
            inspect_jsonl = argv[++i];
        } else if (arg == "--file-io" && i + 1 < argc) {
            // #371 PHASE C: bind a runtime file-IO trace (MINIANDROID_FILE_IO
            // JSONL) so pkginspect serves the RUNTIME + DIAGNOSTICS sections.
            inspect_file_io = argv[++i];
        } else if (arg == "--api-trace" && i + 1 < argc) {
            // #371 PHASE C: bind a run api_trace.json for the API census +
            // first-divergence diagnostics.
            inspect_api_trace = argv[++i];
        } else if (arg.find("--execution-mode") == 0) {
            // EXP-031: Parse execution mode
            std::string mode_str;
            if (arg.find('=') != std::string::npos) {
                mode_str = arg.substr(arg.find('=') + 1);
            } else if (i + 1 < argc) {
                mode_str = argv[++i];
            }
            
            if (mode_str == "legacy" || mode_str == "LEGACY") {
                config.execution_mode = runtime::ExecutionMode::LEGACY;
                std::cout << "[*] Execution mode: LEGACY (simulated lifecycle)\n";
            } else if (mode_str == "real-dalvik" || mode_str == "REAL_DALVIK") {
                config.execution_mode = runtime::ExecutionMode::REAL_DALVIK;
                std::cout << "[*] Execution mode: REAL_DALVIK (bytecode interpretation)\n";
            } else {
                std::cerr << "[ERROR] Unknown execution mode: " << mode_str << std::endl;
                std::cerr << "[INFO] Valid modes: legacy, real-dalvik\n";
                return 1;
            }
        } else if (arg[0] != '-') {
            apk_path = arg;
        } else {
            std::cerr << "[WARNING] Unknown option: " << arg << std::endl;
        }
    }
    
    if (apk_path.empty() && run_package.empty() && command != "list-packages" &&
        command != "pkgaudit" && command != "pkginspect" && command != "uninstall") {
        std::cerr << "[ERROR] No APK file specified\n\n";
        print_usage(argv[0]);
        return 1;
    }

    // F-NEW-231: resolve an installed package from identity alone. The run
    // then operates on the INSTALLED base.apk — provenance flows from the
    // resolved codePath (ApplicationInfo.sourceDir law), not the sideload.
    // (pkgaudit does its own resolution + JSON — keep stdout machine-clean.)
    // (pkginspect likewise resolves internally and keeps stdout machine-
    // readable — GATE A inspection is its own resolution authority.)
    // (uninstall must NOT be pre-guarded: NOT_INSTALLED is its own honest
    // verdict with its own exit contract, like PMS NAME_NOT_FOUND.)
    if (!run_package.empty() && command != "pkgaudit" && command != "pkginspect" &&
        command != "uninstall") {
        if (config.data_root.empty()) {
            std::cerr << "[ERROR] --package requires --data-root <dir>\n";
            return 1;
        }
        auto installed = pkgstore::package_dir(config.data_root, run_package)
                         / "base.apk";
        std::error_code ec;
        if (!std::filesystem::exists(installed, ec)) {
            std::cerr << "[ERROR] Package not installed: " << run_package
                      << " (looked for " << installed.string() << ")\n";
            return 1;
        }
        std::cout << "[*] INSTALLED-PACKAGE MODE: " << run_package << "\n";
        std::cout << "[*] codePath: " << installed.string() << "\n";
        apk_path = installed.string();
    }

    // Interaction drivers are mutually exclusive: one manifest writer per run.
    if (config.click_count > 0 && config.frame_count > 0) {
        std::cerr << "[ERROR] --click-count and --frames are mutually exclusive "
                  << "(use two runs to capture both proof modes)\n";
        return 1;
    }
    
    // Execute command
    if (command == "install") {
        return cmd_install(apk_path, config.data_root, verbose);
    } else if (command == "uninstall") {
        return cmd_uninstall(run_package, config.data_root);
    } else if (command == "list-packages") {
        return cmd_list_packages(config.data_root);
    } else if (command == "pkgaudit") {
        return cmd_pkg_audit(run_package, config.data_root);
    } else if (command == "pkginspect") {
        // GATE A (issue #370): installed-environment inspection. Package
        // resolution is INTERNAL (pkgaudit-style: stdout stays machine-clean).
        miniandroid::gatea::InspectRequest req;
        req.package = run_package;
        req.data_root = config.data_root;
        req.apk_path = apk_path;
        req.what = inspect_what;
        req.jsonl_out = inspect_jsonl;
        req.file_io_path = inspect_file_io;
        req.api_trace_path = inspect_api_trace;
        req.verbose = verbose;
        return miniandroid::gatea::cmd_pkg_inspect(req);
    } else if (command == "analyze") {
        return cmd_analyze(apk_path, verbose);
    } else if (command == "dex") {
        return cmd_dex(apk_path, verbose);
    } else if (command == "run") {
        return cmd_run(apk_path, config);
    } else {
        std::cerr << "[ERROR] Unknown command: " << command << "\n\n";
        print_usage(argv[0]);
        return 1;
    }
}
