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
        // [S192-C8] F-C8-161 — scheduled-executor factories.
        // OpenJDK (Executors.java): newScheduledThreadPool(n[,tf]) and
        // newSingleThreadScheduledExecutor([tf]) return a
        // ScheduledExecutorService (impl ScheduledThreadPoolExecutor).
        // The schedule surface rides the F-C8-150 deterministic-queue law
        // (dalvik_engine.cpp — keyed on ScheduledThreadPoolExecutor).
        // klondike + tower3d consume newScheduledThreadPool (2 APKs);
        // klondike consumes newSingleThreadScheduledExecutor (3 sites).
        if (m == "newScheduledThreadPool" ||
            m == "newSingleThreadScheduledExecutor") {
            if (!heap_) return CallResult::handled_null();
            int n = ctx.arg_as_int(0, 1);
            if (n < 0) {
                // OpenJDK: IllegalArgumentException on negative core.
                std::cerr << "[EXECUTOR][LAW-VIOLATION] " << m << "(" << n
                          << ") — AOSP throws IllegalArgumentException"
                          << std::endl;
                n = 0;
            }
            uint32_t id = heap_->get_or_create(
                "Ljava/util/concurrent/ScheduledThreadPoolExecutor;");
            ExecutorState& st = executors_[id];
            st.shutdown = false;
            st.tasks_submitted = 0;
            st.core_pool_size =
                (m == "newSingleThreadScheduledExecutor") ? 1 : n;
            std::cerr << "[EXECUTOR] " << m << " → ScheduledThreadPool"
                      << "Executor obj=" << id
                      << " core=" << st.core_pool_size << std::endl;
            return CallResult::handled_object(
                id,
                "Ljava/util/concurrent/ScheduledThreadPoolExecutor;");
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
                // F-C4-593 (W10, 4APP4 Coder-4) — EXECUTOR-THREAD IDENTITY
                // law. AOSP (java.util.concurrent.ThreadPoolExecutor): a
                // task submitted to a background executor runs on one of
                // the POOL'S worker threads — NEVER the main thread. The
                // engine's one-queue serialization stays, but the DELIVERY
                // IDENTITY is now the executor's own worker Thread object,
                // so inside every Executor.execute task:
                //   Thread.currentThread() != Looper.getMainLooper().getThread()
                // exactly like a real device. Live-proven root (Tusky
                // v33.1, the ×10 ISE family): Room's assertNotMainThread
                // (R8 Ln8/x;.a) ran `Looper.getMainLooper().getThread() ==
                // Thread.currentThread()` on executor-delivered query work
                // and threw "Cannot access database on the main thread
                // since it may potentially lock the UI for a long period
                // of time." at every WorkManager/Room query. Handler.post
                // on the main Looper keeps the F-NEW-289 main-identity law.
                uint32_t worker_tid = 0;
                if (heap_) {
                    // A FRESH Thread object per pool (NOT get_or_create —
                    // that answers the MAIN Thread singleton; the worker
                    // must be a distinct identity).
                    if (st.worker_thread_id == 0)
                        st.worker_thread_id =
                            heap_->allocate("Ljava/lang/Thread;");
                    worker_tid = st.worker_thread_id;
                }
                hs->enqueue_on_thread(runnable, /*delay_ms=*/0,
                                      "Ljava/util/concurrent/ThreadPoolExecutor;",
                                      worker_tid);
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
        // [S192-C8] F-C8-162 — ExecutorService.shutdownNow +
        // awaitTermination (OpenJDK laws). shutdownNow: attempts to stop
        // actively executing tasks, returns the list of tasks awaiting
        // execution (serialized engine: tasks ran INLINE at execute —
        // the list is EMPTY; JDK would drain the queue). awaitTermination(
        // timeout, unit): shutdown → true immediately (queue drained);
        // live pool → JDK blocks up to the timeout then answers false
        // (the engine advances the deterministic virtual clock by the
        // window — same time law as Thread.sleep).
        if (m == "shutdownNow") {
            st.shutdown = true;
            int drained = st.tasks_submitted;
            st.tasks_submitted = 0;
            uint32_t empty_list = 0;
            if (heap_)
                empty_list = heap_->allocate("Ljava/util/ArrayList;");
            std::cerr << "[EXECUTOR] shutdownNow obj=" << recv
                      << " (submitted=" << drained
                      << ") → empty await-list o" << empty_list
                      << " (serialized: tasks ran inline)" << std::endl;
            return CallResult::handled_object(empty_list,
                                              "Ljava/util/List;");
        }
        if (m == "awaitTermination") {
            if (st.shutdown) {
                std::cerr << "[EXECUTOR] awaitTermination obj=" << recv
                          << " → true (shutdown, queue drained)"
                          << std::endl;
                return CallResult::handled_bool(true);
            }
            // Timed window on a LIVE pool: JDK blocks then false. Advance
            // the deterministic virtual clock by the window (TimeUnit
            // ordinal law — NANOSECONDS=0..DAYS=6, F-NEW-216).
            int64_t amount = 0;
            if (!ctx.args.empty()) {
                if (ctx.args[0].kind == CallContext::Arg::Kind::LONG)
                    amount = ctx.args[0].long_val;
                else
                    amount = ctx.arg_as_int(0, 0);
            }
            int64_t ms = amount;  // MILLISECONDS default
            static const int64_t kDiv[7] = {1, 1, 1, 1000, 60000,
                                            3600000, 86400000};
            if (ctx.args.size() >= 2 && heap_ &&
                ctx.args[1].kind == CallContext::Arg::Kind::OBJECT) {
                int32_t ord = -1;
                if (heap_->get_object_int_field(ctx.args[1].object_id,
                                                "ordinal", ord) &&
                    ord >= 0 && ord < 7)
                    ms = amount * kDiv[ord];
            }
            if (auto* hs = registry_ ? registry_->find_as<HandlerShadow>()
                                     : nullptr)
                hs->advance_virtual(ms);
            std::cerr << "[EXECUTOR] awaitTermination obj=" << recv
                      << " → false after " << ms
                      << "ms (pool live — JDK blocks then false)"
                      << std::endl;
            return CallResult::handled_bool(false);
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
