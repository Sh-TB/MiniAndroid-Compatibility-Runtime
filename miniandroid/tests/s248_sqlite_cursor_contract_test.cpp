// s248_sqlite_cursor_contract_test — W20-K (S237-WS5, independent coder
// cODER-ohc #issuecomment): AOSP AbstractCursor.getColumnIndex law
// (@android-14 L323-360):
//   1. strip the table qualifier after the LAST '.'
//   2. match case-insensitively
//   3. missing column → -1 (getColumnIndex), IllegalArgumentException with
//      the AOSP message shape + available-columns list (OrThrow)
// Shadow-level contract: real DatabaseShadow, real in-file sqlite db.
#include "../src/storage/sqlite_shadow.h"
#include "../src/dex/dalvik_engine_impl.h"
// W20-K test adapter: DalvikHeap behind the shadow HeapAllocator face.
class TestHeapAdapter : public miniandroid::framework::HeapAllocator {
public:
    explicit TestHeapAdapter(miniandroid::dalvik::DalvikHeap& h) : h_(h) {}
    uint32_t allocate(const std::string& c) override {
        return h_.allocate(c, 0, 0);
    }
    uint32_t get_singleton(const std::string&) override { return 0; }
    uint32_t get_or_create(const std::string& c) override {
        return h_.allocate(c, 0, 0);
    }
    bool has_object(uint32_t) override { return true; }
private:
    miniandroid::dalvik::DalvikHeap& h_;
};

#include "../src/framework/shadow_registry.h"

#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::framework::CallContext;
using miniandroid::framework::CallResult;
using miniandroid::storage::DatabaseShadow;

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) ++g_pass; else ++g_fail;
}

static CallContext ctx_for(uint32_t recv, const std::string& m,
                           const std::string& arg0 = "",
                           const std::string& cls =
                               "Landroid/database/sqlite/SQLiteCursor;") {
    CallContext c;
    c.has_receiver = recv != 0;
    c.receiver_id = recv;
    c.receiver_class = cls;
    c.class_name = cls;
    c.method = m;
    if (!arg0.empty()) {
        CallContext::Arg a;
        a.kind = CallContext::Arg::Kind::STRING;
        a.string_val = arg0;
        c.args.push_back(a);
    }
    return c;
}

int main() {
    std::cout << "== s248_sqlite_cursor_contract ==\n";
    DatabaseShadow db;
    miniandroid::dalvik::DalvikHeap heap;
    TestHeapAdapter heap_adapter(heap);
    db.init(&heap_adapter);

    // Real db + table + row (the WS5 fixture shape) — routed through the
    // SQLiteOpenHelper face (the same real-sqlite3 open path apps reach):
    // a REAL helper object carries the db_name the open path resolves.
    uint32_t helper = heap.allocate(
        "Landroid/database/sqlite/SQLiteOpenHelper;", 0, 0);
    // AOSP SQLiteOpenHelper.<init>(Context, name, factory, version) — the
    // face records the db_name the open path resolves.
    {
        CallContext ic = ctx_for(helper, "<init>", "",
                                 "Landroid/database/sqlite/SQLiteOpenHelper;");
        CallContext::Arg a0; a0.kind = CallContext::Arg::Kind::OBJECT;
        a0.object_id = helper;
        ic.args.push_back(a0);
        CallContext::Arg a1; a1.kind = CallContext::Arg::Kind::STRING;
        a1.string_val = "w20_s248.db";
        ic.args.push_back(a1);
        CallContext::Arg a2; a2.kind = CallContext::Arg::Kind::INT;
        a2.int_val = 1;
        ic.args.push_back(a2);
        db.dispatch(ic);
    }
    CallContext oc = ctx_for(helper, "getWritableDatabase", "",
                             "Landroid/database/sqlite/SQLiteOpenHelper;");
    auto opened = db.dispatch(oc);
    if (!opened.handled) {
        record("s248_db_opened", false,
               "helper getWritableDatabase not handled");
        std::cout << "== " << g_pass << " passed / " << g_fail
                  << " failed ==\n";
        return 1;
    }
    record("s248_db_opened", true, "real sqlite3 db open (helper face)");

    auto sql = [&](const std::string& s) {
        CallContext c = ctx_for(0, "execSQL");
        c.args.clear();
        CallContext::Arg a; a.kind = CallContext::Arg::Kind::STRING;
        a.string_val = s; c.args.push_back(a);
        return db.dispatch(c);
    };
    uint32_t dbobj = opened.handled ? opened.object_id : 0;
    record("s248_db_object", dbobj != 0,
           "db obj#" + std::to_string(dbobj));
    auto sql2 = [&](const std::string& s) {
        CallContext c = ctx_for(dbobj, "execSQL", s,
                                "Landroid/database/sqlite/SQLiteDatabase;");
        return db.dispatch(c);
    };
    sql2("CREATE TABLE IF NOT EXISTS t1(id INTEGER, name TEXT, t2 TEXT)");
    sql2("INSERT INTO t1 VALUES(7,'first','x')");

    // rawQuery → cursor object
    CallContext qc = ctx_for(dbobj, "rawQuery", "",
                             "Landroid/database/sqlite/SQLiteDatabase;");
    qc.args.clear();
    { CallContext::Arg a; a.kind = CallContext::Arg::Kind::STRING;
      a.string_val = "SELECT id, name, t2 FROM t1"; qc.args.push_back(a); }
    auto q = db.dispatch(qc);
    uint32_t cur = q.handled ? q.object_id : 0;
    record("s248_rawquery_cursor", q.handled && cur != 0,
           "cursor obj#" + std::to_string(cur));

    if (cur != 0) {
        auto idx = [&](const std::string& col) {
            auto r = db.cursor_dispatch(ctx_for(cur, "getColumnIndex", col));
            return (r.handled && r.ret_kind ==
                        CallResult::RetKind::INT) ? r.int_val : -999;
        };
        record("ws5_exact", idx("name") == 1, "getColumnIndex(name)=1");
        record("ws5_case_insensitive", idx("NAME") == 1,
               "getColumnIndex(NAME)=1 (AOSP equalsIgnoreCase law)");
        record("ws5_table_qualifier", idx("t1.t2") == 2,
               "getColumnIndex(t1.t2)=2 (AOSP bug-903852 strip law)");
        record("ws5_qualifier_case", idx("T1.T2") == 2,
               "getColumnIndex(T1.T2)=2");
        record("ws5_miss_minus_one", idx("nope") == -1,
               "missing column answers -1");

        auto thr = db.cursor_dispatch(
            ctx_for(cur, "getColumnIndexOrThrow", "NOPE"));
        bool throws_iae = thr.is_exc &&
                          thr.exc_class.find(
                              "IllegalArgumentException") !=
                              std::string::npos;
        record("ws5_orthrow_throws_iae", throws_iae,
               "AOSP IllegalArgumentException on missing column");
        record("ws5_orthrow_message_shape",
               throws_iae &&
                   thr.exc_msg.find("does not exist") !=
                       std::string::npos &&
                   thr.exc_msg.find("Available columns") !=
                       std::string::npos,
               "AOSP message shape + available-columns list");
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
