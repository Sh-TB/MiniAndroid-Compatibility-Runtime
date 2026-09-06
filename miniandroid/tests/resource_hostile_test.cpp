// GOLDEN-03 §14 — hostile / malformed resources.arsc safety tests.
//
// Contract (WineDroid + DexFile-audit hardening philosophy):
//   • every malformed input fails with a NAMED, DETERMINISTIC error
//   • no crash, no OOM, no hang, no silent mis-resolution
//   • resolve_full/bag_value on hostile-but-parseable tables fail named
//
// Each case builds a real synthetic table (tests/synthetic_arsc.h) and then
// mutates specific bytes — so every attack targets a REAL layout field, not
// a made-up blob.
#include "synthetic_arsc.h"

#include <chrono>
#include <iostream>
#include <string>
#include <vector>

using namespace miniandroid::resources;

static int g_pass = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    if (ok) { g_pass++; std::cout << "  PASS: " << what << "\n"; }
    else    { g_fail++; std::cout << "  FAIL: " << what << "\n"; }
}

// Parse a blob under a wall-clock guard; returns parse result and whether it
// finished inside the budget (any hang = failure).
static bool parse_guarded(const std::vector<uint8_t>& blob, ArscParser& arsc,
                          bool& finished_in_time) {
    auto t0 = std::chrono::steady_clock::now();
    bool ok = arsc.parse(blob);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                  std::chrono::steady_clock::now() - t0).count();
    finished_in_time = ms < 5000;
    return ok;
}

static std::vector<uint8_t> base_table() {
    return synthetic_arsc::build(
        {"hello"},
        {{1, "string", 0, {{"hello_message", false, 0, 0x03, 0, 0, {}}}}});
}

// Walk the REAL chunk nesting (table → global pool → package → 2 pools →
// type chunks) and return the offset of the FIRST 0x0201 type chunk.
static size_t find_type_chunk(const std::vector<uint8_t>& t) {
    auto u16 = [&](size_t o) { return (uint16_t)(t[o] | (t[o+1] << 8)); };
    auto u32 = [&](size_t o) {
        uint32_t v; std::memcpy(&v, &t[o], 4); return v;
    };
    size_t off = 12;                                   // past table header
    if (u16(off) != 0x0001) return 0;                  // global string pool
    off += u32(off + 4);
    if (u16(off) != 0x0200) return 0;                  // package chunk
    off += u16(off + 2);                               // past package header
    for (int i = 0; i < 2 && u16(off) == 0x0001; i++)  // type + key pools
        off += u32(off + 4);
    while (off + 8 <= t.size()) {
        uint16_t ct = u16(off);
        uint32_t cs = u32(off + 4);
        if (cs < 8) break;
        if (ct == 0x0201) return off;
        off += cs;
    }
    return 0;
}


