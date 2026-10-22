// CAMPAIGN 010 R9 — GLES20 bridge: real android.opengl.GLES20 API surface
// forwarded to PortableGL (MIT, rswinkle/PortableGL @ 7cf39dc).
//
// Android GLES20 is a static-method class whose methods map 1:1 onto C GL
// calls returning int handles (shaders/programs/buffers) or void. PGL
// implements the GL function set natively (glGenBuffers, glBindBuffer,
// glBufferData, glVertexAttribPointer, glDrawArrays, glDrawElements,
// glClear, glViewport, glEnable, depth/stencil/blend state, uniforms).
//
// GLSL SOURCE HONESTY: glShaderSource stores the GLSL string (traceable),
// glCompileShader records a compile attempt but PortableGL does NOT parse
// GLSL — programs execute C-function shaders registered via
// register_program_shaders(). For the golden cube the C shaders are exact
// functional equivalents of the GLSL source shipped in the harness. This
// limitation is documented in GLES_BACKEND_COMPARISON_010.md with the
// Mesa-llvmpipe alternative for arbitrary APK GLSL.
#ifndef MINIANDROID_GLES20_BRIDGE_H
#define MINIANDROID_GLES20_BRIDGE_H

#include <string>
#include <vector>
#include <map>
#include <cstdint>
#include <cstdint>
#include <map>

namespace miniandroid {
namespace gles {

// C-function shaders a program uses at draw time (PGL execution model).
struct PGLShaderFuncs {
    void* vert = nullptr;  // vert_func
    void* frag = nullptr;  // frag_func
    int interp_mode = 0;   // PGL_SMOOTH4 etc. (single-component count encoded by caller)
};

class GLES20Bridge {
public:
    static GLES20Bridge& instance();

    // Dispatch one GLES20 static method by Java name. Types mirror JNI:
    // args are int/float/bool/pointer(void*) values; returns true if the
    // method was handled. int_ret/float_ret receive the result when the
    // Java method returns int/float/boolean.
    bool dispatch(const std::string& method,
                  const uint64_t* iargs, int ni,
                  const float* fargs, int nf,
                  const void** pargs, int np,
                  int32_t* int_ret, float* float_ret,
                  std::string& trace);

    // PGL-specific: attach C-function shaders to a program "name" so that
    // glUseProgram(name) + draw calls execute them.
    void register_program_shaders(uint32_t program, void* vert, void* frag, int interp_n);

    // Counters for evidence/traces.
    struct Stats {
        uint64_t draws = 0, buffer_ops = 0, state_ops = 0, uniform_ops = 0;
        uint64_t shader_ops = 0, glsl_bytes = 0;
    };
    Stats stats() const { return stats_; }
    void reset_stats() { stats_ = {}; }

private:
    GLES20Bridge() = default;
    Stats stats_;
    std::map<uint32_t, PGLShaderFuncs> programs_;
    std::map<uint32_t, std::string> shader_sources_;
    uint32_t next_vert_ = 1, next_frag_ = 1;

    // ── F-NEW-505 (CONT-159): GLSL shader-handle family, engine-side ────
    // This PortableGL port stubs the whole GLSL surface (glCreateShader
    // returns 0, glCompileShader/glLinkProgram no-op — the backend renders
    // through fixed-function C-function programs, the register_program_
    // shaders path). The stubs leaked through the bridge as REAL answers:
    // glCreateShader → 0 → ShaderProgram.loadShader's `if (shader == 0)`
    // branch skipped the compile entirely → isCompiled() false →
    // SpriteBatch.createDefaultShader threw IllegalArgumentException →
    // AndroidLauncher.onCreate death (tower3d, the first libGDX-3D title to
    // reach SpriteBatch init). The engine owns the handle algebra:
    //   shaders:  handle → {type, source, compiled, deleted}
    //   programs: handle → {attached shaders, linked, deleted}
    //   locations: stable per-program (name → location) map so glUniform*
    //     calls bind the same slot the getter minted.
    // Status queries flow through the Java-side law (gl_surface_shadow
    // F-NEW-503b: COMPILE_STATUS/LINK_STATUS → GL_TRUE for engine-minted
    // handles). The GLSL source itself is stored for the trace (the
    // glsl-not-compiled honesty note stands).
    struct GlShader { uint32_t type = 0; bool compiled = false; bool deleted = false; };
    struct GlProgram { std::vector<uint32_t> attached; bool linked = false; bool deleted = false; };
    std::map<uint32_t, GlShader> gl_shaders_;
    std::map<uint32_t, GlProgram> gl_programs_;
    std::map<uint32_t, std::map<std::string, int32_t>> gl_locations_;
    uint32_t gl_next_shader_ = 1;
    uint32_t gl_next_program_ = 1;
};

}  // namespace gles
}  // namespace miniandroid

#endif  // MINIANDROID_GLES20_BRIDGE_H
