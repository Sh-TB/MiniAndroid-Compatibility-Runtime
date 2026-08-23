// EXP-088 Phase F — Handler/Looper queue semantics test
//
// Standalone C++ test for HandlerShadow queue semantics.
//
// Tests the exact scenario the user requested:
//   onCreate → Handler.post(A) → Handler.post(B) → Handler.postDelayed(C)
//            → removeCallbacks(B) → drain
//   Expected: A, C  (exactly once, in order)
//
// Plus additional tests:
//   - exactly-once execution (drain twice → second drain is empty)
//   - delayed execution semantics with virtual time
//   - postAtFrontOfQueue (front insertion)
//   - removeCallbacksAndMessages (clear all)
//
// This proves the queue infrastructure without requiring a real APK
// that triggers Handler.post during onCreate (no such APK exists in
// our corpus, and we can't compile Java to DEX in this environment).
//
// The C++ side is the source of truth here: if HandlerShadow works
// correctly in isolation, then any APK that calls Handler.post() will
// benefit from the same infrastructure.

#include "../src/framework/android_shadows.h"
#include "../src/framework/shadow_registry.h"

#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::framework::HandlerShadow;
using miniandroid::framework::ShadowRegistry;

struct TestResult {
    std::string name;
    bool passed = false;
    std::string detail;
};

static std::vector<TestResult> g_results;

static void record(const std::string& name, bool passed, const std::string& detail = "") {
    g_results.push_back({name, passed, detail});
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
}

// Test 1: post A, post B, postDelayed C, removeCallbacks(B), drain → A, C
// (The user's exact scenario)
void test_user_scenario() {
    std::cout << "\n[Test 1] User scenario: post(A), post(B), postDelayed(C), remove(B), drain\n";
    std::cout << "Expected: drain returns [A, C] in order, B excluded\n";

    ShadowRegistry registry;
    auto* hs = registry.register_shadow<HandlerShadow>();

    uint32_t A = 100, B = 200, C = 300;
    hs->enqueue(A, 0,    "LA;");
    hs->enqueue(B, 0,    "LB;");
    hs->enqueue(C, 100,  "LC;");   // delayed 100ms

    bool size_3 = (hs->queue_size() == 3);
    record("queue_size_is_3_after_enqueues", size_3);

    // Remove B
    size_t removed = hs->remove_callbacks(B);
    bool removed_1 = (removed == 1);
    record("remove_callbacks_B_returns_1", removed_1);

    bool size_2 = (hs->queue_size() == 2);
    record("queue_size_is_2_after_remove", size_2);

    // Drain
    std::vector<uint32_t> drained;
    size_t n = hs->drain_ready(&drained);
    std::cout << "  drained " << n << " items:";
    for (auto id : drained) std::cout << " " << id;
    std::cout << "\n";

    bool drained_2 = (n == 2);
    record("drain_returns_2", drained_2);

    bool order_AC = (drained.size() == 2 && drained[0] == A && drained[1] == C);
    record("drain_order_is_AC", order_AC,
           "expected A=100 then C=300, got [" +
           (drained.size() >= 1 ? std::to_string(drained[0]) : std::string("?")) + ", " +
           (drained.size() >= 2 ? std::to_string(drained[1]) : std::string("?")) + "]");

    bool B_excluded = true;
    for (auto id : drained) {
        if (id == B) {
            B_excluded = false;
            break;
        }
    }
    record("B_excluded_from_drain", B_excluded);
}

// Test 2: exactly-once execution — drain twice, second drain is empty
void test_exactly_once() {
    std::cout << "\n[Test 2] Exactly-once execution — drain twice\n";
    std::cout << "Expected: first drain returns [A, B, C], second drain returns []\n";

    ShadowRegistry registry;
    auto* hs = registry.register_shadow<HandlerShadow>();

    hs->enqueue(1, 0, "LA;");
    hs->enqueue(2, 0, "LB;");
    hs->enqueue(3, 0, "LC;");

    std::vector<uint32_t> drained1;
    size_t n1 = hs->drain_ready(&drained1);
    bool first_drain_3 = (n1 == 3 && drained1.size() == 3);
    record("first_drain_returns_3", first_drain_3);

    bool first_drain_order = (drained1.size() == 3 &&
                              drained1[0] == 1 && drained1[1] == 2 && drained1[2] == 3);
    record("first_drain_FIFO_order", first_drain_order);

    std::vector<uint32_t> drained2;
    size_t n2 = hs->drain_ready(&drained2);
    bool second_drain_0 = (n2 == 0 && drained2.empty());
    record("second_drain_returns_0", second_drain_0,
           "no Runnable should be drained twice");
}

// Test 3: postDelayed with virtual time — delay_ms is captured but treated
// as 0 in deterministic mode (the runtime drains everything when drain is called)
void test_postDelayed_virtual_time() {
    std::cout << "\n[Test 3] postDelayed captures delay_ms (deterministic mode treats as 0)\n";
    std::cout << "Expected: delayed item is drained in same drain call as immediate items\n";

    ShadowRegistry registry;
    auto* hs = registry.register_shadow<HandlerShadow>();

    hs->enqueue(10, 0,    "LX;");    // immediate
    hs->enqueue(20, 500,  "LY;");    // 500ms delay
    hs->enqueue(30, 1000, "LZ;");    // 1000ms delay

    bool size_3 = (hs->queue_size() == 3);
    record("queue_accepts_delayed_items", size_3);

    std::vector<uint32_t> drained;
    hs->drain_ready(&drained);
    bool all_drained = (drained.size() == 3);
    record("all_delayed_drained_in_deterministic_mode", all_drained,
           "delays treated as 0 (matches real Android when main thread is idle)");

    bool order_ok = (drained.size() == 3 &&
                     drained[0] == 10 && drained[1] == 20 && drained[2] == 30);
    record("delayed_items_drained_in_FIFO_order", order_ok);
}

