// s234_w26_engine_laws_test — the W26 (Coder-4) three-engine-law battery.
//
// The W26 wave (issue #594) landed three laws for the opencalc vc53 face
// (com.darkempire78.opencalculator_53, APK sha256 26426138…). The diff was
// NOT posted (the evidence comment carries images + logs only), so the laws
// were re-implemented on main from the issue body's exact definitions and
// pinned here as executable contracts:
//
//   F-NEW-636 — framework Class-reflection hierarchy parity:
//     * Class.getSuperclass resolves BOOTCLASSPATH classes through the SAME
//       AOSP framework_direct_superclass table the sibling
//       getGenericSuperclass (F-NEW-225c) already uses — one hierarchy, two
//       entry points. Root cause it fixes: Gson $Gson$Types.resolve climbs
//       getSuperclass chains of the TypeToken rawType (j1/a.a); the dex-only
//       handler answered null MID-CHAIN → NPE at the next hop → the factory
//       rethrow → APP-BOUNDARY death (MainActivity.onCreate pc=1871).
//     * Class.getInterfaces serves the F-NEW-236 framework_class_interfaces
//       table for the same world (dex-first precedence kept).
//   F-NEW-637 — OpenJDK StringReader.read law: serve from the source
//     captured at <init> (the "s" field), track __sr_pos, return the char
//     count / 0 iff len==0 (with pos < length) / -1 at EOF (EOF FIRST).
//     Root cause it fixes: Gson JsonReader.fillBuffer exits ONLY on
//     read(char[],int,int) == -1; the generic stub answered 0 → the loop
//     spun to the F084 halt → VirtualMachineError ×2 under --tap.
//   F-NEW-638 — degenerate-container hit-test pass-through: a container
//     WITH CHILDREN and a <=0 box FILLS ITS PARENT for the input walk (the
//     SlidingUpPanelLayout 0x0 box rejected the whole keypad subtree —
//     HITPROBE d=3 id=846 (0,0 0x0) REJECT — and every tap returned
//     target=0); a CHILDLESS 0x0 view keeps rejecting. The F-NEW-373
//     sentinel (-1x-1) fill law is regression-guarded.
//
// Engine rows follow the kotlin-family-probe pattern (hand-assembled Dalvik
// on a synthetic DexReport, world-1 = the framework class is NOT in the
// report); hit rows follow the input_pipeline_law_test synthetic-tree
// pattern (no DEX).

#include "../src/dex/dalvik_engine.h"
#include "../src/framework/shadow_registry.h"
#include "../src/framework/heap_adapter.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/touch_dispatcher.h"

#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
namespace flw = miniandroid::framework;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexFieldId;
using miniandroid::dex::DexMethodId;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

namespace opc {
constexpr uint16_t CONST              = 0x14;  // 31i
constexpr uint16_t CONST_CLASS        = 0x1C;  // 21c
constexpr uint16_t CONST_STRING       = 0x1A;  // 21c
constexpr uint16_t NEW_INSTANCE       = 0x22;  // 21c
constexpr uint16_t NEW_ARRAY          = 0x23;  // 22c
constexpr uint16_t ARRAY_LENGTH       = 0x21;  // 12x
constexpr uint16_t AGET_CHAR          = 0x49;  // 23x (dalvik_engine.h:168)
constexpr uint16_t MOVE_RESULT        = 0x0A;  // 11x
constexpr uint16_t MOVE_RESULT_OBJECT = 0x0C;  // 11x
constexpr uint16_t RETURN             = 0x0F;  // 11x
constexpr uint16_t RETURN_OBJECT      = 0x11;  // 11x
constexpr uint16_t INVOKE_VIRTUAL     = 0x6E;  // 35c
constexpr uint16_t INVOKE_DIRECT      = 0x70;  // 35c
constexpr uint16_t IF_EQZ             = 0x38;  // 21t
constexpr uint16_t IF_NE              = 0x33;  // 22b
}  // namespace opc

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) ++g_pass; else ++g_fail;
}

