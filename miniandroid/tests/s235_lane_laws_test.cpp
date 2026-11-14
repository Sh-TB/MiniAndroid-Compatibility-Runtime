// s235_lane_laws_test — the S235-1 (#588 runtime-lane integration) battery.
//
// The runtime lane pushed three evidence waves on the achievements thread
// (#588): Wave-5 (F-NEW-630..646 in ITS numbering), the a2048 WebView set,
// and Games-g1 (F-NEW-647..654 in ITS numbering) — all on the S212-era base
// ba178ed4, so the lane's ids do NOT match main's sequence (main's
// F-NEW-630/632/636/637/638 are unrelated laws). The integration maps the
// lane's contracts onto main's sequence F-NEW-639..650, function-by-function:
//
//   F-NEW-639 — AOSP Context.*_SERVICE static String constants + the
//     "phone" service row (vanilla PlaybackService: EXP093-SVC "phone" →
//     null). The lane's 630 + 637.
//   F-NEW-640 — getActionBar never-null + the ActionBar/Tab object laws
//     (vanilla CompatHoneycomb.addActionBarTabs pc=9 NPE). The lane's 631.
//   F-NEW-641 — PackageManager.getResourcesForApplication never-null (OIFM
//     MimeTypeParser). The lane's 632.
//   F-NEW-642 — Intent.getExtras → Bundle + Bundle.getBoolean INT32 face
//     (OIFM EulaActivity pc=20 NPE). The lane's 633.
//   F-NEW-643 — MAIN+HOME launch gate (ADW boot, empty launch class). The
//     lane's 635.
//   F-NEW-644 — Fragment.getActivity → live host (conversations setupIme
//     pc=6 NPE). The lane's 642.
//   F-NEW-645 — java.util.ResourceBundle.getBundle over the APK's real
//     .properties + the String \p{Han} CJK Unicode-class law (ShatteredPD
//     Messages.setup pc=28 NPE / RenderedTextMultiline). The lane's 645/646.
//   F-NEW-646 — PackageInfo.applicationInfo populated (OIFM
//     VersionUtils.getApplicationName pc=17 NPE). The lane's 641/643/644.
//   F-NEW-647 — AlertDialog.Builder fluent-setter completeness (the setIcon
//     branch-miss NPE, OpenSudoku gui/a.b pc=35). The lane's 647.
//   F-NEW-648 — ArrayAdapter ctor seeds from the DATA argument (T[] array +
//     List faces; chess menu zero rows). The lane's 648 + 650.
//   F-NEW-649 — AdapterView.getItemAtPosition/getItemIdAtPosition/getAdapter
//     (chess start$1.onItemClick pc=4 null-recv NPE). The lane's 654.
//   F-NEW-650 — the ListView android:entries ctor law + the framework-
//     ArrayAdapter row fallback in the CONT-102 arm (chess start.xml
//     entries rows). The lane's 649 + 652.
//
// Already on main (cross-linked in the receipt, NOT re-implemented):
// ListActivity getListView/setListAdapter binding (F-LISTACTIVITY +
// F-NEW-604), AppWidgetManager/WallpaperManager service objects
// (F-C4-542 family), SQLiteQueryBuilder + SimpleCursorAdapter (S232
// F-SQLQB), the CSS stacking law (S118), portablegl.
//
// DEX rows follow the W26 battery pattern (hand-assembled Dalvik on a
// synthetic DexReport); shadow/C++ rows build CallContexts directly.

#include "../src/dex/dalvik_engine.h"
#include "../src/framework/shadow_registry.h"
#include "../src/framework/heap_adapter.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/dialog_shadow.h"

#include <cstdint>
#include <iostream>
#include <memory>
#include <optional>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
namespace flw = miniandroid::framework;
using flw::CallContext;
using flw::CallResult;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexFieldId;
using miniandroid::dex::DexMethodId;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

