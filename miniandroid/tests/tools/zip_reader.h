/*
 * UNIFIED_007 — shared minimal ZIP reader for tools.
 */
#ifndef MINIANDROID_TESTS_ZIP_READER_H
#define MINIANDROID_TESTS_ZIP_READER_H

#include <cstdint>
#include <string>
#include <vector>
#include <fstream>
#include <zlib.h>

inline bool read_file_bytes(const std::string& path, std::vector<uint8_t>& out) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;
    f.seekg(0, std::ios::end);
    size_t n = f.tellg();
    f.seekg(0);
    out.resize(n);
    f.read((char*)out.data(), n);
    return true;
}

inline bool zip_extract_entry(const std::vector<uint8_t>& zip, const std::string& name,
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

#endif
