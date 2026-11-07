/* W12 diagnostic: interpose operator new[]/new and __cxa_throw to catch the
 * huge allocation that becomes std::bad_alloc in queens' RunBundle.
 * PROBE ONLY — never linked into the runtime; LD_PRELOAD for one run. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <execinfo.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static void emit_bt(const char* tag, void* const* bt, int n) {
    fprintf(stderr, "[W12-NEW] %s frames=%d\n", tag, n);
    for (int i = 0; i < n && i < 40; ++i) {
        FILE* maps = fopen("/proc/self/maps", "r");
        char line[600]; int done = 0;
        while (maps && fgets(line, sizeof line, maps)) {
            unsigned long lo, hi; char perms[8], path[400] = "";
            if (sscanf(line, "%lx-%lx %7s %*x %*x:%*x %*u %399s",
                       &lo, &hi, perms, path) >= 3) {
                if ((unsigned long)bt[i] >= lo &&
                    (unsigned long)bt[i] < hi && path[0] == '/') {
                    fprintf(stderr, "[W12-NEW]   [%d] %s +0x%lx\n", i,
                            path, (unsigned long)bt[i] - lo);
                    done = 1; break;
                }
            }
        }
        if (maps) fclose(maps);
        if (!done) fprintf(stderr, "[W12-NEW]   [%d] anon\n", i);
    }
    fflush(stderr);
}

static void* (*real_new)(size_t) = NULL;
static void* (*real_arr_new)(size_t) = NULL;

static void resolve_one(const char* tag, void* pc) {
    FILE* maps = fopen("/proc/self/maps", "r");
    char line[600]; int done = 0;
    while (maps && fgets(line, sizeof line, maps)) {
        unsigned long lo, hi; char perms[8], path[400] = "";
        if (sscanf(line, "%lx-%lx %7s %*x %*x:%*x %*u %399s",
                   &lo, &hi, perms, path) >= 3) {
            if ((unsigned long)pc >= lo && (unsigned long)pc < hi) {
                fprintf(stderr, "[W12-NEW]   %s %s %s +0x%lx %s\n", tag,
                        perms, path, (unsigned long)pc - lo,
                        (perms[1] == 'x') ? "CODE?" : "DATA");
                done = 1; break;
            }
        }
    }
    if (maps) fclose(maps);
    if (!done) fprintf(stderr, "[W12-NEW]   %s unmapped %p\n", tag, pc);
}

static int g_new_depth = 0;

void* _Znwm(size_t sz) {
    if (!real_new) real_new = (void*(*)(size_t))dlsym(RTLD_NEXT, "_Znwm");
    // LOG BEFORE the allocation — a throwing huge allocation never returns.
    if (sz > (64u << 20) && g_new_depth == 0) {
        g_new_depth = 1;
        void* ra = __builtin_return_address(0);  // TRUE caller PC
        void** sp = (void**)__builtin_frame_address(0);
        fprintf(stderr, "[W12-NEW] _Znwm size=%zu (0x%zx) PRE ra=%p\n",
                sz, sz, ra);
        resolve_one("ra", ra);
        // stack context: 8 slots around the RA slot
        for (int k = 0; k < 10; ++k) {
            resolve_one("ctx", sp[k]);
        }
        void* bt[32];
        int n = backtrace(bt, 32);
        emit_bt("new-pre", bt, n);
        g_new_depth = 0;
    }
    return real_new(sz);
}

void* _Znam(size_t sz) {
    if (!real_arr_new) real_arr_new = (void*(*)(size_t))dlsym(RTLD_NEXT, "_Znam");
    if (sz > (64u << 20) && g_new_depth == 0) {
        g_new_depth = 1;
        void* bt[32];
        int n = backtrace(bt, 32);
        fprintf(stderr, "[W12-NEW] _Znam size=%zu (0x%zx) PRE\n", sz, sz);
        emit_bt("new[]-pre", bt, n);
        g_new_depth = 0;
    }
    return real_arr_new(sz);
}

typedef void (*cxa_throw_fn)(void*, void*, void (*)(void*, void*));
void __cxa_throw(void* ex, void* tinfo, void (*dest)(void*, void*)) {
    static cxa_throw_fn real_throw = NULL;
    if (!real_throw) real_throw = (cxa_throw_fn)dlsym(RTLD_NEXT, "__cxa_throw");
    if (tinfo) {
        const char* mangled = ((const char**)tinfo)[1]; /* type_info::name */
        if (mangled) fprintf(stderr, "[W12-THROW] type=%s\n", mangled);
    }
    void* bt[48];
    int n = backtrace(bt, 48);
    emit_bt("throw", bt, n);
    real_throw(ex, tinfo, dest);
}
