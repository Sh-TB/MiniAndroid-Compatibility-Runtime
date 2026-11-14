// s236_port_laws_test — the S236 pre-merge audit battery (issue #595).
//
// The #588 runtime lane pushed Games-g2 / g2-round-2 / Games-g3 evidence
// (F-NEW-655..662 in the lane's numbering). The pre-merge audit (#595)
// found that FOUR of the port rules are already on main (656 UriMatcher
// #371, 657b receiver-inclusive bridge args EXP-071, 658c ContentValues
// copy-ctor #371, 661b unconditional framework-ancestry consult S138+/
// TRAIN-31) — SUPERSEDED, covered here by coverage rows where cheap and
// by the existing batteries otherwise. This battery covers the PORTED
// set, one row per law, plus negative/control rows:
//
//   F-NEW-657 — the sput half of R-NEW-561: an inherited static's write
//     lands in the DECLARING class's ONE cell (subclass <clinit> rebind
//     is visible to the superclass query). r1.
//   F-NEW-658 — SQLiteDatabase.insert/insertOrThrow/insertWithOnConflict:
//     a REAL sqlite3 INSERT answering the rowId (never silent). r2.
//   F-NEW-658b — ContentValues.put unboxes a heap-String via the
//     F-NEW-580b __string_value__ identity (the lane's PGN=NULL face). r3.
//   F-NEW-658c — the ContentValues copy-ctor mirrors the flat map
//     (SUPERSEDED — #371 already implements it). r4.
//   F-NEW-659/659b — framework (0x01-package) string ids resolve from the
//     byte-verified android-4.4w_r1 table BEFORE the GATE-A throw. r5/r6,
//     negative r7 (an unlisted 0x01 id still throws).
//   F-NEW-660 — AbstractStringBuilder.indexOf(String[, from]) — the
//     search half of the removeDoubleSpaces pair. r8.
//   F-NEW-655 — Activity.managedQuery forwards to ContentResolver.query
//     (the resolver law now REACHES — the vanilla face was not-handled). r9.
//   F-NEW-656 — UriMatcher ctor/addURI/match (SUPERSEDED — #371). r10.
//
// Engine-bridge rows call engine.bridge_to_api directly; shadow rows
// dispatch through the registered shadow; the 657 row is hand-assembled
// Dalvik on a synthetic three-class DexReport (the s235 battery pattern).

#include "../src/dex/dalvik_engine.h"
#include "../src/framework/shadow_registry.h"
#include "../src/framework/heap_adapter.h"
#include "../src/framework/android_shadows.h"
#include "../src/storage/sqlite_shadow.h"

#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dalvik::DalvikType;
using miniandroid::dalvik::DalvikValue;
namespace flw = miniandroid::framework;
using flw::CallContext;
using flw::CallResult;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexFieldId;
using miniandroid::dex::DexMethodId;
using miniandroid::dex::DexReport;
using miniandroid::dex::FieldInfo;
using miniandroid::dex::MethodInfo;

