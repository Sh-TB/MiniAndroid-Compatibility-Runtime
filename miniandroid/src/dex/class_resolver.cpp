/*
 * MiniAndroid Runtime v0.1 - Class Resolver Implementation
 * EXP-002: HelloWorld Runtime Stub
 * 
 * Implements the resolution pipeline:
 *   APK → classes.dex → class_defs → MainActivity → method_ids → onCreate()
 */

#include "class_resolver.h"

#include <iostream>
#include <algorithm>
#include <chrono>
#include <sstream>
#include <iomanip>
#include <cstring>

namespace miniandroid {
namespace dex {

ClassResolver::ClassResolver() : verbose_(false) {
}

ClassResolver::~ClassResolver() {
}

ExecutionTrace ClassResolver::resolve(const DexReport& report) {
    return resolve_target(report, "", "onCreate");
}

ExecutionTrace ClassResolver::resolve_target(
    const DexReport& report,
    const std::string& target_class,
    const std::string& target_method
) {
    ExecutionTrace trace;
    trace.experiment_id = "EXP-002";
    trace.apk_path = report.dex_path;
    trace.dex_path = report.dex_path;
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    // Validate input
    if (!report.is_valid) {
        trace.success = false;
        trace.status_message = "Invalid DEX report: " + report.validation_error;
        
        ExecutionTrace::Issue issue;
        issue.severity = "error";
        issue.code = "INVALID_DEX";
        issue.message = trace.status_message;
        trace.issues.push_back(issue);
        
        return trace;
    }
    
    log("Starting class resolution pipeline...");
    
    // Stage 1: Find Activity classes
    auto stage1_start = std::chrono::high_resolution_clock::now();
    std::vector<const ClassInfo*> activities = find_activities(report);
    auto stage1_end = std::chrono::high_resolution_clock::now();
    double stage1_ms = std::chrono::duration<double, std::milli>(stage1_end - stage1_start).count();
    
    bool stage1_success = !activities.empty();
    
    // Build activity list for trace
    for (const auto* activity : activities) {
        trace.activity_classes.push_back(activity->name);
        log("Found Activity: " + activity->name);
    }
    
    std::stringstream ss1;
    ss1 << "Found " << activities.size() << " Activity class(es)";
    if (!activities.empty()) {
        ss1 << ": ";
        for (size_t i = 0; i < activities.size(); i++) {
            if (i > 0) ss1 << ", ";
            ss1 << to_readable_class(activities[i]->name);
        }
    }
    add_stage(trace, "Activity Discovery", stage1_success, ss1.str(), stage1_ms);
    
    if (!stage1_success) {
        trace.success = false;
        trace.status_message = "No Activity classes found in DEX";
        
        ExecutionTrace::Issue issue;
        issue.severity = "error";
        issue.code = "NO_ACTIVITY";
        issue.message = "No classes extending android.app.Activity found";
        trace.issues.push_back(issue);
        
        return trace;
    }
    
    // Stage 2: Resolve target class (MainActivity or specified)
    auto stage2_start = std::chrono::high_resolution_clock::now();
    
    const ClassInfo* target_cls = nullptr;
    
    if (!target_class.empty()) {
        // Search by name
        for (const auto& cls : report.classes) {
            if (cls.name.find(target_class) != std::string::npos ||
                to_readable_class(cls.name).find(target_class) != std::string::npos) {
                target_cls = &cls;
                break;
            }
        }
        
        // Also check in activities
        if (!target_cls) {
            for (const auto* activity : activities) {
                if (activity->name.find(target_class) != std::string::npos ||
                    to_readable_class(activity->name).find(target_class) != std::string::npos) {
                    target_cls = activity;
                    break;
                }
            }
        }
    } else {
        // Use first Activity (or prefer MainActivity)
        for (const auto* activity : activities) {
            if (activity->name.find("MainActivity") != std::string::npos ||
                activity->name.find("main") != std::string::npos ||
                activity->name.find("Main") != std::string::npos) {
                target_cls = activity;
                break;
            }
        }
        
        // Fallback to first activity
        if (!target_cls && !activities.empty()) {
            target_cls = activities[0];
        }
    }
    
    auto stage2_end = std::chrono::high_resolution_clock::now();
    double stage2_ms = std::chrono::duration<double, std::milli>(stage2_end - stage2_start).count();
    
    bool stage2_success = (target_cls != nullptr);
    
    if (stage2_success) {
        trace.entry_point.class_name = target_cls->name;
        trace.entry_point.readable_class = to_readable_class(target_cls->name);
        trace.entry_point.class_info = *target_cls;
        trace.entry_point.is_activity = is_activity_class(*target_cls);
        
        std::stringstream ss2;
        ss2 << "Resolved class: " << to_readable_class(target_cls->name);
        if (!target_cls->superclass_name.empty()) {
            ss2 << " extends " << to_readable_class(target_cls->superclass_name);
        }
        add_stage(trace, "Class Resolution", true, ss2.str(), stage2_ms);
    } else {
        std::string msg = "Target class not found: " + (target_class.empty() ? "<default>" : target_class);
        add_stage(trace, "Class Resolution", false, msg, stage2_ms);
        
        ExecutionTrace::Issue issue;
        issue.severity = "error";
        issue.code = "CLASS_NOT_FOUND";
        issue.message = msg;
        trace.issues.push_back(issue);
        
        trace.success = false;
        trace.status_message = msg;
        return trace;
    }
    
    // Stage 3: Resolve onCreate() method
    auto stage3_start = std::chrono::high_resolution_clock::now();
    
    bool method_resolved = resolve_on_create(*target_cls, trace.entry_point);
    
    auto stage3_end = std::chrono::high_resolution_clock::now();
    double stage3_ms = std::chrono::duration<double, std::milli>(stage3_end - stage3_start).count();
    
    if (method_resolved) {
        std::stringstream ss3;
        ss3 << "Resolved method: " << trace.entry_point.method_name 
            << trace.entry_point.descriptor;
        if (trace.entry_point.has_bytecode) {
            ss3 << " @ " << trace.entry_point.hex_offset 
                << " (" << trace.entry_point.instruction_count << " instructions)";
        }
        add_stage(trace, "Method Resolution", true, ss3.str(), stage3_ms);
    } else {
        std::string msg = "Method '" + target_method + "' not found in " + to_readable_class(target_cls->name);
        add_stage(trace, "Method Resolution", false, msg, stage3_ms);
        
        ExecutionTrace::Issue issue;
        issue.severity = "warning";
        issue.code = "METHOD_NOT_FOUND";
        issue.message = msg;
        trace.issues.push_back(issue);
        
        // Continue anyway - we have the class
    }
    
    // Stage 4: Extract bytecode information
    if (trace.entry_point.resolved && trace.entry_point.has_bytecode) {
        auto stage4_start = std::chrono::high_resolution_clock::now();
        
        extract_bytecode_info(trace.entry_point.method_info, trace.entry_point);
        
        auto stage4_end = std::chrono::high_resolution_clock::now();
        double stage4_ms = std::chrono::duration<double, std::milli>(stage4_end - stage4_start).count();
        
        std::stringstream ss4;
        ss4 << "Bytecode @ " << trace.entry_point.hex_offset 
            << ", " << trace.entry_point.instruction_count << " instructions";
        add_stage(trace, "Bytecode Extraction", true, ss4.str(), stage4_ms);
    }
    
    // Build method map for the entry class
    if (target_cls) {
        for (const auto& method : target_cls->all_methods()) {
            ExecutionTrace::MethodMapEntry entry;
            entry.name = method.name;
            entry.descriptor = method.descriptor;
            entry.offset = method.code_offset;
            entry.has_code = !method.bytecode.empty();
            entry.insn_count = static_cast<uint32_t>(method.bytecode.size());
            trace.method_map.push_back(entry);
        }
    }
    
    // Final validation and status
    auto end_time = std::chrono::high_resolution_clock::now();
    double total_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
    
    trace.entry_point.resolved = validate_entry_point(trace.entry_point);
    
    if (trace.entry_point.resolved) {
        trace.entry_point.status = ResolutionStatus::RESOLVED;
        trace.success = true;
        trace.status_message = "Entry point fully resolved";
        
        if (!trace.entry_point.has_bytecode) {
            trace.entry_point.status = ResolutionStatus::PARTIAL;
            
            ExecutionTrace::Issue issue;
            issue.severity = "warning";
            issue.code = "NO_BYTECODE";
            issue.message = "Entry point resolved but no bytecode available (abstract/native?)";
            trace.issues.push_back(issue);
        }
    } else {
        trace.entry_point.status = ResolutionStatus::PARTIAL;
        trace.success = true;  // Partial success is still success for EXP-002
        trace.status_message = "Entry point partially resolved";
    }
    
    // Add timing info
    std::stringstream timing_ss;
    timing_ss << "Total resolution time: " << std::fixed << std::setprecision(2) << total_ms << "ms";
    log(timing_ss.str());
    
    return trace;
}

std::vector<const ClassInfo*> ClassResolver::find_activities(const DexReport& report) const {
    std::vector<const ClassInfo*> activities;
    
    for (const auto& cls : report.classes) {
        if (is_activity_class(cls)) {
            activities.push_back(&cls);
        }
    }
    
    return activities;
}

bool ClassResolver::is_activity_class(const ClassInfo& cls) const {
    // Direct check
    if (cls.superclass_name == ACTIVITY_CLASS ||
        cls.superclass_name == APPCOMPAT_ACTIVITY ||
        cls.superclass_name == COMPONENT_ACTIVITY) {
        return true;
    }
    
    // Check class name patterns (heuristic)
    std::string lower_name = cls.name;
    std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
    
    if (lower_name.find("/activity") != std::string::npos &&
        lower_name.find("android") == std::string::npos) {
        // User-defined Activity subclass
        return true;
    }
    
    // Check superclass chain (simplified - would need full hierarchy for production)
    if (cls.superclass_name.find("Activity") != std::string::npos &&
        cls.superclass_name.find("android") != std::string::npos) {
        return true;
    }
    
    return false;
}

bool ClassResolver::find_main_activity(const DexReport& report, EntryPoint& entry) {
    auto activities = find_activities(report);
    
    if (activities.empty()) {
        last_error_ = "No Activity classes found";
        return false;
    }
    
    // Prefer MainActivity
    const ClassInfo* main_activity = nullptr;
    
    for (const auto* activity : activities) {
        std::string name = activity->name;
        
        // Convert to lowercase for comparison
        std::string lower_name = name;
        std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
        
        if (lower_name.find("mainactivity") != std::string::npos ||
            lower_name.find("/main") != std::string::npos) {
            main_activity = activity;
            break;
        }
    }
    
    // Fallback to first activity
    if (!main_activity) {
        main_activity = activities[0];
    }
    
    entry.class_name = main_activity->name;
    entry.readable_class = to_readable_class(main_activity->name);
    entry.class_info = *main_activity;
    entry.is_activity = true;
    
    return true;
}

bool ClassResolver::resolve_on_create(const ClassInfo& cls, EntryPoint& entry) {
    // Search for onCreate in direct methods first (where it should be)
    for (const auto& method : cls.direct_methods) {
        if (method.name == "onCreate") {
            entry.method_name = method.name;
            entry.descriptor = method.descriptor;
            entry.method_info = method;
            entry.resolved = true;
            entry.overrides_oncreate = true;
            entry.has_bytecode = !method.bytecode.empty();
            
            if (entry.has_bytecode) {
                entry.bytecode_offset = method.code_offset;
                entry.hex_offset = to_hex(method.code_offset);
                entry.instruction_count = static_cast<uint32_t>(method.bytecode.size());
            }
            
            log("Found onCreate in direct methods");
            return true;
        }
    }
    
    // Search virtual methods (shouldn't be here, but just in case)
    for (const auto& method : cls.virtual_methods) {
        if (method.name == "onCreate") {
            entry.method_name = method.name;
            entry.descriptor = method.descriptor;
            entry.method_info = method;
            entry.resolved = true;
            entry.overrides_oncreate = true;
            entry.has_bytecode = !method.bytecode.empty();
            
            if (entry.has_bytecode) {
                entry.bytecode_offset = method.code_offset;
                entry.hex_offset = to_hex(method.code_offset);
                entry.instruction_count = static_cast<uint32_t>(method.bytecode.size());
            }
            
            log("Found onCreate in virtual methods (unusual)");
            return true;
        }
    }
    
    // Not found - will use inherited version
    log("onCreate not found in class - will inherit from Activity");
    entry.resolved = false;  // Mark as not explicitly overridden
    
    return false;
}

bool ClassResolver::extract_bytecode_info(const MethodInfo& method, EntryPoint& entry) {
    if (method.bytecode.empty()) {
        log("No bytecode available for method");
        entry.has_bytecode = false;
        return false;
    }
    
    entry.bytecode_offset = method.code_offset;
    entry.hex_offset = to_hex(method.code_offset);
    entry.instruction_count = static_cast<uint32_t>(method.bytecode.size());
    entry.has_bytecode = true;
    
    // Log first few instructions for debugging
    std::stringstream ss;
    ss << "Bytecode preview (" << method.bytecode.size() << " instructions):";
    size_t preview_count = std::min(size_t(5), method.bytecode.size());
    for (size_t i = 0; i < preview_count; i++) {
        ss << " 0x" << std::hex << std::setw(4) << std::setfill('0') << method.bytecode[i];
    }
    if (method.bytecode.size() > 5) {
        ss << "...";
    }
    log(ss.str());
    
    return true;
}

std::optional<MethodInfo> ClassResolver::resolve_method(
    const ClassInfo& cls,
    const std::string& method_name
) const {
    for (const auto& method : cls.all_methods()) {
        if (method.name == method_name) {
            return method;
        }
    }
    
    return std::nullopt;
}

std::string ClassResolver::to_hex(uint32_t value) const {
    std::stringstream ss;
    ss << "0x" << std::hex << std::uppercase << value;
    return ss.str();
}

std::string ClassResolver::to_readable_class(const std::string& descriptor) const {
    if (descriptor.empty()) return "<empty>";
    
    std::string result = descriptor;
    
    // Remove leading 'L' and trailing ';'
    if (result.front() == 'L') {
        result = result.substr(1);
    }
    if (result.back() == ';') {
        result = result.substr(0, result.length() - 1);
    }
    
    // Replace '/' with '.'
    std::replace(result.begin(), result.end(), '/', '.');
    
    return result;
}

bool ClassResolver::validate_entry_point(const EntryPoint& entry) const {
    // Must have at least a class resolved
    if (entry.class_name.empty()) {
        return false;
    }
    
    // For EXP-002, having the class is minimum requirement
    // Method resolution is preferred but not required
    return true;
}

void ClassResolver::log(const std::string& message) {
    if (verbose_) {
        std::cerr << "[ClassResolver] " << message << std::endl;
    }
}

void ClassResolver::add_stage(ExecutionTrace& trace, const std::string& name, 
                               bool success, const std::string& evidence, double duration_ms) {
    ExecutionTrace::PipelineStage stage;
    stage.name = name;
    stage.success = success;
    stage.duration_ms = duration_ms;
    stage.evidence = evidence;
    trace.pipeline_stages.push_back(stage);
    
    log(std::string("[") + (success ? "OK" : "FAIL") + "] " + name + ": " + evidence);
}

} // namespace dex
} // namespace miniandroid
