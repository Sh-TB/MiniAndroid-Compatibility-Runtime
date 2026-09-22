// matrix_shadow.cpp — S83-GFX-BASE: android.graphics.Matrix semantics.
#include "matrix_shadow.h"

#include <cmath>
#include <cstring>

namespace miniandroid { namespace framework {

using M33 = MatrixShadow::M33;

// ── heap value I/O ───────────────────────────────────────────────────────
bool MatrixShadow::read_matrix(HeapAllocator* heap, uint32_t obj, M33& out) {
    if (!heap || obj == 0) return false;
    bool any = false;
    for (int i = 0; i < 9; i++) {
        float f = 0.f;
        if (heap->get_object_float_field(obj, "m" + std::to_string(i), f)) {
            out.v[i] = f;
            any = true;
        }
    }
    return any;
}

void MatrixShadow::write_matrix(HeapAllocator* heap, uint32_t obj, const M33& m) {
    if (!heap || obj == 0) return;
    for (int i = 0; i < 9; i++) {
        heap->set_object_float_field(obj, "m" + std::to_string(i), m.v[i]);
    }
}

M33 MatrixShadow::mul(const M33& a, const M33& b) {
    // Row-major 3x3 multiply (affine ∘ affine keeps w row intact).
    M33 r;
    for (int row = 0; row < 3; row++) {
        for (int col = 0; col < 3; col++) {
            float s = 0.f;
            for (int k = 0; k < 3; k++)
                s += a.v[row * 3 + k] * b.v[k * 3 + col];
            r.v[row * 3 + col] = s;
        }
    }
    return r;
}

void MatrixShadow::init(HeapAllocator* heap) {
    heap_ = heap;
}

uint32_t MatrixShadow::receiver_or_new(const CallContext& ctx) {
    if (ctx.has_receiver && ctx.receiver_id != 0) return ctx.receiver_id;
    return heap_ ? heap_->get_or_create("Landroid/graphics/Matrix;") : 0;
}

CallResult MatrixShadow::dispatch(const CallContext& ctx) {
    const std::string& m = ctx.method;
    if (!heap_) return CallResult{};

    // <init> — a fresh Matrix is the identity (AOSP).
    if (m == "<init>" || m == "init") {
        const uint32_t obj = receiver_or_new(ctx);
        if (obj == 0) return CallResult{};
        M33 id;   // identity
        // Copy-ctor: Matrix(Matrix src) copies src values.
        if (ctx.args.size() >= 1 &&
            ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
            M33 src;
            if (read_matrix(heap_, ctx.args[0].object_id, src)) id = src;
        }
        write_matrix(heap_, obj, id);
        return CallResult::handled_void();
    }

    const uint32_t obj = receiver_or_new(ctx);
    if (obj == 0) return CallResult{};

    M33 cur;
    if (!read_matrix(heap_, obj, cur)) {
        cur = M33{};   // identity baseline
    }

    // arg float helpers (CallContext::Arg::FLOAT / INT both legal).
    auto farg = [&](size_t i, float def = 0.f) -> float {
        if (i >= ctx.args.size()) return def;
        const auto& a = ctx.args[i];
        if (a.kind == CallContext::Arg::Kind::FLOAT) return a.float_val;
        if (a.kind == CallContext::Arg::Kind::INT) return (float)a.int_val;
        if (a.kind == CallContext::Arg::Kind::DOUBLE) return (float)a.double_val;
        return def;
    };

    auto build = [&](M33& out, const std::string& m) -> bool {
        // Fill `out` with the op matrix for method name `m`; false =
        // method not a builder (fall through to other handlers).
        out = M33{};
        const size_t n = ctx.args.size();
        if (m == "reset") { return true; }
        if (m == "setTranslate") {
            out.v[2] = farg(0); out.v[5] = farg(1); return true;
        }
        if (m == "setScale") {
            if (n >= 4) {   // (sx, sy, px, py) pivot variant
                const float sx = farg(0), sy = farg(1);
                const float px = farg(2), py = farg(3);
                out.v[0] = sx; out.v[4] = sy;
                out.v[2] = px - sx * px;
                out.v[5] = py - sy * py;
            } else {
                out.v[0] = farg(0); out.v[4] = farg(1);
            }
            return true;
        }
        if (m == "setRotate") {
            const float deg = farg(0);
            const float rad = deg * 3.14159265358979323846f / 180.0f;
            const float cs = std::cos(rad), sn = std::sin(rad);
            if (n >= 3) {   // (deg, px, py)
                const float px = farg(1), py = farg(2);
                out.v[0] = cs; out.v[1] = -sn; out.v[3] = sn; out.v[4] = cs;
                out.v[2] = px - cs * px + sn * py;
                out.v[5] = py - sn * px - cs * py;
            } else {
                out.v[0] = cs; out.v[1] = -sn; out.v[3] = sn; out.v[4] = cs;
            }
            return true;
        }
        if (m == "setSinCos") {
            const float sn = farg(0), cs = farg(1);
            if (n >= 4) {
                const float px = farg(2), py = farg(3);
                out.v[0] = cs; out.v[1] = -sn; out.v[3] = sn; out.v[4] = cs;
                out.v[2] = px - cs * px + sn * py;
                out.v[5] = py - sn * px - cs * py;
            } else {
                out.v[0] = cs; out.v[1] = -sn; out.v[3] = sn; out.v[4] = cs;
            }
            return true;
        }
        if (m == "setSkew") {
            if (n >= 4) {
                const float kx = farg(0), ky = farg(1);
                const float px = farg(2), py = farg(3);
                out.v[1] = kx; out.v[3] = ky;
                out.v[2] = -kx * py; out.v[5] = -ky * px;
            } else {
                out.v[1] = farg(0); out.v[3] = farg(1);
            }
            return true;
        }
        if (m == "setValues") {
            // float[9] heap array — array elements are fields "array[i]".
            const uint32_t arr = ctx.arg_as_object(0, 0);
            if (arr == 0) return false;
            M33 nv;
            for (int i = 0; i < 9; i++) {
                float f = 0.f;
                if (heap_->get_object_float_field(arr, "array[" + std::to_string(i) + "]", f))
                    nv.v[i] = f;
            }
            out = nv;
            return true;
        }
        return false;
    };

    M33 op;
    if (build(op, m)) {
        if (m == "reset" || m.rfind("set", 0) == 0) {
            // set*/reset REPLACE the current values (AOSP law).
            write_matrix(heap_, obj, op);
        }
        return CallResult::handled_void();
    }

    // ── pre*/post*/concat family ─────────────────────────────────────────
    M33 rhs;
    bool has_rhs = false;
    if (m == "preConcat" || m == "postConcat" || m == "set") {
        const uint32_t src = ctx.arg_as_object(0, 0);
        has_rhs = read_matrix(heap_, src, rhs);
    } else {
        // pre/post Translate/Scale/Rotate/Skew/SinCos: build the op matrix by
        // method-name mapping ("preTranslate"/"postTranslate"→"setTranslate").
        const bool is_pre = m.rfind("pre", 0) == 0;
        const bool is_post = m.rfind("post", 0) == 0;
        if (is_pre || is_post) {
            const std::string base = "set" + m.substr(is_pre ? 3 : 4);
            has_rhs = build(rhs, base);
        }
    }
    if (has_rhs) {
        if (m == "preConcat" || m.rfind("pre", 0) == 0) {
            // M' = M ∘ Op
            cur = mul(cur, rhs);
        } else if (m == "postConcat" || m.rfind("post", 0) == 0) {
            // M' = Op ∘ M
            cur = mul(rhs, cur);
        } else if (m == "set") {
            cur = rhs;
        }
        write_matrix(heap_, obj, cur);
        return CallResult::handled_void();
    }

    // ── queries ──────────────────────────────────────────────────────────
    if (m == "getValues") {
        const uint32_t arr = ctx.arg_as_object(0, 0);
        if (arr != 0) {
            for (int i = 0; i < 9; i++) {
                heap_->set_object_float_field(arr, "array[" + std::to_string(i) + "]",
                                              cur.v[i]);
            }
        }
        return CallResult::handled_void();
    }
    if (m == "isIdentity") {
        const bool id = cur.v[0] == 1.f && cur.v[1] == 0.f && cur.v[2] == 0.f &&
                        cur.v[3] == 0.f && cur.v[4] == 1.f && cur.v[5] == 0.f;
        return CallResult::handled_bool(id);
    }
    if (m == "isAffine") {
        const bool aff = cur.v[6] == 0.f && cur.v[7] == 0.f && cur.v[8] == 1.f;
        return CallResult::handled_bool(aff);
    }
    if (m == "rectStaysRect") {
        // True when the matrix maps rects to rects (90° rotations / scale /
        // translate / skew with one zero axis). Conservative exact law.
        const bool axis_aligned =
            (cur.v[1] == 0.f && cur.v[3] == 0.f) ||      // pure scale+trans
            (cur.v[0] == 0.f && cur.v[4] == 0.f);        // 90° rotations
        return CallResult::handled_bool(axis_aligned);
    }
    if (m == "mapPoints") {
        // mapPoints(float[] pts) | (float[] dst, float[] src) — xy pairs.
        const uint32_t first = ctx.arg_as_object(0, 0);
        const uint32_t arr = ctx.args.size() >= 2
                                 ? ctx.arg_as_object(1, first) : first;
        if (arr != 0) {
            int32_t len = 0;
            heap_->get_object_array_length(arr, len);
            const int npts = len / 2;
            for (int i = 0; i < npts; i++) {
                float x = 0.f, y = 0.f;
                heap_->get_object_float_field(arr, "array[" + std::to_string(i * 2) + "]", x);
                heap_->get_object_float_field(arr, "array[" + std::to_string(i * 2 + 1) + "]", y);
                const float nx = cur.v[0] * x + cur.v[1] * y + cur.v[2];
                const float ny = cur.v[3] * x + cur.v[4] * y + cur.v[5];
                heap_->set_object_float_field(arr, "array[" + std::to_string(i * 2) + "]", nx);
                heap_->set_object_float_field(arr, "array[" + std::to_string(i * 2 + 1) + "]", ny);
            }
        }
        return CallResult::handled_void();
    }
    if (m == "mapRadius") {
        const float r = ctx.args.size() >= 1 ? farg(0, 0.f) : 0.f;
        const float scale = std::sqrt(std::fabs(cur.v[0] * cur.v[4] - cur.v[1] * cur.v[3]));
        return CallResult::handled_float(r * scale);
    }

    // Unknown Matrix method: honest fall-through (no silent success).
    return CallResult{};
}

} } // namespace miniandroid::framework
