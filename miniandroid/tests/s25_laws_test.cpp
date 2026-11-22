// s25_laws_test — the S25 battery (easy-APK completion continuation).
//
// Pins the four shared laws this wave landed, each at unit level with the
// exact app face it moved:
//   r1  S25-W2  — java.util collection COPY-CONSTRUCTION law:
//                 new ArrayList<E>(Collection c) copies the source's live
//                 slots and mutations never alias (EventBus
//                 SubscriberMethodFinder.getMethodsAndRelease — minos 10004
//                 face: the registered @Subscribe methods were lost between
//                 FindState and the cache put → EventBusException).
//   r2  S25-W1c — java.util.Arrays.asList slot-count + dual-store law:
//                 an array WITHOUT __array_length__ (flip MainActivity.<init>
//                 varargs face) still yields the REAL elements through BOTH
//                 store conventions (array[i] and __al_i<k>__), and the
//                 declared-interface dispatch walks the runtime class.
//   r3  S25-W1d — AnimatorSet Builder law: play() returns a NON-NULL
//                 Builder; with() chains the SAME builder identity
//                 (flip animationSetup pc=94 face: Builder.with on null).
//   r4  S25-W1b — the AOSP View tag law: axml android:tag stamps the node's
//                 default_tag at INFLATE time (flip DataBinding bind()
//                 entry contract — root tag layout/activity_main_0).

#include "../src/dex/dalvik_engine_impl.h"
#include "../src/resources/layout_inflater.h"
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/shadow_registry.h"
#include "../src/framework/heap_adapter.h"

#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikType;
using miniandroid::dalvik::DalvikValue;
using miniandroid::dalvik::ApiCallTrace;
namespace flw = miniandroid::framework;

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) ++g_pass; else ++g_fail;
}

static bool bridge(DalvikExecutionEngine& e, const std::string& cls,
                   const std::string& m, const std::vector<DalvikValue>& args,
                   DalvikValue& out) {
    ApiCallTrace::Status st = ApiCallTrace::Status::STUBBED;
    return e.bridge_to_api(cls, m, args, out, st, 0);
}

static DalvikValue obj(uint32_t id, const std::string& cls) {
    return DalvikValue::make_object(id, cls);
}

// r1 — the collection copy-construction law.
static bool r1_copy_ctor(std::string& detail) {
    DalvikExecutionEngine engine;
    auto& heap = engine.get_heap_public();
    const std::string al = "Ljava/util/ArrayList;";
    uint32_t src = heap.allocate(al, 0, 0);
    const char* elems[3] = {"a", "b", "c"};
    for (const char* s : elems) {
        DalvikValue out;
        if (!bridge(engine, al, "add",
                    {obj(src, al), DalvikValue::make_string(s, 0)}, out))
            return false;
    }
    uint32_t dst = heap.allocate(al, 0, 0);
    DalvikValue ctor_out;
    if (!bridge(engine, al, "<init>",
                {obj(dst, al), obj(src, al)}, ctor_out))
        return false;
    auto n = heap.get_object_field(dst, "__al_n__");
    if (!(n.has_value() && n->type == DalvikType::INT32 && n->int_val == 3)) {
        detail = "copy count != 3";
        return false;
    }
    DalvikValue g0;
    if (!bridge(engine, al, "get", {obj(dst, al), DalvikValue::make_int(0)},
                g0))
        return false;
    if (!(g0.type == DalvikType::STRING_REF && g0.string_val == "a")) {
        detail = "copy get(0) != a";
        return false;
    }
    // no-alias law: appending to the copy leaves the source intact.
    DalvikValue add_out, ssize;
    bridge(engine, al, "add",
           {obj(dst, al), DalvikValue::make_string("d", 0)}, add_out);
    bridge(engine, al, "size", {obj(src, al)}, ssize);
    if (!(ssize.type == DalvikType::INT32 && ssize.int_val == 3)) {
        detail = "copy mutation aliased the source";
        return false;
    }
    return true;
}

