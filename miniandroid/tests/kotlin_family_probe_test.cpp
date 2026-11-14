// A-R6 KOTLIN FAMILY PROBE — roadmap §8 F (Kotlin/JVM interop) first-ever
// family probe.
//
// Finding source: the A-R6 review (issue transfer, base 1a0fa259). Roadmap
// §8 F1 carries 9 unchecked rows (Unit, Pair, Triple, default arguments,
// synthetic $default, generated component methods, copy, sequence basics —
// audited unchecked at the reconciliation pass); the runtime source has NO
// Kotlin-specific surface (zero shadow registrations for any Lkotlin/*
// class; the only Kotlin-adjacent laws ever landed are Coder-4's W11 spot
// pair — the EXP-045 sanitizeStackTrace gate removal + the bridge-class
// toString in concat — plus the S186e lastIndexOf CHAR fix). The #380
// CONT-11 "Kotlin stdlib semantic backend investigation" never delivered
// its required decision or coverage matrix (its comment trail moved to the
// generic F-NEW-509+ waves).
//
// This probe measures the §8 F1 surface as an engine-level fixture (the
// r25_dispatch_matrix pattern) across the two worlds every real APK runs in:
//
//   WORLD 1 — host-boundary (the Kotlin class is NOT in the DexReport):
//     R8-minified apps and every synthetic/probe report reference kotlin
//     well-known types whose DEX bodies are absent; the engine must answer
//     the Kotlin law or fail loudly — never a silent wrong value.
//     a1 unit identity: Unit.INSTANCE IS Unit.INSTANCE (object law: exactly
//        one instance per engine)
//     a2 unit static-field roundtrip: a Unit reference survives sput/sget
//     b1 Pair component identity: component1()/component2() return the
//        constructor arguments verbatim (kotlin.Pair law)
//     b2 Pair.toString() == "(a, b)" (kotlin.Pair toString law)
//     b3 Triple component3 identity (kotlin.Triple law)
//     d1 Intrinsics.checkNotNullParameter non-null → no-op (must continue)
//     d2 Intrinsics.checkNotNullParameter null → NPE per the Kotlin law
//        (observational: the engine must never answer silent success)
//
//   WORLD 2 — guest-DEX (the interface IS in the report):
//     c1 invoke-interface on a DEFAULT method body declared in the
//        interface itself (the receiver class does not override it) —
//        the $default dispatch precondition
//     c2 the D8 static bridge shape: invoke-static Comp.foo$default(rcv,
//        mask, null) whose body invoke-interfaces into the default body —
//        the exact face the engine's own comments name twice as
//        "invoke-interface dispatch for $default methods (sometimes)
//        fails" (dalvik_engine.cpp EXP-071 sites)
//
// Kotlin law sources (Tier 1): kotlin/Unit object declaration (exactly one
// instance); kotlin/Pair + kotlin/Triple data-class-like semantics
// (constructor args stored verbatim; componentN returns them; Pair.toString
// = "($a, $b)"); kotlin.jvm.internal.Intrinsics.checkNotNullParameter
// throws NullPointerException("Parameter specified as non-null is null: "
// + name) for null and is a no-op otherwise; JVM interface default methods
// execute the interface's own body when the receiver class does not
// override (JVMS invokeinterface; the D8 $default bridge is a plain static
// call into that contract).

#include "../src/dex/dalvik_engine.h"
#include "../src/framework/shadow_registry.h"
#include "../src/framework/heap_adapter.h"

#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dex::ClassInfo;
namespace flw = miniandroid::framework;
using miniandroid::dex::DexFieldId;
using miniandroid::dex::DexMethodId;
using miniandroid::dex::DexReport;
using miniandroid::dex::FieldInfo;
using miniandroid::dex::MethodInfo;

