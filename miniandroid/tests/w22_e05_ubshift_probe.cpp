// AUD-47 (#627 E-05): standalone const/high16 shift-law probe — FIXED form.
// NOT a battery member (see the Makefile rule comment). Under
// `make UBSAN=1` (-fsanitize=undefined -fno-sanitize-recover=all) the
// unsigned-width shift is C++17-DEFINED, so the process must exit 0 with
// 7/7 bit-exact rows — the machine verification of the hub's "fixed form →
// exit 0, 7/7 bit-exact" evidence (issue #627, comment 6991611630).
// Vector set: the 3 vectors the hub named (0x8000/0xABCD/0xFFFF) + the 4
// boundary neighbours (0x0000/0x0001/0x7FFF/0x8001). The hub's exact
// 7-vector set was never published; this is the audit's reconstruction,
// and the same 7 vectors are engine-tested in the w15 law test rows.
#include <cstdint>
#include <cstdio>

static int failures = 0;

static void expect(const char* name, uint16_t raw, uint32_t want) {
    // THE fixed form (W22-A: dalvik_interpreter.cpp CONST_HIGH16 +
    // dalvik_engine.cpp monolith counterpart): shift in unsigned width.
    uint32_t got = static_cast<uint32_t>(static_cast<uint16_t>(raw)) << 16;
    const bool ok = got == want;
    std::printf("[%-4s] %s: const/high16 %04hX -> %08X (want %08X)\n",
                ok ? "PASS" : "FAIL", name, raw, got, want);
    if (!ok) ++failures;
}

int main() {
    expect("const_high16_0000", 0x0000, 0x00000000u);
    expect("const_high16_0001", 0x0001, 0x00010000u);
    expect("const_high16_7fff", 0x7FFF, 0x7FFF0000u);
    expect("const_high16_8000", 0x8000, 0x80000000u);
    expect("const_high16_8001", 0x8001, 0x80010000u);
    expect("const_high16_abcd", 0xABCD, 0xABCD0000u);
    expect("const_high16_ffff", 0xFFFF, 0xFFFF0000u);
    std::printf("E-05 FIXED-FORM PROBE: %d/7 bit-exact, failures=%d\n",
                7 - failures, failures);
    return failures == 0 ? 0 : 1;
}
