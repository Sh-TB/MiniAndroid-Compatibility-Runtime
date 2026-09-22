// matrix_shadow.h — S83-GFX-BASE (§5 Contract C1/C2): android.graphics.Matrix.
//
// ─────────────────────────────────────────────────────────────────────────
// LAW (AOSP graphics/Matrix.java + SkMatrix):
//   The Matrix is a 3x3 row-major value table:
//     | m0 m1 m2 |     | MSCALE_X MSKEW_X  MTRANS_X |
//     | m3 m4 m5 |  =  | MSKEW_Y  MSCALE_Y MTRANS_Y |
//     | m6 m7 m8 |     | MPERSP_0 MPERSP_1 MPERSP_2 |
//   x' = m0*x + m1*y + m2 ; y' = m3*x + m4*y + m5 (persp row is the
//   projective w-division; identity w = m8 = 1 — MiniAndroid stores the
//   perspective row honestly but the affine consumers ignore it, which is
//   exactly AOSP behavior for affine matrices).
//
//   * set*(...)      REPLACES the current values (SkMatrix::setSinCos etc.)
//   * pre*(...)      M' = M ∘ Op  (op applies BEFORE the existing matrix —
//                    this is Canvas.translate/scale/... law)
//   * post*(...)     M' = Op ∘ M  (op applies AFTER)
//   * setValues/getValues exchange the full float[9] table
//   * mapPoints maps an float[] xy pairs through the matrix
//
// STORAGE: values live in the HEAP OBJECT as float fields m0..m8 — the same
// fields CanvasShadow::concat reads. One source of truth; no shadow-local
// copy that could drift (§8 state-confusion prevention).
//
// AUDIT NOTE (S83): the pre-existing Canvas concat law read the transpose
// layout (e from m6, b from m1); no Matrix shadow existed, so no fixture
// could pin the bug. This shadow writes the AOSP layout, and the concat law
// is corrected in the same wave (regression: ladder m-transform fixture).
// ─────────────────────────────────────────────────────────────────────────
#pragma once

#include "shadow_registry.h"

#include <string>

namespace miniandroid { namespace framework {

class MatrixShadow : public Shadow {
public:
    std::string name() const override { return "MatrixShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls == "Landroid/graphics/Matrix;" ||
               cls.find("graphics/Matrix;") != std::string::npos;
    }

    void init(HeapAllocator* heap) override;
    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"reset", "set", "setTranslate", "setScale", "setRotate",
                "setSinCos", "setSkew", "setValues", "getValues",
                "preTranslate", "preScale", "preRotate", "preSkew",
                "preConcat", "postTranslate", "postScale", "postRotate",
                "postSkew", "postConcat", "isIdentity", "isAffine",
                "rectStaysRect", "mapPoints", "mapRadius"};
    }

    // Read the 3x3 from a heap Matrix object (returns identity if absent).
    struct M33 {
        // row-major: v[0..2] = row 0 (x' = 0*x + 1*y + 2), v[3..5] row 1,
        // v[6..8] perspective row.
        float v[9] = {1, 0, 0, 0, 1, 0, 0, 0, 1};
    };
    static bool read_matrix(HeapAllocator* heap, uint32_t obj, M33& out);
    static void write_matrix(HeapAllocator* heap, uint32_t obj, const M33& m);

private:
    // Ensure the heap object exists for the receiver (or allocate one for
    // static/new paths) and return its id (0 on failure).
    uint32_t receiver_or_new(const CallContext& ctx);
    // Apply a 3x3 multiply: a = a ∘ b (a applied LAST — AOSP post law).
    static M33 mul(const M33& a, const M33& b);
};

} } // namespace miniandroid::framework
