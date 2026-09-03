// FINAL CANONICAL MASTER RECONCILIATION — Pass-3 differential fixture.
//
// Covers the runtime areas the master audit requires that NO earlier fixture
// discriminated: XmlPullParser real event progression + termination,
// AtomicReference CAS (identity + null), InputStream.read() REAL asset bytes,
// the full conversion matrix (incl. NaN/±Inf/truncation), div/rem lit16 +
// 2addr zero-divisor exceptions, backward-target switch dispatch, and the
// parse/string edge matrix (Java boundaries, exceptions, strictness).
//
// Harness pattern follows tests/semantic_switch_parse_neg_test.cpp.
// Every case is chosen so a stub / tag-only / happy-path-only implementation
// produces a DIFFERENT observable result.

#include "../src/dex/dalvik_engine.h"

#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dalvik::InstructionTrace;
using miniandroid::dalvik::DalvikValue;
using miniandroid::dalvik::DalvikType;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexMethodId;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

namespace opc {
constexpr uint16_t CONST          = 0x14;  // 31i
constexpr uint16_t CONST_WIDE     = 0x18;  // 51l
constexpr uint16_t CONST_STRING   = 0x1A;  // 21c
constexpr uint16_t CONST_4        = 0x12;  // 11n
constexpr uint16_t MOVE_RESULT        = 0x0A;
constexpr uint16_t MOVE_RESULT_WIDE   = 0x0B;
constexpr uint16_t MOVE_RESULT_OBJECT = 0x0C;
constexpr uint16_t RETURN         = 0x0F;
constexpr uint16_t RETURN_WIDE    = 0x10;
constexpr uint16_t RETURN_OBJECT  = 0x11;
constexpr uint16_t PACKED_SWITCH  = 0x2B;  // 31t
constexpr uint16_t SPARSE_SWITCH  = 0x2C;  // 31t
constexpr uint16_t NEW_INSTANCE   = 0x22;  // 21c
constexpr uint16_t NEW_ARRAY      = 0x23;  // 22c
constexpr uint16_t AGET_BYTE      = 0x48;  // 23x
constexpr uint16_t INVOKE_STATIC  = 0x71;  // 35c
constexpr uint16_t INVOKE_VIRTUAL = 0x6E;  // 35c
constexpr uint16_t INVOKE_DIRECT  = 0x70;  // 35c
constexpr uint16_t ADD_INT        = 0x90;  // 23x
constexpr uint16_t SUB_INT        = 0x91;  // 23x
constexpr uint16_t MUL_INT        = 0x92;  // 23x
constexpr uint16_t ADD_INT_2ADDR  = 0xB0;  // 12x
constexpr uint16_t DIV_INT_2ADDR  = 0xB3;  // 12x
constexpr uint16_t MUL_INT_LIT8   = 0xDA;  // 22b (AOSP)
constexpr uint16_t DIV_INT        = 0x93;  // 23x
constexpr uint16_t REM_INT        = 0x94;  // 23x
constexpr uint16_t DIV_INT_LIT16  = 0xD3;  // 22s (AOSP)
constexpr uint16_t REM_INT_LIT16  = 0xD4;  // 22s (AOSP)
constexpr uint16_t DIV_LONG       = 0x9E;  // 23x
constexpr uint16_t REM_LONG       = 0x9F;  // 23x
// PASS-3: constants corrected to the TRUE AOSP values (the first draft of
// this fixture had shifted values — proof that independent reference tables
// must be used, never memory).
constexpr uint16_t INT_TO_LONG    = 0x81;  // 12x
constexpr uint16_t INT_TO_FLOAT   = 0x82;  // 12x
constexpr uint16_t INT_TO_DOUBLE  = 0x83;  // 12x
constexpr uint16_t LONG_TO_INT    = 0x84;  // 12x
constexpr uint16_t LONG_TO_FLOAT  = 0x85;  // 12x
constexpr uint16_t LONG_TO_DOUBLE = 0x86;  // 12x
constexpr uint16_t FLOAT_TO_INT   = 0x87;  // 12x
constexpr uint16_t FLOAT_TO_LONG  = 0x88;  // 12x
constexpr uint16_t FLOAT_TO_DOUBLE= 0x89;  // 12x
constexpr uint16_t DOUBLE_TO_INT  = 0x8A;  // 12x
constexpr uint16_t DOUBLE_TO_LONG = 0x8B;  // 12x
constexpr uint16_t DOUBLE_TO_FLOAT= 0x8C;  // 12x
constexpr uint16_t NOP            = 0x00;
}  // namespace opc

static int g_pass = 0, g_fail = 0, g_skip = 0;
static void record(const std::string& name, bool passed, const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    passed ? ++g_pass : ++g_fail;
}

// ── opcode encoders ────────────────────────────────────────────────────────
static uint16_t w11x(uint8_t reg, uint16_t op) { return static_cast<uint16_t>((reg << 8) | op); }
static uint16_t w12x(uint8_t vA, uint8_t vB, uint16_t op) {
    return static_cast<uint16_t>((vA << 12) | (vB << 8) | op);
}
static void emit_const(std::vector<uint16_t>& c, uint8_t reg, int32_t imm) {
    c.push_back(w11x(reg, opc::CONST));
    uint32_t u = static_cast<uint32_t>(imm);
    c.push_back(static_cast<uint16_t>(u & 0xFFFF));
    c.push_back(static_cast<uint16_t>(u >> 16));
}
static void emit_const_wide(std::vector<uint16_t>& c, uint8_t reg, int64_t imm) {
    c.push_back(w11x(reg, opc::CONST_WIDE));
    uint64_t u = static_cast<uint64_t>(imm);
    for (int i = 0; i < 4; i++) c.push_back(static_cast<uint16_t>((u >> (i * 16)) & 0xFFFF));
}
static void emit_const_wide_bits(std::vector<uint16_t>& c, uint8_t reg, uint64_t bits) {
    c.push_back(w11x(reg, opc::CONST_WIDE));
    for (int i = 0; i < 4; i++) c.push_back(static_cast<uint16_t>((bits >> (i * 16)) & 0xFFFF));
}
static void emit_23x(std::vector<uint16_t>& c, uint16_t op, uint8_t va, uint8_t vb, uint8_t vc) {
    c.push_back(w11x(va, op));
    c.push_back(static_cast<uint16_t>(vb | (vc << 8)));
}
static void emit_22s(std::vector<uint16_t>& c, uint16_t op, uint8_t va, uint8_t vb, int16_t lit) {
    // 22s: word0 = B|A|op (A high nibble, B low nibble of the high byte),
    //      word1 = the FULL signed 16-bit literal.
    c.push_back(static_cast<uint16_t>((va << 12) | (vb << 8) | op));
    c.push_back(static_cast<uint16_t>(static_cast<uint16_t>(lit)));
}
static void emit_22b(std::vector<uint16_t>& c, uint16_t op, uint8_t va, uint8_t vb, int8_t lit) {
    c.push_back(w11x(va, op));
    c.push_back(static_cast<uint16_t>(vb | (static_cast<uint16_t>(static_cast<uint8_t>(lit)) << 8)));
}
static void emit_21c(std::vector<uint16_t>& c, uint16_t op, uint8_t reg, uint16_t idx) {
    c.push_back(w11x(reg, op));
    c.push_back(idx);
}
static void emit_22c(std::vector<uint16_t>& c, uint16_t op, uint8_t va, uint8_t vb, uint16_t idx) {
    // 22c: word0 = B|A|op (B high nibble, A low nibble of high byte), word1 = idx@BBBB
    c.push_back(static_cast<uint16_t>((vb << 12) | (va << 8) | op));
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

// ── try-table encoder (same as unified0113) ───────────────────────────────
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
    if (catch_all_addr >= 0) put_uleb(tries_data, static_cast<uint32_t>(catch_all_addr));
}

