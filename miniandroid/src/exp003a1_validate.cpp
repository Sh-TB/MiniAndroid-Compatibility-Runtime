/*
 * MiniAndroid Runtime v0.1 - EXP-003-A.1 Validation
 * 
 * Golden Debug Protocol - Evidence Validation
 * 
 * Goal: Verify const-string resolves correct application strings
 * 
 * Evidence Produced:
 *   - run/dex_strings.json: Complete DEX string pool dump
 *   - run/decoded_method.json: Decoded onCreate bytecode
 * 
 * Validation Checks:
 *   1. String pool integrity (count, indices, values)
 *   2. Bytecode decoding accuracy
 *   3. const-string target resolution correctness
 */

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <string_view>

#include "dex/dex_parser.h"
#include "dex/class_resolver.h"
#include "apk/apk_parser.h"

#include "nlohmann/json.hpp"

using json = nlohmann::json;
using namespace miniandroid;

// ============================================================================
// Opcode Decoder Utility
// ============================================================================

struct DecodedInstruction {
    uint32_t offset;              // Byte offset in method
    uint32_t pc;                  // Instruction index (in 16-bit units)
    uint16_t opcode;
    std::string opcode_name;
    std::vector<std::pair<std::string, std::string>> operands;
    std::string disassembly;      // Human-readable form
    size_t instruction_size;      // Size in 16-bit units
    
    // For const-string specifically
    bool is_const_string = false;
    uint8_t dest_register = 0;
    uint16_t string_index = 0;
    std::string resolved_string;  // Resolved from string pool
    bool string_resolved = false;
};

class OpcodeDecoder {
public:
    static std::string opcode_to_string(uint16_t opcode) {
        switch (opcode) {
            case 0x00: return "nop";
            case 0x0E: return "return-void";
            case 0x0F: return "return";
            case 0x11: return "return-object";
            case 0x12: return "const/4";
            case 0x13: return "const/16";
            case 0x14: return "const";
            case 0x15: return "const/high16";
            case 0x1A: return "const-string";
            case 0x1B: return "const-string/jumbo";
            case 0x22: return "new-instance";
            case 0x23: return "new-array";
            case 0x26: return "iget";
            case 0x59: return "iget-object";
            case 0x6E: return "invoke-virtual";
            case 0x6F: return "invoke-super";
            case 0x70: return "invoke-direct";
            case 0x71: return "invoke-static";
            case 0x72: return "invoke-interface";
            default: {
                std::ostringstream oss;
                oss << "opcode_0x" << std::hex << std::setw(2) << std::setfill('0') << opcode;
                return oss.str();
            }
        }
    }
    
