#!/usr/bin/env python3
"""F-PD-636 (Wave-5, #588): the PD_TEXTURE_QUAD shader family port.

ShatteredPD's glwrap/NoosaScript quad pipeline — the one Wave-5 law
missing from main. Structural classifier entry + family-gated link
(the GP583-GLES-006 law) + the PGL C pair (pd_vert/pd_frag) +
uniform/attrib routing (uCamera/uModel/uColorM/uColorA, aXYZW/aUV).
"""
from pathlib import Path

B = Path("/tmp/w238_int/miniandroid/src/gles/gles20_bridge.cpp")
H = Path("/tmp/w238_int/miniandroid/src/gles/gles20_bridge.h")
PB = Path("/tmp/w238_int/miniandroid/src/gles/pgl_backend.cpp")
PH = Path("/tmp/w238_int/miniandroid/src/gles/pgl_backend.h")

# 1. enum
s = H.read_text()
old = "        BOUNCY_LINE = 3,\n        BOUNCY_CIRCLE = 4,\n    };"
new = ("        BOUNCY_LINE = 3,\n        BOUNCY_CIRCLE = 4,\n"
       "        // ── F-PD-636 (Wave-5, #588; ShatteredPD glwrap/"
       "NoosaScript): the\n        // texture-quad family — attribs "
       "aXYZW (vec4) + aUV (vec2), the two\n        // mat4 uniforms "
       "uCamera (projection) + uModel (per-draw transform),\n"
       "        // and the tint multiply-add fragment (uColorM/uColorA "
       "against the\n        // bound uTex). Classified structurally "
       "(the same declared-interface\n        // law as the four "
       "existing families); executes as the registered C\n"
       "        // pair (pd_vert/pd_frag).\n        PD_TEXTURE_QUAD = 5,\n"
       "    };")
assert old in s, "enum anchor"
H.write_text(s.replace(old, new, 1))

# 2. FamilySig + matcher + useProgram + uniform routing
s = B.read_text()

old = """    int n_attribs;
    bool fragment_sampler;
};"""
new = """    int n_attribs;
    bool fragment_sampler;
    // F-PD-636: family-dependent uniform shapes. The four libGDX families
    // carry exactly one mat4 (n_mat4=1) and zero vec4 fragment uniforms
    // (n_frag_vec4=0) — the defaults preserve their contracts verbatim.
    // The PD glwrap pair carries TWO mat4s (uCamera+uModel) and TWO vec4
    // fragment uniforms (uColorM+uColorA).
    int n_mat4 = 1;
    int n_frag_vec4 = 0;
};"""
assert old in s, "FamilySig anchor"
s = s.replace(old, new, 1)

old = """    return mat4 == 1;
}"""
new = """    return mat4 == sig.n_mat4;
}"""
assert old in s, "vertex matcher anchor"
s = s.replace(old, new, 1)

old = """    int samplers = 0;
    for (const auto& u : f.uniforms) {
        // uniforms are stored (type, name) — the TYPE is first.
        if (u.first == "sampler2D") ++samplers;
        else return false;
    }
    if (samplers != (sig.fragment_sampler ? 1 : 0)) return false;"""
new = """    int samplers = 0, vec4s = 0;
    for (const auto& u : f.uniforms) {
        // uniforms are stored (type, name) — the TYPE is first.
        if (u.first == "sampler2D") ++samplers;
        else if (u.first == "vec4") ++vec4s;  // F-PD-636: uColorM/uColorA
        else return false;
    }
    if (samplers != (sig.fragment_sampler ? 1 : 0)) return false;
    if (vec4s != sig.n_frag_vec4) return false;"""
assert old in s, "fragment matcher anchor"
s = s.replace(old, new, 1)

