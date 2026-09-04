// CAMPAIGN 010 R9/R10 — golden GLES cube through the MiniAndroid GLES20
// bridge (PortableGL backend) → framebuffer → PNG (libpng writer).
//
// Real GLES2 pipeline: shader program (PGL C-function shaders — exact
// functional equivalents of the GLSL below), VBO created THROUGH the
// bridge, per-vertex color+normal, depth test, MVP matrix, timed frames.
//
//   #version 100
//   attribute vec4 a_pos; attribute vec3 a_color; attribute vec3 a_normal;
//   uniform mat4 u_mvp; uniform mat4 u_model;
//   varying vec3 v_color; varying vec3 v_normal;
//   void main() {
//     gl_Position = u_mvp * a_pos;
//     v_color = a_color;
//     v_normal = mat3(u_model) * a_normal;
//   }
//   #version 100
//   precision mediump float;
//   varying vec3 v_color; varying vec3 v_normal;
//   void main() {
//     float lam = max(dot(normalize(v_normal), normalize(vec3(0.4,0.7,0.6))), 0.0);
//     gl_FragColor = vec4(v_color * (0.25 + 0.75 * lam), 1.0);
//   }
//
// Build (from repo/miniandroid):
//   g++ -std=c++17 -O2 -Isrc -Isrc/gles -I$PGL_DIR -Ithird_party/nlohmann_json/include \
//       -I$RLOTTIE/inc run/uc010_gles_cube.cpp src/gles/pgl_backend.cpp \
//       src/gles/gles20_bridge.cpp src/renderer/software_renderer.cpp \
//       -o build/uc010_gles_cube -lz -lwebp -lwebpdemux -ljpeg $RLOTTIE/librlottie.a \
//       -lstdc++ -lm -lpthread -lfreetype -lharfbuzz -lfribidi -lpng
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <chrono>
#include <string>
#include <vector>

#include "gles/pgl_backend.h"
#include "gles/gles20_bridge.h"

#include <portablegl.h>

#include "renderer/software_renderer.h"

using miniandroid::gles::PGLBackend;
using miniandroid::gles::GLES20Bridge;
using namespace miniandroid::renderer;

// ---- PGL C-function shaders (equivalents of the GLSL above) --------------
// 2 vec4 varyings (color, normal) = 8 interpolated floats.
struct CubeUniforms {
    mat4 mvp;
    mat4 model;
};

void cube_vs(float* vs_output, vec4* vertex_attribs, Shader_Builtins* builtins, void* uniforms) {
    CubeUniforms* u = (CubeUniforms*)uniforms;
    ((vec4*)vs_output)[0] = vertex_attribs[1];                 // v_color
    vec4 n_model = mult_m4_v4(u->model, vertex_attribs[2]);    // normal in world space
    ((vec4*)vs_output)[1] = vec4{n_model.x, n_model.y, n_model.z, 0.0f};
    builtins->gl_Position = mult_m4_v4(u->mvp, vertex_attribs[0]);
}

void cube_fs(float* fs_input, Shader_Builtins* builtins, void* uniforms) {
    (void)uniforms;
    vec3 n = { ((vec4*)fs_input)[1].x, ((vec4*)fs_input)[1].y, ((vec4*)fs_input)[1].z };
    normalize_v3(&n);
    vec3 l = { 0.4f, 0.7f, 0.6f };
    normalize_v3(&l);
    float lam = dot_v3s(n, l);
    if (lam < 0.0f) lam = 0.0f;
    float k = 0.25f + 0.75f * lam;
    vec4 c = ((vec4*)fs_input)[0];
    builtins->gl_FragColor = vec4{c.x * k, c.y * k, c.z * k, 1.0f};
}

