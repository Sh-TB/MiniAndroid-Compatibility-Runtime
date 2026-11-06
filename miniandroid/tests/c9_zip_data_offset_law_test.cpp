/*
 * C9-2 (CODER 9) — ZipEntry data-offset law, unit law test.
 *
 * Pins the AOSP AssetFileDescriptor contract (AssetManager.openFd →
 * Asset): startOffset must be the entry DATA offset inside the APK,
 * resolved from the LOCAL file header:
 *     data_offset = LFH_offset + 30 + LFH.file_name_length
 *                                 + LFH.extra_field_length     (APPNOTE §4.3.7)
 * read from the LFH ITSELF because LFH and CDE extra fields may legally
 * differ (APPNOTE §4.4.11). Hostile/truncated LFH → has_data_offset=false
 * (honest-miss law; consumers must not pretend).
 *
 * 42 laws across 7 families, all on crafted in-memory ZIP archives:
 *   F1 plain STORED · F2 LFH-extra != CDE-extra discriminator ·
 *   F3 multi-entry mixed · F4 data-descriptor (streaming bit-3) ·
 *   F5 prepended stub · F6 hostile archives · F7 integration identities.
 *
 * Build: g++ -std=c++17 -w -g -O1 -Isrc -o build/c9_zip_data_offset_law_test
 *   tests/c9_zip_data_offset_law_test.cpp build/apk/apk_parser.o
 *   build/apk/manifest_reader.o build/resources/string_pool.o
 *   build/resources/arsc_parser.o build/resources/res_id.o
 *   build/resources/res_config.o build/dex/mutf8.o -lz -lpthread
 */

#include <apk/apk_parser.h>
#include <zlib.h>

#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

using miniandroid::apk::ApkParser;
using miniandroid::apk::ZipEntry;

static int g_pass = 0, g_fail = 0;
#define LAW(cond, num, name)                                                    \
    do {                                                                        \
        if (cond) { ++g_pass; }                                                 \
        else { ++g_fail;                                                        \
            std::printf("  LAW %02d FAIL: %s\n", (num), (name)); }              \
    } while (0)

static constexpr uint32_t SIG_LFH = 0x04034b50u;
static constexpr uint32_t SIG_CDE = 0x02014b50u;
static constexpr uint32_t SIG_EOCD = 0x06054b50u;
static constexpr uint32_t SIG_DESCRIPTOR = 0x08074b50u;

static void put16(std::vector<uint8_t>& b, uint16_t v) {
    b.push_back(v & 0xFF); b.push_back((v >> 8) & 0xFF);
}
static void put32(std::vector<uint8_t>& b, uint32_t v) {
    b.push_back(v & 0xFF); b.push_back((v >> 8) & 0xFF);
    b.push_back((v >> 16) & 0xFF); b.push_back((v >> 24) & 0xFF);
}

struct CraftedEntry {
    std::string name;
    std::vector<uint8_t> payload;
    uint16_t method = 0;                    // 0 = STORED, 8 = DEFLATE
    std::vector<uint8_t> lfh_extra;         // extra field written in the LFH
    std::vector<uint8_t> cde_extra;         // extra field written in the CDE
    bool data_descriptor = false;           // streaming entry (general flag bit 3)
    bool corrupt_lfh_sig = false;           // hostile: LFH signature is not PK\x03\x04
    uint32_t cde_compressed_size_override = 0;  // hostile: lie about csize (0 = honest)
    bool hide_lfh = false;                  // hostile: offset points outside the file
};

// Raw-DEFLATE (ZIP method 8 uses raw deflate, windowBits -15).
static std::vector<uint8_t> raw_deflate(const std::vector<uint8_t>& in) {
    z_stream zs{};
    deflateInit2(&zs, Z_BEST_SPEED, Z_DEFLATED, -15, 8, Z_DEFAULT_STRATEGY);
    zs.next_in = const_cast<Bytef*>(in.data());
    zs.avail_in = (uInt)in.size();
    std::vector<uint8_t> out;
    uint8_t buf[4096];
    int ret = Z_OK;
    do {
        zs.next_out = buf; zs.avail_out = sizeof(buf);
        ret = deflate(&zs, Z_FINISH);
        out.insert(out.end(), buf, buf + (sizeof(buf) - zs.avail_out));
    } while (ret != Z_STREAM_END);
    deflateEnd(&zs);
    return out;
}

