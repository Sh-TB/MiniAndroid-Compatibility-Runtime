// OSMesa sanity test: real software GL context + version + a clear call.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <GL/osmesa.h>
#include <GL/gl.h>

int main(void) {
    int attribs[] = { OSMESA_FORMAT, OSMESA_RGBA,
                      OSMESA_DEPTH_BITS, 24,
                      OSMESA_STENCIL_BITS, 8,
                      OSMESA_ACCUM_BITS, 0, 0 };
    OSMesaContext ctx = OSMesaCreateContextAttribs(attribs, NULL);
    if (!ctx) { printf("FAIL: OSMesaCreateContextAttribs\n"); return 1; }
    static unsigned char buf[256 * 256 * 4];
    if (!OSMesaMakeCurrent(ctx, buf, GL_UNSIGNED_BYTE, 256, 256)) {
        printf("FAIL: OSMesaMakeCurrent\n"); return 1;
    }
    printf("GL_VENDOR:   %s\n", (char*)glGetString(GL_VENDOR));
    printf("GL_RENDERER: %s\n", (char*)glGetString(GL_RENDERER));
    printf("GL_VERSION:  %s\n", (char*)glGetString(GL_VERSION));
    printf("GLSL:        %s\n", (char*)glGetString(GL_SHADING_LANGUAGE_VERSION));
    printf("EXTENSIONS contains GLES3? %s\n",
           strstr((char*)glGetString(GL_EXTENSIONS), "GL_ARB_ES3_compatibility") ? "yes" : "no");
    glClearColor(0.2f, 0.4f, 0.8f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    unsigned char px[4];
    glReadPixels(128, 128, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, px);
    printf("readback px: %d %d %d %d (expect 51 102 204 255)\n",
           px[0], px[1], px[2], px[3]);
    OSMesaDestroyContext(ctx);
    printf("OSMESA REAL GL OK\n");
    return 0;
}
