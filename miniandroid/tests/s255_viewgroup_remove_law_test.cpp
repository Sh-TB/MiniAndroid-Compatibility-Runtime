// s255_viewgroup_remove_law_test — F-NEW-685 (W31): the ViewGroup
// INDEX-based removal family battery.
//
// The runtime had the object-identity removal arms (removeView /
// removeViewInLayout / removeAllViews) but NONE of the index arms AOSP
// apps drive teardown through: removeViewAt(int) / removeViews(int,int)
// / removeViewsInLayout(int,int) fell through to the generic stub tail
// (silent no-op — the child stayed in mChildren and the app face kept
// the removed row).
//
// Law references (AOSP ViewGroup.java; the R-NEW-302 removal doctrine
// extended to the index family):
//   r1  addView base — the rig drives the production addView arms.
//   r2  removeViewAt(int) middle removal: mChildren compacts, the
//       removed child's mParent is cleared, survivors keep identity,
//       requestLayout fires (layout_dirty — R-NEW-302).
//   r3  removeViewAt out-of-range: IndexOutOfBoundsException deferred
//       BEFORE any removal (AOSP getChildAt bounds check); tree
//       unchanged.
//   r4  removeViews(start, count) range: removes [start, start+count),
//       survivors keep order + identity, requestLayout fires.
//   r5  removeViews invalid range: deferred IOOBE, tree unchanged.
//   r6  removeViewsInLayout(start, count): identical removal, NO
//       requestLayout (the AOSP in-pass law — layout_dirty stays false;
//       the detachViewFromParent F-NEW-323 family documents the same
//       rule for detach).
//   r7  family regression guard: removeView(View) / removeAllViews /
//       removeViews(count==0) keep their established behavior.
//
// Tests are package-independent: no APK, no ARSC, synthetic trees.

#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/framework/shadow_registry.h"

#include <cstdint>
#include <cstdio>
#include <string>

using namespace miniandroid;

static int g_checks = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    g_checks++;
    if (!ok) { g_fail++; printf("  FAIL: %s\n", what.c_str()); }
    else      printf("  PASS: %s\n", what.c_str());
}

namespace {

struct Rig {
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter heap_adapter{&heap};
    framework::ShadowRegistry reg;
    framework::ViewShadow* views = nullptr;

    Rig() {
        views = reg.register_shadow<framework::ViewShadow>();
        reg.set_heap(&heap_adapter);
        views->init(&heap_adapter);
    }

    uint32_t view(const char* cls = "Landroid/view/View;") {
        return views->create_view(cls);
    }

    framework::CallResult call(const std::string& method, uint32_t recv,
                               const std::vector<framework::CallContext::Arg>& args) {
        framework::CallContext ctx;
        ctx.class_name = "Landroid/widget/LinearLayout;";
        ctx.method = method;
        ctx.descriptor = "";
        ctx.has_receiver = true;
        ctx.receiver_id = recv;
        ctx.receiver_class = ctx.class_name;
        ctx.args = args;
        return views->dispatch(ctx);
    }

    static framework::CallContext::Arg obj_arg(uint32_t id) {
        framework::CallContext::Arg a;
        a.kind = framework::CallContext::Arg::Kind::OBJECT;
        a.object_id = id;
        return a;
    }
    static framework::CallContext::Arg int_arg(int32_t v) {
        framework::CallContext::Arg a;
        a.kind = framework::CallContext::Arg::Kind::INT;
        a.int_val = v;
        return a;
    }

    // Production-path addView (receiver = parent, arg0 = child).
    void add(uint32_t parent, uint32_t child) {
        call("addView", parent, {obj_arg(child)});
    }

    int32_t count(uint32_t parent) {
        auto cr = call("getChildCount", parent, {});
        return cr.ret_kind == framework::CallResult::RetKind::INT
                   ? cr.int_val : -1;
    }

    uint32_t child_at(uint32_t parent, int32_t idx) {
        auto cr = call("getChildAt", parent, {int_arg(idx)});
        return cr.ret_kind == framework::CallResult::RetKind::OBJECT
                   ? cr.object_id : 0;
    }

    bool parent_of(uint32_t child, uint32_t expected) {
        auto cr = call("getParent", child, {});
        if (expected == 0)
            return cr.ret_kind == framework::CallResult::RetKind::NULL_REF ||
                   (cr.ret_kind == framework::CallResult::RetKind::OBJECT &&
                    cr.object_id == 0);
        return cr.ret_kind == framework::CallResult::RetKind::OBJECT &&
               cr.object_id == expected;
    }
};

// A fresh parent with the three named children added (r-base shape).
struct Tree3 {
    Rig rig;
    uint32_t parent, c0, c1, c2;
    Tree3()
        : parent(rig.view("Landroid/widget/LinearLayout;")),
          c0(rig.view()), c1(rig.view()), c2(rig.view()) {
        rig.add(parent, c0);
        rig.add(parent, c1);
        rig.add(parent, c2);
    }
};

}  // namespace

