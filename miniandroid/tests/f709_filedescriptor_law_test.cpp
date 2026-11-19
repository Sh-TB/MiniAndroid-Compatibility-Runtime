// f709_filedescriptor_law_test.cpp — F-NEW-709 regression fence.
//
// Root cause (farmerbb/Notepad v3.0.6 original APK, W11-APPS): the app's
// durability flush `stream.getFD().sync()` (Lv1/F;.j pc=191/196) hit a NULL
// FileDescriptor because FileOutputStream.getFD() fell through the S186I
// stub triage; the NPE chain unwound 4× to the top → no window content
// root → blank screen (trace: /tmp/f_notepad/launch, 2026-11-18).
//
// Laws pinned here (AOSP libcore OpenJDK semantics):
//   T1  getFD() on a FileOutputStream receiver materializes a NON-NULL
//       heap object of class Ljava/io/FileDescriptor; (never null).
//   T2  repeated getFD() on the same stream yields usable descriptors —
//       FileDescriptor.valid() answers true on both (single-materialization
//       reuse is enforced by the fd_to_stream_ map).
//   T3  FileDescriptor.sync() completes without throwing (fsync face →
//       host-stream flush) and the snippet falls through to the marker.
//   T4  FileDescriptor.valid() returns TRUE (boolean 1) for a live
//       descriptor.
//   T5  sync()/valid() on a NULL receiver IS an NPE (art law kept — the
//       fix must not mask genuine null descriptors).
//
// Harness pattern follows tests/semantic_pass3_bridge_test.cpp (S-61).
#include "../src/dex/dalvik_engine.h"

#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dalvik::DalvikValue;
using miniandroid::dalvik::DalvikType;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexMethodId;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

namespace opc {
constexpr uint16_t CONST              = 0x14;  // 31i
constexpr uint16_t MOVE_RESULT        = 0x0A;
constexpr uint16_t MOVE_RESULT_OBJECT = 0x0C;
constexpr uint16_t RETURN             = 0x0F;
constexpr uint16_t RETURN_OBJECT      = 0x11;
constexpr uint16_t NEW_INSTANCE       = 0x22;  // 21c
constexpr uint16_t INVOKE_VIRTUAL     = 0x6E;  // 35c
}

static int g_pass = 0, g_fail = 0;

static void record(const char* name, bool ok, const std::string& detail) {
    std::printf("%s %s %s\n", ok ? "PASS" : "FAIL", name, detail.c_str());
    ok ? ++g_pass : ++g_fail;
}

static uint16_t w11x(uint8_t reg, uint16_t op) {
    return static_cast<uint16_t>((reg << 8) | op);
}
static void emit_const(std::vector<uint16_t>& c, uint8_t reg, int32_t imm) {
    c.push_back(w11x(reg, opc::CONST));
    c.push_back(static_cast<uint16_t>(imm & 0xFFFF));
    c.push_back(static_cast<uint16_t>((imm >> 16) & 0xFFFF));
}
static void emit_21c(std::vector<uint16_t>& c, uint16_t op, uint8_t reg, uint16_t idx) {
    c.push_back(w11x(reg, op));
    c.push_back(idx);
}
static void emit_invoke(std::vector<uint16_t>& c, uint16_t op, uint8_t argc,
                        const std::vector<uint8_t>& regs, uint16_t method_idx) {
    uint16_t word0 = static_cast<uint16_t>((argc << 12) | op);
    uint16_t word2 = 0;
    for (int i = 0; i < 4 && i < static_cast<int>(regs.size()); ++i)
        word2 |= static_cast<uint16_t>(regs[static_cast<size_t>(i)] << (4 * i));
    c.push_back(word0);
    c.push_back(method_idx);
    c.push_back(word2);
}
static void emit_move_result(std::vector<uint16_t>& c, uint8_t reg, uint16_t op) {
    c.push_back(w11x(reg, op));
}

