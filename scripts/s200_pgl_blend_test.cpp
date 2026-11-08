// S200 Target-B: isolated PGL blend test — does a fragment with alpha > 1
// (the observed out.a = 13-17 from the garbage v_color path) commit BLACK
// or produce a wrapped/clamped-white pixel over a white clear?
#include <portablegl.h>  // impl lives in pgl_backend.cpp (single-TU law)
#include "pgl_backend.h"
using namespace miniandroid::gles;
#include <cstdio>
#include <cstring>

static uint32_t* backbuf;

// viewport matrix: (0..16) px -> NDC (-1..1), y-flip like the SB camera
struct U { float m[16] = {0.125f, 0, 0, 0,  0, -0.125f, 0, 0,
                          0, 0, 1, 0,  -1, 1, 0, 1}; };
static U u;

void vsh(float* vs_out, vec4* va, Shader_Builtins* b, void* un) {
    static long n = 0;
    if (n < 4)
        std::printf("vsh #%ld pos=%.1f,%.1f,%.1f,%.1f col=%.1f,%.1f,%.1f,%.1f\n",
                    ++n, va[0].x, va[0].y, va[0].z, va[0].w,
                    va[1].x, va[1].y, va[1].z, va[1].w);
    ((vec4*)vs_out)[0] = va[1];
    b->gl_Position = mult_m4_v4(((U*)un)->m, va[0]);
}
void fsh2(float* fs_in, Shader_Builtins* b, void* un) {
    (void)un;
    vec4 c = ((vec4*)fs_in)[0];
    b->gl_FragColor = c;
}

// mirror of the runtime sb pair: 6-float varyings, texture multiply
static GLuint g_tex;
void sb_vert(float* vs_output, vec4* vertex_attribs, Shader_Builtins* builtins,
             void* uniforms) {
    static int vn = 0;
    if (vn < 6)
        std::printf("mvsh #%d pos=%.1f,%.1f col=%.4f,%.4f,%.4f,%.4f uv=%.3f,%.3f\n",
                    vn++, vertex_attribs[0].x, vertex_attribs[0].y,
                    vertex_attribs[1].x, vertex_attribs[1].y,
                    vertex_attribs[1].z, vertex_attribs[1].w,
                    vertex_attribs[2].x, vertex_attribs[2].y);
    ((vec4*)vs_output)[0] = vertex_attribs[1];
    vec2 uv = {vertex_attribs[2].x, vertex_attribs[2].y};
    ((vec2*)vs_output)[2] = uv;
    builtins->gl_Position = mult_m4_v4(((U*)uniforms)->m, vertex_attribs[0]);
}
void sb_frag(float* fs_input, Shader_Builtins* builtins, void* uniforms) {
    (void)uniforms;
    vec4 v_color = ((vec4*)fs_input)[0];
    vec2 uv = ((vec2*)fs_input)[2];
    GLuint tex = miniandroid::gles::pgl_bound_texture_2d();
    builtins->gl_FragColor = mult_v4s(v_color, texture2D(tex, uv.x, uv.y));
}

int main() {
    miniandroid::gles::PGLBackend::instance();
    std::string err;
    miniandroid::gles::PGLBackend::instance().init(96, 96, err);
    auto* bb = const_cast<uint32_t*>(miniandroid::gles::PGLBackend::instance().pixels());

    glClearColor(1, 1, 1, 1);
    glClear(GL_COLOR_BUFFER_BIT);

    // 16x16 red opaque texture (name 1)
    glGenTextures(1, &g_tex);
    glBindTexture(GL_TEXTURE_2D, g_tex);
    unsigned char texpx[16 * 16 * 4];
    for (int k = 0; k < 16 * 16; ++k) {
        texpx[k * 4 + 0] = 255; texpx[k * 4 + 1] = 0;
        texpx[k * 4 + 2] = 0;   texpx[k * 4 + 3] = 255;
    }
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 16, 16, 0, GL_RGBA,
                 GL_UNSIGNED_BYTE, texpx);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);

    GLenum interp[6] = {PGL_SMOOTH4, PGL_SMOOTH2};
    GLuint prog = pglCreateProgram(sb_vert, sb_frag, 6, interp, GL_FALSE);
    glUseProgram(prog);
    // SB-like matrix: (0..96)px -> NDC, y-flip
    U u;  // 0.020833 = 2/96
    for (int k = 0; k < 16; ++k) u.m[k] = 0;
    u.m[0] = 2.0f / 96; u.m[5] = -2.0f / 96;
    u.m[12] = -1; u.m[13] = 1; u.m[15] = 1;
    pglSetProgramUniform(prog, &u);

    // app-exact vertex format: stride 20 = pos(2F) + color(4xUB@8) + uv(2F@12)
    // color bytes = (0,0,0,254) black a254; uv = full texture
    unsigned char vtx[6][20];
    const float pos[4][2] = {{0, 0}, {96, 0}, {96, 96}, {0, 96}};
    const float uvs[4][2] = {{0, 1}, {1, 1}, {1, 0}, {0, 0}};
    const unsigned char col[4] = {0, 0, 0, 254};
    int idx6[6] = {0, 1, 2, 2, 3, 0};
    for (int k = 0; k < 6; ++k) {
        std::memcpy(vtx[k], pos[idx6[k]], 8);
        std::memcpy(vtx[k] + 8, col, 4);
        std::memcpy(vtx[k] + 12, uvs[idx6[k]], 8);
    }
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 20, vtx);
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 4, GL_UNSIGNED_BYTE, GL_TRUE, 20, vtx[0] + 8);
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 20, vtx[0] + 12);

    glEnable(GL_BLEND);
    glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE,
                        GL_ONE_MINUS_SRC_ALPHA);
    glDrawArrays(GL_TRIANGLES, 0, 6);
    std::printf("mirror app path px(48,48) = %08x (expect ff0000-ish red)\n",
                bb[48 * 96 + 48]);
    std::printf("mirror app path px(2,2)   = %08x\n", bb[2 * 96 + 2]);
    return 0;
}
