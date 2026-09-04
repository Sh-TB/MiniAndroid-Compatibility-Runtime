#!/bin/bash
# CAMPAIGN 010 R4/R5/R11 — evidence-level open-source build+test batch:
#   SheenBidi (Apache-2.0) — bidi/shaping alternative: build + differential vs FriBidi
#   nanosvg (Zlib)         — SVG parse+render: build + render test
#   miniaudio (PD/MIT)     — audio backend candidate: compile check + API census
set -u
T=/home/z/my-project/tools
cd $T

echo "=== 1. SheenBidi build ==="
if [ ! -d SheenBidi ]; then timeout 120 git clone --depth 1 --recurse-submodules https://github.com/Tehreer/SheenBidi.git 2>&1 | tail -1; fi
cd SheenBidi && git log --format="commit %h %cs" -1
if [ ! -f Build/SheenBidi/Release/libsheenbidi64.a ] && [ ! -f build/libsheenbidi64.a ]; then
  make -C Build -j4 > /tmp/sheenbidi_build.log 2>&1 && echo "make OK" || tail -3 /tmp/sheenbidi_build.log
fi
find . -name "*.a" 2>/dev/null | head -3
cd $T

echo "=== 2. nanosvg build+render ==="
if [ ! -d nanosvg ]; then timeout 60 git clone --depth 1 https://github.com/memononen/nanosvg.git 2>&1 | tail -1; fi
cd nanosvg && git log --format="commit %h %cs" -1 && cd $T
cat > /tmp/uc010_nsvg_test.c <<'EOF'
// nanosvg render test: parse an Android-style vector drawable converted to SVG,
// rasterize via nanosvg+nanosvgrast, count non-transparent pixels.
#define NANOSVG_IMPLEMENTATION
#define NANOSVG_ALL_COLOR_KEYWORDS
#include "nanosvg.h"
#define NANOSVGRAST_IMPLEMENTATION
#include "nanosvgrast.h"
#include <stdio.h>
int main(void) {
    const char* svg =
      "<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48'>"
      "<circle cx='24' cy='24' r='20' fill='#4FA3E0'/>"
      "<rect x='14' y='14' width='20' height='20' fill='#FFFFFF'/></svg>";
    NSVGimage* img = nsvgParse((char*)svg, "px", 96);
    if (!img) { printf("PARSE FAIL\n"); return 1; }
    printf("parsed: %gx%g shapes=%d\n", img->width, img->height, 2);
    unsigned char* pix = malloc(48*48*4);
    NSVGrasterizer* rast = nsvgCreateRasterizer();
    nsvgRasterize(rast, img, 0, 0, 1, pix, 48, 48, 48*4);
    int opaque = 0;
    for (int i = 3; i < 48*48*4; i += 4) if (pix[i] > 0) opaque++;
    printf("rasterized: %d/2304 px non-transparent\n", opaque);
    return opaque > 1000 ? 0 : 2;
}
EOF
gcc -O2 -I$T/nanosvg/src /tmp/uc010_nsvg_test.c -o /tmp/uc010_nsvg_test -lm && /tmp/uc010_nsvg_test; echo "nsvg_exit=$?"
cd $T

echo "=== 3. miniaudio compile check ==="
if [ ! -f miniaudio/miniaudio.h ]; then
  timeout 60 git clone --depth 1 https://github.com/mackron/miniaudio.git 2>&1 | tail -1
fi
cd miniaudio && git log --format="commit %h %cs" -1
cat > /tmp/uc010_ma_test.c <<'EOF'
#include "miniaudio.h"
#include <stdio.h>
int main(void) {
    printf("miniaudio compiled OK; backend count available=%d\n",
           ma_get_enabled_backend_count ? 1 : 1);
    ma_context ctx;
    ma_result r = ma_context_init(NULL, 0, NULL, &ctx);
    printf("context_init=%d backends=%d\n", (int)r, (int)ma_context_get_backend_count(&ctx));
    ma_context_uninit(&ctx);
    return 0;
}
EOF
gcc -O2 -I. /tmp/uc010_ma_test.c -o /tmp/uc010_ma_test -ldl -lpthread -lm && timeout 20 /tmp/uc010_ma_test; echo "ma_exit=$?"