// r2 — the Arrays.asList slot-count + dual-store law.
static bool r2_aslist(std::string& detail) {
    DalvikExecutionEngine engine;
    auto& heap = engine.get_heap_public();
    // The flip face: an array with NO __array_length__ and int_val 0 —
    // the two length sources the pre-S25 handler trusted.
    uint32_t arr = heap.allocate("[Ljava/lang/Object;", 0, 0);
    heap.set_object_field(arr, "array[0]",
                          DalvikValue::make_string("x", 0));
    heap.set_object_field(arr, "array[1]",
                          DalvikValue::make_string("y", 0));
    DalvikValue out;
    if (!bridge(engine, "Ljava/util/Arrays;", "asList",
                {obj(arr, "[Ljava/lang/Object;")}, out)) {
        detail = "asList bridge failed";
        return false;
    }
    if (!(out.type == DalvikType::OBJECT_REF && out.object_id != 0)) {
        detail = "asList answered null";
        return false;
    }
    // Declared-interface dispatch (S24-W2 normalization) on the runtime
    // class Ljava/util/Arrays$ArrayList; — the S25 dual-store slots must
    // answer the real elements.
    const std::string aal = "Ljava/util/Arrays$ArrayList;";
    DalvikValue g0, g1, sz;
    if (!bridge(engine, "Ljava/util/List;", "get",
                {obj(out.object_id, aal), DalvikValue::make_int(0)}, g0))
        return false;
    if (!bridge(engine, "Ljava/util/List;", "get",
                {obj(out.object_id, aal), DalvikValue::make_int(1)}, g1))
        return false;
    if (!bridge(engine, "Ljava/util/List;", "size", {obj(out.object_id, aal)},
                sz))
        return false;
    if (!(g0.type == DalvikType::STRING_REF && g0.string_val == "x" &&
          g1.type == DalvikType::STRING_REF && g1.string_val == "y" &&
          sz.type == DalvikType::INT32 && sz.int_val == 2)) {
        detail = "asList elements/slot-store mismatch";
        return false;
    }
    return true;
}

// r3 — the AnimatorSet Builder law.
static bool r3_anim_set(std::string& detail) {
    DalvikExecutionEngine engine;
    auto& heap = engine.get_heap_public();
    uint32_t aset = heap.allocate("Landroid/animation/AnimatorSet;", 0, 0);
    uint32_t anim = heap.allocate("Landroid/animation/ObjectAnimator;", 0, 0);
    DalvikValue bout;
    if (!bridge(engine, "Landroid/animation/AnimatorSet;", "play",
                {obj(aset, "Landroid/animation/AnimatorSet;"),
                 obj(anim, "Landroid/animation/ObjectAnimator;")},
                bout)) {
        detail = "play bridge failed";
        return false;
    }
    if (!(bout.type == DalvikType::OBJECT_REF && bout.object_id != 0)) {
        detail = "play answered null (the pc=94 face)";
        return false;
    }
    DalvikValue wout;
    if (!bridge(engine, "Landroid/animation/AnimatorSet$Builder;", "with",
                {bout, obj(anim, "Landroid/animation/ObjectAnimator;")},
                wout))
        return false;
    if (!(wout.type == DalvikType::OBJECT_REF &&
          wout.object_id == bout.object_id)) {
        detail = "with() broke the builder chain identity";
        return false;
    }
    return true;
}

// r4 — the axml android:tag stamping law (inflate contract).
struct Rig {
    miniandroid::dalvik::DalvikHeap heap;
    flw::DalvikHeapAdapter heap_adapter{&heap};
    flw::ViewShadow views;
    miniandroid::resources::ArscParser arsc;
    miniandroid::apk::ApkParser apk;
    miniandroid::resources::DeviceMetrics metrics{1080, 1920, 2.625f, 1.0f};
    miniandroid::resources::LayoutInflater inflater{arsc, apk, "", metrics};
    Rig() { views.init(&heap_adapter); }
    uint32_t inflate(miniandroid::resources::AxmlElement& e,
                     uint32_t parent_id = 0) {
        miniandroid::resources::InflateStats st;
        return inflater.inflate_element(&views, e, parent_id, st);
    }
};

static bool r4_tag(std::string& detail) {
    Rig rig;
    miniandroid::resources::AxmlElement e;
    e.name = "Button";
    miniandroid::resources::AxmlAttribute ta;
    ta.ns = "android";
    ta.name = "tag";
    ta.raw_value = "binding_1";
    ta.value.type = miniandroid::resources::DataType::STRING;
    ta.value.string_value = "binding_1";
    e.attributes.push_back(ta);
    uint32_t v = rig.inflate(e);
    if (v == 0) {
        detail = "inflate failed";
        return false;
    }
    auto* n = rig.views.find_node(v);
    if (n == nullptr || n->default_tag.kind != flw::ViewShadow::ViewNode::
                                          TagValue::STRING ||
        n->default_tag.string_val != "binding_1") {
        detail = "android:tag did not stamp the node tag";
        return false;
    }
    return true;
}

int main() {
    std::cout << "s25_laws_test — the S25 shared-law battery\n";
    std::string d;
    bool r1 = r1_copy_ctor(d);
    record("r1-copy-ctor-law (S25-W2, minos EventBus)", r1, d);
    d.clear();
    bool r2 = r2_aslist(d);
    record("r2-aslist-dual-store (S25-W1c, flip drawables)", r2, d);
    d.clear();
    bool r3 = r3_anim_set(d);
    record("r3-animators-builder (S25-W1d, flip animationSetup)", r3, d);
    d.clear();
    bool r4 = r4_tag(d);
    record("r4-axml-tag-stamp (S25-W1b, flip bind entry)", r4, d);
    std::cout << (g_fail == 0 ? "ALL PASS " : "FAILURES ") << g_pass << "/"
              << (g_pass + g_fail) << "\n";
    return g_fail == 0 ? 0 : 1;
}
