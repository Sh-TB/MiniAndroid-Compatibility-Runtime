/*
 * MiniAndroid Runtime - Trace Exporter (EXP-031.5)
 * 
 * Mandatory trace file generation for real execution proof.
 * Golden Debug Protocol: Every execution must produce evidence.
 */

#ifndef MINIANDROID_TRACE_EXPORTER_H
#define MINIANDROID_TRACE_EXPORTER_H

#include "dalvik_engine.h"
#include <string>
#include <vector>
#include <fstream>
#include <memory>

namespace miniandroid {
namespace runtime {
    // Forward declaration for ExecutionSource (defined in execution_engine.h)
    // We use a local enum here to avoid circular dependency
    enum class TraceExecutionSource {
        HOST_SHORTCUT,
        REAL_DALVIK_INTERPRETER,
        UNKNOWN
    };
}

namespace dalvik {

// Use alias for convenience
using ExecutionSource = runtime::TraceExecutionSource;

/**
 * TraceExporter - Generates mandatory evidence files for EXP-031.5
 * 
 * Creates the following trace files in the specified output directory:
 * - opcode_trace.json     - Every instruction executed with PC, opcode, registers
 * - method_trace.json     - Method entry/exit with call stack
 * - register_trace.json   - Register state changes per instruction
 * - heap_trace.json       - Object allocations and GC events
 * - execution_summary.json - Overall execution statistics and verdict
 */
class TraceExporter {
public:
    /**
     * Export all traces from a DalvikExecutionResult
     * 
     * @param result The execution result to export
     * @param output_dir Directory to write trace files
     * @param apk_name Name of the APK being executed
     * @return true if all files written successfully
     */
    static bool export_all_traces(
        const DalvikExecutionResult& result,
        const std::string& output_dir,
        const std::string& apk_name
    );
    
    /**
     * Export opcode trace only
     */
    static bool export_opcode_trace(
        const DalvikExecutionResult& result,
        const std::string& output_dir
    );
    
    /**
     * Export method trace with call stack
     */
    static bool export_method_trace(
        const DalvikExecutionResult& result,
        const std::string& output_dir
    );
    
    /**
     * Export register state trace
     */
    static bool export_register_trace(
        const DalvikExecutionResult& result,
        const std::string& output_dir
    );
    
    /**
     * Export heap allocation trace
     */
    static bool export_heap_trace(
        const DalvikExecutionResult& result,
        const std::string& output_dir
    );
    
    /**
     * Export execution summary with success/failure verdict
     */
    static bool export_execution_summary(
        const DalvikExecutionResult& result,
        const std::string& output_dir,
        const std::string& apk_name
    );

private:
    // Helper to format PC address as hex
    static std::string format_pc(uint32_t pc);
    
    // Helper to convert ExecutionSource to string
    static std::string source_to_string(ExecutionSource source);
    
    // Helper to convert FinalStatus to string
    static std::string status_to_string(DalvikExecutionResult::FinalStatus status);
};

} // namespace dalvik
} // namespace miniandroid

#endif // MINIANDROID_TRACE_EXPORTER_H