// ── branch-resolving assembler. Dalvik 21t/22t branch offsets are relative
//    to the BRANCH instruction's own address (the kotlin-probe "+10→12 from
//    pc2" convention). A placeholder branch records the offset-word index;
//    resolve() patches each with target − branch_start.
struct Asm {
    std::vector<uint16_t> c;
    struct Fix { size_t word; size_t target; };  // word = offset-word index
    std::vector<Fix> fixes;

    size_t here() const { return c.size(); }
    void const_(uint8_t reg, int32_t imm) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::CONST));
        uint32_t u = static_cast<uint32_t>(imm);
        c.push_back(static_cast<uint16_t>(u & 0xFFFF));
        c.push_back(static_cast<uint16_t>(u >> 16));
    }
    void const_class(uint8_t reg, uint16_t type_idx) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::CONST_CLASS));
        c.push_back(type_idx);
    }
    void const_string(uint8_t reg, uint16_t str_idx) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::CONST_STRING));
        c.push_back(str_idx);
    }
    void new_instance(uint8_t reg, uint16_t type_idx) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::NEW_INSTANCE));
        c.push_back(type_idx);
    }
    // 22c: B1|A|op CCCC — vA = dest array ref, vB = size register.
    void new_array(uint8_t dest, uint8_t size_reg, uint16_t type_idx) {
        c.push_back(static_cast<uint16_t>((size_reg & 0xF) << 12 |
                                          (dest & 0xF) << 8 | opc::NEW_ARRAY));
        c.push_back(type_idx);
    }
    // 12x: B|A|op — vA = dest length, vB = array ref.
    void array_length(uint8_t dest, uint8_t src) {
        c.push_back(static_cast<uint16_t>(opc::ARRAY_LENGTH |
                                          (src & 0xF) << 12 |
                                          (dest & 0xF) << 8));
    }
    // 23x: AA|op, BB|CC — vAA = dest, vBB = array, vCC = index.
    void aget_char(uint8_t dest, uint8_t arr, uint8_t idx) {
        c.push_back(static_cast<uint16_t>((dest << 8) | opc::AGET_CHAR));
        c.push_back(static_cast<uint16_t>(arr | (idx << 8)));
    }
    // 35c: A|G|op BBBB F|E|D|C.
    void invoke(uint16_t op, const std::vector<uint8_t>& regs,
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
    void move_result(uint8_t reg, bool object) {
        c.push_back(static_cast<uint16_t>(
            (reg << 8) | (object ? opc::MOVE_RESULT_OBJECT
                                 : opc::MOVE_RESULT)));
    }
    void ret(uint8_t reg, bool object) {
        c.push_back(static_cast<uint16_t>(
            (reg << 8) | (object ? opc::RETURN_OBJECT : opc::RETURN)));
    }
    // Placeholder branch — returns the offset-word index to fix later.
    size_t if_eqz_ph(uint8_t reg) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::IF_EQZ));
        c.push_back(0);
        return c.size() - 1;
    }
    size_t if_ne_ph(uint8_t ra, uint8_t rb) {
        c.push_back(static_cast<uint16_t>((ra & 0x0F) << 8 |
                                          (rb & 0x0F) << 12 | opc::IF_NE));
        c.push_back(0);
        return c.size() - 1;
    }
    void fix(size_t word, size_t target) { fixes.push_back({word, target}); }
    void resolve() {
        for (const auto& f : fixes)
            c[f.word] = static_cast<uint16_t>(f.target - (f.word - 1));
    }
};

// ── id tables (the kotlin-family-probe shape) ──────────────────────────────
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
};

static MethodInfo make_static(const std::string& name,
                              const std::string& descriptor,
                              const std::vector<uint16_t>& code) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = descriptor;
    mi.defining_class = "LSemTest;";
    mi.registers_size = 16;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;
    mi.code_offset = 1;
    return mi;
}

