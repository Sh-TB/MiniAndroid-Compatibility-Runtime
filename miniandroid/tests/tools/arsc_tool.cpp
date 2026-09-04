/*
 * UNIFIED_007 — standalone ARSC parser validation tool.
 * Usage: arsc_tool <apk-or-arsc> [dump_json_out]
 * Parses resources.arsc from APK/ZIP or raw ARSC, prints stats + samples.
 */
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <iostream>
#include <zlib.h>

#include "../../src/resources/arsc_parser.h"

static bool read_file(const std::string& path, std::vector<uint8_t>& out) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;
    f.seekg(0, std::ios::end);
    size_t n = f.tellg();
    f.seekg(0);
    out.resize(n);
    f.read((char*)out.data(), n);
    return true;
}

static bool zip_extract(const std::vector<uint8_t>& zip, const std::string& name,
                        std::vector<uint8_t>& out) {
    if (zip.size() < 4) return false;
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
            out.resize(1 << 23);
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
    if (argc < 2) { fprintf(stderr, "usage: %s <apk|arsc> [out.json]\n", argv[0]); return 2; }
    std::vector<uint8_t> data;
    if (!read_file(argv[1], data)) { fprintf(stderr, "read failed\n"); return 1; }
    std::vector<uint8_t> arsc;
    if (data.size() > 4 && data[0]=='P' && data[1]=='K') {
        if (!zip_extract(data, "resources.arsc", arsc)) {
            fprintf(stderr, "no resources.arsc in zip\n"); return 1;
        }
    } else {
        arsc = data;
    }
    miniandroid::resources::ArscParser p;
    if (!p.parse(arsc)) {
        fprintf(stderr, "PARSE FAILED: %s\n", p.last_error().c_str());
        return 1;
    }
    const auto& st = p.stats();
    printf("OK packages=%u global_strings=%u type_chunks=%u entry_configs=%u named_ids=%u\n",
           st.package_count, st.global_string_count, st.type_count, st.entry_count, st.named_ids);
    for (auto& kv : st.entries_by_type)
        printf("  type %-14s %u entries\n", kv.first.c_str(), kv.second);
    std::string js = p.to_json(300);
    printf("json: %.900s...\n", js.c_str());
    if (argc > 2) {
        std::ofstream out(argv[2]);
        out << js;
    }
    return 0;
}
