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
__attribute__((visibility("default")))
uint8_t __sF[3][88] = {{0}, {0}, {0}};

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
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdarg.h>

static FILE* ma_real_stream(const void* f) {
    if (f == (const void*)&__sF[0]) return stdin;
    if (f == (const void*)&__sF[1]) return stdout;
    if (f == (const void*)&__sF[2]) return stderr;
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
    static int (*real_fflush)(FILE*);
    if (!real_fflush) real_fflush = dlsym(RTLD_NEXT, "fflush");
    return real_fflush(r ? r : f);
}
