// CAMPAIGN 010 R9 — GLES20 bridge implementation over PortableGL.
// NOTE: PORTABLEGL_IMPLEMENTATION lives only in pgl_backend.cpp.
#include "gles20_bridge.h"
#include "pgl_backend.h"

#include <portablegl.h>

#include <sstream>
#include <cstring>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <algorithm>

namespace miniandroid {
namespace gles {

// ── GP583-GLES-006: shader-family classification law ───────────────────
// PGL executes C-function shaders; there is no GLSL compiler in this
// runtime. The honest contract (GP583-GLES-006/004): ONLY a positively
// identified, source-verified shader family with a registered functional
// C equivalent may report compile/link success and be mapped at glUseProgram.
// Everything else answers GL_FALSE and records the unsupported boundary.
//
// Supported families (structural signature, not byte-exact — aapt-compiled
// constant concatenation and app-side whitespace differ while the declared
// interface stays identical):
//   SPRITEBATCH   vertex: attributes a_position (vec4) + a_color (vec4) +
//                 a_texCoord0 (vec2), one mat4 projection uniform, gl_Position
//                 assigned from proj * a_position; fragment: one sampler2D
//                 (u_texture), gl_FragColor from the declared varying ×
//                 texture2D.
//   SHAPERENDERER vertex: attributes a_position + a_color, one mat4 uniform,
//                 no sampler; fragment: NO sampler, gl_FragColor = the
//                 declared vec4 varying. (libGDX's real ShapeRenderer
//                 varying is named v_col — the family contract is the
//                 DECLARED varying, not a hardcoded name.)
// Preprocessor lines (#ifdef GL_ES / #define LOWP / precision) are ignored.
namespace {

struct GlslFace {
    bool syntax_ok = false;
    std::string raw;                       // comment-stripped source
    std::vector<std::string> attributes;   // declared attribute names (order)
    std::vector<std::pair<std::string, std::string>> uniforms; // (type, name)
    std::vector<std::string> varyings;     // declared varying names (order)
    bool has_main = false;
    bool assigns_gl_position = false;
    bool assigns_fragcolor = false;
    bool uses_texture2d = false;
};

std::string glsl_strip_comments(const std::string& src) {
    std::string out;
    out.reserve(src.size());
    bool in_line = false, in_block = false;
    for (size_t i = 0; i < src.size(); ++i) {
        if (in_line) {
            if (src[i] == '\n') { in_line = false; out.push_back('\n'); }
            continue;
        }
        if (in_block) {
            if (i + 1 < src.size() && src[i] == '*' && src[i + 1] == '/') {
                in_block = false; ++i;
            }
            continue;
        }
        if (i + 1 < src.size() && src[i] == '/' && src[i + 1] == '/') {
            in_line = true; ++i; continue;
        }
        if (i + 1 < src.size() && src[i] == '/' && src[i + 1] == '*') {
            in_block = true; ++i; continue;
        }
        out.push_back(src[i]);
    }
    return out;
}

// Drop preprocessor LINES entirely: "#endif\nvarying vec4 v_col;" has no
// ';' between the two, so the #endif merged with the following declaration
// and the statement scan lost the varying (the single-varying ShapeRenderer
// fragment face). Preprocessor lines carry nothing the family law reads.
std::string glsl_drop_preprocessor(const std::string& src) {
    std::string out;
    out.reserve(src.size());
    bool at_line_start = true;
    for (size_t i = 0; i < src.size(); ++i) {
        if (at_line_start && src[i] == '#') {
            while (i < src.size() && src[i] != '\n') ++i;
            continue;  // skip the whole directive line (incl. its newline)
        }
        at_line_start = (src[i] == '\n');
        out.push_back(src[i]);
    }
    return out;
}

// Tokenize into identifier/number/symbol words (whitespace-separated model is
// not enough: "uniform mat4\nu_projTrans;" — split on whitespace AND keep
// ';'/braces visible).
void glsl_analyze(const std::string& raw_src, GlslFace& f) {
    std::string src =
        glsl_drop_preprocessor(glsl_strip_comments(raw_src));
    f.raw = src;
    // brace balance + main presence
    int depth = 0, min_depth = 0;
    for (char ch : src) {
        if (ch == '{') ++depth;
        else if (ch == '}') { --depth; if (depth < min_depth) min_depth = depth; }
    }
    f.syntax_ok = (depth == 0 && min_depth == 0);
    if (!f.syntax_ok) return;
    f.has_main = src.find("main") != std::string::npos;
    f.assigns_gl_position = src.find("gl_Position") != std::string::npos &&
                            src.find("gl_Position =") != std::string::npos;
    f.assigns_fragcolor = src.find("gl_FragColor") != std::string::npos &&
                          src.find("gl_FragColor =") != std::string::npos;
    f.uses_texture2d = src.find("texture2D") != std::string::npos;

    // declaration scan: split on ';' and whitespace-normalize each statement
    std::vector<std::string> stmts;
    std::string cur;
    for (char ch : src) {
        if (ch == ';') { stmts.push_back(cur); cur.clear(); }
        else cur.push_back(ch);
    }
    for (auto& st : stmts) {
        // normalize whitespace to single spaces
        std::string w;
        for (char ch : st) w.push_back((ch == '\n' || ch == '\t' || ch == '\r') ? ' ' : ch);
        std::string tok;
        std::vector<std::string> words;
        for (char ch : w) {
            if (ch == ' ') { if (!tok.empty()) words.push_back(tok); tok.clear(); }
            else tok.push_back(ch);
        }
        if (!tok.empty()) words.push_back(tok);
        if (words.size() < 2) continue;
        if (words[0] == "attribute" && words.size() >= 3) {
            f.attributes.push_back(words[2]);
        } else if (words[0] == "uniform" && words.size() >= 3) {
            f.uniforms.emplace_back(words[1], words[2]);
        } else if (words[0] == "varying" && words.size() >= 3) {
            // "varying [LOWP] vec4 name" — the precision qualifier may sit
            // between (e.g. gdx's "varying LOWP vec4 v_color"); the name is
            // the LAST word of the statement.
            f.varyings.push_back(words[words.size() - 1]);
        }
    }
}

// The declared-attribute contract of each supported family (canonical order
// — the same order the pgl_sb_attrib_location bind law and the per-program
// introspection answer).
struct FamilySig {
    GLES20Bridge::ShaderFamily family;
    const char* attribs[4];
    uint32_t types[4];
    int n_attribs;
    bool fragment_sampler;
};
const FamilySig kFamilySigs[] = {
    {GLES20Bridge::ShaderFamily::SPRITEBATCH,
     {"a_position", "a_color", "a_texCoord0"},
     {0x8B52u, 0x8B52u, 0x8B53u}, 3, true},
    {GLES20Bridge::ShaderFamily::SHAPERENDERER,
     {"a_position", "a_color"},
     {0x8B52u, 0x8B52u}, 2, false},
};

// Is this VERTEX source a member of the family? Structural checks only —
// the app-visible contract is the declared interface + the projection
// pipeline, not the exact source text.
bool vertex_matches_family(const GlslFace& f, const FamilySig& sig) {
    if (!f.syntax_ok || !f.has_main || !f.assigns_gl_position) return false;
    if ((int)f.attributes.size() != sig.n_attribs) return false;
    for (int i = 0; i < sig.n_attribs; ++i)
        if (f.attributes[i] != sig.attribs[i]) return false;
    // exactly one mat4 uniform, no sampler in a vertex shader
    // (uniform pairs are (type, name) — the TYPE is first)
    int mat4 = 0;
    for (const auto& u : f.uniforms) {
        if (u.first == "sampler2D") return false;
        if (u.first == "mat4") ++mat4;
        else return false;  // any other uniform type is outside the families
    }
    return mat4 == 1;
}

bool fragment_matches_family(const GlslFace& f, const FamilySig& sig) {
    if (!f.syntax_ok || !f.has_main || !f.assigns_fragcolor) return false;
    if (!f.attributes.empty()) return false;  // no attributes in a fragment shader
    int samplers = 0;
    for (const auto& u : f.uniforms) {
        // uniforms are stored (type, name) — the TYPE is first.
        if (u.first == "sampler2D") ++samplers;
        else return false;
    }
    if (samplers != (sig.fragment_sampler ? 1 : 0)) return false;
    // Family fragments pipe the declared vec4 varying into gl_FragColor —
    // the name is whatever the source declares (gdx SpriteBatch uses
    // v_color, ShapeRenderer uses v_col). A degenerate no-varying fragment
    // ("gl_FragColor = vec4(…)") is NOT a family member.
    if (f.varyings.empty()) return false;
    const std::string& v = f.varyings[0];
    // the declared varying must actually feed gl_FragColor (referenced in
    // the body, not merely declared)
    const bool used = f.raw.find(v) != std::string::npos;
    return (f.uses_texture2d == sig.fragment_sampler) && used;
}

GLES20Bridge::ShaderFamily classify_vertex(const std::string& src) {
    GlslFace f;
    glsl_analyze(src, f);
    for (const auto& sig : kFamilySigs)
        if (vertex_matches_family(f, sig)) return sig.family;
    return GLES20Bridge::ShaderFamily::UNKNOWN;
}

GLES20Bridge::ShaderFamily classify_fragment(const std::string& src) {
    GlslFace f;
    glsl_analyze(src, f);
    for (const auto& sig : kFamilySigs)
        if (fragment_matches_family(f, sig)) return sig.family;
    return GLES20Bridge::ShaderFamily::UNKNOWN;
}

}  // namespace

// S198 draw-time probe storage (env-gated consumers only).
static const void* g_last_attrib_ptr[4] = {nullptr, nullptr, nullptr, nullptr};
static GLint g_last_attrib_size[4] = {0, 0, 0, 0};

// ── GP583-GLES-008: per-program introspection implementation ──────────
bool GLES20Bridge::shader_query(uint32_t shader, uint32_t pname,
                                int32_t* out) const {
    auto it = gl_shaders_.find(shader);
    if (it == gl_shaders_.end()) return false;
    switch (pname) {
        case 0x8B80u: if (out) *out = it->second.deleted ? 1 : 0; return true;   // DELETE_STATUS
        case 0x8B81u: if (out) *out = it->second.compiled ? 1 : 0; return true;  // COMPILE_STATUS
        default: return false;
    }
}

bool GLES20Bridge::program_query(uint32_t program, uint32_t pname,
                                 int32_t* out) const {
    auto it = gl_programs_.find(program);
    if (it == gl_programs_.end()) return false;
    switch (pname) {
        case 0x8B80u: if (out) *out = it->second.deleted ? 1 : 0; return true;   // DELETE_STATUS
        case 0x8B82u: if (out) *out = it->second.linked ? 1 : 0; return true;    // LINK_STATUS
        case 0x8B87u: if (out) *out = (int32_t)it->second.attached.size(); return true;  // ATTACHED_SHADERS
        case 0x8B89u: {  // ACTIVE_ATTRIBUTES — the classified family's count
            if (!it->second.supported) { if (out) *out = 0; return true; }
            for (const auto& sig : kFamilySigs)
                if (sig.family == it->second.family) {
                    if (out) *out = sig.n_attribs;
                    return true;
                }
            if (out) *out = 0;
            return true;
        }
        case 0x8B8Au: {  // ACTIVE_ATTRIBUTE_MAX_LENGTH — real max name len + NUL
            if (!it->second.supported) { if (out) *out = 0; return true; }
            int mx = 0;
            for (const auto& sig : kFamilySigs)
                if (sig.family == it->second.family)
                    for (int i = 0; i < sig.n_attribs; ++i)
                        mx = std::max(mx, (int)std::strlen(sig.attribs[i]) + 1);
            if (out) *out = mx;
            return true;
        }
        default: return false;
    }
}

bool GLES20Bridge::program_attrib(uint32_t program, uint32_t index,
                                  const char** name, uint32_t* gl_type) const {
    auto it = gl_programs_.find(program);
    if (it == gl_programs_.end() || !it->second.supported) return false;
    for (const auto& sig : kFamilySigs) {
        if (sig.family != it->second.family) continue;
        if (index >= (uint32_t)sig.n_attribs) return false;
        if (name) *name = sig.attribs[index];
        if (gl_type) *gl_type = sig.types[index];
        return true;
    }
    return false;
}

bool GLES20Bridge::program_supported(uint32_t program) const {
    auto it = gl_programs_.find(program);
    return it != gl_programs_.end() && it->second.supported;
}

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
        // GP583-GLES-006: family-gated compile-status law. The old behavior
        // set compiled=true UNCONDITIONALLY — an arbitrary GLSL source was
        // reported compiled although no GLSL compilation occurs, then
        // glUseProgram silently substituted the SpriteBatch C pair (the
        // false-success chain GLES-004 documents). The source is classified
        // first: only a positively identified supported family (whose exact
        // functional C pair executes in PGL) answers GL_TRUE; everything
        // else answers GL_FALSE with the honest diagnostic in the trace.
        auto git = gl_shaders_.find((uint32_t)I(0));
        if (git != gl_shaders_.end()) {
            auto sit = shader_sources_.find((uint32_t)I(0));
            const std::string src = sit != shader_sources_.end()
                                        ? sit->second : std::string();
            // glCreateShader stores the PGL-TRANSLATED type slot (S(0) —
            // spec 0x8B31 → pgl 339); pgl_to_spec restores the spec value
            // the family law classifies against. GLES2 law: 0x8B31 =
            // GL_VERTEX_SHADER, 0x8B30 = GL_FRAGMENT_SHADER (there is no
            // 0x8B32 — that value exists in neither GLES2 nor desktop GL2).
            const bool is_vertex =
                pgl_to_spec(git->second.type) == 0x8B31u;  // GL_VERTEX_SHADER
            const auto fam = is_vertex ? classify_vertex(src)
                                       : classify_fragment(src);
            git->second.family = fam;
            git->second.compiled = (fam != ShaderFamily::UNKNOWN) && !src.empty();
            // GP583-GLES-006 diagnostic: dump the classified source + verdict
            // (MINIANDROID_GLSL_DEBUG only) — shows exactly what text the
            // family classifier saw when an app shader misclassifies.
            {
                static const bool glsl_dbg = std::getenv("MINIANDROID_GLSL_DEBUG");
                if (glsl_dbg) {
                    std::fprintf(stderr,
                        "[GLSLDBG] shader=%u type-vertex=%d len=%zu compiled=%d\n"
                        "--- source ---\n%s\n--------------\n",
                        (uint32_t)I(0), is_vertex ? 1 : 0, src.size(),
                        git->second.compiled ? 1 : 0, src.c_str());
                }
            }
            trace += git->second.compiled
                         ? "glsl-family-verified;compile-emulated-by-c-shader"
                         : "glsl-unsupported-source;compile-honest-false";
        } else {
            trace += "glCompileShader: unknown shader handle";
        }
        stats_.shader_ops++;
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
        if (pit != gl_programs_.end()) {
            // GP583-GLES-007: attachment bookkeeping mirrors GL semantics —
            // an already-attached shader is NOT appended twice.
            const uint32_t sh = (uint32_t)I(1);
            auto& att = pit->second.attached;
            if (std::find(att.begin(), att.end(), sh) == att.end())
                att.push_back(sh);
        }
        stats_.shader_ops++;
        return true;
    }
    if (method == "glDetachShader") {
        // GP583-GLES-007: GL object deletion/lifecycle family.
        auto pit = gl_programs_.find((uint32_t)I(0));
        if (pit != gl_programs_.end()) {
            auto& att = pit->second.attached;
            att.erase(std::remove(att.begin(), att.end(), (uint32_t)I(1)),
                      att.end());
        }
        stats_.shader_ops++;
        return true;
    }
    if (method == "glDeleteShader") {
        // GP583-GLES-007: GLES 2.0 deletion semantics — flag the shader as
        // deleted; DELETE_STATUS reflects it. The handle stays retired for
        // reuse (GL names are never recycled). Attachments are legal until
        // the owning programs detach or delete (deferred destruction).
        auto git = gl_shaders_.find((uint32_t)I(0));
        if (git != gl_shaders_.end()) git->second.deleted = true;
        stats_.shader_ops++;
        return true;
    }
    if (method == "glDeleteProgram") {
        // GP583-GLES-007: delete law — flag the program, release the PGL
        // slot (the SpriteBatch mapping storage), clear the minted-location
        // map, and stop tracking it as the current engine program. A still-
        // bound program keeps rendering until the app binds another one
        // (deferred destruction per GL spec).
        const uint32_t prog = (uint32_t)I(0);
        auto pit = gl_programs_.find(prog);
        if (pit != gl_programs_.end()) pit->second.deleted = true;
        pgl_sb_release_program(prog);
        gl_locations_.erase(prog);
        if (cur_engine_prog_ == prog) cur_engine_prog_ = 0;
        stats_.shader_ops++;
        return true;
    }
    if (method == "glIsProgram") {
        auto pit = gl_programs_.find((uint32_t)I(0));
        if (int_ret)
            *int_ret = (pit != gl_programs_.end() && !pit->second.deleted) ? 1 : 0;
        stats_.shader_ops++;
        return true;
    }
    if (method == "glIsShader") {
        auto git = gl_shaders_.find((uint32_t)I(0));
        if (int_ret)
            *int_ret = (git != gl_shaders_.end() && !git->second.deleted) ? 1 : 0;
        stats_.shader_ops++;
        return true;
    }
    if (method == "glLinkProgram") {
        // GP583-GLES-006: family-gated link-status law. linked=true ONLY
        // when the program carries exactly one vertex + one fragment shader,
        // both compiled, and both classify into the SAME supported family.
        // Anything else answers GL_FALSE — use of such a program is the
        // app-visible unsupported boundary, not a silent substitution.
        auto pit = gl_programs_.find((uint32_t)I(0));
        if (pit != gl_programs_.end()) {
            uint32_t nv = 0, nf = 0;
            ShaderFamily fvert = ShaderFamily::UNKNOWN;
            ShaderFamily ffrag = ShaderFamily::UNKNOWN;
            bool all_compiled = true;
            for (uint32_t sh : pit->second.attached) {
                auto git = gl_shaders_.find(sh);
                if (git == gl_shaders_.end()) { all_compiled = false; continue; }
                const uint32_t spec_type = pgl_to_spec(git->second.type);
                if (spec_type == 0x8B31u) {  // GL_VERTEX_SHADER
                    ++nv;
                    fvert = git->second.family;
                } else if (spec_type == 0x8B30u) {  // GL_FRAGMENT_SHADER
                    ++nf;
                    ffrag = git->second.family;
                }
                if (!git->second.compiled) all_compiled = false;
            }
            pit->second.family = fvert;
            pit->second.supported =
                all_compiled && nv == 1 && nf == 1 &&
                fvert != ShaderFamily::UNKNOWN && fvert == ffrag;
            pit->second.linked = pit->second.supported;
            // GP583-GLES-006 diagnostic (MINIANDROID_GLSL_DEBUG): the link
            // gate inputs — shows why a pair was rejected.
            {
                static const bool glsl_dbg2 = std::getenv("MINIANDROID_GLSL_DEBUG");
                if (glsl_dbg2) {
                    std::fprintf(stderr,
                        "[GLSLDBG] link prog=%u nv=%u nf=%u all_compiled=%d "
                        "fvert=%d ffrag=%d supported=%d attached=[%zu]",
                        (uint32_t)I(0), nv, nf, all_compiled ? 1 : 0,
                        (int)fvert, (int)ffrag,
                        pit->second.supported ? 1 : 0,
                        pit->second.attached.size());
                    for (uint32_t sh : pit->second.attached) {
                        auto g2 = gl_shaders_.find(sh);
                        std::fprintf(stderr, " (id=%u found=%d rawtype=%u)",
                                     sh, g2 != gl_shaders_.end() ? 1 : 0,
                                     g2 != gl_shaders_.end() ? g2->second.type
                                                             : 0u);
                    }
                    std::fprintf(stderr, "\n");
                }
            }
            trace += pit->second.linked
                         ? "link-family-verified"
                         : "link-honest-false (unsupported/invalid shader pair)";
        }
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
        // while the mapped program is current.
        //
        // GP583-GLES-004 fix: the mapping is now family-GATED. The old
        // dispatch routed EVERY engine-minted program to the SpriteBatch C
        // pair regardless of its source — a custom shader was reported
        // linked/used but actually ran the fixed SpriteBatch shader
        // (silently semantically-wrong pixels). Only programs whose shader
        // pair classified into a supported family at glLinkProgram (see
        // GLES-006) get the mapping; anything else leaves the current
        // program unchanged and records the explicit unsupported verdict
        // (the GL-law face of using a program that never linked —
        // GL_INVALID_OPERATION — with the current program unchanged).
        uint32_t prog = (uint32_t)I(0);
        auto pit = gl_programs_.find(prog);
        if (pit != gl_programs_.end()) {
            if (!pit->second.supported) {
                trace = "glUseProgram: unsupported-program "
                        "(family unverified; PGL executes C-function shaders "
                        "only; SpriteBatch/ShapeRenderer families supported)";
                cur_engine_prog_ = 0;
                stats_.state_ops++;
                return true;
            }
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
            // S203 F-NEW-626e: bounded vertex-run dump — when
            // MINIANDROID_VBODUMP_PREFIX is set, the first two
            // glDrawArrays calls spill the interleaved SpriteBatch run
            // (count * stride bytes at attrib0) so the quads' pos/color/UV
            // tuples can be reconstructed off-line against the dumped
            // atlas (MINIANDROID_TEXDUMP_PREFIX).
            {
                static const char* vdump_prefix =
                    std::getenv("MINIANDROID_VBODUMP_PREFIX");
                static int vdumped = 0;
                if (vdump_prefix && vdumped < 2 &&
                    g_last_attrib_ptr[0] && (GLint)I(2) > 0) {
                    char vpath[512];
                    std::snprintf(vpath, sizeof(vpath), "%s_%d_count%d.vtx",
                                  vdump_prefix, vdumped, (GLint)I(2));
                    std::FILE* vf = std::fopen(vpath, "wb");
                    if (vf) {
                        // stride: last glVertexAttribPointer stride — the
                        // bridge stores it per index; default 20 is the
                        // SpriteBatch layout (x,y,color,u,v).
                        size_t vsz = (size_t)(GLint)I(2) * 20;
                        std::fwrite(g_last_attrib_ptr[0], 1, vsz, vf);
                        std::fclose(vf);
                        std::fprintf(stderr,
                            "[F-NEW-626e] vertex dump %s\n", vpath);
                    }
                    ++vdumped;
                }
            }
        }
        stats_.draws++;
        return true;
    }
    if (method == "glDrawElements") {
        // F-NEW-503: pointer-array indexing + null guard.
        if (P(0) != nullptr) {
            // GP583-GLES-001 fix (with the offset-clarification follow-up):
            // the old S203 probe was NOT environment-gated, ALWAYS read six
            // indices regardless of the requested count, ALWAYS interpreted
            // them as unsigned short regardless of the supplied GL index
            // type, and dereferenced the indices argument unconditionally —
            // but when an element-array buffer is bound, GLES defines that
            // argument as a BYTE OFFSET into the buffer, not a host pointer
            // (Khronos glDrawElements refpage). A legal one-index draw with
            // a four-byte client buffer, or a bound-EBO draw with offset 4,
            // made the diagnostic read outside the caller's memory.
            // New law: OFF by default (MINIANDROID_GL_DEBUG only), type-
            // validated, count-bounded (never beyond the declared count),
            // and NEVER a pointer dereference — the offset/pointer question
            // is recorded in the trace instead of being dereferenced.
            {
                static const bool gldbg = std::getenv("MINIANDROID_GL_DEBUG");
                static int eshown = 0;
                const GLsizei count = (GLsizei)I(1);
                const GLenum type = S(2);
                if (gldbg && eshown < 8 && count > 0) {
                    ++eshown;
                    // GP583-GLES-001 offset clarification: with a bound
                    // element-array buffer the indices argument is a byte
                    // offset — record it, NEVER dereference it.
                    if (pgl_element_buffer_bound()) {
                        std::fprintf(stderr,
                            "[GLDBG] DELE count=%d type=0x%x ebo-offset=%lu "
                            "(not dereferenced: offset face)\n",
                            (int)count, (unsigned)type,
                            (unsigned long)(uintptr_t)P(0));
                    } else if (type == 0x1401u || type == 0x1403u ||
                               type == 0x1405u) {  // UBYTE / USHORT / UINT
                        // width-validated, count-bounded peek of the
                        // client-pointer face (never beyond the declared
                        // count, never the old fixed six).
                        size_t iw = type == 0x1401u ? 1
                                    : type == 0x1403u ? 2 : 4;
                        const unsigned char* base =
                            (const unsigned char*)P(0);
                        const size_t n = std::min((size_t)count,
                                                  (size_t)6);
                        std::fprintf(stderr,
                            "[GLDBG] DELE count=%d type=0x%x "
                            "i0..%zu=", (int)count, (unsigned)type,
                            n - 1);
                        for (size_t k = 0; k < n; ++k) {
                            unsigned long v = 0;
                            std::memcpy(&v, base + k * iw, iw);
                            std::fprintf(stderr, "%s%lu", k ? "," : "", v);
                        }
                        std::fprintf(stderr, "\n");
                    } else {
                        std::fprintf(stderr,
                            "[GLDBG] DELE count=%d type=0x%x "
                            "(probe skipped: invalid index type)\n",
                            (int)count, (unsigned)type);
                    }
                }
            }
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
                // S203 F-NEW-626e: bounded atlas dump — when
                // MINIANDROID_TEXDUMP_PREFIX is set, the first three
                // uploads spill their RAW RGBA bytes (w*h*4) to
                // <prefix>_<n>.rgba so the atlas content can be
                // reconstructed off-line and compared against the UV
                // layout the SpriteBatch quads sample.
                {
                    static const char* dump_prefix =
                        std::getenv("MINIANDROID_TEXDUMP_PREFIX");
                    static int dumped = 0;
                    if (dump_prefix && dumped < 3 && d && npix > 0 &&
                        npix <= 8388608) {
                        char path[512];
                        std::snprintf(path, sizeof(path), "%s_%d_%ux%u.rgba",
                                      dump_prefix, dumped, (unsigned)I(3),
                                      (unsigned)I(4));
                        std::FILE* df = std::fopen(path, "wb");
                        if (df) {
                            std::fwrite(d, 1, (size_t)npix, df);
                            std::fclose(df);
                            std::fprintf(stderr,
                                "[F-NEW-626e] atlas dump %s\n", path);
                        }
                        ++dumped;
                    }
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
