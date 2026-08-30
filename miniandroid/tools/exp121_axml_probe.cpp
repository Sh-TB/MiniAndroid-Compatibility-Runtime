// EXP-121 probe: parse real layout AXML from corpus APKs and dump trees.
#include "apk/apk_parser.h"
#include "resources/arsc_parser.h"
#include "resources/axml_parser.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>

using namespace miniandroid;
using json = nlohmann::json;

static json dump_node(const resources::AxmlNode& n) {
    json j;
    j["name"] = n.name;
    j["attrs"] = json::array();
    for (const auto& a : n.attrs) {
        json aj;
        aj["name"] = (a.ns.empty() ? "" : a.ns + ":") + a.name;
        aj["type"] = int(a.value_type);
        if (a.value_type == 0x03) aj["value"] = a.raw_value;
        else aj["data"] = a.value_data;
        if (a.attr_id) aj["attr_id"] = json{{"hex", "0x0101XXXX"}, {"int", a.attr_id}};
        j["attrs"].push_back(aj);
    }
    j["children"] = json::array();
    for (const auto& c : n.children) j["children"].push_back(dump_node(c));
    return j;
}

int main(int argc, char** argv) {
    std::string apk = argc > 1 ? argv[1] : "download/corpus/simplestopwatch.apk";
    std::string out_dir = argc > 2 ? argv[2] : "run_exp007/axml";
    std::filesystem::create_directories(out_dir);

    apk::ApkParser ap;
    ap.parse(apk);
    resources::ArscParser arsc;
    auto arsc_bytes = ap.extract_entry_cached("resources.arsc");
    if (arsc_bytes.empty() || !arsc.load(arsc_bytes)) {
        std::cerr << "ARSC load failed: " << arsc.error() << std::endl;
        return 1;
    }

    json out;
    out["apk"] = apk;
    out["layouts"] = json::object();
    int total = 0, ok_count = 0;
    for (auto& [nm, id] : arsc.entries_of_type("layout")) {
        total++;
        // find real path across configs
        std::string path;
        // layouts point at file strings per config; use drawable_paths helper
        auto paths = arsc.drawable_paths(id);
        if (!paths.empty()) path = paths.front();
        if (path.empty()) path = "res/layout/" + nm + ".xml";
        auto xml = ap.extract_entry_cached(path);
        if (xml.empty()) continue;
        resources::AxmlParser ax;
        if (!ax.parse(xml.data(), xml.size())) {
            out["layouts"][path] = {{"error", ax.error()}};
            continue;
        }
        ok_count++;
        out["layouts"][path] = dump_node(ax.root());
    }
    out["total_layouts"] = total;
    out["parsed_ok"] = ok_count;
    std::ofstream f(out_dir + "/layout_trees.json");
    f << out.dump(2) << std::endl;
    std::cout << "layouts parsed: " << ok_count << "/" << total << std::endl;
    return ok_count == total ? 0 : 1;
}
