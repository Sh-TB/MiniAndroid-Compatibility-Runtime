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
gcc -shared -fPIC -O2 -Wl,-soname,libc.so -Wl,--no-as-needed -lc \
    -o "$OUT/libc.so" tmp/cont83_anchors/empty.c

for f in "$OUT"/*.so; do
    printf '%s soname=%s sha16=%s\n' "$f" \
      "$(readelf -d "$f" | grep SONAME | sed 's/.*\[\(.*\)\]/\1/')" \
      "$(sha256sum "$f" | cut -c1-16)"
done