// ── try-table encoder (same as unified0113 / semantic_pass3) ──────────────
static void put_uleb(std::vector<uint8_t>& v, uint32_t val) {
    do { uint8_t b = val & 0x7F; val >>= 7; if (val) b |= 0x80; v.push_back(b); } while (val);
}
static void put_sleb(std::vector<uint8_t>& v, int32_t val) {
    bool more = true;
    while (more) {
        uint8_t b = val & 0x7F; val >>= 7;
        if ((val == 0 && !(b & 0x40)) || (val == -1 && (b & 0x40))) more = false;
        else b |= 0x80;
        v.push_back(b);
    }
}
static void append_try(std::vector<uint8_t>& tries_data, uint32_t start, uint16_t insn_count,
                       const std::vector<std::pair<uint32_t, uint32_t>>& typed,
                       int32_t catch_all_addr) {
    auto push_u16 = [&](uint16_t x) { tries_data.push_back(x & 0xFF); tries_data.push_back((x >> 8) & 0xFF); };
    auto push_u32 = [&](uint32_t x) { tries_data.push_back(x & 0xFF); tries_data.push_back((x >> 8) & 0xFF);
                                      tries_data.push_back((x >> 16) & 0xFF); tries_data.push_back((x >> 24) & 0xFF); };
    push_u32(start);
    push_u16(insn_count);
    push_u16(1);
    put_uleb(tries_data, 1);
    int32_t enc_size = catch_all_addr >= 0 ? -static_cast<int32_t>(typed.size()) - 1
                                           : static_cast<int32_t>(typed.size());
    put_sleb(tries_data, enc_size);
    for (const auto& [t_idx, t_addr] : typed) { put_uleb(tries_data, t_idx); put_uleb(tries_data, t_addr); }
}

struct MethodIds {
    std::vector<DexMethodId> ids;
    std::vector<std::string> types;
    std::vector<std::string> strings;
    uint16_t add(const std::string& class_desc, const std::string& name) {
        auto add_in = [](std::vector<std::string>& v, const std::string& s) {
            for (size_t i = 0; i < v.size(); ++i) if (v[i] == s) return static_cast<uint16_t>(i);
            v.push_back(s);
            return static_cast<uint16_t>(v.size() - 1);
        };
        uint16_t ci = add_in(types, class_desc);
        uint16_t ni = add_in(strings, name);
        ids.push_back(DexMethodId{ci, 0, ni});
        return static_cast<uint16_t>(ids.size() - 1);
    }
    uint16_t string_idx(const std::string& s) {
        for (size_t i = 0; i < strings.size(); ++i) if (strings[i] == s) return static_cast<uint16_t>(i);
        strings.push_back(s);
        return static_cast<uint16_t>(strings.size() - 1);
    }
    uint16_t type_idx(const std::string& t) {
        for (size_t i = 0; i < types.size(); ++i) if (types[i] == t) return static_cast<uint16_t>(i);
        types.push_back(t);
        return static_cast<uint16_t>(types.size() - 1);
    }
};

static const miniandroid::dalvik::InstructionTrace* find_return(const DalvikExecutionResult& r) {
    for (const auto& t : r.instruction_traces)
        if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) return &t;
    return nullptr;
}
static double as_double(const DalvikValue& v) {
    switch (v.type) {
        case DalvikType::INT32:   return static_cast<double>(v.int_val);
        case DalvikType::BOOLEAN: return (v.int_val != 0) ? 1.0 : 0.0;
        default:                  return 0;
    }
}

// Execute a snippet whose method_ids[] come from MethodIds.
static DalvikExecutionResult run_full(DalvikExecutionEngine& e,
                                      const std::vector<uint16_t>& code,
                                      const std::string& desc,
                                      const std::string& name,
                                      const MethodIds& mid,
                                      const std::vector<uint8_t>* tries_data) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = desc;
    mi.defining_class = "LF709Test;";
    mi.registers_size = 24;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;
    if (tries_data) { mi.tries_data = *tries_data; mi.tries_size = 1; }

    DexReport report;
    report.strings = mid.strings;
    report.types = mid.types;
    report.method_ids = mid.ids;
    report.types.push_back("LF709Test;");
    report.strings.push_back("LF709Test;");
    ClassInfo ci;
    ci.name = "LF709Test;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);
    return e.execute_method(ci.direct_methods[0], report, {}, false);
}

static bool expect_num(DalvikExecutionEngine& e, const char* name,
                       const std::vector<uint16_t>& code, const std::string& desc,
                       const MethodIds& mid, double expected) {
    DalvikExecutionResult r = run_full(e, code, desc, name, mid, nullptr);
    const auto* ret = find_return(r);
    if (!ret || !ret->return_value) {
        std::string last_op = r.instruction_traces.empty()
            ? "<none>" : r.instruction_traces.back().opcode_name;
        record(name, false, "no return trace/value (final_status=" +
               std::to_string(static_cast<int>(r.final_status)) + " last_op=" + last_op + ")");
        return false;
    }
    double got = as_double(*ret->return_value);
    record(name, got == expected,
           "expected " + std::to_string(expected) + ", got " + std::to_string(got));
    return got == expected;
}