old = """    {GLES20Bridge::ShaderFamily::BOUNCY_CIRCLE,
     // declaration order in the app asset (the matcher is positional)
     {"position", "inColor", "inRadiusSquared", "inInnerRadiusSquared",
      "inCenter"},
     {0x8B52u, 0x8B52u, 0x8B50u, 0x8B50u, 0x8B52u}, 5, false},
};"""
new = """    {GLES20Bridge::ShaderFamily::BOUNCY_CIRCLE,
     // declaration order in the app asset (the matcher is positional)
     {"position", "inColor", "inRadiusSquared", "inInnerRadiusSquared",
      "inCenter"},
     {0x8B52u, 0x8B52u, 0x8B50u, 0x8B50u, 0x8B52u}, 5, false},
    // ── F-PD-636 (Wave-5, #588; ShatteredPD glwrap/NoosaScript): the
    // texture-quad family. Declared interface only — aXYZW (vec4) +
    // aUV (vec2) attribs, uCamera+uModel mat4s, the sampler + tint
    // vec4s on the fragment side. aXYZW/aUV are glwrap-specific names
    // (NoosaScript), so the structural contract does not collide with
    // the libGDX families.
    {GLES20Bridge::ShaderFamily::PD_TEXTURE_QUAD,
     {"aXYZW", "aUV"},
     {0x8B52u, 0x8B51u}, 2, true, 2, 2},
};"""
assert old in s, "sig table anchor"
s = s.replace(old, new, 1)

old = """            else
                mapped = pgl_spritebatch_program_for(prog);"""
new = """            else if (pit->second.family ==
                     GLES20Bridge::ShaderFamily::PD_TEXTURE_QUAD)
                mapped = pgl_pd_texture_quad_program_for(prog);
            else
                mapped = pgl_spritebatch_program_for(prog);"""
assert old in s, "useProgram mapping anchor"
s = s.replace(old, new, 1)

old = """                trace = "glUseProgram: unsupported-program "
                        "(family unverified; PGL executes C-function shaders "
                        "only; SpriteBatch/ShapeRenderer families supported)";"""
new = """                trace = "glUseProgram: unsupported-program "
                        "(family unverified; PGL executes C-function shaders "
                        "only; SpriteBatch/ShapeRenderer/Bouncy/"
                        "PD_TEXTURE_QUAD families supported)";"""
assert old in s, "trace text anchor"
s = s.replace(old, new, 1)

old = """                } else if (nm && bun_diag_on()) {"""
new = """                }
                // F-PD-636: the PD glwrap pair carries TWO mat4 uniforms —
                // uCamera (the projection) and uModel (the per-draw
                // transform) — both routed to the per-engine-program
                // uniform block (the F-NEW-609b per-program law).
                if (nm && (*nm == "uCamera" || *nm == "uModel"))
                    pgl_pd_set_matrix_for(cur_engine_prog_, nm->c_str(),
                                          (const GLfloat*)P(0),
                                          I(2) != 0);
                else if (nm && bun_diag_on()) {"""
assert old in s, "mat4 routing anchor"
s = s.replace(old, new, 1)

old = """    if (method == "glUniform4f") {
        glUniform4f((GLint)I(0), fargs[1], fargs[2], fargs[3], fargs[4]);
        stats_.uniform_ops++;
        return true;
    }"""
new = """    if (method == "glUniform4f") {
        glUniform4f((GLint)I(0), fargs[1], fargs[2], fargs[3], fargs[4]);
        // F-PD-636: scalar-form tint uniforms — same per-engine-program
        // block law as the array form below.
        if (cur_engine_prog_) {
            const std::string* nm4f =
                sb_uniform_name_for_loc((GLint)I(0));
            if (nm4f && (*nm4f == "uColorM" || *nm4f == "uColorA")) {
                const float v4f[4] = {fargs[1], fargs[2], fargs[3],
                                      fargs[4]};
                pgl_pd_set_color_for(cur_engine_prog_, nm4f->c_str(), v4f);
            }
        }
        stats_.uniform_ops++;
        return true;
    }
    if (method == "glUniform4fv") {
        // F-PD-636: the glwrap tint path — glUniform4fv(uColorM|uColorA,
        // 1, ptr). PGL's glUniform* are app-managed stubs for
        // engine-minted programs, so the PD uniform block is fed here
        // (the F-NEW-609 law shape); other programs pass through to PGL
        // untouched.
        if (cur_engine_prog_) {
            const std::string* nm4 = sb_uniform_name_for_loc((GLint)I(0));
            if (nm4 && (*nm4 == "uColorM" || *nm4 == "uColorA") &&
                P(0) != nullptr)
                pgl_pd_set_color_for(cur_engine_prog_, nm4->c_str(),
                                     (const GLfloat*)P(0));
        } else if (P(0) != nullptr) {
            glUniform4fv((GLint)I(0), (GLsizei)I(1), (const GLfloat*)P(0));
        }
        stats_.uniform_ops++;
        return true;
    }"""
