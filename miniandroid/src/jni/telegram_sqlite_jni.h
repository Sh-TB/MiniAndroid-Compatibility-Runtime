/*
 * MiniAndroid Runtime — Telegram private SQLite JNI surface
 * S108 ROOT-017: org.telegram.SQLite.* native methods over REAL sqlite3.
 *
 * Telegram ships its own thin SQLite wrapper (org/telegram/SQLite/*) with
 * native methods instead of android.database.sqlite. The runtime previously
 * answered them as JNI-UNSUPPORTED — `step` returned the fail-soft 0, which
 * SQLiteCursor.next() reads as SQLITE_ROW ("row available") forever, so
 * every `while (cursor.next())` loop in MessagesStorage/LocationController
 * spun until the F084 halt-loop guard fired (50k visits) and killed the
 * whole launch chain at LaunchActivity APP BOUNDARY.
 *
 * This module mirrors the real TMessagesProj/jni/sqlite_database.c contract:
 *   opendb(path, name)      -> sqlite3_open_v2, handle = (jlong)(intptr_t)db
 *   prepare(db, sql)        -> sqlite3_prepare_v2
 *   step(stmt)              -> SQLITE_ROW -> 0, SQLITE_DONE -> 1, else -1
 *   bindXxx(stmt, idx, v)   -> sqlite3_bind_* (index passed 1-based, as-is)
 *   columnXxx(stmt, col)    -> sqlite3_column_* (0-based, as-is)
 *   beginTransaction/commit -> sqlite3_exec("BEGIN"/"COMMIT")
 *
 * Handles are raw pointer bits in a 64-bit long — exactly the real JNI
 * convention — which is why NativeCallContext::pos now carries full-width
 * longs (the legacy int_args view truncated them).
 */

#ifndef MINIANDROID_TELEGRAM_SQLITE_JNI_H
#define MINIANDROID_TELEGRAM_SQLITE_JNI_H

#include <sqlite3.h>
#include <string>
#include <filesystem>
#include <iostream>
#include "jni/jni_bridge.h"

namespace miniandroid {
namespace jni {
namespace telegram_sqlite {

inline bool g_logged_open = false;

// helper: statement handle -> sqlite3_stmt*
inline sqlite3_stmt* stmt_of(const NativeCallContext& ctx, size_t arg_index) {
    return reinterpret_cast<sqlite3_stmt*>(
        static_cast<intptr_t>(ctx.arg(arg_index).long_val));
}
inline sqlite3* db_of(const NativeCallContext& ctx, size_t arg_index) {
    return reinterpret_cast<sqlite3*>(
        static_cast<intptr_t>(ctx.arg(arg_index).long_val));
}

inline void register_all() {
    auto& bridge = JNIBridge::instance();

    // ── SQLiteDatabase natives ─────────────────────────────────────────
    // opendb(String, String)J  [instance: arg0=this, arg1=name, arg2=path]
    // Empirical DEX ground truth (forkgram 12.10.8): the Java <init> calls
    // opendb(cacheFile_full_path, filesDir_path) — the FIRST string is the
    // FULL path to the db file (e.g. "<filesDir>/cache4.db"), the SECOND
    // is the files dir (auxiliary). Real JNI opens the first string.
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteDatabase;", "opendb", "(Ljava/lang/String; Ljava/lang/String;)J",
        [](const NativeCallContext& ctx, int32_t&, int64_t& lr, float&, double&,
           std::string&, uint32_t&, bool&) {
            std::string a1 = ctx.arg(1).string_val;
            std::string a2 = ctx.arg(2).string_val;
            std::string file;
            if (!a1.empty() && a1.find('/') != std::string::npos) {
                file = a1;  // full path form
            } else if (!a1.empty()) {
                file = a2 + "/" + a1;  // bare name + dir form
            } else {
                file = a2 + "/cache.db";  // legacy fallback
            }
            // ensure the containing directory exists (files dir may be new)
            std::error_code ec;
            std::filesystem::path parent = std::filesystem::path(file).parent_path();
            if (!parent.empty()) std::filesystem::create_directories(parent, ec);
            sqlite3* db = nullptr;
            int rc = sqlite3_open_v2(file.c_str(), &db,
                                     SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE, nullptr);
            if (rc != SQLITE_OK || !db) {
                if (db) sqlite3_close(db);
                std::cerr << "[TG-SQLITE] opendb FAILED rc=" << rc << " file=" << file << std::endl;
                lr = 0;
                return;
            }
            if (!g_logged_open) {
                std::cerr << "[TG-SQLITE] opendb OK file=" << file << std::endl;
                g_logged_open = true;
            }
            lr = reinterpret_cast<intptr_t>(db);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "Telegram SQLiteDatabase.opendb -> real sqlite3");

    // beginTransaction(J)V  [arg1=dbHandle]
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteDatabase;", "beginTransaction", "(J)V",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3* db = db_of(ctx, 1);
            if (db) sqlite3_exec(db, "BEGIN TRANSACTION", nullptr, nullptr, nullptr);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "BEGIN TRANSACTION");