// Shared tail: compare v6/v7/v8 against v9/v10/v11 — any mismatch jumps to
// the fail arm; the fall-through returns 1. (Pattern: comparisons FIRST,
// then the ok arm, then the fail arm — branches patched to the fail arm.)
static void emit_3check_tail(Asm& a, int64_t want6, int64_t want7,
                             int64_t want8) {
    a.const_(9, static_cast<int32_t>(want6));
    a.const_(10, static_cast<int32_t>(want7));
    a.const_(11, static_cast<int32_t>(want8));
    size_t w1 = a.if_ne_ph(6, 9);
    size_t w2r = a.if_ne_ph(7, 10);
    size_t w3 = a.if_ne_ph(8, 11);
    a.const_(0, 1);
    a.ret(0, false);
    size_t fail = a.here();
    a.const_(0, 0);
    a.ret(0, false);
    a.fix(w1, fail);
    a.fix(w2r, fail);
    a.fix(w3, fail);
    a.resolve();
}

static DexReport build_world(Tables& t) {
    DexReport report;
    // The dex-first row's class: LTestDexCls; implements LW26Marker; — IS in
    // the report (and NOT in any framework table) so getInterfaces must
    // answer from the DEX def, not the framework table.
    {
        ClassInfo ci;
        ci.name = "LTestDexCls;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.access_flags = 0x1;
        ci.interfaces.push_back("LW26Marker;");
        report.classes.push_back(ci);
    }
    // LSemTest; — the entry-point class (all rows are static methods).
    {
        ClassInfo ci;
        ci.name = "LSemTest;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.access_flags = 0x1;

        // w1_super_framework()I — getSuperclass(Ljava/util/ArrayList;) is
        // NON-null (AbstractList). The dex-only world answered null here.
        {
            Asm a;
            a.const_class(0, t.type("Ljava/util/ArrayList;"));
            a.invoke(opc::INVOKE_VIRTUAL, {0}, t.method("Ljava/lang/Class;",
                                                        "getSuperclass"));
            a.move_result(1, true);
            size_t w = a.if_eqz_ph(1);
            a.const_(0, 1);
            a.ret(0, false);
            size_t isnull = a.here();
            a.const_(0, 0);
            a.ret(0, false);
            a.fix(w, isnull);
            a.resolve();
            ci.direct_methods.push_back(
                make_static("w1_super_framework", "()I", a.c));
        }
        // w1_super_chain_two_hops()I — super(super(ArrayList)) is non-null
        // (AbstractCollection): the CLIMB terminates like on a JVM.
        {
            Asm a;
            a.const_class(0, t.type("Ljava/util/ArrayList;"));
            a.invoke(opc::INVOKE_VIRTUAL, {0}, t.method("Ljava/lang/Class;",
                                                        "getSuperclass"));
            a.move_result(1, true);
            a.invoke(opc::INVOKE_VIRTUAL, {1}, t.method("Ljava/lang/Class;",
                                                        "getSuperclass"));
            a.move_result(2, true);
            size_t w = a.if_eqz_ph(2);
            a.const_(0, 1);
            a.ret(0, false);
            size_t isnull = a.here();
            a.const_(0, 0);
            a.ret(0, false);
            a.fix(w, isnull);
            a.resolve();
            ci.direct_methods.push_back(
                make_static("w1_super_chain_two_hops", "()I", a.c));
        }
        // w1_object_super_null()I — Object.getSuperclass() IS null (the
        // OpenJDK contract; the table must NOT answer past Object).
        {
            Asm a;
            a.const_class(0, t.type("Ljava/lang/Object;"));
            a.invoke(opc::INVOKE_VIRTUAL, {0}, t.method("Ljava/lang/Class;",
                                                        "getSuperclass"));
            a.move_result(1, true);
            size_t w = a.if_eqz_ph(1);
            a.const_(0, 0);   // non-null (WRONG) → 0
            a.ret(0, false);
            size_t isnull = a.here();
            a.const_(0, 1);   // null (the law) → 1
            a.ret(0, false);
            a.fix(w, isnull);
            a.resolve();
            ci.direct_methods.push_back(
                make_static("w1_object_super_null", "()I", a.c));
        }
        // w1_ifaces_framework()I — getInterfaces(Ljava/util/ArrayList;) has
        // FOUR entries (List / RandomAccess / Cloneable / Serializable —
        // the F-NEW-236 table entry); the row returns the length.
        {
            Asm a;
            a.const_class(0, t.type("Ljava/util/ArrayList;"));
            a.invoke(opc::INVOKE_VIRTUAL, {0}, t.method("Ljava/lang/Class;",
                                                        "getInterfaces"));
            a.move_result(1, true);
            a.array_length(0, 1);
            a.ret(0, false);
            ci.direct_methods.push_back(
                make_static("w1_ifaces_framework", "()I", a.c));
        }
        // w1_ifaces_dex_first()I — getInterfaces(LTestDexCls;) answers from
        // the DEX def (1 entry: LW26Marker;) — dex-first precedence kept.
        {
            Asm a;
            a.const_class(0, t.type("LTestDexCls;"));
            a.invoke(opc::INVOKE_VIRTUAL, {0}, t.method("Ljava/lang/Class;",
                                                        "getInterfaces"));
            a.move_result(1, true);
            a.array_length(0, 1);
            a.ret(0, false);
            ci.direct_methods.push_back(
                make_static("w1_ifaces_dex_first", "()I", a.c));
        }
        // s1a/s1b/s1c — the three s1 faces split for diagnosis:
        //   a: read([C,0,4) returns 3 (the count)
        //   b: array[0] carries 'a' (97)
        //   c: the NEXT read returns -1 (EOF — the fillBuffer termination)
        {
            Asm a;
            a.const_string(1, t.str("abc"));
            a.new_instance(0, t.type("Ljava/io/StringReader;"));
            a.invoke(opc::INVOKE_DIRECT, {0, 1},
                     t.method("Ljava/io/StringReader;", "<init>"));
            a.const_(2, 4);
            a.new_array(3, 2, t.type("[C"));
            a.const_(4, 0);
            a.const_(5, 4);
            a.invoke(opc::INVOKE_VIRTUAL, {0, 3, 4, 5},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(6, false);
            a.ret(6, false);
            ci.direct_methods.push_back(
                make_static("s1a_read_count", "()I", a.c));
        }
        {
            Asm a;
            a.const_string(1, t.str("abc"));
            a.new_instance(0, t.type("Ljava/io/StringReader;"));
            a.invoke(opc::INVOKE_DIRECT, {0, 1},
                     t.method("Ljava/io/StringReader;", "<init>"));
            a.const_(2, 4);
            a.new_array(3, 2, t.type("[C"));
            a.const_(4, 0);
            a.const_(5, 4);
            a.invoke(opc::INVOKE_VIRTUAL, {0, 3, 4, 5},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(6, false);
            a.aget_char(7, 3, 4);
            a.ret(7, false);
            ci.direct_methods.push_back(
                make_static("s1b_read_content", "()I", a.c));
        }
        {
            Asm a;
            a.const_string(1, t.str("abc"));
            a.new_instance(0, t.type("Ljava/io/StringReader;"));
            a.invoke(opc::INVOKE_DIRECT, {0, 1},
                     t.method("Ljava/io/StringReader;", "<init>"));
            a.const_(2, 4);
            a.new_array(3, 2, t.type("[C"));
            a.const_(4, 0);
            a.const_(5, 4);
            a.invoke(opc::INVOKE_VIRTUAL, {0, 3, 4, 5},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(6, false);
            a.invoke(opc::INVOKE_VIRTUAL, {0, 3, 4, 5},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(7, false);
            a.ret(7, false);
            ci.direct_methods.push_back(
                make_static("s1c_read_eof", "()I", a.c));
        }
        // s1_read_cii_eof_content()I — StringReader("abc"): read([C,0,4)
        // returns 3 and writes 'a' at [0]; the NEXT read returns -1 (the
        // fillBuffer termination face).
        {
            Asm a;
            a.const_string(1, t.str("abc"));
            a.new_instance(0, t.type("Ljava/io/StringReader;"));
            a.invoke(opc::INVOKE_DIRECT, {0, 1},
                     t.method("Ljava/io/StringReader;", "<init>"));
            a.const_(2, 4);
            a.new_array(3, 2, t.type("[C"));
            a.const_(4, 0);
            a.const_(5, 4);
            a.invoke(opc::INVOKE_VIRTUAL, {0, 3, 4, 5},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(6, false);
            a.aget_char(7, 3, 4);
            a.invoke(opc::INVOKE_VIRTUAL, {0, 3, 4, 5},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(8, false);
            emit_3check_tail(a, 3, 97, -1);
            ci.direct_methods.push_back(
                make_static("s1_read_cii_eof_content", "()I", a.c));
        }
        // s2_read_len0_then_char()I — StringReader("ab"): read([C,0,0)
        // returns 0 WITHOUT consuming (pos < length, len==0); the follow-up
        // read() returns 'a' (97) — pos untouched by the zero-length call.
        {
            Asm a;
            a.const_string(1, t.str("ab"));
            a.new_instance(0, t.type("Ljava/io/StringReader;"));
            a.invoke(opc::INVOKE_DIRECT, {0, 1},
                     t.method("Ljava/io/StringReader;", "<init>"));
            a.const_(2, 2);
            a.new_array(3, 2, t.type("[C"));
            a.const_(4, 0);
            a.const_(5, 0);
            a.invoke(opc::INVOKE_VIRTUAL, {0, 3, 4, 5},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(6, false);
            a.invoke(opc::INVOKE_VIRTUAL, {0},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(7, false);
            a.const_(9, 0);
            a.const_(10, 97);
            size_t w1 = a.if_ne_ph(6, 9);
            size_t w2 = a.if_ne_ph(7, 10);
            a.const_(0, 1);
            a.ret(0, false);
            size_t fail = a.here();
            a.const_(0, 0);
            a.ret(0, false);
            a.fix(w1, fail);
            a.fix(w2, fail);
            a.resolve();
            ci.direct_methods.push_back(
                make_static("s2_read_len0_then_char", "()I", a.c));
        }
        // s3_read_single_char_chain()I — read() ×3 on "hi": 104, 105, -1.
        {
            Asm a;
            a.const_string(1, t.str("hi"));
            a.new_instance(0, t.type("Ljava/io/StringReader;"));
            a.invoke(opc::INVOKE_DIRECT, {0, 1},
                     t.method("Ljava/io/StringReader;", "<init>"));
            a.invoke(opc::INVOKE_VIRTUAL, {0},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(6, false);
            a.invoke(opc::INVOKE_VIRTUAL, {0},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(7, false);
            a.invoke(opc::INVOKE_VIRTUAL, {0},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(8, false);
            emit_3check_tail(a, 104, 105, -1);
            ci.direct_methods.push_back(
                make_static("s3_read_single_char_chain", "()I", a.c));
        }
        // s1f_read_return_array()Ljava/lang/Object; — diagnostic: run ONE
        // read([CII) and RETURN THE ARRAY OBJECT so main() can probe the
        // heap fields directly (write-side vs read-side localization).
        {
            Asm a;
            a.const_string(1, t.str("abc"));
            a.new_instance(0, t.type("Ljava/io/StringReader;"));
            a.invoke(opc::INVOKE_DIRECT, {0, 1},
                     t.method("Ljava/io/StringReader;", "<init>"));
            a.const_(2, 4);
            a.new_array(3, 2, t.type("[C"));
            a.const_(4, 0);
            a.const_(5, 4);
            a.invoke(opc::INVOKE_VIRTUAL, {0, 3, 4, 5},
                     t.method("Ljava/io/StringReader;", "read"));
            a.move_result(6, false);
            a.ret(3, true);
            MethodInfo mi = make_static("s1f_read_return_array",
                                        "()[B", a.c);
            mi.descriptor = "()[C";
            ci.direct_methods.push_back(mi);
        }
        report.classes.push_back(ci);
    }
    report.strings = t.strings;
    report.types = t.types;
    report.method_ids = t.method_ids;
    report.field_ids = t.field_ids;
    return report;
}

static int run_row_ex(DalvikExecutionEngine& engine, DexReport& report,
                      const std::string& method_name, int64_t* out_val,
                      uint32_t* out_obj) {
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
    if (!ret || !ret->return_value) return 0;
    const auto& v = *ret->return_value;
    using T = miniandroid::dalvik::DalvikType;
    if (v.type == T::INT32 || v.type == T::SHORT || v.type == T::BYTE)
        *out_val = v.int_val;
    else if (v.type == T::CHAR)
        *out_val = v.char_val;
    else if (v.type == T::BOOLEAN)
        *out_val = v.int_val;
    else if (v.type == T::OBJECT_REF) {
        if (out_obj) *out_obj = v.object_id;
        return 2;
    } else
        return 0;
    return 1;
}

static int run_row(DalvikExecutionEngine& engine, DexReport& report,
                   const std::string& method_name, int64_t* out_val) {
    return run_row_ex(engine, report, method_name, out_val, nullptr);
}

// ── F-NEW-638: the synthetic-tree rows (input_pipeline pattern, no DEX) ────
static void run_hit_rows() {
    // h1: the W26 face — a 0x0 container WITH a real-box clickable child.
    // BEFORE the law the panel rejected the whole subtree → target=0;
    // AFTER, the panel fills its parent for the walk and the button claims.
    {
        flw::ViewShadow views;
        flw::HandlerShadow handler;
        flw::TouchDispatcher dispatcher{&views, &handler};
        auto* root = views.get_or_create_node(
            1, "Landroid/widget/FrameLayout;");
        root->x = 0; root->y = 0; root->width = 1080; root->height = 1920;
        auto* panel = views.get_or_create_node(
            2, "Lcom/sothree/slidinguppanel/SlidingUpPanelLayout;");
        panel->x = 0; panel->y = 0; panel->width = 0; panel->height = 0;
        views.add_child(1, 2);
        auto* btn = views.get_or_create_node(3, "Landroid/widget/Button;");
        btn->x = 150; btn->y = 1005; btn->width = 259; btn->height = 230;
        btn->clickable = true;
        views.add_child(2, 3);
        uint32_t clicked = 0;
        dispatcher.set_click_dispatch(
            [&](uint32_t id, float, float) { clicked = id; return true; });
        dispatcher.dispatch(1, {flw::TouchAction::DOWN, 279, 1120});
        bool down_ok = dispatcher.gesture_target() == 3;
        dispatcher.dispatch(1, {flw::TouchAction::UP, 279, 1120});
        // PerformClick posts on the virtual queue at the UP instant — drain
        // it the way the runtime does (advance + drain_ready + fire).
        handler.advance_virtual(1);
        std::vector<uint32_t> due;
        size_t n = handler.drain_ready(&due);
        for (uint32_t id : due)
            dispatcher.fire_framework_callback(id, nullptr);
        record("h1_degenerate_container_pass_through",
               down_ok && clicked == 3 && n >= 1,
               "target_ok=" + std::to_string(down_ok) +
                   " drained=" + std::to_string(n) +
                   " clicked=" + std::to_string(clicked));
    }
    // h2: the honest side of the law — a CHILDLESS 0x0 view keeps rejecting
    // (a truly empty view has no touchable area).
    {
        flw::ViewShadow views;
        flw::HandlerShadow handler;
        flw::TouchDispatcher dispatcher{&views, &handler};
        auto* root = views.get_or_create_node(
            1, "Landroid/widget/FrameLayout;");
        root->x = 0; root->y = 0; root->width = 1080; root->height = 1920;
        auto* empty = views.get_or_create_node(5, "Landroid/view/View;");
        empty->x = 400; empty->y = 400; empty->width = 0; empty->height = 0;
        views.add_child(1, 5);
        dispatcher.dispatch(1, {flw::TouchAction::DOWN, 450, 450});
        record("h2_childless_zero_box_rejects",
               dispatcher.gesture_target() == 0,
               "target=" + std::to_string(dispatcher.gesture_target()));
    }
    // h3: regression guard — the F-NEW-373 sentinel (-1x-1) fill law still
    // works (the un-measured wrapper fills its parent; the child claims).
    {
        flw::ViewShadow views;
        flw::HandlerShadow handler;
        flw::TouchDispatcher dispatcher{&views, &handler};
        auto* root = views.get_or_create_node(
            1, "Landroid/widget/FrameLayout;");
        root->x = 0; root->y = 0; root->width = 1080; root->height = 1920;
        auto* wrapper = views.get_or_create_node(
            6, "Landroidx/appcompat/widget/FitWindowsLinearLayout;");
        // width/height stay the -1x-1 default (the un-measured sentinel).
        views.add_child(1, 6);
        auto* btn = views.get_or_create_node(7, "Landroid/widget/Button;");
        btn->x = 100; btn->y = 100; btn->width = 200; btn->height = 80;
        btn->clickable = true;
        views.add_child(6, 7);
        dispatcher.dispatch(1, {flw::TouchAction::DOWN, 150, 120});
        record("h3_sentinel_fill_regression_guard",
               dispatcher.gesture_target() == 7,
               "target=" + std::to_string(dispatcher.gesture_target()));
    }
}

int main(int argc, char** argv) {
    std::cout << "== s234_w26_engine_laws — F-NEW-636/637/638 ==\n";
    bool expect_mode = argc > 1 && std::string(argv[1]) == "--expect";
    (void)expect_mode;
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 4000;
    flw::ShadowRegistry registry;
    flw::register_platform_shadows(registry);
    auto heap_adapter = std::make_unique<flw::DalvikHeapAdapter>(
        &engine.get_heap_public(), &engine);
    registry.set_heap(heap_adapter.get());
    engine.set_shadow_registry(&registry);

    Tables t;
    for (const char* s : {"Ljava/util/ArrayList;", "Ljava/lang/Object;",
                          "Ljava/lang/Class;", "Ljava/lang/StringReader;",
                          "[C", "LSemTest;", "Ljava/lang/String;",
                          "LTestDexCls;", "LW26Marker;"})
        t.type(s);
    t.method("Ljava/lang/Class;", "getSuperclass");
    t.method("Ljava/lang/Class;", "getInterfaces");
    t.method("Ljava/io/StringReader;", "<init>");
    t.method("Ljava/io/StringReader;", "read");
    t.str("abc");
    t.str("ab");
    t.str("hi");

    DexReport report = build_world(t);

    struct Row { const char* name; int64_t want; };
    static const Row kRows[] = {
        {"w1_super_framework", 1},
        {"w1_super_chain_two_hops", 1},
        {"w1_object_super_null", 1},
        {"w1_ifaces_framework", 4},
        {"w1_ifaces_dex_first", 1},
        {"s1a_read_count", 3},
        {"s1b_read_content", 97},
        {"s1c_read_eof", -1},
        {"s1_read_cii_eof_content", 1},
        {"s2_read_len0_then_char", 1},
        {"s3_read_single_char_chain", 1},
    };
    for (const auto& row : kRows) {
        int64_t got = -999;
        int rc = run_row(engine, report, row.name, &got);
        record(row.name, rc == 1 && got == row.want,
               "rc=" + std::to_string(rc) + " got=" + std::to_string(got) +
                   " want=" + std::to_string(row.want));
    }
    // Heap-level write-side assertion: run s1f (one read([CII) + return the
    // array), then verify the F-NEW-637 handler stored the real chars.
    {
        int64_t v = 0;
        uint32_t arr_oid = 0;
        int rc = run_row_ex(engine, report, "s1f_read_return_array", &v,
                            &arr_oid);
        auto& heap = engine.get_heap_public();
        auto e0 = heap.get_object_field(arr_oid, "array[0]");
        auto e1 = heap.get_object_field(arr_oid, "array[1]");
        bool ok = rc == 2 && e0.has_value() && e1.has_value() &&
                  e0->type == miniandroid::dalvik::DalvikType::CHAR &&
                  static_cast<unsigned char>(e0->char_val) == 97 &&
                  static_cast<unsigned char>(e1->char_val) == 98;
        record("s1g_heap_fields_written", ok,
               "arr_oid=" + std::to_string(arr_oid) +
                   " array[0].char_val=" +
                   (e0.has_value()
                        ? std::to_string(
                              static_cast<int>(e0->char_val))
                        : std::string("MISSING")));
    }
    run_hit_rows();

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
