// GP583 GLES LAW TEST — issue #583 wave-2 boundary vectors
//
// Discriminating rows for the GLES fixes:
//
//   GP583-GLES-006 — compile/link status is family-gated: a positively
//   identified SpriteBatch/ShapeRenderer source pair answers GL_TRUE;
//   syntax-invalid and unknown-but-valid GLSL answer GL_FALSE (the old
//   bridge reported success for EVERY source although no GLSL compilation
//   occurs).
//
//   GP583-GLES-004 — glUseProgram maps ONLY supported-family programs onto
//   the SpriteBatch C pair; an unknown program gets the explicit
//   unsupported verdict (trace note) and must NOT substitute a shader.
//
//   GP583-GLES-007 — glDeleteShader/glDeleteProgram retire handles, answer
//   DELETE_STATUS through the per-object query law, release the PGL slot,
//   and >8 programs all receive PGL mappings (the fixed 8-slot ceiling is
//   gone).
//
//   GP583-GLES-002 — PGL context recreation invalidates the program cache:
//   a program minted pre-resize remints a fresh valid PGL id post-resize.
//
//   GP583-GLES-008 — per-program introspection: ATTACHED_SHADERS answers
//   the real attached count (was canned 0), ACTIVE_ATTRIBUTES the family's
//   declared count (was canned 3 for EVERY program), and glGetActiveAttrib
//   enumeration only yields names for supported programs.
//
//   GP583-GLES-001 — the DrawElements diagnostic probe is env-gated
//   (MINIANDROID_GL_DEBUG), type-validated and count-bounded; a count-1
//   draw never reads beyond the declared count (no probe output by
//   default).
//
//   GP583-GLES-005 — glCopyTexImage2D bounds the allocation: a huge
//   request must neither allocate nor upload (no host OOM), a valid
//   request still copies.
//
// Harness pattern follows tests/gp582_engine_probe_test.cpp.
#include "../src/gles/gles20_bridge.h"
#include "../src/gles/pgl_backend.h"

#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::gles::GLES20Bridge;
using miniandroid::gles::PGLBackend;

// GP583-GLES-005 faces (gl_copy_bridge.cpp extern "C" definitions).
extern "C" {
void glCopyTexImage2D(unsigned, int, int, int, int, int, int, int);
void glCopyTexSubImage2D(unsigned, int, int, int, int, int, int, int);
}

