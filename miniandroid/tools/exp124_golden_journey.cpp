// UNIFIED_007 EXP-124: GOLDEN_REAL_APP complete user journey.
//
// Runs the golden APK through the REAL runtime (Dalvik bytecode execution,
// in-runtime ARSC+AXML layout inflation, real listeners) and drives a
// user-like journey:
//
//   launch → screenshot → tap(Start) → screenshot → pump(timers) →
//   screenshot → tap(Reset) → screenshot → tap(Menu) → screenshot →
//   relaunch → screenshot
//
// Every step records: tap coordinate, hit-tested target (view id, class,
// handler invoked, instruction count), state deltas (texts), screenshot
// path + SHA-256, non-white pixel count.
//
// This is REAL application behavior: taps go through the engine's click
// dispatch (OnClickListener) or the XML android:onClick method invocation
// on the real Activity instance. No synthetic callbacks.

#include "apk/apk_parser.h"
#include "framework/android_shadows.h"
#include "framework/shadow_registry.h"
#include "renderer/view_renderer.h"
#include "resources/arsc_parser.h"
#include "runtime/execution_engine.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>

using namespace miniandroid;
using json = nlohmann::json;

namespace fs = std::filesystem;

static std::string sha256_of_file(const std::string& path) {
    // small helper: uses zlib-free double hash via std::hash is NOT crypto.
    // We shell out to sha256sum for real evidence integrity.
    std::string cmd = "sha256sum '" + path + "' 2>/dev/null | cut -d' ' -f1";
    FILE* p = popen(cmd.c_str(), "r");
    if (!p) return "";
    char buf[128] = {0};
    if (!fgets(buf, sizeof buf, p)) { pclose(p); return ""; }
    pclose(p);
    std::string s(buf);
    while (!s.empty() && (s.back() == '\n' || s.back() == '\r')) s.pop_back();
    return s;
}

// Drain the Handler queue: real postDelayed runnables (timers) execute.
static size_t pump_handlers(runtime::ExecutionEngine& engine, int max_iters = 12) {
    size_t total = 0;
    auto* reg = engine.registry();
    if (!reg) return 0;
    auto* hs = reg->find_as<framework::HandlerShadow>();
    if (!hs) return 0;
    for (int it = 0; it < max_iters; ++it) {
        std::vector<uint32_t> drained;
        size_t n = hs->drain_ready(&drained);
        if (n == 0) break;
        total += n;
        for (uint32_t rid : drained) {
            auto& heap = engine.dalvik().get_heap_public();
            if (!heap.has_object(rid)) continue;
            const auto* obj = heap.get(rid);
            std::string cls = obj ? obj->class_descriptor : "";
            if (cls.empty()) continue;
            dalvik::DalvikValue ret;
            dalvik::DalvikExecutionResult res;
            std::vector<dalvik::DalvikValue> args;
            args.push_back(dalvik::DalvikValue::make_object(rid, cls));
            engine.dalvik().try_recursive_invoke(cls, "run", args, ret, res);
        }
    }
    return total;
}

struct Step {
    std::string name;
    json record;
};

static json snapshot_texts(framework::ViewShadow* views) {
    json out = json::object();
    for (const auto& [id, node] : views->all_nodes()) {
        if (!node->text.empty())
            out[std::to_string(id)] = {{"class", node->class_desc},
                                       {"text", node->text}};
    }
    return out;
}

