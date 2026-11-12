// gl_surface_shadow.cpp — S83-GFX-BASE §24/§25 implementation.
#include "gl_surface_shadow.h"
#include "gles/pgl_backend.h"
#include "gles/gles20_bridge.h"
#include "diagnostics/gfx_trace.h"
#include "jni/dlopen_exec.h"  // F-NEW-608 (S198, C3): lookup_direct_buffer

#include <portablegl.h>

#include <cmath>
#include <cstring>
#include <iostream>
#include <vector>

namespace miniandroid { namespace framework {

// ── CONT-83 F-NEW-388: GLES20 static dispatch adapter ───────────────────
// android.opengl.GLES20 statics previously fell through every shadow and
// answered REC-MISS (each call returned null/void; GLES20Bridge existed
// but was never wired). The adapter marshals one CallContext into the
// bridge (real PortableGL calls) under a bounded, honest law:
//   INT/LONG/BOOL → integer slot; FLOAT/DOUBLE → float slot; STRING →
//   pointer slot (NUL-terminated). OBJECT: engine heap arrays ("[F"/"[I"/
//   "[S"/"[B"/"[C" descriptors with "array[i]" fields) materialize up to
//   kMaxArrayElems; java.nio Buffer objects are chased ONE ref-field level
//   to a heap array (generic field-names probe, R-NEW-360 idiom — no
//   name-based class table); NULL_REF → null pointer. Anything else: an
//   honest marshal-fail trace row + REC-MISS — never an invented pointer.
namespace {

constexpr size_t kMaxArrayElems = 65536;

struct GlMarshal {
    std::vector<uint64_t> ia;
    std::vector<float> fa;
    std::vector<const void*> pa;
    std::vector<std::vector<uint8_t>> hold;   // materialized byte buffers
    std::vector<std::string> strs;
    bool ok = true;
    std::string why;
};

bool read_array_elems(HeapAllocator* heap, uint32_t arr_id,
                      const std::string& elem_desc, size_t count,
                      std::vector<uint8_t>& out) {
    auto read_i = [&](size_t i, int32_t& v) {
        return heap->get_object_int_field(
            arr_id, "array[" + std::to_string(i) + "]", v);
    };
    if (elem_desc == "[F") {
        out.resize(count * 4);
        for (size_t i = 0; i < count; ++i) {
            float f = 0.f;
            // ── S199 W19a F-NEW-618 — [F RAW-BITS ELEMENT LAW (F-028) ───
            // A [F element may sit as FLOAT32 (DEX aput-float) or as
            // INT32 RAW BITS (engine internals — the W18 primitive-array
            // commit keeps per-element storage conventions). The
            // field-level getter NUMERICALLY casts INT32 (for RectF-style
            // mixed shadows that is right); a TYPED ARRAY element must
            // BIT-REINTERPRET (Matrix4.val[15] = 1.0f → int32 0x3F800000
            // → numeric cast answered 1.06535e+09 → u_projTrans m33
            // corrupt → every vertex clipped → the all-white frame).
            // get_object_array_float_element implements exactly this.
            if (!heap->get_object_array_float_element(
                    arr_id, i, f))
                return false;
            std::memcpy(out.data() + i * 4, &f, 4);
        }
        return true;
    }
    if (elem_desc == "[I") {
        out.resize(count * 4);
        for (size_t i = 0; i < count; ++i) {
            int32_t v;
            if (!read_i(i, v)) return false;
            std::memcpy(out.data() + i * 4, &v, 4);
        }
        return true;
    }
    if (elem_desc == "[S") {
        out.resize(count * 2);
        for (size_t i = 0; i < count; ++i) {
            int32_t v;
            if (!read_i(i, v)) return false;
            std::memcpy(out.data() + i * 2, &v, 2);
        }
        return true;
    }
    if (elem_desc == "[B" || elem_desc == "[C") {
        out.resize(count);
        for (size_t i = 0; i < count; ++i) {
            int32_t v;
            if (!read_i(i, v)) return false;
            out[i] = (uint8_t)v;
        }
        return true;
    }
    return false;   // [J / object arrays: honest frontier, not invented
}

bool chase_buffer(HeapAllocator* heap, uint32_t obj_id, uint32_t& arr_out,
                  std::string& elem_desc) {
    std::string cls;
    if (!heap->get_object_class(obj_id, cls) || cls.empty()) return false;
    if (cls[0] == '[') { arr_out = obj_id; elem_desc = cls; return true; }
    // java.nio Buffer: one ref-field level to a heap array (generic probe).
    for (const auto& fn : heap->get_object_field_names(obj_id)) {
        uint32_t ref = 0;
        if (heap->get_object_ref_field(obj_id, fn, ref) && ref != 0) {
            std::string rcls;
            if (heap->get_object_class(ref, rcls) && !rcls.empty() &&
                rcls[0] == '[') {
                arr_out = ref;
                elem_desc = rcls;
                return true;
            }
        }
    }
    return false;
}

// ── S199 W19a F-NEW-616c — GL OUT-PARAM PARENT-MIRROR write-back ────────
// The one-identity law has TWO writer surfaces: the engine (typed put /
// copyJni) writes the parent direct memory AND the view field run; the GL
// out-param laws (glGetShaderiv F-NEW-503b, glGetIntegerv, gen* F-NEW-506)
// wrote ONLY the view field run. With the engine get reading the parent
// memory first (F-NEW-616b), a field-only write was shadowed by the zeroed
// parent memory — live face: ShaderProgram.isCompiled() read COMPILE_STATUS
// 0 from the parent calloc memory → createDefaultShader IAE → onCreate APP
// BOUNDARY (nondeterministic vs runs where the shader path raced differently).
// Law: EVERY GL out-param write lands in BOTH surfaces (field run AND the
// parent's real direct memory, little-endian by element width).
int gl_view_mirror_write(HeapAllocator* heap, uint32_t holder, int32_t elem_idx,
                         int32_t val) {
    if (!heap || holder == 0) return 0;
    int esz = 4;
    std::string hcls;
    if (heap->get_object_class(holder, hcls)) {
        if (hcls.find("ShortBuffer;") != std::string::npos ||
            hcls.find("CharBuffer;") != std::string::npos) esz = 2;
        else if (hcls.find("LongBuffer;") != std::string::npos ||
                 hcls.find("DoubleBuffer;") != std::string::npos) esz = 8;
        else if (hcls.find("ByteBuffer;") != std::string::npos) esz = 1;
    }
    // GP S225 NATIVE-001 (issue #582): the out-param write-back is a GUEST-
    // CONTROLLED write into real native memory. AOSP NIO law: a write at
    // element index i of a buffer with capacity C is in range iff
    // 0 <= i and (i+1)*esz <= C — one byte past the capacity, a negative
    // index, or an overflowing base offset must NEVER write. The old form
    // rejected none of these (negative elem_idx, int32 base overflow, and
    // dcap==0 treated as write permission).
    if (elem_idx < 0) return 0;              // negative index: no write
    int64_t base64 = (int64_t)elem_idx * (int64_t)esz;  // no int32 overflow
    uint32_t par = 0;
    if (!heap->get_object_ref_field(holder, "__bb_parent__", par) || par == 0)
        return esz;
    int64_t addr = 0;
    if (!heap->get_object_long_field(par, "__bb_direct__", addr) || addr == 0)
        return esz;
    int32_t dcap = 0;
    heap->get_object_int_field(par, "__bb_direct_cap__", dcap);
    // Unknown/zero capacity: the backing allocation identity is unproven —
    // do not write (was: dcap==0 fell through as permission).
    if (dcap <= 0) return esz;
    if (base64 < 0 || base64 + esz > (int64_t)dcap) return esz;  // tail check
    unsigned char* mem = reinterpret_cast<unsigned char*>((uintptr_t)addr);
    int32_t base = (int32_t)base64;
    for (int b = 0; b < esz; ++b) {
        int32_t o = base + b;
        if (o >= 0 && o < dcap)
            mem[o] = (unsigned char)(((uint32_t)val >> (8 * b)) & 0xFF);
    }
    return esz;
}

// AOSP GLES20 array+offset overloads: glUniform{1,2,3,4}{f,i}v and
// glUniformMatrix{2,3,4}fv take (…, T[] value, int offset) — the int arg
// following the array is the ELEMENT offset. Bounded name law (AOSP
// GLES20.java signature set, not app knowledge).
bool uniform_offset_family(const std::string& m) {
    if (m.rfind("glUniformMatrix", 0) == 0) return true;
    if (m.rfind("glUniform", 0) == 0) {
        const size_t d = m.find("fv") != std::string::npos
                             ? m.find("fv") : m.find("iv");
        return d != std::string::npos && d > 8;
    }
    return false;
}

size_t elem_size(const std::string& ed) {
    if (ed == "[F" || ed == "[I" || ed == "[J") return 4;
    if (ed == "[S") return 2;
    return 1;   // [B / [C
}

bool marshal_gles20(HeapAllocator* heap, const CallContext& ctx,
                    GlMarshal& m) {
    bool fa_used = false;
    for (size_t ai = 0; ai < ctx.args.size(); ++ai) {
        const auto& a = ctx.args[ai];
        switch (a.kind) {
        case CallContext::Arg::Kind::INT:
        case CallContext::Arg::Kind::LONG:
        case CallContext::Arg::Kind::BOOL:
            m.ia.push_back((uint64_t)(a.kind == CallContext::Arg::Kind::LONG
                                          ? (uint64_t)a.long_val
                                          : (uint64_t)(uint32_t)a.int_val));
            break;
        case CallContext::Arg::Kind::FLOAT:
        case CallContext::Arg::Kind::DOUBLE:
            if (!fa_used) { m.fa.push_back(0.f); fa_used = true; }  // slot 0 reserved
            m.fa.push_back(a.kind == CallContext::Arg::Kind::FLOAT
                               ? a.float_val
                               : (float)a.double_val);
            break;
        case CallContext::Arg::Kind::STRING:
            m.strs.push_back(a.string_val);
            m.pa.push_back(m.strs.back().c_str());
            break;
        case CallContext::Arg::Kind::NULL_REF:
            m.pa.push_back(nullptr);
            break;
        case CallContext::Arg::Kind::OBJECT: {
            uint32_t arr = 0;
            std::string ed;
            // ── S200 Target-B F-NEW-622: HEAP-STRING OBJECT RESOLUTION at
            // the GLES marshal ─────────────────────────────────────────
            // gdx VertexAttribute.alias Strings and the fetchAttributes
            // decoded attribute names arrive as HEAP String OBJECTS (kind
            // OBJECT), not STRING-kind args. The pre-622 marshal chased
            // them as buffers → marshal-fail → glGetAttribLocation answered
            // the unhandled default → the app's attribute map got garbage
            // keys and VertexBufferObject.bind (map-only getAttributeLocation
            // — real bytecode) silently skipped EVERY attribute
            // (location<0 → continue) → attrib0=(nil) at the shape draw.
            // AOSP/ART law: a String object is its chars — resolve via the
            // F-NEW-580 identity fields (__string_value__/value), one law
            // for every GLES20 static that takes a java.lang.String.
            {
                std::string ocls622;
                if (heap->get_object_class(a.object_id, ocls622) &&
                    ocls622 == "Ljava/lang/String;") {
                    std::string sv622;
                    if (!heap->get_object_string_field(
                            a.object_id, "__string_value__", sv622))
                        heap->get_object_string_field(a.object_id, "value",
                                                      sv622);
                    m.strs.push_back(sv622);
                    m.pa.push_back(m.strs.back().c_str());
                    break;
                }
            }
            // ── S188-W18 F-NEW-605: the DIRECT-buffer pointer slot ──────
            // A ByteBuffer minted from a native NewDirectByteBuffer
            // (Gdx2DPixmap.load's pixel surface) has NO heap-array backing;
            // it carries the REAL pointer in __bb_addr__ (+ __bb_cap__ /
            // position / limit). Serving the real pointer is the honest
            // upload law — the driver reads the app's actual decoded
            // pixels. (The pre-W18 path answered marshal-fail → REC-MISS
            // for every texture upload from a native-loaded pixmap.)
            int64_t bb_addr = 0;
            int32_t bb_cap = 0, bb_pos = 0;
            if (heap->get_object_long_field(a.object_id, "__bb_addr__",
                                            bb_addr) &&
                bb_addr != 0 && heap->get_object_int_field(
                                    a.object_id, "__bb_cap__", bb_cap)) {
                heap->get_object_int_field(a.object_id, "position", bb_pos);
                if (bb_pos < 0 || bb_cap <= 0 || bb_pos > bb_cap ||
                    bb_cap > (16 << 20)) {
                    m.ok = false;
                    m.why = "direct-buffer bounds dishonest (cap=" +
                            std::to_string(bb_cap) + " pos=" +
                            std::to_string(bb_pos) + ")";
                    gfx::GfxTrace::instance().marshal_fail(
                        "GLES20", ctx.method, m.why);
                    return false;
                }
                m.pa.push_back((const void*)(uintptr_t)(bb_addr + bb_pos));
                break;
            }
            if (!chase_buffer(heap, a.object_id, arr, ed)) {
                // ── F-NEW-608 (S198, C3): DIRECT-BUFFER FALLBACK law ────────
                // Engine-minted direct ByteBuffers carry __bb_direct__
                // (native addr, INT64) + __bb_direct_cap__ (bytes) — the
                // F-NEW-582 registry face (allocateDirect /
                // newDisposableByteBuffer / native-mint paths). Typed views
                // (asFloatBuffer…) carry __bb_parent__ = the byte receiver
                // and __bb_pos__ in ELEMENT units (the OPENJDK typed-view
                // law). Real libGDX hands GL its direct buffers
                // (Mesh.bind → glVertexAttribPointer; Pixmap pixels →
                // glTexImage2D) — without this fallback every such call
                // died "object arg not materializable" (234×/frame in the
                // tictactoe probe) and nothing rasterized.
                // INTEGRATION NOTE (S195 audit): the lookup goes through
                // nativeexec::lookup_direct_buffer, implemented over this
                // line's W18 engine hooks (f590 direct-buffer registry) —
                // one shared registry, both contributors' mint paths feed
                // it; no second registry was created.
                auto ocls = a.object_class;
                bool is_buffer = ocls.find("Buffer;") != std::string::npos;
                uint32_t owner = a.object_id;
                size_t esz = 1;
                void* dbuf_addr = nullptr;
                int32_t dbuf_cap = 0;
                // ── S199 W19a F-NEW-616 — TYPED-VIEW PARENT-FIRST RESOLUTION
                // law ────────────────────────────────────────────────────
                // A typed view (FloatBuffer/ShortBuffer/…) over a direct
                // parent MUST chase __bb_parent__ FIRST. The pre-616 order
                // looked up the view oid itself first: the f590 hook's
                // snapshot leg "succeeded" on the view — it packs the
                // view's OWN __bb_b<i>__ field run (ELEMENT-indexed, never
                // filled when the data was written through the parent's
                // REAL direct memory by copyJni/put — one identity, one
                // writer) into a FRESH zeroed malloc. Live face (tictactoe,
                // S199): the three SpriteBatch attribute binds received
                // three DIFFERENT zeroed snapshot pointers (attrib0
                // v0=0.000, sb_frag color=0,000 uv=garbage) — triangles
                // rasterized fully transparent over the white clear →
                // white frame. Parent-first serves the ONE real vertex
                // buffer with the view position in ELEMENT units.
                bool is_typed_view = is_buffer &&
                    ocls.find("ByteBuffer;") == std::string::npos &&
                    (ocls.find("FloatBuffer;") != std::string::npos ||
                     ocls.find("IntBuffer;") != std::string::npos ||
                     ocls.find("ShortBuffer;") != std::string::npos ||
                     ocls.find("CharBuffer;") != std::string::npos ||
                     ocls.find("LongBuffer;") != std::string::npos ||
                     ocls.find("DoubleBuffer;") != std::string::npos);
                bool have_direct = false;
                uint32_t par = 0;
                if (is_typed_view) {
                    if (heap->get_object_ref_field(a.object_id,
                                                   "__bb_parent__", par) &&
                        par != 0 &&
                        nativeexec::lookup_direct_buffer(par, &dbuf_addr,
                                                         &dbuf_cap)) {
                        have_direct = true;
                        owner = par;
                        static const struct { const char* n; size_t e; }
                            kViewEsz[] = {
                            {"FloatBuffer;", 4}, {"IntBuffer;", 4},
                            {"ShortBuffer;", 2}, {"CharBuffer;", 2},
                            {"LongBuffer;", 8}, {"DoubleBuffer;", 8},
                        };
                        for (const auto& ve : kViewEsz)
                            if (ocls.find(ve.n) != std::string::npos)
                                { esz = ve.e; break; }
                    }
                }
                if (!have_direct && is_buffer)
                    have_direct = nativeexec::lookup_direct_buffer(
                        a.object_id, &dbuf_addr, &dbuf_cap);
                if (!have_direct && is_buffer && !is_typed_view) {
                    // byte-buffer form: chase __bb_parent__ (element size 1)
                    if (heap->get_object_ref_field(a.object_id,
                                                   "__bb_parent__", par) &&
                        par != 0 &&
                        nativeexec::lookup_direct_buffer(par, &dbuf_addr,
                                                         &dbuf_cap)) {
                        have_direct = true;
                        owner = par;
                        esz = 1;
                    }
                }
                if (have_direct && dbuf_addr) {
                    // __bb_pos__ semantics (the OPENJDK buffer-algebra law):
                    // ByteBuffer pos is BYTES; a typed view's pos is in
                    // ELEMENT units of the view class — always read it from
                    // the ARG object (the view), never from the parent.
                    int32_t pos = 0;
                    heap->get_object_int_field(a.object_id, "__bb_pos__", pos);
                    if (!(pos >= 0 &&
                          (int64_t)pos * (int64_t)esz <= dbuf_cap))
                        pos = 0;  // out-of-bounds position → honest base ptr
                    m.pa.push_back((void*)(uintptr_t)(
                        (uint64_t)(uintptr_t)dbuf_addr + (uint64_t)pos * esz));
                    break;
                }
                m.ok = false;
                m.why = "object arg not materializable (o#" +
                        std::to_string(a.object_id) + " " + a.object_class + ")";
                gfx::GfxTrace::instance().marshal_fail(
                    "GLES20", ctx.method, m.why);
                return false;
            }
            int32_t len = 0;
            if (!heap->get_object_array_length(arr, len) || len < 0) {
                m.ok = false;
                m.why = "array length unreadable";
                gfx::GfxTrace::instance().marshal_fail(
                    "GLES20", ctx.method, m.why);
                return false;
            }
            size_t n = std::min((size_t)len, kMaxArrayElems);
            m.hold.emplace_back();
            if (!read_array_elems(heap, arr, ed, n, m.hold.back())) {
                m.hold.pop_back();
                m.ok = false;
                m.why = "element kind not materializable (" + ed + ")";
                gfx::GfxTrace::instance().marshal_fail(
                    "GLES20", ctx.method, m.why);
                return false;
            }
            // AOSP array+offset family: the NEXT int arg is the element
            // offset — the pointer must start at value[offset], never at
            // value[0] (invented data is forbidden).
            const size_t esz = elem_size(ed);
            if (uniform_offset_family(ctx.method) &&
                ai + 1 < ctx.args.size() &&
                ctx.args[ai + 1].kind == CallContext::Arg::Kind::INT) {
                const int64_t off = ctx.args[ai + 1].int_val;
                if (off < 0 || (size_t)off * esz > m.hold.back().size()) {
                    m.ok = false;
                    m.why = "uniform array offset out of bounds (" +
                            std::to_string(off) + ")";
                    gfx::GfxTrace::instance().marshal_fail(
                        "GLES20", ctx.method, m.why);
                    return false;
                }
                if (off > 0) {
                    // Slice in place: point at the offset inside the hold.
                    m.pa.push_back(m.hold.back().data() + (size_t)off * esz);
                    break;
                }
            }
            m.pa.push_back(m.hold.back().data());
            break;
        }
        default:
            m.ok = false;
            m.why = "arg kind unsupported";
            gfx::GfxTrace::instance().marshal_fail("GLES20", ctx.method, m.why);
            return false;
        }
    }
    // ── S200 Target-B F-NEW-623: the VBO OFFSET form of
    // glVertexAttribPointer ─────────────────────────────────────────────
    // AOSP GLES20 has two overloads: (..., java.nio.Buffer pointer) — the
    // CLIENT-array form (a real address) — and (..., int offset) — the
    // VBO form (a BYTE OFFSET into the GL_ARRAY_BUFFER bound at call
    // time). gdx VertexBufferObject.bind (real bytecode) issues the INT
    // form after glEnableVertexAttribArray. The pre-623 marshal left the
    // pointer array EMPTY for the int form → the bridge's null guard
    // skipped EVERY VBO-path attribute bind (attrib0=(nil) at the
    // tictactoe shape draw). Law: the last arg INT ⇒ the offset form —
    // serve the offset AS the pointer value (the GL contract with a bound
    // GL_ARRAY_BUFFER); PGL resolves it against the bound VBO.
    if (ctx.method == "glVertexAttribPointer" && !ctx.args.empty() &&
        ctx.args.back().kind == CallContext::Arg::Kind::INT) {
        const int64_t off623 = ctx.args.back().int_val;
        if (off623 < 0 || off623 > (64 << 20)) {
            m.ok = false;
            m.why = "vbo attribute offset out of bounds (" +
                    std::to_string(off623) + ")";
            gfx::GfxTrace::instance().marshal_fail("GLES20", ctx.method,
                                                   m.why);
            return false;
        }
        m.pa.push_back((const void*)(uintptr_t)off623);
    }
    return true;
}
CallResult dispatch_gles20_static(HeapAllocator* heap, const CallContext& ctx) {
    // CONT-159 (F-NEW-503 decode diag, env-gated): every GLES20/GLES30
    // static that reaches the shadow — method + arg kinds + ids. Answers
    // WHICH calls the layering delivers and which miss it entirely.
    {
        static thread_local uint64_t gdiag_n = 0;
        static thread_local const bool gdiag_on =
            std::getenv("MINIANDROID_GL_DISPATCH_TRACE") != nullptr;
        if (gdiag_on && gdiag_n < 200) {
            ++gdiag_n;
            std::cerr << "[GL-DISPATCH] " << ctx.method << " argc="
                      << ctx.args.size();
            for (size_t gi = 0; gi < ctx.args.size() && gi < 5; ++gi) {
                const auto& a = ctx.args[gi];
                std::cerr << " a" << gi << ":k" << (int)a.kind;
                if (a.kind == CallContext::Arg::Kind::OBJECT)
                    std::cerr << "o" << a.object_id;
                else if (a.kind == CallContext::Arg::Kind::INT)
                    std::cerr << "=" << a.int_val;
            }
            std::cerr << std::endl;
        }
    }
    // ── F-NEW-463 (CONT-114): state-query-into-Buffer family ────────────
    // AOSP GLES20.glGetIntegerv(pname, params) writes the queried state
    // into the typed java.nio view (the tower3d path passes the IntBuffer
    // from BufferUtils.newIntBuffer into DefaultTextureBinder). The bridge
    // has no native-query path yet; the answer table carries the OpenGL ES
    // 2.0 spec-minimum family (a real driver answers its own limits — the
    // spec guarantees at least these). Writes land in the view object's
    // __bb_b<i>__ element run — the engine's F-NEW-463 view-buffer identity
    // (same storage the IntBuffer.get shadow reads).
    // S200 Target-B probe: what IS the OBJECT-kind name arg?
    if (ctx.method == "glGetAttribLocation" && ctx.args.size() >= 2 &&
        ctx.args[1].kind == CallContext::Arg::Kind::OBJECT && heap) {
        static int nprobe = 0;
        static const bool probe_on =
            std::getenv("MINIANDROID_GL_DEBUG") != nullptr;
        if (probe_on && nprobe < 8) {
            ++nprobe;
            uint32_t oid = ctx.args[1].object_id;
            std::string ocls;
            heap->get_object_class(oid, ocls);
            std::string sval;
            if (!heap->get_object_string_field(oid, "__string_value__", sval))
                heap->get_object_string_field(oid, "value", sval);
            std::cerr << "[GLATTR-PROBE] prog=" << ctx.args[0].int_val
                      << " name_obj=" << oid << " class=" << ocls
                      << " str=" << (sval.empty() ? "(empty)" : sval)
                      << std::endl;
        }
    }
    if (ctx.method == "glGetIntegerv" && ctx.args.size() >= 2 &&
        ctx.args[0].kind == CallContext::Arg::Kind::INT &&
        ctx.args[1].kind == CallContext::Arg::Kind::OBJECT) {
        static const struct { uint32_t pname; int32_t val; } kGlQuery[] = {
            {0x8872u, 8},     // GL_MAX_TEXTURE_IMAGE_UNITS (ES2 spec min)
            {0x8B4Du, 8},     // GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS
            {0x8869u, 8},     // GL_MAX_VERTEX_ATTRIBS
            {0x0D33u, 2048},  // GL_MAX_TEXTURE_SIZE
        };
        const uint32_t pname = (uint32_t)ctx.args[0].int_val;
        const uint32_t buf = ctx.args[1].object_id;
        for (const auto& q : kGlQuery) {
            if (q.pname != pname) continue;
            if (heap && buf != 0) {
                heap->set_object_int_field(buf, "__bb_b0__", q.val);
                gl_view_mirror_write(heap, buf, 0, q.val);  // F-NEW-616c
            }
            gfx::GfxTrace::instance().gl_call(
                "GLES20", ctx.method, true, (int)ctx.args.size(),
                "state-query-into-buffer");
            return CallResult::handled_void();
        }
    }
    // ── F-NEW-503b (CONT-159): shader/program STATUS-QUERY family ───────
    // AOSP GLES20.glGetShaderiv(shader, pname, params) writes the query
    // result into the typed view. ROOT CAUSE this replaces: NO handler →
    // the params view stayed 0 → ShaderProgram.isCompiled() read
    // COMPILE_STATUS == 0 → createDefaultShader threw
    // IllegalArgumentException("Error compiling shader: ") →
    // AndroidLauncher.onCreate death (tower3d live face — SpriteBatch init).
    // Law (libGDX ShaderProgram + OpenGL ES 2.0): COMPILE_STATUS/LINK_STATUS
    // answer GL_TRUE — portablegl's glCompileShader/glLinkProgram really run
    // and the engine's shader set is the libGDX fixed-function family the
    // backend supports; DELETE_STATUS answers GL_FALSE. Writes land in the
    // view object's __bb_b0__ (the F-NEW-463 view-buffer identity, the same
    // storage the IntBuffer.get shadow reads). Unknown pname → fall through
    // to the generic marshal (honest MISS surface unchanged).
    if ((ctx.method == "glGetShaderiv" || ctx.method == "glGetProgramiv") &&
        ctx.args.size() >= 3 && ctx.args[2].kind == CallContext::Arg::Kind::OBJECT) {
        static const struct { uint32_t pname; int32_t val; } kGlSiv[] = {
            {0x8B81u, 1},  // GL_COMPILE_STATUS  → GL_TRUE (legacy/PGL-native face)
            {0x8B82u, 1},  // GL_LINK_STATUS     → GL_TRUE (legacy/PGL-native face)
            {0x8B80u, 0},  // GL_DELETE_STATUS   → GL_FALSE
            {0x8B84u, 0},  // GL_INFO_LOG_LENGTH → 0 (empty log)
            {0x8B85u, 0},  // GL_ACTIVE_UNIFORMS → 0 (uniforms resolve lazily, F-NEW-505)
            {0x8B86u, 0},  // GL_ACTIVE_UNIFORM_MAX_LENGTH → 0
            {0x8B87u, 0},  // GL_ATTACHED_SHADERS → 0 (legacy face)
            // ── S199 W19a F-NEW-620 — the gdx fetchAttributes fix ──────
            // GL_ACTIVE_ATTRIBUTES answered 0 (the pre-620 comment even
            // mislabeled 0x8B89 as ACTIVE_UNIFORMS): gdx
            // ShaderProgram.fetchAttributes() read numAttributes=0 → the
            // attributes ObjectIntMap stayed EMPTY → VertexBufferObject.bind's
            // map-only getAttributeLocation(alias) answered -1 for EVERY
            // program → enableVertexAttribute(-1)/setVertexAttribute(-1)
            // silently no-oped in PGL → the mesh drew with whatever attrib
            // state was left from the previous bind (tictactoe: the shape
            // mesh drew over the SpriteBatch's buffer — board lines
            // missing). The canonical gdx attribute set IS 3
            // (a_position/a_color/a_texCoord0 — the default shaders), so 3
            // is the honest answer for this program family.
            {0x8B89u, 3},  // GL_ACTIVE_ATTRIBUTES → 3 (legacy gdx canonical set)
            {0x8B8Au, 32}, // GL_ACTIVE_ATTRIBUTE_MAX_LENGTH → 32
        };
        const uint32_t pname = (uint32_t)ctx.args[1].int_val;
        const uint32_t buf = ctx.args[2].object_id;
        // ── GP583-GLES-008 fix: PER-OBJECT query answers ────────────────
        // The canned table above answered ONE global reflection for every
        // program (GL_ATTACHED_SHADERS → 0 even after attach calls;
        // GL_ACTIVE_ATTRIBUTES → 3 for unrelated programs). The engine-side
        // bridge now owns the real per-handle state (attached list, family-
        // gated compile/link, deletion flags, per-family attribute counts).
        // Law: consult the bridge FIRST; the canned row applies only to
        // handles the engine does not track (PGL-native program ids).
        const uint32_t handle = (uint32_t)ctx.args[0].int_val;
        int32_t v = 0;
        bool answered = false;
        auto& bridge = gles::GLES20Bridge::instance();
        if (ctx.method == "glGetShaderiv") {
            answered = bridge.shader_query(handle, pname, &v);
        } else {
            answered = bridge.program_query(handle, pname, &v);
        }
        if (!answered) {
            for (const auto& q : kGlSiv) {
                if (q.pname == pname) { v = q.val; answered = true; break; }
            }
        }
        if (answered) {
            if (heap && buf != 0) {
                heap->set_object_int_field(buf, "__bb_b0__", v);
                gl_view_mirror_write(heap, buf, 0, v);  // F-NEW-616c
            }
            gfx::GfxTrace::instance().gl_call(
                "GLES20", ctx.method, true, (int)ctx.args.size(),
                "shader-status-query-into-buffer");
            return CallResult::handled_void();
        }
    }
    // ── S199 W19a F-NEW-620b — glGetActiveAttrib canonical-name law ────
    // The companion of the 620 GL_ACTIVE_ATTRIBUTES answer: gdx's
    // fetchAttributes() loop calls glGetActiveAttrib(program, index,
    // …, length, type, size, name) and resolves the location via
    // glGetAttribLocation(name). Names come from the program's classified
    // family (GP583-GLES-008) — never fabricated for unverifiable sources.
    //
    // ── GP583-GLES-010 fix: the FULL Android GLES20 overload contract ──
    // The old handler wrote length[0], type[0] and the whole name at
    // name[0..nlen] UNCONDITIONALLY — it ignored bufsize, the Java
    // lengthOffset/typeOffset/sizeOffset/nameOffset, the destination array
    // capacities and the ByteBuffer position/limit. Real faces (AOSP
    // GLES20.glGetActiveAttrib javadoc contract):
    //   caller passes lengthOffset=2 → result belongs in length[2], not
    //     length[0] (the old write CORRUPTED unrelated application data);
    //   caller passes bufsize=1 → at most 0 name chars + terminator may be
    //     written (the old write copied the whole canonical name);
    //   a short destination array/ByteBuffer must never be overrun (the
    //     direct-memory face wrote before ANY capacity check — a native
    //     memory-safety face).
    // Observed real layout (624DIAG evidence, the 12-slot AOSP array form):
    //   a0=program a1=index a2=bufsize a3=length[] a4=lengthOffset
    //   a5=type[] a6=typeOffset a7=size[] a8=sizeOffset a9=name[] a10=nameOffset
    if (ctx.method == "glGetActiveAttrib" && ctx.args.size() >= 5 &&
        ctx.args[0].kind == CallContext::Arg::Kind::INT &&
        ctx.args[1].kind == CallContext::Arg::Kind::INT) {
        // Legacy/PGL-native fallback set (engine-untracked handles only —
        // engine-minted programs answer per-family through the bridge).
        static const struct { uint32_t t; const char* n; } kAttribs[] = {
            {0x8B52u, "a_position"},   // GL_FLOAT_VEC4
            {0x8B52u, "a_color"},      // GL_FLOAT_VEC4
            {0x8B53u, "a_texCoord0"},  // GL_FLOAT_VEC2
        };
        const int idx = ctx.args[1].int_val;
        const uint32_t prog = (uint32_t)ctx.args[0].int_val;
        // ── GP583-GLES-008: per-program attribute enumeration ──────────
        const char* nm = nullptr;
        uint32_t atype = 0;
        auto& bridge = gles::GLES20Bridge::instance();
        bool engine_answered = bridge.program_attrib(
            prog, (uint32_t)idx, &nm, &atype);
        if (!engine_answered) {
            if (idx >= 0 && idx < 3) {
                nm = kAttribs[idx].n;       // legacy/PGL-native face
                atype = kAttribs[idx].t;
            } else {
                nm = nullptr;               // out of range: honest empty face
            }
        }
        const int nlen = nm ? (int)std::strlen(nm) : 0;
        if (heap) {
            // ── S200 Target-B F-NEW-624: ARG-LAYOUT LAW (extended) ──────
            // Typed holder selection: length = first [I, type = second [I,
            // size = third [I, name = THE [B; Buffer-view forms fall back
            // to the same rule with fewer holders.
            auto holder_class = [&](size_t k) -> std::string {
                if (k >= ctx.args.size() ||
                    ctx.args[k].kind != CallContext::Arg::Kind::OBJECT)
                    return "";
                std::string c;
                heap->get_object_class(ctx.args[k].object_id, c);
                return c;
            };
            // Java-side destination capacity: arrays via the heap's array
            // length law; Buffer views via the __bb_cap__/__bb_lim__ int
            // fields (the engine ByteBuffer algebra).
            auto holder_capacity = [&](size_t k) -> int {
                if (k >= ctx.args.size() ||
                    ctx.args[k].kind != CallContext::Arg::Kind::OBJECT)
                    return 0;
                const uint32_t oid = ctx.args[k].object_id;
                int32_t len = 0;
                if (heap->get_object_array_length(oid, len) && len > 0)
                    return len;
                int32_t lim = 0;
                if (heap->get_object_int_field(oid, "__bb_lim__", lim) &&
                    lim > 0)
                    return lim;
                int32_t cap = 0;
                if (heap->get_object_int_field(oid, "__bb_cap__", cap))
                    return cap;
                return 0;
            };
            // Buffer-view current position (direct/heap ByteBuffer faces).
            auto bb_position = [&](size_t k) -> int {
                if (k >= ctx.args.size() ||
                    ctx.args[k].kind != CallContext::Arg::Kind::OBJECT)
                    return 0;
                int32_t pos = 0;
                heap->get_object_int_field(ctx.args[k].object_id,
                                           "__bb_pos__", pos);
                return pos > 0 ? pos : 0;
            };
            size_t objs624[4] = {0, 0, 0, 0};
            int nobj624 = 0;
            for (size_t z = 2; z < ctx.args.size() && nobj624 < 4; ++z)
                if (ctx.args[z].kind == CallContext::Arg::Kind::OBJECT)
                    objs624[nobj624++] = z;
            size_t li = 0, ti = 0, si = 0, ni624 = 0;
            int ni_seen = 0;
            for (int z624 = 0; z624 < nobj624; ++z624) {
                const std::string c624 = holder_class(objs624[z624]);
                if (c624 == "[B") { ni624 = objs624[z624]; }
                else if (ni_seen == 0) { li = objs624[z624]; ni_seen = 1; }
                else if (ni_seen == 1) { ti = objs624[z624]; ni_seen = 2; }
                else if (ni_seen == 2) { si = objs624[z624]; ni_seen = 3; }
                else if (ni624 == 0) { ni624 = objs624[z624]; }
            }
            if (ni624 == 0 && nobj624 > 0) ni624 = objs624[nobj624 - 1];
            // GP583-GLES-010: the Java offset argument FOLLOWS each holder
            // (AOSP 12-slot packing: holder at k, offset at k+1). Pads are
            // INT-0 → offset 0, the correct value for the Buffer forms.
            auto offset_after = [&](size_t k) -> int {
                if (k + 1 < ctx.args.size() &&
                    ctx.args[k + 1].kind == CallContext::Arg::Kind::INT)
                    return ctx.args[k + 1].int_val;
                return 0;
            };
            // bufsize: the first INT arg after program/index (a2 in the
            // observed packing) when present. 0 = not supplied (Buffer
            // forms) → the name is bounded by the destination capacity.
            int bufsize = 0;
            if (ctx.args.size() > 2 &&
                ctx.args[2].kind == CallContext::Arg::Kind::INT &&
                nobj624 > 0 && objs624[0] > 2)
                bufsize = ctx.args[2].int_val;
            // Name write bound: bufsize law (GLES spec: at most bufsize-1
            // name chars + NUL) AND the real destination capacity.
            int name_write = nlen;
            if (bufsize > 0 && name_write > bufsize - 1)
                name_write = std::max(0, bufsize - 1);
            if (ni624 || li || ti || si) {
                auto is_array = [](const std::string& c) {
                    return c.size() > 1 && c[0] == '[';
                };
                // length holder: name length (offset + capacity honored)
                if (li) {
                    const uint32_t lb = ctx.args[li].object_id;
                    const std::string lc = holder_class(li);
                    const int off = std::max(0, offset_after(li));
                    const int cap = holder_capacity(li);
                    if (cap > 0 && off >= cap) {
                        // offset outside the array: write nothing (AOSP
                        // throws ArrayIndexOutOfBoundsException; the
                        // engine surface records the boundary honestly).
                    } else if (is_array(lc)) {
                        heap->set_object_int_field(lb, "array[" + std::to_string(off) + "]", nlen);
                    } else {
                        heap->set_object_int_field(lb, "__bb_b0__", nlen);
                        gl_view_mirror_write(heap, lb, 0, nlen);
                    }
                }
                // type holder: GL type enum
                if (ti) {
                    const uint32_t tb = ctx.args[ti].object_id;
                    const std::string tc = holder_class(ti);
                    const int off = std::max(0, offset_after(ti));
                    const int cap = holder_capacity(ti);
                    if (!(cap > 0 && off >= cap)) {
                        if (is_array(tc))
                            heap->set_object_int_field(
                                tb, "array[" + std::to_string(off) + "]",
                                (int32_t)atype);
                        else {
                            heap->set_object_int_field(
                                tb, "__bb_b0__", (int32_t)atype);
                            gl_view_mirror_write(heap, tb, 0, (int32_t)atype);
                        }
                    }
                }
                // size holder (third [I — the GLES20 overload the old
                // handler silently skipped): every family attrib is size 1.
                if (si) {
                    const uint32_t sb = ctx.args[si].object_id;
                    const std::string sc = holder_class(si);
                    const int off = std::max(0, offset_after(si));
                    const int cap = holder_capacity(si);
                    if (!(cap > 0 && off >= cap) && is_array(sc))
                        heap->set_object_int_field(
                            sb, "array[" + std::to_string(off) + "]", 1);
                }
                // name holder: clamped bytes + NUL, EVERY surface the
                // one-identity family defines
                if (ni624) {
                    const uint32_t nb = ctx.args[ni624].object_id;
                    const std::string nc = holder_class(ni624);
                    const int noff = std::max(0, offset_after(ni624));
                    const int cap = holder_capacity(ni624);
                    const int pos = bb_position(ni624);
                    if (is_array(nc)) {
                        // byte[] name: array[nameOffset + i]; never past
                        // the array capacity; NUL only when a byte remains.
                        for (int i = 0; i < name_write; ++i) {
                            if (cap > 0 && noff + i >= cap) break;
                            heap->set_object_int_field(
                                nb, "array[" + std::to_string(noff + i) + "]",
                                (int32_t)(unsigned char)nm[i]);
                        }
                        if (nlen > 0 &&
                            (cap <= 0 || noff + name_write < cap))
                            heap->set_object_int_field(
                                nb,
                                "array[" + std::to_string(noff + name_write) +
                                    "]",
                                0);
                    } else {
                        // ByteBuffer name: direct memory first (bounded by
                        // limit/position — the capacity check now happens
                        // BEFORE the write), field run always.
                        int64_t daddr = 0;
                        uint32_t par = nb;
                        for (int hop = 0; hop < 4 && par != 0; ++hop) {
                            int64_t a2 = 0;
                            if (heap->get_object_long_field(par, "__bb_addr__",
                                                            a2) &&
                                a2 != 0) { daddr = a2; break; }
                            if (heap->get_object_long_field(par, "__bb_direct__",
                                                            a2) &&
                                a2 != 0) { daddr = a2; break; }
                            uint32_t p2 = 0;
                            if (!heap->get_object_ref_field(par, "__bb_parent__",
                                                            p2) ||
                                p2 == 0) break;
                            par = p2;
                        }
                        if (daddr != 0) {
                            const int remaining =
                                cap > 0 ? cap - pos : name_write + 1;
                            const int writable = std::min(name_write,
                                                          std::max(0, remaining - 1));
                            unsigned char* mem = reinterpret_cast<
                                unsigned char*>((uintptr_t)daddr) + pos;
                            for (int i = 0; i < writable; ++i)
                                mem[i] = (unsigned char)nm[i];
                            if (writable > 0)
                                mem[writable] = 0;
                        }
                        for (int i = 0; i < name_write; ++i)
                            heap->set_object_int_field(
                                nb, "__bb_b" + std::to_string(pos + i) + "__",
                                (int32_t)(unsigned char)nm[i]);
                        heap->set_object_int_field(
                            nb, "__bb_b" + std::to_string(pos + name_write) + "__",
                            0);
                    }
                }
                gfx::GfxTrace::instance().gl_call(
                    "GLES20", ctx.method, true, (int)ctx.args.size(),
                    engine_answered ? "active-attrib-per-program"
                                    : "active-attrib-canonical");
                return CallResult::handled_void();
            }
        }
    }
    GlMarshal m;
    const bool marsh = marshal_gles20(heap, ctx, m);
    int32_t iret = 0;
    float fret = 0.f;
    std::string note;
    bool handled = false;
    if (marsh) {
        handled = gles::GLES20Bridge::instance().dispatch(
            ctx.method,
            m.ia.empty() ? nullptr : m.ia.data(), (int)m.ia.size(),
            m.fa.empty() ? nullptr : m.fa.data(), (int)m.fa.size(),
            m.pa.empty() ? nullptr : m.pa.data(), (int)m.pa.size(),
            &iret, &fret, note);
    }
    gfx::GfxTrace::instance().gl_call(
        "GLES20", ctx.method, handled, (int)ctx.args.size(),
        handled ? (note.empty() ? nullptr : note.c_str())
                : (marsh ? "op-not-in-bridge" : m.why.c_str()));
    // ── F-NEW-506 (CONT-159): OUT-PARAM WRITE-BACK law (gen* family) ────
    // GLES20.glGenBuffers/glGenTextures write the generated ids through the
    // marshalled pointer — a COPY of the Java holder's contents. Without a
    // write-back the ids die in the hold: the caller's handle.get(0) read 0
    // → libGDX IndexBufferObject.bind threw GdxRuntimeException("No buffer
    // allocated!") → AndroidLauncher.onCreate death (tower3d). Law: after a
    // handled gen* call, copy the hold bytes back into the Java holder —
    // heap arrays via the array[i] field convention (the read_array_elems
    // mirror), F-NEW-463 Buffer views via the __bb_b<i>__ element run (the
    // glGetIntegerv precedent — the same storage the typed-view get reads).
    if (handled && !m.hold.empty() &&
        (ctx.method == "glGenBuffers" || ctx.method == "glGenTextures")) {
        for (size_t ai = 0; ai < ctx.args.size(); ++ai) {
            if (ctx.args[ai].kind != CallContext::Arg::Kind::OBJECT) continue;
            const uint32_t holder = ctx.args[ai].object_id;
            if (holder == 0 || !heap) continue;
            std::string hcls;
            if (!heap->get_object_class(holder, hcls) || hcls.empty())
                continue;
            const auto& bytes = m.hold.back();
            if (hcls[0] == '[') {
                // array holder: write array[i] per the element width.
                const size_t esz = elem_size(hcls);
                const size_t n = bytes.size() / esz;
                for (size_t ei = 0; ei < n; ++ei) {
                    int32_t v = 0;
                    if (esz == 4)
                        std::memcpy(&v, bytes.data() + ei * 4, 4);
                    else if (esz == 2)
                        std::memcpy(&v, bytes.data() + ei * 2, 2);
                    else
                        v = bytes[ei];
                    heap->set_object_int_field(
                        holder, "array[" + std::to_string(ei) + "]", v);
                }
            } else {
                // Buffer-view holder: __bb_b<i>__ element run (F-NEW-463
                // identity — the typed-view get reads the same slots).
                // F-NEW-616c: mirror each element into the parent's REAL
                // direct memory too (one identity, both writer surfaces).
                for (size_t ei = 0; ei * 4 < bytes.size(); ++ei) {
                    int32_t v = 0;
                    std::memcpy(&v, bytes.data() + ei * 4, 4);
                    heap->set_object_int_field(
                        holder, "__bb_b" + std::to_string(ei) + "__", v);
                    gl_view_mirror_write(heap, holder, (int32_t)ei, v);
                }
            }
            break;  // the first OBJECT arg is the out-param holder
        }
    }
    if (!handled) return CallResult{};
    // Return-kind law: the DEX prototype is authoritative when the engine
    // supplied one. The shadow bridge call sites (build_ctx) may leave the
    // descriptor empty — then the BRIDGE's own int-returning surface
    // decides (AOSP GLES20.java: these statics return int; every other
    // dispatched op is void). Never infer from argc.
    const auto close = ctx.descriptor.find(')');
    if (close != std::string::npos) {
        const char rt = ctx.descriptor[close + 1];
        if (rt == 'I' || rt == 'Z' || rt == 'S' || rt == 'B' || rt == 'C')
            return CallResult::handled_int(iret);
        if (rt == 'F') return CallResult::handled_float(fret);
        return CallResult::handled_void();
    }
    static const char* const kIntRets[] = {
        "glGetError", "glCreateShader", "glCreateProgram",
        "glGetUniformLocation", "glGetAttribLocation",
        "glCheckFramebufferStatus"};
    for (const char* k : kIntRets)
        if (ctx.method == k) return CallResult::handled_int(iret);
    return CallResult::handled_void();
}

}  // namespace

void GLSurfaceViewShadow::init(HeapAllocator* heap) {
    heap_ = heap;
}

static float argf(const CallContext& ctx, size_t i, float def = 0.f) {
    if (i >= ctx.args.size()) return def;
    const auto& a = ctx.args[i];
    if (a.kind == CallContext::Arg::Kind::FLOAT) return a.float_val;
    if (a.kind == CallContext::Arg::Kind::INT) return (float)a.int_val;
    if (a.kind == CallContext::Arg::Kind::DOUBLE) return (float)a.double_val;
    return def;
}

CallResult GLSurfaceViewShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;