// ── execution harness ──────────────────────────────────────────────────────
struct MethodIds {
    std::vector<DexMethodId> ids;
    // helper: register (class_desc, method_name) and return its method index.
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

static const InstructionTrace* find_return(const DalvikExecutionResult& r) {
    for (const auto& t : r.instruction_traces)
        if (t.status == InstructionTrace::Status::HALT_RETURN) return &t;
    return nullptr;
}
static double as_double(const DalvikValue& v) {
    switch (v.type) {
        case DalvikType::INT32:   return static_cast<double>(v.int_val);
        case DalvikType::INT64:   return static_cast<double>(v.long_val);
        case DalvikType::FLOAT32: return static_cast<double>(v.float_val);
        case DalvikType::FLOAT64: return v.double_val;
        case DalvikType::BOOLEAN: return (v.int_val != 0) ? 1.0 : 0.0;
        case DalvikType::BYTE:    return static_cast<double>(v.byte_val);
        case DalvikType::SHORT:   return static_cast<double>(v.short_val);
        case DalvikType::CHAR:    return static_cast<double>(static_cast<unsigned char>(v.char_val));
        default:                  return 0;
    }
}

// Execute a snippet whose method_ids[] come from MethodIds (may be empty).
static DalvikExecutionResult run_full(DalvikExecutionEngine& e,
                                      const std::vector<uint16_t>& code,
                                      const std::string& desc,
                                      const std::string& name,
                                      const MethodIds& mid,
                                      const std::vector<uint8_t>* tries_data) {
    if (getenv("FX_DUMP")) {
        std::cout << "DUMP " << name << " (" << code.size() << " units):";
        char buf[8];
        for (uint16_t u : code) { snprintf(buf, sizeof(buf), " %04X", u); std::cout << buf; }
        std::cout << "\n  strings:";
        for (auto& s : mid.strings) std::cout << " '" << s << "'";
        std::cout << "\n  types:";
        for (auto& t : mid.types) std::cout << " '" << t << "'";
        std::cout << "\n  mids:";
        for (auto& m : mid.ids) std::cout << " {c" << m.class_idx << ",n" << m.name_idx << "}";
        std::cout << "\n";
    }
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = desc;
    mi.defining_class = "LSemTest;";
    mi.registers_size = 24;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;
    if (tries_data) { mi.tries_data = *tries_data; mi.tries_size = 1; }

    DexReport report;
    report.strings = mid.strings;
    report.types = mid.types;
    report.method_ids = mid.ids;
    report.types.push_back("LSemTest;");
    report.strings.push_back("LSemTest;");
    ClassInfo ci;
    ci.name = "LSemTest;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);
    return e.execute_method(ci.direct_methods[0], report, {}, false);
}

static bool expect_num_ids(DalvikExecutionEngine& e, const char* name,
                           const std::vector<uint16_t>& code, const std::string& desc,
                           const MethodIds& mid, double expected,
                           const std::vector<uint8_t>* tries = nullptr) {
    DalvikExecutionResult r = run_full(e, code, desc, name, mid, tries);
    const auto* ret = find_return(r);
    if (!ret || !ret->return_value) {
        std::string last_op = r.instruction_traces.empty()
            ? "<none>" : r.instruction_traces.back().opcode_name;
        record(name, false, "no return trace/value (final_status=" +
               std::to_string(static_cast<int>(r.final_status)) + " last_op=" + last_op + ")");
        return false;
    }
    double got = as_double(*ret->return_value);
    bool ok = (got == expected);
    if (!ok) {
        std::string last_op = r.instruction_traces.empty()
            ? "<none>" : r.instruction_traces.back().opcode_name;
        record(name, ok, "expected " + std::to_string(expected) + ", got " + std::to_string(got) +
               " (final_status=" + std::to_string(static_cast<int>(r.final_status)) +
               " last_op=" + last_op + " ret_type=" +
               std::to_string(static_cast<int>(ret->return_value->type)) + ")");
    } else {
        record(name, ok, "expected " + std::to_string(expected) + ", got " + std::to_string(got));
    }
    return ok;
}
static bool expect_str_ids(DalvikExecutionEngine& e, const char* name,
                           const std::vector<uint16_t>& code, const MethodIds& mid,
                           const std::string& expected) {
    DalvikExecutionResult r = run_full(e, code, "()Ljava/lang/String;", name, mid, nullptr);
    const auto* ret = find_return(r);
    if (!ret || !ret->return_value) {
        record(name, false, "no return trace/value");
        return false;
    }
    std::string got = ret->return_value->string_val;
    bool ok = (got == expected);
    record(name, ok, "expected \"" + expected + "\", got \"" + got + "\"");
    return ok;
}
// Object-returning case: PASS iff a non-null object ref came back.
static bool expect_obj_nonnull(DalvikExecutionEngine& e, const char* name,
                               const std::vector<uint16_t>& code, const MethodIds& mid) {
    DalvikExecutionResult r = run_full(e, code, "()Ljava/lang/Object;", name, mid, nullptr);
    const auto* ret = find_return(r);
    if (!ret || !ret->return_value) {
        record(name, false, "no return trace/value");
        return false;
    }
    bool ok = (ret->return_value->type == DalvikType::OBJECT_REF);
    record(name, ok, ok ? "object ref returned" : "no object ref (type=" +
           std::to_string(static_cast<int>(ret->return_value->type)) + ")");
    return ok;
}
// Typed-catch oracle with arbitrary exception type list.
static bool expect_caught_types(DalvikExecutionEngine& e, const char* name,
                                const std::vector<uint16_t>& code,
                                MethodIds& mid, const std::string& exc_type,
                                int handler_marker) {
    // code layout: caller's `code` ends with its own fallthrough
    // "const v0,1; return v0" (marker 1 = no throw). Handler appended here:
    // const v0, marker (31i = 3 units); return v0.
    uint32_t hstart = static_cast<uint32_t>(code.size());
    std::vector<uint16_t> full = code;
    emit_const(full, 0, handler_marker);
    full.push_back(w11x(0, opc::RETURN));
    std::vector<uint8_t> tries;
    uint16_t t_idx = mid.type_idx(exc_type);
    append_try(tries, 0, static_cast<uint16_t>(hstart), {{t_idx, static_cast<uint32_t>(hstart)}}, -1);
    DalvikExecutionResult r = run_full(e, full, "()I", name, mid, &tries);
    const auto* ret = find_return(r);
    if (!ret || !ret->return_value) {
        record(name, false, "no return trace/value (exception uncaught?)");
        return false;
    }
    double got = as_double(*ret->return_value);
    bool ok = (got == static_cast<double>(handler_marker));
    record(name, ok, got == 1.0 ? "fell through (no throw)" :
           "expected handler marker " + std::to_string(handler_marker) + ", got " + std::to_string(got));
    return ok;
}
static bool expect_null_obj(DalvikExecutionEngine& e, const char* name,
                            const std::vector<uint16_t>& code, const MethodIds& mid) {
    DalvikExecutionResult r = run_full(e, code, "()Ljava/lang/Object;", name, mid, nullptr);
    const auto* ret = find_return(r);
    if (!ret || !ret->return_value) {
        record(name, false, "no return trace/value");
        return false;
    }
    bool ok = (ret->return_value->type == DalvikType::NULL_REF);
    record(name, ok, ok ? "null ref returned" : "expected null, got type=" +
           std::to_string(static_cast<int>(ret->return_value->type)));
    return ok;
}
static bool expect_nan_or_inf(DalvikExecutionEngine& e, const char* name,
                              const std::vector<uint16_t>& code, const std::string& desc,
                              const MethodIds& mid, int kind /*0=NaN,1=+Inf,2=-Inf*/) {
    DalvikExecutionResult r = run_full(e, code, desc, name, mid, nullptr);
    const auto* ret = find_return(r);
    if (!ret || !ret->return_value) { record(name, false, "no return value"); return false; }
    double got = as_double(*ret->return_value);
    bool ok = (kind == 0) ? std::isnan(got)
            : (kind == 1) ? (std::isinf(got) && got > 0)
            :               (std::isinf(got) && got < 0);
    record(name, ok, "got " + std::to_string(got));
    return ok;
}

// raw bit pattern of a double (for const-wide with FLOAT64 payloads — the
// engine stores const-wide bits raw, tagged INT64: rule #3 in K docs).
static uint64_t dbits(double d) { uint64_t u; memcpy(&u, &d, 8); return u; }

// Invoke-helpers shorthand builders -----------------------------------------
static void call_virtual(std::vector<uint16_t>& c, uint16_t midx,
                         const std::vector<uint8_t>& regs, uint8_t dst, uint16_t move_op) {
    emit_invoke(c, opc::INVOKE_VIRTUAL, static_cast<uint8_t>(regs.size()), regs, midx);
    emit_move_result(c, dst, move_op);
}

// ═══════════════════ GROUP X: XmlPullParser ═══════════════════
static void group_xml(DalvikExecutionEngine& e) {
    std::cout << "\n[GROUP X] XmlPullParser — real event progression + termination\n";
    const std::string XML1 = "<r a='1'><b>hi</b><!--c--></r>";

    {   // X1: full event sequence 2,2,4,3,3,1 → packed base-10 = 224331
        MethodIds mid;
        uint16_t m_new   = mid.add("Landroid/util/Xml;", "newPullParser");
        uint16_t m_init  = mid.add("Ljava/io/StringReader;", "<init>");
        uint16_t m_input = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "setInput");
        uint16_t m_next  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "next");
        uint16_t t_sr    = mid.type_idx("Ljava/io/StringReader;");
        uint16_t s_xml   = mid.string_idx(XML1);
        std::vector<uint16_t> c;
        emit_invoke(c, opc::INVOKE_STATIC, 0, {}, m_new);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);        // v0 = parser
        emit_21c(c, opc::NEW_INSTANCE, 1, t_sr);                 // v1 = StringReader
        emit_21c(c, opc::CONST_STRING, 2, s_xml);                // v2 = XML text
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {1, 2}, m_init);   // StringReader.<init>
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {0, 1}, m_input); // setInput(reader)
        emit_const(c, 3, 0);                                      // v3 = accumulator
        for (int i = 0; i < 6; ++i) {
            call_virtual(c, m_next, {0}, 4, opc::MOVE_RESULT);
            emit_22b(c, opc::MUL_INT_LIT8, 3, 3, 10);            // v3 *= 10 (lit8 path too)
            emit_23x(c, opc::ADD_INT, 3, 3, 4);                   // v3 += event
        }
        emit_move_result(c, 3, opc::RETURN);
        expect_num_ids(e, "xml_event_sequence_tags_text_comment_end", c, "()I", mid, 224331.0);
    }
    {   // X2: getEventType right after setInput = START_DOCUMENT(0); first next() = START_TAG(2)
        MethodIds mid;
        uint16_t m_new   = mid.add("Landroid/util/Xml;", "newPullParser");
        uint16_t m_init  = mid.add("Ljava/io/StringReader;", "<init>");
        uint16_t m_input = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "setInput");
        uint16_t m_type  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "getEventType");
        uint16_t m_next  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "next");
        uint16_t t_sr    = mid.type_idx("Ljava/io/StringReader;");
        uint16_t s_xml   = mid.string_idx(XML1);
        std::vector<uint16_t> c;
        emit_invoke(c, opc::INVOKE_STATIC, 0, {}, m_new);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_21c(c, opc::NEW_INSTANCE, 1, t_sr);
        emit_21c(c, opc::CONST_STRING, 2, s_xml);
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {1, 2}, m_init);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {0, 1}, m_input);
        call_virtual(c, m_type, {0}, 3, opc::MOVE_RESULT);        // v3 = 0
        call_virtual(c, m_next, {0}, 4, opc::MOVE_RESULT);        // v4 = 2
        // packed = 0*10 + 2 → but keep distinct: 0*100 + 2
        emit_const(c, 5, 100);
        emit_22b(c, opc::MUL_INT_LIT8, 3, 3, 100);
        emit_23x(c, opc::ADD_INT, 3, 3, 4);
        emit_move_result(c, 3, opc::RETURN);
        expect_num_ids(e, "xml_eventtype_initial_then_starttag", c, "()I", mid, 2.0);
    }
    {   // X3: getName at START_TAG → "r"
        MethodIds mid;
        uint16_t m_new   = mid.add("Landroid/util/Xml;", "newPullParser");
        uint16_t m_init  = mid.add("Ljava/io/StringReader;", "<init>");
        uint16_t m_input = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "setInput");
        uint16_t m_next  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "next");
        uint16_t m_name  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "getName");
        uint16_t t_sr    = mid.type_idx("Ljava/io/StringReader;");
        uint16_t s_xml   = mid.string_idx(XML1);
        std::vector<uint16_t> c;
        emit_invoke(c, opc::INVOKE_STATIC, 0, {}, m_new);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_21c(c, opc::NEW_INSTANCE, 1, t_sr);
        emit_21c(c, opc::CONST_STRING, 2, s_xml);
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {1, 2}, m_init);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {0, 1}, m_input);
        call_virtual(c, m_next, {0}, 3, opc::MOVE_RESULT);
        call_virtual(c, m_name, {0}, 4, opc::MOVE_RESULT_OBJECT);
        emit_move_result(c, 4, opc::RETURN_OBJECT);
        expect_str_ids(e, "xml_getname_root_tag", c, mid, "r");
    }
    {   // X4: getText at TEXT → "hi"
        MethodIds mid;
        uint16_t m_new   = mid.add("Landroid/util/Xml;", "newPullParser");
        uint16_t m_init  = mid.add("Ljava/io/StringReader;", "<init>");
        uint16_t m_input = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "setInput");
        uint16_t m_next  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "next");
        uint16_t m_text  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "getText");
        uint16_t t_sr    = mid.type_idx("Ljava/io/StringReader;");
        uint16_t s_xml   = mid.string_idx(XML1);
        std::vector<uint16_t> c;
        emit_invoke(c, opc::INVOKE_STATIC, 0, {}, m_new);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_21c(c, opc::NEW_INSTANCE, 1, t_sr);
        emit_21c(c, opc::CONST_STRING, 2, s_xml);
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {1, 2}, m_init);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {0, 1}, m_input);
        for (int i = 0; i < 3; ++i) call_virtual(c, m_next, {0}, 3, opc::MOVE_RESULT);
        call_virtual(c, m_text, {0}, 4, opc::MOVE_RESULT_OBJECT);
        emit_move_result(c, 4, opc::RETURN_OBJECT);
        expect_str_ids(e, "xml_gettext_text_event", c, mid, "hi");
    }
    {   // X5: getAttributeValue(ns="", name="a") → "1"
        MethodIds mid;
        uint16_t m_new   = mid.add("Landroid/util/Xml;", "newPullParser");
        uint16_t m_init  = mid.add("Ljava/io/StringReader;", "<init>");
        uint16_t m_input = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "setInput");
        uint16_t m_next  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "next");
        uint16_t m_attr  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "getAttributeValue");
        uint16_t t_sr    = mid.type_idx("Ljava/io/StringReader;");
        uint16_t s_xml   = mid.string_idx(XML1);
        uint16_t s_ns    = mid.string_idx("");
        uint16_t s_a     = mid.string_idx("a");
        std::vector<uint16_t> c;
        emit_invoke(c, opc::INVOKE_STATIC, 0, {}, m_new);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_21c(c, opc::NEW_INSTANCE, 1, t_sr);
        emit_21c(c, opc::CONST_STRING, 2, s_xml);
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {1, 2}, m_init);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {0, 1}, m_input);
        call_virtual(c, m_next, {0}, 3, opc::MOVE_RESULT);
        emit_21c(c, opc::CONST_STRING, 5, s_ns);                 // ns = ""
        emit_21c(c, opc::CONST_STRING, 6, s_a);                  // name = "a"
        emit_invoke(c, opc::INVOKE_VIRTUAL, 3, {0, 5, 6}, m_attr);
        emit_move_result(c, 7, opc::MOVE_RESULT_OBJECT);
        emit_move_result(c, 7, opc::RETURN_OBJECT);
        expect_str_ids(e, "xml_getattributevalue_by_name", c, mid, "1");
    }
    {   // X6: next() AFTER END_DOCUMENT throws XmlPullParserException (typed catch)
        MethodIds mid;
        uint16_t m_new   = mid.add("Landroid/util/Xml;", "newPullParser");
        uint16_t m_init  = mid.add("Ljava/io/StringReader;", "<init>");
        uint16_t m_input = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "setInput");
        uint16_t m_next  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "next");
        uint16_t t_sr    = mid.type_idx("Ljava/io/StringReader;");
        uint16_t s_xml   = mid.string_idx(XML1);
        std::vector<uint16_t> c;
        emit_invoke(c, opc::INVOKE_STATIC, 0, {}, m_new);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_21c(c, opc::NEW_INSTANCE, 1, t_sr);
        emit_21c(c, opc::CONST_STRING, 2, s_xml);
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {1, 2}, m_init);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {0, 1}, m_input);
        for (int i = 0; i < 7; ++i) {                             // 6 valid + 1 past-end
            call_virtual(c, m_next, {0}, 3, opc::MOVE_RESULT);
        }
        emit_const(c, 3, 1);                                      // fallthrough marker
        emit_move_result(c, 3, opc::RETURN);
        expect_caught_types(e, "xml_next_after_end_document_throws", c, mid,
                            "Lorg/xmlpull/v1/XmlPullParserException;", 777);
    }
    {   // X7: self-closing tag <br/> queues exactly one END_TAG
        //     "<r><br/><b>x</b></r>" → 2,2,3,2,4,3,3 → packed 2232433
        MethodIds mid;
        uint16_t m_new   = mid.add("Landroid/util/Xml;", "newPullParser");
        uint16_t m_init  = mid.add("Ljava/io/StringReader;", "<init>");
        uint16_t m_input = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "setInput");
        uint16_t m_next  = mid.add("Lorg/xmlpull/v1/XmlPullParser;", "next");
        uint16_t t_sr    = mid.type_idx("Ljava/io/StringReader;");
        uint16_t s_xml   = mid.string_idx("<r><br/><b>x</b></r>");
        std::vector<uint16_t> c;
        emit_invoke(c, opc::INVOKE_STATIC, 0, {}, m_new);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_21c(c, opc::NEW_INSTANCE, 1, t_sr);
        emit_21c(c, opc::CONST_STRING, 2, s_xml);
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {1, 2}, m_init);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {0, 1}, m_input);
        emit_const(c, 3, 0);
        for (int i = 0; i < 7; ++i) {
            call_virtual(c, m_next, {0}, 4, opc::MOVE_RESULT);
            emit_22b(c, opc::MUL_INT_LIT8, 3, 3, 10);
            emit_23x(c, opc::ADD_INT, 3, 3, 4);
        }
        emit_move_result(c, 3, opc::RETURN);
        expect_num_ids(e, "xml_selfclosing_tag_end_event", c, "()I", mid, 2232433.0);
    }
}