namespace opc {
constexpr uint16_t CONST         = 0x14;  // 31i
constexpr uint16_t CONST_4       = 0x12;  // 11n
constexpr uint16_t CONST_STRING  = 0x1A;  // 21c
constexpr uint16_t MOVE_RESULT   = 0x0A;  // 11x
constexpr uint16_t MOVE_RESULT_OBJECT = 0x0C;  // 11x
constexpr uint16_t RETURN        = 0x0F;  // 11x
constexpr uint16_t RETURN_OBJECT = 0x11;  // 11x
constexpr uint16_t NEW_INSTANCE  = 0x22;  // 21c
constexpr uint16_t SGET           = 0x60;  // 21c
constexpr uint16_t SGET_OBJECT   = 0x62;  // 21c
constexpr uint16_t SPUT          = 0x69;  // 21c
constexpr uint16_t SPUT_OBJECT   = 0x6B;  // 21c
constexpr uint16_t INVOKE_VIRTUAL   = 0x6E;  // 35c
constexpr uint16_t INVOKE_SUPER     = 0x6F;  // 35c
constexpr uint16_t INVOKE_DIRECT    = 0x70;  // 35c
constexpr uint16_t INVOKE_STATIC    = 0x71;  // 35c
constexpr uint16_t INVOKE_INTERFACE = 0x72;  // 35c
constexpr uint16_t IF_EQ = 0x32;  // 22b
constexpr uint16_t IF_NE = 0x33;  // 22b
constexpr uint16_t IF_EQZ = 0x38;  // 21t
}  // namespace opc

static int g_pass = 0, g_fail = 0, g_obs = 0;

static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) { if (g_obs == 0) ++g_pass; }
    else ++g_fail;
}
static void mark_obs() { g_obs = 1; }
static void clear_obs() { g_obs = 0; }

// ── encoders (Dalvik formats; same shape as r25_dispatch_matrix_test) ─────
static uint16_t w11x(uint8_t reg, uint16_t op) {
    return static_cast<uint16_t>((reg << 8) | op);
}
static void emit_new_instance(std::vector<uint16_t>& c, uint8_t reg,
                              uint16_t type_idx) {
    c.push_back(w11x(reg, opc::NEW_INSTANCE));
    c.push_back(type_idx);
}
static void emit_const_string(std::vector<uint16_t>& c, uint8_t reg,
                              uint16_t string_idx) {
    c.push_back(w11x(reg, opc::CONST_STRING));
    c.push_back(string_idx);
}
static void emit_sget_object(std::vector<uint16_t>& c, uint8_t reg,
                             uint16_t field_idx) {
    c.push_back(w11x(reg, opc::SGET_OBJECT));
    c.push_back(field_idx);
}
static void emit_sput(std::vector<uint16_t>& c, uint8_t reg, uint16_t op,
                      uint16_t field_idx) {
    c.push_back(w11x(reg, op));
    c.push_back(field_idx);
}
static void emit_invoke(std::vector<uint16_t>& c, uint16_t op,
                        const std::vector<uint8_t>& regs,
                        uint16_t method_idx) {
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
static void emit_const_4(std::vector<uint16_t>& c, uint8_t reg, int8_t imm) {
    c.push_back(static_cast<uint16_t>(
        (static_cast<uint16_t>(reg & 0x0F) << 8) |
        (static_cast<uint16_t>(imm & 0x0F) << 12) | opc::CONST_4));
}
static void emit_if_ne(std::vector<uint16_t>& c, uint8_t ra, uint8_t rb,
                       int16_t offset) {
    uint16_t word0 = static_cast<uint16_t>(
        (static_cast<uint16_t>(ra & 0x0F) << 8) |
        (static_cast<uint16_t>(rb & 0x0F) << 12) | opc::IF_NE);
    c.push_back(word0);
    c.push_back(static_cast<uint16_t>(offset));
}
static void emit_if_eq(std::vector<uint16_t>& c, uint8_t ra, uint8_t rb,
                       int16_t offset) {
    uint16_t word0 = static_cast<uint16_t>(
        (static_cast<uint16_t>(ra & 0x0F) << 8) |
        (static_cast<uint16_t>(rb & 0x0F) << 12) | opc::IF_EQ);
    c.push_back(word0);
    c.push_back(static_cast<uint16_t>(offset));
}
static void emit_if_eqz(std::vector<uint16_t>& c, uint8_t ra,
                        int16_t offset) {
    c.push_back(w11x(ra, opc::IF_EQZ));
    c.push_back(static_cast<uint16_t>(offset));
}
static void emit_move_result(std::vector<uint16_t>& c, uint8_t reg,
                             bool object) {
    c.push_back(w11x(reg, object ? opc::MOVE_RESULT_OBJECT
                                 : opc::MOVE_RESULT));
}
static void emit_return(std::vector<uint16_t>& c, uint8_t reg, bool object) {
    c.push_back(w11x(reg, object ? opc::RETURN_OBJECT : opc::RETURN));
}

// ── id tables ──────────────────────────────────────────────────────────────
struct Tables {
    std::vector<DexMethodId> method_ids;
    std::vector<DexFieldId> field_ids;
    std::vector<std::string> types;
    std::vector<std::string> strings;

    uint16_t str(const std::string& s) {
        for (size_t i = 0; i < strings.size(); ++i)
            if (strings[i] == s) return static_cast<uint16_t>(i);
        strings.push_back(s);
        return static_cast<uint16_t>(strings.size() - 1);
    }
    uint16_t type(const std::string& t) {
        for (size_t i = 0; i < types.size(); ++i)
            if (types[i] == t) return static_cast<uint16_t>(i);
        types.push_back(t);
        return static_cast<uint16_t>(types.size() - 1);
    }
    uint16_t method(const std::string& cls, const std::string& name) {
        uint16_t ci = type(cls);
        uint16_t ni = str(name);
        method_ids.push_back(DexMethodId{ci, 0, ni});
        return static_cast<uint16_t>(method_ids.size() - 1);
    }
    uint16_t field(const std::string& cls, const std::string& ftype,
                   const std::string& name) {
        uint16_t ci = type(cls);
        uint16_t ti = type(ftype);
        uint16_t ni = str(name);
        field_ids.push_back(DexFieldId{ci, ti, ni});
        return static_cast<uint16_t>(field_ids.size() - 1);
    }
};

static MethodInfo make_static(const std::string& name,
                              const std::string& descriptor,
                              const std::vector<uint16_t>& code) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = descriptor;
    mi.defining_class = "LSemTest;";
    mi.registers_size = 10;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;
    mi.code_offset = 1;  // parsed-MethodInfo fidelity (concrete body)
    return mi;
}

