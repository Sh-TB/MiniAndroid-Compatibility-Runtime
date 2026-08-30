/*
 * CAMPAIGN 009 — §6 verification probe: configuration bucket matching.
 *
 * Usage: res_config_probe <apk-or-arsc> [resource_name ...]
 *   For each named string resource (or a sample of multi-bucket resources),
 *   prints every config bucket and which one best() selects under the
 *   current device config (MINIANDROID_LOCALE / MINIANDROID_DENSITY).
 *
 * Build: see scripts/p2_config_probe.sh
 */
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <iostream>
#include <zlib.h>

#include "../../src/resources/arsc_parser.h"

using namespace miniandroid::resources;

static bool read_file(const std::string& path, std::vector<uint8_t>& out) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;
    f.seekg(0, std::ios::end);
    size_t n = f.tellg();
    f.seekg(0);
    out.resize(n);
    f.read((char*)out.data(), n);
    return (size_t)f.gcount() == n;
}

static bool zip_extract(const std::vector<uint8_t>& zip, const std::string& name,
                        std::vector<uint8_t>& out) {
    size_t i = 0;
    while (i + 30 <= zip.size()) {
        uint32_t sig = zip[i] | (zip[i+1]<<8) | (zip[i+2]<<16) | ((uint32_t)zip[i+3]<<24);
        if (sig != 0x04034b50) { i++; continue; }
        uint16_t method = zip[i+8] | (zip[i+9]<<8);
        uint32_t csize = zip[i+18] | (zip[i+19]<<8) | ((uint32_t)zip[i+20]<<16) | ((uint32_t)zip[i+21]<<24);
        uint16_t nlen  = zip[i+26] | (zip[i+27]<<8);
        uint16_t elen  = zip[i+28] | (zip[i+29]<<8);
        std::string fname((const char*)&zip[i+30], nlen);
        size_t data_off = i + 30 + nlen + elen;
        if (data_off + csize > zip.size()) break;
        if (fname == name) {
            if (method == 0) {
                out.assign(zip.begin() + data_off, zip.begin() + data_off + csize);
                return true;
            }
            std::vector<uint8_t> src(zip.begin() + data_off, zip.begin() + data_off + csize);
            z_stream zs{};
            inflateInit2(&zs, -15);
            out.resize(1 << 24);
            zs.next_in = src.data(); zs.avail_in = (uInt)src.size();
            zs.next_out = out.data(); zs.avail_out = (uInt)out.size();
            int rc = inflate(&zs, Z_FINISH);
            out.resize(out.size() - zs.avail_out);
            inflateEnd(&zs);
            return rc == Z_STREAM_END || rc == Z_OK;
        }
        i = data_off + csize;
    }
    return false;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: res_config_probe <apk-or-arsc> [resource_name ...]\n");
        return 1;
    }
    std::vector<uint8_t> blob;
    if (!read_file(argv[1], blob)) { fprintf(stderr, "read failed\n"); return 1; }
    std::vector<uint8_t> arsc;
    if (blob.size() > 4 && blob[0] == 'P' && blob[1] == 'K') {
        if (!zip_extract(blob, "resources.arsc", arsc)) { fprintf(stderr, "no resources.arsc\n"); return 1; }
    } else {
        arsc = std::move(blob);
    }
    ArscParser p;
    if (!p.parse(arsc)) { fprintf(stderr, "parse failed: %s\n", p.last_error().c_str()); return 1; }

    const ResTableConfig& dev = device_config();
    printf("device: locale=%s-%s density=%u sw=%u w=%ux%u dp=%ux%u sdk=%u\n",
           dev.language_str().c_str(), dev.country_str().c_str(), dev.density,
           dev.smallestScreenWidthDp, dev.screenWidth, dev.screenHeight,
           dev.screenWidthDp, dev.screenHeightDp, dev.sdkVersion);

    // names to probe (args) or auto-sample multi-bucket resources
    std::vector<std::pair<uint32_t, std::string>> probes;
    if (argc > 2) {
        for (int i = 2; i < argc; i++) {
            std::string name = argv[i];
            auto id = p.find_id("", "string", name);
            if (id) probes.push_back({*id, name});
            else {
                auto id2 = p.find_id("", "drawable", name);
                if (id2) probes.push_back({*id2, name + " (drawable)"});
                else printf("NOT-FOUND: %s\n", name.c_str());
            }
        }
    } else {
        // auto: sample string resources with >1 config bucket
        auto strings = p.list_type("", "string");
        int sampled = 0;
        for (auto& [id, name] : strings) {
            if (sampled >= 12) break;
            auto r = p.resolve(id);
            if (r && r->configs.size() > 1) { probes.push_back({id, name}); sampled++; }
        }
        // plus a few drawables with multiple buckets
        auto drawables = p.list_type("", "drawable");
        int dsampled = 0;
        for (auto& [id, name] : drawables) {
            if (dsampled >= 4) break;
            auto r = p.resolve(id);
            if (r && r->configs.size() > 1) { probes.push_back({id, name + " (drawable)"}); dsampled++; }
        }
    }

    for (auto& [id, name] : probes) {
        auto r = p.resolve(id);
        if (!r) continue;
        const ArscEntry* b = r->best();
        printf("\n0x%08x %s (%zu buckets)\n", id, name.c_str(), r->configs.size());
        for (auto& c : r->configs) {
            std::string val;
            if (c.value.is_string()) val = c.value.string_value.substr(0, 40);
            else if (c.value.is_reference()) val = "ref->0x" + [&]{ char buf[12]; snprintf(buf, sizeof buf, "%x", c.value.ref_id); return std::string(buf); }();
            else val = "type=0x" + [&]{ char buf[8]; snprintf(buf, sizeof buf, "%02x", (uint8_t)c.value.type); return std::string(buf); }();
            bool matches = c.has_config ? c.config.match(dev) : true;
            printf("   [%s%-14s] %s %s\n",
                   c.has_config ? c.config.to_string().c_str() : "default",
                   c.config_desc.c_str(),  // aapt-style desc (may be empty)
                   matches ? "MATCH " : "REJECT",
                   val.c_str());
            (void)val;
        }
        if (b) printf("   => SELECTED: [%s]\n", b->has_config ? b->config.to_string().c_str() : "default");
    }
    return 0;
}
