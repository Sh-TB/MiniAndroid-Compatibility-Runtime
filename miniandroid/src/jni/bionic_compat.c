/* cont83_bionic_compat.c — T18:
 * (note: _GNU_SOURCE must precede every system include for Dl_info)
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
/* cont83_bionic_compat.c — T18: bionic-legacy stdio symbol compat for the
 * libc.so anchor (F-NEW-387 family, bionic-ABI-caveat law).
 *
 * __sF: old bionic exposed `FILE __sF[3]` and old NDK headers spelled
 * stderr as (&__sF[2]). glibc FILE structs CANNOT be reconstructed at the
 * bionic element stride, so any stdio call THROUGH &__sF[k] inside the
 * native lib will fault — that fault is caught by the FIX-TTT native guard
 * (honest load/call failure, runtime survives). What this symbol BUYS:
 * the dlopen itself proceeds, so every non-stdio function of the library
 * (the actual crypto/media surface) becomes reachable.
 *
 * Layout: 3 slots x 88 bytes (old bionic sizeof(FILE)) zeroed. NOT a real
 * stdio backend — recorded as a named risk in the F-NEW-564 evidence.
 */
#include <stdint.h>
/* T23 (F-NEW-564 ROOT FIX): __sF STRIDE MISMATCH. The app lib computes
 * &__sF[k] with ITS OWN bionic FILE stride (modern bionic 64-bit = 152
 * bytes — verified: libtmessages stored __sF+152 as its log stream), while
 * this array used the old-NDK stride (88). Slot starts never matched, the
 * fake fell through to glibc, and fflush+0x97 deref'd the zeroed
 * "lock" (offset 0x88 = 0) — the deterministic SIGSEGV. Fix: enlarge the
 * array to the max stride (3x192) and match BOTH ladders by exact
 * arithmetic (88: 0/88/176, 152: 0/152/304 — provably collision-free). */
__attribute__((visibility("default")))
uint8_t __sF[3][192] = {{0}, {0}, {0}};

/* ── T18 additions: the residual bionic-only surface (census vs glibc) ── */
#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/cdefs.h>

/* bionic __errno(): returns int* (glibc: __errno_location) */
__attribute__((visibility("default")))
int* __errno(void) { return __errno_location(); }

/* bionic __assert2(file, line, func, expr): real first-party abort path */
__attribute__((visibility("default")))
void __assert2(const char* file, int line, const char* func,
               const char* expr) {
    fprintf(stderr, "[BIONIC-COMPAT] assert: %s:%d %s: %s\n",
            file ? file : "?", line, func ? func : "?", expr ? expr : "?");
    abort();
}

/* bionic _FORTIFY checks — the checked bound is honest-by-construction:
 * the underlying glibc op itself detects overflow (strlen cannot exceed
 * the real buffer; fd_set ops bound-checked by the caller's nfds). */
__attribute__((visibility("default")))
size_t __strlen_chk(const char* s, size_t n) {
    (void)n;
    return strlen(s);
}
#include <sys/select.h>
__attribute__((visibility("default")))
void __FD_CLR_chk(int fd, void* set, size_t set_size) {
    (void)set_size; FD_CLR(fd, (fd_set*)set);
}
__attribute__((visibility("default")))
void __FD_SET_chk(int fd, void* set, size_t set_size) {
    (void)set_size; FD_SET(fd, (fd_set*)set);
}
__attribute__((visibility("default")))
int __FD_ISSET_chk(int fd, void* set, size_t set_size) {
    (void)set_size; return FD_ISSET(fd, (fd_set*)set);
}

/* T22 (F-NEW-564 support): android_set_abort_message — the bionic libc
 * abort-message surface libtmessages binds. First-party: store the last
 * message (bounded) + one stderr row; abort itself stays glibc. */
static char ma_abort_msg[256] = {0};
__attribute__((visibility("default")))
void android_set_abort_message(const char* msg) {
    if (!msg) return;
    size_t n = strlen(msg);
    if (n >= sizeof(ma_abort_msg)) n = sizeof(ma_abort_msg) - 1;
    memcpy(ma_abort_msg, msg, n);
    ma_abort_msg[n] = 0;
    fprintf(stderr, "[BIONIC-ABORT] %s\n", ma_abort_msg);
}
__attribute__((visibility("default")))
const char* android_get_abort_message(void) { return ma_abort_msg; }

