// CAMPAIGN 010 R9 — PGLBackend implementation.
// Exactly one TU defines PORTABLEGL_IMPLEMENTATION (this file).
// PortableGL: MIT, rswinkle/PortableGL @ 7cf39dc1741e (verified live 2026-08-30).
//
// PGL headless model (per the embedded canonical example in portablegl.h):
// draw with standard gl* calls, then read `backbuf` directly — there is no
// swap step. frame_end() therefore only tracks a frame counter.
#include "pgl_backend.h"

#define PORTABLEGL_IMPLEMENTATION
#include <portablegl.h>

#include <cstring>
#include <map>

// S198 F-NEW-607: GENERATED spec→PGL pairs (scripts/s198_gen_pgl_map.py).
// Numeric only — no PGL macros needed; see the header for the law.
#include "pgl_const_map.inc"

namespace miniandroid {
namespace gles {

static glContext s_ctx;

// ── S198 F-NEW-607 implementations ──────────────────────────────────────
// Lookup is a linear scan over 120 entries — GL call rates here are ≤
// ~1e5/frame, so 1.2e7 compares worst-case is negligible next to software
// rasterization itself. Identity fallback keeps UNKNOWN spec values honest
// (PGL flags INVALID_ENUM; no silent invention).
uint32_t pgl_from_spec(uint32_t spec_val) {
    for (int i = 0; i < kSpecToPglN; ++i)
        if (kSpecToPgl[i].spec == spec_val) return kSpecToPgl[i].pgl;
    return spec_val;
}

uint32_t pgl_mode_from_spec(uint32_t mode) {
    // Spec draw modes 0..6 collide with blend/error constants in spec
    // space, so the general table would mistranslate them. PGL primitive
    // order: POINTS, LINES, LINE_STRIP, LINE_LOOP, TRIANGLES,
    // TRIANGLE_STRIP, TRIANGLE_FAN (portablegl.h primitive-types block —
    // note STRIP/LOOP order vs spec). Translate only the seven legal modes;
    // anything else passes through (PGL INVALID_ENUM — honest).
    static const uint32_t kSpecModes[7] = {0, 1, 2, 3, 4, 5, 6};
    static const uint32_t kPglModes[7] = {
        GL_POINTS, GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP,
        GL_TRIANGLES, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN};
    for (int i = 0; i < 7; ++i)
        if (kSpecModes[i] == mode) return kPglModes[i];
    return mode;
}

uint32_t pgl_mask_from_spec(uint32_t mask) {
    uint32_t out = 0;
    if (mask & 0x4000u) out |= GL_COLOR_BUFFER_BIT;    // spec 1<<14 -> 1<<10
    if (mask & 0x0100u) out |= GL_DEPTH_BUFFER_BIT;    // spec 1<<8  -> 1<<11
    if (mask & 0x0400u) out |= GL_STENCIL_BUFFER_BIT;  // spec 1<<10 -> 1<<12
    // bits outside the three legal spec bits pass through so PGL's
    // INVALID_VALUE check still fires on garbage (no silent masking).
    constexpr uint32_t kLegal = 0x4000u | 0x0100u | 0x0400u;
    out |= (mask & ~kLegal);
    return out;
}

uint32_t pgl_to_spec(uint32_t pgl_val) {
    for (int i = 0; i < kSpecToPglN; ++i)
        if (kSpecToPgl[i].pgl == pgl_val) return kSpecToPgl[i].spec;
    return pgl_val;
}

// ── S198 F-NEW-609: the libGDX SpriteBatch default-shader law ───────────
// libGDX SpriteBatch.createDefaultShader() GLSL (gdx-parent-1.9.10,
// SpriteBatch.java):
//   vertex:   attribute vec4 a_position;      // bind() → location 0
//             attribute vec4 a_color;         // location 1
//             attribute vec2 a_texCoord0;     // location 2
//             uniform mat4 u_projView;
//             v_color = a_color; v_texCoords = a_texCoord0;
//             gl_Position = u_projView * a_position;
//   fragment: uniform sampler2D u_texture;    // always unit 0 (setUniforms)
//             gl_FragColor = v_color * texture2D(u_texture, v_texCoords);
// PGL executes C-function shaders, not GLSL. This C pair is the EXACT
// functional equivalent (the "bouncy app-shaders as C programs" precedent,
// now for the single most-deployed libGDX shader — every SpriteBatch app:
// tictactoe, the gdx game family). Arbitrary APK GLSL stays the honest
// Mesa-llvmpipe frontier (GLES_BACKEND_COMPARISON_010.md).
namespace {

struct SBUniforms { float proj_view[16] = {1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1}; };

// The C shader functions must outlive the program — static storage.
void sb_vert(float* vs_output, vec4* vertex_attribs,
             Shader_Builtins* builtins, void* uniforms) {
    SBUniforms* u = (SBUniforms*)uniforms;
    // S198 probe (bounded): count vertex invocations, dump first clip pos.
    {
        static const bool dbg = std::getenv("MINIANDROID_GL_DEBUG");
        static long n = 0, nz = 0;
        ++n;
        bool nonzero = vertex_attribs[0].x != 0.f || vertex_attribs[0].y != 0.f;
        if (dbg && ((nz == 0 && nonzero) || n <= 2) && nz < 3) {
            if (nonzero) ++nz;
            auto& va = c->vertex_arrays.a[c->cur_vertex_array].vertex_attribs;
            std::fprintf(stderr,
                "[GLDBG] sb_vert #%ld pos=%.2f,%.2f proj00=%g clip=%.4f,%.4f "
                "| PGL attribs: en0=%d sz0=%d off0=%zx en1=%d sz1=%d en2=%d "
                "curVA=%u nprog=%zu\n",
                n, vertex_attribs[0].x, vertex_attribs[0].y,
                u->proj_view[0], builtins->gl_Position.x,
                builtins->gl_Position.y,
                va[0].enabled, va[0].size, (size_t)va[0].offset,
                va[1].enabled, va[1].size, va[2].enabled,
                c->cur_vertex_array, (size_t)c->programs.size);
        }
    }
    // varyings: v_color (4 floats, slot 0) + v_texCoords (2 floats, slot 1)
    ((vec4*)vs_output)[0] = vertex_attribs[1];              // a_color
    vec2 uv = {vertex_attribs[2].x, vertex_attribs[2].y};   // a_texCoord0
    ((vec2*)vs_output)[2] = uv;
    builtins->gl_Position =
        mult_m4_v4(u->proj_view, vertex_attribs[0]);        // a_position
}

void sb_frag(float* fs_input, Shader_Builtins* builtins, void* uniforms) {
    (void)uniforms;
    {
        static const bool dbg = std::getenv("MINIANDROID_GL_DEBUG");
        static long n = 0;
        if (dbg && n < 3) {
            ++n;
            vec4 v_color = ((vec4*)fs_input)[0];
            vec2 uv = ((vec2*)fs_input)[2];
            GLuint tex = c->bound_textures[GL_TEXTURE_2D - GL_TEXTURE_UNBOUND - 1];
            std::fprintf(stderr,
                "[GLDBG] sb_frag #%ld color=%.3f,%.3f,%.3f,%.3f uv=%.3f,%.3f tex=%u\n",
                n, v_color.x, v_color.y, v_color.z, v_color.w, uv.x, uv.y, tex);
        }
    }
    vec4 v_color = ((vec4*)fs_input)[0];
    vec2 uv = ((vec2*)fs_input)[2];
    // u_texture is always sampler unit 0 in the SpriteBatch default shader
    // (SpriteBatch.setUniform(u_texture, 0)); sample the CURRENTLY bound
    // GL_TEXTURE_2D — the same object glBindTexture(GL_TEXTURE_2D, …)
    // selected (PGL bound_textures index = target - GL_TEXTURE_UNBOUND - 1).
    GLuint tex = c->bound_textures[GL_TEXTURE_2D - GL_TEXTURE_UNBOUND - 1];
    builtins->gl_FragColor = mult_v4s(v_color, texture2D(tex, uv.x, uv.y));
}

uint32_t g_sb_program = 0;  // 0 = not created (PGL ids are 1-based)
SBUniforms g_sb_uniforms;   // legacy single uniform block

// GP583-GLES-002/003 fix: the old cache was a FIXED EIGHT-SLOT process-
// static array (kMaxSbPrograms=8) with no release path. Three real defects:
//   (1) PGLBackend::init destroyed and recreated the PGL context on any
//       resize but the slots kept PGL program ids minted in the DEAD
//       context — the cache then returned stale ids that render nothing
//       (GLES-002);
//   (2) after eight distinct engine program ids in one process lifetime
//       every later glCreateProgram could not get a PGL mapping (GLES-003);
//   (3) there was no glDeleteProgram dispatch to retire a slot even when
//       the app correctly disposed its ShaderPrograms (GLES-007).
// New law: a context-OWNED map keyed by engine id. Lifetime = context:
// PGLBackend::init bumps g_pgl_context_gen and clears the map + legacy
// g_sb_program; glDeleteProgram releases its slot explicitly. PGL program
// ids are re-minted in the CURRENT context on demand.
struct SbProgramSlot {
    uint32_t pgl_id = 0;
    uint64_t context_gen = 0;  // PGL context generation this id was minted in
    SBUniforms uniforms;
};
static std::map<uint32_t, SbProgramSlot> g_sb_map;   // engine_id → slot
static uint64_t g_pgl_context_gen = 0;               // bumped by PGLBackend::init

static SbProgramSlot* sb_slot_for(uint32_t engine_id) {
    auto it = g_sb_map.find(engine_id);
    if (it != g_sb_map.end()) {
        // Context-generation law (GLES-002): an id minted in a destroyed
        // context is invalid — remint in the current one.
        if (it->second.pgl_id != 0 &&
            it->second.context_gen == g_pgl_context_gen)
            return &it->second;
        it->second.pgl_id = 0;
    }
    SbProgramSlot& s = g_sb_map[engine_id];
    GLenum interp[6] = {PGL_SMOOTH4, PGL_SMOOTH2};
    s.pgl_id = pglCreateProgram(sb_vert, sb_frag, 6, interp, GL_FALSE);
    s.context_gen = g_pgl_context_gen;
    if (s.pgl_id) pglSetProgramUniform(s.pgl_id, &s.uniforms);
    return s.pgl_id ? &s : nullptr;
}

}  // namespace

// GP583-GLES-007: glDeleteProgram releases the engine program's PGL slot;
// the next use of the same engine id remints a fresh PGL program in the
// current context. (GL semantics: names are never reused — the engine-side
// handle stays retired; only the PGL-side storage is released.)
void pgl_sb_release_program(uint32_t engine_id) {
    g_sb_map.erase(engine_id);
}

// GP583-GLES-002: explicit cache reset — called by PGLBackend::init when
// the PGL context is destroyed/recreated; also usable by tests. Every
// cached PGL id belongs to the dead context and must not survive it.
void pgl_sb_cache_reset() {
    g_sb_map.clear();
    g_sb_program = 0;
}

// GP583-GLES-001 (offset clarification): is an ELEMENT_ARRAY_BUFFER bound?
// When it is, the glDrawElements `indices` argument is a BYTE OFFSET into
// that buffer — never a host pointer. The bridge's (env-gated) diagnostic
// must consult this before touching any address.
bool pgl_element_buffer_bound() {
    return c != nullptr &&
           c->bound_buffers[GL_ELEMENT_ARRAY_BUFFER - GL_ARRAY_BUFFER] != 0;
}

// GP583-GLES-005: the read-framebuffer extent — copies may never allocate
// for more pixels than the framebuffer actually holds.
bool pgl_framebuffer_size(int* w, int* h) {
    // A live PGL context with a real back buffer is the truth (free
    // functions cannot reach PGLBackend's private init state).
    if (c == nullptr || c->back_buffer.w <= 0 || c->back_buffer.h <= 0)
        return false;
    if (w) *w = (int)c->back_buffer.w;
    if (h) *h = (int)c->back_buffer.h;
    return true;
}

uint32_t pgl_spritebatch_program() {
    // Legacy face: returns the first slot's PGL program (the bridge probe
    // prints it). Real use goes through pgl_spritebatch_program_for().
    if (g_sb_program == 0) g_sb_program = pgl_spritebatch_program_for(1);
    return g_sb_program;
}

uint32_t pgl_spritebatch_program_for(uint32_t engine_id) {
    SbProgramSlot* s = sb_slot_for(engine_id ? engine_id : 1);
    return s ? s->pgl_id : 0;
}

void pgl_sb_set_proj_view_for(uint32_t engine_id, const float* m16,
                              bool transpose) {
    // glUniformMatrix4fv(u_projView) — PGL's glUniform* are app-managed
    // stubs; the per-engine-program uniform block is ours. Column-major.
    SbProgramSlot* s = sb_slot_for(engine_id ? engine_id : 1);
    if (!s || !m16) return;
    if (!transpose)
        std::memcpy(s->uniforms.proj_view, m16, sizeof(float) * 16);
    else
        for (int r = 0; r < 4; ++r)
            for (int k = 0; k < 4; ++k)
                s->uniforms.proj_view[r * 4 + k] = m16[k * 4 + r];
}

void pgl_debug_attrib_dump(const char* tag) {
    // S198 corruption probe: hex-dump vertex_attribs[0..3] (env-gated).
    static const bool dbg = std::getenv("MINIANDROID_GL_DEBUG");
    if (!dbg) return;
    auto& va = c->vertex_arrays.a[c->cur_vertex_array].vertex_attribs;
    for (int i = 0; i < 4; ++i) {
        const unsigned char* p = (const unsigned char*)&va[i];
        char hx[97];  // 32 bytes * 3
        for (int b = 0; b < 32; ++b)
            std::snprintf(hx + b * 3, 4, "%02x ", p[b]);
        std::fprintf(stderr, "[GLDBG] va[%d] @%s: %s\n", i, tag, hx);
    }
}

void pgl_sb_set_proj_view(const float* m16, bool transpose) {
    // Legacy face (single block) — the bridge calls the _for(engine) form.
    pgl_sb_set_proj_view_for(0, m16, transpose);
}

int pgl_sb_uniform_location(const char* name) {
    // Name law (SpriteBatch.createDefaultShader + setUniforms; ShapeRenderer
    // default shaders use u_projModelView, SpriteBatch uses u_projTrans —
    // the single mat4 slot serves all of them). Unknown names answer -1
    // honestly.
    if (!name) return -1;
    if (std::strcmp(name, "u_projView") == 0 ||
        std::strcmp(name, "u_projTrans") == 0 ||
        std::strcmp(name, "u_projModelView") == 0) return 0;
    if (std::strcmp(name, "u_texture") == 0) return 1;
    return -1;
}

int pgl_sb_attrib_location(const char* name) {
    // bind() law: a_position 0, a_color 1, a_texCoord0 2 (the indices the
    // C shaders read). Unknown → -1.
    if (!name) return -1;
    if (std::strcmp(name, "a_position") == 0) return 0;
    if (std::strcmp(name, "a_color") == 0) return 1;
    if (std::strcmp(name, "a_texCoord0") == 0) return 2;
    return -1;
}

PGLBackend& PGLBackend::instance() {
    static PGLBackend b;
    return b;
}

bool PGLBackend::make_current() {
    // init_glContext binds the global PGL context pointer (c = context);
    // re-bind defensively so gl* calls always land on OUR context.
    if (!inited_) return false;
    c = &s_ctx;
    return true;
}

bool PGLBackend::init(int width, int height, std::string& error) {
    if (inited_ && width == width_ && height == height_) return true;
    // Re-init at new size: PGL owns its buffers; a fresh context is the
    // supported path (init_glContext allocates the back buffer).
    if (inited_) {
        free_glContext(&s_ctx);
        // GP583-GLES-002: the old context is gone — every PGL object id
        // minted in it (SpriteBatch cache included) is invalid. Bump the
        // generation and drop the cache so stale ids can never be bound.
        ++g_pgl_context_gen;
        pgl_sb_cache_reset();
    }
    std::memset(&s_ctx, 0, sizeof(s_ctx));
    if (!init_glContext(&s_ctx, &backbuf_, width, height)) {
        error = "init_glContext failed (out of memory?)";
        inited_ = false;
        return false;
    }
    width_ = width;
    height_ = height;
    ctx_ = &s_ctx;
    inited_ = true;
    return true;
}

void PGLBackend::frame_end() {
    if (!inited_) return;
    // Headless PGL renders straight into backbuf_; nothing to swap.
}

const char* pgl_version_string() {
    return "PortableGL rswinkle@7cf39dc (MIT)";
}

}  // namespace gles
}  // namespace miniandroid
