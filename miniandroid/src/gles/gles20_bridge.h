// CAMPAIGN 010 R9 — GLES20 bridge: real android.opengl.GLES20 API surface
// forwarded to PortableGL (MIT, rswinkle/PortableGL @ 7cf39dc).
//
// Android GLES20 is a static-method class whose methods map 1:1 onto C GL
// calls returning int handles (shaders/programs/buffers) or void. PGL
// implements the GL function set natively (glGenBuffers, glBindBuffer,
// glBufferData, glVertexAttribPointer, glDrawArrays, glDrawElements,
// glClear, glViewport, glEnable, depth/stencil/blend state, uniforms).
//
// GLSL SOURCE HONESTY: glShaderSource stores the GLSL string (traceable).
// GP583-GLES-006: glCompileShader/glLinkProgram NO LONGER report success
// unconditionally — the source is classified first, and only a positively
// identified, source-verified shader family (the libGDX default SpriteBatch
// and ShapeRenderer pairs, whose exact functional C equivalents execute in
// PGL) answers COMPILE_STATUS/LINK_STATUS = GL_TRUE. Unknown GLSL answers
// GL_FALSE with an honest diagnostic — the app sees the unsupported
// boundary instead of silently running a substituted shader (GLES-004).
// Arbitrary GLSL stays the documented Mesa-llvmpipe frontier
// (GLES_BACKEND_COMPARISON_010.md).
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

    // ── GP583-GLES-006: positively-identified shader families ───────────
    enum class ShaderFamily {
        UNKNOWN = 0,       // arbitrary/unverifiable GLSL — NOT executable
        SPRITEBATCH = 1,   // libGDX SpriteBatch default shader family
        SHAPERENDERER = 2, // libGDX ShapeRenderer default shader family
        // ── F-BGLSL-1 (S226; #508 Vector-Pinball render chain): the two
        // Vector-Pinball GL20Renderer shader families (app assets
        // shaders/line.vert|frag + shaders/circle.vert|frag — upstream
        // dozingcat/Vector-Pinball). Line = flat-color geometry (the table
        // walls, 7794-index draw). Circle = per-fragment radial alpha
        // falloff against gl_FragCoord (ball/bumpers/flippers, 48-index
        // draw). Both classify structurally (attrib names + one mat4
        // uniform, no samplers) and execute as the registered C pairs.
        BOUNCY_LINE = 3,
        BOUNCY_CIRCLE = 4,
    };

    // ── GP583-GLES-008: PER-PROGRAM introspection (was canned/global) ──
    // Query answers are keyed by the actual engine-side object state.
    // Returns true when the handle is engine-minted and pname is answered
    // (out receives the value); false → caller falls back (PGL-native
    // handles). pnames answered: DELETE_STATUS (0x8B80), COMPILE_STATUS
    // (0x8B81), LINK_STATUS (0x8B82), ATTACHED_SHADERS (0x8B87 — the real
    // attached count, was canned 0), ACTIVE_ATTRIBUTES (0x8B89 — the
    // classified family's declared attribute count, was canned 3 for EVERY
    // program), ACTIVE_ATTRIBUTE_MAX_LENGTH (0x8B8A).
    bool shader_query(uint32_t shader, uint32_t pname, int32_t* out) const;
    bool program_query(uint32_t program, uint32_t pname, int32_t* out) const;

    // GP583-GLES-008: per-program active-attribute enumeration for a
    // supported family (index < ACTIVE_ATTRIBUTES). Returns false for
    // unknown-family/unknown programs — the caller must NOT fabricate
    // canonical names for unverifiable shaders.
    bool program_attrib(uint32_t program, uint32_t index,
                        const char** name, uint32_t* gl_type) const;

    // GP583-GLES-004: is this program a positively identified family whose
    // PGL C-shader mapping may be installed at glUseProgram?
    bool program_supported(uint32_t program) const;

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
        uint64_t shader_ops = 0, glsl_bytes = 0, tex_ops = 0;  // F-NEW-608
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
    //
    // GP583-GLES-006 UPDATE: "engine-minted → GL_TRUE" was exactly the
    // false-success the finding documents (compile status answered TRUE
    // although no GLSL compilation occurs). The status law is now
    // family-gated: a shader compiles only when its stored source belongs
    // to a positively identified supported family; a program links only
    // when its attached vertex+fragment pair compiles and is compatible.
    // The GlShader/GlProgram records carry the classification.
    struct GlShader {
        uint32_t type = 0;
        bool compiled = false;
        bool deleted = false;
        ShaderFamily family = ShaderFamily::UNKNOWN;  // source classification
    };
    struct GlProgram {
        std::vector<uint32_t> attached;
        bool linked = false;
        bool deleted = false;
        ShaderFamily family = ShaderFamily::UNKNOWN;
        bool supported = false;  // positively identified at link time
    };
    std::map<uint32_t, GlShader> gl_shaders_;
    std::map<uint32_t, GlProgram> gl_programs_;
    std::map<uint32_t, std::map<std::string, int32_t>> gl_locations_;
    uint32_t gl_next_shader_ = 1;
    uint32_t gl_next_program_ = 1;

    // ── F-NEW-609 (S198): the engine program currently mapped to the
    // SpriteBatch default C-shader PGL program (0 = none / real PGL id).
    uint32_t cur_engine_prog_ = 0;

    // Reverse lookup of the F-NEW-505 minted locations: minted id → name
    // (the SB glUniform* routing reads it; maps are tiny).
    const std::string* sb_uniform_name_for_loc(int32_t loc) const {
        if (!cur_engine_prog_) return nullptr;
        auto pit = gl_locations_.find(cur_engine_prog_);
        if (pit == gl_locations_.end()) return nullptr;
        for (const auto& kv : pit->second)
            if (kv.second == loc) return &kv.first;
        return nullptr;
    }
};

}  // namespace gles
}  // namespace miniandroid

#endif  // MINIANDROID_GLES20_BRIDGE_H