// Walk the REAL chunk nesting (table -> global pool -> package -> 2 pools ->
// type chunks) and return the offset of the FIRST 0x0201 type chunk.
int main() {
    std::cout << "── hostile resource table safety (GOLDEN-03 §14) ──\n";
    std::vector<uint8_t> base = base_table();

    // ── 1. truncation family ───────────────────────────────────────────────
    {
        std::vector<uint8_t> t7(base.begin(), base.begin() + 7);
        ArscParser a; bool in_time;
        bool ok = parse_guarded(t7, a, in_time);
        check(!ok && in_time, "7-byte truncation → parse false (named: "
              + a.last_error() + ") in time");
        std::vector<uint8_t> t30(base.begin(), base.begin() + 30);
        ArscParser a2; parse_guarded(t30, a2, in_time);
        check(in_time, "mid-header truncation terminates in time");
    }

    // ── 2. wrong magic ─────────────────────────────────────────────────────
    {
        std::vector<uint8_t> t = base;
        t[0] = 0xFF;
        ArscParser a; bool in_time;
        bool ok = parse_guarded(t, a, in_time);
        check(!ok && in_time && a.last_error() == "not RES_TABLE_TYPE",
              "corrupt table type → named 'not RES_TABLE_TYPE'");
    }

    // ── 3. declared size overruns the buffer ───────────────────────────────
    {
        std::vector<uint8_t> t = base;
        synthetic_arsc::put32(t, 4, 0xFFFFFFF0u);
        ArscParser a; bool in_time;
        bool ok = parse_guarded(t, a, in_time);
        check(!ok && in_time && a.last_error() == "size overruns data",
              "declared size > data → named 'size overruns data'");
    }

    // ── 4. hostile string-pool offsets (package header fields) ─────────────
    {
        std::vector<uint8_t> t = base;
        // package starts after 12-byte table header + global pool; the type
        // strings offset is at pkg+268. Mutate to a value far beyond data.
        // Find the package chunk first (0x0200).
        size_t pkg = 12 + *(uint32_t*)&base[16];   // global pool size at +16
        // robust scan for 0x0200
        pkg = 0;
        for (size_t o = 12; o + 8 <= base.size(); ) {
            uint16_t ct = base[o] | (base[o+1] << 8);
            uint32_t cs; std::memcpy(&cs, &base[o+4], 4);
            if (cs < 8) break;
            if (ct == 0x0200) { pkg = o; break; }
            o += cs;
        }
        check(pkg != 0, "package chunk located for mutation tests");
        if (pkg) {
            std::vector<uint8_t> t = base;
            synthetic_arsc::put32(t, pkg + 268, 0xFFFFFFF0u);   // typeStrings off
            ArscParser a; bool in_time;
            bool ok = parse_guarded(t, a, in_time);
            check(!ok && in_time && !a.last_error().empty(),
                  "typeStrings offset beyond data → named failure ('" +
                  a.last_error() + "')");
        }
    }

    // -- 5. hostile type-chunk entryCount (the offs[i] OOB read class) ------
    {
        std::vector<uint8_t> t = base;
        size_t tc = find_type_chunk(t);
        check(tc != 0, "type chunk located for mutation tests");
        if (tc) {
            synthetic_arsc::put32(t, tc + 12, 0x00FFFFFFu);   // entryCount
            ArscParser a; bool in_time;
            bool ok = parse_guarded(t, a, in_time);
            check(!ok && in_time &&
                  a.last_error() == "type: entry offsets overrun chunk",
                  "entryCount 0xFFFFFF -> named 'entry offsets overrun chunk' "
                  "(pre-hardening this was an out-of-bounds read)");
        }
    }

    // -- 6. entries_start out of range --------------------------------------
    {
        std::vector<uint8_t> t = base;
        size_t tc = find_type_chunk(t);
        if (tc) {
            synthetic_arsc::put32(t, tc + 16, 0xFFFFFFF0u);   // entriesStart
            ArscParser a; bool in_time;
            bool ok = parse_guarded(t, a, in_time);
            check(!ok && in_time &&
                  a.last_error() == "type: entries_start out of range",
                  "entriesStart beyond chunk -> named failure");
        }
    }

    // -- 7. hostile entry size (vp past buffer): parse survives, no OOB -----
    {
        std::vector<uint8_t> t = base;
        size_t tc = find_type_chunk(t);
        if (tc) {
            uint32_t es; std::memcpy(&es, &t[tc + 16], 4);
            size_t ep = tc + es;   // first (only) entry
            synthetic_arsc::put16(t, ep, 0xFFF0u);   // entry size field
        }
        ArscParser a; bool in_time;
        parse_guarded(t, a, in_time);
        check(in_time, "hostile entry size: no OOB, terminates in time");
        if (a.valid()) {
            ResolutionResult r1 = a.resolve_full(0x7f010000, device_config());
            ResolutionResult r2 = a.resolve_full(0x7f010000, device_config());
            check(r1.ok == r2.ok && r1.error == r2.error,
                  "wounded entry resolves deterministically");
        }
    }

    // ── 8. malformed Res_value inside a bag item ───────────────────────────
    {
        // type 3 "style" bag with a malformed item (Res_value size 3)
        std::vector<uint8_t> blob = synthetic_arsc::build(
            {"x"},
            {{3, "style", 0, {
                {"S", true, 0, 0, 0, -1,
                 {{0x01010054, 0x03, 0}}},   // REFERENCE → nothing (id 0)
            }}});
        ArscParser a; bool in_time;
        bool ok = parse_guarded(blob, a, in_time);
        check(ok && in_time, "bag with dangling REFERENCE parses (value kept raw)");
        if (a.valid()) {
            ResolutionResult r = a.resolve_full(0x7f030000, device_config());
            check(r.ok && r.chain.size() == 1,
                  "complex bag entry is TERMINAL in the chain (parent not "
                  "followed as a reference) — deterministic");
        }
    }

    // ── 9. bag parent cycle at parse level (§8 safety) ─────────────────────
    {
        std::vector<uint8_t> blob = synthetic_arsc::build(
            {"x"},
            {{3, "style", 0, {
                {"A", true, 0x7f030001, 0, 0, -1, {}},
                {"B", true, 0x7f030000, 0, 0, -1, {}},
            }}});
        ArscParser a; bool in_time;
        bool ok = parse_guarded(blob, a, in_time);
        check(ok && in_time, "parent-cycle table parses in time");
        if (a.valid()) {
            auto v = a.bag_value(0x7f030000, 0x01010054, device_config());
            check(!v.has_value(), "bag_value through parent cycle → safe nullopt");
        }
    }

    // -- 10. impossible config record (declared size 0xFFFF) ----------------
    {
        std::vector<uint8_t> t = base;
        size_t tc = find_type_chunk(t);
        if (tc) synthetic_arsc::put32(t, tc + 20, 0xFFFFu);   // cfg size field
        ArscParser a; bool in_time;
        parse_guarded(t, a, in_time);
        check(in_time, "impossible config size: bounded read, no crash");
    }

    // ── 11. determinism of named failures (same input → same error) ────────
    {
        std::vector<uint8_t> t = base;
        synthetic_arsc::put32(t, 4, 0xFFFFFFF0u);
        ArscParser a1, a2;
        bool t1, t2;
        parse_guarded(t, a1, t1);
        parse_guarded(t, a2, t2);
        check(a1.last_error() == a2.last_error() && t1 && t2,
              "identical hostile input → identical named error (twice)");
    }

    // ── 12. valid table still parses after the hardening (no false positive)
    {
        ArscParser a; bool in_time;
        bool ok = parse_guarded(base, a, in_time);
        check(ok && in_time && a.valid(),
              "valid table unaffected by §14 hardening (no false positives)");
    }

    std::cout << "RESULT: " << g_pass << " passed, " << g_fail << " failed\n";
    return g_fail == 0 ? 0 : 1;
}