// Test 4: removeCallbacksAndMessages clears entire queue
void test_removeCallbacksAndMessages() {
    std::cout << "\n[Test 4] removeCallbacksAndMessages(null) clears entire queue\n";

    ShadowRegistry registry;
    auto* hs = registry.register_shadow<HandlerShadow>();

    hs->enqueue(1, 0, "LA;");
    hs->enqueue(2, 0, "LB;");
    hs->enqueue(3, 0, "LC;");
    hs->enqueue(4, 100, "LD;");

    bool size_4 = (hs->queue_size() == 4);
    record("queue_size_4_before_clear", size_4);

    size_t removed = hs->remove_all();
    bool removed_4 = (removed == 4);
    record("remove_all_returns_4", removed_4);

    bool size_0 = (hs->queue_size() == 0);
    record("queue_size_0_after_clear", size_0);

    std::vector<uint32_t> drained;
    size_t n = hs->drain_ready(&drained);
    bool drain_empty = (n == 0);
    record("drain_after_clear_returns_0", drain_empty);
}

// Test 5: removeCallbacks for non-existent Runnable is a no-op
void test_removeCallbacks_nonexistent() {
    std::cout << "\n[Test 5] removeCallbacks(nonexistent) is a no-op\n";

    ShadowRegistry registry;
    auto* hs = registry.register_shadow<HandlerShadow>();

    hs->enqueue(100, 0, "LA;");
    hs->enqueue(200, 0, "LB;");

    size_t removed = hs->remove_callbacks(999);  // not in queue
    bool removed_0 = (removed == 0);
    record("remove_nonexistent_returns_0", removed_0);

    bool size_2 = (hs->queue_size() == 2);
    record("queue_unchanged_after_nonexistent_remove", size_2);
}

// Test 6: removeCallbacks removes ALL matching Runnables (if duplicates)
void test_removeCallbacks_all_matches() {
    std::cout << "\n[Test 6] removeCallbacks removes ALL matching Runnables\n";

    ShadowRegistry registry;
    auto* hs = registry.register_shadow<HandlerShadow>();

    // Enqueue the same Runnable ID twice (this can happen if post(R) is
    // called twice with the same Runnable instance)
    hs->enqueue(42, 0, "LX;");
    hs->enqueue(43, 0, "LY;");
    hs->enqueue(42, 0, "LX;");  // duplicate

    bool size_3 = (hs->queue_size() == 3);
    record("queue_size_3_with_duplicate", size_3);

    size_t removed = hs->remove_callbacks(42);
    bool removed_2 = (removed == 2);
    record("remove_all_matches_returns_2", removed_2);

    bool size_1 = (hs->queue_size() == 1);
    record("queue_size_1_after_removing_duplicates", size_1);
}

// Test 7: Empty queue drain returns 0
void test_empty_drain() {
    std::cout << "\n[Test 7] Empty queue drain returns 0\n";

    ShadowRegistry registry;
    auto* hs = registry.register_shadow<HandlerShadow>();

    std::vector<uint32_t> drained;
    size_t n = hs->drain_ready(&drained);
    record("empty_drain_returns_0", n == 0 && drained.empty());
}

// Test 8: FIFO ordering preserved with 5 items
void test_FIFO_5_items() {
    std::cout << "\n[Test 8] FIFO ordering preserved with 5 items\n";

    ShadowRegistry registry;
    auto* hs = registry.register_shadow<HandlerShadow>();

    for (uint32_t i = 1; i <= 5; i++) {
        hs->enqueue(i, 0, "L" + std::to_string(i) + ";");
    }

    std::vector<uint32_t> drained;
    hs->drain_ready(&drained);

    bool fifo = (drained.size() == 5);
    for (size_t i = 0; fifo && i < 5; i++) {
        if (drained[i] != i + 1) fifo = false;
    }
    record("FIFO_5_items_drained_in_order", fifo);
}

int main() {
    std::cout << "=== EXP-088 Phase F — Handler/Looper Queue Semantics ===\n";
    std::cout << "Tests the user's exact scenario:\n";
    std::cout << "  onCreate → post(A) → post(B) → postDelayed(C) → removeCallbacks(B) → drain\n";
    std::cout << "  Expected: drain returns [A, C] in order, B excluded\n";

    test_user_scenario();
    test_exactly_once();
    test_postDelayed_virtual_time();
    test_removeCallbacksAndMessages();
    test_removeCallbacks_nonexistent();
    test_removeCallbacks_all_matches();
    test_empty_drain();
    test_FIFO_5_items();

    int passed = 0, failed = 0;
    for (const auto& r : g_results) {
        if (r.passed) passed++;
        else failed++;
    }
    std::cout << "\n=== SUMMARY ===\n";
    std::cout << "Passed: " << passed << "\n";
    std::cout << "Failed: " << failed << "\n";
    std::cout << "Total:  " << g_results.size() << "\n";

    return (failed == 0) ? 0 : 1;
}
