// sqlite_shadow.h — M3 F-ROOM-CHAIN: SQLite family shadow (REAL sqlite3).
//
// ─────────────────────────────────────────────────────────────────────────
// LAW (AOSP frameworks/base + SQLite project):
//   * SQLiteOpenHelper.getWritableDatabase()/getReadableDatabase() MUST
//     return a NON-NULL SQLiteDatabase. On first open the helper invokes
//     the app override onCreate(SQLiteDatabase) (virtual, real DEX) and
//     then persists PRAGMA user_version = requested version. A version
//     bump invokes onUpgrade(old, new) instead. ART never returns null —
//     a null here is what collapsed microtimer's Alarm.expiresMs to zero
//     (the app's R8-inlined Kotlin Intrinsics null-check threw, the
//     artifact AIOOBE from the stack walk was swallowed, and the whole
//     Room open chain silently died → no tick scheduling).
//   * SQLiteDatabase is backed by a REAL SQLite database file under the
//     app sandbox (databases/<name>), exactly like /data/data/<pkg>/
//     databases on a device. Room's generated SQL (CREATE TABLE /
//     INSERT OR ABORT / UPDATE OR ABORT / SELECT) executes for real.
//   * Determinism: the single-threaded deterministic runtime means one
//     connection, sequenced statements; queries MATERIALIZ their full
//     result set into the cursor object at query time (no lazy stepping
//     across frame boundaries).
//
// Lifecycle callbacks (onCreate/onUpgrade) are fired ENGINE-SIDE via
// try_recursive_invoke — see DalvikExecutionEngine::bridge_to_api —
// because shadows have no interpreter access. The shadow only records
// pending_create / pending_upgrade; the engine consumes the flags right
// after a successful open dispatch.
// ─────────────────────────────────────────────────────────────────────────
#ifndef MINIANDROID_SQLITE_SHADOW_H
#define MINIANDROID_SQLITE_SHADOW_H

#include "../framework/shadow_registry.h"

#include <string>
#include <unordered_map>
#include <vector>

struct sqlite3;
struct sqlite3_stmt;

namespace miniandroid { namespace storage {

class DatabaseShadow : public framework::Shadow {
public:
    // Engine sets this at APK load: <sandbox>/<package>/databases.
    // Default keeps parity with the SharedPreferences bridge path.
    static void set_databases_dir(const std::string& dir);
    static const std::string& databases_dir();

    std::string name() const override { return "DatabaseShadow"; }
    bool handles_class(const std::string& class_name) const override;
    framework::CallResult dispatch(const framework::CallContext& ctx) override;
    std::vector<std::string> implemented_methods() const override;

    // ── engine-side lifecycle callback protocol ──────────────────────────
    // True when this helper oid has a pending onCreate/onUpgrade flag —
    // the engine polls this after ANY successful open-method dispatch
    // (the declared class at the call site may be the app subclass, not
    // SQLiteOpenHelper, because dispatch reaches us via the superclass
    // retry pass).
    bool has_pending_lifecycle(uint32_t helper_oid) const;
    // Returns true exactly once per open that needs the app onCreate.
    bool consume_pending_create(uint32_t helper_oid);
    // Returns true exactly once per open that needs onUpgrade; fills versions.
    bool consume_pending_upgrade(uint32_t helper_oid, int64_t& old_version,
                                 int64_t& new_version);
    // Engine calls after the onCreate/onUpgrade DEX callback returned:
    // persists PRAGMA user_version = requested version.
    void notify_lifecycle_callbacks_done(uint32_t helper_oid);

    size_t active_connections() const;
    size_t open_cursors() const;

private:
    struct HelperState {
        std::string db_name;
        int64_t version = 1;
        uint32_t db_oid = 0;       // cached SQLiteDatabase heap object
        bool pending_create = false;
        bool pending_upgrade = false;
        int64_t upgrade_from = 0;
        bool wal_requested = false;
    };
    struct DbState {
        sqlite3* db = nullptr;
        std::string path;          // ":memory:" or sandbox file path
        bool in_transaction = false;
        bool tx_successful = false;
        bool wal_enabled = false;
    };
    struct StmtState {
        sqlite3_stmt* stmt = nullptr;
        uint32_t db_oid = 0;
    };
    struct CursorState {
        std::vector<std::string> columns;
        // Row cell values (variant of the CallContext::Arg kinds we need).
        struct Cell {
            enum class Kind { LONG, STRING, NULLV } kind = Kind::NULLV;
            int64_t long_val = 0;
            std::string string_val;
        };
        std::vector<std::vector<Cell>> rows;
        int pos = -1;              // -1 = before first (AOSP Cursor law)
        bool closed = false;
    };

    framework::CallResult helper_dispatch(const framework::CallContext& ctx);
    framework::CallResult db_dispatch(const framework::CallContext& ctx);
    framework::CallResult stmt_dispatch(const framework::CallContext& ctx);
    framework::CallResult cursor_dispatch(const framework::CallContext& ctx);

    // Shared query materialization for rawQuery / rawQueryWithFactory
    // (F-026: bare rawQuery(String,String[]) previously had NO handler —
    // the fail-soft bridge turned every scalar read into a null cursor).
    framework::CallResult raw_query_common(sqlite3* raw, const std::string& sql,
                                           uint32_t bind_array_oid);

    // Shared open path for getWritableDatabase/getReadableDatabase.
    framework::CallResult open_helper_database(uint32_t helper_oid,
                                               const std::string& helper_class);

    HelperState* helper_of(uint32_t oid);
    DbState* db_of(uint32_t oid);
    StmtState* stmt_of(uint32_t oid);
    CursorState* cursor_of(uint32_t oid);
    sqlite3* sqlite_of(uint32_t db_oid);

    void close_db(uint32_t db_oid);
    void finalize_stmt(uint32_t stmt_oid);
    void close_cursor(uint32_t cursor_oid);

    std::unordered_map<uint32_t, HelperState> helpers_;
    std::unordered_map<uint32_t, DbState> dbs_;
    std::unordered_map<uint32_t, StmtState> stmts_;
    std::unordered_map<uint32_t, CursorState> cursors_;

    static std::string databases_dir_;
};

}} // namespace miniandroid::storage

#endif // MINIANDROID_SQLITE_SHADOW_H
