/*
 * UNIFIED_007 — ResourceRuntime: process-wide ARSC + LayoutInflater access.
 * Loaded lazily from the APK being executed; reused by ActivityShadow
 * (setContentView), TextView.setText(resid), renderer (drawable extraction),
 * and touch dispatch (onClick handler resolution).
 */
#ifndef MINIANDROID_RESOURCE_RUNTIME_H
#define MINIANDROID_RESOURCE_RUNTIME_H

#include <string>
#include <vector>
#include <memory>

#include "arsc_parser.h"
#include "axml_parser.h"
#include "layout_inflater.h"
#include "../apk/apk_parser.h"

namespace miniandroid {
namespace resources {

class ResourceRuntime {
public:
    static ResourceRuntime& instance();

    // Ensure ARSC + APK cache loaded for this APK. Returns false on failure.
    bool ensure_loaded(const std::string& apk_path);

    ArscParser& arsc() { return arsc_; }
    apk::ApkParser& apk() { return apk_; }
    // TICTACTOE-GOLDEN campaign: always return a usable inflater. The old
    // accessor dereferenced a null unique_ptr for APKs with no
    // resources.arsc (fixtures, plain-asset apps) the moment any code path
    // needed the layout engine without ARSC — e.g. the generic
    // setContentView(View) measure pass for programmatic View trees.
    LayoutInflater& inflater() {
        if (!inflater_) {
            metrics_ = DeviceMetrics{};
            inflater_ = std::make_unique<LayoutInflater>(arsc_, apk_, apk_path_, metrics_);
        }
        return *inflater_;
    }
    const DeviceMetrics& metrics() const { return metrics_; }
    bool loaded() const { return loaded_; }
    const std::string& apk_path() const { return apk_path_; }

    // Evidence dump
    std::string stats_json() const;

private:
    ResourceRuntime() = default;
    ArscParser arsc_;
    apk::ApkParser apk_;
    std::unique_ptr<LayoutInflater> inflater_;
    DeviceMetrics metrics_;
    bool loaded_ = false;
    std::string apk_path_;
    std::string load_error_;
};

} // namespace resources
} // namespace miniandroid

#endif // MINIANDROID_RESOURCE_RUNTIME_H
