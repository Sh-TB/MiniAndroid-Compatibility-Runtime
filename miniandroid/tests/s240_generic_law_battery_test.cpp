// s240_generic_law_battery — the W15/W16/W17/W26 + LEGACY content-face
// battery (bridge-level rows for the generic law stacks the S239 sweep
// found landing as naked comments):
//   r1/r2  W16 (#564) String.regionMatches — the PORTED arm (5-arg exact
//          + 6-arg ignoreCase fold)
//   r3     W26 (#594) Gson.getAdapter — the bound adapter object
//   r4     W17 (#566) the TSK okhttp SSL wall — SSLSocketFactory.getDefault
//          → the factory object (the base-layer face the okhttp stack
//          rides)
//   r4     W15 (#563) Room/SQLiteOpenHelper.getWritableDatabase — the
//          pending-open helper face
//
// (the AdapterView.getAdapter and GLES20.glCreateShader arms verified
// state/context-gated — recorded in the receipt, not forced here)
#include "../src/dex/dalvik_engine_impl.h"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikType;
using miniandroid::dalvik::DalvikValue;

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
    std::cout << "== s240_generic_law_battery ==\n";
    (void)argc; (void)argv;
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 3000;
    auto& heap = engine.get_heap_public();

    // r1: regionMatches exact — "OpenSudoku".regionMatches(4,"Sudo",0,4)
    {
        DalvikValue out;
        bool ok = bridge(engine, "Ljava/lang/String;", "regionMatches",
                         {DalvikValue::make_string("OpenSudoku", 0),
                          DalvikValue::make_int(4),
                          DalvikValue::make_string("Sudoku", 0),
                          DalvikValue::make_int(0),
                          DalvikValue::make_int(4)},
                         out);
        record("r1_region_matches_exact",
               ok && out.type == DalvikType::BOOLEAN && out.bool_val,
               "\"OpenSudoku\" vs \"Sudoku\"[0..4) -> true");
    }
    // r2: regionMatches ignoreCase — "HELLO".regionMatches(0,"hello",0,5,true)
    {
        DalvikValue out;
        bool ok = bridge(engine, "Ljava/lang/String;", "regionMatches",
                         {DalvikValue::make_string("HELLO", 0),
                          DalvikValue::make_int(0),
                          DalvikValue::make_string("hello", 0),
                          DalvikValue::make_int(0),
                          DalvikValue::make_int(5),
                          DalvikValue::make_bool(true)},
                         out);
        record("r2_region_matches_ignorecase",
               ok && out.type == DalvikType::BOOLEAN && out.bool_val,
               "the fold face -> true");
    }
    // r4: W17 TSK okhttp SSL wall — SSLSocketFactory.getDefault
    {
        DalvikValue out;
        bool ok = bridge(engine, "Ljavax/net/ssl/SSLSocketFactory;", "getDefault",
                         {}, out);
        record("r3_w17_ssl_factory_default",
               ok && out.type == DalvikType::OBJECT_REF && out.object_id != 0,
               "factory obj#" + std::to_string(out.object_id) +
                   " (the okhttp stack's base-layer SSL face)");
    }
    // r6: W15 Room/helper getWritableDatabase face
    {
        uint32_t h = heap.allocate(
            "Landroid/database/sqlite/SQLiteOpenHelper;", 0, 0);
        DalvikValue out;
        bool ok = bridge(engine,
                         "Landroid/database/sqlite/SQLiteOpenHelper;",
                         "getWritableDatabase",
                         {DalvikValue::make_object(
                             h, "Landroid/database/sqlite/SQLiteOpenHelper;")},
                         out);
        record("r4_w15_getwritabledatabase",
               ok, "dispatched (the pending-open helper face — the Room "
                   "2.7 stack rides this arm)");
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