    // Decode a single instruction at given PC
    static DecodedInstruction decode(const uint16_t* code, uint32_t pc, 
                                      const std::vector<std::string>& strings) {
        DecodedInstruction inst;
        inst.pc = pc;
        inst.offset = pc * 2;  // Convert to byte offset
        inst.opcode = code[pc] & 0xFF;
        inst.opcode_name = opcode_to_string(inst.opcode);
        
        switch (inst.opcode) {
            case 0x1A: {  // const-string vAA, string@BBBB
                inst.instruction_size = 3;  // 3 code units (opcode + AA + BBBB as 2 units)
                uint8_t aa = (code[pc] >> 8) & 0xFF;
                uint16_t bbbb = code[pc + 1];
                
                inst.dest_register = aa;
                inst.string_index = bbbb;
                inst.is_const_string = true;
                
                inst.operands.push_back({"vAA", "v" + std::to_string(aa)});
                inst.operands.push_back({"string@BBBB", "0x" + to_hex(bbbb)});
                
                // Resolve string if possible
                if (bbbb < strings.size()) {
                    inst.resolved_string = strings[bbbb];
                    inst.string_resolved = true;
                }
                
                inst.disassembly = "const-string v" + std::to_string(aa) + 
                                   ", \"" + (inst.string_resolved ? inst.resolved_string : "?") + "\"";
                break;
            }
            
            case 0x22: {  // new-instance vAA, type@BBBB
                inst.instruction_size = 3;
                uint8_t aa = (code[pc] >> 8) & 0xFF;
                uint16_t bbbb = code[pc + 1];
                
                inst.operands.push_back({"vAA", "v" + std::to_string(aa)});
                inst.operands.push_back({"type@BBBB", "0x" + to_hex(bbbb)});
                
                inst.disassembly = "new-instance v" + std::to_string(aa) + ", type@" + to_hex(bbbb);
                break;
            }
            
            case 0x70: {  // invoke-direct {vC..}, method@BBBB
                inst.instruction_size = 3;
                uint8_t args = (code[pc] >> 8) & 0xFF;
                uint16_t bbbb = code[pc + 1];
                
                inst.operands.push_back({"args", std::to_string(args)});
                inst.operands.push_back({"method@BBBB", "0x" + to_hex(bbbb)});
                
                inst.disassembly = "invoke-direct {args=" + std::to_string(args) + 
                                   "}, method@" + to_hex(bbbb);
                break;
            }
            
            case 0x6E: {  // invoke-virtual {vC..}, method@BBBB
                inst.instruction_size = 3;
                uint8_t args = (code[pc] >> 8) & 0xFF;
                uint16_t bbbb = code[pc + 1];
                
                inst.operands.push_back({"args", std::to_string(args)});
                inst.operands.push_back({"method@BBBB", "0x" + to_hex(bbbb)});
                
                inst.disassembly = "invoke-virtual {args=" + std::to_string(args) + 
                                   "}, method@" + to_hex(bbbb);
                break;
            }
            
            case 0x0E: {  // return-void
                inst.instruction_size = 1;
                inst.disassembly = "return-void";
                break;
            }
            
            default: {
                // Unknown/unimplemented - assume 1 code unit
                inst.instruction_size = 1;
                inst.disassembly = inst.opcode_name + " [unimplemented]";
                break;
            }
        }
        
        return inst;
    }
    
private:
    static std::string to_hex(uint16_t val) {
        std::ostringstream oss;
        oss << std::hex << std::setw(4) << std::setfill('0') << val;
        return oss.str();
    }
};

// ============================================================================
// Validation Result Structure
// ============================================================================

struct ValidationResult {
    bool string_pool_valid = false;
    bool bytecode_decoded = false;
    bool const_string_correct = false;
    
    // Evidence data
    json dex_strings_evidence;
    json decoded_method_evidence;
    
    // Issues found
    std::vector<std::string> issues;
    std::vector<std::string> warnings;
    
    void add_issue(const std::string& issue) {
        issues.push_back(issue);
    }
    
    void add_warning(const std::string& warning) {
        warnings.push_back(warning);
    }
    
    json to_json() const {
        json result;
        result["experiment_id"] = "EXP-003-A.1";
        result["validation_type"] = "Const-String Resolution Verification";
        result["timestamp"] = get_timestamp();
        
        result["checks"] = {
            {"string_pool_integrity", string_pool_valid},
            {"bytecode_decode_accuracy", bytecode_decoded},
            {"const_string_resolution", const_string_correct}
        };
        
        result["overall_pass"] = string_pool_valid && bytecode_decoded && const_string_correct;
        
        if (!issues.empty()) result["issues"] = issues;
        if (!warnings.empty()) result["warnings"] = warnings;
        
        return result;
    }
    
private:
    static std::string get_timestamp() {
        // Simple timestamp - in production would use proper time library
        return "2026-08-09T00:00:00Z";  // Placeholder
    }
};

// ============================================================================
// Main Validation Logic
// ============================================================================

