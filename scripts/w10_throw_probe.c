/* W10 diagnostic: interpose __cxa_throw to capture the throw site of the
 * length_error that lands in run_native_guarded's catch during queens'
 * RunBundleAndSnapshotFromLibrary. PROBE ONLY — never linked into the
 * runtime; used via LD_PRELOAD on a single diagnostic run.
 *
 * Build: gcc -shared -fPIC -o /tmp/w10_throw_probe.so w10_throw_probe.c
 * Run:   LD_PRELOAD=/tmp/w10_throw_probe.so <the run command>
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <execinfo.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

typedef void (*cxa_throw_fn)(void*, void*, void (*)(void*, void*));
typedef void* (*cxa_allocate_fn)(size_t);

static cxa_throw_fn real_throw = NULL;
static cxa_allocate_fn real_allocate = NULL;
static int depth = 0;

void __cxa_throw(void* ex, void* info, void (*dest)(void*, void*)) {
    if (!real_throw) real_throw = (cxa_throw_fn)dlsym(RTLD_NEXT, "__cxa_throw");
    if (++depth <= 6) {  // bounded: only the first few throws
        void* bt[32];
        int n = backtrace(bt, 32);
        fprintf(stderr, "[W10-CXA-THROW] throw #%d (exception=%p)\n", depth, ex);
        // resolve each frame against the CURRENT maps (lib base + offset)
        for (int i = 0; i < n && i < 32; ++i) {
            FILE* maps = fopen("/proc/self/maps", "r");
            char line[600];
            int done = 0;
            while (maps && fgets(line, sizeof line, maps)) {
                unsigned long lo, hi;
                char perms[8], path[400] = "";
                if (sscanf(line, "%lx-%lx %7s %*x %*x:%*x %*u %399s",
                           &lo, &hi, perms, path) >= 3) {
                    if ((unsigned long)bt[i] >= lo &&
                        (unsigned long)bt[i] < hi && path[0] == '/') {
                        fprintf(stderr,
                                "[W10-CXA-THROW]   [%d] %s +0x%lx\n", i,
                                path, (unsigned long)bt[i] - lo);
                        done = 1;
                        break;
                    }
                }
            }
            if (maps) fclose(maps);
            if (!done)
                fprintf(stderr, "[W10-CXA-THROW]   [%d] %p (anon)\n", i,
                        bt[i]);
        }
        fflush(stderr);
    }
    --depth;
    real_throw(ex, info, dest);
}

/* Also demangle the exception class name at throw time. */
__attribute__((constructor)) static void probe_init(void) {
    if (!real_allocate)
        real_allocate = (cxa_allocate_fn)dlsym(RTLD_NEXT, "__cxa_allocate_exception");
}
