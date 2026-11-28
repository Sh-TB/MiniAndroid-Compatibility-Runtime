// T280 law tests (KA-KYK-028/029/030) — discriminating fixtures for the
// three foundational defects reconciled against remote main @ 69ebc96ca.
//
// KA-KYK-028  Choreographer.getFrameTime() unit law: AOSP
//             Choreographer.java — getFrameTime() is the MILLISECOND getter
//             ((int)(getFrameTimeNanos() / NANOS_PER_MS)); the old shadow
//             answered the same ns value for both getters (ms readers saw
//             a value 1e6x too large).
// KA-KYK-029  RectF float bridge: AOSP RectF.java — width()/height() are
//             float consumers of the FLOAT32 fields the ctor law stores;
//             the old shared reader answered INT32 fields only, so every
//             real RectF returned 0.
// KA-KYK-030  Rect/RectF isEmpty OR law: AOSP Rect.java —
//             `return left >= right || top >= bottom;` (a zero-width OR
//             zero-height rect IS empty). The first implementation used
//             && (both axes degenerate), with the AOSP source misquoted
//             in the comment.
//
// Each test FAILS on the defective law and PASSES on the AOSP law.
#include "../src/dex/dalvik_engine_impl.h"
#include "../src/framework/choreographer_shadow.h"

#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

using namespace miniandroid;
using dalvik::DalvikExecutionEngine;
using dalvik::DalvikValue;
using dalvik::DalvikType;
using dalvik::ApiCallTrace;

static int g_pass = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    if (ok) { g_pass++; printf("  PASS: %s\n", what.c_str()); }
    else    { g_fail++; printf("  FAIL: %s\n", what.c_str()); }
}

static framework::CallResult call(framework::ChoreographerShadow& ch,
                                  const char* method) {
    framework::CallContext ctx;
    ctx.class_name = "Landroid/view/Choreographer;";
    ctx.method = method;
    ctx.descriptor = "()J";
    return ch.dispatch(ctx);
}

static bool bridge(DalvikExecutionEngine& eng, const std::string& cls,
                   const std::string& method, uint32_t recv,
                   DalvikValue& result) {
    std::vector<DalvikValue> args;
    args.push_back(DalvikValue::make_object(recv, cls));
    ApiCallTrace::Status st = ApiCallTrace::Status::STUBBED;
    return eng.bridge_to_api(cls, method, args, result, st);
}

static void rectf_fields(DalvikExecutionEngine& eng, uint32_t id,
                         float l, float t, float r, float b) {
    auto& heap = eng.get_heap();
    heap.set_object_field(id, "left", DalvikValue::make_float(l));
    heap.set_object_field(id, "top", DalvikValue::make_float(t));
    heap.set_object_field(id, "right", DalvikValue::make_float(r));
    heap.set_object_field(id, "bottom", DalvikValue::make_float(b));
}

static void rect_fields(DalvikExecutionEngine& eng, uint32_t id,
                        int32_t l, int32_t t, int32_t r, int32_t b) {
    auto& heap = eng.get_heap();
    heap.set_object_field(id, "left", DalvikValue::make_int(l));
    heap.set_object_field(id, "top", DalvikValue::make_int(t));
    heap.set_object_field(id, "right", DalvikValue::make_int(r));
    heap.set_object_field(id, "bottom", DalvikValue::make_int(b));
}

