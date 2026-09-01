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
#include <filesystem>

#include "runtime/execution_engine.h"
#include "apk/apk_parser.h"
// EXP-086 Phase 7 (B4 FIX): ShadowRegistry + HandlerShadow for Runnable queue
#include "framework/android_shadows.h"
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
    std::cout << "  version   Show version information\n";
    std::cout << "  help      Show this help message\n\n";
    std::cout << "Options:\n";
    std::cout << "  -o, --output <dir>     Output directory (default: ./run)\n";
    std::cout << "  -v, --verbose          Enable verbose output\n";
    std::cout << "  --width <pixels>       Screen width (default: 1080)\n";
    std::cout << "  --height <pixels>      Screen height (default: 1920)\n";
    std::cout << "  --text <text>          Override displayed text\n";
    std::cout << "  --click-test           Dispatch real clicks on clickable views after the first frame\n";
    std::cout << "  --execution-mode <mode> Execution mode: legacy | real-dalvik (default: real-dalvik)\n\n";
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

int cmd_run(const std::string& apk_path, const runtime::ExecutionConfig& config) {
    std::cout << "[*] Running APK: " << apk_path << std::endl;
    std::cout << "[*] Output directory: " << config.output_directory << std::endl;
    
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
    auto* handler_shadow = shadow_registry.register_shadow<framework::HandlerShadow>();
    auto* view_shadow = shadow_registry.register_shadow<framework::ViewShadow>();
    auto* activity_shadow = shadow_registry.register_shadow<framework::ActivityShadow>();
    auto* collection_shadow = shadow_registry.register_shadow<framework::CollectionShadow>();
    if (activity_shadow) {
        activity_shadow->set_apk_path(apk_path);
    }
    (void)handler_shadow; (void)view_shadow; (void)collection_shadow;
    engine.set_shadow_registry(&shadow_registry);
    auto result = engine.execute(apk_path, config);
    
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
    std::string apk_path;
    bool verbose = false;
    
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
    
    if (apk_path.empty()) {
        std::cerr << "[ERROR] No APK file specified\n\n";
        print_usage(argv[0]);
        return 1;
    }
    
    // Execute command
    if (command == "analyze") {
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
