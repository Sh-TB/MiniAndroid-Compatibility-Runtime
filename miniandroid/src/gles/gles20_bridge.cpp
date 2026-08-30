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
        if (int_ret) *int_ret = (int32_t)glCreateShader(I(0));
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
        // Recorded, not executed (see header honesty note).
        stats_.shader_ops++;
        trace += "glsl-not-compiled-by-pgl;";
        return true;
    }
    if (method == "glCreateProgram") {
        if (int_ret) *int_ret = (int32_t)glCreateProgram();
        stats_.shader_ops++;
        return true;
    }
    if (method == "glAttachShader") {
        glAttachShader(I(0), I(1));
        stats_.shader_ops++;
        return true;
    }
    if (method == "glLinkProgram") { stats_.shader_ops++; return true; }
    if (method == "glUseProgram") {
        // If C shaders were registered for this program id, the owning code
        // created the matching PGL program via pglCreateProgram() under the
        // same id (see register_program_shaders).
        uint32_t prog = (uint32_t)I(0);
        auto it = programs_.find(prog);
        (void)it;
        glUseProgram(prog);
        stats_.state_ops++;
        return true;
    }
    // ---- buffers -------------------------------------------------------
    if (method == "glGenBuffers") {
        glGenBuffers((GLsizei)I(0), (GLuint*)P(1));
        stats_.buffer_ops++;
        return true;
    }
    if (method == "glBindBuffer") {
        glBindBuffer(I(0), I(1));
        stats_.buffer_ops++;
        return true;
    }
    if (method == "glBufferData") {
        glBufferData(I(0), (GLsizeiptr)(uintptr_t)I(1), P(2), I(3));
        stats_.buffer_ops++;
        return true;
    }
    if (method == "glVertexAttribPointer") {
        glVertexAttribPointer(I(0), (GLint)I(1), I(2), (GLboolean)I(3),
                              (GLsizei)I(4), P(5));
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
        if (int_ret) *int_ret = (int32_t)glGetUniformLocation(I(0), (const char*)P(1));
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glUniformMatrix4fv") {
        glUniformMatrix4fv((GLint)I(0), (GLsizei)I(1), (GLboolean)I(2), (const GLfloat*)P(3));
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glUniform4f") {
        glUniform4f((GLint)I(0), fargs[1], fargs[2], fargs[3], fargs[4]);
        stats_.uniform_ops++;
        return true;
    }
    // ---- state ----------------------------------------------------------
    if (method == "glEnable")  { glEnable(I(0));  stats_.state_ops++; return true; }
    if (method == "glDisable") { glDisable(I(0)); stats_.state_ops++; return true; }
    if (method == "glDepthFunc") { glDepthFunc(I(0)); stats_.state_ops++; return true; }
    if (method == "glBlendFunc") { glBlendFunc(I(0), I(1)); stats_.state_ops++; return true; }
    if (method == "glViewport") {
        glViewport((GLint)I(0), (GLint)I(1), (GLsizei)I(2), (GLsizei)I(3));
        stats_.state_ops++;
        return true;
    }
    if (method == "glClearColor") {
        glClearColor(fargs[0], fargs[1], fargs[2], fargs[3]);
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
        glDrawElements(I(0), (GLsizei)I(1), I(2), P(3));
        stats_.draws++;
        return true;
    }
    return false;
}

}  // namespace gles
}  // namespace miniandroid