// ═══════════════════ GROUP AR: AtomicReference ═══════════════════
static void group_atomic(DalvikExecutionEngine& e) {
    std::cout << "\n[GROUP AR] AtomicReference — CAS identity/null semantics\n";
    const std::string AR = "Ljava/util/concurrent/atomic/AtomicReference;";

    {   // AR1: <init>() then get() → null
        MethodIds mid;
        uint16_t m_init = mid.add(AR, "<init>");
        uint16_t m_get  = mid.add(AR, "get");
        uint16_t t_ar   = mid.type_idx(AR);
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 0, t_ar);
        emit_invoke(c, opc::INVOKE_DIRECT, 1, {0}, m_init);
        call_virtual(c, m_get, {0}, 1, opc::MOVE_RESULT_OBJECT);
        emit_move_result(c, 1, opc::RETURN_OBJECT);
        expect_null_obj(e, "ar_get_after_noarg_init_is_null", c, mid);
    }
    {   // AR2: init("v1"); CAS("v2","v3") → false (expect mismatch)
        MethodIds mid;
        uint16_t m_init = mid.add(AR, "<init>");
        uint16_t m_cas  = mid.add(AR, "compareAndSet");
        uint16_t t_ar   = mid.type_idx(AR);
        uint16_t s_v1   = mid.string_idx("v1");
        uint16_t s_v2   = mid.string_idx("v2");
        uint16_t s_v3   = mid.string_idx("v3");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 0, t_ar);
        emit_21c(c, opc::CONST_STRING, 1, s_v1);
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {0, 1}, m_init);
        emit_21c(c, opc::CONST_STRING, 2, s_v2);
        emit_21c(c, opc::CONST_STRING, 3, s_v3);
        call_virtual(c, m_cas, {0, 2, 3}, 4, opc::MOVE_RESULT);
        emit_move_result(c, 4, opc::RETURN);
        expect_num_ids(e, "ar_cas_wrong_expect_false", c, "()I", mid, 0.0);
    }
    {   // AR3: init("v1"); CAS("v1","v2") → true
        MethodIds mid;
        uint16_t m_init = mid.add(AR, "<init>");
        uint16_t m_cas  = mid.add(AR, "compareAndSet");
        uint16_t t_ar   = mid.type_idx(AR);
        uint16_t s_v1   = mid.string_idx("v1");
        uint16_t s_v2   = mid.string_idx("v2");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 0, t_ar);
        emit_21c(c, opc::CONST_STRING, 1, s_v1);
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {0, 1}, m_init);
        emit_21c(c, opc::CONST_STRING, 2, s_v1);
        emit_21c(c, opc::CONST_STRING, 3, s_v2);
        call_virtual(c, m_cas, {0, 2, 3}, 4, opc::MOVE_RESULT);
        emit_move_result(c, 4, opc::RETURN);
        expect_num_ids(e, "ar_cas_success_true", c, "()I", mid, 1.0);
    }
    {   // AR4: init("v1"); getAndSet("v2") → returns OLD "v1"
        MethodIds mid;
        uint16_t m_init = mid.add(AR, "<init>");
        uint16_t m_gas  = mid.add(AR, "getAndSet");
        uint16_t t_ar   = mid.type_idx(AR);
        uint16_t s_v1   = mid.string_idx("v1");
        uint16_t s_v2   = mid.string_idx("v2");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 0, t_ar);
        emit_21c(c, opc::CONST_STRING, 1, s_v1);
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {0, 1}, m_init);
        emit_21c(c, opc::CONST_STRING, 2, s_v2);
        call_virtual(c, m_gas, {0, 2}, 3, opc::MOVE_RESULT_OBJECT);
        emit_move_result(c, 3, opc::RETURN_OBJECT);
        expect_str_ids(e, "ar_getandset_returns_old", c, mid, "v1");
    }
    {   // AR5: init("v1"); getAndSet("v2"); CAS("v2","v3") → true (proves the set landed)
        MethodIds mid;
        uint16_t m_init = mid.add(AR, "<init>");
        uint16_t m_gas  = mid.add(AR, "getAndSet");
        uint16_t m_cas  = mid.add(AR, "compareAndSet");
        uint16_t t_ar   = mid.type_idx(AR);
        uint16_t s_v1   = mid.string_idx("v1");
        uint16_t s_v2   = mid.string_idx("v2");
        uint16_t s_v3   = mid.string_idx("v3");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 0, t_ar);
        emit_21c(c, opc::CONST_STRING, 1, s_v1);
        emit_invoke(c, opc::INVOKE_DIRECT, 2, {0, 1}, m_init);
        emit_21c(c, opc::CONST_STRING, 2, s_v2);
        call_virtual(c, m_gas, {0, 2}, 3, opc::MOVE_RESULT_OBJECT);
        emit_21c(c, opc::CONST_STRING, 4, s_v2);
        emit_21c(c, opc::CONST_STRING, 5, s_v3);
        call_virtual(c, m_cas, {0, 4, 5}, 6, opc::MOVE_RESULT);
        emit_move_result(c, 6, opc::RETURN);
        expect_num_ids(e, "ar_cas_after_getandset_true", c, "()I", mid, 1.0);
    }
    {   // AR6 (identity discriminator): init(objA); CAS(objB, objC) → FALSE even
        //     though both are "LSemObj;" — a class-name/string-compare fake
        //     implementation would wrongly return true here.
        MethodIds mid;
        uint16_t m_init = mid.add(AR, "<init>");
        uint16_t m_set  = mid.add(AR, "set");
        uint16_t m_cas  = mid.add(AR, "compareAndSet");
        uint16_t t_ar   = mid.type_idx(AR);
        uint16_t t_obj  = mid.type_idx("LSemObj;");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 0, t_ar);                 // AR
        emit_invoke(c, opc::INVOKE_DIRECT, 1, {0}, m_init);
        emit_21c(c, opc::NEW_INSTANCE, 1, t_obj);                // objA
        call_virtual(c, m_set, {0, 1}, 2, opc::MOVE_RESULT);     // set(objA)
        emit_21c(c, opc::NEW_INSTANCE, 3, t_obj);                // objB (distinct!)
        emit_21c(c, opc::NEW_INSTANCE, 4, t_obj);                // objC
        call_virtual(c, m_cas, {0, 3, 4}, 5, opc::MOVE_RESULT);  // CAS(objB→objC)
        emit_move_result(c, 5, opc::RETURN);
        expect_num_ids(e, "ar_cas_object_identity_not_class_match", c, "()I", mid, 0.0);
    }
    {   // AR7: init(objA); CAS(objA→objC) → TRUE (real identity match works)
        MethodIds mid;
        uint16_t m_init = mid.add(AR, "<init>");
        uint16_t m_set  = mid.add(AR, "set");
        uint16_t m_cas  = mid.add(AR, "compareAndSet");
        uint16_t t_ar   = mid.type_idx(AR);
        uint16_t t_obj  = mid.type_idx("LSemObj;");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 0, t_ar);
        emit_invoke(c, opc::INVOKE_DIRECT, 1, {0}, m_init);
        emit_21c(c, opc::NEW_INSTANCE, 1, t_obj);                // objA
        call_virtual(c, m_set, {0, 1}, 2, opc::MOVE_RESULT);
        emit_21c(c, opc::NEW_INSTANCE, 3, t_obj);                // objB (not stored)
        emit_21c(c, opc::NEW_INSTANCE, 4, t_obj);                // objC
        call_virtual(c, m_cas, {0, 1, 4}, 5, opc::MOVE_RESULT);  // CAS(objA→objC)
        emit_move_result(c, 5, opc::RETURN);
        expect_num_ids(e, "ar_cas_object_identity_match_true", c, "()I", mid, 1.0);
    }
}


