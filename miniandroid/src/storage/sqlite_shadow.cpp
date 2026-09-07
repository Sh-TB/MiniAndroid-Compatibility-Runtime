// sqlite_shadow.cpp — M3 F-ROOM-CHAIN implementation (REAL sqlite3 backend).
// See sqlite_shadow.h for the law block.
#include "sqlite_shadow.h"

#include <sqlite3.h>

#include <algorithm>
#include <cerrno>
#include <cstdio>
#include <filesystem>
#include <iostream>
#include <sys/stat.h>

namespace fs = std::filesystem;

namespace miniandroid { namespace storage {

std::string DatabaseShadow::databases_dir_ = "runtime/data";

void DatabaseShadow::set_databases_dir(const std::string& dir) {
    databases_dir_ = dir;
}

const std::string& DatabaseShadow::databases_dir() { return databases_dir_; }

// ─────────────────────────────────────────────────────────────────────────
// Class claims: exact framework descriptors only (no catch-all). The
// receiver object may be an APP subclass (e.g. Room's obfuscated helper
// Lh/f extends SQLiteOpenHelper) — dispatch reaches us because the INVOKE
// declared class is the framework descriptor (invoke-super / inherited
// virtual) or because the engine's ancestry pass tries the parent.
// ─────────────────────────────────────────────────────────────────────────
bool DatabaseShadow::handles_class(const std::string& class_name) const {
    return class_name == "Landroid/database/sqlite/SQLiteOpenHelper;" ||
           class_name == "Landroid/database/sqlite/SQLiteDatabase;" ||
           class_name == "Landroid/database/sqlite/SQLiteStatement;" ||
           class_name == "Landroid/database/sqlite/SQLiteProgram;" ||
           class_name == "Landroid/database/sqlite/SQLiteCursor;" ||
           class_name == "Landroid/database/sqlite/SQLiteClosable;" ||
           class_name == "Landroid/database/Cursor;";
}

std::vector<std::string> DatabaseShadow::implemented_methods() const {
    return {
        "SQLiteOpenHelper.<init>", "getWritableDatabase", "getReadableDatabase",
        "getDatabaseName", "close", "setWriteAheadLoggingEnabled",
        "execSQL", "beginTransaction", "beginTransactionNonExclusive",
        "setTransactionSuccessful", "endTransaction", "inTransaction",
        "isOpen", "getPath", "getVersion", "compileStatement",
        "rawQueryWithFactory", "setMaxSqlCacheSize",
        "bindLong", "bindString", "bindNull", "bindDouble",
        "executeInsert", "executeUpdateDelete", "execute",
        "getCount", "getColumnCount", "getColumnIndex", "getColumnNames",
        "moveToFirst", "moveToNext", "moveToPosition",
        "getInt", "getLong", "getString", "isNull",
    };
}

// ─────────────────────────────────────────────────────────────────────────
// state lookup helpers
// ─────────────────────────────────────────────────────────────────────────
DatabaseShadow::HelperState* DatabaseShadow::helper_of(uint32_t oid) {
    auto it = helpers_.find(oid);
    return it == helpers_.end() ? nullptr : &it->second;
}
DatabaseShadow::DbState* DatabaseShadow::db_of(uint32_t oid) {
    auto it = dbs_.find(oid);
    return it == dbs_.end() ? nullptr : &it->second;
}
DatabaseShadow::StmtState* DatabaseShadow::stmt_of(uint32_t oid) {
    auto it = stmts_.find(oid);
    return it == stmts_.end() ? nullptr : &it->second;
}
DatabaseShadow::CursorState* DatabaseShadow::cursor_of(uint32_t oid) {
    auto it = cursors_.find(oid);
    return it == cursors_.end() ? nullptr : &it->second;
}
sqlite3* DatabaseShadow::sqlite_of(uint32_t db_oid) {
    DbState* s = db_of(db_oid);
    return s ? s->db : nullptr;
}

size_t DatabaseShadow::active_connections() const { return dbs_.size(); }
size_t DatabaseShadow::open_cursors() const { return cursors_.size(); }

bool DatabaseShadow::has_pending_lifecycle(uint32_t helper_oid) const {
    auto it = helpers_.find(helper_oid);
    return it != helpers_.end() &&
           (it->second.pending_create || it->second.pending_upgrade);
}

bool DatabaseShadow::consume_pending_create(uint32_t helper_oid) {
    HelperState* h = helper_of(helper_oid);
    if (!h || !h->pending_create) return false;
    h->pending_create = false;
    return true;
}

bool DatabaseShadow::consume_pending_upgrade(uint32_t helper_oid,
                                             int64_t& old_version,
                                             int64_t& new_version) {
    HelperState* h = helper_of(helper_oid);
    if (!h || !h->pending_upgrade) return false;
    h->pending_upgrade = false;
    old_version = h->upgrade_from;
    new_version = h->version;
    return true;
}

void DatabaseShadow::notify_lifecycle_callbacks_done(uint32_t helper_oid) {
    HelperState* h = helper_of(helper_oid);
    if (!h) return;
    sqlite3* raw = h->db_oid ? sqlite_of(h->db_oid) : nullptr;
    if (raw) {
        std::string pragma = "PRAGMA user_version = " + std::to_string(h->version) + ";";
        char* err = nullptr;
        if (sqlite3_exec(raw, pragma.c_str(), nullptr, nullptr, &err) != SQLITE_OK) {
            std::cerr << "[SQLITE-SHADOW] user_version persist failed: "
                      << (err ? err : "?") << std::endl;
            if (err) sqlite3_free(err);
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────
// open path — ART law: non-null db, onCreate/onUpgrade flagging
// ─────────────────────────────────────────────────────────────────────────
framework::CallResult DatabaseShadow::open_helper_database(uint32_t helper_oid,
                                                           const std::string&) {
    HelperState* h = helper_of(helper_oid);
    if (!h) return framework::CallResult::not_handled();

    // Already opened for this helper → same object every call (identity law).
    if (h->db_oid && db_of(h->db_oid) && db_of(h->db_oid)->db) {
        return framework::CallResult::handled_object(
            h->db_oid, "Landroid/database/sqlite/SQLiteDatabase;");
    }

    DbState st;
    if (h->db_name.empty() || h->db_name == ":memory:") {
        st.path = ":memory:";
    } else {
        fs::path dir(databases_dir_);
        std::error_code ec;
        fs::create_directories(dir, ec);
        st.path = (dir / h->db_name).string();
    }

    sqlite3* raw = nullptr;
    int flags = SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE;
    int rc = h->db_name.empty() || h->db_name == ":memory:"
                 ? sqlite3_open_v2(":memory:", &raw, flags, nullptr)
                 : sqlite3_open_v2(st.path.c_str(), &raw, flags, nullptr);
    if (rc != SQLITE_OK) {
        std::cerr << "[SQLITE-SHADOW] open failed rc=" << rc << " path=" << st.path
                  << " err=" << (raw ? sqlite3_errmsg(raw) : "?") << std::endl;
        if (raw) sqlite3_close(raw);
        // ART throws SQLiteException here; never returns null. Returning the
        // null-object result would resurrect the exact F-ROOM-CHAIN bug.
        return framework::CallResult::not_handled();
    }
    st.db = raw;

    // Version gate — real PRAGMA user_version, matching AOSP SQLiteOpenHelper.
    int uv = 0;
    {
        sqlite3_stmt* q = nullptr;
        if (sqlite3_prepare_v2(raw, "PRAGMA user_version;", -1, &q, nullptr) == SQLITE_OK &&
            sqlite3_step(q) == SQLITE_ROW) {
            uv = sqlite3_column_int(q, 0);
        }
        if (q) sqlite3_finalize(q);
    }
    if (uv == 0) {
        h->pending_create = true;
    } else if (uv != h->version) {
        h->pending_upgrade = true;
        h->upgrade_from = uv;
    }

    uint32_t db_oid = heap_->allocate("Landroid/database/sqlite/SQLiteDatabase;");
    h->db_oid = db_oid;
    dbs_[db_oid] = st;

    std::cerr << "[SQLITE-SHADOW] opened db oid=" << db_oid << " path=" << st.path
              << " user_version=" << uv << " target_version=" << h->version
              << (h->pending_create ? " [onCreate pending]"
                  : (h->pending_upgrade ? " [onUpgrade pending]" : ""))
              << std::endl;
    return framework::CallResult::handled_object(
        db_oid, "Landroid/database/sqlite/SQLiteDatabase;");
}

// ─────────────────────────────────────────────────────────────────────────
// dispatch entry
// ─────────────────────────────────────────────────────────────────────────
framework::CallResult DatabaseShadow::dispatch(const framework::CallContext& ctx) {
    if (ctx.class_name == "Landroid/database/sqlite/SQLiteOpenHelper;")
        return helper_dispatch(ctx);
    if (ctx.class_name == "Landroid/database/sqlite/SQLiteDatabase;")
        return db_dispatch(ctx);
    if (ctx.class_name == "Landroid/database/sqlite/SQLiteStatement;" ||
        ctx.class_name == "Landroid/database/sqlite/SQLiteProgram;")
        return stmt_dispatch(ctx);
    if (ctx.class_name == "Landroid/database/sqlite/SQLiteCursor;" ||
        ctx.class_name == "Landroid/database/Cursor;" ||
        ctx.class_name == "Landroid/database/sqlite/SQLiteClosable;")
        return cursor_dispatch(ctx);
    return framework::CallResult::not_handled();
}

framework::CallResult DatabaseShadow::helper_dispatch(const framework::CallContext& ctx) {
    const std::string& m = ctx.method;
    uint32_t this_oid = ctx.has_receiver ? ctx.receiver_id : 0;

    if (m == "<init>") {
        // (Context, String name, CursorFactory, int version[, DatabaseErrorHandler])
        HelperState h;
        // name: first STRING arg; version: first INT/LONG arg after position 2.
        for (size_t i = 1; i < ctx.args.size(); i++) {
            const auto& a = ctx.args[i];
            if (a.kind == framework::CallContext::Arg::Kind::STRING &&
                h.db_name.empty()) {
                h.db_name = a.string_val;
            }
        }
        for (int i = (int)ctx.args.size() - 1; i >= 1; i--) {
            const auto& a = ctx.args[i];
            if (a.kind == framework::CallContext::Arg::Kind::INT) {
                h.version = a.int_val;
                break;
            }
        }
        helpers_[this_oid] = h;
        std::cerr << "[SQLITE-SHADOW] helper<init> oid=" << this_oid
                  << " name=\"" << h.db_name << "\" version=" << h.version
                  << std::endl;
        return framework::CallResult::handled_void();
    }
    if (m == "getWritableDatabase" || m == "getReadableDatabase") {
        if (!ctx.has_receiver) return framework::CallResult::not_handled();
        return open_helper_database(this_oid, ctx.receiver_class);
    }
    if (m == "getDatabaseName") {
        HelperState* h = helper_of(this_oid);
        return h ? framework::CallResult::handled_string(h->db_name)
                 : framework::CallResult::handled_null();
    }
    if (m == "setWriteAheadLoggingEnabled") {
        HelperState* h = helper_of(this_oid);
        if (h && !ctx.args.empty()) h->wal_requested = ctx.args[0].bool_val;
        // Journal mode intentionally left default for byte-determinism; the
        // flag is recorded for isOpen/isWriteAheadLoggingEnabled law answers.
        return framework::CallResult::handled_void();
    }
    if (m == "close") {
        HelperState* h = helper_of(this_oid);
        if (h && h->db_oid) close_db(h->db_oid);
        return framework::CallResult::handled_void();
    }
    return framework::CallResult::not_handled();
}

void DatabaseShadow::close_db(uint32_t db_oid) {
    DbState* s = db_of(db_oid);
    if (!s) return;
    if (s->db) {
        sqlite3_close(s->db);
        s->db = nullptr;
    }
}

void DatabaseShadow::finalize_stmt(uint32_t stmt_oid) {
    StmtState* s = stmt_of(stmt_oid);
    if (!s) return;
    if (s->stmt) {
        sqlite3_finalize(s->stmt);
        s->stmt = nullptr;
    }
}

void DatabaseShadow::close_cursor(uint32_t cursor_oid) {
    CursorState* c = cursor_of(cursor_oid);
    if (c) c->closed = true;
}

framework::CallResult DatabaseShadow::db_dispatch(const framework::CallContext& ctx) {
    const std::string& m = ctx.method;
    uint32_t db_oid = ctx.has_receiver ? ctx.receiver_id : 0;
    DbState* st = db_of(db_oid);
    sqlite3* raw = st ? st->db : nullptr;

    if (m == "execSQL" && ctx.args.size() >= 1 &&
        ctx.args[0].kind == framework::CallContext::Arg::Kind::STRING) {
        if (!raw) return framework::CallResult::not_handled();
        char* err = nullptr;
        int rc = sqlite3_exec(raw, ctx.args[0].string_val.c_str(), nullptr, nullptr, &err);
        if (rc != SQLITE_OK) {
            std::cerr << "[SQLITE-SHADOW] execSQL rc=" << rc << " err="
                      << (err ? err : "?") << " sql=\""
                      << ctx.args[0].string_val.substr(
                             0, std::min<size_t>(120, ctx.args[0].string_val.size()))
                      << "\" (caller " << ctx.receiver_class << ")" << std::endl;
            if (err) sqlite3_free(err);
            // Deviation note (documented): ART throws SQLiteException; the
            // CallResult channel has no exception kind yet, so the failure
            // is loud on stderr but non-fatal. Do NOT hide: the diagnostic
            // carries caller + SQL head.
            return framework::CallResult::handled_void();
        }
        return framework::CallResult::handled_void();
    }
    if (m == "beginTransaction" || m == "beginTransactionNonExclusive") {
        if (!raw) return framework::CallResult::not_handled();
        char* err = nullptr;
        sqlite3_exec(raw, "BEGIN;", nullptr, nullptr, &err);
        if (err) sqlite3_free(err);
        st->in_transaction = true;
        st->tx_successful = false;
        return framework::CallResult::handled_void();
    }
    if (m == "setTransactionSuccessful") {
        if (st) st->tx_successful = true;
        return framework::CallResult::handled_void();
    }
    if (m == "endTransaction") {
        if (!raw) return framework::CallResult::not_handled();
        char* err = nullptr;
        sqlite3_exec(raw, st->tx_successful ? "COMMIT;" : "ROLLBACK;", nullptr,
                     nullptr, &err);
        if (err) sqlite3_free(err);
        st->in_transaction = false;
        st->tx_successful = false;
        return framework::CallResult::handled_void();
    }
    if (m == "inTransaction") {
        return framework::CallResult::handled_bool(
            raw ? sqlite3_get_autocommit(raw) == 0 : false);
    }
    if (m == "isOpen") {
        return framework::CallResult::handled_bool(raw != nullptr);
    }
    if (m == "isWriteAheadLoggingEnabled") {
        return framework::CallResult::handled_bool(st ? st->wal_enabled : false);
    }
    if (m == "getPath") {
        return framework::CallResult::handled_string(st ? st->path : std::string());
    }
    if (m == "getVersion") {
        int uv = 0;
        if (raw) {
            sqlite3_stmt* q = nullptr;
            if (sqlite3_prepare_v2(raw, "PRAGMA user_version;", -1, &q, nullptr) ==
                    SQLITE_OK &&
                sqlite3_step(q) == SQLITE_ROW) {
                uv = sqlite3_column_int(q, 0);
            }
            if (q) sqlite3_finalize(q);
        }
        return framework::CallResult::handled_int(uv);
    }
    if (m == "setMaxSqlCacheSize") {
        return framework::CallResult::handled_void();
    }
    if (m == "compileStatement" && ctx.args.size() >= 1 &&
        ctx.args[0].kind == framework::CallContext::Arg::Kind::STRING) {
        if (!raw) return framework::CallResult::not_handled();
        sqlite3_stmt* ps = nullptr;
        int rc = sqlite3_prepare_v2(raw, ctx.args[0].string_val.c_str(), -1, &ps, nullptr);
        if (rc != SQLITE_OK) {
            std::cerr << "[SQLITE-SHADOW] compileStatement rc=" << rc << " err="
                      << sqlite3_errmsg(raw) << " sql=\"" << ctx.args[0].string_val
                      << "\"" << std::endl;
            return framework::CallResult::not_handled();
        }
        uint32_t stmt_oid = heap_->allocate("Landroid/database/sqlite/SQLiteStatement;");
        StmtState ss;
        ss.stmt = ps;
        ss.db_oid = db_oid;
        stmts_[stmt_oid] = ss;
        return framework::CallResult::handled_object(
            stmt_oid, "Landroid/database/sqlite/SQLiteStatement;");
    }
    if (m == "rawQueryWithFactory" && ctx.args.size() >= 3 &&
        ctx.args[1].kind == framework::CallContext::Arg::Kind::STRING) {
        // (factory, sql, selectionArgs[], editTable[, cancellationSignal])
        if (!raw) return framework::CallResult::not_handled();
        const std::string& sql = ctx.args[1].string_val;
        sqlite3_stmt* ps = nullptr;
        int rc = sqlite3_prepare_v2(raw, sql.c_str(), -1, &ps, nullptr);
        if (rc != SQLITE_OK) {
            std::cerr << "[SQLITE-SHADOW] rawQuery rc=" << rc << " err="
                      << sqlite3_errmsg(raw) << " sql=\"" << sql << "\"" << std::endl;
            return framework::CallResult::not_handled();
        }
        // Bind selectionArgs (1-based).
        if (ctx.args.size() >= 3 &&
            ctx.args[2].kind == framework::CallContext::Arg::Kind::OBJECT) {
            uint32_t arr_oid = ctx.args[2].object_id;
            int32_t n = 0;
            heap_->get_object_array_length(arr_oid, n);
            for (int64_t i = 0; i < n; i++) {
                std::string sv;
                if (heap_->get_object_array_string_element(arr_oid, (size_t)i, sv)) {
                    sqlite3_bind_text(ps, (int)(i + 1), sv.c_str(), -1,
                                      SQLITE_TRANSIENT);
                } else {
                    sqlite3_bind_null(ps, (int)(i + 1));
                }
            }
        }
        // Materialize the full result set (deterministic single-thread law).
        CursorState cs;
        int ncols = sqlite3_column_count(ps);
        for (int c = 0; c < ncols; c++) {
            const char* nm = sqlite3_column_name(ps, c);
            cs.columns.push_back(nm ? nm : "");
        }
        while (sqlite3_step(ps) == SQLITE_ROW) {
            std::vector<CursorState::Cell> row(ncols);
            for (int c = 0; c < ncols; c++) {
                if (sqlite3_column_type(ps, c) == SQLITE_NULL) {
                    row[c].kind = CursorState::Cell::Kind::NULLV;
                } else if (sqlite3_column_type(ps, c) == SQLITE_TEXT) {
                    const unsigned char* txt = sqlite3_column_text(ps, c);
                    row[c].kind = CursorState::Cell::Kind::STRING;
                    row[c].string_val = txt ? reinterpret_cast<const char*>(txt) : "";
                } else {
                    row[c].kind = CursorState::Cell::Kind::LONG;
                    row[c].long_val = sqlite3_column_int64(ps, c);
                }
            }
            cs.rows.push_back(std::move(row));
        }
        sqlite3_finalize(ps);
        uint32_t cur_oid = heap_->allocate("Landroid/database/sqlite/SQLiteCursor;");
        cursors_[cur_oid] = std::move(cs);
        std::cerr << "[SQLITE-SHADOW] rawQuery rows=" << cursors_[cur_oid].rows.size()
                  << " cols=" << ncols << " sql=\""
                  << sql.substr(0, std::min<size_t>(100, sql.size())) << "\""
                  << std::endl;
        return framework::CallResult::handled_object(
            cur_oid, "Landroid/database/sqlite/SQLiteCursor;");
    }
    if (m == "close") {
        close_db(db_oid);
        return framework::CallResult::handled_void();
    }
    return framework::CallResult::not_handled();
}

framework::CallResult DatabaseShadow::stmt_dispatch(const framework::CallContext& ctx) {
    const std::string& m = ctx.method;
    uint32_t stmt_oid = ctx.has_receiver ? ctx.receiver_id : 0;
    StmtState* s = stmt_of(stmt_oid);
    if (!s || !s->stmt) return framework::CallResult::not_handled();
    sqlite3_stmt* ps = s->stmt;

    if (m == "bindLong" && ctx.args.size() >= 2) {
        int64_t v = ctx.args[1].kind == framework::CallContext::Arg::Kind::LONG
                        ? ctx.args[1].long_val
                        : (int64_t)ctx.args[1].int_val;
        sqlite3_bind_int64(ps, ctx.args[0].int_val, v);
        if (std::getenv("MINIANDROID_TRACE_FRAMES")) {
            std::cerr << "[SQLITE-BIND] stmt=" << stmt_oid
                      << " idx=" << ctx.args[0].int_val << " long=" << v
                      << std::endl;
        }
        return framework::CallResult::handled_void();
    }
    if (m == "bindString" && ctx.args.size() >= 2) {
        sqlite3_bind_text(ps, ctx.args[0].int_val, ctx.args[1].string_val.c_str(), -1,
                          SQLITE_TRANSIENT);
        if (std::getenv("MINIANDROID_TRACE_FRAMES")) {
            std::cerr << "[SQLITE-BIND] stmt=" << stmt_oid
                      << " idx=" << ctx.args[0].int_val
                      << " str=\"" << ctx.args[1].string_val << "\"" << std::endl;
        }
        return framework::CallResult::handled_void();
    }
    if (m == "bindNull") {
        sqlite3_bind_null(ps, ctx.args[0].int_val);
        if (std::getenv("MINIANDROID_TRACE_FRAMES")) {
            std::cerr << "[SQLITE-BIND] stmt=" << stmt_oid
                      << " idx=" << ctx.args[0].int_val << " NULL" << std::endl;
        }
        return framework::CallResult::handled_void();
    }
    if (m == "bindDouble" && ctx.args.size() >= 2) {
        sqlite3_bind_double(ps, ctx.args[0].int_val,
                            ctx.args[1].kind == framework::CallContext::Arg::Kind::DOUBLE
                                ? ctx.args[1].double_val
                                : (double)ctx.args[1].float_val);
        return framework::CallResult::handled_void();
    }
    if (m == "bindBlob") {
        sqlite3_bind_zeroblob(ps, ctx.args[0].int_val, 0);
        return framework::CallResult::handled_void();
    }
    if (m == "executeInsert") {
        int rc = sqlite3_step(ps);
        if (rc != SQLITE_DONE) {
            std::cerr << "[SQLITE-SHADOW] executeInsert step rc=" << rc << " err="
                      << sqlite3_errmsg(sqlite3_db_handle(ps)) << std::endl;
            sqlite3_reset(ps);
            return framework::CallResult::handled_long(-1);
        }
        int64_t rowid = sqlite3_last_insert_rowid(sqlite3_db_handle(ps));
        sqlite3_reset(ps);
        return framework::CallResult::handled_long(rowid);
    }
    if (m == "executeUpdateDelete") {
        int rc = sqlite3_step(ps);
        int changed = rc == SQLITE_DONE ? sqlite3_changes(sqlite3_db_handle(ps)) : -1;
        if (rc != SQLITE_DONE) {
            std::cerr << "[SQLITE-SHADOW] executeUpdateDelete rc=" << rc << std::endl;
        }
        sqlite3_reset(ps);
        return framework::CallResult::handled_int(changed);
    }
    if (m == "execute") {
        int rc = sqlite3_step(ps);
        if (rc != SQLITE_DONE) {
            std::cerr << "[SQLITE-SHADOW] execute rc=" << rc << " err="
                      << sqlite3_errmsg(sqlite3_db_handle(ps)) << std::endl;
        }
        sqlite3_reset(ps);
        return framework::CallResult::handled_void();
    }
    if (m == "close") {
        finalize_stmt(stmt_oid);
        return framework::CallResult::handled_void();
    }
    return framework::CallResult::not_handled();
}

framework::CallResult DatabaseShadow::cursor_dispatch(const framework::CallContext& ctx) {
    const std::string& m = ctx.method;
    uint32_t cur_oid = ctx.has_receiver ? ctx.receiver_id : 0;
    CursorState* c = cursor_of(cur_oid);
    if (!c) return framework::CallResult::not_handled();

    if (m == "getCount") return framework::CallResult::handled_int((int)c->rows.size());
    if (m == "getColumnCount")
        return framework::CallResult::handled_int((int)c->columns.size());
    if (m == "getColumnIndex" && ctx.args.size() >= 1) {
        for (size_t i = 0; i < c->columns.size(); i++) {
            if (c->columns[i] == ctx.args[0].string_val)
                return framework::CallResult::handled_int((int)i);
        }
        return framework::CallResult::handled_int(-1);
    }
    if (m == "getColumnNames") {
        uint32_t arr = heap_->allocate("Larray;");
        heap_->set_object_int_field(arr, "__array_length__", (int32_t)c->columns.size());
        for (size_t i = 0; i < c->columns.size(); i++) {
            heap_->set_object_string_field(arr, "array[" + std::to_string(i) + "]",
                                           c->columns[i]);
        }
        return framework::CallResult::handled_object(arr, "Larray;");
    }
    if (m == "moveToFirst") {
        c->pos = c->rows.empty() ? -1 : 0;
        return framework::CallResult::handled_bool(!c->rows.empty());
    }
    if (m == "moveToNext") {
        if (c->pos + 1 < (int)c->rows.size()) {
            c->pos++;
            return framework::CallResult::handled_bool(true);
        }
        c->pos = (int)c->rows.size();
        return framework::CallResult::handled_bool(false);
    }
    if (m == "moveToPosition") {
        int p = ctx.args[0].int_val;
        if (p >= 0 && p < (int)c->rows.size()) {
            c->pos = p;
            return framework::CallResult::handled_bool(true);
        }
        c->pos = (int)c->rows.size();
        return framework::CallResult::handled_bool(false);
    }
    bool row_ok = c->pos >= 0 && c->pos < (int)c->rows.size();
    if (m == "getInt" && row_ok) {
        const auto& cell = c->rows[c->pos][ctx.args[0].int_val];
        return framework::CallResult::handled_int((int32_t)cell.long_val);
    }
    if (m == "getLong" && row_ok) {
        const auto& cell = c->rows[c->pos][ctx.args[0].int_val];
        return framework::CallResult::handled_long(cell.long_val);
    }
    if (m == "getString" && row_ok) {
        const auto& cell = c->rows[c->pos][ctx.args[0].int_val];
        return framework::CallResult::handled_string(
            cell.kind == CursorState::Cell::Kind::STRING ? cell.string_val
                                                         : std::string());
    }
    if (m == "isNull" && row_ok) {
        const auto& cell = c->rows[c->pos][ctx.args[0].int_val];
        return framework::CallResult::handled_bool(
            cell.kind == CursorState::Cell::Kind::NULLV);
    }
    if (m == "close") {
        close_cursor(cur_oid);
        return framework::CallResult::handled_void();
    }
    return framework::CallResult::not_handled();
}

}} // namespace miniandroid::storage