int main() {
    printf("s255_viewgroup_remove_law_test — F-NEW-685 index-removal family\n");

    // r1 — the rig base: three addView dispatches land three children.
    {
        Tree3 t;
        check(t.rig.count(t.parent) == 3, "r1 addView base childCount==3");
        check(t.rig.child_at(t.parent, 0) == t.c0 &&
                  t.rig.child_at(t.parent, 1) == t.c1 &&
                  t.rig.child_at(t.parent, 2) == t.c2,
              "r1 child identity order c0,c1,c2");
    }

    // r2 — removeViewAt(1): the middle child leaves, survivors keep
    // identity + parent, the removed child's mParent clears, and the
    // R-NEW-302 requestLayout law fires (layout_dirty).
    {
        Tree3 t;
        auto cr = t.rig.call("removeViewAt", t.parent,
                             {Rig::int_arg(1)});
        check(!cr.is_exc && cr.handled, "r2 removeViewAt(1) handled, no exc");
        check(t.rig.count(t.parent) == 2, "r2 childCount 3 -> 2");
        check(t.rig.child_at(t.parent, 0) == t.c0 &&
                  t.rig.child_at(t.parent, 1) == t.c2,
              "r2 survivors c0,c2 (compaction kept order)");
        check(t.rig.parent_of(t.c1, 0), "r2 removed child mParent cleared");
        check(t.rig.parent_of(t.c0, t.parent) &&
                  t.rig.parent_of(t.c2, t.parent),
              "r2 survivors keep mParent");
        check(t.rig.views->layout_dirty, "r2 removeViewAt -> requestLayout (layout_dirty)");
    }

    // r3 — removeViewAt out-of-range: AOSP getChildAt bounds check
    // defers IndexOutOfBoundsException BEFORE any removal.
    {
        Tree3 t;
        auto hi = t.rig.call("removeViewAt", t.parent, {Rig::int_arg(5)});
        check(hi.is_exc &&
                  hi.exc_class == "Ljava/lang/IndexOutOfBoundsException;",
              "r3 removeViewAt(5) defers IOOBE");
        check(t.rig.count(t.parent) == 3, "r3 tree unchanged after OOB high");
        Tree3 t2;
        auto neg = t2.rig.call("removeViewAt", t2.parent, {Rig::int_arg(-1)});
        check(neg.is_exc &&
                  neg.exc_class == "Ljava/lang/IndexOutOfBoundsException;",
              "r3 removeViewAt(-1) defers IOOBE");
        check(t2.rig.count(t2.parent) == 3,
              "r3 tree unchanged after OOB negative");
    }

    // r4 — removeViews(1, 2): the range [1,3) leaves, the survivor keeps
    // order + identity, requestLayout fires.
    {
        Tree3 t;
        auto cr = t.rig.call("removeViews", t.parent,
                             {Rig::int_arg(1), Rig::int_arg(2)});
        check(!cr.is_exc && cr.handled, "r4 removeViews(1,2) handled");
        check(t.rig.count(t.parent) == 1, "r4 childCount 3 -> 1");
        check(t.rig.child_at(t.parent, 0) == t.c0, "r4 survivor c0 at index 0");
        check(t.rig.parent_of(t.c1, 0) && t.rig.parent_of(t.c2, 0),
              "r4 removed children mParent cleared");
        check(t.rig.views->layout_dirty,
              "r4 removeViews -> requestLayout (layout_dirty)");
    }

    // r5 — removeViews invalid range: start+count beyond childCount and
    // negative start defer IOOBE; the tree is unchanged.
    {
        Tree3 t;
        auto over = t.rig.call("removeViews", t.parent,
                               {Rig::int_arg(2), Rig::int_arg(2)});
        check(over.is_exc &&
                  over.exc_class == "Ljava/lang/IndexOutOfBoundsException;",
              "r5 removeViews(2,2) on 3 children defers IOOBE");
        check(t.rig.count(t.parent) == 3, "r5 tree unchanged after range OOB");
        Tree3 t2;
        auto neg = t2.rig.call("removeViews", t2.parent,
                               {Rig::int_arg(-1), Rig::int_arg(1)});
        check(neg.is_exc &&
                  neg.exc_class == "Ljava/lang/IndexOutOfBoundsException;",
              "r5 removeViews(-1,1) defers IOOBE");
        check(t2.rig.count(t2.parent) == 3, "r5 tree unchanged after neg start");
    }

    // r6 — removeViewsInLayout(0, 2): identical removal, but the AOSP
    // in-pass law keeps requestLayout silent (layout_dirty stays false).
    // The addView arms set layout_dirty themselves (a tree addition must
    // re-layout too), so clear the flag after construction to isolate the
    // arm under test.
    {
        Tree3 t;
        t.rig.views->layout_dirty = false;
        auto cr = t.rig.call("removeViewsInLayout", t.parent,
                             {Rig::int_arg(0), Rig::int_arg(2)});
        check(!cr.is_exc && cr.handled, "r6 removeViewsInLayout(0,2) handled");
        check(t.rig.count(t.parent) == 1, "r6 childCount 3 -> 1");
        check(t.rig.child_at(t.parent, 0) == t.c2,
              "r6 survivor c2 (range [0,2) removed)");
        check(!t.rig.views->layout_dirty,
              "r6 removeViewsInLayout does NOT requestLayout (in-pass law)");
    }

    // r7 — the established family members keep their behavior (the new
    // arms sit beside them, nothing regressed).
    {
        Tree3 t;
        auto rv = t.rig.call("removeView", t.parent, {Rig::obj_arg(t.c1)});
        check(rv.handled && !rv.is_exc && t.rig.count(t.parent) == 2,
              "r7 removeView(View) still removes");
        auto all = t.rig.call("removeAllViews", t.parent, {});
        check(all.handled && t.rig.count(t.parent) == 0 &&
                  t.rig.parent_of(t.c0, 0) && t.rig.parent_of(t.c2, 0),
              "r7 removeAllViews still clears all + clears mParent");
        Tree3 t2;
        auto zero = t2.rig.call("removeViews", t2.parent,
                                {Rig::int_arg(9), Rig::int_arg(0)});
        check(zero.handled && !zero.is_exc && t2.rig.count(t2.parent) == 3,
              "r7 removeViews(count==0) = AOSP empty-loop no-op (no exc)");
    }

    printf("s255: %d checks, %d failures\n", g_checks, g_fail);
    return g_fail == 0 ? 0 : 1;
}
