// install_inspection.h — GATE A (issue #370): INSTALL-ENVIRONMENT CAPABILITY
// inspection surface.
//
// ─────────────────────────────────────────────────────────────────────────
// LAW (issue #370 §15/§16): an agent must be able to inspect, from package
// identity alone, essentially every important installed-package fact —
// manifest/components, APK entries, resources, assets, DEX, native
// libraries, app data, external data, databases, preferences, provenance —
// as machine-readable output, INDEPENDENT of whether the application
// renders (GATE A ≠ GATE B/C). No silent success: absent things are
// reported as absent, unreadable things as unreadable.
//
// CLI:
//   miniandroid pkginspect --package <pkg> --data-root <root>
//                          [--what identity,manifest,entries,dex,resources,
//                                 assets,libs,media,data,external,dbs,prefs,
//                                 provenance] [--jsonl <out>] [-v]
//   miniandroid pkginspect --apk <path> [...]   # direct-APK mode (no store)
// ─────────────────────────────────────────────────────────────────────────
#ifndef MINIANDROID_INSTALL_INSPECTION_H
#define MINIANDROID_INSTALL_INSPECTION_H

#include <string>
#include <vector>

namespace miniandroid {
namespace gatea {

struct InspectRequest {
    std::string package;          // installed package name (store mode)
    std::string data_root;        // package store root
    std::string apk_path;         // direct-APK mode (no package store)
    std::string what = "all";     // comma-separated section filter / "all"
    std::string jsonl_out;        // optional full-fidelity JSONL dump path
    bool verbose = false;
};

// Returns the process exit code (0 = inspection emitted; 1 = input error).
int cmd_pkg_inspect(const InspectRequest& req);

// ZIP central-directory membership probe (GATE A helper for the runtime's
// System.loadLibrary law): true when `entry` exists in the APK. `stored`
// reports the compression method when found.
bool zip_contains_entry(const std::string& apk, const std::string& entry,
                        bool* stored);

// JSON string escape shared by the section emitters.
std::string jesc(const std::string& s);

} // namespace gatea
} // namespace miniandroid

#endif // MINIANDROID_INSTALL_INSPECTION_H