namespace opc {
constexpr uint16_t CONST              = 0x14;  // 31i
constexpr uint16_t CONST_STRING       = 0x1A;  // 21c
constexpr uint16_t MOVE_RESULT        = 0x0A;  // 11x
constexpr uint16_t MOVE_RESULT_OBJECT = 0x0C;  // 11x
constexpr uint16_t RETURN             = 0x0F;  // 11x
constexpr uint16_t RETURN_OBJECT      = 0x11;  // 11x
constexpr uint16_t INVOKE_VIRTUAL     = 0x6E;  // 35c
constexpr uint16_t INVOKE_STATIC      = 0x71;  // 35c
constexpr uint16_t SPUT_OBJECT        = 0x69;  // 21c
constexpr uint16_t SGET_OBJECT        = 0x62;  // 21c
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
    void sput_object(uint8_t src, uint16_t field_idx) {
        c.push_back(static_cast<uint16_t>((src << 8) | opc::SPUT_OBJECT));
        c.push_back(field_idx);
    }
    void sget_object(uint8_t reg, uint16_t field_idx) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::SGET_OBJECT));
        c.push_back(field_idx);
    }
    void invoke_static(const std::vector<uint8_t>& regs, uint16_t method_idx) {
        uint16_t word0 = static_cast<uint16_t>(
            (static_cast<uint16_t>(regs.size()) << 12) | opc::INVOKE_STATIC);
        uint16_t word2 = 0;
        for (int i = 0; i < 4 && i < static_cast<int>(regs.size()); ++i)
            word2 |= static_cast<uint16_t>(regs[static_cast<size_t>(i)]
                                           << (4 * i));
        c.push_back(word0);
        c.push_back(method_idx);
        c.push_back(word2);
    }
    void move_result_object(uint8_t reg) {
        c.push_back(static_cast<uint16_t>((reg << 8) |
                                          opc::MOVE_RESULT_OBJECT));
    }
    void ret(uint8_t reg, bool object) {
        c.push_back(static_cast<uint16_t>(
            (reg << 8) | (object ? opc::RETURN_OBJECT : opc::RETURN)));
    }
    void ret_void() { c.push_back(opc::RETURN); }
    size_t if_eqz_ph(uint8_t reg) {
        c.push_back(static_cast<uint16_t>((reg << 8) | opc::IF_EQZ));
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

static MethodInfo make_method(const std::string& cls, const std::string& name,
                              const std::string& descriptor,
                              const std::vector<uint16_t>& code) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = descriptor;
    mi.defining_class = cls;
    mi.registers_size = 16;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;
    mi.code_offset = 1;
    return mi;
}

static DexReport build_world(Tables& t) {
    DexReport report;
    {
        // The battery class (the row driver).
        ClassInfo ci;
        ci.name = "LSemTest;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.access_flags = 0x1;
        // r1 — F-NEW-657: the child <clinit>-style rebind via the
        // ACCESS-SITE field ref (LSChild;.sConf — javac/dx emit the
        // access-site class for inherited statics) must land in the
        // DECLARER's cell; the parent read uses the DECLARER field ref.
        {
            Asm a;
            a.invoke_static({}, t.method("LSChild;", "f657_touch"));
            a.invoke_static({}, t.method("LSParent;", "f657_read"));
            a.move_result_object(0);
            size_t w = a.if_eqz_ph(0);
            a.const_(1, 1);
            a.ret(1, false);
            size_t isnull = a.here();
            a.const_(1, 0);
            a.ret(1, false);
            a.fix(w, isnull);
            a.resolve();
            ci.direct_methods.push_back(
                make_method("LSemTest;", "r1_f657_decl_cell", "()I", a.c));
        }
        report.classes.push_back(ci);
    }
    {
        // The DECLARER: owns the static cell + the reader.
        ClassInfo ci;
        ci.name = "LSParent;";
        ci.superclass_name = "Ljava/lang/Object;";
        ci.access_flags = 0x1;
        FieldInfo sf;
        sf.name = "sConf";
        sf.type = "Ljava/lang/String;";
        sf.is_static = true;
        ci.static_fields.push_back(sf);
        {
            Asm a;
            a.sget_object(0, t.field("LSParent;", "sConf",
                                     "Ljava/lang/String;"));
            a.ret(0, true);
            ci.direct_methods.push_back(
                make_method("LSParent;", "f657_read",
                            "()Ljava/lang/String;", a.c));
        }
        report.classes.push_back(ci);
    }
    {
        // The SUBCLASS: rebinds the inherited static via its OWN class ref
        // (the access-site form — the pre-law write landed under LSChild).
        ClassInfo ci;
        ci.name = "LSChild;";
        ci.superclass_name = "LSParent;";
        ci.access_flags = 0x1;
        {
            Asm a;
            a.const_string(0, t.str("s236-declarer-cell"));
            a.sput_object(0, t.field("LSChild;", "sConf",
                                     "Ljava/lang/String;"));
            a.ret_void();
            ci.direct_methods.push_back(
                make_method("LSChild;", "f657_touch", "()V", a.c));
        }
        report.classes.push_back(ci);
    }
    report.types = t.types;
    report.strings = t.strings;
    report.method_ids = t.method_ids;
    report.field_ids = t.field_ids;
    return report;
}