// Serializes a crafted archive; fills recorded LFH offsets for expectations.
static std::vector<uint8_t> craft_zip(const std::vector<CraftedEntry>& entries,
                                      size_t stub_bytes,
                                      std::vector<size_t>* lfh_offsets) {
    std::vector<uint8_t> z;
    const std::string stub(stub_bytes, 'S');
    z.insert(z.end(), stub.begin(), stub.end());

    struct CdeRec { std::vector<uint8_t> bytes; };
    std::vector<CdeRec> cdes;

    for (const auto& e : entries) {
        const size_t lfh_off = z.size();
        if (lfh_offsets) lfh_offsets->push_back(lfh_off);

        std::vector<uint8_t> stored = e.payload;
        std::vector<uint8_t> comp;
        const uint8_t* data_ptr = stored.data();
        uint32_t csize = (uint32_t)stored.size();
        uint32_t usize = (uint32_t)stored.size();
        if (e.method == 8) {
            comp = raw_deflate(stored);
            data_ptr = comp.data();
            csize = (uint32_t)comp.size();
        }
        if (e.cde_compressed_size_override) csize = e.cde_compressed_size_override;

        // Local file header
        put32(z, e.corrupt_lfh_sig ? 0xDEADBEEF : SIG_LFH);
        put16(z, 20);              // version needed
        put16(z, e.data_descriptor ? 0x0008 : 0);
        put16(z, e.method);
        put16(z, 0); put16(z, 0);  // time / date
        put32(z, e.data_descriptor ? 0 : crc32(0L, stored.data(), stored.size()));
        put32(z, e.data_descriptor ? 0 : csize);   // descriptor: sizes in LFH are 0
        put32(z, e.data_descriptor ? 0 : usize);
        put16(z, (uint16_t)e.name.size());
        put16(z, (uint16_t)e.lfh_extra.size());
        z.insert(z.end(), e.name.begin(), e.name.end());
        z.insert(z.end(), e.lfh_extra.begin(), e.lfh_extra.end());
        z.insert(z.end(), data_ptr, data_ptr + (e.cde_compressed_size_override
                                                ? (uint32_t)stored.size() : csize));
        if (e.data_descriptor) {   // descriptor AFTER the data (bit-3 law)
            put32(z, SIG_DESCRIPTOR);
            put32(z, crc32(0L, stored.data(), stored.size()));
            put32(z, (uint32_t)stored.size());
            put32(z, (uint32_t)stored.size());
        }

        // Central directory record (sizes/crc always authoritative here)
        CdeRec& rec = cdes.emplace_back();
        std::vector<uint8_t>& c = rec.bytes;
        put32(c, SIG_CDE);
        put16(c, 0x031E);          // version made by (unix)
        put16(c, 20);
        put16(c, e.data_descriptor ? 0x0008 : 0);
        put16(c, e.method);
        put16(c, 0); put16(c, 0);
        put32(c, crc32(0L, stored.data(), stored.size()));
        put32(c, csize);
        put32(c, usize);
        put16(c, (uint16_t)e.name.size());
        put16(c, (uint16_t)e.cde_extra.size());
        put16(c, 0);               // comment len
        put16(c, 0);               // disk number
        put16(c, 0);               // internal attrs
        put32(c, 0100644 << 16);   // external attrs
        const uint32_t recorded = e.hide_lfh ? (uint32_t)(z.size() + 1 << 20)
                                             : (uint32_t)lfh_off;
        put32(c, recorded);
        c.insert(c.end(), e.name.begin(), e.name.end());
        c.insert(c.end(), e.cde_extra.begin(), e.cde_extra.end());
    }

    const uint32_t cd_offset = (uint32_t)z.size();
    for (auto& c : cdes) z.insert(z.end(), c.bytes.begin(), c.bytes.end());
    const uint32_t cd_size = (uint32_t)z.size() - cd_offset;

    put32(z, SIG_EOCD);
    put16(z, 0); put16(z, 0);
    put16(z, (uint16_t)entries.size());
    put16(z, (uint16_t)entries.size());
    put32(z, cd_size);
    put32(z, cd_offset);
    put16(z, 0);
    return z;
}

static bool write_file(const std::string& path, const std::vector<uint8_t>& b) {
    std::ofstream f(path, std::ios::binary | std::ios::trunc);
    f.write(reinterpret_cast<const char*>(b.data()), (std::streamsize)b.size());
    return (bool)f;
}

static std::vector<uint8_t> read_slice(const std::string& path, size_t off, size_t len) {
    std::ifstream f(path, std::ios::binary);
    f.seekg((std::streamoff)off);
    std::vector<uint8_t> out(len);
    f.read(reinterpret_cast<char*>(out.data()), (std::streamsize)len);
    out.resize((size_t)f.gcount());
    return out;
}

