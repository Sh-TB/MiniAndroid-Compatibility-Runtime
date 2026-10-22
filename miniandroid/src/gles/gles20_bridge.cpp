// CAMPAIGN 010 R9 — GLES20 bridge implementation over PortableGL.
// NOTE: PORTABLEGL_IMPLEMENTATION lives only in pgl_backend.cpp.
#include "gles20_bridge.h"
#include "pgl_backend.h"

#include <portablegl.h>

#include <sstream>
#include <cstring>
#include <cstdarg>

namespace miniandroid {
namespace gles {

GLES20Bridge& GLES20Bridge::instance() {
    static GLES20Bridge b;
    return b;
}

void GLES20Bridge::register_program_shaders(uint32_t program, void* vert,
                                            void* frag, int interp_n) {
    programs_[program] = PGLShaderFuncs{vert, frag, interp_n};
}

bool GLES20Bridge::dispatch(const std::string& method,
                            const uint64_t* iargs, int ni,
                            const float* fargs, int nf,
                            const void** pargs, int np,
                            int32_t* int_ret, float* float_ret,
                            std::string& trace) {
    (void)fargs; (void)nf; (void)float_ret;
    auto I = [&](int k) -> GLenum { return k < ni ? (GLenum)iargs[k] : 0; };
    auto P = [&](int k) -> const void* { return k < np ? pargs[k] : nullptr; };

    if (method == "glGetError") {
        if (int_ret) *int_ret = (int32_t)glGetError();
        stats_.state_ops++;
        return true;
    }
    // ---- shader/program lifecycle -------------------------------------
    if (method == "glCreateShader") {
        // F-NEW-505 (CONT-159): engine-side handle. The PGL port stubs this
        // (returns 0) — a 0 shader made ShaderProgram.loadShader skip the
        // compile (tower3d SpriteBatch death chain, see the header law).
        uint32_t sh = gl_next_shader_++;
        gl_shaders_[sh].type = I(0);
        if (int_ret) *int_ret = (int32_t)sh;
        stats_.shader_ops++;
        return true;
    }
    if (method == "glShaderSource") {
        // PGL does not compile GLSL; store source for trace + future
        // GLSL->C translation. iargs[0]=shader, pargs[0]=char* source.
        uint32_t sh = (uint32_t)I(0);
        const char* src = (const char*)P(0);
        shader_sources_[sh] = src ? src : "";
        stats_.glsl_bytes += shader_sources_[sh].size();
        return true;
    }
    if (method == "glCompileShader") {
        // F-NEW-505: engine-side compile-status law — the engine-minted
        // shader compiles (the status queries answer through the Java-side
        // F-NEW-503b law; the GLSL source itself is stored, not executed —
        // the glsl-not-compiled honesty note stands).
        auto git = gl_shaders_.find((uint32_t)I(0));
        if (git != gl_shaders_.end()) git->second.compiled = true;
        stats_.shader_ops++;
        trace += "glsl-not-compiled-by-pgl;engine-handle-compiled";
        return true;
    }
    if (method == "glCreateProgram") {
        // F-NEW-505: engine-side program handle (PGL stubs this → 0).
        uint32_t pr = gl_next_program_++;
        gl_programs_[pr];
        if (int_ret) *int_ret = (int32_t)pr;
        stats_.shader_ops++;
        return true;
    }
    if (method == "glAttachShader") {
        auto pit = gl_programs_.find((uint32_t)I(0));
        if (pit != gl_programs_.end())
            pit->second.attached.push_back((uint32_t)I(1));
        stats_.shader_ops++;
        return true;
    }
    if (method == "glLinkProgram") {
        // F-NEW-505: engine-side link-status law (pairs with the F-NEW-503b
        // LINK_STATUS query answer).
        auto pit = gl_programs_.find((uint32_t)I(0));
        if (pit != gl_programs_.end()) pit->second.linked = true;
        stats_.shader_ops++;
        return true;
    }
    if (method == "glUseProgram") {
        // If C shaders were registered for this program id, the owning code
        // created the matching PGL program via pglCreateProgram() under the
        // same id (see register_program_shaders).
        // F-NEW-505: engine-minted GLSL programs (gl_programs_) must NOT
        // reach PGL — its program namespace only contains pglCreateProgram
        // ids; an unknown id errors (and the fixed-function default path is
        // the honest render bound for stored-GLSL programs anyway).
        uint32_t prog = (uint32_t)I(0);
        if (gl_programs_.find(prog) == gl_programs_.end()) {
            glUseProgram(prog);
        }
        stats_.state_ops++;
        return true;
    }
    // ---- buffers -------------------------------------------------------
    if (method == "glGenBuffers") {
        // F-NEW-503 (CONT-159): POINTER-ARRAY indexing + null guard. P(k)
        // indexes the pointer-only array (marshal_gles20 pushes ONLY object
        // args there — ints go to iargs), so the single-pointer call is
        // P(0); the old P(1) read past the array (bounds-checked → nullptr)
        // and portablegl's glGenBuffers wrote the generated ids through the
        // NULL out-param → SEGV (fault_addr=0x0, tower3d live face: the
        // first libGDX-3D title to reach mesh building). The guard keeps
        // the crash out of the engine when the buffer was not
        // materializable (empty view / unmaterializable elements): the ids
        // stay 0 downstream — the same observable the null marshalling
        // already produced, minus the process death. Write-back of the
        // generated ids to the Java view (F-NEW-463 pattern) is registered
        // as frontier.
        const void* gen_ptr = P(0);
        if (gen_ptr != nullptr) {
            glGenBuffers((GLsizei)I(0), (GLuint*)gen_ptr);
        } else {
            trace = "glGenBuffers: null out-buffer (ids lost, no crash)";
        }
        stats_.buffer_ops++;
        return true;
    }
    if (method == "glBindBuffer") {
        glBindBuffer(I(0), I(1));
        stats_.buffer_ops++;
        return true;
    }
    if (method == "glBufferData") {
        // F-NEW-503: pointer-array indexing (data = the ONLY object arg).
        // A null data is legal GL (uninitialized storage) — no guard needed.
        glBufferData(I(0), (GLsizeiptr)(uintptr_t)I(1), P(0), I(3));
        stats_.buffer_ops++;
        return true;
    }
    if (method == "glVertexAttribPointer") {
        // F-NEW-503: pointer-array indexing + null guard (a null client
        // pointer would crash portablegl's attribute read path).
        if (P(0) != nullptr) {
            glVertexAttribPointer(I(0), (GLint)I(1), I(2), (GLboolean)I(3),
                                  (GLsizei)I(4), P(0));
        } else {
            trace = "glVertexAttribPointer: null client pointer (skipped)";
        }
        stats_.buffer_ops++;
        return true;
    }
    if (method == "glEnableVertexAttribArray") {
        glEnableVertexAttribArray(I(0));
        stats_.state_ops++;
        return true;
    }
    if (method == "glDisableVertexAttribArray") {
        glDisableVertexAttribArray(I(0));
        stats_.state_ops++;
        return true;
    }
    // ---- uniforms -------------------------------------------------------
    if (method == "glGetUniformLocation") {
        // F-NEW-505: stable per-program location minting (the PGL stub
        // returned 0 for EVERY name — all uniforms collapsed to slot 0).
        uint32_t prog = (uint32_t)I(0);
        const char* name = (const char*)P(0);
        auto& loc = gl_locations_[prog];
        std::string key = name ? name : "";
        auto lit = loc.find(key);
        if (lit == loc.end()) {
            int32_t id = (int32_t)loc.size();
            loc.emplace(key, id);
            if (int_ret) *int_ret = id;
        } else {
            if (int_ret) *int_ret = lit->second;
        }
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glGetAttribLocation") {
        // F-NEW-505: same minting law as glGetUniformLocation (shared
        // per-program map; the honest bound — attribute/uniform namespaces
        // collide — is recorded in the registry row).
        uint32_t prog = (uint32_t)I(0);
        const char* name = (const char*)P(0);
        auto& loc = gl_locations_[prog];
        std::string key = name ? name : "";
        auto lit = loc.find(key);
        if (lit == loc.end()) {
            int32_t id = (int32_t)loc.size();
            loc.emplace(key, id);
            if (int_ret) *int_ret = id;
        } else {
            if (int_ret) *int_ret = lit->second;
        }
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glUniformMatrix4fv") {
        // F-NEW-503: pointer-array indexing + null guard (portablegl reads
        // the matrix through the pointer — null would SEGV).
        if (P(0) != nullptr) {
            glUniformMatrix4fv((GLint)I(0), (GLsizei)I(1), (GLboolean)I(2), (const GLfloat*)P(0));
        } else {
            trace = "glUniformMatrix4fv: null matrix pointer (skipped)";
        }
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glUniform4f") {
        glUniform4f((GLint)I(0), fargs[1], fargs[2], fargs[3], fargs[4]);
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glUniform1i") {
        glUniform1i((GLint)I(0), (GLint)I(1));
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glUniform1f") {
        glUniform1f((GLint)I(0), fargs[1]);
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glUniform2f") {
        glUniform2f((GLint)I(0), fargs[1], fargs[2]);
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glUniform3f") {
        glUniform3f((GLint)I(0), fargs[1], fargs[2], fargs[3]);
        stats_.uniform_ops++;
        return true;
    }
    // ---- state ----------------------------------------------------------
    if (method == "glEnable")  { glEnable(I(0));  stats_.state_ops++; return true; }
    if (method == "glDisable") { glDisable(I(0)); stats_.state_ops++; return true; }
    if (method == "glDepthFunc") { glDepthFunc(I(0)); stats_.state_ops++; return true; }
    if (method == "glBlendFunc") { glBlendFunc(I(0), I(1)); stats_.state_ops++; return true; }
    if (method == "glActiveTexture") { glActiveTexture(I(0)); stats_.state_ops++; return true; }
    if (method == "glBindTexture") { glBindTexture(I(0), I(1)); stats_.state_ops++; return true; }
    if (method == "glGenTextures") {
        // F-NEW-503: pointer-array indexing + null guard (same law as
        // glGenBuffers above).
        const void* gen_tex_ptr = P(0);
        if (gen_tex_ptr != nullptr) {
            glGenTextures((GLsizei)I(0), (GLuint*)gen_tex_ptr);
        } else {
            trace = "glGenTextures: null out-buffer (ids lost, no crash)";
        }
        stats_.state_ops++;
        return true;
    }
    if (method == "glViewport") {
        glViewport((GLint)I(0), (GLint)I(1), (GLsizei)I(2), (GLsizei)I(3));
        stats_.state_ops++;
        return true;
    }
    if (method == "glClearColor") {
        // Marshalling law (CONT-83 F-NEW-388): float args occupy slots 1..
        // (slot 0 is the reserved placeholder — see gl_surface_shadow.cpp
        // marshal_gles20).
        glClearColor(fargs[1], fargs[2], fargs[3], fargs[4]);
        stats_.state_ops++;
        return true;
    }
    if (method == "glClear") {
        glClear(I(0));
        stats_.state_ops++;
        return true;
    }
    // ---- draw ------------------------------------------------------------
    if (method == "glDrawArrays") {
        glDrawArrays(I(0), (GLint)I(1), (GLsizei)I(2));
        stats_.draws++;
        return true;
    }
    if (method == "glDrawElements") {
        // F-NEW-503: pointer-array indexing + null guard.
        if (P(0) != nullptr) {
            glDrawElements(I(0), (GLsizei)I(1), I(2), P(0));
        } else {
            trace = "glDrawElements: null index pointer (skipped)";
        }
        stats_.draws++;
        return true;
    }
    return false;
}

}  // namespace gles
}  // namespace miniandroid