// ═══════════════════ GROUP ST: InputStream real bytes ═══════════════════
static void group_stream(DalvikExecutionEngine& e) {
    std::cout << "\n[GROUP ST] InputStream.read — REAL asset bytes (simplestopwatch license.html)\n";
    const char* cache = getenv("MINIANDROID_APK_CACHE");
    std::string base = cache ? cache : "/home/z/my-project/miniandroid_ws/apk_cache";
    std::string apk = base + "/corpus/simplestopwatch.apk";
    // Independent oracle: extract the first bytes OUTSIDE the engine.
    std::string truth;
    {
        std::string cmd = "unzip -p '" + apk + "' 'assets/license.html' 2>/dev/null | head -c 8";
        FILE* p = popen(cmd.c_str(), "r");
        char buf[16] = {0};
        size_t n = fread(buf, 1, sizeof(buf) - 1, p);
        pclose(p);
        truth.assign(buf, n);
    }
    if (truth.size() < 4) {
        std::cout << "  SKIP  (oracle asset unavailable — recorded, not hidden)\n";
        g_skip += 1;
        return;
    }
    e.set_apk_path(apk);
    auto ub = [](unsigned char c) { return static_cast<double>(c); };
    double b0 = ub(static_cast<unsigned char>(truth[0]));
    double b1 = ub(static_cast<unsigned char>(truth[1]));
    double b2 = ub(static_cast<unsigned char>(truth[2]));
    std::cout << "  (oracle: first bytes = " << std::hex
              << static_cast<int>(static_cast<unsigned char>(truth[0])) << " "
              << static_cast<int>(static_cast<unsigned char>(truth[1])) << " "
              << static_cast<int>(static_cast<unsigned char>(truth[2]))
              << std::dec << ")\n";

    {   // ST1: first three read() values packed: b0 + b1*256 + b2*65536
        MethodIds mid;
        uint16_t m_open = mid.add("Landroid/content/res/AssetManager;", "open");
        uint16_t m_read = mid.add("Ljava/io/InputStream;", "read");
        uint16_t t_am   = mid.type_idx("Landroid/content/res/AssetManager;");
        uint16_t s_a    = mid.string_idx("license.html");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 14, t_am);                   // v20 = AssetManager
        emit_21c(c, opc::CONST_STRING, 1, s_a);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {14, 1}, m_open);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);             // v0 = stream
        static const double mult[3] = {1.0, 256.0, 65536.0};
        emit_const(c, 4, 0);                                         // v4 = accumulator
        for (int i = 0; i < 3; ++i) {
            call_virtual(c, m_read, {0}, 2, opc::MOVE_RESULT);       // v2 = byte
            int32_t m = static_cast<int32_t>(mult[i]);
            emit_const(c, 3, m);
            emit_23x(c, opc::MUL_INT, 3, 2, 3);                      // v3 = byte*m
            emit_23x(c, opc::ADD_INT, 4, 4, 3);                      // v4 += v3
        }
        emit_move_result(c, 4, opc::RETURN);
        expect_num_ids(e, "st_read_first_bytes_match_asset", c, "()I", mid,
                       b0 + b1 * 256.0 + b2 * 65536.0);
    }
    {   // ST2: available() decreases by exactly 1 after one read()
        MethodIds mid;
        uint16_t m_open = mid.add("Landroid/content/res/AssetManager;", "open");
        uint16_t m_read = mid.add("Ljava/io/InputStream;", "read");
        uint16_t m_av   = mid.add("Ljava/io/InputStream;", "available");
        uint16_t t_am   = mid.type_idx("Landroid/content/res/AssetManager;");
        uint16_t s_a    = mid.string_idx("license.html");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 14, t_am);
        emit_21c(c, opc::CONST_STRING, 1, s_a);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {14, 1}, m_open);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        call_virtual(c, m_av, {0}, 5, opc::MOVE_RESULT);
        call_virtual(c, m_read, {0}, 2, opc::MOVE_RESULT);
        call_virtual(c, m_av, {0}, 6, opc::MOVE_RESULT);
        emit_23x(c, opc::SUB_INT, 7, 5, 6);
        emit_move_result(c, 7, opc::RETURN);
        expect_num_ids(e, "st_available_decrements_by_one", c, "()I", mid, 1.0);
    }
    {   // ST3: read(byte[],0,16) fills the array — aget-byte[0] == oracle byte0
        MethodIds mid;
        uint16_t m_open = mid.add("Landroid/content/res/AssetManager;", "open");
        uint16_t m_read = mid.add("Ljava/io/InputStream;", "read");
        uint16_t t_am   = mid.type_idx("Landroid/content/res/AssetManager;");
        uint16_t t_ba   = mid.type_idx("[B");
        uint16_t s_a    = mid.string_idx("license.html");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 14, t_am);
        emit_21c(c, opc::CONST_STRING, 1, s_a);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {14, 1}, m_open);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_const(c, 2, 16);
        emit_22c(c, opc::NEW_ARRAY, 3, 2, t_ba);                     // v3 = byte[16]
        emit_const(c, 4, 0);  emit_const(c, 5, 16);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 4, {0, 3, 4, 5}, m_read);
        emit_move_result(c, 6, opc::MOVE_RESULT);                    // v6 = count
        emit_const(c, 7, 0);
        emit_23x(c, opc::AGET_BYTE, 8, 3, 7);                        // v8 = b[0]
        // packed = count*1000 + b[0] → 16*1000 + b0 (proves BOTH count and content)
        emit_const(c, 9, 1000);
        emit_23x(c, opc::MUL_INT, 10, 6, 9);
        emit_23x(c, opc::ADD_INT, 11, 10, 8);
        emit_move_result(c, 11, opc::RETURN);
        expect_num_ids(e, "st_bulk_read_fills_array", c, "()I", mid, 16.0 * 1000.0 + b0);
    }
    {   // ST4: EOF — bulk read drains, then read() → -1
        MethodIds mid;
        uint16_t m_open = mid.add("Landroid/content/res/AssetManager;", "open");
        uint16_t m_read = mid.add("Ljava/io/InputStream;", "read");
        uint16_t t_am   = mid.type_idx("Landroid/content/res/AssetManager;");
        uint16_t t_ba   = mid.type_idx("[B");
        uint16_t s_a    = mid.string_idx("license.html");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 14, t_am);
        emit_21c(c, opc::CONST_STRING, 1, s_a);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {14, 1}, m_open);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_const(c, 2, 65536);
        emit_22c(c, opc::NEW_ARRAY, 3, 2, t_ba);
        emit_const(c, 4, 0);  emit_const(c, 5, 65536);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 4, {0, 3, 4, 5}, m_read);
        emit_move_result(c, 6, opc::MOVE_RESULT);
        call_virtual(c, m_read, {0}, 7, opc::MOVE_RESULT);
        emit_move_result(c, 7, opc::RETURN);
        expect_num_ids(e, "st_read_after_drain_is_eof_minus1", c, "()I", mid, -1.0);
    }
    {   // ST5: close() then read() → -1
        MethodIds mid;
        uint16_t m_open = mid.add("Landroid/content/res/AssetManager;", "open");
        uint16_t m_read = mid.add("Ljava/io/InputStream;", "read");
        uint16_t m_cls  = mid.add("Ljava/io/InputStream;", "close");
        uint16_t t_am   = mid.type_idx("Landroid/content/res/AssetManager;");
        uint16_t s_a    = mid.string_idx("license.html");
        std::vector<uint16_t> c;
        emit_21c(c, opc::NEW_INSTANCE, 14, t_am);
        emit_21c(c, opc::CONST_STRING, 1, s_a);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {14, 1}, m_open);
        emit_move_result(c, 0, opc::MOVE_RESULT_OBJECT);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 1, {0}, m_cls);
        call_virtual(c, m_read, {0}, 2, opc::MOVE_RESULT);
        emit_move_result(c, 2, opc::RETURN);
        expect_num_ids(e, "st_read_after_close_is_eof", c, "()I", mid, -1.0);
    }
}

