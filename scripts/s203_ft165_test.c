// s203_ft165_test.c — render chars 32..200 from Roboto-Medium.ttf at 120px
// via HOST freetype directly — isolates whether FT_Render_Glyph hangs on
// char 165 (¥) or whether the engine dispatch is the wall.
#include <stdio.h>
#include <stdlib.h>
#include <ft2build.h>
#include FT_FREETYPE_H

int main(void) {
    FT_Library lib;
    if (FT_Init_FreeType(&lib)) { fprintf(stderr, "init fail\n"); return 1; }
    FT_Face face;
    if (FT_New_Memory_Face(lib, (const FT_Byte*)0, 0, 0, &face) == 0) {}
    FILE* f = fopen("/tmp/Roboto-Medium.ttf", "rb");
    if (!f) { perror("font"); return 1; }
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    unsigned char* buf = malloc(sz);
    if (fread(buf, 1, sz, f) != (size_t)sz) { perror("read"); return 1; }
    fclose(f);
    if (FT_New_Memory_Face(lib, buf, sz, 0, &face)) {
        fprintf(stderr, "face fail\n"); return 1;
    }
    printf("faces=%ld num_glyphs=%lu\n", (long)face,
           (unsigned long)face->num_glyphs);
    if (FT_Set_Pixel_Sizes(face, 0, 120)) { printf("setPx fail\n"); return 1; }
    int rendered = 0;
    for (int ch = 32; ch <= 200; ++ch) {
        if (FT_Load_Char(face, (FT_ULong)ch, FT_LOAD_DEFAULT)) {
            printf("ch %d load FAIL\n", ch);
            continue;
        }
        FT_GlyphSlot slot = face->glyph;
        printf("ch %d format=%d bmp=%dx%d ... ", ch, (int)slot->format,
               slot->bitmap.width, slot->bitmap.rows);
        fflush(stdout);
        FT_Error e = FT_Render_Glyph(slot, FT_RENDER_MODE_NORMAL);
        printf("render e=%d rows=%d pitch=%d\n", (int)e,
               (int)slot->bitmap.rows, (int)slot->bitmap.pitch);
        fflush(stdout);
        rendered++;
    }
    printf("ALL DONE rendered=%d\n", rendered);
    return 0;
}