// ---- cube geometry: pos(3) color(3) normal(3), 36 verts -------------------
static const float CUBE_VERTS[] = {
    // +Z face (red)
    -1,-1, 1,  1,0,0,  0,0,1,   1,-1, 1,  1,0,0,  0,0,1,   1, 1, 1,  1,0,0,  0,0,1,
    -1,-1, 1,  1,0,0,  0,0,1,   1, 1, 1,  1,0,0,  0,0,1,  -1, 1, 1,  1,0,0,  0,0,1,
    // -Z face (green)
    -1,-1,-1,  0,1,0,  0,0,-1,  1, 1,-1,  0,1,0,  0,0,-1,   1,-1,-1,  0,1,0,  0,0,-1,
    -1,-1,-1,  0,1,0,  0,0,-1, -1, 1,-1,  0,1,0,  0,0,-1,   1, 1,-1,  0,1,0,  0,0,-1,
    // +Y face (blue)
    -1, 1,-1,  0,0,1,  0,1,0,  -1, 1, 1,  0,0,1,  0,1,0,    1, 1, 1,  0,0,1,  0,1,0,
    -1, 1,-1,  0,0,1,  0,1,0,   1, 1, 1,  0,0,1,  0,1,0,    1, 1,-1,  0,0,1,  0,1,0,
    // -Y face (yellow)
    -1,-1, 1,  1,1,0,  0,-1,0,  1,-1,-1,  1,1,0,  0,-1,0,  -1,-1,-1,  1,1,0,  0,-1,0,
    -1,-1, 1,  1,1,0,  0,-1,0,  1, 1,-1,  1,1,0,  0,-1,0,   1,-1, 1,  1,1,0,  0,-1,0,
    // +X face (magenta)
     1,-1, 1,  1,0,1,  1,0,0,   1,-1,-1,  1,0,1,  1,0,0,    1, 1,-1,  1,0,1,  1,0,0,
     1,-1, 1,  1,0,1,  1,0,0,   1, 1,-1,  1,0,1,  1,0,0,    1, 1, 1,  1,0,1,  1,0,0,
    // -X face (cyan)
    -1,-1,-1,  0,1,1, -1,0,0,  -1,-1, 1,  0,1,1, -1,0,0,   -1, 1, 1,  0,1,1, -1,0,0,
    -1,-1,-1,  0,1,1, -1,0,0,  -1, 1, 1,  0,1,1, -1,0,0,   -1, 1,-1,  0,1,1, -1,0,0,
};

// ---- mat4 helpers (column-major, matching PGL mult_mat4_vec4) -------------
static void mat4_identity(float* m) {
    std::memset(m, 0, 16 * sizeof(float));
    m[0] = m[5] = m[10] = m[15] = 1.0f;
}
static void mat4_mul(float* out, const float* a, const float* b) {
    float r[16];
    for (int c = 0; c < 4; c++)
        for (int row = 0; row < 4; row++) {
            float s = 0;
            for (int k = 0; k < 4; k++) s += a[k * 4 + row] * b[c * 4 + k];
            r[c * 4 + row] = s;
        }
    std::memcpy(out, r, sizeof(r));
}
static void mat4_perspective(float* m, float fovy, float aspect, float n, float f) {
    std::memset(m, 0, 16 * sizeof(float));
    float t = 1.0f / std::tan(fovy * 0.5f);
    m[0] = t / aspect; m[5] = t;
    m[10] = (f + n) / (n - f); m[11] = -1.0f;
    m[14] = 2.0f * f * n / (n - f);
}
static void mat4_translate(float* m, float x, float y, float z) {
    mat4_identity(m); m[12] = x; m[13] = y; m[14] = z;
}
static void mat4_rotate_y(float* m, float a) {
    mat4_identity(m);
    m[0] = std::cos(a);  m[2] = std::sin(a);
    m[8] = -std::sin(a); m[10] = std::cos(a);
}
static void mat4_rotate_x(float* m, float a) {
    mat4_identity(m);
    m[5] = std::cos(a);  m[6] = std::sin(a);
    m[9] = -std::sin(a); m[10] = std::cos(a);
}

