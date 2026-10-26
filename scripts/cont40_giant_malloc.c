/* CONT-40 — the giant-malloc interposer.
 * LD_PRELOAD before the engine; logs every malloc/calloc/realloc >=
 * GIANT_MIN (default 100MB) with a short backtrace. Falsifies or confirms
 * WHERE the 2939MB / 1489MB / 1024MB telegram mappings come from.
 * Build: gcc -shared -fPIC -o libgiant.so giant_malloc.c -ldl
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <execinfo.h>
#include <unistd.h>

static void (*real_free)(void*) = NULL;
static void* (*real_malloc)(size_t) = NULL;
static void* (*real_calloc)(size_t, size_t) = NULL;
static void* (*real_realloc)(void*, size_t) = NULL;
static long giant_min = 100; /* MB */
static int in_hook = 0;

static void init_real(void) {
    real_malloc = dlsym(RTLD_NEXT, "malloc");
    real_calloc = dlsym(RTLD_NEXT, "calloc");
    real_realloc = dlsym(RTLD_NEXT, "realloc");
    real_free = dlsym(RTLD_NEXT, "free");
    const char* e = getenv("GIANT_MIN_MB");
    if (e) giant_min = atol(e);
}

static void log_giant(const char* kind, size_t size) {
    if (in_hook) return;
    in_hook = 1;
    void* bt[12];
    int n = backtrace(bt, 12);
    fprintf(stderr, "[GIANT-MALLOC] %s(%zu) = %.1f MB backtrace:\n",
            kind, size, (double)size / (1024.0 * 1024.0));
    char** syms = backtrace_symbols(bt, n);
    for (int i = 0; i < n && i < 10; ++i)
        fprintf(stderr, "[GIANT-MALLOC]   #%d %s\n", i, syms[i]);
    free(syms);
    in_hook = 0;
}

void* malloc(size_t size) {
    if (!real_malloc) init_real();
    if (size >= (size_t)giant_min << 20) log_giant("malloc", size);
    return real_malloc(size);
}

void* calloc(size_t n, size_t sz) {
    if (!real_calloc) {
        /* dlsym may calloc during init — serve from a static arena */
        static char buf[8192];
        static size_t used = 0;
        size_t need = n * sz;
        if (need + used < sizeof(buf)) {
            void* p = buf + used;
            used += need;
            memset(p, 0, need);
            return p;
        }
        init_real();
    }
    if (n * sz >= (size_t)giant_min << 20) log_giant("calloc", n * sz);
    return real_calloc(n, sz);
}

void* realloc(void* p, size_t size) {
    if (!real_realloc) init_real();
    if (size >= (size_t)giant_min << 20) log_giant("realloc", size);
    return real_realloc(p, size);
}

void free(void* p) {
    if (!real_free) {
        /* nothing freed before init */
        return;
    }
    real_free(p);
}