static void choreographer_unit_law() {
    printf("── KA-KYK-028 Choreographer.getFrameTime unit law ──\n");
    DalvikExecutionEngine eng;
    // Minimal HeapAllocator shim forwarding to the engine heap — the same
    // wiring production does via heap_adapter_ (execution_engine.cpp:882).
    struct HeapShim : framework::HeapAllocator {
        DalvikExecutionEngine* eng;
        explicit HeapShim(DalvikExecutionEngine* e) : eng(e) {}
        uint32_t allocate(const std::string& cd) override {
            return eng->get_heap().allocate(cd, 0, 0);
        }
        uint32_t get_singleton(const std::string&) override { return 0; }
        uint32_t get_or_create(const std::string& cd) override {
            return eng->get_heap().allocate(cd, 0, 0);
        }
        bool has_object(uint32_t object_id) override {
            return eng->get_heap().has_object(object_id);
        }
    } shim{&eng};
    framework::ChoreographerShadow ch;
    ch.init(&shim);  // the shadow gates dispatch on the heap

    // Advance the deterministic virtual clock one frame: post + take-due
    // (the F-050 frame pump owns the tick when callbacks are pending).
    framework::CallContext post;
    post.class_name = "Landroid/view/Choreographer;";
    post.method = "postFrameCallback";
    post.descriptor = "(Landroid/view/Choreographer$FrameCallback;)V";
    framework::CallContext::Arg cb;
    cb.kind = framework::CallContext::Arg::Kind::OBJECT;
    cb.object_id = 4242;
    cb.object_class = "Ltest/FakeCallback;";
    post.args.push_back(cb);
    auto pr = ch.dispatch(post);
    check(pr.handled, "postFrameCallback handled");
    auto due = ch.take_due_callbacks();
    // The deterministic virtual clock: base 1e9 ns (kFrameBaseNanos) and
    // each take_due tick advances ONE 60 Hz quantum — the first delivered
    // frame time is 1,016,666,667 ns (the F-050 frame-pump law; the same
    // value the 028 audit computed for the AOSP ms answer, 1016 ms).
    const int64_t first_ft = framework::ChoreographerShadow::kFrameBaseNanos +
                             framework::ChoreographerShadow::kFrameIntervalNanos;
    check(due.size() == 1 && due[0].frame_time_nanos == first_ft,
          "first doFrame carries 1e9 ns + one 60 Hz quantum (1016666667 ns)");

    // THE UNIT LAW: nanos getter == doFrame timestamp; ms getter == / 1e6.
    auto ns = call(ch, "getFrameTimeNanos");
    check(ns.handled && ns.ret_kind == framework::CallResult::RetKind::LONG &&
              ns.long_val == first_ft,
          "getFrameTimeNanos() == doFrame timestamp (ns)");

    auto ms = call(ch, "getFrameTime");
    const int64_t want_ms = first_ft / 1000000LL;
    check(ms.handled && ms.ret_kind == framework::CallResult::RetKind::LONG &&
              ms.long_val == want_ms,
          "getFrameTime() == doFrame timestamp / 1_000_000 (ms)");
    check(ms.long_val != ns.long_val,
          "the ms getter is NOT the raw ns value (the 028 defect)");

    // Second frame monotonic + same-frame coherence: AOSP posts a new
    // callback for the next frame (the clock ticks once per vsync with
    // pending callbacks; empty pending leaves the clock untouched).
    pr = ch.dispatch(post);
    check(pr.handled, "second postFrameCallback handled");
    auto due2 = ch.take_due_callbacks();
    check(due2.size() == 1 &&
              due2[0].frame_time_nanos ==
                  first_ft + framework::ChoreographerShadow::kFrameIntervalNanos,
          "second frame strictly monotonic (+16666667 ns @ 60 Hz)");
    auto ms2 = call(ch, "getFrameTime");
    const int64_t want_ms2 = (first_ft + framework::ChoreographerShadow::kFrameIntervalNanos) / 1000000LL;
    check(ms2.long_val == want_ms2 && ms2.long_val > ms.long_val,
          "getFrameTime() tracks the second frame's ms (floor(1033333334/1e6))");
}

