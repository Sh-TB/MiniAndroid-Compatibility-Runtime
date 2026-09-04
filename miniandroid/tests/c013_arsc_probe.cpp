// C013 §18 — ARSC resolution probe using the runtime's own parser.
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"

#include <iostream>
#include <vector>

using namespace miniandroid::resources;
using namespace miniandroid::apk;

int main(int argc, char** argv) {
    if (argc < 2) { std::cerr << "usage: arsc_probe_cxx <apk> [resid_hex]\n"; return 2; }
    const std::string apk = argv[1];

    ApkParser apk_parser;
    auto entries = apk_parser.list_entries(apk);
    std::vector<std::string> names;
    for (auto& e : entries) names.push_back(e.name);
    std::cerr << "[probe] apk entries: " << names.size() << "\n";

    // pull resources.arsc bytes from the APK
    auto arsc_bytes = apk_parser.extract_entry(apk, "resources.arsc");
    if (arsc_bytes.empty()) { std::cerr << "[probe] no resources.arsc\n"; return 1; }
    ArscParser arsc;
    if (!arsc.parse(arsc_bytes)) {
        std::cerr << "[probe] parse failed: " << arsc.last_error() << "\n"; return 1;
    }
    std::cerr << "[probe] arsc valid\n";

    if (argc >= 3) {
        uint32_t resid = (uint32_t)strtoul(argv[2], nullptr, 16);
        auto r = arsc.resolve(resid);
        if (r) std::cout << "resolve(" << std::hex << resid << ") -> type=" << r->type_name
                         << " name=" << r->name << " configs=" << r->configs.size() << "\n";
        else    std::cout << "resolve(" << std::hex << resid << ") -> NONE\n";
        auto p = arsc.apk_path_for(resid, names);
        std::cout << "apk_path_for -> " << (p ? *p : "NONE") << "\n";
        if (r) {
            for (auto& cfg : r->configs) {
                std::cout << "  config '" << cfg.config_desc << "' value type=" << (int)cfg.value.type
                          << " str=" << (cfg.value.string_value.empty() ? "<none>" : cfg.value.string_value)
                          << " data=0x" << std::hex << cfg.value.data << std::dec << "\n";
            }
        }
    }
    // list all layouts and try path-matching each
    auto layouts = arsc.list_type("", "layout");
    std::cout << "layout entries: " << layouts.size() << "\n";
    int matched = 0;
    for (auto& [rid, nm] : layouts) {
        auto p = arsc.apk_path_for(rid, names);
        if (p) matched++;
        if (layouts.size() <= 40)
            std::cout << "  " << std::hex << rid << " " << nm << " -> "
                      << (p ? *p : "NO FILE") << "\n";
    }
    std::cout << "layouts with file: " << matched << "/" << layouts.size() << "\n";
    return 0;
}