// ═══════════════════ GROUP CV: full conversion matrix ═══════════════════
static void group_conv(DalvikExecutionEngine& e) {
    std::cout << "\n[GROUP CV] conversions — real numeric semantics (JLS 5.1.3)\n";
    {   // long→int truncation of 0x1_0000_0005 → 5
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, 0x100000005LL);
        c.push_back(w12x(2, 0, opc::LONG_TO_INT));
        emit_move_result(c, 2, opc::RETURN);
        expect_num_ids(e, "cv_long_to_int_truncates", c, "()I", MethodIds{}, 5.0);
    }
    {   // int→long sign extension of -5
        std::vector<uint16_t> c;
        emit_const(c, 0, -5);
        c.push_back(w12x(2, 0, opc::INT_TO_LONG));
        emit_move_result(c, 2, opc::RETURN_WIDE);
        expect_num_ids(e, "cv_int_to_long_sign_extends", c, "()J", MethodIds{}, -5.0);
    }
    {   // long→float of 12345678901 (precision-limited float)
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, 12345678901LL);
        c.push_back(w12x(2, 0, opc::LONG_TO_FLOAT));
        emit_move_result(c, 2, opc::RETURN);
        float expected = static_cast<float>(12345678901LL);
        expect_num_ids(e, "cv_long_to_float_numeric", c, "()F", MethodIds{}, static_cast<double>(expected));
    }
    {   // long→double exact for 2^53
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, 9007199254740992LL);
        c.push_back(w12x(2, 0, opc::LONG_TO_DOUBLE));
        emit_move_result(c, 2, opc::RETURN_WIDE);
        expect_num_ids(e, "cv_long_to_double_exact_2p53", c, "()D", MethodIds{}, 9007199254740992.0);
    }
    {   // long→double negative
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, -1234567890123LL);
        c.push_back(w12x(2, 0, opc::LONG_TO_DOUBLE));
        emit_move_result(c, 2, opc::RETURN_WIDE);
        expect_num_ids(e, "cv_long_to_double_negative", c, "()D", MethodIds{}, -1234567890123.0);
    }
    {   // double→long truncation toward zero: 1234567890.75 → 1234567890
        std::vector<uint16_t> c;
        emit_const_wide_bits(c, 0, dbits(1234567890.75));
        c.push_back(w12x(2, 0, opc::DOUBLE_TO_LONG));
        emit_move_result(c, 2, opc::RETURN_WIDE);
        expect_num_ids(e, "cv_double_to_long_truncates", c, "()J", MethodIds{}, 1234567890.0);
    }
    {   // double→long negative truncation: -1234567890.75 → -1234567890
        std::vector<uint16_t> c;
        emit_const_wide_bits(c, 0, dbits(-1234567890.75));
        c.push_back(w12x(2, 0, opc::DOUBLE_TO_LONG));
        emit_move_result(c, 2, opc::RETURN_WIDE);
        expect_num_ids(e, "cv_double_to_long_negative_toward_zero", c, "()J", MethodIds{}, -1234567890.0);
    }
    {   // double→float→long chain: 3.7e9 → 3700000000 (64-bit target; an int32
        //     truncating implementation would wrap to a negative value)
        std::vector<uint16_t> c;
        emit_const_wide_bits(c, 0, dbits(3700000000.0));
        c.push_back(w12x(2, 0, opc::DOUBLE_TO_FLOAT));
        c.push_back(w12x(3, 2, opc::FLOAT_TO_LONG));
        emit_move_result(c, 3, opc::RETURN_WIDE);
        expect_num_ids(e, "cv_double_float_long_3p7e9_64bit", c, "()J", MethodIds{}, 3700000000.0);
    }
    {   // double→float rounding: (double)(float)0.1 ≠ 0.1
        std::vector<uint16_t> c;
        emit_const_wide_bits(c, 0, dbits(0.1));
        c.push_back(w12x(2, 0, opc::DOUBLE_TO_FLOAT));
        emit_move_result(c, 2, opc::RETURN);
        expect_num_ids(e, "cv_double_to_float_rounds", c, "()F", MethodIds{},
                       static_cast<double>(static_cast<float>(0.1)));
    }
    {   // NaN double→int → 0 (JLS)
        std::vector<uint16_t> c;
        emit_const_wide_bits(c, 0, dbits(std::nan("")));
        c.push_back(w12x(2, 0, opc::DOUBLE_TO_INT));
        emit_move_result(c, 2, opc::RETURN);
        expect_num_ids(e, "cv_nan_double_to_int_zero", c, "()I", MethodIds{}, 0.0);
    }
    {   // +Inf double→int → INT_MAX (JLS clamp)
        std::vector<uint16_t> c;
        emit_const_wide_bits(c, 0, dbits(HUGE_VAL));
        c.push_back(w12x(2, 0, opc::DOUBLE_TO_INT));
        emit_move_result(c, 2, opc::RETURN);
        expect_num_ids(e, "cv_posinf_double_to_int_clamps_max", c, "()I", MethodIds{}, 2147483647.0);
    }
    {   // -Inf double→int → INT_MIN (JLS clamp)
        std::vector<uint16_t> c;
        emit_const_wide_bits(c, 0, dbits(-HUGE_VAL));
        c.push_back(w12x(2, 0, opc::DOUBLE_TO_INT));
        emit_move_result(c, 2, opc::RETURN);
        expect_num_ids(e, "cv_neginf_double_to_int_clamps_min", c, "()I", MethodIds{}, -2147483648.0);
    }
    {   // +Inf double→long → LONG_MAX
        std::vector<uint16_t> c;
        emit_const_wide_bits(c, 0, dbits(HUGE_VAL));
        c.push_back(w12x(2, 0, opc::DOUBLE_TO_LONG));
        emit_move_result(c, 2, opc::RETURN_WIDE);
        expect_num_ids(e, "cv_posinf_double_to_long_clamps_max", c, "()J", MethodIds{},
                       9223372036854775807.0);
    }
    {   // double→float→int truncation: 2.75 → 2.75f → 2
        std::vector<uint16_t> c;
        emit_const_wide_bits(c, 0, dbits(2.75));
        c.push_back(w12x(2, 0, opc::DOUBLE_TO_FLOAT));
        c.push_back(w12x(3, 2, opc::FLOAT_TO_INT));
        emit_move_result(c, 3, opc::RETURN);
        expect_num_ids(e, "cv_double_float_int_truncates", c, "()I", MethodIds{}, 2.0);
    }
}

