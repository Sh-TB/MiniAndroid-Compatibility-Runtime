// s27_audit2_fuzz_test — the S27-AUDIT-2 wave: the friend-method applied
// BY the engine itself (2026-11-23).
//
// The external audit found its 36 findings through adversarial input
// review. This wave re-runs that lens systematically and EMPIRICALLY:
// 6000 mutated inputs (seed-fixed, reproducible) against the three raw-
// buffer parser surfaces, compiled under ASan + UBSan. The contract is
// the gp_dex003 no-crash law, generalized:
//   every mutated input must return gracefully — a bool result and/or an
//   error string — never a signal, never a hang, never an escapee C++
//   exception (bad_alloc / length_error escaping = a FINDING).
//
// Seeds are semi-valid skeletons for each container (AXML chunk tree,
// DEX header+string pool, ARSC table+string pool); mutations mix random
// bit flips, targeted header-field corruption, truncation and splicing.

#include "../src/dex/dex_parser.h"
#include "../src/resources/axml_parser.h"
#include "../src/resources/arsc_parser.h"

#include <cstdio>
#include <cstdint>
#include <cstring>
#include <random>
#include <string>
#include <vector>

using miniandroid::dex::DexParser;
namespace res = miniandroid::resources;

namespace {

std::mt19937 g_rng(0x527A27D2u);  // fixed seed — the run is reproducible
int g_caught = 0;

void put16(std::vector<uint8_t>& d, size_t off, uint16_t v) {
    d[off] = v & 0xFF; d[off + 1] = (v >> 8) & 0xFF;
}
void put32(std::vector<uint8_t>& d, size_t off, uint32_t v) {
    d[off] = v & 0xFF; d[off + 1] = (v >> 8) & 0xFF;
    d[off + 2] = (v >> 16) & 0xFF; d[off + 3] = (v >> 24) & 0xFF;
}

// A UTF-16 string pool chunk (header 0x1C) holding two 1-char strings.
// base: absolute offset where the chunk starts; returns bytes consumed.
size_t append_string_pool(std::vector<uint8_t>& d, size_t base,
                          uint32_t chunk_size) {
    put16(d, base + 0, 0x0001);        // RES_STRING_POOL_TYPE
    put16(d, base + 2, 0x001C);        // header size
    put32(d, base + 4, chunk_size);
    put32(d, base + 8, 2);             // stringCount
    put32(d, base + 12, 0);            // styleCount
    put32(d, base + 16, 0);            // flags (UTF-16)
    put32(d, base + 20, 0x24);         // stringsStart (rel to chunk base)
    put32(d, base + 24, 0);            // stylesStart
    put32(d, base + 28, 0);            // offset[0] -> stringsStart+0
    put32(d, base + 32, 5);            // offset[1]
    size_t s0 = base + 0x24;
    d[s0] = 1; d[s0 + 1] = 0;          // u16 len 1
    d[s0 + 2] = 'a'; d[s0 + 3] = 0; d[s0 + 4] = 0;
    size_t s1 = s0 + 5;
    d[s1] = 1; d[s1 + 1] = 0;
    d[s1 + 2] = 'b'; d[s1 + 3] = 0; d[s1 + 4] = 0;
    return 0x1C + 8 + 5 + 5;
}

std::vector<uint8_t> axml_seed() {
    std::vector<uint8_t> d(0x80, 0);
    put16(d, 0, 0x0003);               // RES_XML_TYPE
    put16(d, 2, 0x0008);               // header size
    put32(d, 4, 0x80);                 // chunk size
    append_string_pool(d, 8, 0x78);
    return d;
}

std::vector<uint8_t> dex_seed() {
    std::vector<uint8_t> d(0x78, 0);
    const char magic[8] = {'d', 'e', 'x', '\n', '0', '3', '5', '\0'};
    std::memcpy(d.data(), magic, 8);
    put32(d, 0x20, 0x78);              // file_size
    put32(d, 0x24, 0x70);              // header_size
    put32(d, 0x28, 0x12345678);        // endian_tag
    put32(d, 0x38, 1);                 // string_ids_size
    put32(d, 0x3C, 0x70);              // string_ids_off
    put32(d, 0x70, 0x74);              // string_data offset
    d[0x74] = 1; d[0x75] = 'a'; d[0x76] = 0;
    return d;
}

std::vector<uint8_t> arsc_seed() {
    std::vector<uint8_t> d(0x80, 0);
    put16(d, 0, 0x0002);               // RES_TABLE_TYPE
    put16(d, 2, 0x000C);               // header size
    put32(d, 4, 0x80);                 // chunk size
    put32(d, 8, 1);                    // packageCount
    append_string_pool(d, 12, 0x74);
    return d;
}

// Targeted header fields a hostile input loves to corrupt.
const size_t AXML_FIELDS[] = {2, 4, 8, 12, 16, 20, 24, 28, 32};
const size_t DEX_FIELDS[] = {0x20, 0x24, 0x28, 0x38, 0x3C, 0x40, 0x44,
                             0x54, 0x58, 0x64};
const size_t ARSC_FIELDS[] = {2, 4, 8, 12, 16, 20, 24, 28, 32, 36};

std::vector<uint8_t> mutate(const std::vector<uint8_t>& seed,
                            const size_t* fields, size_t nfields) {
    std::vector<uint8_t> d = seed;
    int n_mut = 1 + (int)(g_rng() % 3);
    for (int m = 0; m < n_mut; m++) {
        int kind = (int)(g_rng() % 4);
        if (kind == 0) {                                  // bit flip
            size_t i = g_rng() % d.size();
            d[i] ^= (uint8_t)(1u << (g_rng() % 8));
        } else if (kind == 1 && nfields) {                // field corrupt
            put32(d, fields[g_rng() % nfields], g_rng());
        } else if (kind == 2) {                           // byte blast
            size_t off = g_rng() % d.size();
            size_t len = 1 + g_rng() % 8;
            for (size_t i = 0; i < len && off + i < d.size(); i++)
                d[off + i] = (uint8_t)g_rng();
        } else {                                          // truncate / pad
            if (g_rng() % 2 && d.size() > 16) {
                d.resize(1 + g_rng() % d.size());
            } else {
                size_t add = 1 + g_rng() % 64;
                for (size_t i = 0; i < add; i++) d.push_back((uint8_t)g_rng());
            }
        }
    }
    return d;
}

// One parser arm: N iterations, every call under try/catch; any escapee
// exception is a FINDING and names the seed so the case is reproducible.
template <typename Fn>
void fuzz_arm(const char* name, int n, Fn&& call) {
    int accepted = 0, rejected = 0, caught = 0;
    std::vector<uint32_t> bad_seeds;
    for (int i = 0; i < n; i++) {
        uint32_t stamp = (uint32_t)i;
        try {
            bool ok = call(stamp);
            (ok ? accepted : rejected)++;
        } catch (const std::exception& e) {
            caught++;
            if (bad_seeds.size() < 5) bad_seeds.push_back(stamp);
            std::printf("  [FINDING] %s iter %d threw: %s\n", name, i,
                        e.what());
        } catch (...) {
            caught++;
            if (bad_seeds.size() < 5) bad_seeds.push_back(stamp);
            std::printf("  [FINDING] %s iter %d threw (non-std)\n", name, i);
        }
    }
    std::printf("%s: %d iters — accepted %d / rejected %d / ESCAPEE %d\n",
                name, n, accepted, rejected, caught);
    if (!bad_seeds.empty()) {
        std::printf("  repro seeds:");
        for (uint32_t s : bad_seeds) std::printf(" %u", s);
        std::printf("\n");
    }
    g_caught += caught;
}

} // namespace

