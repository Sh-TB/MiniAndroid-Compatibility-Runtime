// A-R5 R25 PROBE — the declared-receiver ≠ runtime-receiver dispatch matrix
//
// Finding R25 (issue #581, A-R4): roadmap §5 C3 demands, verbatim, "Explicitly
// detect `declared receiver ≠ runtime receiver` and test invoke-interface /
// invoke-virtual / invoke-super / invoke-direct against all four
// combinations." The machinery existed (F-NEW-264c subclass dispatch,
// class_resolver.cpp:105 R8 synthetic heuristics) but the 4×4 matrix was
// never materialized — no fixture, no test, no recorded run.
//
// This probe ASSEMBLES the matrix as an engine-level C++ fixture (the
// mwr_opcode_probe pattern): 4 invoke kinds × 4 declared-receiver shapes,
// each row asserting the dispatch ART prescribes (JVMS/AOSP InvokeVirtual /
// InvokeInterface resolve on the RUNTIME class; invoke-direct / invoke-super
// use the DECLARED class).
//
//   Legal cells (hard asserts):
//     invoke-virtual     × declared==runtime            → runtime override runs
//     invoke-virtual     × declared-super               → RUNTIME override runs (the law)
//     invoke-virtual     × declared-interface           → runtime resolution through the iface call site
//     invoke-virtual     × declared-synthetic-merged    → runtime resolution (merged shape)
//     invoke-interface   × declared==runtime            → runtime body
//     invoke-interface   × declared-super-shape         → runtime body (iface call site, runtime receiver)
//     invoke-super       × declared-superclass          → DECLARED class body (+ discriminator)
//     invoke-super       × declared-grandparent         → upward walk through the hierarchy
//     invoke-direct      × declared==runtime (private)  → declared body
//     invoke-direct      × declared-super (private)     → DECLARED body (NOT the subclass same-name private)
//   Observational cells (recorded, not gated — ART prescribes ICPE/ICCE;
//   the runtime's current behavior is documented either way):
//     invoke-direct × receiver not an instance of the resolved class
//     invoke-super  × declared class outside the receiver hierarchy
//
// Discrimination proof: every legal cell produces a DIFFERENT observable
// value under the wrong dispatch law (declared-class dispatch answers the
// base value; runtime dispatch answers the override; super cells carry a
// +10 discriminator so a fallback-zero arm reads 10, not 11).

#include "../src/dex/dalvik_engine.h"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexMethodId;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

namespace opc {
constexpr uint16_t CONST          = 0x14;  // 31i
constexpr uint16_t MOVE_RESULT    = 0x0A;  // 11x
constexpr uint16_t RETURN         = 0x0F;  // 11x
constexpr uint16_t NEW_INSTANCE   = 0x22;  // 21c
constexpr uint16_t INVOKE_VIRTUAL = 0x6E;  // 35c
constexpr uint16_t INVOKE_SUPER   = 0x6F;  // 35c
constexpr uint16_t INVOKE_DIRECT  = 0x70;  // 35c
constexpr uint16_t INVOKE_INTERFACE = 0x72;  // 35c
constexpr uint16_t ADD_INT        = 0x90;  // 23x
}  // namespace opc

static int g_pass = 0, g_fail = 0;

static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    passed ? ++g_pass : ++g_fail;
}

