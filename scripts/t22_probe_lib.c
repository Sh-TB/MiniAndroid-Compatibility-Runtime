/* t22_probe_lib.c — the DUT (device under test): a stripped-style native lib
 * with old-NDK stdio usage: fflush on the __sF spelling (bionic old layout).
 * Undefined symbols __sF + fflush — how they BIND is the T22 question. */
#include <stdio.h>
#include <stdint.h>

extern uint8_t __sF[3][88];

__attribute__((visibility("default")))
void t22_probe(void) {
    fflush((FILE*)&__sF[2]);   /* old-NDK stderr spelling — the crash shape */
}