    // commitTransaction(J)V
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteDatabase;", "commitTransaction", "(J)V",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3* db = db_of(ctx, 1);
            if (db) sqlite3_exec(db, "COMMIT", nullptr, nullptr, nullptr);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "COMMIT");

    // closedb(J)V
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteDatabase;", "closedb", "(J)V",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3* db = db_of(ctx, 1);
            if (db) sqlite3_close_v2(db);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_close_v2");

    // ── SQLitePreparedStatement natives ────────────────────────────────
    // prepare(J db, String sql)J  [arg1=dbHandle, arg2=sql]
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLitePreparedStatement;", "prepare", "(J Ljava/lang/String;)J",
        [](const NativeCallContext& ctx, int32_t&, int64_t& lr, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3* db = db_of(ctx, 1);
            const std::string& sql = ctx.arg(2).string_val;
            if (!db) { lr = 0; return; }
            sqlite3_stmt* stmt = nullptr;
            int rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
            if (rc != SQLITE_OK || !stmt) {
                std::cerr << "[TG-SQLITE] prepare FAILED rc=" << rc
                          << " err=" << (db ? sqlite3_errmsg(db) : "no-db")
                          << " sql=" << sql.substr(0, 80) << std::endl;
                lr = 0;
                return;
            }
            lr = reinterpret_cast<intptr_t>(stmt);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_prepare_v2");

    // step(J)I  — Telegram convention: ROW->0, DONE->1, else -1
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLitePreparedStatement;", "step", "(J)I",
        [](const NativeCallContext& ctx, int32_t& ir, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            if (!stmt) { ir = -1; return; }
            int rc = sqlite3_step(stmt);
            if (rc == SQLITE_ROW) ir = 0;
            else if (rc == SQLITE_DONE) ir = 1;
            else ir = -1;
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_step (ROW=0 DONE=1)");

    // finalize(J)V
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLitePreparedStatement;", "finalize", "(J)V",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            if (stmt) sqlite3_finalize(stmt);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_finalize");

    // reset(J)V
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLitePreparedStatement;", "reset", "(J)V",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            if (stmt) sqlite3_reset(stmt);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_reset");

    // bindInt(J I I)V   [arg1=stmt, arg2=index, arg3=value]
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLitePreparedStatement;", "bindInt", "(J I I)V",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            if (stmt) sqlite3_bind_int(stmt, ctx.arg(2).int_val, ctx.arg(3).int_val);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_bind_int");

