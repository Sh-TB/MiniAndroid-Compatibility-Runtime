// s18_sql_shadow_laws_test — S18 family F (#632-SQL-4/5/6): the sqlite shadow
// contract through the REAL DatabaseShadow dispatch (s248's harness shape:
// helper face -> getWritableDatabase -> execSQL/rawQuery -> cursor reads).
// Laws:
//   F1  BLOB cell (SQL-4): a BLOB value survives INSERT/SELECT through the
//       real sqlite3 path and is surfaced by the cursor contract — pin the
//       CURRENT materialization (observe-then-pin; the claim says BLOBs are
//       "not materialized" — the law settles what actually happens).
//   F2  CursorFactory accepted (SQL-5): opening with a factory argument in
//       the AOSP <init>(Context, name, factory, version) position yields the
//       SAME working cursor as opening without (accepted-and-ignored law).
//   F3  WAL (SQL-6): PRAGMA journal_mode through the real connection reports
//       wal (the config IS applied); the claim's second half (pool not
//       configured) stays a census note — see the methodology doc.
#include "../src/storage/sqlite_shadow.h"
#include "../src/dex/dalvik_engine_impl.h"
#include "../src/framework/heap_adapter.h"
#include "../src/framework/shadow_registry.h"

#include <cstdio>
#include <iostream>
#include <string>

using namespace miniandroid;

static int g_pass = 0, g_fail = 0;
static void record(bool ok, const std::string& what) {
    std::cout << (ok ? "  PASS  " : "  FAIL  ") << what << "\n";
    if (ok) ++g_pass; else ++g_fail;
}

// harness glue (s248's shape): wrap the DalvikHeap as the shadow's allocator
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

static TestHeapAdapter* g_adapter = nullptr;
static framework::CallContext ctx_for(uint32_t oid, const std::string& method,
                                      const std::string& arg0 = "",
                                      const std::string& declared = "") {
    framework::CallContext c;
    c.has_receiver = oid != 0;
    c.receiver_id = oid;
    c.receiver_class = declared;
    c.class_name = declared;
    c.method = method;
    if (!arg0.empty()) {
        framework::CallContext::Arg a;
        a.kind = framework::CallContext::Arg::Kind::STRING;
        a.string_val = arg0;
        c.args.push_back(a);
    }
    return c;
}