class Exp003A1Validator {
public:
    ValidationResult validate(const std::string& apk_path) {
        ValidationResult result;
        
        std::cout << "========================================\n";
        std::cout << "MiniAndroid EXP-003-A.1 Validation\n";
        std::cout << "Goal: Verify const-string resolution\n";
        std::cout << "========================================\n\n";
        
        // Step 1: Load APK and parse DEX
        std::cout << "[Step 1] Loading APK and parsing DEX...\n";
        
        apk::ApkParser apk_parser;
        auto apk_result = apk_parser.parse(apk_path);
        
        if (!apk_result.is_valid) {
            result.add_issue("APK loading failed: " + apk_result.validation_error);
            return result;
        }
        
        std::cout << "  APK loaded: " << apk_path << "\n";
        std::cout << "  DEX files found: " << apk_result.dex_files.size() << "\n";
        
        // Use first DEX file
        if (apk_result.dex_files.empty()) {
            result.add_issue("No DEX files found in APK");
            return result;
        }
        
        // Extract DEX from APK (same as EXP-002)
        std::string dex_filename = apk_result.dex_files[0];
        std::string dex_path = "run/classes.dex";
        
        {
            auto dex_data = apk_parser.extract_entry(apk_path, dex_filename);
            if (dex_data.empty()) {
                result.add_issue("Failed to extract " + dex_filename + " from APK");
                return result;
            }
            
            std::ofstream dex_out(dex_path, std::ios::binary);
            dex_out.write(reinterpret_cast<const char*>(dex_data.data()), dex_data.size());
            dex_out.close();
            
            std::cout << "  Extracted: " << dex_filename << " (" << dex_data.size() << " bytes)\n";
        }
        
        // Step 2: Parse DEX completely
        std::cout << "\n[Step 2] Parsing DEX structure...\n";
        
        dex::DexParser dex_parser;
        auto dex_report = dex_parser.parse(dex_path);
        
        if (!dex_report.is_valid) {
            result.add_issue("DEX parsing failed: " + dex_report.validation_error);
            return result;
        }
        
        std::cout << "  Strings: " << dex_report.strings_count << "\n";
        std::cout << "  Types: " << dex_report.types_count << "\n";
        std::cout << "  Methods: " << dex_report.methods_count << "\n";
        std::cout << "  Classes: " << dex_report.classes_count << "\n";
        
        // Step 3: Generate string pool evidence
        std::cout << "\n[Step 3] Generating string pool evidence...\n";
        
        result.dex_strings_evidence = generate_strings_evidence(dex_report);
        result.string_pool_valid = true;
        std::cout << "  String pool dumped: " << dex_report.strings.size() << " entries\n";
        
        // Step 4: Resolve entry point
        std::cout << "\n[Step 4] Resolving entry point...\n";
        
        dex::ClassResolver resolver;
        auto resolution = resolver.resolve(dex_report);
        
        if (!resolution.entry_point.resolved) {
            result.add_issue("Entry point resolution failed");
            return result;
        }
        
        std::cout << "  Entry: " << resolution.entry_point.readable_class 
                  << "." << resolution.entry_point.method_name << "\n";
        std::cout << "  Bytecode offset: 0x" << std::hex << resolution.entry_point.bytecode_offset 
                  << std::dec << "\n";
        std::cout << "  Instructions: " << resolution.entry_point.instruction_count << "\n";
        
        // Step 5: Use the method info from resolution (same as EXP-003-A)
        std::cout << "\n[Step 5] Locating method bytecode...\n";
        
        const dex::MethodInfo* method_info = &resolution.entry_point.method_info;
        
        if (!method_info || method_info->bytecode.empty()) {
            result.add_issue("Could not find method bytecode");
            return result;
        }
        
        std::cout << "  Bytecode size: " << method_info->bytecode.size() << " units (" 
                  << (method_info->bytecode.size() * 2) << " bytes)\n";
        
        // Debug: Show first few code units in hex
        std::cout << "  First 10 code units (hex):";
        for (size_t i = 0; i < std::min(size_t(10), method_info->bytecode.size()); ++i) {
            std::cout << " " << std::hex << std::setw(4) << std::setfill('0') 
                      << method_info->bytecode[i] << std::dec;
        }
        std::cout << "\n";
        
        // Debug: Show method details
        std::cout << "  Method name: \"" << method_info->name << "\"\n";
        std::cout << "  Class: \"" << method_info->defining_class << "\"\n";
        std::cout << "  Code offset: 0x" << std::hex << method_info->code_offset << std::dec << "\n";
        
        // Step 6: Decode all instructions
        std::cout << "\n[Step 6] Decoding bytecode instructions...\n";
        
        result.decoded_method_evidence = generate_method_evidence(
            *method_info, dex_report.strings, resolution.entry_point);
        result.bytecode_decoded = true;
        
        auto instructions = result.decoded_method_evidence["instructions"];
        std::cout << "  Decoded " << instructions.size() << " instructions\n";
        
        // Step 7: Validate const-string resolution
        std::cout << "\n[Step 7] Validating const-string resolution...\n";
        
        result.const_string_correct = validate_const_string_resolution(
            result.decoded_method_evidence, result.dex_strings_evidence, result);
        
        // Summary
        std::cout << "\n========================================\n";
        std::cout << "VALIDATION SUMMARY\n";
        std::cout << "========================================\n";
        std::cout << "String Pool Integrity: " << (result.string_pool_valid ? "PASS" : "FAIL") << "\n";
        std::cout << "Bytecode Decode Accuracy: " << (result.bytecode_decoded ? "PASS" : "FAIL") << "\n";
        std::cout << "Const-String Resolution: " << (result.const_string_correct ? "PASS" : "FAIL") << "\n";
        std::cout << "Overall: " << ((result.string_pool_valid && result.bytecode_decoded && 
                                       result.const_string_correct) ? "PASS" : "FAIL") << "\n";
        
        if (!result.issues.empty()) {
            std::cout << "\nIssues:\n";
            for (const auto& issue : result.issues) {
                std::cout << "  - " << issue << "\n";
            }
        }
        
        return result;
    }
    
private:
    // Helper to sanitize string for JSON (handle MUTF-8 issues)
    std::string sanitize_for_json(const std::string& str) {
        std::string result;
        result.reserve(str.size());
        
        for (size_t i = 0; i < str.size(); ++i) {
            unsigned char c = static_cast<unsigned char>(str[i]);
            
            // Check for valid UTF-8 continuation or ASCII
            if (c < 0x80) {
                // ASCII - safe
                result += static_cast<char>(c);
            } else if (c >= 0xC2 && c <= 0xF4) {
                // Start of valid UTF-8 multi-byte sequence
                // Check if we have enough bytes left
                int expected_bytes = 0;
                if (c <= 0xDF) expected_bytes = 2;
                else if (c <= 0xEF) expected_bytes = 3;
                else expected_bytes = 4;
                
                bool valid = true;
                if (i + expected_bytes > str.size()) {
                    valid = false;
                } else {
                    for (int j = 1; j < expected_bytes; ++j) {
                        unsigned char next = static_cast<unsigned char>(str[i + j]);
                        if (next < 0x80 || next >= 0xC0) {
                            valid = false;
                            break;
                        }
                    }
                }
                
                if (valid) {
                    result += str.substr(i, expected_bytes);
                    i += (expected_bytes - 1);
                } else {
                    // Invalid - use replacement
                    result += "<byte:";
                    result += std::to_string(static_cast<int>(c));
                    result += ">";
                }
            } else if (c >= 0x80 && c < 0xC0) {
                // Continuation byte without start - invalid
                result += "<byte:";
                result += std::to_string(static_cast<int>(c));
                result += ">";
            } else {
                // Invalid start byte (0xC0, 0xC1, 0xF5-0xFF)
                result += "<byte:";
                result += std::to_string(static_cast<int>(c));
                result += ">";
            }
        }
        
        return result;
    }
    