int main(int argc, char** argv) {
    std::string apk_path = argc > 1 ? argv[1] : "download/corpus/simplestopwatch.apk";
    std::string out_dir = argc > 2 ? argv[2] : "run_exp007/golden";
    int screen_w = argc > 3 ? std::atoi(argv[3]) : 1080;
    int screen_h = argc > 4 ? std::atoi(argv[4]) : 1920;
    fs::create_directories(out_dir);

    json report;
    report["experiment"] = "EXP-124 GOLDEN_REAL_APP complete user journey";
    report["apk"] = apk_path;
    report["apk_sha256"] = sha256_of_file(apk_path);
    report["screen"] = {screen_w, screen_h};
    std::vector<Step> steps;

    // ------------------------------------------------------------------
    // Step 0: LAUNCH — real bytecode execution + real layout inflation
    // ------------------------------------------------------------------
    framework::ShadowRegistry registry;
    auto* handler_shadow = registry.register_shadow<framework::HandlerShadow>();
    auto* view_shadow = registry.register_shadow<framework::ViewShadow>();
    auto* activity_shadow = registry.register_shadow<framework::ActivityShadow>();
    registry.register_shadow<framework::CollectionShadow>();
    activity_shadow->set_apk_path(apk_path);

    runtime::ExecutionEngine engine;
    engine.set_shadow_registry(&registry);
    runtime::ExecutionConfig config;
    config.output_directory = out_dir;
    config.screen_width = screen_w;
    config.screen_height = screen_h;
    (void)handler_shadow;

    auto result = engine.execute(apk_path, config);
    report["launch"] = {
        {"status", int(result.status)},
        {"api_calls", result.metrics.api_calls_count},
        {"errors", result.metrics.errors_count},
    };
    pump_handlers(engine);

    auto* views = registry.find_as<framework::ViewShadow>();
    if (!views || views->all_nodes().empty()) {
        std::cerr << "FATAL: no view tree after execution" << std::endl;
        report["fatal"] = "no view tree";
        std::ofstream f(out_dir + "/journey_report.json");
        f << report.dump(2);
        return 1;
    }

    // root = node with parent_id == 0 and the largest subtree
    uint32_t root = activity_shadow->content_view_id();
    if (!root || !views->find_node(root)) {
        for (const auto& [id, node] : views->all_nodes())
            if (node->parent_id == 0) root = id;
    }
    report["root_view_id"] = root;
    std::cerr << "[JOURNEY] root view id=" << root << std::endl;

    renderer::ViewRenderer vr(views, screen_w, screen_h);
    apk::ApkParser ap;
    ap.parse(apk_path);
    vr.preload_bitmaps(root, ap);
    vr.layout(root);

    auto shot = [&](const std::string& name, Step& s) {
        std::string path = out_dir + "/" + name;
        bool ok = vr.render_png(root, path, {0, 0, 0, 255});
        s.record["screenshot"] = name;
        s.record["screenshot_ok"] = ok;
        s.record["screenshot_sha256"] = sha256_of_file(path);
        s.record["nonwhite_pixels"] = vr.stats().nonwhite_pixels;
        s.record["stats"] = {{"laid_out", vr.stats().laid_out},
                             {"drawn", vr.stats().drawn},
                             {"images", vr.stats().images_drawn},
                             {"bg_bitmaps", vr.stats().bg_bitmaps_drawn},
                             {"bg_shapes", vr.stats().bg_shapes_drawn},
                             {"texts_shaped", vr.stats().texts_shaped},
                             {"texts_fallback", vr.stats().texts_bitmap_fallback}};
    };

    Step s0;
    s0.name = "01_launch";
    s0.record["action"] = "launch";
    shot("01_launch.png", s0);
    s0.record["layout"] = vr.layout_dump(root);
    steps.push_back(s0);
    json texts_before = snapshot_texts(views);

    // ------------------------------------------------------------------
    // Tap helper: coordinate → hit test → real dispatch
    // ------------------------------------------------------------------
    std::string activity_class;
    {
        apk::ApkParser info;
        auto ai = info.parse(apk_path);
        activity_class = ai.main_activity_full;
        if (!activity_class.empty() && activity_class[0] != 'L')
            activity_class = "L" + activity_class + ";";
        // DEX descriptors use slashes, not dots.
        std::replace(activity_class.begin(), activity_class.end(), '.', '/');
    }

    auto tap = [&](const std::string& label, const std::string& screenshot,
                   const std::string& match_text, const std::string& match_onclick,
                   int fallback_x, int fallback_y) {
        Step s;
        s.name = screenshot;
        if (match_text == "__pump_only__") {
            // no interaction: pump timers only, capture state
            size_t pumped = pump_handlers(engine);
            s.record["action"] = "pump";
            s.record["runnables_pumped"] = pumped;
            json texts_after = snapshot_texts(views);
            s.record["text_changes"] = json::array();
            for (const auto& [k, v] : texts_after.items()) {
                if (!texts_before.contains(k) || texts_before[k]["text"] != v["text"]) {
                    s.record["text_changes"].push_back(
                        {{"view", k}, {"before", texts_before.value(k, json::object()).value("text", "")},
                         {"after", v["text"]}});
                }
            }
            texts_before = texts_after;
            shot(screenshot, s);
            steps.push_back(s);
            std::cerr << "[JOURNEY] pump-only pumped=" << pumped << std::endl;
            return s;
        }
        // pick target: prefer on_click match, then text match, then fallback
        uint32_t target = 0;
        int tx = fallback_x, ty = fallback_y;
        for (const auto& [id, node] : views->all_nodes()) {
            if (node->visibility != 0) continue;
            if (!match_onclick.empty() && node->on_click_method == match_onclick) { target = id; break; }
            if (target == 0 && !match_text.empty() && node->text == match_text) target = id;
        }
        if (target == 0) target = vr.hit_test(root, tx, ty);
        if (target == 0) {
            s.record = {{"action", "tap"}, {"target", nullptr}, {"hit", false},
                        {"note", "no target found"}};
            steps.push_back(s);
            return s;
        }
        auto* n = views->find_node(target);
        int cx = n->x + n->width / 2, cy = n->y + n->height / 2;
        tx = cx; ty = cy;
        s.record["action"] = "tap";
        s.record["coordinate"] = {tx, ty};
        s.record["target"] = {{"view_id", target},
                              {"class", n->class_desc},
                              {"android_id", n->android_view_id},
                              {"text", n->text},
                              {"on_click_xml", n->on_click_method},
                              {"listener_class", n->click_listener_class}};
        // REAL dispatch path 1: engine click dispatch (OnClickListener)
        bool invoked = engine.dalvik().dispatch_click(target);
        s.record["dispatch_path"] = invoked ? "OnClickListener" : "";
        // REAL dispatch path 2: android:onClick method on the Activity
        // (walking the superclass chain — e.g. onButtonMenu lives on
        // simplestopwatch.ShowTime, the parent of StopWatch).
        if (!invoked && !n->on_click_method.empty()) {
            std::string cls = activity_class;
            for (int hop = 0; hop < 4 && !invoked && !cls.empty(); ++hop) {
                dalvik::DalvikValue ret;
                dalvik::DalvikExecutionResult res;
                std::vector<dalvik::DalvikValue> args;
                args.push_back(dalvik::DalvikValue::make_object(target, n->class_desc));
                invoked = engine.dalvik().try_recursive_invoke(
                    cls, n->on_click_method, args, ret, res);
                if (invoked) {
                    s.record["dispatch_class"] = cls;
                    s.record["insn_count"] = int(res.instruction_traces.size());
                }
                std::cerr << "[JOURNEY] onClick hop " << hop << " class=" << cls << " result=" << invoked << std::endl;
                cls = engine.dalvik().get_superclass(cls);
            }
            s.record["dispatch_path"] = "android:onClick:" + n->on_click_method;
        }
        s.record["callback_invoked"] = invoked;
        size_t pumped = pump_handlers(engine);
        s.record["runnables_pumped"] = pumped;
        json texts_after = snapshot_texts(views);
        s.record["text_changes"] = json::array();
        for (const auto& [k, v] : texts_after.items()) {
            if (!texts_before.contains(k) || texts_before[k]["text"] != v["text"]) {
                s.record["text_changes"].push_back(
                    {{"view", k}, {"before", texts_before.value(k, json::object()).value("text", "")},
                     {"after", v["text"]}});
            }
        }
        texts_before = texts_after;
        shot(screenshot, s);
        steps.push_back(s);
        std::cerr << "[JOURNEY] " << label << " target=" << target
                  << " (" << n->class_desc << ") invoked=" << invoked
                  << " pumped=" << pumped << std::endl;
        return s;
    };

    // Journey (real, user-like)
    Step s1 = tap("tap Start", "02_after_start_tap.png", "Start", "onButtonStart", 300, 1780);
    Step s2 = tap("pump+running shot", "03_running.png", "__pump_only__", "", 0, 0);
    Step s3 = tap("tap Reset", "04_after_reset_tap.png", "Reset", "onButtonReset", 780, 1780);
    Step s4 = tap("tap Menu", "05_after_menu_tap.png", "", "onButtonMenu", 980, 150);
    Step s5 = tap("tap Settings", "06_after_settings_tap.png", "", "onButtonSettings", 980, 60);

    // ------------------------------------------------------------------
    // Relaunch: fresh engine, same APK
    // ------------------------------------------------------------------
    {
        framework::ShadowRegistry reg2;
        reg2.register_shadow<framework::HandlerShadow>();
        auto* vs2 = reg2.register_shadow<framework::ViewShadow>();
        auto* act2 = reg2.register_shadow<framework::ActivityShadow>();
        reg2.register_shadow<framework::CollectionShadow>();
        act2->set_apk_path(apk_path);
        runtime::ExecutionEngine eng2;
        eng2.set_shadow_registry(&reg2);
        runtime::ExecutionConfig cfg2 = config;
        auto r2 = eng2.execute(apk_path, cfg2);
        pump_handlers(eng2);
        Step s;
        s.name = "07_relaunch";
        s.record["action"] = "relaunch";
        s.record["status"] = int(r2.status);
        uint32_t root2 = act2->content_view_id();
        if (!root2 || !vs2->find_node(root2))
            for (const auto& [id, node] : vs2->all_nodes())
                if (node->parent_id == 0) root2 = id;
        renderer::ViewRenderer vr2(vs2, screen_w, screen_h);
        vr2.preload_bitmaps(root2, ap);
        vr2.layout(root2);
        std::string path = out_dir + "/07_relaunch.png";
        bool ok = vr2.render_png(root2, path, {0, 0, 0, 255});
        s.record["screenshot"] = "07_relaunch.png";
        s.record["screenshot_ok"] = ok;
        s.record["screenshot_sha256"] = sha256_of_file(path);
        s.record["nonwhite_pixels"] = vr2.stats().nonwhite_pixels;
        s.record["matches_first_launch_sha"] =
            s.record["screenshot_sha256"] == steps[0].record["screenshot_sha256"];
        steps.push_back(s);
    }

    json arr = json::array();
    for (auto& s : steps) arr.push_back(s.record);
    report["steps"] = arr;
    std::ofstream f(out_dir + "/journey_report.json");
    f << report.dump(2) << std::endl;

    int shots_ok = 0;
    for (auto& s : steps)
        if (s.record.value("screenshot_ok", false)) shots_ok++;
    std::cout << "journey steps=" << steps.size()
              << " screenshots_ok=" << shots_ok << std::endl;
    return shots_ok >= 6 ? 0 : 1;
}
