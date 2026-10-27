#!/usr/bin/env bash
# cont83_build_anchors.sh — build the F-NEW-387 first-party anchor set.
#
# Each anchor is a REAL ELF64 shared object carrying the ANDROID soname so
# an app lib's DT_NEEDED (libm.so/liblog.so/…) matches by SONAME when the
# runtime pre-loads it RTLD_GLOBAL (native_dep.cpp). The anchor's own
# dependency chain pulls the REAL host library, so the app's undefined
# symbols resolve against genuine implementations — never a stub:
#   libm.so       → -lm            (glibc libm: layout-free C math surface)
#   libdl.so      → -ldl           (glibc dl: dlopen/dlsym contracts)
#   libstdc++.so  → anchor against -lstdc++ (CONT-113 F-NEW-460: an empty
#                    anchor SATISFIED the Android DT_NEEDED by SONAME and
#                    thereby BLOCKED glibc's real libstdc++.so.6 — every
#                    Itanium-ABI symbol the NDK C++ libs need
#                    (__cxa_pure_virtual, operator new, ...) died with
#                    "undefined symbol". The anchor must carry the real
#                    host C++ ABI in its dependency chain, exactly like
#                    the libm/libc anchors carry -lm/-lc; layout-free
#                    Itanium-ABI symbols are SysV-stable, the same ABI
#                    caveat as the C anchors).
#   liblog.so     → first-party implementation of the core liblog surface
#                    (__android_log_print/write/vprint/buf_print) writing
#                    bounded [LOG] rows to stderr — a real compatibility
#                    implementation, not a fake success.
#   libc.so       → empty anchor against -lc (glibc). ABI caveat recorded:
#                    layout-free C symbols are SysV-stable; bionic struct
#                    layouts (pthread/FILE) remain the named risk.
set -euo pipefail
# Repo root derived from THIS script's location (fresh-container law: no
# container-specific absolute paths — the T17-era `cd /home/z/fresh-repo`
# broke every container that didn't mount that exact path).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OUT=miniandroid/build/anchor_libs
mkdir -p "$OUT" tmp/cont83_anchors

# ── liblog first-party implementation ───────────────────────────────────
cat > tmp/cont83_anchors/log_shim.c <<'EOF'
/* F-NEW-387 first-party liblog anchor: the core Android liblog surface,
   implemented faithfully onto bounded stderr rows. Priorities mirror
   <android/log.h> (ANDROID_LOG_* values are the same constants). */
#include <stdarg.h>
#include <stdio.h>
typedef int android_LogPriority;
__attribute__((visibility("default")))
int __android_log_print(int prio, const char* tag, const char* fmt, ...) {
    va_list ap; va_start(ap, fmt);
    fprintf(stderr, "[LOG:%d] %s: ", prio, tag ? tag : "-");
    vfprintf(stderr, fmt, ap);
    fputc('\n', stderr);
    va_end(ap);
    return 1;
}
__attribute__((visibility("default")))
int __android_log_write(int prio, const char* tag, const char* text) {
    return __android_log_print(prio, tag, "%s", text ? text : "");
}
__attribute__((visibility("default")))
int __android_log_vprint(int prio, const char* tag, const char* fmt, va_list ap) {
    fprintf(stderr, "[LOG:%d] %s: ", prio, tag ? tag : "-");
    vfprintf(stderr, fmt, ap);
    fputc('\n', stderr);
    return 1;
}
__attribute__((visibility("default")))
int __android_log_buf_print(int bufID, int prio, const char* tag,
                            const char* fmt, ...) {
    va_list ap; va_start(ap, fmt);
    int r = __android_log_vprint(prio, tag, fmt, ap);
    va_end(ap);
    (void)bufID;
    return r;
}
EOF

gcc -shared -fPIC -O2 -Wl,-soname,liblog.so \
    -o "$OUT/liblog.so" tmp/cont83_anchors/log_shim.c

# ── host-library anchors (soname + real dependency chain) ───────────────
echo 'int __ma_anchor;' > tmp/cont83_anchors/empty.c
gcc -shared -fPIC -O2 -Wl,-soname,libm.so -Wl,--no-as-needed -lm \
    -o "$OUT/libm.so" tmp/cont83_anchors/empty.c
gcc -shared -fPIC -O2 -Wl,-soname,libdl.so -Wl,--no-as-needed -ldl \
    -o "$OUT/libdl.so" tmp/cont83_anchors/empty.c