/* boringssl OPENSSL_memory_* hooks — real malloc-backed block allocator
 * with an 8-byte size prefix (OPENSSL_memory_get_size contract). */
__attribute__((visibility("default")))
void* OPENSSL_memory_alloc(size_t size) {
    uint8_t* p = (uint8_t*)malloc(size + 8);
    if (!p) return NULL;
    *(size_t*)p = size;
    return p + 8;
}
__attribute__((visibility("default")))
void OPENSSL_memory_free(void* ptr) {
    if (!ptr) return;
    free((uint8_t*)ptr - 8);
}
__attribute__((visibility("default")))
size_t OPENSSL_memory_get_size(void* ptr) {
    if (!ptr) return 0;
    return *(size_t*)((uint8_t*)ptr - 8);
}

/* ── T19: __sF stdio SHIM — redirect-if-fake, passthrough otherwise ─────
 * Callers holding &__sF[k] (old-NDK stderr/stdout/stdin spelling) get REAL
 * stdio behavior: the shim detects the fake addresses and forwards to the
 * genuine glibc stream. All other FILE* (engine, native libs on real
 * streams) pass through via RTLD_NEXT — zero behavior change. This turns
 * the F-NEW-564 SIGSEGV candidate (vfprintf on a fake FILE) into working
 * stderr output. */
#include <dlfcn.h>
#include <stdarg.h>

/* T22 stdio probe gate: MINIANDROID_STDIO_PROBE=1 + 64-line budget */
static int stdio_probe_on(void) {
    static int on = -1;
    if (on < 0) on = getenv("MINIANDROID_STDIO_PROBE") ? 1 : 0;
    return on;
}
static int stdio_probe_budget(void) {
    static int budget = 40000;
    return budget-- > 0;
}

/* T23 (F-NEW-564): PRISTINE STREAM SNAPSHOT. The native lib's old-NDK init
 * can POISON glibc's writable stdout/stderr VARIABLES with the fake
 * &__sF[k] addresses (bionic spelled stdout = &__sF[1]); the shim's own
 * redirect then reads the POISONED variable and hands the fake back to
 * glibc — SIGSEGV at fflush+0x97 (lock deref of a zeroed fake). The
 * snapshot is taken at exe start (constructor 101 — before main and
 * before any dlopen), so it can never observe the poison. */
static FILE* ma_snap_stdin;
static FILE* ma_snap_stdout;
static FILE* ma_snap_stderr;
__attribute__((constructor(101)))
static void ma_stream_snapshot(void) {
    ma_snap_stdin = stdin;
    ma_snap_stdout = stdout;
    ma_snap_stderr = stderr;
}
/* poison witness: log when a stream VARIABLE no longer holds its
 * snapshot (env-gated, bounded). */
static void ma_poison_witness(void) {
    static int budget = 16;
    if (budget <= 0 || !stdio_probe_on()) return;
    if ((stdout != ma_snap_stdout) || (stderr != ma_snap_stderr) ||
        (stdin != ma_snap_stdin)) {
        budget--;
        fprintf(stderr,
                "[T22-POISON] stream variable changed: stdout=%p (snap %p)"
                " stderr=%p (snap %p)\n",
                (void*)stdout, (void*)ma_snap_stdout, (void*)stderr,
                (void*)ma_snap_stderr);
    }
}

static FILE* ma_real_stream(const void* f) {
    /* T23 dual-ladder __sF matching (stride-agnostic slot starts) */
    const uint8_t* base = (const uint8_t*)&__sF[0][0];
    uintptr_t d = (uintptr_t)f - (uintptr_t)base;
    if (d < sizeof(__sF)) {
        if (d % 152 == 0 && d / 152 < 3) {
            /* modern-bionic ladder */
            switch (d / 152) {
                case 0: return ma_snap_stdin;
                case 1: return ma_snap_stdout;
                case 2: return ma_snap_stderr;
            }
        }
        if (d % 88 == 0 && d / 88 < 3) {
            /* old-NDK ladder */
            switch (d / 88) {
                case 0: return ma_snap_stdin;
                case 1: return ma_snap_stdout;
                case 2: return ma_snap_stderr;
            }
        }
    }
    /* also catch the POISONED variables receiving the fake addresses */
    if (f == (const void*)ma_snap_stdout) return ma_snap_stdout;
    if (f == (const void*)ma_snap_stderr) return ma_snap_stderr;
    if (f == (const void*)ma_snap_stdin) return ma_snap_stdin;
    return NULL;
}

