/*
 * UNIFIED_007 — AXML parser validation tool.
 * Usage: axml_tool <apk> <entry-in-apk> [out.json]
 * Example: axml_tool gmdice.apk res/layout/act_gmdice.xml
 */
#include <cstdio>
#include <string>
#include <vector>
#include <fstream>
#include <zlib.h>

#include "../../src/resources/axml_parser.h"
#include "zip_reader.h"

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s <apk> <entry> [out.json]\n", argv[0]); return 2; }
    std::vector<uint8_t> zip;
    if (!read_file_bytes(argv[1], zip)) { fprintf(stderr, "read failed\n"); return 1; }
    std::vector<uint8_t> xml;
    if (!zip_extract_entry(zip, argv[2], xml)) { fprintf(stderr, "extract failed: %s\n", argv[2]); return 1; }
    miniandroid::resources::AxmlParser p;
    if (!p.parse(xml)) {
        fprintf(stderr, "PARSE FAILED: %s\n", p.last_error().c_str());
        return 1;
    }
    printf("OK root=%s ns=%s\n", p.root().name.c_str(), p.android_ns().c_str());
    std::string js = p.to_json();
    printf("json: %.1200s...\n", js.c_str());
    if (argc > 3) { std::ofstream out(argv[3]); out << js; }
    return 0;
}
