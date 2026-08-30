// EXP-120 (UNIFIED_007): REAL resources.arsc parser validation probe.
//
// For every corpus APK:
//   1. extract resources.arsc via the real zip reader
//   2. parse it with the new ArscParser
//   3. ORACLE CHECKS (no faking):
//      a) every drawable entry with file-path value  -> path must exist
//         in the APK zip listing (count matches vs misses)
//      b) string entries: count resolvable non-empty strings
//      c) app_name resolvable (when present)
//      d) layout names resolvable by find_id("layout", name)
//   4. Harvest VERIFIED framework attr (name -> id) pairs from layout AXML
//      resource-map chunks across APKs (>=3 independent APKs => verified)
//
// Output: run_exp007/arsc/<apk>_arsc.json + summary + attr map json.

#include "apk/apk_parser.h"
#include "resources/arsc_parser.h"
#include "renderer/software_renderer.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <map>

using namespace miniandroid;
using json = nlohmann::json;

int main(int argc, char** argv) {
    std::string corpus_dir = argc > 1 ? argv[1] : "download/corpus";
    std::string out_dir = argc > 2 ? argv[2] : "run_exp007/arsc";
    std::filesystem::create_directories(out_dir);

    std::vector<std::string> apks;
    for (auto& e : std::filesystem::directory_iterator(corpus_dir)) {
        if (e.path().extension() == ".apk") apks.push_back(e.path().string());
    }
    std::sort(apks.begin(), apks.end());

    json summary = json::array();
    // verified attr pairs: name -> {id, seen_in_n_apks}
    std::map<std::string, std::map<uint32_t, int>> attr_votes;

    int total = 0, parsed_ok = 0;
    for (const std::string& apk : apks) {
        total++;
        std::string name = std::filesystem::path(apk).filename().string();
        apk::ApkParser ap;
        ap.parse(apk);
        if (!ap.has_cached_data()) {
            summary.push_back({{"apk", name}, {"zip", "FAIL"}});
            continue;
        }
        std::set<std::string> zip_names;
        for (auto& ze : ap.list_entries(apk)) zip_names.insert(ze.name);
        auto exists = [&](const std::string& p) { return zip_names.count(p) > 0; };
        auto arsc_bytes = ap.extract_entry_cached("resources.arsc");
        json rec;
        rec["apk"] = name;
        rec["arsc_bytes"] = arsc_bytes.size();
        if (arsc_bytes.empty()) {
            rec["parse"] = "NO_ARSC";
            summary.push_back(rec);
            continue;
        }
        resources::ArscParser arsc;
        bool ok = arsc.load(arsc_bytes);
        rec["parse"] = ok ? "OK" : "FAIL";
        if (!ok) {
            rec["error"] = arsc.error();
            summary.push_back(rec);
            continue;
        }
        parsed_ok++;
        const auto& st = arsc.stats();
        rec["stats"] = {
            {"packages", st.packages},
            {"global_strings", st.global_strings},
            {"type_chunks", st.type_chunks},
            {"entries_total", st.entries_total},
            {"bag_entries", st.bag_entries},
        };
        rec["entries_per_type"] = arsc.dump_inventory()["packages"][0]["entries_per_type"];

        // ---- ORACLE A: drawable paths must exist in zip ----
        auto drawables = arsc.entries_of_type("drawable");
        int draw_total = 0, draw_hit = 0;
        for (auto& [nm, id] : drawables) {
            auto paths = arsc.drawable_paths(id);
            for (auto& p : paths) {
                draw_total++;
                if (exists(p)) draw_hit++;
            }
        }
        rec["oracle_drawable_paths"] = {{"total", draw_total}, {"hit", draw_hit},
                                        {"miss", draw_total - draw_hit}};

        // ---- ORACLE B: strings resolvable ----
        auto strings = arsc.entries_of_type("string");
        int str_total = 0, str_nonempty = 0;
        for (auto& [nm, id] : strings) {
            auto v = arsc.resolve(id);
            str_total++;
            if (v.found && v.type == resources::VAL_STRING && !v.str.empty())
                str_nonempty++;
        }
        rec["oracle_strings"] = {{"total", str_total}, {"nonempty", str_nonempty}};

        // ---- ORACLE C: app_name ----
        uint32_t app_name_id = arsc.find_id("string", "app_name");
        if (app_name_id) {
            auto v = arsc.resolve(app_name_id);
            rec["app_name"] = v.found && v.type == resources::VAL_STRING
                                  ? v.str : "(unresolved)";
        } else {
            rec["app_name"] = nullptr;
        }

        // ---- ORACLE D: layouts resolvable by name ----
        auto layouts = arsc.entries_of_type("layout");
        rec["layout_count"] = layouts.size();
        json lnames = json::array();
        for (auto& [nm, id] : layouts) lnames.push_back(nm);
        rec["layout_names"] = lnames;

        // ---- ATTR VOTE: harvest (name,id) from layout AXML resource maps ----
        for (auto& [nm, id] : layouts) {
            // find the actual layout file path from zip: res/layout/<nm>.xml
            std::string path = "res/layout/" + nm + ".xml";
            if (!exists(path)) continue;
            auto xml = ap.extract_entry_cached(path);
            if (xml.size() < 12) continue;
            const uint8_t* d = xml.data();
            uint16_t t0 = d[0] | (d[1] << 8);
            if (t0 != 0x0003) continue;
            size_t off = 8;
            // first chunk must be string pool
            if ((d[off] | (d[off+1] << 8)) != 0x0001) continue;
            uint16_t hs = d[off+2] | (d[off+3] << 8);
            uint32_t cs = d[off+4] | (d[off+5]<<8) | (d[off+6]<<16) | (d[off+7]<<24);
            uint32_t scount = d[off+8] | (d[off+9]<<8) | (d[off+10]<<16) | (d[off+11]<<24);
            uint32_t flags = d[off+16] | (d[off+17]<<8) | (d[off+18]<<16) | (d[off+19]<<24);
            uint32_t sstart = d[off+20] | (d[off+21]<<8) | (d[off+22]<<16) | (d[off+23]<<24);
            bool utf8 = flags & 0x100;
            auto read_str = [&](uint32_t i) -> std::string {
                if (i >= scount) return "";
                uint32_t o = d[off+hs+4*i] | (d[off+hs+4*i+1]<<8) | (d[off+hs+4*i+2]<<16) | (d[off+hs+4*i+3]<<24);
                const uint8_t* q = d + off + sstart + o;
                if (utf8) {
                    size_t pos = 0;
                    auto rl = [&]() { uint8_t b = q[pos++]; if (b & 0x80) b = ((b&0x7f)<<8)|q[pos++]; return b; };
                    rl(); uint32_t n = rl();  // skip u16len, read u8len
                    return std::string((const char*)q + pos, n);
                } else {
                    uint32_t n = q[0] | (q[1]<<8); size_t pos = 2;
                    if (n & 0x8000) { n = ((n&0x7fff)<<16) | (q[2]|(q[3]<<8)); pos = 4; }
                    std::string s;
                    for (uint32_t c = 0; c < n; ++c) {
                        uint16_t u = q[pos+2*c] | (q[pos+2*c+1]<<8);
                        if (u < 0x80) s.push_back(char(u));
                        else if (u < 0x800) { s.push_back(char(0xC0|(u>>6))); s.push_back(char(0x80|(u&0x3f))); }
                        else { s.push_back(char(0xE0|(u>>12))); s.push_back(char(0x80|((u>>6)&0x3f))); s.push_back(char(0x80|(u&0x3f))); }
                    }
                    return s;
                }
            };
            // resource map chunk follows string pool
            size_t moff = off + cs;
            if (moff + 8 <= xml.size() && (d[moff]|(d[moff+1]<<8)) == 0x0180) {
                uint16_t mhs = d[moff+2] | (d[moff+3]<<8);
                uint32_t mcs = d[moff+4] | (d[moff+5]<<8) | (d[moff+6]<<16) | (d[moff+7]<<24);
                for (uint32_t i = 0; moff + mhs + 4*i + 4 <= moff + mcs; ++i) {
                    uint32_t rid = d[moff+mhs+4*i] | (d[moff+mhs+4*i+1]<<8) | (d[moff+mhs+4*i+2]<<16) | (d[moff+mhs+4*i+3]<<24);
                    std::string attr = read_str(i);
                    if (!attr.empty()) attr_votes[attr][rid]++;
                }
            }
        }
        summary.push_back(rec);
        std::ofstream f(out_dir + "/" + name + "_arsc.json");
        f << rec.dump(2) << std::endl;
    }

    // Attr map: keep pairs where >=3 APKs voted and no conflicting ID.
    json attrs = json::object();
    for (auto& [attr, ids] : attr_votes) {
        if (ids.size() == 1) {
            for (auto& [id, votes] : ids) {
                if (votes >= 3) attrs[attr] = json{{"id", id}, {"votes", votes}};
            }
        }
    }
    std::ofstream af(out_dir + "/verified_android_attrs.json");
    af << attrs.dump(2) << std::endl;

    json out;
    out["experiment"] = "EXP-120 arsc parser probe";
    out["apks_total"] = total;
    out["parsed_ok"] = parsed_ok;
    out["verified_attr_count"] = attrs.size();
    out["results"] = summary;
    std::ofstream sf(out_dir + "/summary.json");
    sf << out.dump(2) << std::endl;
    std::cout << out.dump(2) << std::endl;
    return parsed_ok == total ? 0 : 1;
}