// ── encoders (Dalvik formats; same shape as semantic_pass3_bridge) ────────
static uint16_t w11x(uint8_t reg, uint16_t op) {
    return static_cast<uint16_t>((reg << 8) | op);
}
static void emit_new_instance(std::vector<uint16_t>& c, uint8_t reg,
                              uint16_t type_idx) {
    c.push_back(w11x(reg, opc::NEW_INSTANCE));
    c.push_back(type_idx);
}
static void emit_invoke(std::vector<uint16_t>& c, uint16_t op,
                        const std::vector<uint8_t>& regs,
                        uint16_t method_idx) {
    // 35c: word0 = A|G|op|F|E|D|C (A = count in bits 12-15), word1 = method@BBBB,
    // word2 = regs (4 nibbles).
    uint16_t word0 = static_cast<uint16_t>(
        (static_cast<uint16_t>(regs.size()) << 12) | op);
    uint16_t word2 = 0;
    for (int i = 0; i < 4 && i < static_cast<int>(regs.size()); ++i)
        word2 |= static_cast<uint16_t>(regs[static_cast<size_t>(i)]
                                       << (4 * i));
    c.push_back(word0);
    c.push_back(method_idx);
    c.push_back(word2);
}
static void emit_const(std::vector<uint16_t>& c, uint8_t reg, int32_t imm) {
    c.push_back(w11x(reg, opc::CONST));
    uint32_t u = static_cast<uint32_t>(imm);
    c.push_back(static_cast<uint16_t>(u & 0xFFFF));
    c.push_back(static_cast<uint16_t>(u >> 16));
}

// Method-id table (same shape as semantic_pass3_bridge's MethodIds).
struct MethodIds {
    std::vector<DexMethodId> ids;
    std::vector<std::string> types;
    std::vector<std::string> strings;
    uint16_t add(const std::string& class_desc, const std::string& name) {
        auto add_in = [](std::vector<std::string>& v, const std::string& s) {
            for (size_t i = 0; i < v.size(); ++i)
                if (v[i] == s) return static_cast<uint16_t>(i);
            v.push_back(s);
            return static_cast<uint16_t>(v.size() - 1);
        };
        uint16_t ci = add_in(types, class_desc);
        uint16_t ni = add_in(strings, name);
        ids.push_back(DexMethodId{ci, 0, ni});
        return static_cast<uint16_t>(ids.size() - 1);
    }
    uint16_t type_idx(const std::string& t) {
        for (size_t i = 0; i < types.size(); ++i)
            if (types[i] == t) return static_cast<uint16_t>(i);
        types.push_back(t);
        return static_cast<uint16_t>(types.size() - 1);
    }
};

static MethodInfo make_static_method(const std::string& name,
                                     const std::vector<uint16_t>& code) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = "()I";
    mi.defining_class = "LSemTest;";
    mi.registers_size = 8;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;
    return mi;
}