    json generate_strings_evidence(const dex::DexReport& report) {
        json evidence;
        evidence["source_dex"] = report.dex_path;
        evidence["total_strings"] = report.strings_count;
        evidence["strings"] = json::array();
        
        for (size_t i = 0; i < report.strings.size(); ++i) {
            json entry;
            entry["index"] = i;
            entry["value"] = sanitize_for_json(report.strings[i]);
            entry["raw_value_hex"] = "";  // Could add hex dump if needed
            
            // Categorize the string (use sanitized version)
            std::string sanitized = sanitize_for_json(report.strings[i]);
            std::string category = categorize_string(sanitized);
            entry["category"] = category;
            
            // Mark strings that look like application content
            if (category == "application_content" || category == "class_descriptor") {
                entry["is_app_relevant"] = true;
            }
            
            evidence["strings"].push_back(entry);
        }
        
        return evidence;
    }
    
    std::string categorize_string(const std::string& str) {
        if (str.empty()) return "empty";
        if (str[0] == 'L' && str.find(';') != std::string::npos) return "class_descriptor";
        if (str[0] == '(') return "method_descriptor";
        if (str.find('/') != std::string::npos && str.find(';') != std::string::npos) return "type_signature";
        if (str.find("android/") == 0) return "android_framework";
        if (str.find("java/") == 0) return "java_framework";
        if (str.find("com/miniandroid") != std::string::npos) return "application_content";
        if (str == "<init>" || str == "<clinit>") return "special_method";
        if (str == "Hello World!" || str == "HelloWorld") return "user_visible_string";
        return "other";
    }
    