static DexReport build_world(Tables& t) {
    DexReport report;

    // ── WORLD 2 classes ────────────────────────────────────────────────
    // LComp; — interface carrying a DEFAULT body foo()I (sput 42 →
    // LComp;.sState; return 42) + the D8 bridge shape foo$default. The
    // receiver class below does NOT override foo.
    {
        ClassInfo ci;
        ci.name = "LComp;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.access_flags = 0x200;  // ACC_INTERFACE
        MethodInfo foo;
        foo.name = "foo";
        foo.descriptor = "()I";
        foo.defining_class = "LComp;";
        foo.registers_size = 4;
        foo.ins_size = 1;
        foo.outs_size = 1;
        // this at v3 (registers_size - ins_size)
        emit_const(foo.bytecode, 0, 42);
        emit_sput(foo.bytecode, 0, opc::SPUT, t.field("LComp;", "I", "sState"));
        emit_return(foo.bytecode, 0, false);
        foo.code_offset = 1;
        foo.is_abstract = false;  // DEFAULT body — not abstract
        ci.virtual_methods.push_back(foo);
        // The D8 bridge shape (the $default static synthetic): every
        // desugared interface default method carries it. Body: invoke-
        // interface into the DEFAULT body through the receiver argument
        // (the real D8 body additionally tests the mask — this probe's
        // bridge always delegates, which is the face the engine's EXP-071
        // comments name as historically failing).
        MethodInfo bridge;
        bridge.name = "foo$default";
        bridge.descriptor = "(LComp;ILjava/lang/Object;)V";
        bridge.defining_class = "LComp;";
        bridge.registers_size = 4;
        bridge.ins_size = 3;  // static: args at v1 (rcv), v2 (mask), v3 (marker)
        bridge.outs_size = 1;
        emit_invoke(bridge.bytecode, opc::INVOKE_INTERFACE, {1},
                    t.method("LComp;", "foo"));
        bridge.bytecode.push_back(0x0E00);  // return-void
        bridge.code_offset = 1;
        ci.virtual_methods.push_back(bridge);
        // static int sState
        FieldInfo sf;
        sf.name = "sState";
        sf.type = "I";
        sf.defining_class = "LComp;";
        sf.is_static = true;
        ci.static_fields.push_back(sf);
        report.classes.push_back(ci);
    }
    // LImpl; implements LComp; — NO foo override (default must serve).
    // A real D8-produced class always carries the default <init>()V; the
    // F-NEW-274 ctor-less gate would honestly refuse to fabricate an
    // instance otherwise (and the c-rows would fail for the wrong reason).
    {
        ClassInfo ci;
        ci.name = "LImpl;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.interfaces.push_back("LComp;");
        ci.access_flags = 0x1;
        MethodInfo init;
        init.name = "<init>";
        init.descriptor = "()V";
        init.defining_class = "LImpl;";
        init.registers_size = 2;
        init.ins_size = 1;
        init.outs_size = 1;
        init.bytecode.push_back(0x0E00);  // return-void
        init.code_offset = 1;
        ci.direct_methods.push_back(init);
        report.classes.push_back(ci);
    }
    // LHolder; — static Lkotlin/Unit; u (the a2 roundtrip store)
    {
        ClassInfo ci;
        ci.name = "LHolder;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.access_flags = 0x1;
        FieldInfo sf;
        sf.name = "u";
        sf.type = "Lkotlin/Unit;";
        sf.defining_class = "LHolder;";
        sf.is_static = true;
        ci.static_fields.push_back(sf);
        report.classes.push_back(ci);
    }
    // ── LSemTest; — the entry-point class (all rows are static methods) ──
    {
        ClassInfo ci;
        ci.name = "LSemTest;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.access_flags = 0x1;

        // a1_unit_identity()I — Unit.INSTANCE: NON-null (if-eqz guard) AND
        // identical across two sgets (object law) ⇒ 1. The null guard is
        // the discriminator: an unresolved-field world silently answers
        // NULL for both sgets — null==null would pass an identity-only row.
        {
            std::vector<uint16_t> c;
            // layout: 0 sget v0 | 2 if-eqz +10→12 | 4 sget v1 | 6 if-ne +6→12
            //         | 8-10 const 1 | 11 return | 12-14 const 0 | 15 return
            emit_sget_object(c, 0, t.field("Lkotlin/Unit;", "Lkotlin/Unit;",
                                           "INSTANCE"));
            emit_if_eqz(c, 0, 10);  // null → return 0 (word 12)
            emit_sget_object(c, 1, t.field("Lkotlin/Unit;", "Lkotlin/Unit;",
                                           "INSTANCE"));
            emit_if_ne(c, 0, 1, 6);  // not identical → return 0 (word 12)
            emit_const(c, 0, 1);
            emit_return(c, 0, false);
            emit_const(c, 0, 0);
            emit_return(c, 0, false);
            ci.direct_methods.push_back(
                make_static("a1_unit_identity", "()I", c));
        }
        // a2_unit_field_roundtrip()I — Unit.INSTANCE → LHolder;.u → back
        {
            std::vector<uint16_t> c;
            emit_sget_object(c, 0, t.field("Lkotlin/Unit;", "Lkotlin/Unit;",
                                           "INSTANCE"));
            emit_sput(c, 0, opc::SPUT_OBJECT,
                      t.field("LHolder;", "Lkotlin/Unit;", "u"));
            // layout: 0 sget v0 | 2-3 sput u | 4-5 sget v1,u | 6 if-eqz +10→16
            //         | 8-9 sget v2 | 10 if-ne +6→16 | 12-14 const 1 | 15 return
            //         | 16-18 const 0 | 19 return
            emit_sget_object(c, 1, t.field("LHolder;", "Lkotlin/Unit;", "u"));
            emit_if_eqz(c, 1, 10);  // the store lost the reference → 0 (word 16)
            emit_sget_object(c, 2, t.field("Lkotlin/Unit;", "Lkotlin/Unit;",
                                           "INSTANCE"));
            emit_if_ne(c, 1, 2, 6);  // not identical → 0 (word 16)
            emit_const(c, 0, 1);
            emit_return(c, 0, false);
            emit_const(c, 0, 0);
            emit_return(c, 0, false);
            ci.direct_methods.push_back(
                make_static("a2_unit_field_roundtrip", "()I", c));
        }
        // b1_pair_component_identity()I — Pair("L","R"): component1()==arg0
        // and component2()==arg1 (verbatim storage law) ⇒ 1
        {
            std::vector<uint16_t> c;
            emit_const_string(c, 1, t.str("L"));
            emit_const_string(c, 2, t.str("R"));
            emit_new_instance(c, 3, t.type("Lkotlin/Pair;"));
            emit_invoke(c, opc::INVOKE_DIRECT, {3, 1, 2},
                        t.method("Lkotlin/Pair;", "<init>"));
            emit_invoke(c, opc::INVOKE_VIRTUAL, {3},
                        t.method("Lkotlin/Pair;", "component1"));
            emit_move_result(c, 0, true);
            // layout: 13 if-ne v0,v1 +12→25 (component1 ≠ arg0 → 0)
            emit_if_ne(c, 0, 1, 12);
            emit_invoke(c, opc::INVOKE_VIRTUAL, {3},
                        t.method("Lkotlin/Pair;", "component2"));
            emit_move_result(c, 0, true);
            // 19 if-ne v0,v2 +6→25 (component2 ≠ arg1 → 0)
            emit_if_ne(c, 0, 2, 6);
            emit_const(c, 0, 1);
            emit_return(c, 0, false);
            emit_const(c, 0, 0);
            emit_return(c, 0, false);
            ci.direct_methods.push_back(
                make_static("b1_pair_component_identity", "()I", c));
        }
        // b2_pair_tostring()I — Pair("a","b").toString().equals("(a, b)")
        {
            std::vector<uint16_t> c;
            emit_const_string(c, 1, t.str("a"));
            emit_const_string(c, 2, t.str("b"));
            emit_new_instance(c, 3, t.type("Lkotlin/Pair;"));
            emit_invoke(c, opc::INVOKE_DIRECT, {3, 1, 2},
                        t.method("Lkotlin/Pair;", "<init>"));
            emit_invoke(c, opc::INVOKE_VIRTUAL, {3},
                        t.method("Lkotlin/Pair;", "toString"));
            emit_move_result(c, 0, true);
            emit_const_string(c, 1, t.str("(a, b)"));
            emit_invoke(c, opc::INVOKE_VIRTUAL, {0, 1},
                        t.method("Ljava/lang/String;", "equals"));
            emit_move_result(c, 0, false);
            emit_return(c, 0, false);
            ci.direct_methods.push_back(
                make_static("b2_pair_tostring", "()I", c));
        }
        // b3_triple_component3_identity()I — Triple("a","b","c"):
        // component3()==arg2 ⇒ 1
        {
            std::vector<uint16_t> c;
            emit_const_string(c, 1, t.str("a"));
            emit_const_string(c, 2, t.str("b"));
            emit_const_string(c, 3, t.str("c"));
            emit_new_instance(c, 4, t.type("Lkotlin/Triple;"));
            emit_invoke(c, opc::INVOKE_DIRECT, {4, 1, 2, 3},
                        t.method("Lkotlin/Triple;", "<init>"));
            emit_invoke(c, opc::INVOKE_VIRTUAL, {4},
                        t.method("Lkotlin/Triple;", "component3"));
            emit_move_result(c, 0, true);
            // layout: 15 if-ne v0,v3 +6→21 (component3 ≠ arg2 → 0)
            emit_if_ne(c, 0, 3, 6);
            emit_const(c, 0, 1);
            emit_return(c, 0, false);
            emit_const(c, 0, 0);
            emit_return(c, 0, false);
            ci.direct_methods.push_back(
                make_static("b3_triple_component3_identity", "()I", c));
        }
        // c1_iface_default_direct()I — invoke-interface foo()I on a fresh
        // LImpl; (no override — the interface's own default body must run)
        {
            std::vector<uint16_t> c;
            emit_new_instance(c, 0, t.type("LImpl;"));
            emit_invoke(c, opc::INVOKE_DIRECT, {0},
                        t.method("LImpl;", "<init>"));
            emit_invoke(c, opc::INVOKE_INTERFACE, {0},
                        t.method("LComp;", "foo"));
            emit_move_result(c, 0, false);
            emit_return(c, 0, false);
            ci.direct_methods.push_back(
                make_static("c1_iface_default_direct", "()I", c));
        }
        // c2_default_bridge_static()I — the D8 $default bridge shape:
        // invoke-static LComp;.foo$default(LImpl;, 0, null) then sget sState
        {
            std::vector<uint16_t> c;
            emit_new_instance(c, 0, t.type("LImpl;"));
            emit_invoke(c, opc::INVOKE_DIRECT, {0},
                        t.method("LImpl;", "<init>"));
            emit_const_4(c, 1, 0);  // mask 0
            emit_const_4(c, 2, 0);  // null marker
            emit_invoke(c, opc::INVOKE_STATIC, {0, 1, 2},
                        t.method("LComp;", "foo$default"));
            emit_sget_object(c, 0, t.field("LComp;", "I", "sState"));
            // sState is int — use SGET (0x60); fix via dedicated helper below
            ci.direct_methods.push_back(
                make_static("c2_default_bridge_static", "()I", c));
        }
        // d1_intrinsics_nonnull()I — checkNotNullParameter("x","x") then 7
        {
            std::vector<uint16_t> c;
            emit_const_string(c, 0, t.str("x"));
            emit_invoke(c, opc::INVOKE_STATIC, {0, 0},
                        t.method("Lkotlin/jvm/internal/Intrinsics;",
                                 "checkNotNullParameter"));
            emit_const(c, 0, 7);
            emit_return(c, 0, false);
            ci.direct_methods.push_back(
                make_static("d1_intrinsics_nonnull", "()I", c));
        }
        // d2_intrinsics_null_throw()I — checkNotNullParameter(null,"p")
        // (OBSERVATIONAL: the Kotlin law throws NPE)
        {
            std::vector<uint16_t> c;
            emit_const_4(c, 0, 0);  // null
            emit_const_string(c, 1, t.str("p"));
            emit_invoke(c, opc::INVOKE_STATIC, {0, 1},
                        t.method("Lkotlin/jvm/internal/Intrinsics;",
                                 "checkNotNullParameter"));
            emit_const(c, 0, 7);
            emit_return(c, 0, false);
            ci.direct_methods.push_back(
                make_static("d2_intrinsics_null_throw", "()I", c));
        }
        report.classes.push_back(ci);
    }

    report.strings = t.strings;
    report.types = t.types;
    report.method_ids = t.method_ids;
    report.field_ids = t.field_ids;
    return report;
}

