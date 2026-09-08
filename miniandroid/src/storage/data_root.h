// data_root.h — M3 FINDING-012: ONE app-data root law for the whole runtime.
//
// ─────────────────────────────────────────────────────────────────────────
// LAW (AOSP frameworks/base, Context / Environment):
//   * Android anchors EVERY app's private storage at /data/data/<pkg>/
//     (getFilesDir, getCacheDir, getDatabasePath, getSharedPreferences
//     all resolve inside it). The anchor belongs to the DEVICE INSTANCE,
//     never to the invoking shell's CWD.
//   * MiniAndroid previously resolved all three storage consumers
//     (DatabaseShadow, SharedPreferences XML store, FileSandbox /
//     ApplicationContext) against the CWD-relative literal
//     "runtime/data". Consequence (observed on microtimer): two runs
//     launched from the same directory silently shared one SQLite file —
//     run 2 loaded run 1's Room rows and rendered a different first
//     frame, breaking the 3-run byte-determinism gate; the prior
//     session's identical runs were an ACCIDENT of launching from
//     different CWDs, not a protocol guarantee.
//   * LAW FIX: a single process-wide app-data root, default
//     "runtime/data" (back-compat), overridable per invocation via
//     --data-root <dir> or MINIANDROID_DATA_ROOT. Storage consumers must
//     NEVER hardcode the root literal again.
// ─────────────────────────────────────────────────────────────────────────
#ifndef MINIANDROID_DATA_ROOT_H
#define MINIANDROID_DATA_ROOT_H

#include <string>

namespace Storage {

/// Set the process-wide app-data root (one anchor for sqlite, prefs,
/// files). Forwards to DatabaseShadow::set_databases_dir so the sqlite
/// family obeys the same law. Creates the directory.
void set_app_data_root(const std::string& root);

/// Current app-data root (default "runtime/data" until overridden).
const std::string& app_data_root();

/// True once an explicit --data-root / env override was applied.
bool app_data_root_explicit();

} // namespace Storage

#endif // MINIANDROID_DATA_ROOT_H
