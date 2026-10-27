/* T22 (F-NEW-564 support): libEGL anchor — honest first-party surface.
 * Software runtime: GL contexts are emulated (PortableGL) with no real
 * EGL state machine; eglGetCurrentContext honestly reports EGL_NO_CONTEXT
 * when nothing is current (the spec value apps must handle). */
#include <stdint.h>
#include <stddef.h>
__attribute__((visibility("default")))
void* eglGetCurrentContext(void) { return NULL; } /* EGL_NO_CONTEXT */
