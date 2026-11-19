// W15 (#627 D-03/H-03): glibc < 2.33 has no mallinfo2 (added in 2.33,
// https://sourceware.org/glibc/wiki/Release/2.33). The engine's
// MINIANDROID_ENGINE_MEM diagnostics call mallinfo2(); on old glibc the
// declaration is missing and the diagnostic TU fails to compile. This
// header aliases mallinfo2 onto the legacy mallinfo() with WIDENED
// fields (the old struct uses int, which overflows past 2 GB arenas) so
// the diagnostic compiles and reports honest (if 32-bit-sourced) numbers.
// Inactive on glibc >= 2.33. Diagnostic-only path — no runtime semantics.
#ifndef MINIANDROID_GLIBC_MALLINFO2_H
#define MINIANDROID_GLIBC_MALLINFO2_H

#include <malloc.h>

#if defined(__GLIBC__) && defined(__GLIBC_PREREQ)
#define MINIANDROID_GLIBC_VER __GLIBC_PREREQ(2, 33)
#else
#define MINIANDROID_GLIBC_VER 1  // non-glibc: assume the modern API
#endif

#if !MINIANDROID_GLIBC_VER
struct mallinfo2 {
    size_t arena;
    size_t ordblks;
    size_t smblks;
    size_t hblks;
    size_t hblkhd;
    size_t usmblks;
    size_t fsmblks;
    size_t uordblks;
    size_t fordblks;
    size_t keepcost;
};
static inline struct mallinfo2 mallinfo2(void) {
    struct mallinfo m = mallinfo();
    struct mallinfo2 r;
    r.arena = (size_t)m.arena;
    r.ordblks = (size_t)m.ordblks;
    r.smblks = (size_t)m.smblks;
    r.hblks = (size_t)m.hblks;
    r.hblkhd = (size_t)m.hblkhd;
    r.usmblks = 0;  // never populated by mallinfo (historical)
    r.fsmblks = (size_t)m.fsmblks;
    r.uordblks = (size_t)m.uordblks;
    r.fordblks = (size_t)m.fordblks;
    r.keepcost = (size_t)m.keepcost;
    return r;
}
#endif  // !MINIANDROID_GLIBC_VER

#endif  // MINIANDROID_GLIBC_MALLINFO2_H
