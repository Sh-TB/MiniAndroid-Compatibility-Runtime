// s241_compare_law_battery — the S241 wave rows:
//   r1/r2  the PORTED String.compareToIgnoreCase (equal-fold + length-diff)
//   r3     the regionMatches regression (the S240 port, post-rebase green)
// (the Gson TypeToken.get(null) IAE and the Conscrypt dlopen faces verified
//  macro/app-level — receipt-recorded, not forced into bridge rows.)
#include "../src/dex/dalvik_engine.h"

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
    std::cout << "== s241_compare_law_battery ==\n";
    (void)argc; (void)argv;
    DalvikExecutionEngine engine;

    // r1: "OpenSudoku".compareToIgnoreCase("opensudoku") == 0
    {
        DalvikValue out;
        bool ok = bridge(engine, "Ljava/lang/String;", "compareToIgnoreCase",
                         {DalvikValue::make_string("OpenSudoku", 0),
                          DalvikValue::make_string("opensudoku", 0)},
                         out);
        record("r1_compare_ignore_equal",
               ok && out.type == DalvikType::INT32 && out.int_val == 0,
               "fold-equal -> " + std::to_string(out.int_val) + " (expect 0)");
    }
    // r2: "abc".compareToIgnoreCase("ab") == 1 (the length-diff face)
    {
        DalvikValue out;
        bool ok = bridge(engine, "Ljava/lang/String;", "compareToIgnoreCase",
                         {DalvikValue::make_string("abc", 0),
                          DalvikValue::make_string("ab", 0)},
                         out);
        record("r2_compare_ignore_lengthdiff",
               ok && out.type == DalvikType::INT32 && out.int_val == 1,
               "len1-len2 -> " + std::to_string(out.int_val) + " (expect 1)");
    }
    // r3: the S240 regionMatches port still green (post-rebase regression)
    {
        DalvikValue out;
        bool ok = bridge(engine, "Ljava/lang/String;", "regionMatches",
                         {DalvikValue::make_string("OpenSudoku", 0),
                          DalvikValue::make_int(4),
                          DalvikValue::make_string("Sudoku", 0),
                          DalvikValue::make_int(0),
                          DalvikValue::make_int(4)},
                         out);
        record("r3_region_matches_regression",
               ok && out.type == DalvikType::BOOLEAN && out.bool_val,
               "the S240 port green");
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
