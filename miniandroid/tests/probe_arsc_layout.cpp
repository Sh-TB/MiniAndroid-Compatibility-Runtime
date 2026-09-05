// probe_arsc_layout.cpp — G31/G32 diagnostics: which layout variant does the
// runtime's ARSC config law pick for EXT-01, and which attrs does the AXML
// parser expose? Read-only; no runtime behavior change.
#include "../src/resources/arsc_parser.h"
#include "../src/resources/axml_parser.h"
#include "../src/apk/apk_parser.h"
#include <cstdio>

using namespace miniandroid;

int main(int argc, char** argv) {
    const char* apk = "/home/z/corpus/external_hello/HelloWorldSelfAware-1.1.0-android.apk";
    (void)argc; (void)argv;
    apk::ApkParser ap;
    auto info = ap.parse(apk);
    if (info.all_entries.empty()) { std::printf("APK parse FAILED\n"); return 2; }
    auto arsc_data = ap.extract_entry_cached("resources.arsc");
    resources::ArscParser arsc;
    if (!arsc.parse(arsc_data)) { std::printf("ARSC parse FAILED: %s\n", arsc.last_error().c_str()); return 2; }
    auto r = arsc.resolve(0x7f030000);
    if (!r) { std::printf("layout 0x7f030000 NOT FOUND\n"); return 2; }
    std::printf("layout/activity_main configs=%zu best_has=%d\n",
                r->configs.size(), r->best() ? 1 : 0);
    for (const auto& c : r->configs) {
        std::printf("  cfg '%s' has_config=%d sdk=%u version=%u value=%s\n",
                    c.config_desc.c_str(), c.has_config ? 1 : 0,
                    c.config.sdkVersion, c.config.version,
                    c.value.string_value.c_str());
    }
    if (r->best())
        std::printf("BEST -> %s (desc '%s')\n",
                    r->best()->value.string_value.c_str(),
                    r->best()->config_desc.c_str());
    auto p = arsc.apk_path_for(0x7f030000, info.all_entries);
    std::printf("apk_path_for -> %s\n", p ? p->c_str() : "(none)");
    if (p) {
        auto xml = ap.extract_entry(apk, *p);
        resources::AxmlParser xp;
        if (!xp.parse(xml)) { std::printf("AXML parse FAILED\n"); return 2; }
        const auto& root = xp.root();
        std::printf("root element=%s attrs=%zu\n", root.name.c_str(),
                    root.attributes.size());
        for (const auto& a : root.attributes)
            std::printf("  attr ns='%s' name='%s' raw='%s' resid=0x%08x\n",
                        a.ns.c_str(), a.name.c_str(), a.raw_value.c_str(),
                        a.attr_resid);
    }
    return 0;
}