static const ZipEntry* find(const std::vector<ZipEntry>& v, const std::string& n) {
    for (const auto& e : v) if (e.name == n) return &e;
    return nullptr;
}

int main() {
    const std::string dir = "/tmp/c9_zip_law";
    (void)system("mkdir -p /tmp/c9_zip_law");

    const std::vector<uint8_t> payload_a = {'C','9','-','2',' ','d','a','t','a',
                                            ' ','o','f','f','s','e','t',' ','l','a','w'};
    const std::vector<uint8_t> payload_big(2000, 'x');
    const std::vector<uint8_t> extra16 = {0x11,0x00, 8,0,1,2,3,4,5,6,7,8};  // 12B shown; pad to 16 below
    std::vector<uint8_t> lfh_extra16 = extra16;
    lfh_extra16.push_back(0x99); lfh_extra16.push_back(0x99);
    lfh_extra16.push_back(0x98); lfh_extra16.push_back(0x98);

    // ── F1: plain STORED entry (laws 1–5) ────────────────────────────────
    {
        std::vector<size_t> offs;
        auto z = craft_zip({{"assets/plain.txt", payload_a, 0, {}, {}, false, false, 0, false}},
                           0, &offs);
        const std::string p = dir + "/plain.zip";
        write_file(p, z);
        ApkParser parser;
        auto es = parser.list_entries(p);
        const ZipEntry* e = find(es, "assets/plain.txt");
        LAW(e && e->has_data_offset, 1, "plain: has_data_offset");
        LAW(e && e->data_offset == offs[0] + 30 + 16, 2,
            "plain: data_offset == lfh+30+namelen");  // "assets/plain.txt"=16
        LAW(e && e->offset == offs[0], 3, "plain: offset records LFH");
        auto ex = parser.extract_entry(p, "assets/plain.txt");
        LAW(ex == payload_a, 4, "plain: extraction == payload");
        LAW(read_slice(p, e ? (size_t)e->data_offset : 0, payload_a.size()) == payload_a,
            5, "plain: data window bytes == payload");
    }

    // ── F2: LFH extra != CDE extra — THE discriminator (laws 6–11) ───────
    {
        std::vector<size_t> offs;
        auto z = craft_zip({{"assets/extra.txt", payload_a, 0, lfh_extra16, {}, false, false, 0, false}},
                           0, &offs);
        const std::string p = dir + "/extra.zip";
        write_file(p, z);
        ApkParser parser;
        auto es = parser.list_entries(p);
        const ZipEntry* e = find(es, "assets/extra.txt");
        const uint64_t expect = offs[0] + 30 + 16 + 16;  // LFH extra (16), not CDE extra (0)
        const uint64_t cde_arith = offs[0] + 30 + 16;    // wrong: CDE-derived
        LAW(e && e->has_data_offset, 6, "extra-diff: has_data_offset");
        LAW(e && e->data_offset == expect, 7,
            "extra-diff: uses LFH extra field length");
        LAW(e && e->data_offset != cde_arith, 8,
            "extra-diff: NOT the CDE-derived arithmetic");
        auto ex = parser.extract_entry(p, "assets/extra.txt");
        LAW(ex == payload_a, 9, "extra-diff: extraction == payload");
        LAW(read_slice(p, e ? (size_t)e->data_offset : 0, payload_a.size()) == payload_a,
            10, "extra-diff: window bytes == payload");
        LAW(es.size() == 1, 11, "extra-diff: entry listed once");
    }

    // ── F3: multi-entry mixed methods (laws 12–17) ───────────────────────
    {
        std::vector<size_t> offs;
        auto z = craft_zip({
            {"assets/e1_stored.txt", payload_a, 0, {}, {}, false, false, 0, false},
            {"assets/e2_deflate.txt", payload_big, 8, {}, {}, false, false, 0, false},
            {"assets/e3_stored.bin", {'Q','W','E','R','T','Y'}, 0, {}, {}, false, false, 0, false},
        }, 0, &offs);
        const std::string p = dir + "/multi.zip";
        write_file(p, z);
        ApkParser parser;
        auto es = parser.list_entries(p);
        LAW(es.size() == 3, 12, "multi: three entries listed");
        const ZipEntry *e1 = find(es, "assets/e1_stored.txt"),
                       *e2 = find(es, "assets/e2_deflate.txt"),
                       *e3 = find(es, "assets/e3_stored.bin");
        LAW(e1 && e2 && e3 && e1->has_data_offset && e2->has_data_offset &&
            e3->has_data_offset, 13, "multi: all have data_offset");
        LAW(e1 && e1->data_offset == offs[0] + 30 + 20, 14, "multi: e1 data_offset");
        LAW(e2 && e2->data_offset == offs[1] + 30 + 21, 15, "multi: e2 (deflate) data_offset");
        LAW(e3 && e3->data_offset == offs[2] + 30 + 20, 16, "multi: e3 data_offset");
        auto ex2 = parser.extract_entry(p, "assets/e2_deflate.txt");
        LAW(ex2 == payload_big, 17, "multi: deflate extraction == original");
    }

    // ── F4: data-descriptor (streaming, bit 3) (laws 18–23) ──────────────
    {
        std::vector<size_t> offs;
        auto z = craft_zip({{"assets/stream.txt", payload_big, 8, {}, {}, true, false, 0, false}},
                           0, &offs);
        const std::string p = dir + "/stream.zip";
        write_file(p, z);
        ApkParser parser;
        auto es = parser.list_entries(p);
        const ZipEntry* e = find(es, "assets/stream.txt");
        LAW(e && e->has_data_offset, 18, "descriptor: has_data_offset");
        LAW(e && e->data_offset == offs[0] + 30 + 17, 19,
            "descriptor: data_offset ignores trailing descriptor");
        LAW(e && e->compression_method == 8, 20, "descriptor: method 8 parsed");
        auto ex = parser.extract_entry(p, "assets/stream.txt");
        LAW(ex == payload_big, 21, "descriptor: extraction == payload (sizes from CDE)");
        const std::vector<uint8_t> comp_stream = raw_deflate(payload_big);
        auto win = read_slice(p, e ? (size_t)e->data_offset : 0, comp_stream.size());
        LAW(win == comp_stream, 22,
            "descriptor: window == the COMPRESSED data bytes");
        const std::vector<uint8_t> desc_sig = {0x50,0x4b,0x07,0x08};
        LAW(read_slice(p, (e ? (size_t)e->data_offset : 0) + comp_stream.size(), 4)
                == desc_sig,
            23, "descriptor: signature sits AFTER the data window");
    }

    // ── F5: prepended stub (self-extracting style) (laws 24–28) ──────────
    {
        const size_t stub = 777;
        std::vector<size_t> offs;
        auto z = craft_zip({{"assets/stub.txt", payload_a, 0, {}, {}, false, false, 0, false}},
                           stub, &offs);
        const std::string p = dir + "/stub.zip";
        write_file(p, z);
        ApkParser parser;
        auto es = parser.list_entries(p);
        const ZipEntry* e = find(es, "assets/stub.txt");
        LAW(e && e->has_data_offset, 24, "stub: has_data_offset");
        LAW(e && e->data_offset == offs[0] + 30 + 15, 25,
            "stub: absolute offset includes the prepended stub");
        LAW(e && e->offset == offs[0], 26, "stub: LFH offset includes stub");
        auto ex = parser.extract_entry(p, "assets/stub.txt");
        LAW(ex == payload_a, 27, "stub: extraction == payload");
        LAW(read_slice(p, e ? (size_t)e->data_offset : 0, payload_a.size()) == payload_a,
            28, "stub: window bytes == payload");
    }

    // ── F6: hostile archives — honest miss (laws 29–35) ──────────────────
    {
        std::vector<size_t> offs;
        auto z = craft_zip({
            {"assets/bad_sig.txt", payload_a, 0, {}, {}, false, true, 0, false},
            {"assets/good.txt", payload_a, 0, {}, {}, false, false, 0, false},
        }, 0, &offs);
        const std::string p = dir + "/hostile_sig.zip";
        write_file(p, z);
        ApkParser parser;
        auto es = parser.list_entries(p);
        const ZipEntry* bad = find(es, "assets/bad_sig.txt");
        const ZipEntry* good = find(es, "assets/good.txt");
        LAW(bad && !bad->has_data_offset, 29, "hostile: corrupt LFH sig → honest miss");
        LAW(bad != nullptr, 30, "hostile: entry still listed");
        LAW(bad && bad->data_offset == 0, 31, "hostile: data_offset stays 0 on miss");
        LAW(good && good->has_data_offset, 32, "hostile: sibling entry unaffected");

        auto z2 = craft_zip({{"assets/lie.txt", payload_a, 0, {}, {}, false, false,
                              999999, false}}, 0, nullptr);
        const std::string p2 = dir + "/hostile_lie.zip";
        write_file(p2, z2);
        ApkParser parser2;
        auto es2 = parser2.list_entries(p2);
        const ZipEntry* lie = find(es2, "assets/lie.txt");
        LAW(lie && !lie->has_data_offset, 33,
            "hostile: compressed_size beyond EOF → honest miss");

        auto z3 = craft_zip({{"assets/hid.txt", payload_a, 0, {}, {}, false, false, 0, true}},
                            0, nullptr);
        const std::string p3 = dir + "/hostile_oob.zip";
        write_file(p3, z3);
        ApkParser parser3;
        auto es3 = parser3.list_entries(p3);
        const ZipEntry* hid = find(es3, "assets/hid.txt");
        LAW(hid && !hid->has_data_offset, 34,
            "hostile: LFH offset out of file → honest miss");
        auto ex = parser3.extract_entry(p3, "assets/hid.txt");
        LAW(ex.empty(), 35, "hostile: extraction refuses the unresolvable entry");

        std::vector<size_t> offs_zero;
        auto z4 = craft_zip({{"assets/zero.bin", {}, 0, {}, {}, false, false, 0, false}},
                            0, &offs_zero);
        const std::string p4 = dir + "/zero.zip";
        write_file(p4, z4);
        ApkParser parser4;
        auto es4 = parser4.list_entries(p4);
        const ZipEntry* zero = find(es4, "assets/zero.bin");
        LAW(zero && zero->has_data_offset &&
                zero->data_offset == offs_zero[0] + 30 + 15,
            36, "zero-length: data_offset resolves, empty window is legal");
    }

    // ── F7: integration identities (laws 37–42) ──────────────────────────
    {
        std::vector<size_t> offs;
        auto z = craft_zip({
            {"assets/p1.bin", payload_a, 0, {}, {}, false, false, 0, false},
            {"assets/p2.bin", payload_big, 8, {}, {}, false, false, 0, false},
            {"assets/p3.bin", {'M','!'}, 0, {}, {}, false, false, 0, false},
        }, 0, &offs);
        const std::string p = dir + "/integ.zip";
        write_file(p, z);
        ApkParser parser;
        auto es = parser.list_entries(p);

        bool all_have = es.size() == 3;
        for (auto& e : es) all_have = all_have && e.has_data_offset;
        LAW(all_have, 37, "integ: every normal entry resolves");

        bool window_matches = true;
        for (auto& e : es) {
            if (e.compression_method == 0 &&
                read_slice(p, (size_t)e.data_offset, e.uncompressed_size).size()
                    != e.uncompressed_size)
                window_matches = false;
        }
        LAW(window_matches, 38, "integ: STORED windows fully addressable");

        const ZipEntry* e2 = find(es, "assets/p2.bin");
        LAW(e2 && e2->data_offset + e2->compressed_size <= z.size(), 39,
            "integ: DEFLATE window within file bounds");

        bool monotonic = true;
        for (size_t i = 1; i < es.size(); ++i)
            if (es[i].data_offset < es[i-1].data_offset) monotonic = false;
        LAW(monotonic, 40, "integ: data_offset non-decreasing for sequential layout");

        // Law formula re-derived from the raw file bytes (independent LFH read).
        bool formula = true;
        for (auto& e : es) {
            std::ifstream f(p, std::ios::binary);
            f.seekg((std::streamoff)e.offset);
            miniandroid::apk::ZipLocalFileHeader lfh{};
            f.read(reinterpret_cast<char*>(&lfh), sizeof(lfh));
            const uint64_t expect = (uint64_t)e.offset + sizeof(lfh) +
                                    lfh.file_name_length + lfh.extra_field_length;
            if (expect != e.data_offset) formula = false;
        }
        LAW(formula, 41, "integ: data_offset == lfh+30+name+extra (independent re-read)");

        // Two read paths agree: extraction bytes == independent window bytes.
        const ZipEntry* e1 = find(es, "assets/p1.bin");
        auto ex = parser.extract_entry(p, "assets/p1.bin");
        auto win = read_slice(p, e1 ? (size_t)e1->data_offset : 0, ex.size());
        LAW(ex == win, 42, "integ: extraction path == independent fd-window path");
    }

    std::printf("c9_zip_data_offset_law_test: %d/%d PASS\n", g_pass, g_pass + g_fail);
    return g_fail == 0 ? 0 : 1;
}