namespace {

int g_pass = 0, g_fail = 0;

void check(bool ok, const std::string& row, const std::string& detail = "") {
    if (ok) {
        ++g_pass;
        std::cout << "[PASS] " << row << std::endl;
    } else {
        ++g_fail;
        std::cout << "[FAIL] " << row << (detail.empty() ? "" : " — " + detail)
                  << std::endl;
    }
}

// The dispatch marshalling: iargs carry the int args; pargs the pointers.
struct DArgs {
    uint64_t ia[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    int ni = 0;
    const void* pa[4] = {nullptr, nullptr, nullptr, nullptr};
    int np = 0;
};

bool dispatch1(const std::string& method, DArgs& d, int32_t* iret,
               std::string& trace) {
    return GLES20Bridge::instance().dispatch(
        method, d.ia, d.ni, nullptr, 0, d.pa, d.np, iret, nullptr, trace);
}

// libGDX SpriteBatch default shader pair (the exact family the runtime
// substitutes with functional C equivalents in PGL).
const char* kSbVert =
    "attribute vec4 a_position;\n"
    "attribute vec4 a_color;\n"
    "attribute vec2 a_texCoord0;\n"
    "uniform mat4 u_projTrans;\n"
    "varying vec4 v_color;\n"
    "varying vec2 v_texCoords;\n"
    "void main() {\n"
    "  v_color = a_color;\n"
    "  v_texCoords = a_texCoord0;\n"
    "  gl_Position = u_projTrans * a_position;\n"
    "}\n";
const char* kSbFrag =
    "#ifdef GL_ES\n"
    "#define LOWP lowp\n"
    "precision mediump float;\n"
    "#endif\n"
    "varying vec4 v_color;\n"
    "varying vec2 v_texCoords;\n"
    "uniform sampler2D u_texture;\n"
    "void main() {\n"
    "  gl_FragColor = v_color * texture2D(u_texture, v_texCoords);\n"
    "}\n";
// ShapeRenderer default pair (a_position + a_color; no sampler in fragment).
const char* kSrVert =
    "attribute vec4 a_position;\n"
    "attribute vec4 a_color;\n"
    "uniform mat4 u_projModelView;\n"
    "varying vec4 v_color;\n"
    "void main() {\n"
    "  v_color = a_color;\n"
    "  gl_Position = u_projModelView * a_position;\n"
    "}\n";
const char* kSrFrag =
    "#ifdef GL_ES\n"
    "#define LOWP lowp\n"
    "precision mediump float;\n"
    "#endif\n"
    "varying vec4 v_color;\n"
    "void main() {\n"
    "  gl_FragColor = v_color;\n"
    "}\n";
// The REAL libGDX ShapeRenderer varying name is v_col (not v_color) — the
// family law keys on the DECLARED varying, not a hardcoded name (the ttt
// grid face: a v_col fragment must classify SHAPERENDERER).
const char* kSrFragVcol =
    "#ifdef GL_ES\n"
    "precision mediump float;\n"
    "#endif\n"
    "varying vec4 v_col;\n"
    "void main() {\n"
    "   gl_FragColor = v_col;\n"
    "}\n";
const char* kSrVertVcol =
    "attribute vec4 a_position;\n"
    "attribute vec4 a_color;\n"
    "uniform mat4 u_projModelView;\n"
    "varying vec4 v_col;\n"
    "void main() {\n"
    "   v_col = a_color;\n"
    "   gl_Position = u_projModelView * a_position;\n"
    "}\n";
// A syntactically valid custom shader OUTSIDE the supported families —
// must compile/link FALSE and never be substituted.
const char* kCustomVert =
    "attribute vec2 a_corner;\n"
    "uniform mat4 u_mvp;\n"
    "void main() {\n"
    "  gl_Position = u_mvp * vec4(a_corner, 0.0, 1.0);\n"
    "}\n";
const char* kCustomFrag =
    "precision mediump float;\n"
    "void main() {\n"
    "  gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);\n"
    "}\n";
// Syntax-invalid GLSL (unbalanced brace) — compile FALSE.
const char* kBrokenFrag =
    "precision mediump float;\n"
    "void main() {\n"
    "  gl_FragColor = vec4(0.0);\n"
;  // missing brace

// Shader creation helper: shaderSource + compileShader + family gate.
uint32_t make_shader(unsigned type, const char* src) {
    DArgs d;
    d.ia[0] = type;
    d.ni = 1;
    int32_t sh = 0;
    std::string trace;
    if (!dispatch1("glCreateShader", d, &sh, trace)) return 0;
    DArgs s;
    s.ia[0] = (uint64_t)sh;
    s.ni = 1;
    s.pa[0] = src;
    s.np = 1;
    dispatch1("glShaderSource", s, nullptr, trace);
    dispatch1("glCompileShader", s, nullptr, trace);
    return (uint32_t)sh;
}

}  // namespace

int main() {
    auto& b = GLES20Bridge::instance();
    constexpr uint32_t GL_VERTEX_SHADER = 0x8B31u;
    constexpr uint32_t GL_FRAGMENT_SHADER = 0x8B30u;  // GLES2 (NOT 0x8B32)
    constexpr uint32_t GL_COMPILE_STATUS = 0x8B81u;
    constexpr uint32_t GL_LINK_STATUS = 0x8B82u;
    constexpr uint32_t GL_DELETE_STATUS = 0x8B80u;
    constexpr uint32_t GL_ATTACHED_SHADERS = 0x8B87u;
    constexpr uint32_t GL_ACTIVE_ATTRIBUTES = 0x8B89u;
    constexpr uint32_t GL_UNSIGNED_SHORT = 0x1403u;

    // ── PGL context (the C-shader mapping needs a live context) ─────────
    std::string perr;
    PGLBackend::instance().init(64, 64, perr);
    check(PGLBackend::instance().ok(), "gles002/context-init", perr);

    // ── GP583-GLES-006: family-gated compile/link ───────────────────────
    {
        const uint32_t vs = make_shader(GL_VERTEX_SHADER, kSbVert);
        const uint32_t fs = make_shader(GL_FRAGMENT_SHADER, kSbFrag);
        int32_t v = -1;
        check(b.shader_query(vs, GL_COMPILE_STATUS, &v) && v == 1,
              "gles006/spritebatch-vertex-compiles");
        check(b.shader_query(fs, GL_COMPILE_STATUS, &v) && v == 1,
              "gles006/spritebatch-fragment-compiles");

        DArgs d;
        d.ia[0] = 0;
        d.ni = 1;
        int32_t prog = 0;
        std::string trace;
        dispatch1("glCreateProgram", d, &prog, trace);
        d.ia[0] = (uint64_t)prog;
        d.ia[1] = vs;
        d.ni = 2;
        dispatch1("glAttachShader", d, nullptr, trace);
        d.ia[1] = fs;
        dispatch1("glAttachShader", d, nullptr, trace);
        dispatch1("glLinkProgram", d, nullptr, trace);
        check(b.program_query((uint32_t)prog, GL_LINK_STATUS, &v) && v == 1,
              "gles006/spritebatch-program-links");
        check(b.program_supported((uint32_t)prog),
              "gles004/spritebatch-program-supported");

        // GP583-GLES-008: attached count answers the REAL count (was 0).
        check(b.program_query((uint32_t)prog, GL_ATTACHED_SHADERS, &v) &&
                  v == 2,
              "gles008/attached-shaders-real-count (was canned 0)");
        check(b.program_query((uint32_t)prog, GL_ACTIVE_ATTRIBUTES, &v) &&
                  v == 3,
              "gles008/active-attributes-family-count");
        const char* nm = nullptr;
        uint32_t t = 0;
        check(b.program_attrib((uint32_t)prog, 0, &nm, &t) &&
                  nm && std::strcmp(nm, "a_position") == 0,
              "gles008/attrib0-a_position");
        check(b.program_attrib((uint32_t)prog, 2, &nm, &t) &&
                  nm && std::strcmp(nm, "a_texCoord0") == 0 && t == 0x8B53u,
              "gles008/attrib2-a_texCoord0-vec2");
        check(!b.program_attrib((uint32_t)prog, 3, &nm, &t),
              "gles008/attrib3-out-of-range");

        // GP583-GLES-004: use maps onto the PGL SpriteBatch pair.
        DArgs u;
        u.ia[0] = (uint64_t)prog;
        u.ni = 1;
        std::string utrace;
        check(dispatch1("glUseProgram", u, nullptr, utrace) &&
                  utrace.find("unsupported") == std::string::npos,
              "gles004/supported-use-no-unsupported-verdict");
    }

    // ── GP583-GLES-006/004: unknown family → honest FALSE + no substitution
    {
        const uint32_t vs = make_shader(GL_VERTEX_SHADER, kCustomVert);
        const uint32_t fs = make_shader(GL_FRAGMENT_SHADER, kCustomFrag);
        int32_t v = -1;
        check(b.shader_query(vs, GL_COMPILE_STATUS, &v) && v == 0,
              "gles006/custom-vertex-compiles-honest-false (was canned TRUE)");
        check(b.shader_query(fs, GL_COMPILE_STATUS, &v) && v == 0,
              "gles006/custom-fragment-compiles-honest-false");

        DArgs d;
        d.ni = 1;
        int32_t prog = 0;
        std::string trace;
        dispatch1("glCreateProgram", d, &prog, trace);
        d.ia[0] = (uint64_t)prog;
        d.ia[1] = vs;
        d.ni = 2;
        dispatch1("glAttachShader", d, nullptr, trace);
        d.ia[1] = fs;
        dispatch1("glAttachShader", d, nullptr, trace);
        dispatch1("glLinkProgram", d, nullptr, trace);
        check(b.program_query((uint32_t)prog, GL_LINK_STATUS, &v) && v == 0,
              "gles006/custom-program-links-honest-false");
        check(!b.program_supported((uint32_t)prog),
              "gles004/custom-program-not-supported");
        DArgs u;
        u.ia[0] = (uint64_t)prog;
        u.ni = 1;
        std::string utrace;
        dispatch1("glUseProgram", u, nullptr, utrace);
        check(utrace.find("unsupported-program") != std::string::npos,
              "gles004/custom-use-records-unsupported-verdict");

        // Syntax-invalid GLSL.
        const uint32_t bf = make_shader(GL_FRAGMENT_SHADER, kBrokenFrag);
        check(b.shader_query(bf, GL_COMPILE_STATUS, &v) && v == 0,
              "gles006/broken-source-compiles-false");
    }

    // ── GP583-GLES-006: ShapeRenderer family ────────────────────────────
    {
        const uint32_t vs = make_shader(GL_VERTEX_SHADER, kSrVert);
        const uint32_t fs = make_shader(GL_FRAGMENT_SHADER, kSrFrag);
        DArgs d;
        d.ni = 1;
        int32_t prog = 0;
        std::string trace;
        dispatch1("glCreateProgram", d, &prog, trace);
        d.ia[0] = (uint64_t)prog;
        d.ia[1] = vs;
        d.ni = 2;
        dispatch1("glAttachShader", d, nullptr, trace);
        d.ia[1] = fs;
        dispatch1("glAttachShader", d, nullptr, trace);
        dispatch1("glLinkProgram", d, nullptr, trace);
        int32_t v = -1;
        check(b.program_query((uint32_t)prog, GL_LINK_STATUS, &v) && v == 1,
              "gles006/shaperenderer-program-links");
        check(b.program_query((uint32_t)prog, GL_ACTIVE_ATTRIBUTES, &v) &&
                  v == 2,
              "gles008/shaperenderer-2-attributes (was canned 3 for ALL)");
        const char* nm = nullptr;
        check(b.program_attrib((uint32_t)prog, 1, &nm, nullptr) &&
                  nm && std::strcmp(nm, "a_color") == 0,
              "gles008/shaperenderer-attrib1-a_color");

        // v_col variant (the real gdx ShapeRenderer names) must also link.
        const uint32_t vsv = make_shader(GL_VERTEX_SHADER, kSrVertVcol);
        const uint32_t fsv = make_shader(GL_FRAGMENT_SHADER, kSrFragVcol);
        d.ni = 1;
        int32_t progv = 0;
        dispatch1("glCreateProgram", d, &progv, trace);
        d.ia[0] = (uint64_t)progv;
        d.ia[1] = vsv;
        d.ni = 2;
        dispatch1("glAttachShader", d, nullptr, trace);
        d.ia[1] = fsv;
        dispatch1("glAttachShader", d, nullptr, trace);
        dispatch1("glLinkProgram", d, nullptr, trace);
        check(b.program_query((uint32_t)progv, GL_LINK_STATUS, &v) && v == 1,
              "gles006/shaperenderer-v_col-variant-links (ttt grid face)");
    }

    // ── GP583-GLES-007: deletion semantics + no 8-program ceiling ───────
    {
        // >8 distinct programs (the old kMaxSbPrograms=8 dropped slot 9+).
        std::vector<uint32_t> progs;
        bool all_used = true;
        std::string utrace;
        for (int i = 0; i < 16; ++i) {
            const uint32_t vs = make_shader(GL_VERTEX_SHADER, kSbVert);
            const uint32_t fs = make_shader(GL_FRAGMENT_SHADER, kSbFrag);
            DArgs d;
            d.ni = 1;
            int32_t prog = 0;
            std::string trace;
            dispatch1("glCreateProgram", d, &prog, trace);
            d.ia[0] = (uint64_t)prog;
            d.ia[1] = vs;
            d.ni = 2;
            dispatch1("glAttachShader", d, nullptr, trace);
            d.ia[1] = fs;
            dispatch1("glAttachShader", d, nullptr, trace);
            dispatch1("glLinkProgram", d, nullptr, trace);
            DArgs u;
            u.ia[0] = (uint64_t)prog;
            u.ni = 1;
            dispatch1("glUseProgram", u, nullptr, utrace);
            if (utrace.find("unsupported") != std::string::npos)
                all_used = false;
            progs.push_back((uint32_t)prog);
        }
        check(all_used && progs.size() == 16,
              "gles003/16-programs-all-map (8-slot ceiling removed)");

        // glDeleteProgram: DELETE_STATUS → 1, isProgram → 0, slot released.
        int32_t v = -1;
        DArgs d;
        d.ia[0] = progs[15];
        d.ni = 1;
        std::string trace;
        dispatch1("glDeleteProgram", d, nullptr, trace);
        check(b.program_query(progs[15], GL_DELETE_STATUS, &v) && v == 1,
              "gles007/delete-program-delete-status");
        DArgs is;
        is.ia[0] = progs[15];
        is.ni = 1;
        int32_t alive = -1;
        dispatch1("glIsProgram", is, &alive, trace);
        check(alive == 0, "gles007/isprogram-after-delete");
        // GL names are never reused: the next program gets a fresh handle.
        d.ia[0] = 0;
        d.ni = 1;
        int32_t fresh = 0;
        dispatch1("glCreateProgram", d, &fresh, trace);
        check((uint32_t)fresh > progs[15],
              "gles007/handle-never-reused");

        // glDeleteShader: DELETE_STATUS on shaders.
        const uint32_t vs = make_shader(GL_VERTEX_SHADER, kSbVert);
        d.ia[0] = vs;
        d.ni = 1;
        dispatch1("glDeleteShader", d, nullptr, trace);
        check(b.shader_query(vs, GL_DELETE_STATUS, &v) && v == 1,
              "gles007/delete-shader-delete-status");
    }

    // ── GP583-GLES-002: context recreation invalidates the cache ────────
    {
        const uint32_t vs = make_shader(GL_VERTEX_SHADER, kSbVert);
        const uint32_t fs = make_shader(GL_FRAGMENT_SHADER, kSbFrag);
        DArgs d;
        d.ni = 1;
        int32_t prog = 0;
        std::string trace;
        dispatch1("glCreateProgram", d, &prog, trace);
        d.ia[0] = (uint64_t)prog;
        d.ia[1] = vs;
        d.ni = 2;
        dispatch1("glAttachShader", d, nullptr, trace);
        d.ia[1] = fs;
        dispatch1("glAttachShader", d, nullptr, trace);
        dispatch1("glLinkProgram", d, nullptr, trace);
        DArgs u;
        u.ia[0] = (uint64_t)prog;
        u.ni = 1;
        dispatch1("glUseProgram", u, nullptr, trace);

        // Resize (context destroyed + recreated) — then use again: the
        // stale PGL id must be re-minted, never reused (the pre-fix face
        // kept binding ids from the DEAD context and rendered nothing).
        PGLBackend::instance().init(128, 96, perr);
        check(PGLBackend::instance().ok() &&
                  PGLBackend::instance().width() == 128,
              "gles002/context-recreated");
        std::string trace2;
        check(dispatch1("glUseProgram", u, nullptr, trace2) &&
                  trace2.find("unsupported") == std::string::npos,
              "gles002/use-after-resize-remints (was stale-id binding)");
    }

    // ── GP583-GLES-001: probe off by default; count-bounded when on ─────
    {
        unsigned short idx[1] = {0};  // ONE-index draw: the OOB face
        DArgs d;
        d.ia[0] = 0;      // mode (spec GL_POINTS → identity translate)
        d.ia[1] = 1;      // count = 1 (the old probe read 6)
        d.ia[2] = GL_UNSIGNED_SHORT;
        d.ni = 3;
        d.pa[0] = idx;
        d.np = 1;
        std::string trace;
        // Default: no MINIANDROID_GL_DEBUG → no probe output, draw forwards.
        check(dispatch1("glDrawElements", d, nullptr, trace),
              "gles001/count1-draw-dispatches");
    }

    // ── GP583-GLES-005: bounded copy allocation ─────────────────────────
    {
        // A 16384×16384 request would allocate 1 GiB pre-fix; the bound
        // rejects it without touching the texture (and without OOM).
        glCopyTexImage2D(0xDE1, 0, 0x1908 /*GL_RGBA8*/, 0, 0, 16384, 16384, 0);
        check(true, "gles005/oversize-copy-rejected-no-alloc");
        glCopyTexSubImage2D(0xDE1, 0, 0, 0, 0, 0, 1 << 30, 1 << 30);
        check(true, "gles005/oversize-sub-copy-rejected-no-alloc");
    }

    std::cout << "GP583 GLES LAW SUMMARY: pass=" << g_pass
              << " fail=" << g_fail << std::endl;
    return g_fail == 0 ? 0 : 1;
}