// NEW_INSTANCE FileOutputStream → getFD() → RETURN_OBJECT
static DalvikExecutionResult run_getfd(DalvikExecutionEngine& e, const char* name,
                                       MethodIds& mid, uint16_t m_getfd, uint16_t t_fos) {
    std::vector<uint16_t> c;
    emit_21c(c, opc::NEW_INSTANCE, 1, t_fos);
    emit_invoke(c, opc::INVOKE_VIRTUAL, 1, {1}, m_getfd);
    emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
    c.push_back(w11x(0, opc::RETURN_OBJECT));
    return run_full(e, c, "()Ljava/lang/Object;", name, mid, nullptr);
}

int main(int argc, char** argv) {
    std::string only = (argc > 1) ? argv[1] : "";
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 2000;

    MethodIds mid;
    uint16_t m_getfd = mid.add("Ljava/io/FileOutputStream;", "getFD");
    uint16_t m_sync  = mid.add("Ljava/io/FileDescriptor;", "sync");
    uint16_t m_valid = mid.add("Ljava/io/FileDescriptor;", "valid");
    uint16_t t_fos   = mid.type_idx("Ljava/io/FileOutputStream;");

    // ── T1: getFD materializes a NON-NULL FileDescriptor heap object ──
    if (only.empty() || only == "t1") {
        DalvikExecutionResult r = run_getfd(engine, "t1_getfd_nonnull", mid, m_getfd, t_fos);
        const auto* ret = find_return(r);
        bool nonnull = ret && ret->return_value &&
                       ret->return_value->type == DalvikType::OBJECT_REF &&
                       ret->return_value->object_id != 0;
        bool law_class = false;
        if (nonnull) {
            const auto* ro = engine.get_heap().get(ret->return_value->object_id);
            law_class = ro && ro->class_descriptor == "Ljava/io/FileDescriptor;";
        }
        record("t1_getfd_nonnull", nonnull && law_class,
               std::string("nonnull=") + (nonnull ? "1" : "0") +
               " class=Ljava/io/FileDescriptor;=" + (law_class ? "1" : "0"));
    }

    // ── T2: repeated getFD + valid() on both descriptors ──────────────
    if (only.empty() || only == "t2") {
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 1, t_fos);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 1, {1}, m_getfd);      // fd#1 → v0
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 1, {1}, m_getfd);      // fd#2 → v2
        emit_move_result(c, 2, opc::MOVE_RESULT_OBJECT);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 1, {0}, m_valid);      // valid(fd#1)
        emit_move_result(c, 3, opc::MOVE_RESULT);
        c.push_back(w11x(3, opc::RETURN));
        expect_num(engine, "t2_repeat_getfd_valid", c, "()I", mid, 1.0);
    }

    // ── T3: sync() completes without throwing ──────────────────────────
    if (only.empty() || only == "t3") {
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 1, t_fos);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 1, {1}, m_getfd);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 1, {0}, m_sync);       // void
        emit_const(c, 0, 1);                                        // fall-through marker
        c.push_back(w11x(0, opc::RETURN));
        expect_num(engine, "t3_sync_no_throw", c, "()I", mid, 1.0);
    }

    // ── T4: valid() returns TRUE for a live descriptor ─────────────────
    if (only.empty() || only == "t4") {
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 1, t_fos);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 1, {1}, m_getfd);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 1, {0}, m_valid);
        emit_move_result(c, 0, opc::MOVE_RESULT);
        c.push_back(w11x(0, opc::RETURN));
        expect_num(engine, "t4_valid_true", c, "()I", mid, 1.0);
    }

    // ── T5: sync() on a NULL receiver IS an NPE (art law kept) ─────────
    if (only.empty() || only == "t5") {
        std::vector<uint16_t> c;   // v1 stays unset (null/uninit receiver)
        emit_invoke(c, opc::INVOKE_VIRTUAL, 1, {1}, m_sync);
        // caller fallthrough marker (should NOT be reached)
        emit_const(c, 0, 1);
        c.push_back(w11x(0, opc::RETURN));
        // handler: marker 7 → NPE reached the catch
        uint32_t hstart = static_cast<uint32_t>(c.size());
        std::vector<uint16_t> full = c;
        emit_const(full, 0, 7);
        full.push_back(w11x(0, opc::RETURN));
        std::vector<uint8_t> tries;
        uint16_t t_npe = mid.type_idx("Ljava/lang/NullPointerException;");
        append_try(tries, 0, static_cast<uint16_t>(hstart), {{t_npe, hstart}}, -1);
        DalvikExecutionResult r = run_full(engine, full, "()I", "t5_sync_null_npe", mid, &tries);
        const auto* ret = find_return(r);
        bool caught = ret && ret->return_value &&
                      static_cast<double>(ret->return_value->int_val) == 7.0;
        record("t5_sync_null_npe", caught,
               caught ? "NPE caught (marker 7)" : "expected NPE catch marker 7");
    }

    std::printf("\nRESULT: %d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
