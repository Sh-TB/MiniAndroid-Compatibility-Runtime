/*
 * MiniAndroid Runtime v0.1 - EXP-002 Main Entry Point
 * 
 * Experiment: MiniAndroid HelloWorld Runtime Stub
 * Goal: Real APK entry-point resolution (Class Resolution only)
 * 
 * Pipeline:
 *   APK → classes.dex → class_defs → MainActivity → method_ids → onCreate()
 * 
 * Output: execution_trace.json
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <ctime>
#include <filesystem>

#include "apk/apk_parser.h"
#include "dex/dex_parser.h"
#include "dex/class_resolver.h"
#include "diagnostics/trace_engine.h"

#include "../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace fs = std::filesystem;
using json = nlohmann::json;

// ============================================================================
// JSON Serialization Helpers
// ============================================================================

json execution_trace_to_json(const miniandroid::dex::ExecutionTrace& trace) {
    json j;
    
    // Metadata
    j["experiment_id"] = trace.experiment_id;
    j["timestamp"] = trace.timestamp;
    j["apk_path"] = trace.apk_path;
    j["dex_path"] = trace.dex_path;
    
    // Entry point
    j["entry_point"] = {
        {"class_name", trace.entry_point.class_name},
        {"readable_class", trace.entry_point.readable_class},
        {"method_name", trace.entry_point.method_name},
        {"descriptor", trace.entry_point.descriptor},
        {"resolved", trace.entry_point.resolved},
        {"status", static_cast<int>(trace.entry_point.status)},
        {"bytecode_offset", trace.entry_point.hex_offset},
        {"instructions", trace.entry_point.instruction_count},
        {"has_bytecode", trace.entry_point.has_bytecode},
        {"is_activity", trace.entry_point.is_activity},
        {"overrides_oncreate", trace.entry_point.overrides_oncreate}
    };
    
    // Pipeline stages
    json stages = json::array();
    for (const auto& stage : trace.pipeline_stages) {
        stages.push_back({
            {"name", stage.name},
            {"success", stage.success},
            {"duration_ms", stage.duration_ms},
            {"evidence", stage.evidence}
        });
    }
    j["pipeline_stages"] = stages;
    
    // Activity classes
    j["activity_classes"] = trace.activity_classes;
    
    // Method map
    json method_map = json::array();
    for (const auto& entry : trace.method_map) {
        method_map.push_back({
            {"name", entry.name},
            {"descriptor", entry.descriptor},
            {"offset", std::string("0x") + 
                ([&]() { std::stringstream ss; ss << std::hex << entry.offset; return ss.str(); })()},
            {"has_code", entry.has_code},
            {"insn_count", entry.insn_count}
        });
    }
    j["method_map"] = method_map;
    
    // Issues
    json issues = json::array();
    for (const auto& issue : trace.issues) {
        issues.push_back({
            {"severity", issue.severity},
            {"code", issue.code},
            {"message", issue.message}
        });
    }
    j["issues"] = issues;
    
    // Final status
    j["success"] = trace.success;
    j["status_message"] = trace.status_message;
    
    return j;
}

// ============================================================================
// Timestamp Generator
// ============================================================================

std::string get_timestamp() {
    auto now = std::time(nullptr);
    char buf[64];
    std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", std::gmtime(&now));
    return std::string(buf);
}

// ============================================================================
// Main Application
// ============================================================================

int main(int argc, char* argv[]) {
    std::cout << "============================================================\n";
    std::cout << "  MiniAndroid Runtime v0.1 - EXP-002\n";
    std::cout << "  HelloWorld Runtime Stub - Class Resolution\n";
    std::cout << "============================================================\n\n";
    
    // Default APK path
    std::string apk_path = "test_apks/HelloWorld.apk";
    
    if (argc > 1) {
        apk_path = argv[1];
    }
    
    // Output directory
    std::string output_dir = "run";
    fs::create_directories(output_dir);
    
    std::cout << "[EXP-002] Starting Class Resolution Pipeline\n";
    std::cout << "[EXP-002] Target APK: " << apk_path << "\n\n";
    
    // =========================================================================
    // Stage 1: APK Parsing (EXP-001 Checkpoint)
    // =========================================================================
    std::cout << "[Stage 1] APK Parsing (EXP-001 Checkpoint)\n";
    std::cout << "----------------------------------------\n";
    
    miniandroid::apk::ApkParser apk_parser;
    apk_parser.set_verbose(true);
    
    auto apk_info = apk_parser.parse(apk_path);
    
    if (!apk_info.is_valid) {
        std::cerr << "[ERROR] Failed to parse APK: " << apk_info.validation_error << "\n";
        return 1;
    }
    
    std::cout << "✓ Package: " << apk_info.package_name << "\n";
    std::cout << "✓ Main Activity: " << apk_info.main_activity << "\n";
    std::cout << "✓ DEX files: " << apk_info.dex_files.size() << "\n";
    
    // Save APK info (EXP-001 artifact)
    json apk_json;
    apk_json["package_name"] = apk_info.package_name;
    apk_json["version_name"] = apk_info.version_name;
    apk_json["version_code"] = apk_info.version_code;
    apk_json["main_activity"] = apk_info.main_activity;
    apk_json["permissions"] = apk_info.permissions;
    apk_json["dex_files"] = apk_info.dex_files;
    apk_json["min_sdk"] = apk_info.min_sdk_version;
    
    std::ofstream apk_out(output_dir + "/apk_info.json");
    apk_out << std::setw(4) << apk_json << "\n";
    apk_out.close();
    std::cout << "✓ Saved: run/apk_info.json\n\n";
    
    // =========================================================================
    // Stage 2: DEX Parsing (EXP-001 Checkpoint)
    // =========================================================================
    std::cout << "[Stage 2] DEX Parsing (EXP-001 Checkpoint)\n";
    std::cout << "-----------------------------------------\n";
    
    // Find classes.dex in APK
    std::string dex_path;
    if (!apk_info.dex_files.empty()) {
        // Extract DEX from APK
        dex_path = output_dir + "/classes.dex";
        
        auto dex_data = apk_parser.extract_entry(apk_path, "classes.dex");
        if (dex_data.empty()) {
            std::cerr << "[ERROR] Failed to extract classes.dex from APK\n";
            return 1;
        }
        
        // Write extracted DEX
        std::ofstream dex_out(dex_path, std::ios::binary);
        dex_out.write(reinterpret_cast<const char*>(dex_data.data()), dex_data.size());
        dex_out.close();
        
        std::cout << "✓ Extracted classes.dex (" << dex_data.size() << " bytes)\n";
    } else {
        // Try direct path
        dex_path = "test_apks/classes.dex";
        if (!fs::exists(dex_path)) {
            std::cerr << "[ERROR] No DEX file found\n";
            return 1;
        }
    }
    
    // Parse DEX
    miniandroid::dex::DexParser dex_parser;
    dex_parser.set_verbose(true);
    
    auto dex_report = dex_parser.parse(dex_path);
    
    if (!dex_report.is_valid) {
        std::cerr << "[ERROR] Failed to parse DEX: " << dex_report.validation_error << "\n";
        return 1;
    }
    
    std::cout << "✓ DEX Version: " << dex_report.dex_version << "\n";
    std::cout << "✓ Classes: " << dex_report.classes_count << "\n";
    std::cout << "✓ Methods: " << dex_report.methods_count << "\n";
    std::cout << "✓ Strings: " << dex_report.strings_count << "\n";
    
    // Save DEX report (EXP-001 artifact)
    json dex_json;
    dex_json["dex_version"] = dex_report.dex_version;
    dex_json["classes_count"] = dex_report.classes_count;
    dex_json["methods_count"] = dex_report.methods_count;
    dex_json["strings_count"] = dex_report.strings_count;
    dex_json["types_count"] = dex_report.types_count;
    
    json classes_arr = json::array();
    for (const auto& cls : dex_report.classes) {
        json cls_json;
        cls_json["name"] = cls.name;
        cls_json["superclass"] = cls.superclass_name;
        cls_json["source_file"] = cls.source_file;
        
        json methods_arr = json::array();
        for (const auto& m : cls.all_methods()) {
            methods_arr.push_back({
                {"name", m.name},
                {"descriptor", m.descriptor},
                {"has_code", !m.bytecode.empty()}
            });
        }
        cls_json["methods"] = methods_arr;
        classes_arr.push_back(cls_json);
    }
    dex_json["classes"] = classes_arr;
    
    std::ofstream dex_out_file(output_dir + "/dex_report.json");
    dex_out_file << std::setw(4) << dex_json << "\n";
    dex_out_file.close();
    std::cout << "✓ Saved: run/dex_report.json\n\n";
    
    // =========================================================================
    // Stage 3: Class Resolution (EXP-002 Core)
    // =========================================================================
    std::cout << "[Stage 3] Class Resolution (EXP-002 Core)\n";
    std::cout << "------------------------------------------\n";
    
    miniandroid::dex::ClassResolver resolver;
    resolver.set_verbose(true);
    
    // Resolve with target hints from manifest
    std::string target_class = apk_info.main_activity;
    
    // Remove package prefix if present
    size_t dot_pos = target_class.rfind('.');
    if (dot_pos != std::string::npos) {
        target_class = target_class.substr(dot_pos + 1);
    }
    
    std::cout << "[INFO] Resolving target class: " << target_class << "\n";
    
    auto trace = resolver.resolve_target(dex_report, target_class, "onCreate");
    
    // Set timestamp
    trace.timestamp = get_timestamp();
    trace.apk_path = fs::absolute(apk_path).string();
    trace.dex_path = fs::absolute(dex_path).string();
    
    // Print results
    std::cout << "\n[RESULTS]\n";
    std::cout << "───────────────────────────────────────────\n";
    std::cout << "Entry Point: " << trace.entry_point.readable_class 
              << "." << trace.entry_point.method_name << "\n";
    std::cout << "Resolved: " << (trace.entry_point.resolved ? "YES" : "NO") << "\n";
    std::cout << "Status: " << trace.status_message << "\n";
    
    if (trace.entry_point.has_bytecode) {
        std::cout << "Bytecode Offset: " << trace.entry_point.hex_offset << "\n";
        std::cout << "Instructions: " << trace.entry_point.instruction_count << "\n";
    } else {
        std::cout << "Bytecode: Not available (abstract/native?)\n";
    }
    
    std::cout << "\nPipeline Stages:\n";
    for (const auto& stage : trace.pipeline_stages) {
        std::cout << "  [" << (stage.success ? "OK" : "FAIL") << "] " << stage.name;
        std::cout << " (" << std::fixed << std::setprecision(2) << stage.duration_ms << "ms)\n";
        std::cout << "      " << stage.evidence << "\n";
    }
    
    if (!trace.issues.empty()) {
        std::cout << "\nIssues:\n";
        for (const auto& issue : trace.issues) {
            std::cout << "  [" << issue.severity << "] " << issue.code << ": " << issue.message << "\n";
        }
    }
    
    // =========================================================================
    // Stage 4: Generate Output Artifacts
    // =========================================================================
    std::cout << "\n[Stage 4] Generating Output Artifacts\n";
    std::cout << "--------------------------------------\n";
    
    // Generate execution_trace.json (main EXP-002 artifact)
    json trace_json = execution_trace_to_json(trace);
    
    std::ofstream trace_out(output_dir + "/execution_trace.json");
    trace_out << std::setw(4) << trace_json << "\n";
    trace_out.close();
    std::cout << "✓ Saved: run/execution_trace.json\n";
    
    // Generate human-readable report
    std::ofstream report_out(output_dir + "/report.md");
    report_out << "# MiniAndroid Execution Report - EXP-002\n\n";
    report_out << "## Experiment: HelloWorld Runtime Stub\n\n";
    report_out << "**Goal:** Real APK entry-point resolution (Class Resolution only)\n\n";
    report_out << "---\n\n";
    
    report_out << "## Application\n";
    report_out << "- **APK:** " << fs::absolute(apk_path).filename().string() << "\n";
    report_out << "- **Package:** " << apk_info.package_name << "\n";
    report_out << "- **Main Activity:** " << apk_info.main_activity << "\n\n";
    
    report_out << "## Execution Status: ";
    report_out << (trace.success ? "**SUCCESS**" : "**FAILURE**") << "\n\n";
    
    report_out << "## Entry Point Resolution\n";
    report_out << "| Property | Value |\n";
    report_out << "|----------|-------|\n";
    report_out << "| Class | `" << trace.entry_point.readable_class << "` |\n";
    report_out << "| Method | `" << trace.entry_point.method_name << "` |\n";
    report_out << "| Descriptor | `" << trace.entry_point.descriptor << "` |\n";
    report_out << "| Resolved | " << (trace.entry_point.resolved ? "✅ Yes" : "❌ No") << " |\n";
    report_out << "| Bytecode Offset | `" << trace.entry_point.hex_offset << "` |\n";
    report_out << "| Instructions | " << trace.entry_point.instruction_count << " |\n";
    report_out << "| Has Bytecode | " << (trace.entry_point.has_bytecode ? "Yes" : "No") << " |\n";
    report_out << "| Is Activity | " << (trace.entry_point.is_activity ? "Yes" : "No") << " |\n\n";
    
    report_out << "## Pipeline Stages\n";
    report_out << "| Stage | Status | Duration | Evidence |\n";
    report_out << "|-------|--------|----------|----------|\n";
    for (const auto& stage : trace.pipeline_stages) {
        report_out << "| " << stage.name << " | "
                   << (stage.success ? "✅" : "❌") << " | "
                   << std::fixed << std::setprecision(2) << stage.duration_ms << "ms | "
                   << stage.evidence << " |\n";
    }
    
    if (!trace.issues.empty()) {
        report_out << "\n## Issues/Warnings\n";
        for (const auto& issue : trace.issues) {
            report_out << "- **[" << issue.severity << "]** " << issue.code 
                       << ": " << issue.message << "\n";
        }
    }
    
    report_out << "\n## Method Map (" << trace.entry_point.readable_class << ")\n";
    report_out << "| Method | Descriptor | Offset | Code |\n";
    report_out << "|--------|------------|--------|------|\n";
    for (const auto& entry : trace.method_map) {
        std::stringstream ss;
        ss << "0x" << std::hex << entry.offset;
        report_out << "| `" << entry.name << "` | `" << entry.descriptor 
                   << "` | `" << ss.str() << "` | "
                   << (entry.has_code ? "Yes" : "No") << " |\n";
    }
    
    report_out << "\n---\n";
    report_out << "*Generated by MiniAndroid v0.1 - EXP-002*\n";
    report_out << "*Timestamp: " << trace.timestamp << "*\n";
    
    report_out.close();
    std::cout << "✓ Saved: run/report.md\n";
    
    // =========================================================================
    // Summary
    // =========================================================================
    std::cout << "\n============================================================\n";
    std::cout << "  EXP-002 Complete!\n";
    std::cout << "============================================================\n\n";
    
    std::cout << "Output Files:\n";
    std::cout << "  📄 run/execution_trace.json (Primary artifact)\n";
    std::cout << "  📄 run/apk_info.json (EXP-001 checkpoint)\n";
    std::cout << "  📄 run/dex_report.json (EXP-001 checkpoint)\n";
    std::cout << "  📄 run/report.md (Human-readable)\n\n";
    
    std::cout << "Resolution Result:\n";
    if (trace.entry_point.resolved && trace.entry_point.has_bytecode) {
        std::cout << "  ✅ FULLY RESOLVED - Ready for EXP-003 (DEX Interpreter)\n";
        std::cout << "     Entry: " << trace.entry_point.readable_class 
                  << "." << trace.entry_point.method_name << "\n";
        std::cout << "     Location: " << trace.entry_point.hex_offset 
                  << " (" << trace.entry_point.instruction_count << " instructions)\n";
    } else if (trace.entry_point.resolved) {
        std::cout << "  ⚠️  PARTIALLY RESOLVED - Class found, no bytecode\n";
        std::cout << "     Entry: " << trace.entry_point.readable_class 
                  << "." << trace.entry_point.method_name << "\n";
    } else {
        std::cout << "  ❌ NOT RESOLVED - Check issues above\n";
    }
    
    return trace.success ? 0 : 1;
}
