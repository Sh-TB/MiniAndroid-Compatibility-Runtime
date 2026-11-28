// f714_measurespec_law_test.cpp — F-NEW-714 regression fence.
//
// Root cause (name.livitski n-Puzzle original APK, W12): the app's custom
// RelativeLayout override GamePlay$1.onMeasure runs real bytecode and calls
// View$MeasureSpec.getSize — the runtime had NO law for the MeasureSpec
// statics, the typed default answered 0, and the resize math collapsed
// (resizeContent never scaled the board; trace /tmp/w12_f9_npuzzle.log,
// 2026-11-18). A first-cut guard also read args[1] although the MeasureSpec
// methods are STATIC (args[0] is the first parameter) — pinned here too.
//
// Laws pinned (AOSP View.java$MeasureSpec):
//   T1  getSize(AT_MOST|1080) == 1080 (mask strips the mode bits).
//   T2  getMode(EXACTLY|1920) == 0x40000000 (1073741824) — the AOSP MODE
//       BIT PATTERN, never a 0/1/2 index. T279 fix 2026-11-28: the shadow
//       returned (spec>>30)&3; androidx compose
//       AndroidComposeView.convertMeasureSpec compares the mode against the
//       real constants and its else arm throws IllegalStateException —
//       ac.stresa.uturn dex pc=0x48, app.wocheneinkauf, app.simple.peri all
//       died there every measure pass ("Compose measure frontier").
//   T3  getMode(AT_MOST|1080) == 0x80000000 (int32 -2147483648);
//       getMode(UNSPECIFIED|77) == 0.
//   T4  makeMeasureSpec(1080, EXACTLY=0x40000000) == 0x40000000|1080 (size
//       FIRST, mode second; AOSP mask form (size & ~MODE_MASK) |
//       (mode & MODE_MASK)); T4b makeMeasureSpec(1080, 1) == 1080 (an
//       index-encoded "mode" degenerates to UNSPECIFIED under the AOSP mask
//       law — index inputs are not platform-legal).
//   T5  round-trip getSize(makeMeasureSpec(1920, AT_MOST=0x80000000)) == 1920.
//   T6  makeSafeMeasureSpec(1080, UNSPECIFIED) == 0 (AOSP safety clamp).
//   T7  COMPOSE FENCE (T279): getMode(EXACTLY|56) == 0x40000000 — the exact
//       spec shape internalOnMeasure$ui feeds convertMeasureSpec; mode must
//       never come back as 1 or the compose when() hits throw ISE.
//
// Harness pattern follows tests/f709_filedescriptor_law_test.cpp (S-61).
#include "../src/dex/dalvik_engine_impl.h"

#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexMethodId;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

namespace opc {
constexpr uint16_t CONST           = 0x14;  // 31i
constexpr uint16_t MOVE_RESULT     = 0x0A;
constexpr uint16_t RETURN          = 0x0F;
constexpr uint16_t INVOKE_STATIC   = 0x71;  // 35c
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
static void emit_move_result(std::vector<uint16_t>& c, uint8_t reg) {
    c.push_back(w11x(reg, opc::MOVE_RESULT));
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
};

static MethodIds mid_shared;

static const miniandroid::dalvik::InstructionTrace* find_return(const DalvikExecutionResult& r) {
    for (const auto& t : r.instruction_traces)
        if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) return &t;
    return nullptr;
}

static DalvikExecutionResult run_snippet(DalvikExecutionEngine& e,
                                         const std::vector<uint16_t>& code,
                                         const std::string& name,
                                         const std::string& desc,
                                         const MethodIds& mid) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = desc;
    mi.defining_class = "LF714Test;";
    mi.registers_size = 24;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;
    DexReport report;
    report.strings = mid.strings;
    report.types = mid.types;
    report.method_ids = mid.ids;
    report.types.push_back("LF714Test;");
    report.strings.push_back("LF714Test;");
    ClassInfo ci;
    ci.name = "LF714Test;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);
    return e.execute_method(ci.direct_methods[0], report, {}, false);
}

static void expect_static(DalvikExecutionEngine& e, const char* name,
                          uint16_t mm, const char* method, size_t nargs,
                          int32_t a0, int32_t a1, double expected) {
    std::vector<uint16_t> c;
    emit_const(c, 1, a0);
    if (nargs > 1) emit_const(c, 2, a1);
    emit_invoke(c, opc::INVOKE_STATIC, static_cast<uint8_t>(nargs),
                nargs > 1 ? std::vector<uint8_t>{1, 2}
                          : std::vector<uint8_t>{1},
                mm);
    emit_move_result(c, 0);
    c.push_back(w11x(0, opc::RETURN));
    DalvikExecutionResult r = run_snippet(e, c, name, "(I)I", mid_shared);
    const auto* ret = find_return(r);
    double got = ret && ret->return_value
                     ? static_cast<double>(ret->return_value->int_val)
                     : -99999;
    char hex[16];
    snprintf(hex, sizeof hex, "%x", static_cast<uint32_t>(a0));
    record(name, got == expected,
           std::string(method) + " arg0=0x" + hex + " expected " +
               std::to_string(expected) + " got " + std::to_string(got));
}

