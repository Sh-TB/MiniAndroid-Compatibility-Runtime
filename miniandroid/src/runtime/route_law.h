// route_law.h — S188 Phase C/D: route decision at launch (THE ALLEY LAW).
//
// User directive (S188 W2): the runtime must determine, BEFORE execution,
// which alley (route) an application takes. A Java/View application must
// NOT pass through the HTML5 alley. An application that plays MKV must go
// through the MKV alley — an MP4 substitute is never creditable.
//
// The route profile is produced by tools/s188_route_classifier.py
// (reports/apk_routes/<pkg>.json, schema S188_APK_ROUTE_PROFILE_V1).
// This module loads it at `run` startup, prints the ROUTE DECISION, and
// provides three honest runtime facts:
//   * ROUTE_SURPRISE  — the app engaged a route the static profile did not
//                       predict. The classifier must be revised. Never
//                       hidden, never silenced.
//   * ROUTE_VIOLATION — the app engaged a route the profile explicitly
//                       forbids. Logged loudly; execution is not blocked
//                       (the APK itself decides its route at runtime), but
//                       the violation is recorded for the evidence trail.
//   * required capabilities — what this app NEEDS (published for coders).
//
// UNOBSERVED != PASS: loading a profile grants no impact credit.
#ifndef MINIANDROID_S188_ROUTE_LAW_H
#define MINIANDROID_S188_ROUTE_LAW_H

#include <set>
#include <string>
#include <vector>

namespace miniandroid {
namespace runtime {

struct RouteProfile {
    bool loaded = false;
    std::string pkg;
    std::string primary_route;
    std::vector<std::string> routes_detected;
    std::vector<std::string> routes_forbidden;
    std::vector<std::string> required_capabilities;

    bool route_forbidden(const std::string& r) const;
    bool route_predicted(const std::string& r) const;
};

class RouteLaw {
  public:
    static RouteLaw& instance();

    // Load reports/apk_routes/<stem>.json. Search order:
    //   1. $MINIANDROID_ROUTE_PROFILE_DIR/<stem>.json
    //   2. ./reports/apk_routes/<stem>.json
    //   3. ./miniandroid/reports/apk_routes/<stem>.json
    // Stem resolution: package_hint (from --package) wins; else the APK file
    // stem; installed paths (.../<pkg>-<rand>==/base.apk) are parsed back to
    // <pkg>. Returns true when a profile was loaded (result logged either way).
    bool load_for_apk(const std::string& apk_path,
                      const std::string& package_hint = std::string());

    const RouteProfile& profile() const { return profile_; }

    // Called when a subsystem engages at runtime. route e.g. "WEBVIEW",
    // "MEDIA", "LIBGDX". Logs ROUTE_SURPRISE / ROUTE_VIOLATION once per
    // (route, where) pair.
    void observe_route_engagement(const std::string& route,
                                  const std::string& where);

    // One-line ROUTE DECISION summary emitted at startup.
    std::string decision_line() const;

  private:
    RouteLaw() = default;
    RouteProfile profile_;
    std::set<std::string> reported_;
};

}  // namespace runtime
}  // namespace miniandroid

#endif  // MINIANDROID_S188_ROUTE_LAW_H