// ═══════════════════ GROUP DR: div/rem extended matrix ═══════════════════
static void group_divrem(DalvikExecutionEngine& e) {
    std::cout << "\n[GROUP DR] div/rem — lit16/2addr/negative-divisor matrix\n";
    {   // 7 / -2 via div-int/lit16 → -3 (Java truncation)
        std::vector<uint16_t> c;
        emit_const(c, 0, 7);
        emit_22s(c, opc::DIV_INT_LIT16, 2, 0, -2);
        emit_move_result(c, 2, opc::RETURN);
        expect_num_ids(e, "dr_div_int_lit16_negative_divisor", c, "()I", MethodIds{}, -3.0);
    }
    {   // 7 % -2 via rem-int/lit16 → 1
        std::vector<uint16_t> c;
        emit_const(c, 0, 7);
        emit_22s(c, opc::REM_INT_LIT16, 2, 0, -2);
        emit_move_result(c, 2, opc::RETURN);
        expect_num_ids(e, "dr_rem_int_lit16_negative_divisor", c, "()I", MethodIds{}, 1.0);
    }
    {   // -7 / -2 via div-int 23x → 3
        std::vector<uint16_t> c;
        emit_const(c, 0, -7);  emit_const(c, 1, -2);
        emit_23x(c, opc::DIV_INT, 2, 0, 1);
        emit_move_result(c, 2, opc::RETURN);
        expect_num_ids(e, "dr_div_int_neg_neg_positive", c, "()I", MethodIds{}, 3.0);
    }
    {   // 7 / -2 long → -3
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, 7);  emit_const_wide(c, 2, -2);
        emit_23x(c, opc::DIV_LONG, 4, 0, 2);
        emit_move_result(c, 4, opc::RETURN_WIDE);
        expect_num_ids(e, "dr_div_long_negative_divisor", c, "()J", MethodIds{}, -3.0);
    }
    {   // 7 % -2 long → 1
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, 7);  emit_const_wide(c, 2, -2);
        emit_23x(c, opc::REM_LONG, 4, 0, 2);
        emit_move_result(c, 4, opc::RETURN_WIDE);
        expect_num_ids(e, "dr_rem_long_negative_divisor", c, "()J", MethodIds{}, 1.0);
    }
    {   // 7 / 0 via div-int/lit16 → ArithmeticException (typed catch)
        std::vector<uint16_t> c;
        emit_const(c, 0, 7);
        emit_22s(c, opc::DIV_INT_LIT16, 2, 0, 0);
        emit_move_result(c, 2, opc::RETURN);
        MethodIds mid;
        expect_caught_types(e, "dr_div_int_lit16_zero_throws", c, mid,
                            "Ljava/lang/ArithmeticException;", 559);
    }
    {   // 7 % 0 via rem-int/lit16 → ArithmeticException
        std::vector<uint16_t> c;
        emit_const(c, 0, 7);
        emit_22s(c, opc::REM_INT_LIT16, 2, 0, 0);
        emit_move_result(c, 2, opc::RETURN);
        MethodIds mid;
        expect_caught_types(e, "dr_rem_int_lit16_zero_throws", c, mid,
                            "Ljava/lang/ArithmeticException;", 560);
    }
    {   // rem-int 23x zero divisor → ArithmeticException
        std::vector<uint16_t> c;
        emit_const(c, 0, 7);  emit_const(c, 1, 0);
        emit_23x(c, opc::REM_INT, 2, 0, 1);
        emit_move_result(c, 2, opc::RETURN);
        MethodIds mid;
        expect_caught_types(e, "dr_rem_int_23x_zero_throws", c, mid,
                            "Ljava/lang/ArithmeticException;", 561);
    }
    {   // div-int/2addr zero divisor → ArithmeticException (UNGUARDED C++ UB pre-Pass-2)
        std::vector<uint16_t> c;
        emit_const(c, 0, 7);  emit_const(c, 1, 0);
        c.push_back(w12x(0, 1, opc::DIV_INT_2ADDR));  // v0 = v0 / v1
        emit_move_result(c, 0, opc::RETURN);
        MethodIds mid;
        expect_caught_types(e, "dr_div_int_2addr_zero_throws", c, mid,
                            "Ljava/lang/ArithmeticException;", 562);
    }
}

