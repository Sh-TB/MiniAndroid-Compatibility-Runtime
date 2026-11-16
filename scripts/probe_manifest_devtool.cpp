// APP-LOAD probe (#606 verify): run ManifestReader verbose on an APK's
// AndroidManifest.xml and dump the resolution — which activities, which
// flags fired, what main_activity resolved to.
#include "apk/manifest_reader.h"
#include "apk/apk_parser.h"
#include <fstream>
#include <iostream>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 2) { std::cerr << "usage: probe <apk>\n"; return 2; }
    using namespace miniandroid::apk;
    ApkParser parser;
    std::vector<uint8_t> mf = parser.extract_entry(argv[1], "AndroidManifest.xml");
    std::cerr << "manifest bytes: " << mf.size() << "\n";
    ManifestReader reader;
    reader.set_verbose(true);
    auto info = reader.parse(mf);
    std::cout << "package=" << info.package_name << "\n";
    std::cout << "main_activity='" << info.main_activity << "'\n";
    std::cout << "main_activity_full='" << info.main_activity_full << "'\n";
    std::cout << "activities=" << info.activities.size() << "\n";
    for (auto& a : info.activities) {
        std::cout << "  act '" << a.name << "' main=" << a.is_main_activity
                  << " launcher=" << a.is_launcher << " actions=";
        for (auto& s : a.actions) std::cout << s << ",";
        std::cout << "\n";
    }
    return 0;
}
