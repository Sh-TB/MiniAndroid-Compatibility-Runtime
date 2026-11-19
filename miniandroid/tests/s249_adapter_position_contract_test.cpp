// s249_adapter_position_contract_test — W20-K (S237-WS6, independent coder
// cODER-ohc): AOSP AdapterView position accessor law (@android-14
// AdapterView.java L808-818 + Adapter.java L72):
//   getItemIdAtPosition returns LONG; a negative position answers
//   INVALID_ROW_ID = Long.MIN_VALUE — never INT32, never 0 (0 aliases
//   row 0's id and defeats the sentinel contract).
// Bridge-level contract through the REAL dispatch the DEX call reaches.
#include "../src/dex/dalvik_engine_impl.h"
#include "../src/framework/android_shadows.h"

#include <cstdint>
#include <iostream>
#include <limits>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikType;
using miniandroid::dalvik::DalvikValue;
using miniandroid::framework::ShadowRegistry;
using miniandroid::framework::ViewShadow;

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) ++g_pass; else ++g_fail;
}

int main() {
    std::cout << "== s249_adapter_position_contract ==\n";
    DalvikExecutionEngine engine;
    ShadowRegistry registry;
    auto* vs = registry.register_shadow<ViewShadow>();
    engine.set_shadow_registry(&registry);
    if (!vs) {
        record("s249_setup_viewshadow", false, "registry/ViewShadow missing");
        std::cout << "== " << g_pass << " passed / " << g_fail
                  << " failed ==\n";
        return 1;
    }
    // Real ListView node + a bound ArrayAdapter identity (the setAdapter law
    // shape: node.adapter_id != 0 is what the F-NEW-649 arm keys on).
    auto& heap = engine.get_heap_public();
    uint32_t lv = heap.allocate("Landroid/widget/ListView;", 0, 0);
    uint32_t ad = heap.allocate("Landroid/widget/ArrayAdapter;", 0, 0);
    auto* n = vs->get_or_create_node(lv, "Landroid/widget/ListView;");
    n->adapter_id = ad;
    n->adapter_class = "Landroid/widget/ArrayAdapter;";

    auto call = [&](const std::string& m, int32_t pos, DalvikValue& out) {
        miniandroid::dalvik::ApiCallTrace::Status st =
            miniandroid::dalvik::ApiCallTrace::Status::STUBBED;
        std::vector<DalvikValue> args;
        args.push_back(DalvikValue::make_object(lv, "Landroid/widget/ListView;"));
        args.push_back(DalvikValue::make_int(pos));
        return engine.bridge_to_api("Landroid/widget/ListView;", m, args,
                                    out, st, 0);
    };

    {
        DalvikValue out;
        bool ok = call("getItemIdAtPosition", 2, out);
        record("ws6_positive_is_long",
               ok && out.type == DalvikType::INT64 && out.long_val == 2,
               "getItemIdAtPosition(2) → INT64 2 (was INT32)");
    }
    {
        DalvikValue out;
        bool ok = call("getItemIdAtPosition", -1, out);
        record("ws6_negative_is_invalid_row_id",
               ok && out.type == DalvikType::INT64 &&
                   out.long_val == std::numeric_limits<int64_t>::min(),
               "getItemIdAtPosition(-1) → INT64 Long.MIN_VALUE (was INT32 0)");
    }
    {
        DalvikValue out;
        bool ok = call("getItemAtPosition", -1, out);
        // AOSP: answers null — the DalvikValue null encoding may be a
        // typed-null (OBJECT_REF with oid 0) or an explicit NULL kind;
        // the CONTRACT is the null answer (oid 0), matching make_null().
        record("ws6_negative_item_is_null",
               ok && out.object_id == 0,
               "getItemAtPosition(-1) → null (oid 0)");
    }
    {
        DalvikValue out;
        bool ok = call("getAdapter", 0, out);
        record("ws6_getadapter_identity",
               ok && out.type == DalvikType::OBJECT_REF &&
                   out.object_id == ad,
               "getAdapter() → the bound adapter obj#" + std::to_string(ad));
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