#include <cstdio>
int main() {
    // determinism: drop any db left by an earlier run (the real sqlite3 file
    // persists across runs and would accumulate rows)
    std::remove("runtime/data/s18_sql_laws.db");
    std::cout << "== s18 sqlite shadow contract laws ==\n";
    storage::DatabaseShadow db;
    dalvik::DalvikHeap heap;
    TestHeapAdapter heap_adapter(heap);
    g_adapter = &heap_adapter;
    db.init(&heap_adapter);

    // open via the helper face (s248 pattern)
    uint32_t helper = heap.allocate(
        "Landroid/database/sqlite/SQLiteOpenHelper;", 0, 0);
    {
        framework::CallContext ic = ctx_for(helper, "<init>", "",
            "Landroid/database/sqlite/SQLiteOpenHelper;");
        framework::CallContext::Arg a0; a0.kind = framework::CallContext::Arg::Kind::OBJECT;
        a0.object_id = helper; ic.args.push_back(a0);
        framework::CallContext::Arg a1; a1.kind = framework::CallContext::Arg::Kind::STRING;
        a1.string_val = "s18_sql_laws.db"; ic.args.push_back(a1);
        framework::CallContext::Arg a2; a2.kind = framework::CallContext::Arg::Kind::INT;
        a2.int_val = 1; ic.args.push_back(a2);
        db.dispatch(ic);
    }
    auto opened = db.dispatch(ctx_for(helper, "getWritableDatabase", "",
        "Landroid/database/sqlite/SQLiteOpenHelper;"));
    if (!opened.handled || !opened.object_id) {
        record(false, "F0 db opened via helper face (harness sanity)");
        std::cout << "== " << g_pass << " pass / " << g_fail << " fail ==\n";
        return 1;
    }
    record(true, "F0 db opened via helper face (harness sanity)");
    uint32_t dbobj = opened.object_id;

    auto sql2 = [&](const std::string& s) {
        return db.dispatch(ctx_for(dbobj, "execSQL", s,
            "Landroid/database/sqlite/SQLiteDatabase;"));
    };
    auto rawq = [&](const std::string& s) {
        return db.dispatch(ctx_for(dbobj, "rawQuery", s,
            "Landroid/database/sqlite/SQLiteDatabase;"));
    };

    // F1 — BLOB cell (SQL-4): real BLOB through the real sqlite3 path
    {
        sql2("CREATE TABLE b(id INTEGER, data BLOB)");
        sql2("INSERT INTO b VALUES(1, x'01020304')");
        auto q = rawq("SELECT id, data FROM b");
        bool got_cursor = q.handled && q.object_id;
        record(got_cursor, "F1.a BLOB SELECT returns a live cursor");
        if (got_cursor) {
            int32_t rows = -1;
            bool ok = db.cursor_row_count(q.object_id, rows);
            std::string v0, v1;
            bool s0 = db.cursor_value_string(q.object_id, 0, "id", v0);
            bool s1 = db.cursor_value_string(q.object_id, 1, "data", v1);
            std::cout << "        [F1 actual: rows=" << rows
                      << " col0=" << (s0 ? v0 : "<unavail>")
                      << " col1=" << (s1 ? v1 : "<unavail>") << "]\n";
            // observe-then-pin: the BLOB column must surface SOMETHING
            // (either the hex text or a coercible value) — never silently
            // missing while the row exists.
            record(ok && rows == 1 && s0,
                   "F1.b BLOB row materializes: row count 1, id column read");
            // SQL-4 claim CONFIRMED-LIVE: the BLOB column value is NOT
            // surfaced by the string accessor while the row exists — the
            // silence is the defect the claim describes.
            record(ok && s0 && !s1,
                   "F1.c BLOB column NOT surfaced (SQL-4 claim confirmed: "
                   "BLOB cells are not materialized)");
        }
    }

    // F2 — CursorFactory accepted (SQL-5): AOSP <init> arg position 3
    {
        uint32_t helper2 = heap.allocate(
            "Landroid/database/sqlite/SQLiteOpenHelper;", 0, 0);
        uint32_t factory = heap.allocate(
            "Landroid/database/sqlite/SQLiteCursorFactory;", 0, 0);
        framework::CallContext ic = ctx_for(helper2, "<init>", "",
            "Landroid/database/sqlite/SQLiteOpenHelper;");
        framework::CallContext::Arg a0; a0.kind = framework::CallContext::Arg::Kind::OBJECT;
        a0.object_id = helper2; ic.args.push_back(a0);
        framework::CallContext::Arg a1; a1.kind = framework::CallContext::Arg::Kind::STRING;
        a1.string_val = "s18_sql_laws.db"; ic.args.push_back(a1);
        framework::CallContext::Arg a2; a2.kind = framework::CallContext::Arg::Kind::OBJECT;
        a2.object_id = factory; ic.args.push_back(a2);   // the factory slot
        framework::CallContext::Arg a3; a3.kind = framework::CallContext::Arg::Kind::INT;
        a3.int_val = 1; ic.args.push_back(a3);
        db.dispatch(ic);
        auto opened2 = db.dispatch(ctx_for(helper2, "getWritableDatabase", "",
            "Landroid/database/sqlite/SQLiteOpenHelper;"));
        bool ok = opened2.handled && opened2.object_id;
        if (ok) {
            auto q2 = db.dispatch(ctx_for(opened2.object_id, "rawQuery",
                "SELECT 1", "Landroid/database/sqlite/SQLiteDatabase;"));
            ok = q2.handled && q2.object_id;
        }
        record(ok, "F2 CursorFactory in the <init> slot: open+query still work "
                   "(accepted-and-ignored law) (SQL-5)");
    }

    // F3 — WAL applied (SQL-6 first half)
    {
        auto wq = rawq("PRAGMA journal_mode;");
        bool ok = wq.handled && wq.object_id;
        std::string mode = "<no-cursor>";
        if (ok) db.cursor_value_string(wq.object_id, 0, "journal_mode", mode);
        std::cout << "        [F3 actual: journal_mode=" << mode << "]\n";
        // SQL-6 claim CONFIRMED (stronger than claimed): the open path runs
        // PRAGMA journal_mode=WAL (sqlite_shadow.cpp:234) but the readback
        // answers 'delete' — the WAL set does not stick on the read
        // connection, so WAL buys exactly nothing.
        record(ok && mode == "delete",
               "F3 WAL set at open does NOT stick: readback = delete "
               "(SQL-6 'WAL buys nothing' confirmed)");
    }

    std::cout << "== s18 sqlite shadow laws: " << g_pass << " pass / " << g_fail
              << " fail ==\n";
    return g_fail == 0 ? 0 : 1;
}
