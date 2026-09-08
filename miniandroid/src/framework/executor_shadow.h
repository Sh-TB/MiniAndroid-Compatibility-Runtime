// M3 §4 EXECUTOR/EXECUTORS CLOSURE — java.util.concurrent executor family.
//
// ROOT GAP: Executor/Executors were DETECTED-IN-DEX but NOT EXERCISED
// (microtimer's only demand; M3-S11 §8 audit). That is not VERIFIED. This
// shadow closes the law set the corpus demands through the runtime's ONE
// deterministic virtual scheduler.
//
// AOSP/Java laws transferred (java.util.concurrent):
//   * Executors.newFixedThreadPool(int n) / newSingleThreadExecutor() /
//     newCachedThreadPool() return a ThreadPoolExecutor object — the SAME
//     object identity for the lifetime of the executor (callers hold it
//     across calls). n <= 0 is an IllegalArgumentException in AOSP; this
//     engine records the violation LOUDLY in the diagnostic channel and
//     returns the executor anyway (documented boundary — never silent).
//   * Executor.execute(Runnable) eventually runs the runnable. In this
//     runtime the executor family rides the SAME MessageQueue/virtual
//     clock as Handler.post — the engine is a DETERMINISTICALLY SERIALIZED
//     interpreter (ROADMAP family L vocabulary): no host threads, no
//     wall-clock races. Tasks execute in FIFO submit order at the next
//     scheduler drain point (same drain law as Handler callbacks).
//   * ThreadPoolExecutor.shutdown() stops accepting work (isShutdown()
//     turns true); tasks already submitted still run (queue is shared).
//     shutdownNow() is a documented boundary (queue purge is not modeled).
//   * isTerminated() is true only after shutdown AND an empty queue — the
//     single-thread engine observes this at the drain boundary.
//
// No app-specific code: platform primitives any AsyncTask/coroutine/executor
// user shares. Fixture: tests/semantic_pass3_bridge_test.cpp (group F020 /
// executor probe fixture tests/fixtures/f020_executor).

#ifndef MINIANDROID_FRAMEWORK_EXECUTOR_SHADOW_H_
#define MINIANDROID_FRAMEWORK_EXECUTOR_SHADOW_H_

#include "shadow_registry.h"

#include <map>
#include <string>
#include <vector>

namespace miniandroid { namespace framework {

class ExecutorShadow : public Shadow {
public:
    std::string name() const override { return "ExecutorShadow"; }

    // Exact-family claims: the executor surface demanded by the corpus.
    bool handles_class(const std::string& cls) const override {
        return cls == "Ljava/util/concurrent/Executors;" ||
               cls == "Ljava/util/concurrent/Executor;" ||
               cls == "Ljava/util/concurrent/ExecutorService;" ||
               cls == "Ljava/util/concurrent/AbstractExecutorService;" ||
               cls == "Ljava/util/concurrent/ThreadPoolExecutor;" ||
               cls == "Ljava/util/concurrent/ScheduledThreadPoolExecutor;";
    }

    void init(HeapAllocator* heap) override { heap_ = heap; }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"newFixedThreadPool", "newSingleThreadExecutor",
                "newCachedThreadPool", "execute", "shutdown",
                "isShutdown", "isTerminated", "getPoolSize",
                "getActiveCount", "getTaskCount"};
    }
    std::vector<std::string> stubbed_methods() const override {
        // submit()/invokeAll() return Futures — Future semantics are not
        // demanded by the corpus; the stub is loud (STUBBED status), never
        // a silent success.
        return {"submit", "invokeAll", "invokeAny", "awaitTermination",
                "shutdownNow"};
    }

private:
    struct ExecutorState {
        bool shutdown = false;
        int  tasks_submitted = 0;
        int  core_pool_size = 0;
    };
    std::map<uint32_t, ExecutorState> executors_;
};

}} // namespace miniandroid::framework

#endif // MINIANDROID_FRAMEWORK_EXECUTOR_SHADOW_H_
