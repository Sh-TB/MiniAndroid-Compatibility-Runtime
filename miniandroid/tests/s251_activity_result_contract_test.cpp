// s251_activity_result_contract_test — W20-K (S237-WS8, independent coder
// cODER-ohc): AOSP Activity result-delivery law (@android-14 Activity.java
// L766/L953/L956): mResultCode is a DEFAULT (RESULT_CANCELED), not an
// "unset" sentinel — finish() of a child launched for a result delivers
// (RESULT_CANCELED, null Intent) even when setResult was never called;
// delivery is one-shot.
// Shadow-level contract on the EXACT state consume_finish_cascade consumes.
#include "../src/framework/android_shadows.h"

#include <iostream>
#include <string>

using miniandroid::framework::ActivityShadow;

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) ++g_pass; else ++g_fail;
}

int main() {
    std::cout << "== s251_activity_result_contract ==\n";
    ActivityShadow as;

    // row 1: NO setResult → take_result still delivers the AOSP default.
    {
        int rc = -777;
        uint32_t data = 0xdeadbeef;
        bool delivered = as.take_result(&rc, &data);
        record("ws8_unset_delivers_canceled",
               delivered && rc == 0 && data == 0,
               "delivered=1 rc=0(RESULT_CANCELED) data=0(null)");
    }
    // row 2: setResult(RESULT_OK, intent) → delivered verbatim.
    {
        as.set_result(-1, 4242);
        int rc = 0;
        uint32_t data = 0;
        bool delivered = as.take_result(&rc, &data);
        record("ws8_set_ok_delivers_ok_and_data",
               delivered && rc == -1 && data == 4242,
               "delivered=1 rc=-1(RESULT_OK) data=obj#4242");
    }
    // row 3: one-shot law — the second take answers the default again.
    {
        int rc = -1;
        uint32_t data = 4242;
        as.take_result(&rc, &data);
        bool second = as.take_result(&rc, &data);
        record("ws8_take_is_one_shot",
               second && rc == 0 && data == 0,
               "second take → default CANCELED (slot cleared)");
    }
    // row 4: has_result() is evidence-only (delivery no longer gates on it).
    {
        as.set_result(5, 0);
        bool before = as.has_result();
        int rc = 0;
        uint32_t data = 0;
        as.take_result(&rc, &data);
        record("ws8_has_result_evidence_only",
               before && rc == 5 && !as.has_result(),
               "has_result true before, cleared after (rc=5 delivered)");
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
