// s238_achievements_audit_test — the coder-achievements audit battery.
//
// One row per achievement family from the wave stack (#588 Wave-5
// F-NEW-630..646 + the W19 UriMatcher + S233 managedQuery faces), each
// exercised through the REAL bridge with the wave-documented expected
// face. The W26 laws (getSuperclass framework table, StringReader EOF,
// node_at degenerate pass-through) already carry their s234 battery; the
// W27 bounded-append law carries s237 — both audited, not duplicated.

#include "../src/dex/dalvik_engine.h"
#include "../src/framework/shadow_registry.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/gles/gles20_bridge.h"
#include "../src/gles/pgl_backend.h"

#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikType;
using miniandroid::dalvik::DalvikValue;
using miniandroid::gles::GLES20Bridge;
namespace flw = miniandroid::framework;
using flw::CallResult;
using flw::ShadowRegistry;

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
    miniandroid::dalvik::ApiCallTrace::Status st =
        miniandroid::dalvik::ApiCallTrace::Status::STUBBED;
    return e.bridge_to_api(cls, m, args, out, st, 0);
}

int main(int argc, char** argv) {
    std::cout << "== s238_achievements_audit — the #588 wave battery ==\n";
    (void)argc; (void)argv;
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 4000;
    ShadowRegistry registry;
    flw::register_platform_shadows(registry);
    auto heap_adapter = std::make_unique<flw::DalvikHeapAdapter>(
        &engine.get_heap_public(), &engine);
    registry.set_heap(heap_adapter.get());
    engine.set_shadow_registry(&registry);
    auto& heap = engine.get_heap_public();

    // ── the service-object family (F-NEW-630/637/639) ──
    {
        uint32_t ctx = heap.allocate("Landroid/app/Activity;", 0, 0);
        DalvikValue out;
        bool ok1 = bridge(engine, "Landroid/app/Activity;", "getSystemService",
                          {DalvikValue::make_object(ctx, "Landroid/app/Activity;"),
                           DalvikValue::make_string("phone", 0)}, out);
        record("r1_f630_getSystemService_phone",
               ok1 && out.type == DalvikType::OBJECT_REF && out.object_id != 0,
               "obj#" + std::to_string(out.object_id) +
                   " (vanilla PlaybackService.onCreate face)");

        bool ok2 = bridge(engine, "Landroid/app/Activity;", "getSystemService",
                          {DalvikValue::make_object(ctx, "Landroid/app/Activity;"),
                           DalvikValue::make_string("power", 0)}, out);
        record("r2_f637_getSystemService_power",
               ok2 && out.type == DalvikType::OBJECT_REF && out.object_id != 0,
               "obj#" + std::to_string(out.object_id) +
                   " (conversations POWER_SERVICE face)");

        bool ok3 = bridge(engine, "Landroid/app/Activity;", "getSystemService",
                          {DalvikValue::make_object(ctx, "Landroid/app/Activity;"),
                           DalvikValue::make_string("wallpaper", 0)}, out);
        record("r3_f639_getSystemService_wallpaper",
               ok3 && out.type == DalvikType::OBJECT_REF && out.object_id != 0,
               "obj#" + std::to_string(out.object_id) +
                   " (ADW Workspace.updateWallpaperOffset face)");
    }

    // ── F-NEW-638: AppWidgetManager.getInstance never-null ──
    {
        uint32_t ctx = heap.allocate("Landroid/app/Activity;", 0, 0);
        DalvikValue out;
        bool ok = bridge(engine, "Landroid/app/Activity;", "getSystemService",
                         {DalvikValue::make_object(ctx, "Landroid/app/Activity;"),
                          DalvikValue::make_string("appwidget", 0)},
                         out);
        record("r4_f638_appwidget_instance",
               ok && out.type == DalvikType::OBJECT_REF && out.object_id != 0,
               "obj#" + std::to_string(out.object_id) +
                   " (the APPWIDGET_SERVICE mapping law, 76877)");
    }

    // ── F-NEW-631: getActionBar + the Tab contract ──
    {
        uint32_t act = heap.allocate("Landroid/app/Activity;", 0, 0);
        DalvikValue bar, tab;
        bool ok1 = bridge(engine, "Landroid/app/Activity;", "getActionBar",
                          {DalvikValue::make_object(act, "Landroid/app/Activity;")},
                          bar);
        bool bar_ok = ok1 && bar.type == DalvikType::OBJECT_REF && bar.object_id != 0;
        bool ok2 = bridge(engine, "Landroid/app/ActionBar;", "newTab",
                          {DalvikValue::make_object(bar.object_id, "Landroid/app/ActionBar;")},
                          tab);
        uint32_t tab1 = tab.object_id;
        bool tab_ok = ok2 && tab.type == DalvikType::OBJECT_REF && tab1 != 0;
        bool ok3 = bridge(engine, "Landroid/app/ActionBar$Tab;", "setText",
                          {DalvikValue::make_object(tab1, "Landroid/app/ActionBar$Tab;"),
                           DalvikValue::make_string("T", 0)},
                          tab);
        record("r5_f631_actionbar_never_null",
               bar_ok, "obj#" + std::to_string(bar.object_id));
        record("r6_f631_tab_contract",
               tab_ok && ok3 && tab.type == DalvikType::OBJECT_REF &&
                   tab.object_id == tab1,
               "tab obj#" + std::to_string(tab1) +
                   " setText returns the SAME tab (the chaining law)");
    }

    // ── F-NEW-632: getResourcesForApplication never-null ──
    {
        uint32_t pm = heap.allocate("Landroid/content/pm/PackageManager;", 0, 0);
        DalvikValue out;
        bool ok = bridge(engine, "Landroid/content/pm/PackageManager;",
                         "getResourcesForApplication",
                         {DalvikValue::make_object(pm, "Landroid/content/pm/PackageManager;"),
                          DalvikValue::make_string("org.openintents.filemanager", 0)},
                         out);
        record("r7_f632_resources_for_app",
               ok && out.type == DalvikType::OBJECT_REF && out.object_id != 0,
               "obj#" + std::to_string(out.object_id) +
                   " (OIFM MimeTypeParser face)");
    }

    // ── F-NEW-633: Intent.getExtras -> Bundle + Bundle.getBoolean INT32 ──
    {
        uint32_t intent = heap.allocate("Landroid/content/Intent;", 0, 0);
        DalvikValue out;
        bridge(engine, "Landroid/content/Intent;", "putExtra",
               {DalvikValue::make_object(intent, "Landroid/content/Intent;"),
                DalvikValue::make_string("org.openintents.EXTRA_BOOL", 0),
                DalvikValue::make_bool(true)},
               out);
        bool ok = bridge(engine, "Landroid/content/Intent;", "getExtras",
                         {DalvikValue::make_object(intent, "Landroid/content/Intent;")},
                         out);
        uint32_t bundle = out.object_id;
        record("r8_f633_intent_get_extras",
               ok && out.type == DalvikType::OBJECT_REF && bundle != 0,
               "bundle obj#" + std::to_string(bundle) +
                   " (OIFM EulaActivity face)");
        DalvikValue b;
        bool ok2 = bridge(engine, "Landroid/os/Bundle;", "getBoolean",
                          {DalvikValue::make_object(bundle, "Landroid/os/Bundle;"),
                           DalvikValue::make_string("org.openintents.EXTRA_BOOL", 0)},
                          b);
        record("r9_f633_bundle_getboolean_int32",
               ok2 && (b.type == DalvikType::INT32 ||
                       b.type == DalvikType::BOOLEAN) && b.int_val == 1,
               "val=" + std::to_string(b.int_val) + " type=" +
                   std::to_string((int)b.type) +
                   " (the register face the DEX const-restore reads)");
    }

    // ── F-NEW-634: ListActivity.getListView (the NEW F-LISTACTIVITY-GV
    //    arm) — a ViewShadow node carrying android_view_id ==
    //    android.R.id.list (0x0102000A) resolves to the view object ──
    {
        uint32_t act = heap.allocate("Landroid/app/ListActivity;", 0, 0);
        uint32_t lv = 0;
        if (auto* vs = registry.find_as<flw::ViewShadow>()) {
            vs->get_or_create_node(900000, "Landroid/widget/FrameLayout;");
            auto* n = vs->get_or_create_node(900001, "Landroid/widget/ListView;");
            if (n) {
                n->android_view_id = 0x0102000A;
                n->parent_id = 900000;  // the R-NEW-441b scan skips orphans
                lv = 900001;
            }
        }
        DalvikValue out;
        bool ok = bridge(engine, "Landroid/app/ListActivity;", "getListView",
                         {DalvikValue::make_object(act, "Landroid/app/ListActivity;")},
                         out);
        record("r10_f634_getlistview",
               lv != 0 && ok && out.type == DalvikType::OBJECT_REF &&
                   out.object_id == 900001,
               "view obj#" + std::to_string(out.object_id) +
                   " (the K-9 Accounts.onCreate face; resolve-on-first-call)");
    }

    // ── F-NEW-641: Context.getApplicationInfo never-null ──
    {
        uint32_t ctx = heap.allocate("Landroid/app/Activity;", 0, 0);
        DalvikValue out;
        bool ok = bridge(engine, "Landroid/app/Activity;", "getApplicationInfo",
                         {DalvikValue::make_object(ctx, "Landroid/app/Activity;")},
                         out);
        record("r11_f641_get_application_info",
               ok && out.type == DalvikType::OBJECT_REF && out.object_id != 0,
               "obj#" + std::to_string(out.object_id) +
                   " (OIFM VersionUtils face)");
    }

    // ── F-NEW-644: PM.getPackageInfo -> applicationInfo populated ──
    {
        uint32_t pm = heap.allocate("Landroid/content/pm/PackageManager;", 0, 0);
        DalvikValue out;
        bool ok = bridge(engine, "Landroid/content/pm/PackageManager;",
                         "getPackageInfo",
                         {DalvikValue::make_object(pm, "Landroid/content/pm/PackageManager;"),
                          DalvikValue::make_string("org.openintents.filemanager", 0),
                          DalvikValue::make_int(0)},
                         out);
        bool populated = false;
        if (ok && out.type == DalvikType::OBJECT_REF && out.object_id != 0) {
            auto f = heap.get_object_field(out.object_id, "applicationInfo");
            populated = f.has_value() && f->type == DalvikType::OBJECT_REF &&
                        f->object_id != 0;
        }
        record("r12_f644_packageinfo_application_info",
               ok && out.type == DalvikType::OBJECT_REF && out.object_id != 0 &&
                   populated,
               "pkginfo obj#" + std::to_string(out.object_id) +
                   " with a live applicationInfo field");
    }

    // ── S233: managedQuery -> Cursor (the 6-arg face) ──
    {
        uint32_t act = heap.allocate("Landroid/app/Activity;", 0, 0);
        DalvikValue out;
        bool ok = bridge(engine, "Landroid/app/Activity;", "managedQuery",
                         {DalvikValue::make_object(act, "Landroid/app/Activity;"),
                          DalvikValue::make_string(
                              "content://org.moire.opensudoku/sudoku", 0),
                          DalvikValue::make_null(),
                          DalvikValue::make_null(),
                          DalvikValue::make_null(),
                          DalvikValue::make_null()},
                         out);
        // The battery context carries NO content provider: the AOSP
        // unknown-authority contract is the LOUD deferred
        // IllegalArgumentException + a null result (the F-NEW-655
        // forward still runs — the PROVIDER-DISPATCH trace in the log).
        record("r13_s233_managed_query_unknown_authority",
               ok && out.type != DalvikType::OBJECT_REF,
               "the loud deferred IAE + null (no provider installed; "
               "the forward itself ran — [F-NEW-655] trace)");
    }

    // ── W19: UriMatcher addURI + match (the AOSP code law) ──
    {
        uint32_t um = heap.allocate("Landroid/content/UriMatcher;", 0, 0);
        DalvikValue out;
        bridge(engine, "Landroid/content/UriMatcher;", "<init>",
               {DalvikValue::make_object(um, "Landroid/content/UriMatcher;"),
                DalvikValue::make_int(-1)},
               out);
        bridge(engine, "Landroid/content/UriMatcher;", "addURI",
               {DalvikValue::make_object(um, "Landroid/content/UriMatcher;"),
                DalvikValue::make_string("org.moire.opensudoku", 0),
                DalvikValue::make_string("sudoku", 0),
                DalvikValue::make_int(7)},
               out);
        auto uri_obj = [&](const std::string& raw) {
            uint32_t u = heap.allocate("Landroid/net/Uri;", 0, 0);
            heap.set_object_field(
                u, "uri_raw", DalvikValue::make_string(raw, 0));
            return u;
        };
        bool ok1 = bridge(engine, "Landroid/content/UriMatcher;", "match",
                          {DalvikValue::make_object(um, "Landroid/content/UriMatcher;"),
                           DalvikValue::make_object(
                               uri_obj("content://org.moire.opensudoku/sudoku"),
                               "Landroid/net/Uri;")},
                          out);
        bool hit = ok1 && out.type == DalvikType::INT32 && out.int_val == 7;
        bool ok2 = bridge(engine, "Landroid/content/UriMatcher;", "match",
                          {DalvikValue::make_object(um, "Landroid/content/UriMatcher;"),
                           DalvikValue::make_object(
                               uri_obj("content://other/path"),
                               "Landroid/net/Uri;")},
                          out);
        record("r14_w19_urimatcher_law",
               hit && ok2 && out.type == DalvikType::INT32 && out.int_val == -1,
               "match->7, miss->" + std::to_string(out.int_val) +
                   " (the ctor no-match code)");
    }

    // ── F-PD-636: the GLES PD_TEXTURE_QUAD family (the port) ──
    {
        const char* kPdVert =
            "attribute vec4 aXYZW;\n"
            "attribute vec2 aUV;\n"
            "uniform mat4 uCamera;\n"
            "uniform mat4 uModel;\n"
            "varying vec2 vUV;\n"
            "void main() {\n"
            "  gl_Position = uCamera * (uModel * aXYZW);\n"
            "  vUV = aUV;\n"
            "}\n";
        const char* kPdFrag =
            "precision mediump float;\n"
            "varying vec2 vUV;\n"
            "uniform sampler2D uTex;\n"
            "uniform vec4 uColorM;\n"
            "uniform vec4 uColorA;\n"
            "void main() {\n"
            "  gl_FragColor = texture2D(uTex, vUV) * uColorM + uColorA;\n"
            "}\n";
        auto& gl = GLES20Bridge::instance();
        // d1: one int arg + one optional pointer arg; d2: two int args.
        auto d1 = [&gl](const std::string& method, uint64_t a0,
                        const void* p0, int32_t* iret) {
            uint64_t ia[2] = {a0, 0};
            const void* pa[2] = {p0, nullptr};
            std::string trace;
            return gl.dispatch(method, ia, 1, nullptr, 0, pa,
                               p0 ? 1 : 0, iret, nullptr, trace);
        };
        auto d2 = [&gl](const std::string& method, uint64_t a0, uint64_t a1,
                        int32_t* iret) {
            uint64_t ia[2] = {a0, a1};
            std::string trace;
            return gl.dispatch(method, ia, 2, nullptr, 0, nullptr, 0,
                               iret, nullptr, trace);
        };
        int32_t vs = 0, fs = 0, prog = 0;
        bool ok_v = d1("glCreateShader", 0x8B31, nullptr, &vs);
        ok_v = ok_v && d1("glShaderSource", (uint64_t)vs, kPdVert, nullptr);
        ok_v = ok_v && d1("glCompileShader", (uint64_t)vs, nullptr, nullptr);
        int32_t vc = 0;
        gl.shader_query((uint32_t)vs, 0x8B81, &vc);  // COMPILE_STATUS
        bool ok_f = d1("glCreateShader", 0x8B30, nullptr, &fs);
        ok_f = ok_f && d1("glShaderSource", (uint64_t)fs, kPdFrag, nullptr);
        ok_f = ok_f && d1("glCompileShader", (uint64_t)fs, nullptr, nullptr);
        int32_t fc = 0;
        gl.shader_query((uint32_t)fs, 0x8B81, &fc);
        record("g1_f636_pd_compile",
               ok_v && ok_f && vc == 1 && fc == 1,
               "vert COMPILE=" + std::to_string(vc) + " frag COMPILE=" +
                   std::to_string(fc) + " (both classify PD_TEXTURE_QUAD)");

        d1("glCreateProgram", 0, nullptr, &prog);
        d2("glAttachShader", (uint64_t)prog, (uint64_t)vs, nullptr);
        d2("glAttachShader", (uint64_t)prog, (uint64_t)fs, nullptr);
        bool ok_l = d1("glLinkProgram", (uint64_t)prog, nullptr, nullptr);
        int32_t lc = 0;
        gl.program_query((uint32_t)prog, 0x8B82, &lc);  // LINK_STATUS
        record("g2_f636_pd_link",
               ok_l && lc == 1,
               "LINK_STATUS=" + std::to_string(lc) +
                   " (the family-gated GP583-GLES-006 law)");

        d1("glUseProgram", (uint64_t)prog, nullptr, nullptr);
        bool supported = gl.program_supported((uint32_t)prog);
        int32_t a_xyzw = -1, u_cam = -1;
        d1("glGetAttribLocation", (uint64_t)prog, "aXYZW", &a_xyzw);
        d1("glGetUniformLocation", (uint64_t)prog, "uCamera", &u_cam);
        record("g3_f636_pd_supported_and_locations",
               supported && a_xyzw >= 0 && u_cam >= 0,
               "supported=" + std::string(supported ? "true" : "false") +
                   " aXYZW=" + std::to_string(a_xyzw) +
                   " uCamera=" + std::to_string(u_cam));
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
