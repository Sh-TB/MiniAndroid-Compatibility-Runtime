// UNIFIED_011.2 FNA-FIX — filled-new-array (0x24) semantic regression test
//
// Reproduces and validates the fix for the §24 audit finding:
//   PRIOR BUG: arg_count was read from bits 4-7 ((instr >> 4) & 0xF — the
//   high nibble of the OPCODE byte 0x24), yielding a constant 2 regardless
//   of the actual A field; the 5th register (G, bits 8-11) was never read.
//   The invoke family had this fixed in EXP-037 (BLOCKER-016) but
//   filled-new-array never received the same fix.
//
// Format 35c: A|G|op BBBB FEDC
//   code[pc+0] = A|G|op   A = arg count (bits 12-15), G = 5th reg (bits 8-11)
//   code[pc+1] = BBBB     type_idx
//   code[pc+2] = FEDC     register nibbles C,D,E,F
//
// This test builds synthetic method bytecode for arg counts 1..5 with
// distinct register values, executes it on the real interpreter, and
// verifies the produced heap array object (length + every element).
//
// Discrimination proof: under the old code every case except N=2 produced
// a wrong array (N=1 → length 2, N=3/4/5 → length 2 with wrong registers).

#include "../src/dex/dalvik_engine.h"

#include <cstdint>
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dalvik::DalvikValue;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

struct TestResult {
    std::string name;
    bool passed = false;
    std::string detail;
};

static std::vector<TestResult> g_results;

static void record(const std::string& name, bool passed, const std::string& detail = "") {
    g_results.push_back({name, passed, detail});
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
}

// const/4 vA, #+B  — format 11n: B|A|op  (word = (B<<12)|(A<<8)|0x12)
static uint16_t const4(uint8_t reg, int8_t lit) {
    return static_cast<uint16_t>((static_cast<uint16_t>(lit & 0xF) << 12) |
                                 (static_cast<uint16_t>(reg & 0xF) << 8) | 0x12);
}

// move-result-object vAA — format 11x: AA|op (word = (AA<<8)|0x0C)
static uint16_t move_result_object(uint8_t reg) {
    return static_cast<uint16_t>((static_cast<uint16_t>(reg) << 8) | 0x0C);
}

// return-object vAA — format 11x (word = (AA<<8)|0x11)
static uint16_t return_object(uint8_t reg) {
    return static_cast<uint16_t>((static_cast<uint16_t>(reg) << 8) | 0x11);
}

// filled-new-array {vC,vD,vE,vF,vG}, type@BBBB — format 35c
//   word0 = (A<<12)|(G<<8)|0x24, word1 = type_idx, word2 = C|D<<4|E<<8|F<<12
static void filled_new_array(std::vector<uint16_t>& code, const std::vector<uint8_t>& regs,
                             uint16_t type_idx) {
    uint8_t A = static_cast<uint8_t>(regs.size());
    uint8_t G = (A == 5) ? regs[4] : 0;
    uint16_t word0 = static_cast<uint16_t>((A << 12) | (G << 8) | 0x24);
    uint16_t word2 = static_cast<uint16_t>(
        (regs.size() > 0 ? (regs[0] & 0xF) : 0) |
        (regs.size() > 1 ? ((regs[1] & 0xF) << 4) : 0) |
        (regs.size() > 2 ? ((regs[2] & 0xF) << 8) : 0) |
        (regs.size() > 3 ? ((regs[3] & 0xF) << 12) : 0));
    code.push_back(word0);
    code.push_back(type_idx);
    code.push_back(word2);
}

// Execute filled-new-array with `count` distinct register values; verify the
// resulting heap array object: __array_length__ == count and array[i] == i+1.
static bool run_case(DalvikExecutionEngine& engine, int count, std::string* detail_out) {
    const uint8_t result_reg = 6;  // keep result away from element registers v0..v4

    std::vector<uint16_t> code;
    std::vector<uint8_t> element_regs;
    for (int i = 0; i < count; i++) {
        code.push_back(const4(static_cast<uint8_t>(i), static_cast<int8_t>(i + 1)));
        element_regs.push_back(static_cast<uint8_t>(i));
    }
    filled_new_array(code, element_regs, 0 /*type_idx — no per-DEX resolution in unit test*/);
    code.push_back(move_result_object(result_reg));
    code.push_back(return_object(result_reg));

    MethodInfo mi;
    mi.name = "fna_case";
    mi.descriptor = "()[Ljava/lang/Object;";
    mi.defining_class = "LFnaTest;";
    mi.registers_size = 16;
    mi.ins_size = 0;
    mi.outs_size = 1;
    mi.bytecode = code;

    DexReport report;
    report.strings.push_back("fna_case");
    report.types.push_back("LFnaTest;");
    ClassInfo ci;
    ci.name = "LFnaTest;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);

    DalvikExecutionResult result = engine.execute_method(ci.direct_methods[0], report, {}, false);

    // Locate the array object in the heap: the FNA handler sets
    // __array_length__ on the allocated object.
    const auto& heap = engine.get_heap();
    const miniandroid::dalvik::HeapObject* array_obj = nullptr;
    for (uint32_t id : heap.get_all_ids()) {
        const auto* obj = heap.get(id);
        if (obj && obj->fields.count("__array_length__")) {
            // keep the LAST allocated (highest id) in case earlier objects exist
            if (!array_obj || obj->object_id > array_obj->object_id) array_obj = obj;
        }
    }
    if (!array_obj) {
        *detail_out = "no __array_length__ object in heap (instructions_executed=" +
                      std::to_string(result.total_instructions_executed) + ")";
        return false;
    }

    // Length check
    int32_t len = array_obj->fields.at("__array_length__").int_val;
    if (len != count) {
        *detail_out = "length mismatch: expected " + std::to_string(count) + " got " +
                      std::to_string(len);
        return false;
    }

    // Element checks — array[i] must equal the value of register i (i+1)
    for (int i = 0; i < count; i++) {
        std::string fname = "array[" + std::to_string(i) + "]";
        auto it = array_obj->fields.find(fname);
        if (it == array_obj->fields.end()) {
            *detail_out = "missing field " + fname;
            return false;
        }
        int32_t got = it->second.int_val;
        if (got != i + 1) {
            *detail_out = fname + " value mismatch: expected " + std::to_string(i + 1) +
                          " got " + std::to_string(got);
            return false;
        }
    }
    *detail_out = "length=" + std::to_string(len) + " elements=0.." +
                  std::to_string(count - 1) + " all correct";
    return true;
}

int main() {
    std::cout << "=== UNIFIED_011.2 filled-new-array (0x24) semantic test ===\n";
    DalvikExecutionEngine engine;
    engine.config_.generate_trace = false;

    for (int count = 1; count <= 5; count++) {
        std::string detail;
        bool ok = run_case(engine, count, &detail);
        record("filled_new_array_" + std::to_string(count) + "_args", ok, detail);
    }

    int passed = 0, failed = 0;
    for (const auto& r : g_results) (r.passed ? passed : failed)++;
    std::cout << "\nRESULT: " << passed << " passed, " << failed << " failed\n";
    return failed == 0 ? 0 : 1;
}