// ── shadow / bridge rows (no DEX) ───────────────────────────────────────────
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

// Bridge helper: engine.bridge_to_api with a compact verdict.
static bool bridge(DalvikExecutionEngine& e, const std::string& cls,
                   const std::string& m, const std::vector<DalvikValue>& args,
                   DalvikValue& out) {
    miniandroid::dalvik::ApiCallTrace::Status st =
        miniandroid::dalvik::ApiCallTrace::Status::STUBBED;
    return e.bridge_to_api(cls, m, args, out, st, 0);
}

static void run_port_rows(DalvikExecutionEngine& engine,
                          flw::ShadowRegistry& registry) {
    auto& heap = engine.get_heap_public();

    // ── F-NEW-658 + 658b: open a REAL db, insert real rows, answer rowIds.
    {
        auto* db = registry.find_as<miniandroid::storage::DatabaseShadow>();
        uint32_t helper = heap.allocate(
            "Landroid/database/sqlite/SQLiteOpenHelper;", 0, 0);
        CallContext init;
        init.class_name = "Landroid/database/sqlite/SQLiteOpenHelper;";
        init.method = "<init>";
        init.has_receiver = true;
        init.receiver_id = helper;
        init.receiver_class = init.class_name;
        // The scanner walks args from index 1 (args[0] is the
        // receiver-slot mirror in the <init> convention) — park a
        // filler INT at slot 1 and let the STRING/INT scan find the
        // name and the version.
        init.args.push_back(int_arg(1));
        init.args.push_back(str_arg("s236audit.db"));
        init.args.push_back(int_arg(1));
        db->dispatch(init);

        CallContext open;
        open.class_name = init.class_name;
        open.method = "getWritableDatabase";
        open.has_receiver = true;
        open.receiver_id = helper;
        open.receiver_class = init.class_name;
        CallResult opened = db->dispatch(open);
        bool have_db = opened.ret_kind == CallResult::RetKind::OBJECT &&
                       opened.object_id != 0;
        record("r2a_f658_open_helper_db", have_db,
               "ret_kind=" + std::to_string((int)opened.ret_kind));

        if (have_db) {
            uint32_t db_oid = opened.object_id;
            // The table the rows land in.
            CallContext create;
            create.class_name =
                "Landroid/database/sqlite/SQLiteDatabase;";
            create.method = "execSQL";
            create.has_receiver = true;
            create.receiver_id = db_oid;
            create.receiver_class = create.class_name;
            create.args.push_back(str_arg(
                "CREATE TABLE IF NOT EXISTS t1 (id INTEGER PRIMARY KEY, "
                "t TEXT, t2 TEXT)"));
            db->dispatch(create);
            // Determinism: the db file PERSISTS across battery runs —
            // clear the rows so the rowId assertions stay 1,2.
            CallContext clear = create;
            clear.args.clear();
            clear.args.push_back(str_arg("DELETE FROM t1"));
            db->dispatch(clear);

            // ContentValues: a literal put (r2) + a HEAP-STRING put (r3).
            uint32_t cv = heap.allocate("Landroid/content/ContentValues;",
                                        0, 0);
            DalvikValue out;
            bool ok1 = bridge(
                engine, "Landroid/content/ContentValues;", "put",
                {DalvikValue::make_object(cv,
                                          "Landroid/content/ContentValues;"),
                 DalvikValue::make_string("t", 0),
                 DalvikValue::make_string("literal-row", 0)},
                out);
            // F-NEW-658b: a heap String object — the text lives under
            // __string_value__, NOT under "value"; the pre-law flatten
            // mirrored NULL (the lane's 2380 PGN=NULL face).
            uint32_t hs = heap.allocate("Ljava/lang/String;", 0, 0);
            heap.set_object_field(
                hs, "__string_value__",
                DalvikValue::make_string("heap-row-[FEN \"7k/pp3...", 0));
            bool ok2 = bridge(
                engine, "Landroid/content/ContentValues;", "put",
                {DalvikValue::make_object(cv,
                                          "Landroid/content/ContentValues;"),
                 DalvikValue::make_string("t2", 0),
                 DalvikValue::make_object(hs, "Ljava/lang/String;")},
                out);
            auto snap = miniandroid::dalvik::content_values_flat_snapshot(cv);
            bool unboxed = snap.size() == 2 && snap[0].kind == 3 &&
                           snap[0].s == "literal-row" &&
                           snap[1].kind == 3 &&
                           snap[1].s == "heap-row-[FEN \"7k/pp3...";
            record("r3_f658b_heap_string_unbox", ok1 && ok2 && unboxed,
                   "snap=" + std::to_string(snap.size()) +
                       (snap.size() == 2
                            ? " s1=\"" + snap[0].s + "\" s2=\"" + snap[1].s +
                                  "\""
                            : ""));

            // F-NEW-658: the REAL insert — rowId 1 then 2 (never silent).
            CallContext ins;
            ins.class_name = "Landroid/database/sqlite/SQLiteDatabase;";
            ins.method = "insert";
            ins.has_receiver = true;
            ins.receiver_id = db_oid;
            ins.receiver_class = ins.class_name;
            ins.args.push_back(str_arg("t1"));
            ins.args.push_back(str_arg("t2"));  // nullColumnHack
            ins.args.push_back(obj_arg(cv));
            CallResult r1 = db->dispatch(ins);
            CallResult r2 = db->dispatch(ins);
            record("r2b_f658_insert_rowids",
                   r1.ret_kind == CallResult::RetKind::INT &&
                       r2.ret_kind == CallResult::RetKind::INT &&
                       r1.int_val == 1 && r2.int_val == 2,
                   "rowIds=" + std::to_string(r1.int_val) + "," +
                       std::to_string(r2.int_val));

            // The rows are REALLY there (read back through the same db).
            CallContext q;
            q.class_name = "Landroid/database/sqlite/SQLiteDatabase;";
            q.method = "rawQuery";
            q.has_receiver = true;
            q.receiver_id = db_oid;
            q.receiver_class = q.class_name;
            q.args.push_back(str_arg(
                "SELECT t2 FROM t1 WHERE id=2"));
            CallResult qr = db->dispatch(q);
            record("r2c_f658_row_readable",
                   qr.ret_kind == CallResult::RetKind::OBJECT &&
                       qr.object_id != 0,
                   "cursor_ret_kind=" + std::to_string((int)qr.ret_kind));

            // F-NEW-658c (SUPERSEDED coverage — #371 already implements
            // the copy-ctor flat-map mirror).
            uint32_t cvb = heap.allocate("Landroid/content/ContentValues;",
                                         0, 0);
            bool okc = bridge(
                engine, "Landroid/content/ContentValues;", "<init>",
                {DalvikValue::make_object(
                     cvb, "Landroid/content/ContentValues;"),
                 DalvikValue::make_object(cv,
                                          "Landroid/content/ContentValues;")},
                out);
            auto snapb =
                miniandroid::dalvik::content_values_flat_snapshot(cvb);
            record("r4_f658c_copy_ctor_mirror",
                   okc && snapb.size() == 2,
                   "copied=" + std::to_string(snapb.size()));
        }
    }

    // ── F-NEW-659/659b: the framework string-id table before the throw.
    {
        uint32_t res = heap.allocate("Landroid/content/res/Resources;", 0, 0);
        DalvikValue out;
        bool ok = bridge(engine, "Landroid/content/res/Resources;",
                         "getString",
                         {DalvikValue::make_object(
                              res, "Landroid/content/res/Resources;"),
                          DalvikValue::make_int(0x0104000e)},
                         out);
        record("r5_f659_unknownName",
               ok && out.type == DalvikType::STRING_REF &&
                   out.string_val == "(Unknown)",
               "got=\"" + (out.type == DalvikType::STRING_REF
                               ? out.string_val
                               : "") + "\" (the 4.4w byte-truth; the lane "
                       "log paraphrased \"Unknown\")");

        ok = bridge(engine, "Landroid/content/res/Resources;", "getString",
                    {DalvikValue::make_object(
                         res, "Landroid/content/res/Resources;"),
                     DalvikValue::make_int(0x01040000)},
                    out);
        record("r6_f659_cancel", ok &&
               out.type == DalvikType::STRING_REF &&
               out.string_val == "Cancel",
               "got=\"" + (out.type == DalvikType::STRING_REF
                               ? out.string_val
                               : "") + "\"");

        // Negative/control: an UNLISTED 0x01 id still takes the GATE-A
        // throw — at the bridge level the throw_deferred is RECORDED and
        // the arm answers the honest-empty string (never a resolved
        // text, never a fabricated default): the AOSP honesty law.
        ok = bridge(engine, "Landroid/content/res/Resources;", "getString",
                    {DalvikValue::make_object(
                         res, "Landroid/content/res/Resources;"),
                     DalvikValue::make_int(0x0104dead)},
                    out);
        record("r7_f659_unlisted_still_throws",
               ok && out.type == DalvikType::STRING_REF &&
                   out.string_val.empty(),
               "answered=\"" + out.string_val + "\" (empty = the deferred "
                       "NotFoundException, no fabricated default)");
    }

    // ── F-NEW-660: the AbstractStringBuilder.indexOf search half.
    {
        uint32_t sb = heap.allocate("Ljava/lang/StringBuilder;", 0, 0);
        heap.set_object_field(
            sb, "sb_value", DalvikValue::make_string("a  b", 0));
        DalvikValue out;
        bool ok = bridge(engine, "Ljava/lang/StringBuilder;", "indexOf",
                         {DalvikValue::make_object(
                              sb, "Ljava/lang/StringBuilder;"),
                          DalvikValue::make_string("  ", 0)},
                         out);
        int32_t first = out.int_val;
        ok = bridge(engine, "Ljava/lang/StringBuilder;", "indexOf",
                    {DalvikValue::make_object(
                         sb, "Ljava/lang/StringBuilder;"),
                     DalvikValue::make_string("b", 0),
                     DalvikValue::make_int(2)},
                    out) && ok;
        int32_t with_from = out.int_val;
        ok = bridge(engine, "Ljava/lang/StringBuilder;", "indexOf",
                    {DalvikValue::make_object(
                         sb, "Ljava/lang/StringBuilder;"),
                     DalvikValue::make_string("zz", 0)},
                    out) && ok;
        int32_t miss = out.int_val;
        record("r8_f660_sb_indexof",
               ok && first == 1 && with_from == 3 && miss == -1,
               "first=" + std::to_string(first) +
                   " from2=" + std::to_string(with_from) +
                   " miss=" + std::to_string(miss));
    }

    // ── F-NEW-655: managedQuery reaches the resolver query law (the
    // vanilla face fell out of the bridge not-handled).
    {
        uint32_t act = heap.allocate("Landroid/app/Activity;", 0, 0);
        uint32_t uri = heap.allocate("Landroid/net/Uri;", 0, 0);
        heap.set_object_field(
            uri, "uri_raw",
            DalvikValue::make_string("content://s236/t1", 0));
        DalvikValue out;
        miniandroid::dalvik::ApiCallTrace::Status st =
            miniandroid::dalvik::ApiCallTrace::Status::STUBBED;
        bool ok = engine.bridge_to_api(
            "Landroid/app/Activity;", "managedQuery",
            {DalvikValue::make_object(act, "Landroid/app/Activity;"),
             DalvikValue::make_object(uri, "Landroid/net/Uri;"),
             DalvikValue::make_null(), DalvikValue::make_null(),
             DalvikValue::make_null(), DalvikValue::make_null()},
            out, st, 0);
        record("r9_f655_managed_query_forward",
               ok && st == miniandroid::dalvik::ApiCallTrace::Status::
                           IMPLEMENTED,
               "ok=" + std::to_string(ok) + " status=" +
                   std::to_string((int)st));
    }

    // ── F-NEW-656 (SUPERSEDED coverage — the #371 UriMatcher law).
    {
        uint32_t um = heap.allocate("Landroid/content/UriMatcher;", 0, 0);
        DalvikValue out;
        bool ok = bridge(engine, "Landroid/content/UriMatcher;", "<init>",
                         {DalvikValue::make_object(
                              um, "Landroid/content/UriMatcher;"),
                          DalvikValue::make_int(-1)},
                         out);
        ok = bridge(engine, "Landroid/content/UriMatcher;", "addURI",
                    {DalvikValue::make_object(
                         um, "Landroid/content/UriMatcher;"),
                     DalvikValue::make_string("s236", 0),
                     DalvikValue::make_string("t1/#", 0),
                     DalvikValue::make_int(7)},
                    out) && ok;
        uint32_t u1 = heap.allocate("Landroid/net/Uri;", 0, 0);
        heap.set_object_field(u1, "uri_raw",
                              DalvikValue::make_string("content://s236/t1/5",
                                                       0));
        ok = bridge(engine, "Landroid/content/UriMatcher;", "match",
                    {DalvikValue::make_object(
                         um, "Landroid/content/UriMatcher;"),
                     DalvikValue::make_object(u1, "Landroid/net/Uri;")},
                    out) && ok;
        int32_t hit = out.int_val;
        uint32_t u2 = heap.allocate("Landroid/net/Uri;", 0, 0);
        heap.set_object_field(u2, "uri_raw",
                              DalvikValue::make_string("content://s236/other",
                                                       0));
        ok = bridge(engine, "Landroid/content/UriMatcher;", "match",
                    {DalvikValue::make_object(
                         um, "Landroid/content/UriMatcher;"),
                     DalvikValue::make_object(u2, "Landroid/net/Uri;")},
                    out) && ok;
        int32_t nohit = out.int_val;
        record("r10_f656_urimatcher_superseded",
               ok && hit == 7 && nohit == -1,
               "hit=" + std::to_string(hit) +
                   " nohit=" + std::to_string(nohit));
    }
}