int main() {
    const int N = 2000;
    std::printf("S27-AUDIT-2 fuzz: %d mutations x 3 parsers, seed 0x527A27D2\n",
                N);

    fuzz_arm("axml", N, [&](uint32_t) {
        res::AxmlParser p;
        bool ok = p.parse(mutate(axml_seed(), AXML_FIELDS,
                                 sizeof(AXML_FIELDS) / sizeof(size_t)));
        return ok;
    });
    fuzz_arm("dex ", N, [&](uint32_t) {
        DexParser p;
        p.set_verbose(false);
        auto r = p.parse_data(mutate(dex_seed(), DEX_FIELDS,
                                     sizeof(DEX_FIELDS) / sizeof(size_t)),
                              "s27-audit2-fuzz");
        return !p.get_last_error().empty() ? false : true;
    });
    fuzz_arm("arsc", N, [&](uint32_t) {
        res::ArscParser p;
        bool ok = p.parse(mutate(arsc_seed(), ARSC_FIELDS,
                                 sizeof(ARSC_FIELDS) / sizeof(size_t)));
        return ok;
    });

    std::printf(g_caught == 0 ? "ALL CLEAN (0 escapee exceptions)\n"
                              : "FINDINGS: %d escapee exception(s)\n",
                g_caught);
    return g_caught == 0 ? 0 : 1;
}