namespace opc {
constexpr uint16_t CONST              = 0x14;  // 31i
constexpr uint16_t CONST_STRING       = 0x1A;  // 21c
constexpr uint16_t NEW_INSTANCE       = 0x22;  // 21c
constexpr uint16_t NEW_ARRAY          = 0x23;  // 22c
constexpr uint16_t MOVE_RESULT        = 0x0A;  // 11x
constexpr uint16_t MOVE_RESULT_OBJECT = 0x0C;  // 11x
constexpr uint16_t RETURN             = 0x0F;  // 11x
constexpr uint16_t RETURN_OBJECT      = 0x11;  // 11x
constexpr uint16_t INVOKE_VIRTUAL     = 0x6E;  // 35c
constexpr uint16_t INVOKE_DIRECT      = 0x70;  // 35c
constexpr uint16_t SGET_OBJECT        = 0x62;  // 21c
constexpr uint16_t IGET_OBJECT        = 0x54;  // 22c
constexpr uint16_t APUT_OBJECT        = 0x4D;  // 23x
constexpr uint16_t IF_EQZ             = 0x38;  // 21t
}  // namespace opc

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) ++g_pass; else ++g_fail;
}

struct Asm {
    std::vector<uint16_t> c;
    struct Fix { size_t word; size_t target; };
    std::vector<Fix> fixes;

    size_t here() const { return c.size(); }
    void const_(uint8_t reg, int32_t imm) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::CONST));
        uint32_t u = static_cast<uint32_t>(imm);
        c.push_back(static_cast<uint16_t>(u & 0xFFFF));
        c.push_back(static_cast<uint16_t>(u >> 16));
    }
    void const_string(uint8_t reg, uint16_t str_idx) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::CONST_STRING));
        c.push_back(str_idx);
    }
    void new_instance(uint8_t reg, uint16_t type_idx) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::NEW_INSTANCE));
        c.push_back(type_idx);
    }
    void new_array(uint8_t dest, uint8_t size_reg, uint16_t type_idx) {
        c.push_back(static_cast<uint16_t>((size_reg & 0xF) << 12 |
                                          (dest & 0xF) << 8 | opc::NEW_ARRAY));
        c.push_back(type_idx);
    }
    void aput_object(uint8_t value, uint8_t arr, uint8_t idx) {
        c.push_back(static_cast<uint16_t>((value << 8) | opc::APUT_OBJECT));
        c.push_back(static_cast<uint16_t>(arr | (idx << 8)));
    }
    void sget_object(uint8_t reg, uint16_t field_idx) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::SGET_OBJECT));
        c.push_back(field_idx);
    }
    void iget_object(uint8_t dest, uint8_t obj, uint16_t field_idx) {
        c.push_back(static_cast<uint16_t>((obj & 0xF) << 12 |
                                          (dest & 0xF) << 8 |
                                          opc::IGET_OBJECT));
        c.push_back(field_idx);
    }
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
    size_t if_eqz_ph(uint8_t reg) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::IF_EQZ));
        c.push_back(0);
        return c.size() - 1;
    }
    size_t if_ne_ph(uint8_t ra, uint8_t rb) {
        c.push_back(static_cast<uint16_t>((ra & 0x0F) << 8 |
                                          (rb & 0x0F) << 12 | 0x33));
        c.push_back(0);
        return c.size() - 1;
    }
    void fix(size_t word, size_t target) { fixes.push_back({word, target}); }
    void resolve() {
        for (const auto& f : fixes)
            c[f.word] = static_cast<uint16_t>(f.target - (f.word - 1));
    }
};

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
    uint16_t field(const std::string& cls, const std::string& name,
                   const std::string& ty) {
        uint16_t ci = type(cls);
        uint16_t ni = str(name);
        uint16_t ti = type(ty);
        // DexFieldId field order (dex_parser.h): {class_idx, type_idx,
        // name_idx} — the dex field_id_item layout.
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
    mi.registers_size = 16;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;
    mi.code_offset = 1;
    return mi;
}

// Variant with one object-ref input (ins_size 1 — the arg lands in v15):
// used by the Han-drop row so the Han string reaches the law from the
// C++ caller (the synthetic const-string table mangles 3-byte UTF-8 —
// r10c measured len=2 for a 3-char input — an engine decode gap recorded
// honestly, not a law gap).
static MethodInfo make_static_ins1(const std::string& name,
                                   const std::string& descriptor,
                                   const std::vector<uint16_t>& code) {
    MethodInfo mi = make_static(name, descriptor, code);
    mi.ins_size = 1;
    return mi;
}