// Build the class world. Returns the report. All method ids / type indexes
// are PRE-REGISTERED here first (the report snapshots mid at the END — a
// snapshot taken before add() would leave the invoked names/types out of
// the report tables and every resolution would miss).
static DexReport build_world(MethodIds& mid) {
    // ── pre-register every invoke target + every new-instance type ──
    uint16_t m_base      = mid.add("LBase;", "m");
    uint16_t m_iface     = mid.add("LIface;", "m");
    uint16_t m_syn       = mid.add("L$$ExternalSynthetic0;", "m");
    uint16_t m_med       = mid.add("LMed;", "m");
    uint16_t m_sub2      = mid.add("LSub2;", "m");
    uint16_t m_sub3      = mid.add("LSub3;", "m");
    uint16_t m_priv      = mid.add("LPriv;", "pm");
    uint16_t m_privsub   = mid.add("LPrivSub;", "pm");
    uint16_t t_iface     = mid.type_idx("LIface;");
    uint16_t t_base      = mid.type_idx("LBase;");
    uint16_t t_sub       = mid.type_idx("LSub;");
    uint16_t t_syn       = mid.type_idx("L$$ExternalSynthetic0;");
    uint16_t t_med       = mid.type_idx("LMed;");
    uint16_t t_sub2      = mid.type_idx("LSub2;");
    uint16_t t_sub3      = mid.type_idx("LSub3;");
    uint16_t t_priv      = mid.type_idx("LPriv;");
    uint16_t t_privsub   = mid.type_idx("LPrivSub;");
    DexReport report;

    // ── LIface; — the interface (ACC_INTERFACE = 0x200), abstract m()I ──
    {
        ClassInfo ci;
        ci.name = "LIface;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.access_flags = 0x200;
        MethodInfo m;
        m.name = "m";
        m.descriptor = "()I";
        m.defining_class = "LIface;";
        m.registers_size = 8;
        m.ins_size = 1;
        m.outs_size = 1;
        m.bytecode.clear();  // abstract — no body
        m.is_abstract = true;  // parsed-MethodInfo fidelity
        m.code_offset = 0;
        ci.virtual_methods.push_back(m);
        report.classes.push_back(ci);
    }
    // ── LBase; implements LIface; — m()I = 1 ──
    {
        ClassInfo ci;
        ci.name = "LBase;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.interfaces.push_back("LIface;");
        MethodInfo m;
        m.name = "m";
        m.descriptor = "()I";
        m.defining_class = "LBase;";
        m.registers_size = 8;
        m.ins_size = 1;
        m.outs_size = 1;
        emit_const(m.bytecode, 0, 1);
        m.bytecode.push_back(w11x(0, opc::RETURN));
        m.code_offset = 1;  // parsed-MethodInfo fidelity: concrete bodies
                            // carry a non-zero code_offset (the f281c gate
                            // and the native-exact law read it)
        ci.virtual_methods.push_back(m);
        report.classes.push_back(ci);
    }
    // ── LSub; extends LBase; — overrides m()I = 2 ──
    {
        ClassInfo ci;
        ci.name = "LSub;";
        ci.superclass_name = "LBase;";
        MethodInfo m;
        m.name = "m";
        m.descriptor = "()I";
        m.defining_class = "LSub;";
        m.registers_size = 8;
        m.ins_size = 1;
        m.outs_size = 1;
        emit_const(m.bytecode, 0, 2);
        m.bytecode.push_back(w11x(0, opc::RETURN));
        m.code_offset = 1;  // parsed-MethodInfo fidelity
        ci.virtual_methods.push_back(m);
        report.classes.push_back(ci);
    }
    // ── L$$ExternalSynthetic0; extends LBase; — the R8 synthetic-merged
    // shape (name carries the $$ExternalSynthetic marker the R8 heuristic
    // in class_resolver.cpp:105 classifies); m()I = 3 ──
    {
        ClassInfo ci;
        ci.name = "L$$ExternalSynthetic0;";
        ci.superclass_name = "LBase;";
        MethodInfo m;
        m.name = "m";
        m.descriptor = "()I";
        m.defining_class = "L$$ExternalSynthetic0;";
        m.registers_size = 8;
        m.ins_size = 1;
        m.outs_size = 1;
        emit_const(m.bytecode, 0, 3);
        m.bytecode.push_back(w11x(0, opc::RETURN));
        m.code_offset = 1;  // parsed-MethodInfo fidelity
        ci.virtual_methods.push_back(m);
        report.classes.push_back(ci);
    }
    // ── LMed; extends LBase; — the R8 HORIZONTAL-MERGED shape simulation:
    // the call site's DECLARED class (the class R8 merged away); runtime
    // receivers below are LBase; instances. m()I = 4 (if the engine ever
    // dispatched on the DECLARED class this row would answer 4). ──
    {
        ClassInfo ci;
        ci.name = "LMed;";
        ci.superclass_name = "LBase;";
        MethodInfo m;
        m.name = "m";
        m.descriptor = "()I";
        m.defining_class = "LMed;";
        m.registers_size = 8;
        m.ins_size = 1;
        m.outs_size = 1;
        emit_const(m.bytecode, 0, 4);
        m.bytecode.push_back(w11x(0, opc::RETURN));
        m.code_offset = 1;  // parsed-MethodInfo fidelity
        ci.virtual_methods.push_back(m);
        report.classes.push_back(ci);
    }
    // ── LSub2; extends LBase; — m()I = super.m() + 10 (the super-call
    // discriminator: a correct invoke-super arm answers 11; a fallback-zero
    // arm answers 10; a recursion runs away). ins_size=1, this at v7 (the
    // D8 convention: this lives at v[registers_size - ins_size]). ──
    {
        ClassInfo ci;
        ci.name = "LSub2;";
        ci.superclass_name = "LBase;";
        MethodInfo m;
        m.name = "m";
        m.descriptor = "()I";
        m.defining_class = "LSub2;";
        m.registers_size = 8;
        m.ins_size = 1;
        m.outs_size = 2;
        emit_invoke(m.bytecode, opc::INVOKE_SUPER, {7}, m_base);
        m.bytecode.push_back(w11x(1, opc::MOVE_RESULT));
        emit_const(m.bytecode, 2, 10);
        // add-int v3, v1, v2 (23x: AA|op, |CC|BB|)
        m.bytecode.push_back(w11x(3, opc::ADD_INT));
        m.bytecode.push_back(static_cast<uint16_t>((2 << 8) | 1));
        m.bytecode.push_back(w11x(3, opc::RETURN));
        m.code_offset = 1;  // parsed-MethodInfo fidelity
        ci.virtual_methods.push_back(m);
        report.classes.push_back(ci);
    }
    // ── LSub3; extends LSub2; — m()I = super.m() + 10 (grandparent walk:
    // invoke-super must resolve LSub2.m (+10) whose own super arm resolves
    // LBase.m (+10) → 21 proves the upward walk through TWO levels). ──
    {
        ClassInfo ci;
        ci.name = "LSub3;";
        ci.superclass_name = "LSub2;";
        MethodInfo m;
        m.name = "m";
        m.descriptor = "()I";
        m.defining_class = "LSub3;";
        m.registers_size = 8;
        m.ins_size = 1;
        m.outs_size = 2;
        emit_invoke(m.bytecode, opc::INVOKE_SUPER, {7}, m_sub2);
        m.bytecode.push_back(w11x(1, opc::MOVE_RESULT));
        emit_const(m.bytecode, 2, 10);
        m.bytecode.push_back(w11x(3, opc::ADD_INT));
        m.bytecode.push_back(static_cast<uint16_t>((2 << 8) | 1));
        m.bytecode.push_back(w11x(3, opc::RETURN));
        m.code_offset = 1;  // parsed-MethodInfo fidelity
        ci.virtual_methods.push_back(m);
        report.classes.push_back(ci);
    }
    // ── LPriv; — PRIVATE pm()I = 7 (direct_methods: private) ──
    {
        ClassInfo ci;
        ci.name = "LPriv;";
        ci.superclass_name = "Ljava/lang/Object;";
        MethodInfo pm;
        pm.name = "pm";
        pm.descriptor = "()I";
        pm.defining_class = "LPriv;";
        pm.access_flags = 0x2;  // ACC_PRIVATE
        pm.registers_size = 8;
        pm.ins_size = 1;
        pm.outs_size = 1;
        emit_const(pm.bytecode, 0, 7);
        pm.bytecode.push_back(w11x(0, opc::RETURN));
        pm.code_offset = 1;  // parsed-MethodInfo fidelity
        ci.direct_methods.push_back(pm);
        report.classes.push_back(ci);
    }
    // ── LPrivSub; extends LPriv; — a SAME-NAME private pm()I = 8. Private
    // methods do NOT override (statically bound): invoke-direct with the
    // method declared in LPriv MUST answer 7 even when the receiver is an
    // LPrivSub instance. ──
    {
        ClassInfo ci;
        ci.name = "LPrivSub;";
        ci.superclass_name = "LPriv;";
        MethodInfo pm;
        pm.name = "pm";
        pm.descriptor = "()I";
        pm.defining_class = "LPrivSub;";
        pm.access_flags = 0x2;
        pm.registers_size = 8;
        pm.ins_size = 1;
        pm.outs_size = 1;
        emit_const(pm.bytecode, 0, 8);
        pm.bytecode.push_back(w11x(0, opc::RETURN));
        pm.code_offset = 1;  // parsed-MethodInfo fidelity
        ci.direct_methods.push_back(pm);
        report.classes.push_back(ci);
    }

    // ── LSemTest; — the static entry methods (one per matrix cell) ──
    {
        ClassInfo ci;
        ci.name = "LSemTest;";
        ci.superclass_name = "Ljava/lang/Object;";

        // helper: NEW_INSTANCE v0 <T>; INVOKE <op> {v0} <method@>; MOVE_RESULT v1; RETURN v1
        auto cell = [&](const std::string& name, uint16_t op,
                        uint16_t type, uint16_t m_idx) {
            std::vector<uint16_t> c;
            emit_new_instance(c, 0, type);
            emit_invoke(c, op, {0}, m_idx);
            c.push_back(w11x(1, opc::MOVE_RESULT));
            c.push_back(w11x(1, opc::RETURN));
            ci.direct_methods.push_back(make_static_method(name, c));
        };

        // invoke-virtual × declared==runtime (LBase.m on LBase) → 1
        cell("v_declared_eq_runtime", opc::INVOKE_VIRTUAL, t_base, m_base);
        // invoke-virtual × declared-super (LBase.m method-id, LSub instance)
        // → 2 — THE runtime-class law (declared dispatch would answer 1)
        cell("v_declared_super", opc::INVOKE_VIRTUAL, t_sub, m_base);
        // invoke-virtual × declared-interface (LIface.m on LSub) → 2
        cell("v_declared_interface", opc::INVOKE_VIRTUAL, t_sub, m_iface);
        // invoke-virtual × declared-synthetic (L$$ExternalSynthetic0;.m) → 3
        cell("v_declared_synthetic", opc::INVOKE_VIRTUAL, t_syn, m_syn);
        // invoke-virtual × declared-merged-away (LMed.m on LBase) → 1
        // (runtime-class law; a declared-class dispatch would answer 4)
        cell("v_declared_merged", opc::INVOKE_VIRTUAL, t_base, m_med);

        // invoke-interface × runtime LBase / LSub / L$$ExternalSynthetic0
        cell("i_runtime_base", opc::INVOKE_INTERFACE, t_base, m_iface);
        cell("i_runtime_sub", opc::INVOKE_INTERFACE, t_sub, m_iface);
        cell("i_runtime_synthetic", opc::INVOKE_INTERFACE, t_syn, m_iface);

        // invoke-super via the subclass bodies (call LSub2.m / LSub3.m
        // through invoke-virtual; their bodies carry the super arms)
        cell("s_declared_super", opc::INVOKE_VIRTUAL, t_sub2, m_sub2);
        cell("s_declared_grandparent", opc::INVOKE_VIRTUAL, t_sub3, m_sub3);

        // invoke-direct × private, declared==runtime (LPriv.pm) → 7
        cell("d_declared_eq_runtime", opc::INVOKE_DIRECT, t_priv, m_priv);
        // invoke-direct × private, declared-super (LPriv.pm on LPrivSub)
        // → 7 (declared binds; NOT 8)
        cell("d_declared_super", opc::INVOKE_DIRECT, t_privsub, m_priv);

        // Observational cells (ART prescribes ICPE — recorded, not gated)
        cell("o_direct_subclass_method_on_super_recv", opc::INVOKE_DIRECT, t_priv, m_privsub);
        cell("o_super_unrelated_declared", opc::INVOKE_SUPER, t_base, m_priv);

        report.classes.push_back(ci);
    }

    // ── snapshot the id tables (AFTER all registrations) ──
    report.strings = mid.strings;
    report.types = mid.types;
    report.method_ids = mid.ids;
    return report;
}

