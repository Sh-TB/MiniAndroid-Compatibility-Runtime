/* t22_stdio_probe.c — F-NEW-564 single-symbol probe.
 *
 * The T19 attribution: telegram's libtmessages.49.so crashed at glibc
 * fflush+0x97. Theory: MIXED BINDING — an old-NDK stdio call site inside
 * the dlopen'd lib resolves __sF from the EXE's global scope (glibc has no
 * __sF) while fflush resolves DEP-FIRST through the anchor libc.so to
 * glibc -> glibc fflush parses the 88-byte-stride fake bionic FILE -> SIGSEGV.
 *
 * This probe reproduces the engine's EXACT pattern standalone:
 *   exe: -rdynamic + bionic_compat.o (owns fake __sF + shim family)
 *   dlopen(RTLD_LOCAL) a lib that calls fflush(&__sF[2])
 *
 * VERDICT printed: the lib's resolved fflush/__sF addresses + call result.
 *   BEFORE fix: SIGSEGV (glibc fflush on fake FILE)
 *   AFTER  fix (anchor libc.so exports __sF + shim): redirect works.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <dlfcn.h>
#include <stdint.h>
#include <string.h>

/* The probe lib's contract (built as t22_probe_lib.so):
 *   extern uint8_t __sF[3][88];  int fflush(FILE*);
 *   void t22_probe(void) { fflush((FILE*)&__sF[2]); }
 * The lib carries UNDEFINED __sF + fflush; its binding answers the question.
 */
typedef void (*probe_fn)(void);

static void dump_binding(const char* label, void* addr, void* exe_sym) {
    Dl_info info; memset(&info, 0, sizeof(info));
    const char* mod = "?";
    if (addr && dladdr(addr, &info) && info.dli_fname) mod = info.dli_fname;
    printf("[T22-PROBE] %-10s resolved=%p module=%s %s\n", label, addr, mod,
           (exe_sym && addr == exe_sym) ? "(== exe symbol)" : "");
}

int main(void) {
    /* exe-side references (the global-scope symbols the lib may bind) */
    extern uint8_t __sF[3][88] __attribute__((weak));
    printf("[T22-PROBE] exe &__sF[2]=%p\n", (void*)&__sF[2]);
    printf("[T22-PROBE] exe fflush(glibc-or-shim)=%p\n", (void*)&fflush);
    void* exe_sF = (void*)&__sF[2];

    void* h = dlopen("./t22_probe_lib.so", RTLD_LOCAL | RTLD_NOW);
    if (!h) { printf("[T22-PROBE] dlopen failed: %s\n", dlerror()); return 1; }
    printf("[T22-PROBE] dlopen OK (RTLD_LOCAL)\n");

    /* resolve the symbols AS THE LIB SEES THEM (its own scope) */
    void* lib_fflush = dlsym(h, "fflush");
    void* lib_sF = dlsym(h, "__sF");
    dump_binding("lib fflush", lib_fflush, (void*)&fflush);
    dump_binding("lib __sF", lib_sF, exe_sF);
    if (lib_sF) dump_binding("lib __sF[2]", (uint8_t*)lib_sF + 2 * 88, exe_sF);

    /* mixed-binding verdict BEFORE the call */
    int mixed = lib_fflush && lib_sF &&
                dladdr(lib_fflush, &(Dl_info){0}) &&
                strstr(((Dl_info){0}).dli_fname ? "" : "", ""); /* placeholder */
    printf("[T22-PROBE] mixed=%s (fflush-module != __sF-module)\n",
           lib_fflush && lib_sF ? "check above" : "n/a");

    probe_fn probe = (probe_fn)dlsym(h, "t22_probe");
    if (!probe) { printf("[T22-PROBE] no t22_probe symbol\n"); return 1; }
    printf("[T22-PROBE] calling probe (fflush(&__sF[2]))...\n");
    fflush(stdout);
    probe();
    printf("[T22-PROBE] SURVIVED — stdio binding consistent (no SIGSEGV)\n");
    return 0;
}