    // ── CONT-83 F-NEW-388: GLES20/GLES30 statics (real PortableGL) ──────
    if (cls.find("android/opengl/GLES20") != std::string::npos ||
        cls.find("android/opengl/GLES30") != std::string::npos) {
        return dispatch_gles20_static(heap_, ctx);
    }

    // ── GLSurfaceView instance methods (GL lifecycle state) ─────────────
    if (cls.find("opengl/GLSurfaceView") != std::string::npos) {
        const uint32_t self = ctx.receiver_id;
        // ── F-NEW-462 CONT-120 (bouncy evidence): SurfaceView.getHolder law
        // reaches GLSurfaceView. AOSP android.opengl.GLSurfaceView EXTENDS
        // android.view.SurfaceView, so getHolder() is the SurfaceView holder
        // law verbatim: ONE holder per view, allocated on first request,
        // back-linked to the owner so SurfaceHolder methods resolve their
        // view — and NEVER null (a null holder here made bouncy's
        // GL20Renderer.<init> die on SurfaceHolder.setFormat with a null
        // receiver NPE, which unwound onCreate and left later-initialized
        // fields null → the follow-up Set.add null chain). The holder object
        // is the same "Landroid/view/SurfaceHolder;" class SurfaceViewShadow
        // serves, with the same svHolder/svOwner fields, so lockCanvas/
        // setFormat/setFixedSize resolve through the ONE SurfaceHolder law
        // regardless of which view acquired the holder.
        if (m == "getHolder") {
            uint32_t holder = 0;
            auto hf = heap_->get_object_ref_field(self, "svHolder", holder);
            if (!hf || holder == 0 || !heap_->has_object(holder)) {
                holder = heap_->allocate("Landroid/view/SurfaceHolder;");
                heap_->set_object_ref_field(self, "svHolder", holder,
                                            "Landroid/view/SurfaceHolder;",
                                            "", false);
                heap_->set_object_int_field(holder, "svOwner",
                                            static_cast<int32_t>(self));
            }
            return CallResult::handled_object(holder,
                                              "Landroid/view/SurfaceHolder;");
        }
        auto store_ref = [&](const char* field) {
            if (self != 0 && ctx.args.size() >= 1 &&
                ctx.args[0].kind == CallContext::Arg::Kind::OBJECT && heap_) {
                heap_->set_object_ref_field(self, field,
                                            ctx.args[0].object_id,
                                            ctx.args[0].object_class, "", false);
            }
        };
        auto store_int = [&](const char* field, int32_t v) {
            if (self != 0 && heap_) heap_->set_object_int_field(self, field, v);
        };
        if (m == "setRenderer") {
            // AOSP: setRenderer installs the renderer AND starts the GL
            // thread. Single-threaded runtime: the ENGINE drives the frame
            // cycle per frame; record the renderer + default render mode
            // (RENDERMODE_CONTINUOUSLY = 1).
            store_ref("glRenderer");
            store_int("glRenderMode", 1);
            return CallResult::handled_void();
        }
        if (m == "setEGLContextClientVersion") {
            store_int("glClientVersion", ctx.arg_as_int(0, 0));
            return CallResult::handled_void();
        }
        if (m == "setEGLConfigChooser") {
            // overloads: (int configAttribs[]) | (int r,g,b,a,depth,stencil)
            // | (EGLConfigChooser) — all recorded as accepted plumbing.
            store_ref("glConfigChooser");
            return CallResult::handled_void();
        }
        if (m == "setEGLContextFactory") { store_ref("glContextFactory"); return CallResult::handled_void(); }
        if (m == "setEGLWindowSurfaceFactory") { store_ref("glWindowSurfaceFactory"); return CallResult::handled_void(); }
        if (m == "setGLWrapper") { store_ref("glWrapper"); return CallResult::handled_void(); }
        if (m == "setRenderMode") { store_int("glRenderMode", ctx.arg_as_int(0, 1)); return CallResult::handled_void(); }
        if (m == "getRenderMode") {
            int32_t v = 1;
            if (self != 0 && heap_) heap_->get_object_int_field(self, "glRenderMode", v);
            return CallResult::handled_int(v);
        }
        if (m == "setDebugFlags") { store_int("glDebugFlags", ctx.arg_as_int(0, 0)); return CallResult::handled_void(); }
        if (m == "getDebugFlags") {
            int32_t v = 0;
            if (self != 0 && heap_) heap_->get_object_int_field(self, "glDebugFlags", v);
            return CallResult::handled_int(v);
        }
        if (m == "setPreserveEGLContextOnPause") {
            store_int("glPreserve", ctx.arg_as_bool(0, false) ? 1 : 0);
            return CallResult::handled_void();
        }
        if (m == "requestRender" || m == "requestRenderAndWait") {
            return CallResult::handled_void();   // frame pump drives frames
        }
        if (m == "queueEvent") {
            // AOSP: enqueues a runnable on the GL thread. Single-threaded
            // runtime: the Runnable is stored; the next frame drain runs it
            // through the handler queue law when it is a real object with a
            // run() — recorded honestly otherwise.
            store_ref("glQueuedEvent");
            return CallResult::handled_void();
        }
        // <init> and everything View-related: fall through to ViewShadow.
        return CallResult{};
    }