assert old in s, "glUniform4f anchor"
s = s.replace(old, new, 1)

# attrib canonical sites (SB then PD)
n_sb = s.count("int canon = pgl_sb_attrib_location(nm->c_str());")
s = s.replace(
    "int canon = pgl_sb_attrib_location(nm->c_str());",
    "int canon = pgl_sb_attrib_location(nm->c_str());\n"
    "                    if (canon < 0)\n"
    "                        canon = pgl_pd_attrib_location(nm->c_str());")
n_sb2 = s.count("int canon = pgl_sb_attrib_location(nm->c_str());")
n_sb3 = s.count("int canon = pgl_sb_attrib_location(nm2->c_str());")
s = s.replace(
    "int canon2 = nm2 ? pgl_sb_attrib_location(nm2->c_str()) : -1;",
    "int canon2 = nm2 ? pgl_sb_attrib_location(nm2->c_str()) : -1;\n"
    "                    if (nm2 && canon2 < 0)\n"
    "                        canon2 = pgl_pd_attrib_location(nm2->c_str());")
B.write_text(s)

# 3. pgl_backend.cpp — the C pair + setters
s = PB.read_text()
old = """// GP583-GLES-001 (offset clarification): is an ELEMENT_ARRAY_BUFFER bound?"""
new = """// ── F-PD-636 (Wave-5, #588; ShatteredPD glwrap/NoosaScript): the
// PD_TEXTURE_QUAD C pair. Vertex: gl_Position = uCamera * (uModel *
// aXYZW); vUV = aUV passthrough. Fragment: gl_FragColor = texture2D
// (the bound uTex, vUV) * uColorM + uColorA (the glwrap tint
// multiply-add). Canonical attrib slots (the bind law the bridge
// answers): aXYZW=0, aUV=1.
struct PDUniforms {
    float u_camera[16] = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};
    float u_model[16] = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};
    float u_color_m[4] = {1.f, 1.f, 1.f, 1.f};
    float u_color_a[4] = {0.f, 0.f, 0.f, 0.f};
};

void pd_vert(float* vs_output, vec4* vertex_attribs,
             Shader_Builtins* builtins, void* uniforms) {
    PDUniforms* u = (PDUniforms*)uniforms;
    {
        static long pn = 0;
        if (pn++ < 6)
            std::fprintf(stderr,
                "[PD-V] #%ld xyzw=%.1f,%.1f,%.1f uv=%.2f,%.2f "
                "cam00=%g mod00=%g\\n",
                pn, vertex_attribs[0].x, vertex_attribs[0].y,
                vertex_attribs[0].z, vertex_attribs[1].x,
                vertex_attribs[1].y, u->u_camera[0], u->u_model[0]);
    }
    vec4 mid = mult_m4_v4(u->u_model, vertex_attribs[0]);  // aXYZW (0)
    builtins->gl_Position = mult_m4_v4(u->u_camera, mid);
    ((vec2*)vs_output)[0] =
        vec2{vertex_attribs[1].x, vertex_attribs[1].y};    // aUV (1)
}

void pd_frag(float* fs_input, Shader_Builtins* builtins, void* uniforms) {
    PDUniforms* u = (PDUniforms*)uniforms;
    vec2 uv = ((vec2*)fs_input)[0];
    // uTex is sampler unit 0 in the glwrap quad pipeline — sample the
    // CURRENTLY bound GL_TEXTURE_2D (the same object glBindTexture
    // selected; the SpriteBatch sb_frag precedent).
    GLuint tex = c->bound_textures[GL_TEXTURE_2D - GL_TEXTURE_UNBOUND - 1];
    vec4 t = texture2D(tex, uv.x, uv.y);
    vec4 o = {t.x * u->u_color_m[0] + u->u_color_a[0],
              t.y * u->u_color_m[1] + u->u_color_a[1],
              t.z * u->u_color_m[2] + u->u_color_a[2],
              t.w * u->u_color_m[3] + u->u_color_a[3]};
    builtins->gl_FragColor = o;
}

struct PDSlot {
    uint32_t pgl_id = 0;
    uint64_t context_gen = 0;
    PDUniforms uniforms;
};
static std::map<uint32_t, PDSlot> g_pd_map;

static PDSlot* pd_slot_for(uint32_t engine_id) {
    // PGL context guard: c (the global PGL context) is nullptr until a
    // real GL surface exists — creating the slot then would deref c in
    // pglCreateProgram's programs scan (the isolated-bridge-call face
    // the s238 audit battery exposed). Answer 0 honestly; glUseProgram
    // keeps cur_engine_prog_=0 (the same shape as the unsupported
    // program path).
    if (c == nullptr) return nullptr;
    auto it = g_pd_map.find(engine_id);
    if (it != g_pd_map.end()) {
        // Context-generation law (GLES-002): an id minted in a destroyed
        // context is invalid — remint in the current one.
        if (it->second.pgl_id != 0 &&
            it->second.context_gen == g_pgl_context_gen)
            return &it->second;
        it->second.pgl_id = 0;
    }
    PDSlot& s = g_pd_map[engine_id];
    GLenum interp[4] = {PGL_SMOOTH2};  // one varying: vUV (vec2)
    s.pgl_id = pglCreateProgram(pd_vert, pd_frag, 2, interp, GL_FALSE);
    s.context_gen = g_pgl_context_gen;
    if (s.pgl_id) pglSetProgramUniform(s.pgl_id, &s.uniforms);
    return s.pgl_id ? &s : nullptr;
}

uint32_t pgl_pd_texture_quad_program_for(uint32_t engine_id) {
    PDSlot* s = pd_slot_for(engine_id);
    return s ? s->pgl_id : 0;
}

int pgl_pd_attrib_location(const char* name) {
    if (!name) return -1;
    if (std::strcmp(name, "aXYZW") == 0) return 0;
    if (std::strcmp(name, "aUV") == 0) return 1;
    return -1;
}

static void pd_matrix_copy(float* dst, const float* m16, bool transpose) {
    if (!transpose) {
        for (int i = 0; i < 16; ++i) dst[i] = m16[i];
    } else {
        for (int r = 0; r < 4; ++r)
            for (int k = 0; k < 4; ++k)
                dst[r * 4 + k] = m16[k * 4 + r];
    }
}

void pgl_pd_set_matrix_for(uint32_t engine_id, const char* name,
                           const float* m16, bool transpose) {
    if (!name || !m16) return;
    auto it = g_pd_map.find(engine_id);
    if (it == g_pd_map.end()) return;
    if (std::strcmp(name, "uCamera") == 0)
        pd_matrix_copy(it->second.uniforms.u_camera, m16, transpose);
    else if (std::strcmp(name, "uModel") == 0)
        pd_matrix_copy(it->second.uniforms.u_model, m16, transpose);
}

void pgl_pd_set_color_for(uint32_t engine_id, const char* name,
                          const float* v4) {
    if (!name || !v4) return;
    auto it = g_pd_map.find(engine_id);
    if (it == g_pd_map.end()) return;
    float* dst = nullptr;
    if (std::strcmp(name, "uColorM") == 0)
        dst = it->second.uniforms.u_color_m;
    else if (std::strcmp(name, "uColorA") == 0)
        dst = it->second.uniforms.u_color_a;
    if (dst)
        for (int i = 0; i < 4; ++i) dst[i] = v4[i];
}

// GP583-GLES-001 (offset clarification): is an ELEMENT_ARRAY_BUFFER bound?"""
assert old in PB.read_text(), "pgl anchor"
PB.write_text(PB.read_text().replace(old, new, 1))

# 4. pgl_backend.h decls
s = PH.read_text()
old = "uint32_t pgl_bouncy_line_program_for(uint32_t engine_id);"
new = """// ── F-PD-636 (Wave-5, #588): the ShatteredPD texture-quad family —
// per-engine-program PGL mapping + the uniform/attrib routing law.
uint32_t pgl_pd_texture_quad_program_for(uint32_t engine_id);
int pgl_pd_attrib_location(const char* name);
void pgl_pd_set_matrix_for(uint32_t engine_id, const char* name,
                           const float* m16, bool transpose);
void pgl_pd_set_color_for(uint32_t engine_id, const char* name,
                          const float* v4);
uint32_t pgl_bouncy_line_program_for(uint32_t engine_id);"""
assert old in s, "header anchor"
PH.write_text(s.replace(old, new, 1))
print("F-PD-636 ported: enum+sig+matcher+useProgram+mat4/vec4 routing+C pair")