static void rectf_float_bridge_law() {
    printf("── KA-KYK-029 RectF FLOAT bridge law ──\n");
    DalvikExecutionEngine eng;
    auto& heap = eng.get_heap();

    uint32_t rf = heap.allocate("Landroid/graphics/RectF;", 0, 0);
    rectf_fields(eng, rf, 1.5f, 2.0f, 10.75f, 8.25f);

    DalvikValue w;
    check(bridge(eng, "Landroid/graphics/RectF;", "width", rf, w) &&
              w.type == DalvikType::FLOAT32,
          "RectF.width() returns a FLOAT-tagged value");
    check(w.type == DalvikType::FLOAT32 &&
              std::fabs(w.float_val - 9.25f) < 1e-4f,
          "RectF.width() == right - left == 9.25 (fractional kept)");

    DalvikValue h;
    bridge(eng, "Landroid/graphics/RectF;", "height", rf, h);
    check(h.type == DalvikType::FLOAT32 &&
              std::fabs(h.float_val - 6.25f) < 1e-4f,
          "RectF.height() == bottom - top == 6.25");

    // Rect int path unchanged (KA-KYK-029 must not regress Rect).
    uint32_t ri = heap.allocate("Landroid/graphics/Rect;", 0, 0);
    rect_fields(eng, ri, 1, 2, 10, 8);
    DalvikValue iw;
    check(bridge(eng, "Landroid/graphics/Rect;", "width", ri, iw) &&
              iw.type == DalvikType::INT32 && iw.int_val == 9,
          "Rect.width() stays INT and == 9");
}

static void rect_isempty_or_law() {
    printf("── KA-KYK-030 Rect/RectF isEmpty OR law ──\n");
    DalvikExecutionEngine eng;
    auto& heap = eng.get_heap();
    auto is_empty = [&](const std::string& cls, uint32_t id) -> bool {
        DalvikValue v;
        return bridge(eng, cls, "isEmpty", id, v) && v.int_val == 1;
    };

    // zero width + positive height → EMPTY under the AOSP OR law
    // (the && defect classified it non-empty).
    uint32_t a = heap.allocate("Landroid/graphics/RectF;", 0, 0);
    rectf_fields(eng, a, 5.f, 1.f, 5.f, 9.f);
    check(is_empty("Landroid/graphics/RectF;", a),
          "RectF zero-width (l==r, t<b) isEmpty == true");

    // positive width + zero height → EMPTY
    uint32_t b = heap.allocate("Landroid/graphics/RectF;", 0, 0);
    rectf_fields(eng, b, 1.f, 3.f, 8.f, 3.f);
    check(is_empty("Landroid/graphics/RectF;", b),
          "RectF zero-height (t==b, l<r) isEmpty == true");

    // negative width only → EMPTY
    uint32_t c = heap.allocate("Landroid/graphics/RectF;", 0, 0);
    rectf_fields(eng, c, 9.f, 0.f, 2.f, 5.f);
    check(is_empty("Landroid/graphics/RectF;", c),
          "RectF negative-width (l>r) isEmpty == true");

    // normal positive rectangle → NOT empty
    uint32_t d = heap.allocate("Landroid/graphics/RectF;", 0, 0);
    rectf_fields(eng, d, 0.f, 0.f, 10.f, 10.f);
    check(!is_empty("Landroid/graphics/RectF;", d),
          "RectF normal (0,0,10,10) isEmpty == false");

    // Rect int path: same OR law
    uint32_t e = heap.allocate("Landroid/graphics/Rect;", 0, 0);
    rect_fields(eng, e, 4, 4, 4, 10);
    check(is_empty("Landroid/graphics/Rect;", e),
          "Rect zero-width (l==r) isEmpty == true");
    uint32_t f = heap.allocate("Landroid/graphics/Rect;", 0, 0);
    rect_fields(eng, f, 0, 0, 10, 10);
    check(!is_empty("Landroid/graphics/Rect;", f),
          "Rect normal isEmpty == false");
}

int main() {
    printf("── T280 foundational law battery (KA-KYK-028/029/030) ──\n");
    choreographer_unit_law();
    rectf_float_bridge_law();
    rect_isempty_or_law();
    printf("── RESULT: %d passed, %d failed ──\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