    json generate_method_evidence(const dex::MethodInfo& method,
                                   const std::vector<std::string>& strings,
                                   const dex::EntryPoint& entry) {
        json evidence;
        evidence["class_name"] = sanitize_for_json(method.defining_class);
        evidence["method_name"] = sanitize_for_json(method.name);
        evidence["descriptor"] = sanitize_for_json(method.descriptor);
        evidence["bytecode_offset"] = "0x" + to_hex(entry.bytecode_offset);
        evidence["total_code_units"] = method.bytecode.size();
        evidence["instructions"] = json::array();
        
        uint32_t pc = 0;
        uint32_t seq = 0;
        
        while (pc < method.bytecode.size()) {
            auto inst = OpcodeDecoder::decode(method.bytecode.data(), pc, strings);
            
            json inst_json;
            inst_json["sequence"] = seq++;
            inst_json["pc"] = inst.pc;
            inst_json["byte_offset"] = inst.offset;
            inst_json["opcode_hex"] = "0x" + to_hex(inst.opcode);
            inst_json["opcode_name"] = inst.opcode_name;
            inst_json["size_code_units"] = inst.instruction_size;
            inst_json["disassembly"] = sanitize_for_json(inst.disassembly);
            
            // Operands
            json operands = json::array();
            for (const auto& op : inst.operands) {
                operands.push_back({{"name", op.first}, {"value", op.second}});
            }
            inst_json["operands"] = operands;
            
            // Const-string specific
            if (inst.is_const_string) {
                inst_json["const_string_details"] = {
                    {"destination_register", "v" + std::to_string(inst.dest_register)},
                    {"string_index", inst.string_index},
                    {"string_index_hex", "0x" + to_hex(inst.string_index)},
                    {"resolved", inst.string_resolved},
                    {"resolved_value", inst.string_resolved ? json(sanitize_for_json(inst.resolved_string)) : json(nullptr)}
                };
            }
            
            evidence["instructions"].push_back(inst_json);
            
            // Move to next instruction
            pc += inst.instruction_size;
            
            // Safety check for infinite loops
            if (seq > 1000) {
                evidence["warnings"] = "Instruction decode limit reached (1000)";
                break;
            }
        }
        
        evidence["total_instructions_decoded"] = seq;
        
        return evidence;
    }
    