gcc -shared -fPIC -O2 -Wl,-soname,libstdc++.so -Wl,--no-as-needed -lstdc++ \
    -o "$OUT/libstdc++.so" tmp/cont83_anchors/empty.c

# ── libc anchor WITH the bionic-stdio shim family (T22, F-NEW-564) ──────
# ROOT LAW (measured, scripts/t22_stdio_probe.c + LD_DEBUG=bindings): a
# dlopen'd app lib resolves symbols through its LOCAL scope FIRST — and the
# pre-loaded anchor libc.so puts REAL glibc in that scope, so the app lib's
# stdio binds glibc while its __sF binds the exe's global-scope fake array
# (glibc has no __sF). glibc fflush on an 88-byte-stride fake FILE =
# the libtmessages SIGSEGV at fflush+0x97 (T19 attribution).
# THE ONE-POINT FIX: the anchor itself exports the bionic-stdio surface
# (__sF + redirect-if-fake shim family, same first-party source as the
# exe's bionic_compat.c) — the app lib's whole stdio family then binds ONE
# module (dep scope) and never mixes layouts. exe-side callers keep the
# exe's own shim (each world self-consistent; no FILE* crosses worlds).
cp miniandroid/src/jni/bionic_compat.c tmp/cont83_anchors/bionic_compat.c
gcc -shared -fPIC -O2 -Wl,-soname,libc.so -Wl,--no-as-needed -lc \
    -o "$OUT/libc.so" tmp/cont83_anchors/bionic_compat.c

# ── T18 anchor set, restored to the tracked build (fresh-container law) ─
# The T18-era built anchors stayed LOCAL (ZERO-APK spirit) and their build
# was never wired into this script — every fresh container re-lost them
# (the exact F-NEW-387 failure class: soname-carrying shells are REQUIRED
# DT_NEEDED match targets; without them libtmessages dlopen dies with
# "libjnigraphics.so: cannot open shared object file" before JNI_OnLoad).
# Design: empty shells with Android sonames — the app lib's undefined
# gl*/egl*/AndroidBitmap_*/ANativeWindow_*/ symbols resolve through
# the GLOBAL scope to the exe's -rdynamic first-party implementations
# (212-symbol surface, [JNIG-ANCHOR] law). libz passthrough links -lz.
# libOpenSLES: first-party SPEC surface (T22) — the SL_IID_* interface
# GUIDs + slCreateEngine with the honest SL_RESULT_FEATURE_UNSUPPORTED
# verdict (T18's "spec GUIDs + FEATURE_UNSUPPORTED" design, reconstructed
# from the tracked spec text — source scripts/cont83_sles_anchor.c).
gcc -shared -fPIC -O2 -Wl,-soname,libOpenSLES.so \
    -o "$OUT/libOpenSLES.so" scripts/cont83_sles_anchor.c
# libjnigraphics: first-party 3-func AndroidBitmap surface (T22) — reaches
# the exe's BitmapStore through the __ma_bitmap_query C-ABI helper
# (jobject=0x500000000|heap_id marshaling law).
gcc -shared -fPIC -O2 -Wl,-soname,libjnigraphics.so \
    -o "$OUT/libjnigraphics.so" scripts/cont83_jnig_anchor.c -ldl
# libEGL: honest first-party eglGetCurrentContext (T22) — EGL_NO_CONTEXT.
gcc -shared -fPIC -O2 -Wl,-soname,libEGL.so \
    -o "$OUT/libEGL.so" scripts/cont83_egl_anchor.c
gcc -shared -fPIC -O2 -Wl,-soname,libGLESv2.so \
    -o "$OUT/libGLESv2.so" tmp/cont83_anchors/empty.c
# libandroid: honest first-party surface (T22) — ANativeWindow identity
# tokens + no-buffer window ops + NULL-asset AAsset family.
gcc -shared -fPIC -O2 -Wl,-soname,libandroid.so \
    -o "$OUT/libandroid.so" scripts/cont83_android_anchor.c
gcc -shared -fPIC -O2 -Wl,-soname,libz.so -Wl,--no-as-needed -lz \
    -o "$OUT/libz.so" tmp/cont83_anchors/empty.c

for f in "$OUT"/*.so; do
    printf '%s soname=%s sha16=%s\n' "$f" \
      "$(readelf -d "$f" | grep SONAME | sed 's/.*\[\(.*\)\]/\1/')" \
      "$(sha256sum "$f" | cut -c1-16)"
done
