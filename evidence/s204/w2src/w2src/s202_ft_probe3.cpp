// s202_ft_probe3.cpp — differential probe for the rebuilt host-native
// wrapper (tools/native_host/libgdx-freetype64.so). Wave-1 protocol:
// load the WRAPPER (dlopen, NOT link), drive it through the JNI-surface
// calls with a minimal fake JNIEnv whose table has the engine's slot
// numbering (229 NewDirectByteBuffer, 230 GetDirectBufferAddress,
// 231 GetDirectBufferCapacity), render 'A' at 120 px and print
// rows/width/pitch — REAL RENDER gate (wave-1 reference: rows=86
// width=78 pitch=78 on host freetype 2.13.3 + DejaVuSans).
#include <dlfcn.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

typedef long jlong;
typedef int jint;

static void* g_bb_addr = nullptr;
static int64_t g_bb_cap = 0;
static void* fake_new_direct_bb(void*, void* addr, int64_t cap) {
    g_bb_addr = addr;
    g_bb_cap = cap;
    return (void*)0x1234;  // opaque boxed buffer token
}
static void* fake_direct_addr(void*, void*) { return g_bb_addr; }
static int64_t fake_direct_cap(void*, void*) { return g_bb_cap; }

static void* g_table[256];
static void* g_env_obj = g_table;  // JNIEnv* -> *(void**)env = table

int main(int argc, char** argv) {
    const char* so = argc > 1 ? argv[1]
                              : "tools/native_host/libgdx-freetype64.so";
    const char* font = argc > 2 ? argv[2]
                                : "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";
    void* h = dlopen(so, RTLD_NOW);
    if (!h) {
        fprintf(stderr, "dlopen %s FAILED: %s\n", so, dlerror());
        return 1;
    }
    g_table[229] = (void*)&fake_new_direct_bb;
    g_table[230] = (void*)&fake_direct_addr;
    g_table[231] = (void*)&fake_direct_cap;
#define SYM(name) dlsym(h, name)
    auto init_fn = (jlong (*)(void*, void*))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_initFreeTypeJni");
    auto nmf = (jlong (*)(void*, void*, jlong, void*, jint, jint))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Library_"
        "newMemoryFace");
    auto sps = (jint (*)(void*, void*, jlong, jint, jint))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Face_"
        "setPixelSizes");
    auto lc = (jint (*)(void*, void*, jlong, jint, jint))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Face_"
        "loadChar");
    auto gg = (jlong (*)(void*, void*, jlong))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Face_"
        "getGlyph");
    auto gg2 = (jlong (*)(void*, void*, jlong))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024GlyphSlot_"
        "getGlyph");
    auto tb = (jlong (*)(void*, void*, jlong, jint))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Glyph_"
        "toBitmap");
    auto gb = (jlong (*)(void*, void*, jlong))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Glyph_"
        "getBitmap");
    auto bw = (jint (*)(void*, void*, jlong))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Bitmap_"
        "getWidth");
    auto br = (jint (*)(void*, void*, jlong))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Bitmap_"
        "getRows");
    auto bp = (jint (*)(void*, void*, jlong))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Bitmap_"
        "getPitch");
    auto gbuf = (void* (*)(void*, void*, jlong))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Bitmap_"
        "getBuffer");
    auto gdone = (void (*)(void*, void*, jlong))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Glyph_"
        "done");
    auto dfree = (void (*)(void*, void*, jlong))SYM(
        "Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Library_"
        "doneFreeType");
    if (!init_fn || !nmf || !sps || !lc || !gg || !gg2 || !tb || !gb || !bw ||
        !br || !bp || !gbuf || !gdone || !dfree) {
        fprintf(stderr, "SYM MISS\n");
        return 1;
    }
    // read the font file
    FILE* f = fopen(font, "rb");
    if (!f) { fprintf(stderr, "font open FAILED\n"); return 1; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    std::vector<unsigned char> bytes(sz);
    if (fread(bytes.data(), 1, sz, f) != (size_t)sz) { fclose(f); return 1; }
    fclose(f);
    g_bb_addr = bytes.data();
    g_bb_cap = sz;

    jlong lib = init_fn(&g_env_obj, nullptr);
    printf("init library=%ld\n", lib);
    if (!lib) return 1;
    // DEX-CALLER LAW: the native takes (library, buffer, SIZE, OFFSET)
    jlong face = nmf(&g_env_obj, nullptr, lib, (void*)0x9abc, (jint)sz, 0);
    printf("memory face=%ld\n", face);
    if (!face) return 1;
    printf("setPixelSizes(120)=%d\n", sps(&g_env_obj, nullptr, face, 0, 120));
    printf("loadChar('A')=%d\n", lc(&g_env_obj, nullptr, face, 'A', 0x4));
    // GDX-SEMANTICS LAW: Face.getGlyph = the SLOT pointer (no copy);
    // GlyphSlot.getGlyph = the owned FT_Glyph copy.
    jlong slot = gg(&g_env_obj, nullptr, face);
    printf("Face.getGlyph (slot)=%ld\n", slot);
    if (!slot) return 1;
    jlong glyph = gg2(&g_env_obj, nullptr, slot);
    printf("GlyphSlot.getGlyph=%ld\n", glyph);
    if (!glyph) return 1;
    jlong bmp_glyph = tb(&g_env_obj, nullptr, glyph, 2);  // FT_RENDER_MODE_NORMAL
    printf("toBitmap=%ld\n", bmp_glyph);
    if (!bmp_glyph) return 1;
    jlong bmp = gb(&g_env_obj, nullptr, bmp_glyph);
    int w = bw(&g_env_obj, nullptr, bmp);
    int r = br(&g_env_obj, nullptr, bmp);
    int p = bp(&g_env_obj, nullptr, bmp);
    void* buf = gbuf(&g_env_obj, nullptr, bmp);
    printf("bitmap buffer=%p cap=%ld rows=%d width=%d pitch=%d\n", buf,
           g_bb_cap, r, w, p);
    // count non-zero bytes = REAL render proof
    long nz = 0;
    for (int y = 0; y < r; ++y)
        for (int x = 0; x < p; ++x)
            if (((unsigned char*)g_bb_addr)[y * p + x]) ++nz;
    printf("non-zero texels=%ld / %d\n", nz, r * (p > 0 ? p : 0));
    gdone(&g_env_obj, nullptr, bmp_glyph);
    dfree(&g_env_obj, nullptr, lib);
    printf("PROBE %s\n", (r > 0 && w > 0 && nz > 0) ? "REAL-RENDER" : "EMPTY");
    return (r > 0 && w > 0 && nz > 0) ? 0 : 2;
}
