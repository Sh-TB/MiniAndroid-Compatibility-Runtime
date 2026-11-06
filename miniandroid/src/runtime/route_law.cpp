// route_law.cpp — S188 Phase C/D implementation. See route_law.h.
#include "route_law.h"

#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>

#include "../../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid {
namespace runtime {

using nlohmann::json;

bool RouteProfile::route_forbidden(const std::string& r) const {
    for (const auto& f : routes_forbidden) {
        if (f == r) return true;
    }
    return false;
}

bool RouteProfile::route_predicted(const std::string& r) const {
    for (const auto& d : routes_detected) {
        if (d == r) return true;
    }
    return false;
}

RouteLaw& RouteLaw::instance() {
    static RouteLaw law;
    return law;
}

static bool read_profile_file(const std::string& path, RouteProfile* out) {
    std::ifstream in(path);
    if (!in.good()) return false;
    json j;
    try {
        in >> j;
    } catch (...) {
        return false;
    }
    if (!j.is_object()) return false;
    out->loaded = true;
    out->pkg = j.value("pkg", std::string());
    out->primary_route = j.value("primary_route", std::string());
    if (j.contains("routes_detected") && j["routes_detected"].is_array()) {
        for (const auto& r : j["routes_detected"]) {
            if (r.is_object() && r.contains("route")) {
                out->routes_detected.push_back(
                    r["route"].get<std::string>());
            }
        }
    }
    if (j.contains("routes_forbidden") && j["routes_forbidden"].is_array()) {
        for (const auto& r : j["routes_forbidden"]) {
            if (r.is_object() && r.contains("route")) {
                out->routes_forbidden.push_back(
                    r["route"].get<std::string>());
            }
        }
    }
    if (j.contains("required_capabilities") &&
        j["required_capabilities"].is_array()) {
        for (const auto& c : j["required_capabilities"]) {
            if (c.is_object() && c.contains("cap")) {
                out->required_capabilities.push_back(
                    c["cap"].get<std::string>());
            }
        }
    }
    return true;
}

bool RouteLaw::load_for_apk(const std::string& apk_path,
                            const std::string& package_hint) {
    // Stem resolution law: an explicit --package hint wins; else the APK
    // file stem; installed code paths (.../<pkg>-<rand>==/base.apk) parse
    // back to <pkg> (strip the '-' suffix and '==' marker).
    std::string stem = package_hint;
    if (stem.empty()) {
        size_t slash = apk_path.find_last_of('/');
        std::string file = (slash == std::string::npos)
                               ? apk_path
                               : apk_path.substr(slash + 1);
        size_t dot = file.find('.');
        std::string base = (dot == std::string::npos) ? file
                                                      : file.substr(0, dot);
        stem = base;
        if (base == "base") {
            // .../<pkg>-<rand>==/base.apk → parent dir encodes the package.
            size_t dir_end = apk_path.find_last_of('/');
            if (dir_end != std::string::npos && dir_end > 0) {
                size_t dir_start = apk_path.find_last_of('/', dir_end - 1);
                std::string dir = apk_path.substr(
                    dir_start + 1, dir_end - dir_start - 1);
                size_t dash = dir.find('-');
                std::string cand = (dash == std::string::npos)
                                       ? dir
                                       : dir.substr(0, dash);
                while (!cand.empty() && (cand.back() == '=')) cand.pop_back();
                if (!cand.empty() && cand != "app") stem = cand;
            }
        }
    }

    const char* env_dir = std::getenv("MINIANDROID_ROUTE_PROFILE_DIR");
    std::vector<std::string> candidates;
    if (env_dir && *env_dir) {
        candidates.push_back(std::string(env_dir) + "/" + stem + ".json");
    }
    candidates.push_back("./reports/apk_routes/" + stem + ".json");
    candidates.push_back("./miniandroid/reports/apk_routes/" + stem + ".json");

    for (const auto& c : candidates) {
        if (read_profile_file(c, &profile_)) {
            std::cout << "[ROUTE] DECISION pkg=" << profile_.pkg
                      << " primary=" << profile_.primary_route
                      << " routes=";
            for (size_t i = 0; i < profile_.routes_detected.size(); ++i) {
                if (i) std::cout << "+";
                std::cout << profile_.routes_detected[i];
            }
            std::cout << " forbidden=";
            for (size_t i = 0; i < profile_.routes_forbidden.size(); ++i) {
                if (i) std::cout << "+";
                std::cout << profile_.routes_forbidden[i];
            }
            std::cout << " profile=" << c << std::endl;
            if (!profile_.required_capabilities.empty()) {
                std::cout << "[ROUTE] REQUIRED_CAPS pkg=" << profile_.pkg
                          << " caps=";
                for (size_t i = 0;
                     i < profile_.required_capabilities.size(); ++i) {
                    if (i) std::cout << ",";
                    std::cout << profile_.required_capabilities[i];
                }
                std::cout << std::endl;
            }
            return true;
        }
    }
    std::cout
        << "[ROUTE] NO_PROFILE for stem=" << stem
        << " — generate with tools/s188_route_classifier.py (S188 §4); "
           "runtime proceeds route-blind, which is NOT a pass."
        << std::endl;
    return false;
}

std::string RouteLaw::decision_line() const {
    if (!profile_.loaded) return "NO_PROFILE";
    return profile_.pkg + ":" + profile_.primary_route;
}

void RouteLaw::observe_route_engagement(const std::string& route,
                                        const std::string& where) {
    if (!profile_.loaded) return;  // route-blind run: nothing to compare
    std::string key = route + "@" + where;
    if (reported_.count(key)) return;
    reported_.insert(key);
    if (profile_.route_forbidden(route)) {
        std::cout << "[ROUTE_VIOLATION] route=" << route << " where=" << where
                  << " pkg=" << profile_.pkg
                  << " — profile forbids this alley for this APK "
                     "(S188 §1 alley law)" << std::endl;
    } else if (!profile_.route_predicted(route)) {
        std::cout << "[ROUTE_SURPRISE] route=" << route << " where=" << where
                  << " pkg=" << profile_.pkg
                  << " — static profile did not predict this engagement; "
                     "classifier must be revised (honest static limit)"
                  << std::endl;
    }
}

}  // namespace runtime
}  // namespace miniandroid