static int run_row(DalvikExecutionEngine& engine, DexReport& report,
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
    // KFP_TRACE=1: dump the instruction trace (bounded, census debugging).
    if (std::getenv("KFP_TRACE") != nullptr) {
        std::cerr << "[TRACE] " << method_name << " rows="
                  << r.instruction_traces.size() << std::endl;
        int dumped = 0;
        for (const auto& t : r.instruction_traces) {
            if (dumped++ > 40) break;
            std::cerr << "  pc=" << t.pc_before << " op=" << t.opcode_name
                      << " st=" << static_cast<int>(t.status)
                      << (t.return_value
                              ? std::string(" ret_t=") + std::to_string(
                                    static_cast<int>(t.return_value->type))
                              : std::string())
                      << std::endl;
        }
    }
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
    else if (v.type == T::BOOLEAN)
        *out_val = v.int_val;
    else
        return 0;
    return 1;
}

int main(int argc, char** argv) {
    std::cout << "== kotlin_family_probe — roadmap §8 F1 (A-R6) ==\n";
    bool expect_mode = argc > 1 && std::string(argv[1]) == "--expect";
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 4000;

    // A-R6: the shadow registry (the KotlinShadow dispatch layer) — the
    // ApplicationRuntime wiring pattern (register_platform_shadows +
    // DalvikHeapAdapter over the engine's heap + set_shadow_registry).
    flw::ShadowRegistry registry;
    flw::register_platform_shadows(registry);
    auto heap_adapter = std::make_unique<flw::DalvikHeapAdapter>(
        &engine.get_heap_public(), &engine);
    registry.set_heap(heap_adapter.get());
    engine.set_shadow_registry(&registry);

    Tables t;
    // pre-register every type/method/field (report snapshots at the end)
    static const char* kTypes[] = {
        "Lkotlin/Unit;", "Lkotlin/Pair;", "Lkotlin/Triple;",
        "Lkotlin/jvm/internal/Intrinsics;", "LComp;", "LImpl;", "LHolder;",
        "LSemTest;", "Ljava/lang/Object;", "Ljava/lang/String;"};
    for (const char* s : kTypes) t.type(s);
    // methods invoked
    t.method("Lkotlin/Pair;", "<init>");
    t.method("Lkotlin/Pair;", "component1");
    t.method("Lkotlin/Pair;", "component2");
    t.method("Lkotlin/Pair;", "toString");
    t.method("Lkotlin/Triple;", "<init>");
    t.method("Lkotlin/Triple;", "component3");
    t.method("Ljava/lang/String;", "equals");
    t.method("LImpl;", "<init>");
    t.method("LComp;", "foo");
    t.method("LComp;", "foo$default");
    t.method("Lkotlin/jvm/internal/Intrinsics;", "checkNotNullParameter");
    // fields accessed
    t.field("Lkotlin/Unit;", "Lkotlin/Unit;", "INSTANCE");
    t.field("LHolder;", "Lkotlin/Unit;", "u");
    t.field("LComp;", "I", "sState");

    DexReport report = build_world(t);

    // c2's body uses SGET (int) — patch the opcode in place (0x60 = sget)
    for (auto& ci : report.classes) {
        if (ci.name != "LSemTest;") continue;
        for (auto& m : ci.direct_methods) {
            if (m.name != "c2_default_bridge_static") continue;
            for (size_t i = 0; i + 1 < m.bytecode.size(); ++i) {
                if ((m.bytecode[i] & 0xFF) == opc::SGET_OBJECT &&
                    m.bytecode[i + 1] ==
                        t.field("LComp;", "I", "sState"))
                    m.bytecode[i] = static_cast<uint16_t>(opc::SGET);
            }
        }
    }

    struct Row {
        const char* name;
        int64_t expect;
        bool observational;
    };
    static const Row rows[] = {
        {"a1_unit_identity", 1, false},
        {"a2_unit_field_roundtrip", 1, false},
        {"b1_pair_component_identity", 1, false},
        {"b2_pair_tostring", 1, false},
        {"b3_triple_component3_identity", 1, false},
        {"c1_iface_default_direct", 42, false},
        {"c2_default_bridge_static", 42, false},
        {"d1_intrinsics_nonnull", 7, false},
        {"d2_intrinsics_null_throw", 0, true},  // law: throws NPE
    };

    for (const auto& row : rows) {
        int64_t got = 0;
        std::string status;
        int rc = run_row(engine, report, row.name, &got, &status);
        if (row.observational) {
            mark_obs();
            std::string detail =
                rc == 1
                    ? "returned " + std::to_string(got) +
                          " (Kotlin law: checkNotNullParameter(null) throws "
                          "NullPointerException)"
                    : "no-return status=" + status +
                          " (Kotlin law: NPE — a throw is the CORRECT face)";
            std::cout << "  OBS   " << row.name << " — " << detail << "\n";
            clear_obs();
            continue;
        }
        bool ok = (rc == 1) && (got == row.expect);
        std::string detail = "expected " + std::to_string(row.expect) +
                             ", got " +
                             (rc == 1 ? std::to_string(got)
                                      : "<no-return status=" + status + ">");
        if (expect_mode) {
            record(row.name, ok, detail);
        } else {
            // census mode: record behavior without gating
            std::cout << "  CENSUS " << row.name << " — " << detail << "\n";
        }
    }

    if (expect_mode)
        std::cout << "\n== " << g_pass << " passed / " << g_fail
                  << " failed ==\n";
    return expect_mode ? (g_fail == 0 ? 0 : 1) : 0;
}
