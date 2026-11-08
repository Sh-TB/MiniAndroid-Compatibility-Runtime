// CAMPAIGN 010 R9 — GLES20 bridge implementation over PortableGL.
// NOTE: PORTABLEGL_IMPLEMENTATION lives only in pgl_backend.cpp.
#include "gles20_bridge.h"
#include "pgl_backend.h"

#include <portablegl.h>

#include <sstream>
#include <cstring>
#include <cstdarg>
#include <cstdio>

namespace miniandroid {
namespace gles {

// S198 draw-time probe storage (env-gated consumers only).
static const void* g_last_attrib_ptr[4] = {nullptr, nullptr, nullptr, nullptr};
static GLint g_last_attrib_size[4] = {0, 0, 0, 0};

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
    // S198 F-NEW-607: spec→PGL translation (see pgl_backend.h). The S
    // ("spec") form translates the slot; raw I(k) stays for handles/ints.
    auto S = [&](int k) -> GLenum { return pgl_from_spec(I(k)); };
    auto P = [&](int k) -> const void* { return k < np ? pargs[k] : nullptr; };

    if (method == "glGetError") {
        // F-NEW-607: PGL error codes are internal (1,2,3,5) — apps compare
        // against the GL-spec values (0x500/0x501/0x502/0x505). Reverse-
        // translate so the app-side error check is honest.
        if (int_ret) *int_ret = (int32_t)pgl_to_spec((uint32_t)glGetError());
        stats_.state_ops++;
        return true;
    }
    // ---- shader/program lifecycle -------------------------------------
    if (method == "glCreateShader") {
        // F-NEW-505 (CONT-159): engine-side handle. The PGL port stubs this
        // (returns 0) — a 0 shader made ShaderProgram.loadShader skip the
        // compile (tower3d SpriteBatch death chain, see the header law).
        uint32_t sh = gl_next_shader_++;
        gl_shaders_[sh].type = S(0);  // F-NEW-607: spec shader type
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
        // reach PGL with the raw engine id — its program namespace only
        // contains pglCreateProgram ids.
        // F-NEW-609 (S198): an engine-minted program IS executable through
        // the SpriteBatch default C-shader pair (the exact functional
        // equivalent of the libGDX default SpriteBatch GLSL — the dominant
        // shader of every libGDX app). Map engine id → PGL program and bind
        // THAT; uniform/attrib location queries answer through the name law
        // while the mapped program is current. Arbitrary GLSL stays the
        // honest Mesa-llvmpipe frontier.
        uint32_t prog = (uint32_t)I(0);
        if (gl_programs_.find(prog) != gl_programs_.end()) {
            // F-NEW-609 (S198): engine-minted GLSL program → the SpriteBatch
            // default C-shader pair (the exact functional equivalent of the
            // libGDX default SpriteBatch GLSL — the dominant shader of every
            // SpriteBatch app). Uniform/attrib data flows through the name
            // law in the glUniform* handlers below; the minted-location
            // law (F-NEW-505) stays authoritative for ids.
            // F-NEW-609b: PER-ENGINE-PROGRAM PGL program + uniform block
            // (SpriteBatch's u_projTrans and ShapeRenderer's u_projModelView
            // must not share one matrix).
            uint32_t sb = pgl_spritebatch_program_for(prog);
            cur_engine_prog_ = sb ? prog : 0;
            if (sb) glUseProgram(sb);
        } else {
            cur_engine_prog_ = 0;
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
        glBindBuffer(S(0), I(1));  // F-NEW-607
        stats_.buffer_ops++;
        return true;
    }
    if (method == "glBufferData") {
        // F-NEW-503: pointer-array indexing (data = the ONLY object arg).
        // A null data is legal GL (uninitialized storage) — no guard needed.
        glBufferData(S(0), (GLsizeiptr)(uintptr_t)I(1), P(0), S(3));  // F-NEW-607: target+usage
        stats_.buffer_ops++;
        return true;
    }
    if (method == "glVertexAttribPointer") {
        // F-NEW-503: pointer-array indexing + null guard (a null client
        // pointer would crash portablegl's attribute read path).
        // F-NEW-623 (S200 Target-B): the VBO OFFSET form — when the pointer
        // array is EMPTY and the int args carry the 6-arg (loc,size,type,
        // norm,stride,offset) shape, the last int IS the byte offset into
        // the bound GL_ARRAY_BUFFER. Offset 0 must NOT be skipped as a
        // null client pointer (the position attribute rides offset 0).
        const void* vap_ptr = P(0);
        // F-NEW-623: the 6-int shape IS the VBO offset form — the offset
        // is the pointer value EVEN WHEN IT IS 0 (the position attribute
        // rides offset 0; treating 0 as "no pointer" skipped every bind).
        const bool vbo_offset_form = (vap_ptr == nullptr && ni >= 6);
        if (vbo_offset_form)
            vap_ptr = (const void*)(uintptr_t)I(5);
        if (vap_ptr != nullptr || vbo_offset_form) {
            unsigned idx = (unsigned)I(0);
            if (cur_engine_prog_) {
                if (const std::string* nm = sb_uniform_name_for_loc((GLint)idx)) {
                    int canon = pgl_sb_attrib_location(nm->c_str());
                    if (canon >= 0) idx = (unsigned)canon;
                }
            }
            // S200 Target-B probe (bounded): raw minted idx → canonical at
            // the vap boundary.
            {
                static const bool dbg = std::getenv("MINIANDROID_GL_DEBUG");
                static int shown = 0;
                if (dbg && shown < 24) {
                    ++shown;
                    const std::string* nm2 = cur_engine_prog_
                        ? sb_uniform_name_for_loc((GLint)I(0)) : nullptr;
                    int canon2 = nm2 ? pgl_sb_attrib_location(nm2->c_str()) : -1;
                    std::fprintf(stderr,
                        "[GLDBG] vap RAW idx=%u prog=%u name=%s canon=%d "
                        "final=%u\n",
                        (unsigned)I(0), (unsigned)(uintptr_t)cur_engine_prog_,
                        nm2 ? nm2->c_str() : "(none)", canon2, idx);
                }
            }
            glVertexAttribPointer(idx, (GLint)I(1), S(2), (GLboolean)I(3),
                                  (GLsizei)I(4), vap_ptr);  // F-NEW-607: type
            // S198: remember the last pointer per canonical index (the
            // draw-time probe reads it).
            if (idx < 4) {
                g_last_attrib_ptr[idx] = vap_ptr;
                g_last_attrib_size[idx] = (GLint)I(1);
            }
            // S198 debug probe (env-gated, bounded): first attrib records.
            {
                static const bool dbg = std::getenv("MINIANDROID_GL_DEBUG");
                static int shown = 0;
                if (dbg && shown < 6) {
                    ++shown;
                    const float* f = (const float*)P(0);
                    std::fprintf(stderr,
                        "[GLDBG] attrib idx=%u size=%d type=0x%X stride=%d "
                        "ptr=%p v0=%.3f,%.3f,%.3f,%.3f\n",
                        idx, (GLint)I(1), (unsigned)S(2),
                        (GLsizei)I(4), P(0), f[0], f[1],
                        (GLint)I(1) > 2 ? f[2] : 0.f,
                        (GLint)I(1) > 3 ? f[3] : 0.f);
                }
            }
        } else {
            trace = "glVertexAttribPointer: null client pointer (skipped)";
        }
        stats_.buffer_ops++;
        return true;
    }
    if (method == "glEnableVertexAttribArray") {
        // F-NEW-609: same minted-id → canonical-index law.
        unsigned idx = (unsigned)I(0);
        if (cur_engine_prog_) {
            if (const std::string* nm = sb_uniform_name_for_loc((GLint)idx)) {
                int canon = pgl_sb_attrib_location(nm->c_str());
                if (canon >= 0) idx = (unsigned)canon;
            }
        }
        glEnableVertexAttribArray(idx);
        stats_.state_ops++;
        return true;
    }
    if (method == "glDisableVertexAttribArray") {
        unsigned idx = (unsigned)I(0);
        if (cur_engine_prog_) {
            if (const std::string* nm = sb_uniform_name_for_loc((GLint)idx)) {
                int canon = pgl_sb_attrib_location(nm->c_str());
                if (canon >= 0) idx = (unsigned)canon;
            }
        }
        glDisableVertexAttribArray(idx);
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
        // S200 Target-B probe (bounded): the mint answer per name.
        {
            static const bool dbg = std::getenv("MINIANDROID_GL_DEBUG");
            static int shown = 0;
            if (dbg && shown < 40) {
                ++shown;
                std::fprintf(stderr,
                    "[GLDBG] attrib-loc prog=%u name=%s -> %d\n",
                    prog, key.c_str(), int_ret ? *int_ret : -99);
            }
        }
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glUniformMatrix4fv") {
        // F-NEW-503: pointer-array indexing + null guard (portablegl reads
        // the matrix through the pointer — null would SEGV).
        if (P(0) != nullptr) {
            if (cur_engine_prog_) {
                // F-NEW-609: route the minted location back to its NAME and
                // feed the SpriteBatch uniform block (PGL's glUniform* are
                // app-managed stubs).
                const std::string* nm = sb_uniform_name_for_loc((GLint)I(0));
                {
                    static const bool dbg1 = std::getenv("MINIANDROID_GL_DEBUG");
                    static int shown1 = 0;
                    if (dbg1 && shown1 < 4) {
                        ++shown1;
                        const float* f = (const float*)P(0);
                        std::fprintf(stderr,
                            "[GLDBG] mat4 loc=%d engine=%u name=%s t=%u "
                            "m00=%g m30=%g m31=%g m32=%g m33=%g\n",
                            (GLint)I(0), cur_engine_prog_,
                            nm ? nm->c_str() : "<unminted>", (unsigned)I(2),
                            f[0], f[12], f[13], f[14], f[15]);
                    }
                }
                if (nm && (*nm == "u_projView" || *nm == "u_projTrans" ||
                           *nm == "u_projModelView"))
                    pgl_sb_set_proj_view_for(cur_engine_prog_,
                                             (const GLfloat*)P(0), I(2) != 0);
                // other matrix uniforms: the SB default shader has none —
                // handled no-op (honest: no invented storage)
            } else {
                glUniformMatrix4fv((GLint)I(0), (GLsizei)I(1), (GLboolean)I(2), (const GLfloat*)P(0));
            }
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
        // F-NEW-609: u_texture sampler on the SB program — the C shader
        // samples the currently bound GL_TEXTURE_2D (SpriteBatch binds
        // unit 0); the intent is recorded, no storage needed. PGL's
        // glUniform1i is a stub either way.
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
    // ---- state (F-NEW-607: every GLenum slot translated) ----------------
    if (method == "glEnable")  { glEnable(S(0));  stats_.state_ops++; return true; }
    if (method == "glDisable") { glDisable(S(0)); stats_.state_ops++; return true; }
    if (method == "glDepthFunc") { glDepthFunc(S(0)); stats_.state_ops++; return true; }
    if (method == "glBlendFunc") { glBlendFunc(S(0), S(1)); stats_.state_ops++; return true; }
    if (method == "glActiveTexture") { glActiveTexture(S(0)); stats_.state_ops++; return true; }
    if (method == "glBindTexture") { glBindTexture(S(0), I(1)); stats_.state_ops++; return true; }
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
        glClear(pgl_mask_from_spec(I(0)));  // F-NEW-607: spec bits 1<<14/8/10
        stats_.state_ops++;
        return true;
    }
    // ---- draw ------------------------------------------------------------
    if (method == "glDrawArrays") {
        glDrawArrays(pgl_mode_from_spec(I(0)), (GLint)I(1), (GLsizei)I(2));  // F-NEW-607
        {
            static const bool dbg = std::getenv("MINIANDROID_GL_DEBUG");
            static int shown = 0;
            if (dbg && shown < 12) {
                ++shown;
                const float* p = (const float*)g_last_attrib_ptr[0];
                const float* t = (const float*)g_last_attrib_ptr[2];
                std::fprintf(stderr,
                    "[GLDBG] DRAW mode=%u count=%d attrib0=%p %.2f,%.2f attrib2=%p %.3f,%.3f\n",
                    (unsigned)I(0), (GLint)I(2), g_last_attrib_ptr[0],
                    p ? p[0] : -1, p ? p[1] : -1,
                    g_last_attrib_ptr[2], t ? t[0] : -1, t ? t[1] : -1);
            }
        }
        stats_.draws++;
        return true;
    }
    if (method == "glDrawElements") {
        // F-NEW-503: pointer-array indexing + null guard.
        if (P(0) != nullptr) {
            glDrawElements(pgl_mode_from_spec(I(0)), (GLsizei)I(1), S(2), P(0));  // F-NEW-607: mode+type
        } else {
            trace = "glDrawElements: null index pointer (skipped)";
        }
        stats_.draws++;
        return true;
    }
    // ── F-NEW-608 (S198): the census-driven bridge completion set ────────
    // The S198 tictactoe GFX probe (1108 gl.call rows) named the remaining
    // honest REC-MISS ops blocking the first real raster: glTexImage2D +
    // glTexParameteri (textures never uploaded/filtered), glBlendFuncSeparate
    // + glDepthMask (SpriteBatch state), glPixelStorei. Plus the standard
    // state family around them (AOSP GLES20.java surface) so the next app
    // does not re-trip on the same class. Every GLenum slot translated per
    // F-NEW-607; booleans/ints/floats stay raw.
    if (method == "glTexImage2D") {
        // (target, level, internalformat, w, h, border, format, type, pixels)
        // pixels = the marshalled pointer (F-NEW-608 direct-buffer fallback
        // or array hold); null is legal GL (uninitialized storage).
        glTexImage2D(S(0), (GLint)I(1), S(2), (GLsizei)I(3), (GLsizei)I(4),
                     (GLint)I(5), S(6), S(7), P(0));
        {
            static const bool dbg = std::getenv("MINIANDROID_GL_DEBUG");
            static int shown = 0;
            if (dbg && shown < 6) {
                ++shown;
                const unsigned char* d = (const unsigned char*)P(0);
                unsigned long sum = 0; int nonzero = 0;
                long npix = (long)I(3) * (long)I(4) * 4;
                if (d)
                    for (long k = 0; k < npix && k < 8388608; ++k) {
                        sum += d[k];
                        if (d[k]) ++nonzero;
                    }
                std::fprintf(stderr,
                    "[GLDBG] tex2D %ux%u fmt=0x%X type=0x%X ptr=%p "
                    "bytesum=%lu nonzero=%ld/%ld b0=%02x b1=%02x\n",
                    (unsigned)I(3), (unsigned)I(4), (unsigned)S(6),
                    (unsigned)S(7), P(0), sum, nonzero,
                    npix < 8388608 ? npix : -1L, d ? d[0] : 0, d ? d[1] : 0);
            }
        }
        stats_.tex_ops++;
        return true;
    }
    if (method == "glTexParameteri") {
        glTexParameteri(S(0), S(1), S(2));
        stats_.tex_ops++;
        return true;
    }
    if (method == "glBlendFuncSeparate") {
        glBlendFuncSeparate(S(0), S(1), S(2), S(3));
        stats_.state_ops++;
        return true;
    }
    if (method == "glDepthMask") {
        glDepthMask((GLboolean)I(0));
        stats_.state_ops++;
        return true;
    }
    if (method == "glPixelStorei") {
        glPixelStorei(S(0), (GLint)I(1));
        stats_.state_ops++;
        return true;
    }
    if (method == "glCullFace")  { glCullFace(S(0));  stats_.state_ops++; return true; }
    if (method == "glFrontFace") { glFrontFace(S(0)); stats_.state_ops++; return true; }
    if (method == "glBlendEquation") { glBlendEquation(S(0)); stats_.state_ops++; return true; }
    if (method == "glBlendEquationSeparate") {
        glBlendEquationSeparate(S(0), S(1));
        stats_.state_ops++;
        return true;
    }
    if (method == "glBlendColor") {
        glBlendColor(fargs[1], fargs[2], fargs[3], fargs[4]);
        stats_.state_ops++;
        return true;
    }
    if (method == "glDepthRangef" || method == "glClearDepthf") {
        glDepthRangef(fargs[1], fargs[2]);
        stats_.state_ops++;
        return true;
    }
    if (method == "glLineWidth") { glLineWidth(fargs[1]); stats_.state_ops++; return true; }
    if (method == "glGenerateMipmap") { glGenerateMipmap(S(0)); stats_.tex_ops++; return true; }
    // glHint / glBindAttribLocation: PGL 0.101 has no such symbols — left
    // as honest REC-MISS rows (glHint cannot affect raster correctness;
    // attrib binding is name->index only, and libGDX binds by location).
    if (method == "glStencilFunc") {
        glStencilFunc(S(0), (GLint)I(1), (GLuint)I(2));
        stats_.state_ops++;
        return true;
    }
    if (method == "glStencilOp") {
        glStencilOp(S(0), S(1), S(2));
        stats_.state_ops++;
        return true;
    }
    if (method == "glStencilFuncSeparate") {
        glStencilFuncSeparate(S(0), S(1), (GLint)I(2), (GLuint)I(3));
        stats_.state_ops++;
        return true;
    }
    if (method == "glStencilOpSeparate") {
        glStencilOpSeparate(S(0), S(1), S(2), S(3));
        stats_.state_ops++;
        return true;
    }
    if (method == "glFinish" || method == "glFlush" ||
        method == "glReleaseShaderCompiler") {
        stats_.state_ops++;
        return true;
    }
    return false;
}

}  // namespace gles
}  // namespace miniandroid