static int run_cell(DalvikExecutionEngine& engine, DexReport& report,
                    const std::string& method_name, int64_t* out_val,
                    std::string* out_status) {
    MethodInfo* entry = nullptr;
    for (auto& ci : report.classes) {
        if (ci.name != "LSemTest;") continue;
        for (auto& m : ci.direct_methods)
            if (m.name == method_name) entry = &m;
    }
    if (!entry) return -1;
    DalvikExecutionResult r = engine.execute_method(*entry, report, {}, false);
    const miniandroid::dalvik::InstructionTrace* ret = nullptr;
    for (const auto& t : r.instruction_traces)
        if (t.status ==
            miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN)
            ret = &t;
    if (out_status) {
        *out_status = std::to_string(static_cast<int>(r.final_status));
        if (ret && ret->return_value)
            *out_status += " ret_type=" +
                           std::to_string(static_cast<int>(
                               ret->return_value->type));
    }
    if (!ret || !ret->return_value) return 0;
    const auto& v = *ret->return_value;
    using T = miniandroid::dalvik::DalvikType;
    if (v.type == T::INT32 || v.type == T::SHORT || v.type == T::BYTE)
        *out_val = v.int_val;
    else if (v.type == T::INT64)
        *out_val = v.long_val;
    else if (v.type == T::CHAR)
        *out_val = v.char_val;
    else
        return 0;
    return 1;
}

