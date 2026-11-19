// f716_view_tag_law_test.cpp — View tag storage regression fence (M3
// FINDING-011 law, AOSP View.java mTag + mKeyedTags).
//
// Context (W12 n-Puzzle campaign): the app routes every board-tile click
// through cell.setTag(tile) inside assignTile() and GamePlay.onClick reads
// v.getTag() — the W11 run saw dispatched clicks route to NULL because
// assignTile never executed (first-run ImageSelection flow), NOT because of
// a storage defect. This fence pins the storage law itself so the
// interaction chain cannot regress once the picker flow completes:
//
//   T1  setTag(Object) → getTag() round-trips the heap object IDENTITY
//       (object_id + runtime class verbatim — androidx invokes methods on
//       the retrieved tag).
//   T2  repeated setTag overwrites (last write wins, AOSP mTag = field).
//   T3  keyed setTag(int, Object) → getTag(int) round-trips; the DEFAULT
//       tag is untouched by a keyed write.
//   T4  getTag(int) on an absent key → null (AOSP returns null, never
//       throws).
//   T5  distinct views have distinct tag stores (no cross-view leak).
//   T6  getTag() with no tag set → null.
//
// Harness: direct ViewShadow::dispatch with hand-built CallContext rows
// (same pattern as the shadow_registry_invariant §6 checks).
#include "../src/framework/android_shadows.h"
#include "../src/framework/shadow_registry.h"

#include <cstdio>
#include <string>

using namespace miniandroid::framework;

static int g_pass = 0, g_fail = 0;

static void record(const char* name, bool ok, const std::string& detail) {
    std::printf("%s %s %s\n", ok ? "PASS" : "FAIL", name, detail.c_str());
    ok ? ++g_pass : ++g_fail;
}

static CallContext tag_ctx(const char* method, uint32_t view_id,
                           const std::vector<CallContext::Arg>& args) {
    CallContext ctx;
    ctx.class_name = "Landroid/widget/TextView;";
    ctx.method = method;
    ctx.descriptor = "(Ljava/lang/Object;)V";
    ctx.caller = "LF716Test;.run";
    ctx.has_receiver = true;
    ctx.receiver_id = view_id;
    ctx.receiver_class = "Landroid/widget/TextView;";
    ctx.args = args;
    return ctx;
}

static CallContext::Arg obj_arg(uint32_t oid, const char* cls) {
    CallContext::Arg a;
    a.kind = CallContext::Arg::Kind::OBJECT;
    a.object_id = oid;
    a.object_class = cls;
    return a;
}

int main(int argc, char** argv) {
    std::string only = (argc > 1) ? argv[1] : "";
    ShadowRegistry reg;
    register_platform_shadows(reg);
    auto* vs = reg.find_as<ViewShadow>();
    if (!vs) {
        std::printf("FAIL harness ViewShadow not registered\n");
        return 1;
    }

    // T1: object tag round-trip with identity
    if (only.empty() || only == "t1") {
        CallContext::Arg tag = obj_arg(9001, "Lname/livitski/games/puzzle/android/model/Tile;");
        CallResult r1 = vs->dispatch(tag_ctx("setTag", 41, {tag}));
        CallResult r2 = vs->dispatch(tag_ctx("getTag", 41, {}));
        bool ok = r1.handled && r2.handled &&
                  r2.ret_kind == CallResult::RetKind::OBJECT &&
                  r2.object_id == 9001 &&
                  r2.object_class ==
                      "Lname/livitski/games/puzzle/android/model/Tile;";
        record("t1_tag_object_identity", ok,
               "kind=" + std::to_string(static_cast<int>(r2.ret_kind)) +
                   " oid=" + std::to_string(r2.object_id));
    }

    // T2: repeated setTag overwrites
    if (only.empty() || only == "t2") {
        vs->dispatch(tag_ctx("setTag", 42, {obj_arg(1, "LA;")}));
        vs->dispatch(tag_ctx("setTag", 42, {obj_arg(2, "LB;")}));
        CallResult r = vs->dispatch(tag_ctx("getTag", 42, {}));
        bool ok = r.handled && r.ret_kind == CallResult::RetKind::OBJECT &&
                  r.object_id == 2;
        record("t2_tag_overwrite_last_wins", ok,
               "oid=" + std::to_string(r.object_id));
    }

    // T3: keyed tag round-trip + default-tag isolation
    if (only.empty() || only == "t3") {
        vs->dispatch(tag_ctx("setTag", 43, {obj_arg(7, "LDEFAULT;")}));
        CallContext::Arg key;
        key.kind = CallContext::Arg::Kind::INT;
        key.int_val = 7;
        vs->dispatch(tag_ctx("setTag", 43, {key, obj_arg(77, "LKEYED;")}));
        CallResult rk = vs->dispatch(tag_ctx("getTag", 43, {key}));
        CallResult rd = vs->dispatch(tag_ctx("getTag", 43, {}));
        bool ok = rk.handled && rk.ret_kind == CallResult::RetKind::OBJECT &&
                  rk.object_id == 77 && rd.object_id == 7;
        record("t3_keyed_tag_and_default_isolation", ok,
               "keyed_oid=" + std::to_string(rk.object_id) +
                   " default_oid=" + std::to_string(rd.object_id));
    }

    // T4: absent keyed tag → null
    if (only.empty() || only == "t4") {
        CallContext::Arg key;
        key.kind = CallContext::Arg::Kind::INT;
        key.int_val = 999;
        CallResult r = vs->dispatch(tag_ctx("getTag", 44, {key}));
        bool ok = r.handled &&
                  (r.ret_kind == CallResult::RetKind::NULL_REF ||
                   r.object_id == 0);
        record("t4_absent_keyed_tag_null", ok,
               "kind=" + std::to_string(static_cast<int>(r.ret_kind)));
    }

    // T5: distinct views, no leak
    if (only.empty() || only == "t5") {
        vs->dispatch(tag_ctx("setTag", 45, {obj_arg(50, "LVA;")}));
        vs->dispatch(tag_ctx("setTag", 46, {obj_arg(60, "LVB;")}));
        CallResult ra = vs->dispatch(tag_ctx("getTag", 45, {}));
        CallResult rb = vs->dispatch(tag_ctx("getTag", 46, {}));
        bool ok = ra.object_id == 50 && rb.object_id == 60;
        record("t5_distinct_views_no_leak", ok,
               "a_oid=" + std::to_string(ra.object_id) +
                   " b_oid=" + std::to_string(rb.object_id));
    }

    // T6: never-tagged view → null
    if (only.empty() || only == "t6") {
        CallResult r = vs->dispatch(tag_ctx("getTag", 47, {}));
        bool ok = r.handled &&
                  (r.ret_kind == CallResult::RetKind::NULL_REF ||
                   r.object_id == 0);
        record("t6_untagged_view_null", ok,
               "kind=" + std::to_string(static_cast<int>(r.ret_kind)));
    }

    std::printf("\nRESULT: %d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