int main(int argc, char** argv) {
    std::cout << "== s236_port_laws — the #595 audit port battery ==\n";
    (void)argc; (void)argv;
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 4000;
    flw::ShadowRegistry registry;
    flw::register_platform_shadows(registry);
    auto heap_adapter = std::make_unique<flw::DalvikHeapAdapter>(
        &engine.get_heap_public(), &engine);
    registry.set_heap(heap_adapter.get());
    engine.set_shadow_registry(&registry);

    // r1 — the hand-assembled 657 row.
    {
        Tables t;
        DexReport report = build_world(t);
        MethodInfo* entry = nullptr;
        for (auto& m : report.classes[0].direct_methods)
            if (m.name == "r1_f657_decl_cell") entry = &m;
        if (entry) {
            DalvikExecutionResult r =
                engine.execute_method(*entry, report, {}, false);
            const miniandroid::dalvik::InstructionTrace* ret = nullptr;
            for (const auto& tr : r.instruction_traces)
                if (tr.status == miniandroid::dalvik::InstructionTrace::
                                     Status::HALT_RETURN)
                    ret = &tr;
            int64_t got = -999;
            if (ret && ret->return_value)
                got = ret->return_value->int_val;
            record("r1_f657_decl_cell",
                   got == 1 &&
                       r.final_status ==
                           DalvikExecutionResult::FinalStatus::
                               COMPLETED_SUCCESS,
                   "got=" + std::to_string(got) +
                       " (the superclass read answers the subclass "
                       "rebind — the declarer cell)");
        } else {
            record("r1_f657_decl_cell", false, "row method missing");
        }
    }

    run_port_rows(engine, registry);

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