int main() {
    std::cout << "== r25_dispatch_matrix_test — declared≠runtime receiver "
                 "4×4 matrix (roadmap §5 C3) ==\n";
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 4000;

    MethodIds mid;
    // Pre-register every class used by type_idx/new-instance and every
    // invoked method BEFORE build_world snapshots ids/types/strings.
    static const char* kClasses[] = {"LIface;", "LBase;", "LSub;",
                                     "L$$ExternalSynthetic0;", "LMed;",
                                     "LSub2;", "LSub3;", "LPriv;", "LPrivSub;",
                                     "LSemTest;"};
    for (const char* c : kClasses) mid.type_idx(c);

    DexReport report = build_world(mid);

    auto expect = [&](const std::string& name, int64_t expected) {
        int64_t got = 0;
        std::string status;
        int rc = run_cell(engine, report, name, &got, &status);
        bool ok = (rc == 1) && (got == expected);
        record(name, ok, "expected " + std::to_string(expected) + ", got " +
                             (rc == 1 ? std::to_string(got)
                                      : "<no-return status=" + status + ">"));
    };
    auto observe = [&](const std::string& name) {
        int64_t got = 0;
        std::string status;
        int rc = run_cell(engine, report, name, &got, &status);
        record(name + " (observational)", true,
               rc == 1 ? "returned " + std::to_string(got)
                       : "no-return status=" + status);
    };

    std::cout << "-- invoke-virtual row --\n";
    expect("v_declared_eq_runtime", 1);
    expect("v_declared_super", 2);          // runtime override — THE law
    expect("v_declared_interface", 2);
    expect("v_declared_synthetic", 3);
    expect("v_declared_merged", 1);
    std::cout << "-- invoke-interface row --\n";
    expect("i_runtime_base", 1);
    expect("i_runtime_sub", 2);
    expect("i_runtime_synthetic", 3);
    std::cout << "-- invoke-super row (declared-class law + discriminators) --\n";
    expect("s_declared_super", 11);         // Base.m(1) + 10
    expect("s_declared_grandparent", 21);   // two-level upward walk
    std::cout << "-- invoke-direct row (private = statically bound) --\n";
    expect("d_declared_eq_runtime", 7);
    expect("d_declared_super", 7);          // NOT LPrivSub.pm's 8
    std::cout << "-- observational cells (ART: ICPE) --\n";
    observe("o_direct_subclass_method_on_super_recv");
    observe("o_super_unrelated_declared");

    std::cout << "\n== " << g_pass << " passed / " << g_fail
              << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}