int main(int argc, char** argv) {
    const int W = argc > 1 ? atoi(argv[1]) : 320;
    const int H = argc > 2 ? atoi(argv[2]) : 240;
    const int FRAMES = argc > 3 ? atoi(argv[3]) : 24;
    const char* out_png = argc > 4 ? argv[4] : "/tmp/uc010_gles_cube.png";

    std::string err;
    static PGLBackend pgl;
    if (!pgl.init(W, H, err)) {
        printf("PGL init FAIL: %s\n", err.c_str());
        return 1;
    }

    GLES20Bridge& br = GLES20Bridge::instance();
    uint64_t ia[8]; float fa[8]; const void* pa[8];
    int32_t iret = 0; std::string trace;

    // ---- GLSL source registered through the bridge (trace/inspection) ----
    static const char* VS_GLSL =
        "attribute vec4 a_pos; attribute vec3 a_color; attribute vec3 a_normal;\n"
        "uniform mat4 u_mvp; uniform mat4 u_model;\n"
        "varying vec3 v_color; varying vec3 v_normal;\n"
        "void main(){ gl_Position = u_mvp * a_pos; v_color = a_color;"
        " v_normal = mat3(u_model) * a_normal; }";
    static const char* FS_GLSL =
        "precision mediump float; varying vec3 v_color; varying vec3 v_normal;\n"
        "void main(){ float lam = max(dot(normalize(v_normal),"
        " normalize(vec3(0.4,0.7,0.6))), 0.0);"
        " gl_FragColor = vec4(v_color * (0.25 + 0.75 * lam), 1.0); }";

    // glCreateShader/glShaderSource/glCompileShader through the bridge —
    // recorded (PGL does not compile GLSL; documented honestly).
    ia[0] = GL_VERTEX_SHADER;   br.dispatch("glCreateShader", ia, 1, 0, 0, 0, 0, &iret, 0, trace);
    uint32_t vs_name = (uint32_t)iret;
    ia[0] = GL_FRAGMENT_SHADER; br.dispatch("glCreateShader", ia, 1, 0, 0, 0, 0, &iret, 0, trace);
    uint32_t fs_name = (uint32_t)iret;
    ia[0] = vs_name; pa[0] = VS_GLSL; br.dispatch("glShaderSource", ia, 1, 0, 0, pa, 1, 0, 0, trace);
    ia[0] = fs_name; pa[0] = FS_GLSL; br.dispatch("glShaderSource", ia, 1, 0, 0, pa, 1, 0, 0, trace);
    ia[0] = vs_name; br.dispatch("glCompileShader", ia, 1, 0, 0, 0, 0, 0, 0, trace);
    ia[0] = fs_name; br.dispatch("glCompileShader", ia, 1, 0, 0, 0, 0, 0, 0, trace);

    // Program: PGL executes the C-function shader pair. PGL's program ids
    // ARE the GLES20 program names (same namespace) — create via
    // pglCreateProgram, register the mapping in the bridge, then use it
    // through the bridge's glUseProgram.
    GLenum interp8[8];
    for (int i = 0; i < 8; i++) interp8[i] = PGL_SMOOTH;
    GLuint pgl_prog = pglCreateProgram(cube_vs, cube_fs, 8, interp8, GL_FALSE);
    br.register_program_shaders(pgl_prog, (void*)cube_vs, (void*)cube_fs, 8);
    uint32_t prog_name = pgl_prog;
    // glUseProgram through the bridge (activates the PGL program).
    ia[0] = prog_name; br.dispatch("glUseProgram", ia, 1, 0, 0, 0, 0, 0, 0, trace);

    // ---- VBO through the bridge (real GLES2 buffer path) -----------------
    GLuint vbo = 0;
    ia[0] = 1; pa[1] = &vbo;
    br.dispatch("glGenBuffers", ia, 1, 0, 0, pa, 2, 0, 0, trace);
    ia[0] = GL_ARRAY_BUFFER; ia[1] = vbo; br.dispatch("glBindBuffer", ia, 2, 0, 0, 0, 0, 0, 0, trace);
    ia[0] = GL_ARRAY_BUFFER; ia[1] = (uint64_t)sizeof(CUBE_VERTS); pa[2] = CUBE_VERTS; ia[3] = GL_STATIC_DRAW;
    br.dispatch("glBufferData", ia, 4, 0, 0, pa, 3, 0, 0, trace);

    auto draw_frame = [&](float angle) {
        // state via bridge
        ia[0] = GL_DEPTH_TEST; br.dispatch("glEnable", ia, 1, 0, 0, 0, 0, 0, 0, trace);
        ia[0] = GL_LESS; br.dispatch("glDepthFunc", ia, 1, 0, 0, 0, 0, 0, 0, trace);
        ia[0] = 0; ia[1] = 0; ia[2] = (uint64_t)W; ia[3] = (uint64_t)H;
        br.dispatch("glViewport", ia, 4, 0, 0, 0, 0, 0, 0, trace);
        fa[0] = 0.08f; fa[1] = 0.10f; fa[2] = 0.14f; fa[3] = 1.0f;
        br.dispatch("glClearColor", ia, 0, fa, 4, 0, 0, 0, 0, trace);
        ia[0] = GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT;
        br.dispatch("glClear", ia, 1, 0, 0, 0, 0, 0, 0, trace);

        CubeUniforms uni;
        float proj[16], view[16], model[16], ry[16], rx[16], mv[16], mvp[16];
        mat4_perspective(proj, 60.0f * 3.14159265f / 180.0f, float(W) / H, 0.5f, 20.0f);
        mat4_translate(view, 0.0f, 0.0f, -6.0f);
        mat4_rotate_y(ry, angle);
        mat4_rotate_x(rx, angle * 0.7f);
        mat4_mul(model, ry, rx);
        mat4_mul(mv, view, model);
        mat4_mul(mvp, proj, mv);
        std::memcpy(uni.mvp, mvp, sizeof(mvp));
        std::memcpy(uni.model, model, sizeof(model));
        pglSetUniform(&uni);

        // attrib pointers (VBO-relative offsets) via bridge
        const void* off0 = (const void*)(intptr_t)0;
        const void* off3 = (const void*)(intptr_t)(3 * sizeof(float));
        const void* off6 = (const void*)(intptr_t)(6 * sizeof(float));
        ia[0] = 0; ia[1] = 3; ia[2] = GL_FLOAT; ia[3] = 0; ia[4] = 9 * sizeof(float);
        pa[5] = off0; br.dispatch("glVertexAttribPointer", ia, 5, 0, 0, pa, 6, 0, 0, trace);
        ia[0] = 1; pa[5] = off3; br.dispatch("glVertexAttribPointer", ia, 5, 0, 0, pa, 6, 0, 0, trace);
        ia[0] = 2; pa[5] = off6; br.dispatch("glVertexAttribPointer", ia, 5, 0, 0, pa, 6, 0, 0, trace);
        for (int i = 0; i < 3; i++) { ia[0] = (uint64_t)i; br.dispatch("glEnableVertexAttribArray", ia, 1, 0, 0, 0, 0, 0, 0, trace); }
        ia[0] = GL_TRIANGLES; ia[1] = 0; ia[2] = 36;
        br.dispatch("glDrawArrays", ia, 3, 0, 0, 0, 0, 0, 0, trace);
    };

    // Warm-up + timed run
    draw_frame(0.0f);
    auto t0 = std::chrono::steady_clock::now();
    for (int f = 0; f < FRAMES; f++) {
        draw_frame(f * (6.2831853f / FRAMES));
    }
    auto t1 = std::chrono::steady_clock::now();
    double total_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();

    // Last frame → framebuffer → PNG via the runtime's libpng writer.
    const uint32_t* px = pgl.pixels();
    FrameBuffer fb(W, H);
    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            uint32_t p = px[y * W + x];
            uint8_t r = p & 0xFF, g = (p >> 8) & 0xFF, b = (p >> 16) & 0xFF;
            fb.set_pixel(x, y, RGBA{r, g, b, 255});
        }
    }
    bool ok = PNGWriter::write_png(out_png, fb);

    auto st = br.stats();
    long long total_px = (long long)W * H * FRAMES;
    printf("uc010 GLES cube (PortableGL backend via GLES20Bridge)\n");
    printf("  resolution %dx%d, frames %d\n", W, H, FRAMES);
    printf("  total draw time: %.1f ms  (%.2f ms/frame, %.1f fps)\n",
           total_ms, total_ms / FRAMES, FRAMES * 1000.0 / total_ms);
    printf("  rasterized: %lld px  (%.1f Mpx/s)\n", total_px, total_px / 1000.0 / total_ms);
    printf("  PNG written: %s (%s)\n", out_png, ok ? "OK" : "FAIL");
    printf("  bridge stats: draws=%llu state=%llu buffer=%llu uniform=%llu shader=%llu glsl_bytes=%llu\n",
           (unsigned long long)st.draws, (unsigned long long)st.state_ops,
           (unsigned long long)st.buffer_ops, (unsigned long long)st.uniform_ops,
           (unsigned long long)st.shader_ops, (unsigned long long)st.glsl_bytes);

    long long nonbg = 0;
    for (int i = 0; i < W * H; i++) {
        uint32_t p = px[i];
        int r = p & 0xFF, g = (p >> 8) & 0xFF, b = (p >> 16) & 0xFF;
        // clear color (0.08,0.10,0.14) with ±3 tolerance for float rounding
        if (std::abs(r - 20) > 3 || std::abs(g - 25) > 3 || std::abs(b - 35) > 3) nonbg++;
    }
    printf("  non-background pixels: %lld / %d (%.1f%%)\n", nonbg, W * H,
           100.0 * nonbg / (W * H));
    return ok && nonbg > 1000 ? 0 : 2;
}