    // bindLong(J I J)V
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLitePreparedStatement;", "bindLong", "(J I J)V",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            if (stmt) sqlite3_bind_int64(stmt, ctx.arg(2).int_val, ctx.arg(3).long_val);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_bind_int64");

    // bindDouble(J I D)V
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLitePreparedStatement;", "bindDouble", "(J I D)V",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            if (stmt) sqlite3_bind_double(stmt, ctx.arg(2).int_val, ctx.arg(3).double_val);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_bind_double");

    // bindString(J I Ljava/lang/String;)V
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLitePreparedStatement;", "bindString", "(J I Ljava/lang/String;)V",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            if (stmt && ctx.arg(3).kind == NativeCallContext::Arg::Kind::STRING) {
                const std::string& s = ctx.arg(3).string_val;
                sqlite3_bind_text(stmt, ctx.arg(2).int_val, s.c_str(),
                                  static_cast<int>(s.size()), SQLITE_TRANSIENT);
            } else if (stmt) {
                sqlite3_bind_null(stmt, ctx.arg(2).int_val);
            }
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_bind_text");

    // bindNull(J I)V
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLitePreparedStatement;", "bindNull", "(J I)V",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            if (stmt) sqlite3_bind_null(stmt, ctx.arg(2).int_val);
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_bind_null");

    // ── SQLiteCursor natives (all take the STATEMENT handle) ───────────
    // columnCount(J)I
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteCursor;", "columnCount", "(J)I",
        [](const NativeCallContext& ctx, int32_t& ir, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            ir = stmt ? sqlite3_column_count(stmt) : 0;
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_column_count");

    // columnType(J I)I
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteCursor;", "columnType", "(J I)I",
        [](const NativeCallContext& ctx, int32_t& ir, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            ir = stmt ? sqlite3_column_type(stmt, ctx.arg(2).int_val) : 5 /*NULL*/;
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_column_type");

    // columnIsNull(J I)I  — 1 when SQL NULL
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteCursor;", "columnIsNull", "(J I)I",
        [](const NativeCallContext& ctx, int32_t& ir, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            ir = (stmt && sqlite3_column_type(stmt, ctx.arg(2).int_val) == SQLITE_NULL) ? 1 : 0;
        }, NativeImplType::REAL_NATIVE_LIBRARY, "column is NULL check");

    // columnIntValue(J I)I
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteCursor;", "columnIntValue", "(J I)I",
        [](const NativeCallContext& ctx, int32_t& ir, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            ir = stmt ? sqlite3_column_int(stmt, ctx.arg(2).int_val) : 0;
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_column_int");

    // columnLongValue(J I)J
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteCursor;", "columnLongValue", "(J I)J",
        [](const NativeCallContext& ctx, int32_t&, int64_t& lr, float&, double&,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            lr = stmt ? sqlite3_column_int64(stmt, ctx.arg(2).int_val) : 0;
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_column_int64");

    // columnDoubleValue(J I)D
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteCursor;", "columnDoubleValue", "(J I)D",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double& dr,
           std::string&, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            dr = stmt ? sqlite3_column_double(stmt, ctx.arg(2).int_val) : 0.0;
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_column_double");

    // columnStringValue(J I)Ljava/lang/String;  — real String via the
    // S108 string-result channel (NULL column -> null reference).
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteCursor;", "columnStringValue", "(J I)Ljava/lang/String;",
        [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&,
           std::string& sr, uint32_t&, bool&) {
            sqlite3_stmt* stmt = stmt_of(ctx, 1);
            if (!stmt) return;
            const unsigned char* text = sqlite3_column_text(stmt, ctx.arg(2).int_val);
            if (!text) return;  // SQL NULL -> null reference
            sr = std::string(reinterpret_cast<const char*>(text));
            mark_string_result();
        }, NativeImplType::REAL_NATIVE_LIBRARY, "sqlite3_column_text -> String");

    // columnByteArrayValue(J I)[B — needs heap array creation (later wave);
    // NULL is the safe answer: every Telegram call site null-guards blobs.
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteCursor;", "columnByteArrayValue", "(J I)[B",
        [](const NativeCallContext&, int32_t&, int64_t&, float&, double&,
           std::string&, uint32_t&, bool&) {},
        NativeImplType::HOST_COMPATIBILITY_STUB, "blob -> null (null-guarded at call sites)");

    // columnByteBufferValue(J I)J — 0 address (null NativeByteBuffer at the
    // Java side; call sites null-check before readInt32).
    bridge.register_native(
        "Lorg/telegram/SQLite/SQLiteCursor;", "columnByteBufferValue", "(J I)J",
        [](const NativeCallContext&, int32_t&, int64_t& lr, float&, double&,
           std::string&, uint32_t&, bool&) { lr = 0; },
        NativeImplType::HOST_COMPATIBILITY_STUB, "blob address 0 -> null buffer");

    std::cerr << "[TG-SQLITE] registered " << 20 << " org.telegram.SQLite natives over real sqlite3" << std::endl;
}

} // namespace telegram_sqlite
} // namespace jni
} // namespace miniandroid

#endif // MINIANDROID_TELEGRAM_SQLITE_JNI_H