    // ── GL 1.x receivers ────────────────────────────────────────────────
    if (cls.find("opengles/GL10") != std::string::npos ||
        cls.find("opengles/GL11") != std::string::npos ||
        cls.find("opengl/GLES10") != std::string::npos ||
        cls.find("opengl/GLES11") != std::string::npos) {
        return dispatch_gl(ctx, m);
    }

    // ── EGL model ───────────────────────────────────────────────────────
    if (cls.find("khronos/egl/") != std::string::npos ||
        cls.find("opengl/EGL14") != std::string::npos ||
        cls.find("opengl/EGLExt") != std::string::npos) {
        return dispatch_egl(ctx, m);
    }

    return CallResult{};
}

CallResult GLSurfaceViewShadow::dispatch_gl(const CallContext& ctx,
                                            const std::string& m) {
    // CONT-83 WS-B: every GL10/GLES10 op lands one trace row — handled
    // calls AND the honest REC-MISS frontier (first missing transition).
    CallResult r = dispatch_gl_body(ctx, m);
    gfx::GfxTrace::instance().gl_call("GL10", m, r.handled,
                                      (int)ctx.args.size());
    return r;
}

CallResult GLSurfaceViewShadow::dispatch_gl_body(const CallContext& ctx,
                                                 const std::string& m) {
    // One software context: PortableGL (GL 3.x core semantics — see
    // GLES_BACKEND_COMPARISON_010.md for the ES1-FFP/GLSL frontier law).
    auto f = [&](size_t i) { return argf(ctx, i); };
    auto i = [&](size_t k) { return ctx.arg_as_int(k, 0); };

    if (m == "glClearColor") {
        glClearColor(f(0), f(1), f(2), f(3));
        return CallResult::handled_void();
    }
    if (m == "glClear") {
        // ES1 GL_COLOR_BUFFER_BIT 0x4000 == the GL 3.x value; pass through.
        // S83 evidence: the android-34 stub jar encodes GL constants as DEX
        // static initial values this runtime does not materialize yet, so
        // the app's GL10.GL_COLOR_BUFFER_BIT sget arrives 0 — a REAL clear
        // intent. mask==0 + no other bits → assume color-clear (dominant
        // case) with a one-time diagnostic; never a silent fake pass.
        int32_t mask = i(0);
        if (mask == 0) {
            // S83 evidence: the android-34 stub jar encodes GL constants as
            // DEX static initial values this runtime does not materialize
            // yet, so GL10.GL_COLOR_BUFFER_BIT sgets resolve 0 — a REAL
            // clear intent. Diagnose once, clear color.
            mask = 0x4000;
            static bool warned = false;
            if (!warned) {
                warned = true;
                std::cerr << "[S83-GL] glClear(0): unresolved GL constant → "
                             "color clear" << std::endl;
            }
        }
        // PGL 0.101 redefines the clear bits (1<<10/11/12) while Android
        // apps pass the GL-spec values (0x4000/0x100/0x400) — translate.
        static const GLenum kSpecToPgl[] = {0x4000, 0x400, 0x100, 0x400};
        (void)kSpecToPgl;
        GLenum pgl_mask = 0;
        if (mask & 0x4000) pgl_mask |= GL_COLOR_BUFFER_BIT;    // 1<<10
        if (mask & 0x0100) pgl_mask |= GL_DEPTH_BUFFER_BIT;    // 1<<11
        if (mask & 0x0400) pgl_mask |= GL_STENCIL_BUFFER_BIT;  // 1<<12
        glClear(pgl_mask);
        return CallResult::handled_void();
    }
    if (m == "glViewport") {
        glViewport(i(0), i(1), i(2), i(3));
        return CallResult::handled_void();
    }
    if (m == "glEnable")  { glEnable(gles::pgl_from_spec(i(0)));  return CallResult::handled_void(); }   // F-NEW-607 (S198, C3)
    if (m == "glDisable") { glDisable(gles::pgl_from_spec(i(0))); return CallResult::handled_void(); }  // F-NEW-607 (S198, C3)
    if (m == "glBlendFunc") { glBlendFunc(gles::pgl_from_spec(i(0)), gles::pgl_from_spec(i(1))); return CallResult::handled_void(); }  // F-NEW-607 (S198, C3)
    if (m == "glFlush") return CallResult::handled_void();
    if (m == "glGetError") return CallResult::handled_int(0);
    // ── F-NEW-587 (S196, C3): GLES20.glGetString law ────────────────────
    // AOSP GLES20.glGetString(name): the Android GLES2 driver answers
    // GL_EXTENSIONS (0x1F03) with the real extension list (real Android
    // drivers do — libGDX AndroidGraphics.supportsExtension READS it and
    // every gdx texture-init path rides the answer). PortableGL carries
    // its own GL_EXTENSIONS too. The GL10 shadow body answered glGetString
    // but the GLES20 static adapter did NOT — the GLTexture.<clinit>
    // supportsExtension read NULL → String.contains NPE → onCreate
    // APP-BOUNDARY death. Version/Renderer/Vendor get the same PortableGL
    // identity string (one GL — one identity).
    if (m == "glGetString") {
        if (!ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::INT &&
            (uint32_t)ctx.args[0].int_val == 0x1F03u) {
            return CallResult::handled_string(
                "GL_OES_texture_npot GL_OES_compressed_ETC1_RGB8_texture "
                "GL_OES_standard_derivatives GL_EXT_texture_filter_anisotropic");
        }
        return CallResult::handled_string("PortableGL 0.101 (MiniAndroid software GL)");
    }
    // ES1 fixed-function ops (glColor4f/glMatrixMode/glOrthof/glVertexPointer/
    // glDrawArrays-with-client-arrays...) have NO core-GL equivalent — they
    // fall through so the engine records the honest REC-MISS. The software
    // ES1-FFP translation layer is the registered GL frontier (§24).
    (void)f; (void)i;
    return CallResult{};
}

CallResult GLSurfaceViewShadow::dispatch_egl(const CallContext& ctx,
                                             const std::string& m) {
    // CONT-83 WS-B: EGL lifecycle rows (display/config/context/surface).
    CallResult r = dispatch_egl_body(ctx, m);
    gfx::GfxTrace::instance().gl_call("EGL", m, r.handled,
                                      (int)ctx.args.size());
    return r;
}

CallResult GLSurfaceViewShadow::dispatch_egl_body(const CallContext& ctx,
                                                  const std::string& m) {
    if (!heap_) return CallResult{};
    const std::string& cls = ctx.class_name;
    auto obj = [&](const char* c) -> uint32_t {
        return heap_->get_or_create(c);
    };
    // ── EGL14/EGL10 statics ─────────────────────────────────────────────
    if (m == "eglGetDisplay") {
        return CallResult::handled_object(
            obj("Ljavax/microedition/khronos/egl/EGLDisplay;"),
            "Ljavax/microedition/khronos/egl/EGLDisplay;");
    }
    if (m == "eglInitialize") return CallResult::handled_bool(true);
    if (m == "eglChooseConfig") {
        // GLSurfaceView.checkGL20 law (p9 bytecode-proven, androguard):
        // the return gate is `numConfigs[0] > 0` (aget v5,0; if-lez →
        // return true). args (instance, receiver shifted out):
        //   [0]=display [1]=attribs int[] [2]=configs EGLConfig[]
        //   [3]=numRequested int [4]=numConfigs int[] holder
        // Fill configs[0] with the canonical config object and write 1
        // into the TRAILING int[] count holder. The old body wrote the
        // config into the FIRST object arg (= the display) and never
        // touched the count — checkGL20 returned false →
        // GdxRuntimeException "Libgdx requires OpenGL ES 2.0" at
        // createGLSurfaceView (live: /tmp/p9w17.log).
        std::vector<uint32_t> objs;
        for (const auto& a : ctx.args) {
            if (a.kind == CallContext::Arg::Kind::OBJECT && a.object_id != 0)
                objs.push_back(a.object_id);
        }
        uint32_t config_obj =
            obj("Ljavax/microedition/khronos/egl/EGLConfig;");
        if (objs.size() >= 4) {
            // full shape: fill the configs array
            heap_->set_object_ref_field(objs[2], "array[0]", config_obj,
                                        "Ljavax/microedition/khronos/egl/"
                                        "EGLConfig;",
                                        "", false);
        }
        if (!objs.empty() && heap_) {
            heap_->set_object_int_field(objs.back(), "array[0]", 1);
        }
        return CallResult::handled_bool(true);
    }
    if (m == "eglCreateContext") {
        return CallResult::handled_object(
            obj("Ljavax/microedition/khronos/egl/EGLContext;"),
            "Ljavax/microedition/khronos/egl/EGLContext;");
    }
    if (m == "eglCreateWindowSurface") {
        return CallResult::handled_object(
            obj("Ljavax/microedition/khronos/egl/EGLSurface;"),
            "Ljavax/microedition/khronos/egl/EGLSurface;");
    }
    // S188-W17 (F-NEW-604) — the W16 pinned contract completion. Live
    // evidence (p9 probe + halma W15 log): onSurfaceCreated does
    //   eglGetCurrentContext().getGL() -> setupGL(gl)
    // and GdxEglConfigChooser.getAttrib calls eglGetConfigAttrib x9.
    // The first two answered typed-default null (S186I-STUB), the third
    // REC-MISSed — the surface lifecycle stalled right after GLSurfaceView
    // wiring. Honest answers per the pinned contract:
    if (m == "eglGetCurrentContext") {
        return CallResult::handled_object(
            obj("Ljavax/microedition/khronos/egl/EGLContext;"),
            "Ljavax/microedition/khronos/egl/EGLContext;");
    }
    if (m == "getGL") {
        // AOSP EGLContext.getGL(): the GL entry object bound to the
        // current context — the SAME software context the GLES20 bridge
        // drives (one GL, one framebuffer).
        return CallResult::handled_object(
            obj("Ljavax/microedition/khronos/opengles/GL10;"),
            "Ljavax/microedition/khronos/opengles/GL10;");
    }
    if (m == "eglGetConfigAttrib") {
        // Honest PGL software-config values (RGBA8 backbuffer, 16-bit
        // depth, 8-bit stencil, ES2 renderable, window surface) per the
        // W16 pinned contract. args (instance, receiver shifted out by
        // build_ctx): [0]=display [1]=config [2]=attrib(int)
        // [3]=value(int[] holder). GLES2 spec attrib codes (GL spec —
        // not "magic numbers": they are the EGL enumerations).
        int32_t attrib = ctx.arg_as_int(2, 0);
        int32_t val = 0;
        switch (attrib) {
            case 0x3022: val = 8; break;    // EGL_BLUE_SIZE
            case 0x3023: val = 8; break;    // EGL_GREEN_SIZE
            case 0x3024: val = 8; break;    // EGL_RED_SIZE
            case 0x3021: val = 8; break;    // EGL_ALPHA_SIZE
            case 0x3025: val = 16; break;   // EGL_DEPTH_SIZE
            case 0x3026: val = 8; break;    // EGL_STENCIL_SIZE
            case 0x3031: val = 0; break;    // EGL_SAMPLE_BUFFERS
            case 0x3032: val = 0; break;    // EGL_SAMPLES
            case 0x3053: val = 1; break;    // EGL_SURFACE_TYPE (window)
            case 0x3040: val = 4; break;    // EGL_RENDERABLE_TYPE (ES2)
            case 0x302E: val = 32; break;   // EGL_BUFFER_SIZE
            case 0x303D: val = 0; break;    // EGL_LUMINANCE_SIZE
            case 0x3038: val = 0x3038; break;  // EGL_CONFIG_CAVEAT = NONE
            case 0x3033: val = 1; break;    // EGL_NATIVE_VISUAL_ID (RGBA8888)
            case 0x3056: val = 4096; break; // EGL_MAX_PBUFFER_WIDTH
            case 0x3057: val = 4096; break; // EGL_MAX_PBUFFER_HEIGHT
            default: val = 0; break;
        }
        uint32_t holder = 0;
        for (const auto& a : ctx.args) {
            if (a.kind == CallContext::Arg::Kind::OBJECT && a.object_id != 0) {
                // the LAST object arg is the int[] value holder
                holder = a.object_id;
            }
        }
        if (holder != 0 && heap_) {
            heap_->set_object_int_field(holder, "array[0]", val);
        }
        return CallResult::handled_bool(true);
    }
    if (m == "eglMakeCurrent" || m == "eglSwapBuffers" ||
        m == "eglQuerySurface" || m == "eglDestroySurface" ||
        m == "eglDestroyContext" || m == "eglTerminate") {
        // The engine performs the actual present (PGL backbuf → window
        // framebuffer) after onDrawFrame; the call itself answers true.
        return CallResult::handled_bool(true);
    }
    if (m == "eglGetError") return CallResult::handled_int(0x3000);   // EGL_SUCCESS
    // ── khronos object methods (EGLSurface.get width/height etc.) ──────
    if (m == "getEGL") {
        // AOSP EGLContext.getEGL(): the process-wide EGL entry point —
        // libGDX AndroidGraphics.checkGL20 does
        //   ((EGL10) EGLContext.getEGL()).eglGetDisplay(...)
        // a null here NPE'd the whole libGDX init (P9 exact trace).
        return CallResult::handled_object(
            obj("Ljavax/microedition/khronos/egl/EGL10;"),
            "Ljavax/microedition/khronos/egl/EGL10;");
    }
    if (m == "getWidth") return CallResult::handled_int(0);
    if (m == "getHeight") return CallResult::handled_int(0);
    (void)cls;
    return CallResult{};
}

} } // namespace miniandroid::framework