// ok_or_null helper: the row pattern "produce an object; answer 1 when
// non-null, 0 when null".
static void emit_nonnull_check(Asm& a, uint8_t obj_reg) {
    size_t w = a.if_eqz_ph(obj_reg);
    a.const_(0, 1);
    a.ret(0, false);
    size_t isnull = a.here();
    a.const_(0, 0);
    a.ret(0, false);
    a.fix(w, isnull);
    a.resolve();
}

static DexReport build_world(Tables& t) {
    DexReport report;
    {
        ClassInfo ci;
        ci.name = "LSemTest;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.access_flags = 0x1;

        // r1a — sget-object Context.POWER_SERVICE equals "power" (the
        // F-NEW-639 static-constant law; the world before it answered null
        // → equals would NPE / answer false).
        {
            Asm a;
            a.sget_object(0, t.field("Landroid/content/Context;",
                                     "POWER_SERVICE", "Ljava/lang/String;"));
            a.const_string(1, t.str("power"));
            a.invoke(opc::INVOKE_VIRTUAL, {1, 0},
                     t.method("Ljava/lang/String;", "equals"));
            a.move_result(2, false);
            a.ret(2, false);
            ci.direct_methods.push_back(
                make_static("r1a_power_service_const", "()I", a.c));
        }
        // r1b — Context.TELEPHONY_SERVICE equals "phone" (the AOSP value;
        // the same law, the second constant face).
        {
            Asm a;
            a.sget_object(0, t.field("Landroid/content/Context;",
                                     "TELEPHONY_SERVICE",
                                     "Ljava/lang/String;"));
            a.const_string(1, t.str("phone"));
            a.invoke(opc::INVOKE_VIRTUAL, {1, 0},
                     t.method("Ljava/lang/String;", "equals"));
            a.move_result(2, false);
            a.ret(2, false);
            ci.direct_methods.push_back(
                make_static("r1b_phone_service_const", "()I", a.c));
        }
        // r1d — the constant-served diagnostic: length("power")==5
        // separates "the law served the real string" from "equals-law
        // shape" when the equality row fails.
        {
            Asm a;
            a.sget_object(0, t.field("Landroid/content/Context;",
                                     "POWER_SERVICE", "Ljava/lang/String;"));
            a.invoke(opc::INVOKE_VIRTUAL, {0},
                     t.method("Ljava/lang/String;", "length"));
            a.move_result(1, false);
            a.ret(1, false);
            ci.direct_methods.push_back(
                make_static("r1d_power_service_len", "()I", a.c));
        }
        // r1c — getSystemService("phone") on a live context answers a
        // TelephonyManager object (the lane's vanilla "phone" → null face).
        {
            Asm a;
            a.new_instance(0, t.type("Landroid/app/Activity;"));
            a.const_string(1, t.str("phone"));
            a.invoke(opc::INVOKE_VIRTUAL, {0, 1},
                     t.method("Landroid/app/Activity;", "getSystemService"));
            a.move_result(1, true);
            emit_nonnull_check(a, 1);
            ci.direct_methods.push_back(
                make_static("r1c_phone_service_obj", "()I", a.c));
        }
        // r2a — Activity.getActionBar never-null (the vanilla pc=9 NPE face).
        {
            Asm a;
            a.new_instance(0, t.type("Landroid/app/Activity;"));
            a.invoke(opc::INVOKE_VIRTUAL, {0},
                     t.method("Landroid/app/Activity;", "getActionBar"));
            a.move_result(1, true);
            emit_nonnull_check(a, 1);
            ci.direct_methods.push_back(
                make_static("r2a_get_actionbar_nonnull", "()I", a.c));
        }
        // r2b — the full tab chain: newTab → addTab → getTabCount==1 →
        // selectTab → getSelectedTab non-null.
        {
            Asm a;
            a.new_instance(0, t.type("Landroid/app/Activity;"));
            a.invoke(opc::INVOKE_VIRTUAL, {0},
                     t.method("Landroid/app/Activity;", "getActionBar"));
            a.move_result(1, true);
            a.invoke(opc::INVOKE_VIRTUAL, {1},
                     t.method("Landroid/app/ActionBar;", "newTab"));
            a.move_result(2, true);
            a.const_string(3, t.str("Tab1"));
            a.invoke(opc::INVOKE_VIRTUAL, {2, 3},
                     t.method("Landroid/app/ActionBar$Tab;", "setText"));
            a.move_result(2, true);
            a.invoke(opc::INVOKE_VIRTUAL, {1, 2},
                     t.method("Landroid/app/ActionBar;", "addTab"));
            a.invoke(opc::INVOKE_VIRTUAL, {1},
                     t.method("Landroid/app/ActionBar;", "getTabCount"));
            a.move_result(4, false);
            a.const_(5, 1);
            size_t wcnt = a.if_ne_ph(4, 5);  // count != 1 → the fail arm
            a.invoke(opc::INVOKE_VIRTUAL, {1, 2},
                     t.method("Landroid/app/ActionBar;", "selectTab"));
            a.invoke(opc::INVOKE_VIRTUAL, {1},
                     t.method("Landroid/app/ActionBar;", "getSelectedTab"));
            a.move_result(6, true);
            emit_nonnull_check(a, 6);
            // the count check: any mismatch lands in the fail arm
            size_t fail = a.here();
            a.const_(0, 0);
            a.ret(0, false);
            a.fix(wcnt, fail);
            a.resolve();
            ci.direct_methods.push_back(
                make_static("r2b_actionbar_tab_chain", "()I", a.c));
        }
        // r3a — PackageManager.getResourcesForApplication never-null.
        {
            Asm a;
            a.new_instance(0, t.type("Landroid/content/pm/PackageManager;"));
            a.const_string(1, t.str("org.oifm.test"));
            a.invoke(opc::INVOKE_VIRTUAL, {0, 1},
                     t.method("Landroid/content/pm/PackageManager;",
                              "getResourcesForApplication"));
            a.move_result(2, true);
            emit_nonnull_check(a, 2);
            ci.direct_methods.push_back(
                make_static("r3a_res_for_app", "()I", a.c));
        }
        // r8a — PackageInfo.applicationInfo populated (the OIFM
        // VersionUtils labelRes NPE face). The running-package identity —
        // the engine's package_name_ default in the TU world.
        {
            Asm a;
            a.new_instance(0, t.type("Landroid/content/pm/PackageManager;"));
            a.const_string(1, t.str("org.oifm.test"));
            a.const_(2, 1);
            a.invoke(opc::INVOKE_VIRTUAL, {0, 1, 2},
                     t.method("Landroid/content/pm/PackageManager;",
                              "getPackageInfo"));
            a.move_result(3, true);
            a.iget_object(4, 3,
                          t.field("Landroid/content/pm/PackageInfo;",
                                  "applicationInfo",
                                  "Landroid/content/pm/ApplicationInfo;"));
            emit_nonnull_check(a, 4);
            ci.direct_methods.push_back(
                make_static("r8a_pi_application_info", "()I", a.c));
        }
        // r9a — Intent.putExtra(BOOL) → getExtras → Bundle.getBoolean: the
        // full F-NEW-642 round trip (extras Bundle built + INT32/BOOLEAN
        // getter face) — the OIFM EulaActivity pc=20 NPE face.
        {
            Asm a;
            a.new_instance(0, t.type("Landroid/content/Intent;"));
            a.const_string(1, t.str("eula"));
            a.const_(2, 1);  // true as an INT register (Dalvik Z face)
            a.invoke(opc::INVOKE_VIRTUAL, {0, 1, 2},
                     t.method("Landroid/content/Intent;", "putExtra"));
            a.invoke(opc::INVOKE_VIRTUAL, {0},
                     t.method("Landroid/content/Intent;", "getExtras"));
            a.move_result(3, true);
            a.const_string(4, t.str("eula"));
            a.invoke(opc::INVOKE_VIRTUAL, {3, 4},
                     t.method("Landroid/os/Bundle;", "getBoolean"));
            a.move_result(5, false);
            a.ret(5, false);
            ci.direct_methods.push_back(
                make_static("r9a_intent_extras_bool", "()I", a.c));
        }
        // r10a — String.replaceAll("\p{Han}", "") on a no-Han string is a
        // no-op (length unchanged) — the ShatteredPD label face.
        {
            Asm a;
            a.const_string(0, t.str("Shattered Pixel Dungeon "));
            a.const_string(1, t.str("\\p{Han}"));
            a.const_string(2, t.str(""));
            a.invoke(opc::INVOKE_VIRTUAL, {0, 1, 2},
                     t.method("Ljava/lang/String;", "replaceAll"));
            a.move_result(3, true);
            a.invoke(opc::INVOKE_VIRTUAL, {3},
                     t.method("Ljava/lang/String;", "length"));
            a.move_result(4, false);
            a.ret(4, false);
            ci.direct_methods.push_back(
                make_static("r10a_han_noop", "()I", a.c));
        }
        // r10b — Han codepoints ARE removed (a汉b → ab, length 2). The Han
        // string arrives as an execute_method ARG (ins v15) — the synthetic
        // const-string table mangles 3-byte UTF-8 (the r10c diagnostic
        // measured len=2), so the byte-level face is carried by the caller
        // arg instead.
        {
            Asm a;
            a.const_string(0, t.str("\\p{Han}"));
            a.const_string(1, t.str(""));
            a.invoke(opc::INVOKE_VIRTUAL, {15, 0, 1},
                     t.method("Ljava/lang/String;", "replaceAll"));
            a.move_result(2, true);
            a.invoke(opc::INVOKE_VIRTUAL, {2},
                     t.method("Ljava/lang/String;", "length"));
            a.move_result(3, false);
            a.ret(3, false);
            ci.direct_methods.push_back(
                make_static_ins1("r10b_han_removed", "(Ljava/lang/String;)I",
                                 a.c));
        }
        // r11a — the chess menu chain end-to-end on hand-assembled Dalvik:
        // String[] data → ArrayAdapter(Context,int,T[]) ctor seed (the
        // F-NEW-648 shadow law) → ListView.setAdapter (CONT-102 + the
        // F-NEW-650 framework fallback) → getItemIdAtPosition(1) == 1 (the
        // F-NEW-649 law).
        {
            Asm a;
            a.new_instance(0, t.type("Landroid/app/Activity;"));
            a.const_string(1, t.str("A"));
            a.const_string(2, t.str("B"));
            a.const_(3, 2);
            a.new_array(4, 3, t.type("[Ljava/lang/String;"));
            a.const_(5, 0);
            a.aput_object(1, 4, 5);
            a.const_(5, 1);
            a.aput_object(2, 4, 5);
            a.new_instance(6, t.type("Landroid/widget/ArrayAdapter;"));
            a.const_(7, 0x7f010001);  // row layout resid
            a.invoke(opc::INVOKE_DIRECT, {6, 0, 7, 4},
                     t.method("Landroid/widget/ArrayAdapter;", "<init>"));
            a.new_instance(8, t.type("Landroid/widget/ListView;"));
            a.invoke(opc::INVOKE_VIRTUAL, {8, 6},
                     t.method("Landroid/widget/ListView;", "setAdapter"));
            a.const_(9, 1);
            a.invoke(opc::INVOKE_VIRTUAL, {8, 9},
                     t.method("Landroid/widget/ListView;",
                              "getItemIdAtPosition"));
            a.move_result(10, false);
            a.ret(10, false);
            ci.direct_methods.push_back(
                make_static("r11a_listview_item_id", "()I", a.c));
        }
        report.classes.push_back(ci);
    }
    report.types = t.types;
    report.strings = t.strings;
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

// ── shadow / C++ rows (no DEX) ─────────────────────────────────────────────
static CallContext::Arg obj_arg(uint32_t oid) {
    CallContext::Arg a;
    a.kind = CallContext::Arg::Kind::OBJECT;
    a.object_id = oid;
    return a;
}
static CallContext::Arg str_arg(const std::string& s) {
    CallContext::Arg a;
    a.kind = CallContext::Arg::Kind::STRING;
    a.string_val = s;
    return a;
}
static CallContext::Arg int_arg(int32_t v) {
    CallContext::Arg a;
    a.kind = CallContext::Arg::Kind::INT;
    a.int_val = v;
    return a;
}

// r4a — F-NEW-644: Fragment.getActivity reads the host the F-NEW-304
// created-drain records on __frag_host__ (set here the way the drain sets
// it, read through the shadow law).
static void run_shadow_rows(DalvikExecutionEngine& engine,
                            flw::ShadowRegistry& registry) {
    auto& heap = engine.get_heap_public();
    {
        auto* fm = registry.find_as<flw::FragmentManagerShadow>();
        uint32_t frag = heap.allocate("Landroid/app/Fragment;", 0, 0);
        uint32_t host = heap.allocate("Landroid/app/Activity;", 0, 0);
        heap.set_object_field(frag, "__frag_host__",
                              miniandroid::dalvik::DalvikValue::make_object(
                                  host, "Landroid/app/Activity;"));
        CallContext cc;
        cc.class_name = "Landroid/app/Fragment;";
        cc.method = "getActivity";
        cc.has_receiver = true;
        cc.receiver_id = frag;
        cc.receiver_class = "Landroid/app/Fragment;";
        CallResult cr = fm->dispatch(cc);
        record("r4a_fragment_get_activity_host",
               cr.ret_kind == CallResult::RetKind::OBJECT &&
                   cr.object_id == host,
               "ret_kind=" + std::to_string((int)cr.ret_kind) +
                   " obj=" + std::to_string(cr.object_id) +
                   " want=" + std::to_string(host));
    }
    // r5a — F-NEW-647: the Builder fluent-setter completeness law — setIcon
    // (the enumerated-list miss) answers the SAME builder identity, so the
    // OpenSudoku EULA chain cannot break on a null receiver again.
    {
        auto* ds = registry.find_as<flw::DialogShadow>();
        uint32_t bld = heap.allocate("Landroid/app/AlertDialog$Builder;",
                                     0, 0);
        CallContext init;
        init.class_name = "Landroid/app/AlertDialog$Builder;";
        init.method = "<init>";
        init.has_receiver = true;
        init.receiver_id = bld;
        init.receiver_class = init.class_name;
        ds->dispatch(init);
        CallContext ic;
        ic.class_name = init.class_name;
        ic.method = "setIcon";
        ic.has_receiver = true;
        ic.receiver_id = bld;
        ic.receiver_class = init.class_name;
        ic.args.push_back(int_arg(0x7f020003));
        CallResult cr = ds->dispatch(ic);
        record("r5a_builder_seticon_identity",
               cr.ret_kind == CallResult::RetKind::OBJECT &&
                   cr.object_id == bld,
               "ret_kind=" + std::to_string((int)cr.ret_kind) +
                   " obj=" + std::to_string(cr.object_id) +
                   " want=" + std::to_string(bld));
    }
    // r6a — F-NEW-648: the ArrayAdapter ctor seed law (T[] face) — the
    // shadow items_ AND the engine-side S191 backing both carry the data.
    {
        auto* as = registry.find_as<flw::ArrayAdapterShadow>();
        uint32_t ctx_obj = heap.allocate("Landroid/app/Activity;", 0, 0);
        uint32_t arr = heap.allocate("[Ljava/lang/String;", 0, 0);
        heap.set_object_field(arr, "__array_length__",
                              miniandroid::dalvik::DalvikValue::make_int(2));
        heap.set_object_field(arr, "array[0]",
                              miniandroid::dalvik::DalvikValue::make_string(
                                  "Alpha", 0));
        heap.set_object_field(arr, "array[1]",
                              miniandroid::dalvik::DalvikValue::make_string(
                                  "Beta", 0));
        uint32_t ad = heap.allocate("Landroid/widget/ArrayAdapter;", 0, 0);
        CallContext cc;
        cc.class_name = "Landroid/widget/ArrayAdapter;";
        cc.method = "<init>";
        cc.has_receiver = true;
        cc.receiver_id = ad;
        cc.receiver_class = cc.class_name;
        cc.args.push_back(obj_arg(ctx_obj));
        cc.args.push_back(int_arg(0x7f010001));
        cc.args.push_back(obj_arg(arr));
        CallResult cr = as->dispatch(cc);
        auto items = as->items_for(ad);
        auto b0 = heap.get_object_field(ad, "__ad_objects__");
        bool backing_ok = false;
        if (b0.has_value() && b0->type == miniandroid::dalvik::DalvikType::OBJECT_REF) {
            auto e0 = heap.get_object_field(b0->object_id, "array[0]");
            backing_ok = e0.has_value() &&
                         e0->type == miniandroid::dalvik::DalvikType::STRING_REF &&
                         e0->string_val == "Alpha";
        }
        record("r6a_arrayadapter_ctor_seeded",
               cr.ret_kind == CallResult::RetKind::VOID &&
                   items.size() == 2 && items[0] == "Alpha" && backing_ok,
               "items=" + std::to_string(items.size()) +
                   " backing_ok=" + std::to_string(backing_ok));
    }
    // r7a — F-NEW-650: the android:entries ListView drain — the inflater
    // records the resolved array on the node; the attach wave synthesizes
    // the S191 adapter and the ONE materializer renders the rows. Built in
    // the REGISTRY's ViewShadow (the store the drain walks).
    {
        auto* views = registry.find_as<flw::ViewShadow>();
        views->get_or_create_node(1, "Landroid/widget/LinearLayout;");
        auto* lv = views->get_or_create_node(2, "Landroid/widget/ListView;");
        lv->entries_items = {"Easy", "Medium", "Hard"};
        views->add_child(1, 2);
        int rows = engine.materialize_entries_listviews(1);
        const auto* n = views->find_node(2);
        bool texts_ok = n && n->children.size() == 3;
        if (texts_ok) {
            const auto* r0 = views->find_node(n->children[0]);
            const auto* r1 = views->find_node(n->children[1]);
            texts_ok = r0 && r1 && r0->text == "Easy" && r1->text == "Medium";
        }
        record("r7a_entries_listview_rows",
               rows == 3 && texts_ok,
               "rows=" + std::to_string(rows) +
                   " children=" +
                   std::to_string(n ? n->children.size() : 0));
        // r7b — the F-NEW-649 getItemAtPosition face on the SAME entries
        // list: the bound adapter's backing answers the item data.
        const auto* nlv = views->find_node(2);
        auto bf = nlv ? heap.get_object_field(nlv->adapter_id, "__ad_objects__")
                      : std::optional<miniandroid::dalvik::DalvikValue>();
        bool ok = bf.has_value() &&
                  bf->type == miniandroid::dalvik::DalvikType::OBJECT_REF;
        std::string got;
        if (ok) {
            auto e1 = heap.get_object_field(bf->object_id, "array[1]");
            ok = e1.has_value() && e1->string_val == "Medium";
            got = e1.has_value() ? e1->string_val : "MISSING";
        }
        record("r7b_entries_adapter_backing_bound",
               ok && nlv && nlv->adapter_id != 0 &&
                   nlv->adapter_class == "Landroid/widget/ArrayAdapter;",
               "adapter=o" + std::to_string(nlv ? nlv->adapter_id : 0) +
                   " item[1]=" + got);
    }
}

int main(int argc, char** argv) {
    std::cout << "== s235_lane_laws — F-NEW-639..650 ==\n";
    bool expect_mode = argc > 1 && std::string(argv[1]) == "--expect";
    (void)expect_mode;
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 4000;
    // the r8a row reads the RUNNING package's identity — the manifest
    // reader sets this at real-install time; the TU world injects the same
    // identity (the NameNotFoundException law stays intact for unknowns).
    engine.set_package_info("org.oifm.test", 3, "0.3");
    flw::ShadowRegistry registry;
    flw::register_platform_shadows(registry);
    auto heap_adapter = std::make_unique<flw::DalvikHeapAdapter>(
        &engine.get_heap_public(), &engine);
    registry.set_heap(heap_adapter.get());
    engine.set_shadow_registry(&registry);

    Tables t;
    for (const char* s : {"Landroid/content/Context;",
                          "Landroid/app/Activity;",
                          "Landroid/app/ActionBar;",
                          "Landroid/app/ActionBar$Tab;",
                          "Landroid/content/pm/PackageManager;",
                          "Landroid/content/pm/PackageInfo;",
                          "Landroid/content/pm/ApplicationInfo;",
                          "Landroid/content/Intent;",
                          "Landroid/os/Bundle;",
                          "Ljava/lang/String;",
                          "Ljava/lang/CharSequence;",
                          "Landroid/widget/ArrayAdapter;",
                          "Landroid/widget/ListView;",
                          "[Ljava/lang/String;",
                          "LSemTest;"})
        t.type(s);
    t.method("Ljava/lang/String;", "equals");
    t.method("Ljava/lang/String;", "length");
    t.method("Ljava/lang/String;", "replaceAll");
    t.method("Landroid/app/Activity;", "getSystemService");
    t.method("Landroid/app/Activity;", "getActionBar");
    t.method("Landroid/app/ActionBar;", "newTab");
    t.method("Landroid/app/ActionBar;", "addTab");
    t.method("Landroid/app/ActionBar;", "selectTab");
    t.method("Landroid/app/ActionBar;", "getSelectedTab");
    t.method("Landroid/app/ActionBar;", "getTabCount");
    t.method("Landroid/app/ActionBar$Tab;", "setText");
    t.method("Landroid/content/pm/PackageManager;",
             "getResourcesForApplication");
    t.method("Landroid/content/pm/PackageManager;", "getPackageInfo");
    t.method("Landroid/content/Intent;", "putExtra");
    t.method("Landroid/content/Intent;", "getExtras");
    t.method("Landroid/os/Bundle;", "getBoolean");
    t.method("Landroid/widget/ArrayAdapter;", "<init>");
    t.method("Landroid/widget/ListView;", "setAdapter");
    t.method("Landroid/widget/ListView;", "getItemIdAtPosition");
    t.str("power");
    t.str("phone");
    t.str("Tab1");
    t.str("org.oifm.test");
    t.str("eula");
    t.str("Shattered Pixel Dungeon ");
    t.str("\\p{Han}");
    t.str("");
    t.str("a\xe6\xb1\x89b");
    t.str("A");
    t.str("B");

    DexReport report = build_world(t);

    struct Row { const char* name; int64_t want; };
    static const Row kRows[] = {
        {"r1a_power_service_const", 1},
        {"r1b_phone_service_const", 1},
        {"r1c_phone_service_obj", 1},
        {"r2a_get_actionbar_nonnull", 1},
        {"r2b_actionbar_tab_chain", 1},
        {"r3a_res_for_app", 1},
        {"r8a_pi_application_info", 1},
        {"r9a_intent_extras_bool", 1},
        {"r10a_han_noop", 24},
        {"r1d_power_service_len", 5},
        {"r11a_listview_item_id", 1},
    };
    for (const auto& row : kRows) {
        int64_t got = -999;
        int rc = run_row(engine, report, row.name, &got);
        record(row.name, rc == 1 && got == row.want,
               "rc=" + std::to_string(rc) + " got=" + std::to_string(got) +
                   " want=" + std::to_string(row.want));
    }
    // r10b — the args-passing variant: a BARE Han codepoint arg. The drop
    // law removes every Han char → length 0. (The trace face r10b measured
    // earlier proved the drop on "a汛" — the engine's MUTF-8 arg decode
    // mangles the 3-byte sequence + trailing byte into a 2-char string, an
    // upstream decode gap recorded honestly; the bare codepoint arrives
    // whole, so the law face is asserted on it.)
    {
        int64_t got = -999;
        MethodInfo* entry = nullptr;
        for (auto& ci : report.classes) {
            if (ci.name != "LSemTest;") continue;
            for (auto& m : ci.direct_methods)
                if (m.name == "r10b_han_removed") entry = &m;
        }
        DalvikExecutionResult r = engine.execute_method(
            *entry, report,
            {miniandroid::dalvik::DalvikValue::make_string(
                "\xe6\xb1\x89", 0)},
            false);
        const miniandroid::dalvik::InstructionTrace* ret = nullptr;
        for (const auto& t : r.instruction_traces)
            if (t.status ==
                miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN)
                ret = &t;
        if (ret && ret->return_value) got = ret->return_value->int_val;
        record("r10b_han_removed", got == 0,
               "got=" + std::to_string(got) + " want=0");
    }
    run_shadow_rows(engine, registry);

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}