// ═══════════════════ GROUP SW: switch backward + non-zero first key ═══════════════════
static void group_switch(DalvikExecutionEngine& e) {
    std::cout << "\n[GROUP SW] switch — backward targets + non-zero first_key\n";
    {   // packed-switch with BACKWARD target (case code BEFORE the switch)
        std::vector<uint16_t> c;
        emit_const(c, 1, 7770);                       // pc0..2  case0 body
        c.push_back(w11x(1, opc::RETURN));            // pc3
        emit_const(c, 0, 5);                          // pc4..6  key = 5
        size_t switch_pc = c.size();                  // pc7
        c.push_back(w11x(0, opc::PACKED_SWITCH));     // pc7
        c.push_back(0);                               // pc8  (offset patched below)
        emit_const(c, 0, 999);                        // pc9..11  default
        c.push_back(w11x(0, opc::RETURN));            // pc12
        size_t payload_pc = c.size();                 // pc13
        int32_t to_case0 = 0 - static_cast<int32_t>(switch_pc);       // BACKWARD
        int32_t to_payload = static_cast<int32_t>(payload_pc) - static_cast<int32_t>(switch_pc);
        c[switch_pc + 1] = static_cast<uint16_t>(static_cast<uint32_t>(to_payload) & 0xFFFF);
        c[switch_pc + 2] = static_cast<uint16_t>((static_cast<uint32_t>(to_payload) >> 16) & 0xFFFF);
        c.push_back(0x0100);                          // packed ident
        c.push_back(1);                               // size
        c.push_back(5); c.push_back(0);               // first_key = 5
        c.push_back(static_cast<uint16_t>(static_cast<uint32_t>(to_case0) & 0xFFFF));
        c.push_back(static_cast<uint16_t>((static_cast<uint32_t>(to_case0) >> 16) & 0xFFFF));
        expect_num_ids(e, "sw_packed_backward_target", c, "()I", MethodIds{}, 7770.0);
    }
    {   // packed-switch non-zero first_key (100..102), forward targets, key=101
        std::vector<uint16_t> c;
        emit_const(c, 0, 101);                        // pc0..2 key
        c.push_back(w11x(0, opc::PACKED_SWITCH));     // pc3
        c.push_back(0); c.push_back(0);               // pc4..5 offset patched
        size_t switch_pc = 3;
        emit_const(c, 1, 4321);                       // pc6..8   case 100
        c.push_back(w11x(1, opc::RETURN));            // pc9
        emit_const(c, 1, 8765);                       // pc10..12 case 101
        c.push_back(w11x(1, opc::RETURN));            // pc13
        emit_const(c, 1, 1111);                       // pc14..16 case 102
        c.push_back(w11x(1, opc::RETURN));            // pc17
        emit_const(c, 0, 999);                        // pc18..20 default
        c.push_back(w11x(0, opc::RETURN));            // pc21
        size_t payload_pc = c.size();                 // pc22
        int32_t to_payload = static_cast<int32_t>(payload_pc) - static_cast<int32_t>(switch_pc);
        c[switch_pc + 1] = static_cast<uint16_t>(static_cast<uint32_t>(to_payload) & 0xFFFF);
        c[switch_pc + 2] = static_cast<uint16_t>((static_cast<uint32_t>(to_payload) >> 16) & 0xFFFF);
        c.push_back(0x0100); c.push_back(3);
        c.push_back(100); c.push_back(0);             // first_key = 100 (NON-ZERO)
        int32_t t100 = static_cast<int32_t>(6) - static_cast<int32_t>(switch_pc);
        int32_t t101 = static_cast<int32_t>(10) - static_cast<int32_t>(switch_pc);
        c.push_back(static_cast<uint16_t>(static_cast<uint32_t>(t100) & 0xFFFF));
        c.push_back(static_cast<uint16_t>((static_cast<uint32_t>(t100) >> 16) & 0xFFFF));
        c.push_back(static_cast<uint16_t>(static_cast<uint32_t>(t101) & 0xFFFF));
        c.push_back(static_cast<uint16_t>((static_cast<uint32_t>(t101) >> 16) & 0xFFFF));
        expect_num_ids(e, "sw_packed_nonzero_first_key", c, "()I", MethodIds{}, 8765.0);
    }
    {   // sparse-switch with BACKWARD target for key 7
        std::vector<uint16_t> c;
        emit_const(c, 1, 6110);                       // pc0..2 case for key 7
        c.push_back(w11x(1, opc::RETURN));            // pc3
        emit_const(c, 0, 7);                          // pc4..6 key
        size_t switch_pc = c.size();                  // pc7
        c.push_back(w11x(0, opc::SPARSE_SWITCH));     // pc7
        c.push_back(0); c.push_back(0);               // pc8..9 offset patched
        emit_const(c, 0, 2222);                       // pc10..12 default
        c.push_back(w11x(0, opc::RETURN));            // pc13
        size_t payload_pc = c.size();                 // pc14
        int32_t to_payload = static_cast<int32_t>(payload_pc) - static_cast<int32_t>(switch_pc);
        c[switch_pc + 1] = static_cast<uint16_t>(static_cast<uint32_t>(to_payload) & 0xFFFF);
        c[switch_pc + 2] = static_cast<uint16_t>((static_cast<uint32_t>(to_payload) >> 16) & 0xFFFF);
        int32_t to_case = 0 - static_cast<int32_t>(switch_pc);        // BACKWARD
        int32_t to_default = static_cast<int32_t>(10) - static_cast<int32_t>(switch_pc);
        c.push_back(0x0200);                          // sparse ident
        c.push_back(2);                               // size
        c.push_back(7);       c.push_back(0);         // key 7
        c.push_back(1000000 & 0xFFFF); c.push_back((1000000 >> 16) & 0xFFFF);  // key 1000000
        c.push_back(static_cast<uint16_t>(static_cast<uint32_t>(to_case) & 0xFFFF));
        c.push_back(static_cast<uint16_t>((static_cast<uint32_t>(to_case) >> 16) & 0xFFFF));
        c.push_back(static_cast<uint16_t>(static_cast<uint32_t>(to_default) & 0xFFFF));
        c.push_back(static_cast<uint16_t>((static_cast<uint32_t>(to_default) >> 16) & 0xFFFF));
        expect_num_ids(e, "sw_sparse_backward_target", c, "()I", MethodIds{}, 6110.0);
    }
}

