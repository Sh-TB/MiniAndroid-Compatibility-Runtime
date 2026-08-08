/*
 * MiniAndroid Runtime v0.1 - Class Resolver
 * EXP-002: HelloWorld Runtime Stub
 * 
 * Resolves entry points from parsed DEX data.
 * Locates Activity classes, finds onCreate(), extracts bytecode info.
 */

#ifndef MINIANDROID_CLASS_RESOLVER_H
#define MINIANDROID_CLASS_RESOLVER_H

#include "dex_parser.h"
#include <string>
#include <vector>
#include <optional>
#include <functional>

namespace miniandroid {
namespace dex {

// Resolution status
enum class ResolutionStatus {
    NOT_RESOLVED,
    RESOLVED,
    PARTIAL,        // Some parts resolved
    ERROR           // Resolution failed
};

// Entry point information
struct EntryPoint {
    std::string class_name;          // e.g., "Lcom/miniandroid/hello/MainActivity;"
    std::string readable_class;      // e.g., "com.miniandroid.hello.MainActivity"
    std::string method_name;         // e.g., "onCreate"
    std::string descriptor;          // e.g., "(Landroid/os/Bundle;)V"
    
    bool resolved = false;
    ResolutionStatus status = ResolutionStatus::NOT_RESOLVED;
    
    // Bytecode location
    uint32_t bytecode_offset = 0;    // Offset in DEX file
    std::string hex_offset;          // e.g., "0x12340"
    uint32_t instruction_count = 0;  // Number of instructions
    
    // Method details
    MethodInfo method_info;
    ClassInfo class_info;
    
    // Validation
    bool has_bytecode = false;
    bool is_activity = false;
    bool overrides_oncreate = false;
};

// Full execution trace for EXP-002
struct ExecutionTrace {
    // Metadata
    std::string experiment_id;       // "EXP-002"
    std::string timestamp;
    std::string apk_path;
    std::string dex_path;
    
    // Entry point
    EntryPoint entry_point;
    
    // Resolution pipeline stages (evidence of each step)
    struct PipelineStage {
        std::string name;
        bool success = false;
        double duration_ms = 0;
        std::string evidence;
        std::vector<std::string> artifacts;
    };
    
    std::vector<PipelineStage> pipeline_stages;
    
    // All discovered activities
    std::vector<std::string> activity_classes;
    
    // Method map for the entry class
    struct MethodMapEntry {
        std::string name;
        std::string descriptor;
        uint32_t offset;
        bool has_code;
        uint32_t insn_count;
    };
    std::vector<MethodMapEntry> method_map;
    
    // Warnings/issues
    struct Issue {
        std::string severity;       // "warning", "error", "info"
        std::string code;           // e.g., "MISSING_BYTECODE"
        std::string message;
    };
    std::vector<Issue> issues;
    
    // Final status
    bool success = false;
    std::string status_message;
};

/**
 * Class Resolver - Resolves Android entry points from DEX data
 * 
 * Pipeline:
 *   APK → classes.dex → class_defs → MainActivity → method_ids → onCreate()
 */
class ClassResolver {
public:
    ClassResolver();
    ~ClassResolver();
    
    /**
     * Resolve entry point from a parsed DEX report
     */
    ExecutionTrace resolve(const DexReport& report);
    
    /**
     * Resolve entry point with specific class/method hints
     */
    ExecutionTrace resolve_target(
        const DexReport& report,
        const std::string& target_class,     // e.g., "MainActivity" or full path
        const std::string& target_method = "onCreate"
    );
    
    /**
     * Find all Activity subclasses in DEX
     */
    std::vector<const ClassInfo*> find_activities(const DexReport& report) const;
    
    /**
     * Check if class extends android.app.Activity
     */
    bool is_activity_class(const ClassInfo& cls) const;
    
    /**
     * Resolve a specific method in a class
     */
    std::optional<MethodInfo> resolve_method(
        const ClassInfo& cls,
        const std::string& method_name
    ) const;
    
    /**
     * Get last error
     */
    std::string get_last_error() const { return last_error_; }
    
    /**
     * Set verbose logging
     */
    void set_verbose(bool verbose) { verbose_ = verbose; }
    
    // Activity hierarchy detection
    static constexpr const char* ACTIVITY_CLASS = "Landroid/app/Activity;";
    static constexpr const char* APPCOMPAT_ACTIVITY = "Landroidx/appcompat/app/AppCompatActivity;";
    static constexpr const char* COMPONENT_ACTIVITY = "Landroidx/activity/ComponentActivity;";

private:
    // Internal resolution methods
    bool find_main_activity(const DexReport& report, EntryPoint& entry);
    bool resolve_on_create(const ClassInfo& cls, EntryPoint& entry);
    bool extract_bytecode_info(const MethodInfo& method, EntryPoint& entry);
    
    // String formatting helpers
    std::string to_hex(uint32_t value) const;
    std::string to_readable_class(const std::string& descriptor) const;
    
    // Validation
    bool validate_entry_point(const EntryPoint& entry) const;
    
    // Logging
    void log(const std::string& message);
    void add_stage(ExecutionTrace& trace, const std::string& name, bool success, 
                   const std::string& evidence, double duration_ms);
    
    std::string last_error_;
    bool verbose_ = false;
};

} // namespace dex
} // namespace miniandroid

#endif // MINIANDROID_CLASS_RESOLVER_H
