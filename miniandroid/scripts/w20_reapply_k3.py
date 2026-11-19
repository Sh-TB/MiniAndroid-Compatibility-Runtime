#!/usr/bin/env python3
"""W20-K re-apply PART 3: WS5 sqlite, WS6 domain, SolCG bitmap fallback,
Frozen Options seeds, WS4 webview+drag, bridge entry drain, Makefile tests."""
def edit(path, old, new, count=1):
    s = open(path).read()
    n = s.count(old)
    assert n == count, f"{path}: pattern count {n} != {count}\n---\n{old[:120]}"
    open(path, 'w').write(s.replace(old, new))
    print(f"OK {path} ({old[:38].strip()}...)")

# ── WS5: sqlite_shadow.h public decl ────────────────────────────────────
edit('src/storage/sqlite_shadow.h',
'''    static const std::string& databases_dir();''',
'''    static const std::string& databases_dir();

    // W20-K (S237-WS5): public so the contract fixture can drive the exact
    // cursor surface the engine dispatches (s248_sqlite_cursor_contract).
    framework::CallResult cursor_dispatch(const framework::CallContext& ctx);''')
# remove the private duplicate decl
s = open('src/storage/sqlite_shadow.h').read()
dup = '''    framework::CallResult cursor_dispatch(const framework::CallContext
'''
# generic: the original private decl line
import re
priv = re.findall(r'^\s*(framework::CallResult cursor_dispatch\(const framework::CallContext& ctx\);)\s*$', s, re.M)
if len(priv) > 1:
    # remove the last (private) occurrence line
    idx = s.rfind(priv[0])
    s = s[:idx] + s[idx + len(priv[0]):].lstrip('\n')
    open('src/storage/sqlite_shadow.h','w').write(s)
    print("OK sqlite_shadow.h private dup removed")
else:
    print(f"sqlite dup count={len(priv)} (leave)")

# ── WS5: sqlite_shadow.cpp helper + law ─────────────────────────────────
edit('src/storage/sqlite_shadow.cpp',
'''framework::CallResult DatabaseShadow::cursor_dispatch(const framework::CallContext& ctx) {''',
'''// W20-K (S237-WS5, AOSP AbstractCursor.getColumnIndex @android-14 L323-360):
// shared column-name resolution — strip the table qualifier after the LAST
// '.' (the bug-903852 hack) and match case-insensitively. Used by both
// getColumnIndex and getColumnIndexOrThrow.
static bool column_index_ci(const std::vector<std::string>& columns,
                            const std::string& requested, int32_t* out) {
    std::string name = requested;
    size_t p = name.rfind('.');
    if (p != std::string::npos) name = name.substr(p + 1);
    for (size_t i = 0; i < columns.size(); i++) {
        const std::string& col = columns[i];
        if (col.size() == name.size()) {
            bool eq = true;
            for (size_t j = 0; j < col.size(); j++) {
                if (std::tolower((unsigned char)col[j]) !=
                    std::tolower((unsigned char)name[j])) {
                    eq = false;
                    break;
                }
            }
            if (eq) {
                *out = (int32_t)i;
                return true;
            }
        }
    }
    return false;
}

framework::CallResult DatabaseShadow::cursor_dispatch(const framework::CallContext& ctx) {''')

edit('src/storage/sqlite_shadow.cpp',
'''    if (m == "getColumnIndex" && ctx.args.size() >= 1) {
        for (size_t i = 0; i < c->columns.size(); i++) {
            if (c->columns[i] == ctx.args[0].string_val)
                return framework::CallResult::handled_int((int)i);
        }
        return framework::CallResult::handled_int(-1);
    }''',
'''    if (m == "getColumnIndex" && ctx.args.size() >= 1) {
        // W20-K (S237-WS5): AOSP law — qualifier strip + case-insensitive
        // match; missing column answers -1 (never throws).
        int32_t idx = -1;
        if (column_index_ci(c->columns, ctx.args[0].string_val, &idx))
            return framework::CallResult::handled_int(idx);
        return framework::CallResult::handled_int(-1);
    }''')

edit('src/storage/sqlite_shadow.cpp',
'''    if (m == "getColumnIndexOrThrow" && ctx.args.size() >= 1) {
        for (size_t i = 0; i < c->columns.size(); i++) {
            if (c->columns[i] == ctx.args[0].string_val)
                return framework::CallResult::handled_int((int)i);
        }
        std::cerr << "[SQLITE-SHADOW] getColumnIndexOrThrow: unknown column '"
                  << ctx.args[0].string_val << "' (caller " << ctx.receiver_class
                  << ")" << std::endl;
        return framework::CallResult::handled_exception(
            "Ljava/lang/IllegalArgumentException;",
            "Unknown column '" + ctx.args[0].string_val + "'");
    }''',
'''    if (m == "getColumnIndexOrThrow" && ctx.args.size() >= 1) {
        // W20-K (S237-WS5): AOSP matching + message shape with the
        // available-columns list.
        int32_t idx = -1;
        if (column_index_ci(c->columns, ctx.args[0].string_val, &idx))
            return framework::CallResult::handled_int(idx);
        std::string avail;
        for (size_t i = 0; i < c->columns.size(); i++) {
            if (i) avail += ", ";
            avail += c->columns[i];
        }
        std::cerr << "[SQLITE-SHADOW] getColumnIndexOrThrow: unknown column '"
                  << ctx.args[0].string_val << "' (caller " << ctx.receiver_class
                  << ")" << std::endl;
        return framework::CallResult::handled_exception(
            "Ljava/lang/IllegalArgumentException;",
            "column '" + ctx.args[0].string_val +
                "' does not exist. Available columns: [" + avail + "]");
    }''')

# ── WS6: domain make_long + INVALID_ROW_ID ──────────────────────────────
edit('src/dex/dalvik_bridge_domain_app_runtime.cpp',
'''        if (method == "getItemIdAtPosition") {
            result = DalvikValue::make_int(
                pos >= 0 ? pos : 0);
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }''',
'''        if (method == "getItemIdAtPosition") {
            // W20-K (S237-WS6, AOSP AdapterView.java L808-818): returns LONG
            // (Adapter.getItemId -> long); negative position answers
            // INVALID_ROW_ID = Long.MIN_VALUE, never 0 (which aliases row 0).
            result = DalvikValue::make_long(
                pos >= 0 ? (int64_t)pos
                         : std::numeric_limits<int64_t>::min());
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }''')

# ── WS6: <limits> include in the domain ─────────────────────────────────
edit('src/dex/dalvik_bridge_domain_app_runtime.cpp',
'''#include "dex/dalvik_bridge_frame.h"''',
'''#include "dex/dalvik_bridge_frame.h"
#include <limits>  // W20-K (S237-WS6): INVALID_ROW_ID''')

# ── WS7: bridge_to_api entry drain (748-line coordinator) ───────────────
edit('src/dex/dalvik_bridge.cpp',
'''    bridge_census_init();
    BridgeCensusGuard c97_census_guard;
    if (bridge_census().on) c97_census_guard.begin(class_name, method);''',
'''    bridge_census_init();
    BridgeCensusGuard c97_census_guard;
    if (bridge_census().on) c97_census_guard.begin(class_name, method);
    // W20-K (S237-WS7): deliver armed dialog lifecycle tokens (onShow /
    // onDismiss / onCancel) before processing this call — keeps delivery
    // near-synchronous when a dialog show/dismiss/cancel is followed by
    // further framework calls. No-op when nothing is armed.
    deliver_pending_dialog_callbacks();''')
print("PART 3 done")