// ═══════════════════ GROUP PS: parse/string edge matrix ═══════════════════
static void group_parse(DalvikExecutionEngine& e) {
    std::cout << "\n[GROUP PS] parse/substring/concat — Java boundary matrix\n";
    auto parseInt_snippet = [](MethodIds& mid, const std::string& s) {
        uint16_t m = mid.add("Ljava/lang/Integer;", "parseInt");
        uint16_t si = mid.string_idx(s);
        std::vector<uint16_t> c;
        emit_21c(c, opc::CONST_STRING, 1, si);
        emit_invoke(c, opc::INVOKE_STATIC, 1, {1}, m);
        emit_move_result(c, 2, opc::MOVE_RESULT);
        emit_move_result(c, 2, opc::RETURN);
        return c;
    };
    {   // MAX boundary
        MethodIds mid;
        expect_num_ids(e, "ps_parseInt_max_boundary", parseInt_snippet(mid, "2147483647"),
                       "()I", mid, 2147483647.0);
    }
    {   // MIN boundary
        MethodIds mid;
        expect_num_ids(e, "ps_parseInt_min_boundary", parseInt_snippet(mid, "-2147483648"),
                       "()I", mid, -2147483648.0);
    }
    {   // overflow → NumberFormatException
        MethodIds mid;
        expect_caught_types(e, "ps_parseInt_overflow_throws_nfe",
                            parseInt_snippet(mid, "2147483648"), mid,
                            "Ljava/lang/NumberFormatException;", 571);
    }
    {   // empty → NFE
        MethodIds mid;
        expect_caught_types(e, "ps_parseInt_empty_throws_nfe",
                            parseInt_snippet(mid, ""), mid,
                            "Ljava/lang/NumberFormatException;", 572);
    }
    {   // whitespace → NFE (strict Java: no trimming)
        MethodIds mid;
        expect_caught_types(e, "ps_parseInt_whitespace_throws_nfe",
                            parseInt_snippet(mid, " 5"), mid,
                            "Ljava/lang/NumberFormatException;", 573);
    }
    {   // parseDouble exponent + negative
        MethodIds mid;
        uint16_t m = mid.add("Ljava/lang/Double;", "parseDouble");
        uint16_t si = mid.string_idx("-2.5e2");
        std::vector<uint16_t> c;
        emit_21c(c, opc::CONST_STRING, 1, si);
        emit_invoke(c, opc::INVOKE_STATIC, 1, {1}, m);
        emit_move_result(c, 2, opc::MOVE_RESULT_WIDE);
        emit_move_result(c, 2, opc::RETURN_WIDE);
        expect_num_ids(e, "ps_parseDouble_negative_exponent", c, "()D", mid, -250.0);
    }
    {   // parseDouble("NaN") → NaN (Java accepts the word)
        MethodIds mid;
        uint16_t m = mid.add("Ljava/lang/Double;", "parseDouble");
        uint16_t si = mid.string_idx("NaN");
        std::vector<uint16_t> c;
        emit_21c(c, opc::CONST_STRING, 1, si);
        emit_invoke(c, opc::INVOKE_STATIC, 1, {1}, m);
        emit_move_result(c, 2, opc::MOVE_RESULT_WIDE);
        emit_move_result(c, 2, opc::RETURN_WIDE);
        expect_nan_or_inf(e, "ps_parseDouble_nan_word", c, "()D", mid, 0);
    }
    {   // parseDouble("Infinity") → +Inf
        MethodIds mid;
        uint16_t m = mid.add("Ljava/lang/Double;", "parseDouble");
        uint16_t si = mid.string_idx("Infinity");
        std::vector<uint16_t> c;
        emit_21c(c, opc::CONST_STRING, 1, si);
        emit_invoke(c, opc::INVOKE_STATIC, 1, {1}, m);
        emit_move_result(c, 2, opc::MOVE_RESULT_WIDE);
        emit_move_result(c, 2, opc::RETURN_WIDE);
        expect_nan_or_inf(e, "ps_parseDouble_infinity_word", c, "()D", mid, 1);
    }
    auto substring_snippet = [](MethodIds& mid, const std::string& s,
                                int32_t b, int32_t en, bool two_arg) {
        uint16_t m = mid.add("Ljava/lang/String;", "substring");
        uint16_t si = mid.string_idx(s);
        std::vector<uint16_t> c;
        emit_21c(c, opc::CONST_STRING, 0, si);
        emit_const(c, 1, b);
        if (two_arg) emit_const(c, 2, en);
        if (two_arg) emit_invoke(c, opc::INVOKE_VIRTUAL, 3, {0, 1, 2}, m);
        else         emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {0, 1}, m);
        emit_move_result(c, 3, opc::MOVE_RESULT_OBJECT);
        emit_move_result(c, 3, opc::RETURN_OBJECT);
        return c;
    };
    {   // substring(0,2) of "hello" → "he" (beginning)
        MethodIds mid;
        expect_str_ids(e, "ps_substring_beginning", substring_snippet(mid, "hello", 0, 2, true),
                       mid, "he");
    }
    {   // substring(3) of "hello" → "lo" (one-arg tail)
        MethodIds mid;
        expect_str_ids(e, "ps_substring_one_arg_tail", substring_snippet(mid, "hello", 3, 0, false),
                       mid, "lo");
    }
    {   // substring(3,3) of "hello" → "" (empty range is legal)
        MethodIds mid;
        expect_str_ids(e, "ps_substring_empty_range", substring_snippet(mid, "hello", 3, 3, true),
                       mid, "");
    }
    {   // substring(2,1) → StringIndexOutOfBoundsException
        MethodIds mid;
        expect_caught_types(e, "ps_substring_inverted_throws_sioobe",
                            substring_snippet(mid, "hello", 2, 1, true), mid,
                            "Ljava/lang/StringIndexOutOfBoundsException;", 574);
    }
    {   // substring(1,99) → StringIndexOutOfBoundsException
        MethodIds mid;
        expect_caught_types(e, "ps_substring_end_oob_throws_sioobe",
                            substring_snippet(mid, "hello", 1, 99, true), mid,
                            "Ljava/lang/StringIndexOutOfBoundsException;", 575);
    }
    auto concat_snippet = [](MethodIds& mid, const std::string& a, const std::string& bnd) {
        uint16_t m = mid.add("Ljava/lang/String;", "concat");
        uint16_t s1 = mid.string_idx(a);
        uint16_t s2 = mid.string_idx(bnd);
        std::vector<uint16_t> c;
        emit_21c(c, opc::CONST_STRING, 0, s1);
        emit_21c(c, opc::CONST_STRING, 1, s2);
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {0, 1}, m);
        emit_move_result(c, 2, opc::MOVE_RESULT_OBJECT);
        emit_move_result(c, 2, opc::RETURN_OBJECT);
        return c;
    };
    {   // concat with empty receiver side
        MethodIds mid;
        expect_str_ids(e, "ps_concat_empty_first", concat_snippet(mid, "", "x"), mid, "x");
    }
    {   // concat with UTF-8 multibyte content (bytes pass through untouched)
        MethodIds mid;
        expect_str_ids(e, "ps_concat_unicode_bytes", concat_snippet(mid, "h\xc3\xa9llo\xe2\x86\x92", "!"),
                       mid, "h\xc3\xa9llo\xe2\x86\x92!");
    }
}

int main(int argc, char** argv) {
    std::string only = (argc > 1) ? argv[1] : "";
    DalvikExecutionEngine engine;
    if (only.empty() || only == "xml") group_xml(engine);
    if (only.empty() || only == "ar") group_atomic(engine);
    if (only.empty() || only == "st") group_stream(engine);
    if (only.empty() || only == "cv") group_conv(engine);
    if (only.empty() || only == "dr") group_divrem(engine);
    if (only.empty() || only == "sw") group_switch(engine);
    if (only.empty() || only == "ps") group_parse(engine);
    std::cout << "\nRESULT: " << g_pass << " passed, " << g_fail << " failed"
              << (g_skip ? (" (" + std::to_string(g_skip) + " skipped-recorded)") : "")
              << "\n";
    return g_fail == 0 ? 0 : 1;
}
