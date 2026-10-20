/* FIX-TTT bisect probe: dlopen vs JNI_OnLoad on the tictactoe libgdx.so */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <signal.h>
#include <setjmp.h>
#include <string.h>
#include <stdlib.h>

static sigjmp_buf jb;
static volatile sig_atomic_t armed = 0;
static void h(int s) { if (armed) { armed = 0; siglongjmp(jb, 1); } _exit(90); }

int main(int argc, char** argv) {
    const char* path = argv[1];
    struct sigaction sa, old;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = h;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_NODEFER;
    sigaction(SIGSEGV, &sa, &old);

    printf("step1: dlopen(%s) ...\n", path);
    fflush(stdout);
    if (sigsetjmp(jb, 1) == 0) {
        armed = 1;
        void* hd = dlopen(path, RTLD_NOW | RTLD_LOCAL);
        armed = 0;
        if (!hd) { printf("step1 FAIL: %s\n", dlerror()); return 1; }
        printf("step1 OK: handle=%p\n", hd);

        void* onload_sym = dlsym(hd, "JNI_OnLoad");
        printf("step2: JNI_OnLoad symbol = %p\n", onload_sym);
        fflush(stdout);
        if (onload_sym) {
            int (*onload)(void*, void*) = (int (*)(void*, void*))onload_sym;
            void* vm = NULL;  /* minimal bridge hands a table too — probe the raw NULL first */
            printf("step3: calling JNI_OnLoad(&vm_table=NULL, NULL) ...\n");
            fflush(stdout);
            if (sigsetjmp(jb, 1) == 0) {
                armed = 1;
                int v = onload(&vm, NULL);
                armed = 0;
                printf("step3 OK: JNI_OnLoad returned %d (0x%x)\n", v, v);
            } else {
                printf("step3 FAULT: SIGSEGV inside JNI_OnLoad (vm=NULL)\n");
            }
        }
        dlclose(hd);
        printf("done\n");
        return 0;
    }
    printf("step1 FAULT: SIGSEGV inside dlopen (ELF constructor)\n");
    return 2;
}