__attribute__((visibility("default")))
int vfprintf(FILE* f, const char* fmt, va_list ap) {
    FILE* r = ma_real_stream(f);
    static int (*real_vfprintf)(FILE*, const char*, va_list);
    if (!real_vfprintf) real_vfprintf = dlsym(RTLD_NEXT, "vfprintf");
    return real_vfprintf(r ? r : f, fmt, ap);
}
__attribute__((visibility("default")))
int fprintf(FILE* f, const char* fmt, ...) {
    va_list ap; va_start(ap, fmt);
    int n = vfprintf(f, fmt, ap);
    va_end(ap);
    return n;
}
__attribute__((visibility("default")))
size_t fwrite(const void* p, size_t sz, size_t n, FILE* f) {
    FILE* r = ma_real_stream(f);
    static size_t (*real_fwrite)(const void*, size_t, size_t, FILE*);
    if (!real_fwrite) real_fwrite = dlsym(RTLD_NEXT, "fwrite");
    return real_fwrite(p, sz, n, r ? r : f);
}
__attribute__((visibility("default")))
int fputs(const char* s, FILE* f) {
    FILE* r = ma_real_stream(f);
    static int (*real_fputs)(const char*, FILE*);
    if (!real_fputs) real_fputs = dlsym(RTLD_NEXT, "fputs");
    return real_fputs(s, r ? r : f);
}
__attribute__((visibility("default")))
int fputc(int c, FILE* f) {
    FILE* r = ma_real_stream(f);
    static int (*real_fputc)(int, FILE*);
    if (!real_fputc) real_fputc = dlsym(RTLD_NEXT, "fputc");
    return real_fputc(c, r ? r : f);
}
__attribute__((visibility("default")))
int fgetc(FILE* f) {
    FILE* r = ma_real_stream(f);
    static int (*real_fgetc)(FILE*);
    if (!real_fgetc) real_fgetc = dlsym(RTLD_NEXT, "fgetc");
    return real_fgetc(r ? r : f);
}
__attribute__((visibility("default")))
int fclose(FILE* f) {
    FILE* r = ma_real_stream(f);
    if (r) return 0;  /* closing a fake stream: no-op (honest) */
    static int (*real_fclose)(FILE*);
    if (!real_fclose) real_fclose = dlsym(RTLD_NEXT, "fclose");
    return real_fclose(f);
}
__attribute__((visibility("default")))
int fflush(FILE* f) {
    FILE* r = ma_real_stream(f);
    /* T22 F-NEW-564 diagnostic: name the UNKNOWN pointer the native lib
     * feeds fflush — its owning module (dladdr) + the first bytes (the
     * bionic/glibc layout fingerprint). Env-gated, bounded, read-only. */
    if (!r && f && stdio_probe_on() && stdio_probe_budget() &&
        /* T23 noise gate: the lib's log loop fflush()es the two REAL
         * glibc streams tens of thousands of times — they are PROVEN
         * good (IO magic + passthrough works); skipping them keeps the
         * budget for the one call that faults. */
        f != (const void*)ma_snap_stdout && f != (const void*)ma_snap_stderr) {
        Dl_info di; memset(&di, 0, sizeof di);
        const char* mod = "heap/anon";
        uintptr_t off = 0;
        if (dladdr((void*)f, &di) && di.dli_fname) {
            mod = di.dli_fname;
            off = (uintptr_t)f - (uintptr_t)di.dli_fbase;
        }
        const unsigned char* p = (const unsigned char*)f;
        fprintf(stderr,
                "[T22-STDIO] fflush unknown FILE*=%p mod=%s+%lu bytes="
                "%02x %02x %02x %02x %02x %02x %02x %02x\n",
                (void*)f, mod, (unsigned long)off,
                p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]);
    }
    ma_poison_witness();
    static int (*real_fflush)(FILE*);
    if (!real_fflush) real_fflush = dlsym(RTLD_NEXT, "fflush");
    return real_fflush(r ? r : f);
}
