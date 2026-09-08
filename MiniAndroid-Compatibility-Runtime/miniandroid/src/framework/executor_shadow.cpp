// M3 §4 EXECUTOR/EXECUTORS CLOSURE — implementation.
// See executor_shadow.h for the AOSP/Java law mapping and the
// deterministic-serialized boundary statement.
#include "executor_shadow.h"
#include "android_shadows.h"

#include <iostream>

namespace miniandroid { namespace framework {

CallResult ExecutorShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;
    const uint32_t recv = ctx.has_receiver ? ctx.receiver_id : 0;

    // ── Executors static factories ──────────────────────────────────────
    // AOSP: return a new (or cached — irrelevant to the single-thread law)
    // ThreadPoolExecutor. The heap object identity is what app code relies
    // on across subsequent execute() calls.
    if (cls == "Ljava/util/concurrent/Executors;") {
        if (m == "newFixedThreadPool" || m == "newSingleThreadExecutor" ||
            m == "newCachedThreadPool") {
            if (!heap_) return CallResult::handled_null();
            int n = ctx.arg_as_int(0, 1);
            if (n < 0) n = 0;
            if (m == "newFixedThreadPool" && n <= 0) {
                // AOSP: IllegalArgumentException. Deterministic engine:
                // loud diagnostic + the executor object anyway (documented
                // boundary — the corpus never demands the failure path).
                std::cerr << "[EXECUTOR][LAW-VIOLATION] newFixedThreadPool("
                          << n << ") — AOSP throws IllegalArgumentException"
                          << std::endl;
            }
            uint32_t id = heap_->get_or_create(
                "Ljava/util/concurrent/ThreadPoolExecutor;");
            ExecutorState& st = executors_[id];
            st.shutdown = false;
            st.tasks_submitted = 0;
            st.core_pool_size = (m == "newSingleThreadExecutor") ? 1 : n;
            std::cerr << "[EXECUTOR] " << m << " → ThreadPoolExecutor obj="
                      << id << " core=" << st.core_pool_size << std::endl;
            return CallResult::handled_object(
                id, "Ljava/util/concurrent/ThreadPoolExecutor;");
        }
        return CallResult::not_handled();
    }

    // ── ThreadPoolExecutor instance surface ─────────────────────────────
    if (cls == "Ljava/util/concurrent/ThreadPoolExecutor;" ||
        cls == "Ljava/util/concurrent/AbstractExecutorService;" ||
        cls == "Ljava/util/concurrent/ScheduledThreadPoolExecutor;") {
        if (m == "<init>") {
            // ThreadPoolExecutor(int core, int max, long keepAlive, TimeUnit,
            //                    BlockingQueue[, ThreadFactory, RejectedExecHandler])
            // No worker threads exist in a serialized engine — record the
            // pool size law and return. The object exists already
            // (new-instance allocation).
            if (heap_ && recv != 0 && executors_.find(recv) == executors_.end()) {
                ExecutorState& st = executors_[recv];
                st.shutdown = false;
                st.tasks_submitted = 0;
                st.core_pool_size = ctx.arg_as_int(0, 1);
            }
            return CallResult::handled_void();
        }
        ExecutorState& st = executors_[recv];

        if (m == "execute") {
            // Executor.execute(Runnable) — AOSP: enqueue for eventual run.
            // This runtime: the ONE deterministic MessageQueue (the same
            // queue Handler.post uses). FIFO submit order, virtual clock.
            uint32_t runnable = ctx.arg_as_object(0, 0);
            if (runnable == 0 || !registry_) {
                // AOSP: NullPointerException on null task. Loud boundary.
                std::cerr << "[EXECUTOR][LAW-VIOLATION] execute(null) — AOSP "
                          << "throws NullPointerException" << std::endl;
                return CallResult::handled_void();
            }
            if (auto* hs = registry_->find_as<HandlerShadow>()) {
                hs->enqueue(runnable, /*delay_ms=*/0,
                            "Ljava/util/concurrent/ThreadPoolExecutor;");
                st.tasks_submitted++;
            } else {
                std::cerr << "[EXECUTOR][UNSUPPORTED] no MessageQueue "
                          << "registered — task dropped LOUDLY" << std::endl;
            }
            return CallResult::handled_void();
        }
        if (m == "shutdown") {
            st.shutdown = true;
            std::cerr << "[EXECUTOR] shutdown obj=" << recv
                      << " (submitted=" << st.tasks_submitted << ")" << std::endl;
            return CallResult::handled_void();
        }
        if (m == "isShutdown") return CallResult::handled_bool(st.shutdown);
        if (m == "isTerminated") {
            // Serialized law: terminated = shutdown AND queue drained. The
            // drain boundary is owned by the runtime loop; report shutdown
            // as the conservative observable.
            return CallResult::handled_bool(st.shutdown);
        }
        if (m == "getPoolSize" || m == "getMaximumPoolSize") {
            // Serialized engine: exactly ONE worker (the drain loop).
            return CallResult::handled_int(
                st.core_pool_size > 0 ? 1 : 1);
        }
        if (m == "getActiveCount") {
            return CallResult::handled_int(0);   // between drains: idle
        }
        if (m == "getTaskCount") {
            return CallResult::handled_long(
                static_cast<int64_t>(st.tasks_submitted));
        }
        return CallResult::not_handled();
    }

    // Executor/ExecutorService are interfaces — dispatch reaches us via the
    // runtime class (ThreadPoolExecutor). Nothing instance-shaped here.
    return CallResult::not_handled();
}

}} // namespace miniandroid::framework