int main(int argc, char** argv) {
    std::string only = (argc > 1) ? argv[1] : "";
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 2000;
    // ONE shared method-id table (f709 pattern): the engine binds method
    // ids at first registration; per-row tables would re-use index 0 and
    // every row would resolve to the FIRST registered method name.
    MethodIds& mid = mid_shared;
    uint16_t m_getSize = mid.add("Landroid/view/View$MeasureSpec;", "getSize");
    uint16_t m_getMode = mid.add("Landroid/view/View$MeasureSpec;", "getMode");
    uint16_t m_make    = mid.add("Landroid/view/View$MeasureSpec;", "makeMeasureSpec");
    uint16_t m_makeSafe= mid.add("Landroid/view/View$MeasureSpec;", "makeSafeMeasureSpec");

    const int32_t EXACTLY_1920 = static_cast<int32_t>(0x40000000u | 1920u);
    const int32_t AT_MOST_1080 = static_cast<int32_t>(0x80000000u | 1080u);
    const int32_t UNSPEC_77    = 77;

    if (only.empty() || only == "t1")
        expect_static(engine, "t1_getSize_atmost1080", m_getSize, "getSize", 1,
                      AT_MOST_1080, 0, 1080);
    if (only.empty() || only == "t2")
        expect_static(engine, "t2_getMode_exactly1920", m_getMode, "getMode", 1,
                      EXACTLY_1920, 0, 1073741824.0);
    if (only.empty() || only == "t3") {
        expect_static(engine, "t3a_getMode_atmost1080", m_getMode, "getMode", 1,
                      AT_MOST_1080, 0, -2147483648.0);
        expect_static(engine, "t3b_getMode_unspecified", m_getMode, "getMode", 1,
                      UNSPEC_77, 0, 0);
    }
    if (only.empty() || only == "t4") {
        expect_static(engine, "t4_makeMeasureSpec_size_mode", m_make,
                      "makeMeasureSpec", 2, 1080,
                      static_cast<int32_t>(0x40000000u),
                      static_cast<double>(0x40000000u | 1080u));
        expect_static(engine, "t4b_makeMeasureSpec_index_degenerates", m_make,
                      "makeMeasureSpec", 2, 1080, 1, 1080.0);
    }
    if (only.empty() || only == "t5") {
        // Round-trip: getSize(makeMeasureSpec(1920, AT_MOST)) == 1920 — two
        // static calls chained through registers.
        std::vector<uint16_t> c;
        emit_const(c, 1, 1920);
        emit_const(c, 2, static_cast<int32_t>(0x80000000u));  // AT_MOST pattern
        emit_invoke(c, opc::INVOKE_STATIC, 2, {1, 2}, m_make);
        emit_move_result(c, 3);
        emit_invoke(c, opc::INVOKE_STATIC, 1, {3}, m_getSize);
        emit_move_result(c, 0);
        c.push_back(w11x(0, opc::RETURN));
        DalvikExecutionResult r = run_snippet(engine, c, "t5_roundtrip", "(I)I", mid_shared);
        const auto* ret = find_return(r);
        double got = ret && ret->return_value
                         ? static_cast<double>(ret->return_value->int_val)
                         : -99999;
        record("t5_roundtrip", got == 1920,
               "expected 1920 got " + std::to_string(got));
    }
    if (only.empty() || only == "t6")
        expect_static(engine, "t6_makeSafeMeasureSpec_unspecified",
                      m_makeSafe, "makeSafeMeasureSpec", 2, 1080, 0, 0);
    if (only.empty() || only == "t7")
        // T279 compose fence: the exact spec internalOnMeasure$ui feeds
        // AndroidComposeView.convertMeasureSpec (EXACTLY|56 = 0x40000038).
        // The mode must come back as the EXACTLY bit pattern; 1 (the old
        // index convention) is the uturn/wocheneinkauf/peri ISE.
        expect_static(engine, "t7_getMode_compose_convert_fence", m_getMode,
                      "getMode", 1, static_cast<int32_t>(0x40000000u | 56u),
                      0, 1073741824.0);

    std::printf("\nRESULT: %d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