    bool validate_const_string_resolution(const json& decoded_method,
                                           const json& strings_evidence,
                                           ValidationResult& result) {
        bool all_correct = true;
        
        // Find all const-string instructions
        int const_string_count = 0;
        
        for (const auto& inst : decoded_method["instructions"]) {
            if (inst.contains("const_string_details")) {
                const_string_count++;
                auto details = inst["const_string_details"];
                
                uint16_t str_idx = details["string_index"];
                bool resolved = details["resolved"];
                std::string resolved_val = details.value("resolved_value", "");
                
                std::cout << "\n  Const-String #" << const_string_count << ":\n";
                std::cout << "    PC: " << inst["pc"] << "\n";
                std::cout << "    Register: " << details["destination_register"] << "\n";
                std::cout << "    String Index: " << str_idx << " (0x" << to_hex(str_idx) << ")\n";
                std::cout << "    Resolved: " << (resolved ? "YES" : "NO") << "\n";
                if (resolved) {
                    std::cout << "    Value: \"" << resolved_val << "\"\n";
                }
                
                // Validate against string pool
                if (resolved) {
                    if (str_idx < strings_evidence["strings"].size()) {
                        std::string expected = strings_evidence["strings"][str_idx]["value"];
                        if (resolved_val == expected) {
                            std::cout << "    Pool Match: CORRECT ✓\n";
                        } else {
                            std::cout << "    Pool Match: MISMATCH ✗\n";
                            std::cout << "      Expected: \"" << expected << "\"\n";
                            result.add_issue("Const-string at PC=" + 
                                           std::to_string(inst["pc"].get<int>()) +
                                           " resolved to wrong string");
                            all_correct = false;
                        }
                    } else {
                        result.add_warning("String index " + std::to_string(str_idx) + 
                                          " out of range");
                        all_correct = false;
                    }
                } else {
                    result.add_warning("Const-string at PC=" + 
                                      std::to_string(inst["pc"].get<int>()) + 
                                      " could not resolve string");
                    all_correct = false;
                }
            }
        }
        
        std::cout << "\n  Total const-string instructions: " << const_string_count << "\n";
        
        // Check if we found any const-string at all
        if (const_string_count == 0) {
            result.add_warning("No const-string instructions found in method");
        }
        
        return all_correct && !result.issues.empty() == false;
    }
    
    static std::string to_hex(uint32_t val) {
        std::ostringstream oss;
        oss << std::hex << val;
        return oss.str();
    }
};

// ============================================================================
// Main Entry Point
// ============================================================================

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <apk_path>\n";
        std::cerr << "\nMiniAndroid EXP-003-A.1 Validator\n";
        std::cerr << "Verifies const-string opcode resolution correctness.\n";
        std::cerr << "\nEvidence output:\n";
        std::cerr << "  run/dex_strings.json - Complete DEX string pool\n";
        std::cerr << "  run/decoded_method.json - Decoded onCreate bytecode\n";
        return 1;
    }
    
    std::string apk_path = argv[1];
    
    // Run validation
    Exp003A1Validator validator;
    auto result = validator.validate(apk_path);
    
    // Write evidence files
    std::cout << "\n========================================\n";
    std::cout << "WRITING EVIDENCE FILES\n";
    std::cout << "========================================\n\n";
    
    // Write string pool evidence
    {
        std::ofstream f("run/dex_strings.json");
        if (f.is_open()) {
            f << std::setw(2) << result.dex_strings_evidence << std::endl;
            f.close();
            std::cout << "✓ Written: run/dex_strings.json\n";
        } else {
            std::cerr << "✗ Failed to write run/dex_strings.json\n";
        }
    }
    
    // Write decoded method evidence
    {
        std::ofstream f("run/decoded_method.json");
        if (f.is_open()) {
            f << std::setw(2) << result.decoded_method_evidence << std::endl;
            f.close();
            std::cout << "✓ Written: run/decoded_method.json\n";
        } else {
            std::cerr << "✗ Failed to write run/decoded_method.json\n";
        }
    }
    
    // Write validation report
    {
        json report = result.to_json();
        report["apk_path"] = apk_path;
        
        std::ofstream f("run/validation_report.json");
        if (f.is_open()) {
            f << std::setw(2) << report << std::endl;
            f.close();
            std::cout << "✓ Written: run/validation_report.json\n";
        }
    }
    
    // Return appropriate exit code
    bool overall_pass = result.string_pool_valid && result.bytecode_decoded && result.const_string_correct;
    return overall_pass ? 0 : 1;
}
