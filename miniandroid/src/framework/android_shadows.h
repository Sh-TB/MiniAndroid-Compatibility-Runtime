// SPDX-License-Identifier: MIT
// MiniAndroid Compatibility Runtime
// EXP-051 — Concrete Android framework shadows
//
// Shadows implemented in this file:
//   * ThreadShadow       — single deterministic main Thread
//   * LooperShadow       — single deterministic main Looper bound to main Thread
//   * HandlerShadow      — single-thread Runnable queue with post/postDelayed
//   * ActivityShadow     — current Activity tracking + lifecycle state
//   * IntentShadow       — Intent creation, component resolution, startActivity
//   * ViewShadow         — minimal View/ViewGroup hierarchy
//
// All shadows share a single-threaded execution model. There is exactly
// one main Thread object, one main Looper object, and one main Handler
// object — all with the same heap object_id so that
//     Looper.getMainLooper().getThread() == Thread.currentThread()
// returns true, which is what ArchTaskExecutor.isMainThread() actually
// checks.

#ifndef MINIANDROID_FRAMEWORK_ANDROID_SHADOWS_H
#define MINIANDROID_FRAMEWORK_ANDROID_SHADOWS_H

#include "shadow_registry.h"

#include <chrono>
#include <deque>
#include <atomic>
#include <iostream>
#include <cstdlib>
#include <map>
#include <set>
#include <memory>
#include <string>
#include <climits>
#include <vector>

namespace miniandroid { namespace framework {

// ─────────────────────────────────────────────────────────────────────────
// ArchTaskExecutorShadow — handles ArchTaskExecutor.isMainThread.
//
// Real ArchTaskExecutor.isMainThread delegates to mDelegate.isMainThread()
// which (for DefaultTaskExecutor) does:
//   return Looper.getMainLooper().getThread() == Thread.currentThread();
//
// In our model, both sides return the same canonical main Thread object_id
// (bound by ThreadShadow and LooperShadow at init). So isMainThread() is
// always true in the single-threaded runtime.
//
// We do NOT short-circuit the bytecode via a legacy bridge stub — instead,
// we register a Shadow that the bridge consults FIRST. This keeps the
// architecture clean: shadows handle Android framework behavior, the
// engine executes bytecode.
//
// This shadow handles:
//   * ArchTaskExecutor.isMainThread → true (the delegate check)
//   * ArchTaskExecutor.getInstance → singleton ArchTaskExecutor object
//   * ArchTaskExecutor.executeOnDiskIO → no-op (post to disk thread)
//   * ArchTaskExecutor.postToMainThread → enqueue via HandlerShadow
// ─────────────────────────────────────────────────────────────────────────
class ArchTaskExecutorShadow : public Shadow {
public:
    std::string name() const override { return "ArchTaskExecutor"; }
    void init(HeapAllocator* heap) override {
        heap_ = heap;
        if (heap_) {
            instance_id_ = heap_->get_or_create("Landroidx/arch/core/executor/ArchTaskExecutor;");
        }
    }

    bool handles_class(const std::string& class_name) const override {
        return class_name.find("ArchTaskExecutor") != std::string::npos ||
               class_name.find("DefaultTaskExecutor") != std::string::npos ||
               class_name.find("TaskExecutor") != std::string::npos;
    }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"isMainThread", "getInstance", "executeOnDiskIO",
                "postToMainThread"};
    }
    std::vector<std::string> stubbed_methods() const override {
        return {"delegate", "setDelegate"};
    }

    uint32_t instance_id() const { return instance_id_; }

private:
    uint32_t instance_id_ = 0;
};

// ─────────────────────────────────────────────────────────────────────────
// ThreadShadow — owns the single main Thread object.
//
// Identity contract:
//   * Thread.currentThread() returns main_thread_id_ always.
//   * Thread.equals(Object) returns true iff the other object_id is
//     main_thread_id_ (mimics reference equality).
//   * Thread.getId() returns MAIN_THREAD_ID = 1.
//   * Thread.getName() returns "main".
//   * Thread.getStackTrace() returns an empty array (unblocks Intrinsics).
//
// The main_thread_id_ is allocated lazily on first init() call.
// ─────────────────────────────────────────────────────────────────────────
class ThreadShadow : public Shadow {
public:
    static constexpr uint32_t MAIN_THREAD_TID = 1;
    static constexpr const char* MAIN_THREAD_NAME = "main";

    std::string name() const override { return "Thread"; }
    void init(HeapAllocator* heap) override {
        heap_ = heap;
        if (heap_) {
            // Allocate (or look up) the main Thread singleton up-front.
            // We do NOT cache the ID locally yet because get_or_create
            // is idempotent — every later call to currentThread() will
            // return the same heap object.
            main_thread_id_ = heap_->get_or_create("Ljava/lang/Thread;");
        }
    }

    bool handles_class(const std::string& class_name) const override {
        return class_name == "Ljava/lang/Thread;";
    }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"currentThread", "getName", "getId", "getStackTrace",
                "isAlive", "isDaemon", "interrupt"};
    }
    std::vector<std::string> stubbed_methods() const override {
        return {"sleep", "yield", "join", "start", "run", "setDaemon"};
    }

    // Public accessor: returns the canonical main Thread object_id.
    uint32_t main_thread_id() const { return main_thread_id_; }

    // Public mutator: allows the LooperShadow to bind to the same id.
    void set_main_thread_id(uint32_t id) { main_thread_id_ = id; }

    // ── F-110d (S62+): CURRENT-THREAD IDENTITY LAW ─────────────────────
    // AOSP Thread.currentThread() returns the thread object of the thread
    // EXECUTING the code — not a fixed main singleton. The serialized
    // engine runs a drained thread's run() body run-to-completion on the
    // single virtual thread; while such a body is active, currentThread()
    // must return THAT thread's heap object (first real hit: anuto
    // GameLoop.isThreadChangeNeeded gates every GameEngine.post through
    // Thread.currentThread() != mGameThread — with the main singleton
    // returned, the app's own game-thread handoff re-posted loadMap
    // forever and the message queue never drained). The engine sets this
    // for the duration of a drained body (save/restore, nested-safe).
    void set_active_drained_thread(uint32_t oid) { active_drained_thread_ = oid; }
    uint32_t current_thread_id() const {
        return active_drained_thread_ != 0 ? active_drained_thread_ : main_thread_id_;
    }

    // ── M3 F-THREAD-TICK: deterministic virtual-thread law ────────────────
    // Thread.<init>(Runnable[, ...]) records the thread's target Runnable.
    // Thread.start() (or run()) marks a pending inline execution; the ENGINE
    // consumes the pending start right after the dispatch and invokes the
    // target's run() to completion on the virtual main thread (single
    // deterministic thread — no wall-clock, no real concurrency, same
    // observable order as a background worker that finishes before the next
    // main-frame boundary). Never a fake callback: the run() body is the
    // APK's REAL DEX bytecode.
    void record_target(uint32_t thread_oid, uint32_t runnable_oid) {
        if (thread_oid && runnable_oid) runnables_[thread_oid] = runnable_oid;
    }
    bool has_pending_starts() const { return !pending_starts_.empty(); }
    // Pops one pending (thread, runnable) pair. Returns false when drained.
    bool consume_pending_start(uint32_t& thread_oid, uint32_t& runnable_oid) {
        if (pending_starts_.empty()) return false;
        auto front = pending_starts_.front();
        pending_starts_.erase(pending_starts_.begin());
        thread_oid = front.first;
        runnable_oid = front.second;
        return true;
    }
    // F-150 (S72-W4): YIELDED-THREAD REGISTRY. A drained thread body that
    // hit Thread.sleep unwound at the yield point (F-110b law) — AOSP
    // semantics: the thread is BLOCKED on sleep, not dead; it resumes when
    // the sleep elapses. The engine's deterministic counterpart: the body
    // re-drains at the first scheduler boundary whose virtual time reached
    // the recorded WAKE time (now + sleep-ms). Threads whose body completed
    // WITHOUT yielding (loop exit / return) are NOT in this set and never
    // re-drain. The recorded value is (run-target, wake_at_ms) so
    // (Runnable)-ctor threads re-drain their TARGET body, not the
    // framework Thread.run.
    void mark_thread_yielded(uint32_t thread_oid, uint32_t target_oid,
                             int64_t wake_at_ms) {
        if (thread_oid)
            yielded_threads_[thread_oid] = {target_oid ? target_oid
                                                       : thread_oid,
                                            wake_at_ms};
    }
    void clear_thread_yielded(uint32_t thread_oid) {
        yielded_threads_.erase(thread_oid);
    }
    // Pops the earliest-wake due thread (deterministic order law). Returns
    // false when nothing is due at now_ms.
    bool take_due_yielded(int64_t now_ms, uint32_t& thread_oid,
                          uint32_t& target_oid) {
        bool found = false;
        uint32_t best_oid = 0;
        int64_t best_wake = 0;
        for (const auto& [oid, entry] : yielded_threads_) {
            if (entry.second > now_ms) continue;
            if (!found || entry.second < best_wake) {
                found = true;
                best_oid = oid;
                best_wake = entry.second;
            }
        }
        if (!found) return false;
        thread_oid = best_oid;
        target_oid = yielded_threads_[best_oid].first;
        yielded_threads_.erase(best_oid);
        return true;
    }

private:
    uint32_t main_thread_id_ = 0;
    std::map<uint32_t, uint32_t> runnables_;              // thread → target
    std::vector<std::pair<uint32_t, uint32_t>> pending_starts_;
    std::map<uint32_t, std::pair<uint32_t, int64_t>> yielded_threads_;
    uint32_t active_drained_thread_ = 0;  // F-110d: 0 = main thread
};

// ─────────────────────────────────────────────────────────────────────────
// RuntimeShadow (F-141 chain, S72-W3) — java.lang.Runtime minimal semantic
// subset per the OpenJDK law (Runtime.java):
//   * private static final Runtime currentRuntime = new Runtime();
//   * public static Runtime getRuntime() { return currentRuntime; }
// The singleton identity is part of the contract: every getRuntime() call
// returns the SAME heap object, and instance methods run on it.
//   * availableProcessors(): OpenJDK/ART return the VM's usable core count.
//     kotlinx.coroutines sizes Dispatchers.Default with it during <clinit>
//     (dooz: Lxr1;.<clinit> invoke-virtual Runtime.availableProcessors on
//     the getRuntime() result). Engine device profile: FIXED core count
//     (deterministic run ×3 law, §121) — default 4, MINIANDROID_CORES env
//     override for controlled probes only.
// Evidence: dooz S72-W3 — getRuntime() fell through to the generic stub and
// returned null; the F-141 null-receiver NPE law fired at Lxr1;.<clinit>
// pc=4 ("Attempt to invoke virtual method '...Runtime;.availableProcessors'
// on a null object reference"), unwinding the os.get → vs/vx/kv/gt1
// <clinit> chain out of MainActivity.onCreate (the real first divergence
// chain, previously masked by the silent null-receiver dispatch).
// ─────────────────────────────────────────────────────────────────────────
class RuntimeShadow : public Shadow {
public:
    std::string name() const override { return "Runtime"; }
    void init(HeapAllocator* heap) override {
        heap_ = heap;
        // OpenJDK law: the singleton exists once, at class initialization.
        if (heap_) runtime_id_ = heap_->get_or_create("Ljava/lang/Runtime;");
    }
    bool handles_class(const std::string& class_name) const override {
        return class_name == "Ljava/lang/Runtime;";
    }
    CallResult dispatch(const CallContext& ctx) override;
    std::vector<std::string> implemented_methods() const override {
        return {"getRuntime", "availableProcessors"};
    }
    std::vector<std::string> stubbed_methods() const override {
        return {"gc", "exit", "halt", "totalMemory", "freeMemory", "maxMemory"};
    }
    uint32_t runtime_id() const { return runtime_id_; }
private:
    HeapAllocator* heap_ = nullptr;
    uint32_t runtime_id_ = 0;
};

// ────────────────────────────────────────────────────────────────────────
// FragmentManagerShadow (F-141c, S72-W3) — android.app.FragmentManager /
// FragmentTransaction minimal semantic subset per AOSP
// (FragmentManager.java / BackStackRecord.java):
//   * findFragmentByTag/Id: answers the fragment committed under that
//     identity — the runtime's fragment registry starts EMPTY, so the
//     honest answer is null (the androidx LifecycleDispatcher contract:
//     null → install the report fragment via beginTransaction).
//   * beginTransaction(): a NEW FragmentTransaction object per call
//     (AOSP: new BackStackRecord(this)).
//   * FragmentTransaction ops (add/replace/remove/hide/show/detach/
//     attach) return the SAME transaction object (fluent this).
//   * commit()/commitAllowingStateLoss() → int id; commitNow* → void.
//   * executePendingTransactions() → true (pending ops ran now).
// Evidence: dooz androidx LifecycleDispatcher report-fragment install
// (im.onCreate → mc1.b → getFragmentManager → findFragmentByTag null →
// beginTransaction().add(new ReportFragment(), tag).commit() →
// executePendingTransactions()); the null getFragmentManager answer
// fired the F-141 NPE law and killed the activity chain.
// ────────────────────────────────────────────────────────────────────────
class FragmentManagerShadow : public Shadow {
public:
    std::string name() const override { return "FragmentManager"; }
    void init(HeapAllocator* heap) override { heap_ = heap; }
    bool handles_class(const std::string& class_name) const override {
        return class_name == "Landroid/app/FragmentManager;" ||
               class_name == "Landroid/app/FragmentTransaction;";
    }
    CallResult dispatch(const CallContext& ctx) override;
    std::vector<std::string> implemented_methods() const override {
        return {"findFragmentByTag", "findFragmentById", "beginTransaction",
                "add", "replace", "remove", "hide", "show", "detach",
                "attach", "commit", "commitAllowingStateLoss", "commitNow",
                "commitNowAllowingStateLoss", "executePendingTransactions"};
    }
private:
    HeapAllocator* heap_ = nullptr;
};

// ─────────────────────────────────────────────────────────────────────────
// LooperShadow — owns the single main Looper object.
//
// Identity contract:
//   * Looper.getMainLooper() returns main_looper_id_ always.
//   * Looper.myLooper() returns main_looper_id_ (we have only one thread).
//   * Looper.getThread() returns the SAME id as Thread.currentThread().
//     This is the key invariant that makes ArchTaskExecutor.isMainThread()
//     return true.
//   * Looper.getQueue() returns a singleton MessageQueue (no real queue).
//   * Looper.prepare() / Looper.loop() are stubs (return void).
//
// On init, the LooperShadow asks the ThreadShadow for the main Thread
// object_id and binds to it. The LooperShadow and ThreadShadow must be
// registered in the same registry so the LooperShadow can find the
// ThreadShadow.
// ─────────────────────────────────────────────────────────────────────────
class LooperShadow : public Shadow {
public:
    std::string name() const override { return "Looper"; }
    void init(HeapAllocator* heap) override {
        heap_ = heap;
        if (heap_) {
            main_looper_id_ = heap_->get_or_create("Landroid/os/Looper;");
            // Also allocate the MessageQueue singleton referenced by getQueue.
            main_queue_id_  = heap_->get_or_create("Landroid/os/MessageQueue;");
        }
    }

    bool handles_class(const std::string& class_name) const override {
        return class_name == "Landroid/os/Looper;" ||
               class_name == "Landroid/os/MessageQueue;" ||
               // M3 FIX-M3-014: SystemClock reads the same deterministic
               // virtual clock that the G07 Looper machinery schedules
               // against (one clock, one authority).
               class_name == "Landroid/os/SystemClock;";
    }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"getMainLooper", "myLooper", "getThread", "getQueue",
                "myQueue", "getMainLooper", "prepare", "loop",
                "quit", "quitSafely", "prepareMainLooper"};
    }
    std::vector<std::string> stubbed_methods() const override {
        return {"loop", "prepare", "prepareMainLooper"};
    }

    uint32_t main_looper_id() const { return main_looper_id_; }
    uint32_t main_queue_id()  const { return main_queue_id_; }

    // Bind the Looper to a specific Thread object_id (typically
    // ThreadShadow.main_thread_id()). The LooperShadow will return this
    // same id from Looper.getThread().
    void bind_to_thread(uint32_t thread_id) { bound_thread_id_ = thread_id; }
    uint32_t bound_thread_id() const { return bound_thread_id_; }

private:
    uint32_t main_looper_id_ = 0;
    uint32_t main_queue_id_  = 0;
    uint32_t bound_thread_id_ = 0;
};

// ─────────────────────────────────────────────────────────────────────────
// HandlerShadow — deterministic single-thread Runnable queue.
//
// Android's Handler is normally a thread-loose, multi-threaded queue
// backed by a MessageQueue. We don't need real multithreading — we just
// need to faithfully preserve "post this Runnable, eventually run it".
//
// Model:
//   * Handler(Looper) and Handler() are both no-ops that allocate a
//     Handler heap object. We don't actually use the Handler object for
//     dispatch — we maintain a single global queue.
//   * Handler.post(Runnable)    → enqueue(runnable, delay_ms=0)
//   * Handler.postDelayed(R,A)  → enqueue(runnable, delay_ms=A)
//   * Handler.removeCallbacks(R)→ remove from queue
//   * Handler.getLooper()       → return main Looper singleton
//   * AndroidUtilities.runOnUIThread(Runnable) → enqueue(runnable, 0)
//
// The ApplicationRuntime drains the queue at well-defined points:
// after Activity.onCreate, after onResume, etc. Runnables that post
// other Runnables are supported (the drain loop is iterative).
// ─────────────────────────────────────────────────────────────────────────
class HandlerShadow : public Shadow {
public:
    // Reserved framework-callback token base (G06). Framework-internal
    // Runnables (PerformClick / UnsetPressedState / CheckForLongPress) ride
    // this queue through tokens >= this base so the engine can route drained
    // entries to the TouchDispatcher instead of the DEX run() path — one
    // MessageQueue, one ordering law. Heap object ids grow from 1 and never
    // reach this range in any reachable corpus.
    static constexpr uint32_t kFrameworkTokenBase = 0xF0000000u;

    struct QueuedRunnable {
        uint32_t runnable_id = 0;        // heap object_id of the Runnable
        uint32_t enqueue_seq = 0;        // FIFO tiebreaker
        int64_t  ready_at_ms = 0;        // logical "ready" timestamp
        std::string runnable_class;     // for diagnostics
        // FINDING-004 (M3 F-ROOM-CHAIN): AOSP postDelayed(Runnable, Object
        // token, long) rides Message.obj. MicroTimer v8 schedules each
        // countdown tick with the token-overload and cancels per-timer work
        // with removeCallbacksAndMessages(token) where the token is the
        // boxed expires Long. token_id 0 = AOSP msg.obj == null (the public
        // 2-arg overload) — removeCallbacksAndMessages(null) clears those.
        uint32_t token_id = 0;
    };

    std::string name() const override { return "Handler"; }
    void init(HeapAllocator* heap) override {
        heap_ = heap;
        if (heap_) {
            main_handler_id_ = heap_->get_or_create("Landroid/os/Handler;");
        }
    }

    bool handles_class(const std::string& class_name) const override {
        return class_name == "Landroid/os/Handler;" ||
               class_name == "Lorg/telegram/messenger/AndroidUtilities;";
    }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"post", "postDelayed", "postAtFrontOfQueue",
                "removeCallbacks", "removeCallbacksAndMessages",
                "getLooper", "sendEmptyMessage", "sendMessage",
                // M4 F-029a: hidden static API surfaced by HandlerCompat
                "createAsync"};
    }
    std::vector<std::string> stubbed_methods() const override {
        return {"obtainMessage", "sendMessageDelayed", "sendMessageAtTime"};
    }

    // Enqueue a Runnable with a delay (in milliseconds). The ready time is
    // computed against the VIRTUAL clock (virtual_now_ms_ + delay_ms), so
    // scheduling is fully deterministic — no wall-clock involvement.
    void enqueue(uint32_t runnable_id, int64_t delay_ms,
                 const std::string& cls);

    // Token-bearing enqueue (AOSP postDelayed(Runnable, Object token, long)
    // and Message.obtain(r, token)). token_id 0 = no token (msg.obj null).
    void enqueue_tokened(uint32_t runnable_id, int64_t delay_ms,
                         const std::string& cls, uint32_t token_id);

    // AOSP removeCallbacksAndMessages(Object token): a NULL token removes
    // every pending post; a non-null token removes only the posts riding
    // that exact token object (identity, not equality). Returns the number
    // of entries removed.
    size_t remove_by_token(uint32_t token_id);

    // G06 §4: enqueue a FRAMEWORK-INTERNAL callback (PerformClick /
    // UnsetPressedState / CheckForLongPress) on the SAME queue and clock as
    // app Runnables. The AOSP law is one MessageQueue per main thread:
    // a posted PerformClick must be ordered against app Runnables by
    // (when, FIFO). `token` must be >= kFrameworkTokenBase (touch_dispatcher.h)
    // so the engine can route the drained entry to the TouchDispatcher
    // instead of the DEX Runnable path.
    void enqueue_framework(uint32_t token, int64_t delay_ms,
                           const std::string& label) {
        if (token < kFrameworkTokenBase) return;  // hostile-token safe
        enqueue(token, delay_ms, label);
    }

    // Drain every Runnable whose ready time has been reached on the VIRTUAL
    // clock (ready_at_ms <= virtual_now_ms_), in enqueue (FIFO) order among
    // the due entries. Runnables scheduled for a later virtual time stay
    // queued. Returns the number drained.
    // Each drained Runnable's heap object_id is appended to `out_drained`.
    // The ApplicationRuntime is responsible for actually executing the
    // Runnable's run() method.
    size_t drain_ready(std::vector<uint32_t>* out_drained);

    // ── Deterministic virtual clock (Handler/Looper time model) ──────────
    // The runtime has no wall-clock rendering, so Looper time is virtual.
    //  * idle-settle points (post-onCreate) call settle(): the clock jumps
    //    far into the future and one drain dispatches everything posted so
    //    far — the documented EXP-088 law (post(A), post(B), postDelayed(C)
    //    → drain → A, B, C) is preserved.
    //  * time-driven frame capture (--frames N) advances the clock by
    //    --frame-delay per frame and drains only what became due, so a
    //    self-reposting postDelayed animation steps once per frame,
    //    deterministically.
    void settle();                       // jump far into the future
    void advance_virtual(int64_t delta_ms);  // step the clock forward
    int64_t virtual_now_ms() const { return virtual_now_ms_; }

    // M3 F-ROOM-CHAIN (AG, 2026-09-08): due-probe for the drain loops.
    // AOSP law: MessageQueue.next() re-evaluates `when` against the Looper
    // clock between dispatch rounds. A runnable that re-posts with
    // delay=0 at the SAME virtual timestamp is due again immediately —
    // the probe lets the caller (drain_quiescent) model the looper
    // iteration cost (1ms virtual quantum) instead of spinning forever
    // on a frozen clock.
    bool has_due_at(int64_t now_ms) const;

    // M3 FINDING-009: AOSP MessageQueue.next() poll-timeout law.
    // When the head message's `when` is in the future the looper does NOT
    // exit — it sleeps nativePollOnce(head.when - now) and dispatches when
    // the clock reaches `when`. The deterministic drain therefore needs a
    // read-only peek at the EARLIEST ready_at in the queue (the sorted head
    // `when`) to fast-forward the virtual clock by exactly that delta.
    // Returns INT64_MAX when the queue is empty (no poll timeout possible).
    int64_t next_ready_ms() const;

    // EXP-088 Phase F: Remove all queued Runnables matching the given
    // runnable_id. Returns the number removed.
    //
    // Implements Handler.removeCallbacks(Runnable) — removes any
    // matching Runnable from the queue, regardless of its delay/priority.
    // If the Runnable has already been drained, this is a no-op.
    //
    // This is necessary for the user's Phase F acceptance scenario:
    //   post(A), post(B), postDelayed(C), removeCallbacks(B), drain → A, C
    //
    // Previously this was a stub (no-op) — the queue was never modified.
    size_t remove_callbacks(uint32_t runnable_id);

    // EXP-088 Phase F: Remove ALL queued Runnables (Handler.removeCallbacksAndMessages(null)).
    // Returns the number removed.
    size_t remove_all();

    // Total queue depth (for diagnostics).
    size_t queue_size() const { return queue_.size(); }

    // Helper: extract a Runnable argument from a CallContext.
    // `arg_idx` is the index of the Runnable parameter. Returns 0 if
    // the arg is null or absent.
    static uint32_t extract_runnable(const CallContext& ctx, size_t arg_idx);

private:
    uint32_t main_handler_id_ = 0;
    std::deque<QueuedRunnable> queue_;
    uint32_t next_seq_ = 0;
    int64_t virtual_now_ms_ = 0;   // deterministic Looper time (ms)

public:
    // M4 F-029b: the main Handler singleton id (bound at init via
    // heap get_or_create). View.getHandler() law uses the same singleton:
    // an attached view's handler is the ViewRootImpl handler, which on a
    // single-main-thread runtime is exactly this Handler.
    uint32_t main_handler_id() const { return main_handler_id_; }
};

// ─────────────────────────────────────────────────────────────────────────
// IntentShadow — Intent creation, component resolution, startActivity.
//
// Tracks:
//   * The pending Intent set by the most recent startActivity call.
//   * The resolved target Activity class (component class).
//   * Intent extras (key/value map, type-erased).
//
// The ApplicationRuntime reads pending_intent() after each Activity
// callback returns and, if set, transitions to the target Activity by
// invoking its onCreate.
// ─────────────────────────────────────────────────────────────────────────
class IntentShadow : public Shadow {
public:
    struct PendingIntent {
        std::string action;            // Intent.getAction()
        std::string component_class;   // setComponent(...).getClassName()
        std::string package_name;      // setPackage(...)
        std::map<std::string, std::string> extras_string;
        std::map<std::string, int32_t>  extras_int;
        std::map<std::string, bool>     extras_bool;
        int flags = 0;
        uint32_t intent_object_id = 0; // G08: heap object of this Intent
    };

    std::string name() const override { return "Intent"; }
    void init(HeapAllocator* heap) override { heap_ = heap; }

    bool handles_class(const std::string& class_name) const override {
        return class_name == "Landroid/content/Intent;";
    }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"<init>", "setAction", "getAction", "setClass",
                "setClassName", "setComponent", "getComponent",
                "putExtra", "getStringExtra", "getIntExtra",
                "getBooleanExtra", "setFlags", "addFlags",
                "getFlags", "setPackage"};
    }
    std::vector<std::string> stubbed_methods() const override {
        return {"createChooser", "parseUri", "toUri"};
    }

    // Record a startActivity(Intent) call. The ApplicationRuntime will
    // read this on the next drain point.
    void set_pending(std::shared_ptr<PendingIntent> intent) {
        pending_ = std::move(intent);
    }
    std::shared_ptr<PendingIntent> take_pending() {
        auto p = std::move(pending_); pending_.reset(); return p;
    }
    bool has_pending() const { return pending_ != nullptr; }

    // EXP-051: Public so ActivityShadow.startActivity can mark an
    // existing Intent heap object as pending. The Intent must already
    // have been created (the bytecode allocates it via new-instance +
    // <init> before calling startActivity).
    std::shared_ptr<PendingIntent> get_or_create_intent(uint32_t object_id);

private:
    std::shared_ptr<PendingIntent> pending_;
    std::map<uint32_t, std::shared_ptr<PendingIntent>> intents_;
};

// ─────────────────────────────────────────────────────────────────────────
// ActivityShadow — current Activity, lifecycle, view root.
//
// Tracks:
//   * current_activity_id  — heap object_id of the active Activity.
//   * current_activity_class — class descriptor (e.g. "Lorg/telegram/ui/LaunchActivity;").
//   * content_view_id     — heap object_id of the View set by setContentView.
//
// Lifecycle state machine (deterministic, single-threaded):
//   CREATED → STARTED → RESUMED → (PAUSED → STOPPED → DESTROYED)
//
// Lifecycle method invocations on the Activity heap object are NOT
// dispatched by this shadow — the engine's recursive invoke path
// handles those (it can find the Activity's onCreate in DEX bytecode).
// This shadow only tracks state.
// ─────────────────────────────────────────────────────────────────────────
class ActivityShadow : public Shadow {
public:
    enum class LifecycleState {
        NONE, CREATED, STARTED, RESUMED, PAUSED, STOPPED, DESTROYED
    };

    std::string name() const override { return "Activity"; }
    void init(HeapAllocator* heap) override { heap_ = heap; }

    bool handles_class(const std::string& class_name) const override {
        // EXP-087 Phase 3 (B2 FIX): Also handle Activity subclasses whose
        // names don't contain "Activity" (e.g. GameMasterDice extends
        // ListActivity, StopWatch extends Activity). We handle any class
        // that could have inherited setContentView/getIntent/etc.
        return class_name == "Landroid/app/Activity;" ||
               class_name == "Landroid/app/ListActivity;" ||
               class_name.find("/Activity;") != std::string::npos ||
               class_name.find("LaunchActivity") != std::string::npos ||
               class_name.find("LoginActivity")  != std::string::npos ||
               class_name.find("Activity;") != std::string::npos ||
               // EXP-087: Also match known Activity subclass patterns
               class_name.find("/GameMasterDice;") != std::string::npos ||
               class_name.find("/StopWatch;") != std::string::npos ||
               class_name.find("/Notes;") != std::string::npos ||
               class_name.find("/NoteMain;") != std::string::npos ||
               class_name.find("/MainActivity;") != std::string::npos ||
               class_name.find("/AndroidLauncher;") != std::string::npos;
    }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"setContentView", "getContentView", "findViewById",
                "getIntent", "setIntent", "finish", "getApplicationContext",
                "getFragmentManager", "getWindow", "getWindowManager",
                "getResources", "getPackageManager", "getPackageName",
                "getClassLoader", "getFilesDir", "getCacheDir",
                "getSharedPreferences", "startActivity", "startActivityForResult",
                "getCallingActivity", "getCallingPackage"};
    }
    std::vector<std::string> stubbed_methods() const override {
        return {"runOnUiThread", "overridePendingTransition",
                "findViewById", "registerForContextMenu"};
    }

    void set_current_activity(uint32_t id, const std::string& cls) {
        current_activity_id_ = id;
        current_activity_class_ = cls;
        state_ = LifecycleState::CREATED;
    }
    // ── R-NEW-341 (S40): application identity law ──────────────────────
    // AOSP: ActivityThread binds ONE Application object per process;
    // getApplicationContext() and getApplication() must serve THAT object
    // (Hilt/DI type-check it: instanceof Application → Lxb0;.d() unwrap).
    // The engine's bind_manifest_application publishes the bound heap
    // object id + class here so the shadow dispatch path and the engine's
    // P0.7 path never disagree on identity.
    void set_application_heap_identity(uint32_t id, const std::string& cls) {
        application_heap_id_ = id;
        application_heap_class_ = cls;
    }
    uint32_t application_heap_id() const { return application_heap_id_; }
    // UNIFIED_011.3 FRAME-2 (§23): record ONLY the activity's heap object id
    // (no lifecycle-state side effects). Used by execute_apk_with_activity so
    // post-launch probes (click-test android:onClick dispatch) can invoke
    // handlers with the REAL activity instance as `this`.
    void set_activity_heap_id(uint32_t id) { current_activity_id_ = id; }
    uint32_t current_activity_id() const { return current_activity_id_; }
    const std::string& current_activity_class() const { return current_activity_class_; }
    LifecycleState state() const { return state_; }
    void set_state(LifecycleState s) { state_ = s; }

    void set_content_view(uint32_t view_id) { content_view_id_ = view_id; }
    uint32_t content_view_id() const { return content_view_id_; }

    // ── G08: Activity stack + result + launch-intent identity ──────────
    // TransactionExecutor law: a launched activity pushes onto the task
    // stack; finish() pops and RESTORES the previous entry (restart law).
    struct ActivityRecord {
        uint32_t obj_id = 0;            // heap object of the Activity
        std::string cls;                // DEX descriptor
        uint32_t content_view_id = 0;   // its window content root
        LifecycleState state = LifecycleState::CREATED;
        // G08: >= 0 when THIS record's activity launched the current one
        // for a result — delivered to it on pop as onActivityResult.
        int launched_for_request = -1;
    };
    void push_activity_record(const ActivityRecord& r) {
        stack_.push_back(r);
    }

    // ── F-058 (R-NEW-279): Application.ActivityLifecycleCallbacks registry ──
    // AOSP law (Application.java, android-14): mActivityLifecycleCallbacks is
    // a CopyOnWriteArrayList<Application.ActivityLifecycleCallbacks>.
    // registerActivityLifecycleCallbacks APPENDS (duplicates allowed — AOSP
    // never dedupes); unregisterActivityLifecycleCallbacks removes BY
    // IDENTITY (first equal object). Activity.registerActivityLifecycle
    // Callbacks (Activity.java L1627) DELEGATES to the application — the
    // registry is process-wide (one per application), so storing it on the
    // ActivityShadow (the process-wide activity hub) preserves the AOSP
    // visibility: every activity's lifecycle event fans out to every
    // registered observer.
    // Dispatch order law: registration order, per event:
    //   onActivityPreCreated → onCreate → onActivityCreated →
    //   onActivityPostCreated  (and the Started/Resumed pairs likewise).
    // The observer method names are FRAMEWORK-INTERFACE names
    // (android/app/Application$ActivityLifecycleCallbacks) — R8 cannot
    // rename them on implementations (verified in dooz 1.0.18 DEX:
    // androidx/lifecycle/v.onActivityPreCreated keeps its name), so
    // name-based dispatch is the general law, not a heuristic.
    struct LifecycleCallbackEntry {
        uint32_t oid = 0;     // heap object of the observer
        std::string cls;      // runtime class descriptor of the observer
    };
    void register_lifecycle_callback(uint32_t oid, std::string cls) {
        // CopyOnWriteArrayList.add semantics: append unconditionally.
        lifecycle_callbacks_.push_back({oid, std::move(cls)});
    }
    bool unregister_lifecycle_callback(uint32_t oid) {
        // AOSP remove: first identity match (ArrayList.indexOf equality).
        for (auto it = lifecycle_callbacks_.begin();
             it != lifecycle_callbacks_.end(); ++it) {
            if (it->oid == oid) {
                lifecycle_callbacks_.erase(it);
                return true;
            }
        }
        return false;
    }
    const std::vector<LifecycleCallbackEntry>& lifecycle_callbacks() const {
        return lifecycle_callbacks_;
    }
    size_t lifecycle_callback_count() const { return lifecycle_callbacks_.size(); }

    // Pop the top record: the popped entry IS the previous activity —
    // restore it as current (the current activity, which is NOT in the
    // stack, is being destroyed by the finish cascade). Returns false when
    // the stack is empty (plain finish of the root — nothing to restore).
    bool pop_activity_record(ActivityRecord* out_popped) {
        if (stack_.empty()) return false;
        ActivityRecord top = stack_.back();
        stack_.pop_back();
        current_activity_id_ = top.obj_id;
        current_activity_class_ = top.cls;
        content_view_id_ = top.content_view_id;
        state_ = top.state;
        if (out_popped) *out_popped = top;
        return true;
    }
    size_t stack_depth() const { return stack_.size(); }

    // startActivityForResult(Intent, requestCode): the request code rides
    // with the pending launch; onActivityResult(request, result, data) is
    // delivered to the CALLER on pop (before its onStart — the
    // onActivityResult-before-onResume law).
    void set_pending_launch_request_code(int rc) { pending_request_code_ = rc; }
    int take_pending_launch_request_code() {
        int rc = pending_request_code_;
        pending_request_code_ = -1;
        return rc;
    }
    // Activity.setResult(resultCode, data) — recorded on the CURRENT record.
    void set_result(int result_code, uint32_t data_intent_id) {
        has_result_ = true;
        result_code_ = result_code;
        result_data_intent_id_ = data_intent_id;
    }
    bool take_result(int* result_code, uint32_t* data_intent_id) {
        if (!has_result_) return false;
        has_result_ = false;
        if (result_code) *result_code = result_code_;
        if (data_intent_id) *data_intent_id = result_data_intent_id_;
        return true;
    }
    // The Intent the current activity was LAUNCHED with — getIntent()
    // returns it so extras propagate through the real pipeline.
    void set_launch_intent_id(uint32_t id) { launch_intent_id_ = id; }
    uint32_t launch_intent_id() const { return launch_intent_id_; }

    // G07: Activity.finish() law (Activity.java finish → ActivityThread.
    // handleDestroyActivity): finish() does NOT destroy synchronously — it
    // REQUESTS destruction; the runtime performs the PAUSED → STOPPED →
    // DESTROYED cascade at the next frame boundary. The shadow records the
    // request; the ExecutionEngine consumes it (take_pending_finish).
    void request_finish() { pending_finish_ = true; }
    bool pending_finish() const { return pending_finish_; }
    bool take_pending_finish() {
        bool p = pending_finish_;
        pending_finish_ = false;
        return p;
    }

    // EXP-087 Phase 3 (B2 FIX): Set the APK path so setContentView(int)
    // can find the layout_cache.json next to the APK.
    void set_apk_path(const std::string& path) { apk_path_ = path; }

    // UNIFIED_007: real inflation evidence
    const std::string& last_inflate_stats() const { return last_inflate_stats_; }

private:
    uint32_t current_activity_id_ = 0;
    std::string current_activity_class_;
    // R-NEW-341: the process-wide Application identity (AOSP: exactly one
    // Application object per process, bound by ActivityThread).
    uint32_t application_heap_id_ = 0;
    std::string application_heap_class_;
    uint32_t content_view_id_ = 0;
    // F-058 (R-NEW-279): Application.ActivityLifecycleCallbacks registry
    // (CopyOnWriteArrayList semantics — see public accessors above).
    std::vector<LifecycleCallbackEntry> lifecycle_callbacks_;
    // EXP-074: Layout resource ID from setContentView(int layoutResId).
    int32_t layout_resource_id_ = 0;
    LifecycleState state_ = LifecycleState::NONE;
    bool pending_finish_ = false;   // G07: finish() requested, not yet applied
    // G08: task stack (bottom..top; the ROOT activity is stack_[0] once a
    // second activity pushes — the current activity is NOT in the stack).
    std::vector<ActivityRecord> stack_;
    int pending_request_code_ = -1;
    bool has_result_ = false;
    int result_code_ = 0;
    uint32_t result_data_intent_id_ = 0;
    uint32_t launch_intent_id_ = 0;
    // EXP-087 Phase 3 (B2 FIX): APK path for layout_cache.json lookup
    std::string apk_path_;
    // UNIFIED_007: JSON stats from last real inflation
    std::string last_inflate_stats_;
    std::vector<std::string> warnings_;
};

// ─────────────────────────────────────────────────────────────────────────
// ViewShadow — minimal View/ViewGroup hierarchy (semantic, no rendering).
//
// Each View heap object is tracked by:
//   * view_id           — the object_id (== heap object_id)
//   * parent_id         — 0 if root, else the parent ViewGroup's view_id
//   * children           — list of child view_ids (empty for leaf Views)
//   * view_id_android    — the Android `R.id.*` int set by setId() or XML
//   * class_desc         — View subclass class descriptor
//
// Operations supported:
//   * View.<init>(Context)   — allocate a fresh View heap object
//   * View.setId(int)        — record the Android view id
//   * View.getId()           — return the recorded id
//   * ViewGroup(View).addView(View) — parent->children.push_back(child)
//   * ViewGroup(View).removeView(View)
//   * View.getParent()       — return parent_id (or null)
//   * View.getChildAt(int)   — return children[i] or null
//   * View.getChildCount()   — return children.size()
//   * Activity.setContentView(View) — set the content_view on ActivityShadow
//   * Activity.findViewById(int)   — BFS the hierarchy for a view with
//                                       matching view_id_android
// ─────────────────────────────────────────────────────────────────────────
// ─────────────────────────────────────────────────────────────────────────
// G11 FIX-G11-002 — LayoutInflaterShadow (AOSP LayoutInflater law).
//
// Real Android: LayoutInflater.from(context) returns the shared inflater;
// inflate(resid, root[, attachToRoot]) parses the layout XML and, when a
// root is supplied with attachToRoot (the 2-arg overload defaults
// attachToRoot to root != null), attaches the inflated tree INTO the root
// and returns the root. App View constructors rely on this to build their
// child hierarchy (CalculatorDisplay.<init> → inflate(R.layout.display, this)).
// Without this shadow the call silently bridged to nothing and the
// constructor-built subtree vanished.
//
// Dispatch:
//   * static LayoutInflater.from(Context) — singleton heap object
//   * inflate(int)                       — inflate, return new root
//   * inflate(int, View)                 — attach INTO root, return root
//   * inflate(int, View, boolean)        — attach per attachToRoot flag
// ─────────────────────────────────────────────────────────────────────────
class LayoutInflaterShadow : public Shadow {
public:
    std::string name() const override { return "LayoutInflater"; }
    bool handles_class(const std::string& cls) const override {
        return cls == "Landroid/view/LayoutInflater;";
    }
    CallResult dispatch(const CallContext& ctx) override;
    std::vector<std::string> implemented_methods() const override {
        return {"from", "inflate"};
    }
};

class ViewShadow : public Shadow {
public:
    // ── F-062: compose saveable-id anchor key ───────────────────────────
    // The APK's own R.id.compose_view_saveable_id_tag value, captured
    // NAME-BASED from the app DEX (execute_sget*) — no hardcoded resource
    // id. Consumed by the getTag decor-anchor law (android_shadows.cpp).
    static void record_compose_saveable_id_key(int32_t k) {
        compose_saveable_id_key_.store(k, std::memory_order_relaxed);
    }
    static int32_t compose_saveable_id_key() {
        return compose_saveable_id_key_.load(std::memory_order_relaxed);
    }

    struct ViewNode {
        uint32_t view_id = 0;
        uint32_t parent_id = 0;
        std::vector<uint32_t> children;
        int32_t android_view_id = 0;     // View.getId() value
        std::string class_desc;
        // Layout params (semantic only — no real Measure/Layout pass).
        int width  = -1;  // MATCH_PARENT = -1, WRAP_CONTENT = -2
        int height = -1;
        int x = 0, y = 0;
        // Common properties used by Android code paths.
        std::string text;     // TextView.getText()
        std::string hint;     // TextView.getHint() / EditText hint (EXP-065)
        // EXP-071: Context — set during View creation (constructor receives Context).
        // When getContext() is called on this View, return this object_id.
        // In real Android, Views store the Context passed to their constructor.
        // We store it so getParentActivity() can find the Activity via
        // getView().getContext() instanceof Activity.
        uint32_t context_object_id = 0;  // The Context (Activity) that created this View
        // UC009: AOSP View.mAttachInfo equivalence — set when the tree attaches
        // to the window (dispatchAttachedToWindow), cleared on detach.
        // Compose's AbstractComposeView chain checks View.isAttachedToWindow()
        // during ensureCompositionCreated; without this state the composition
        // bails out and ComposeView keeps children=0 forever.
        bool attached_to_window = false;
        // MASTER CAMPAIGN FIX (F8 default-onMeasure law, View.java):
        // TRUE when this node's class chain does NOT override onMeasure up
        // to a framework content class — the AOSP DEFAULT View.onMeasure
        // then applies: setMeasuredDimension(getDefaultSize(...)) where
        // getDefaultSize returns specSize for AT_MOST/EXACTLY (i.e. the
        // parent-available size, NOT the content size). Computed by the DEX
        // engine at constructor time (dex-report-backed override query) and
        // consumed by the measure pass for leaf nodes with no text/image
        // content source. Evidence: org.billthefarmer.scope v140 measured
        // its plain custom Views (Scope/YScale/XScale/Unit) at 0x0/0x1920.
        bool aosp_default_measure = false;
        // MASTER CAMPAIGN FIX (F10 real-DEX onMeasure): TRUE when the DEX
        // chain DOES override onMeasure — the runtime must EXECUTE the
        // app's onMeasure bytecode (via the engine hook) instead of the
        // content model or the default law. Capture fields for the
        // setMeasuredDimension shadow dispatch during that execution:
        bool overrides_on_measure = false;
        int dex_measured_w = 0, dex_measured_h = 0;
        bool dex_measure_valid = false;
        // F-096 (R-NEW-329 root, real-DEX measure+layout lifecycle law):
        // AOSP View lifecycle dispatches onMeasure/onLayout for EVERY view
        // — including PROGRAMMATICALLY-CREATED ViewGroup subclasses whose
        // DEX chain defines the override (e.g. androidx
        // AndroidComposeView: onMeasure → updateRootConstraints+measureOnly,
        // onLayout → measureAndLayout → root.place(0,0) → the ENTIRE
        // compose placement chain). The F10 hook fires only for
        // inflated-leaf views (overrides_on_measure is captured at the
        // inflate ctor hook), so programmatic compose views never ran
        // their placement → every LayoutNode stayed isPlaced=false → 0
        // canvas ops (the R-NEW-329 frontier). This flag marks the
        // one-time lifecycle dispatch per node (layout passes are
        // idempotent for the static-frame runs this runtime models; later
        // frames reuse the composed result).
        bool f096_lifecycle_done = false;
        // EXP-067: Image resource ID — set by ImageView.setImageResource(int)
        // The renderer can look up the drawable path via resource_drawable_paths_.
        int32_t image_resource_id = 0;
        std::string image_drawable_path;  // resolved APK asset path (e.g. "res/abc.webp")
        // G04 §4: SELECTED config density (raw ResTable_config form) of the
        // resolved drawable + its NATURAL pixel dims (probed from the encoded
        // image). BitmapFactory law: displayed/intrinsic size =
        // natural × inTargetDensity/inDensity (DENSITY_NONE → natural).
        uint16_t src_density = 0;         // selected config density of src drawable
        uint16_t bg_drawable_density = 0; // selected config density of bg drawable
        int src_w = 0, src_h = 0;         // natural encoded dims (0 = unknown)
        // EXP-074: Text resource ID — set by TextView.setText(int resid).
        // When non-zero, the renderer resolves it via the ARSC string table.
        int32_t text_resource_id = 0;
        bool clickable = false;
        bool enabled = true;
        int visibility = 0;  // VISIBLE=0, INVISIBLE=4, GONE=8
        // S83-GFX-BASE §19: ImageView scale type (AOSP ScaleType ordinals:
        // matrix 0, fitXY 1, fitStart 2, fitCenter 3, fitEnd 4, center 5,
        // centerCrop 6, centerInside 7). FIT_CENTER = AOSP default.
        int scale_type = 3;
        // ── S55 F-082: ViewAnimator displayed-child model ────────────────
        // AOSP ViewAnimator.java mWhichChild: which child of a
        // ViewAnimator/ViewSwitcher/ViewFlipper is the displayed one.
        // Inflated trees start at 0 (ViewAnimator.initView → showOnly(0);
        // the inflater's G10 FIX-G10-002b law mirrors this by marking
        // children ≥1 GONE). setDisplayedChild/showNext/showPrevious
        // mutate this state and re-apply the showOnly visibility walk.
        int displayed_child = 0;
        // ── S56 F-085: WebView content model ─────────────────────────────
        // AOSP WebView.java stores the loaded document and renders it via
        // chromium. This engine's generic WebView content model: the load
        // family (loadUrl/loadData/loadDataWithBaseURL/postUrl) stores the
        // document verbatim; the render law extracts visible text (generic
        // HTML→text — NO app-specific markdown handling) into `text` so
        // the standard text pipeline paints it. WebView-family nodes only.
        std::string web_url;      // last loadUrl/postUrl target (or baseURL)
        std::string web_data;     // last loadData*/raw document (HTML/URL body)
        std::string web_mime;     // loadData mimeType, empty for loadUrl
        std::string web_title;    // <title> if the document carried one
        // ── G06 §5: view state model (View.java view-flag laws) ─────────
        // pressed: set by the TouchDispatcher per the View.onTouchEvent law
        // (DOWN non-scrolling → setPressed(true); UP → UnsetPressedState
        // posted at PRESSED_STATE_DURATION; CANCEL/move-outside → cleared).
        // Drives state-list background re-resolution at draw time.
        bool pressed = false;
        bool long_clickable = false;     // View.setLongClickable / listener
        bool focusable = false;          // View.setFocusable
        bool focusable_in_touch_mode = false;  // View.setFocusableInTouchMode
        bool focused = false;            // requestFocus result
        bool selected = false;           // View.setSelected
        // ── G06 §5: state-list background (StateListDrawable law) ────────
        // When the android:background drawable resolves to a <selector>
        // XML, the items are parsed once and the winning item is re-picked
        // per (pressed, enabled, selected) EVERY frame (DrawableContainer
        // law — the drawable reacts to drawableStateChanged).
        bool bg_state_list = false;
        bool bg_state_list_checked = false;  // lazy selector parse guard
        struct BgStateItem {
            // -1 = wildcard (state not declared on the item), 0/1 = required
            int state_pressed = -1;
            int state_enabled = -1;
            int state_selected = -1;
            uint32_t color = 0;           // android:color or shape solid
            bool has_color = false;
            std::string drawable_path;    // android:drawable file (may be empty)
        };
        std::vector<BgStateItem> bg_state_items;
        // CAMPAIGN 013 B1: dialog window item/button routing. When
        // dialog_owner_obj != 0 this ViewNode belongs to a DialogShadow
        // window's decor tree and clicks route to the window's
        // DialogInterface$OnClickListener as onClick(dialog, which) —
        // NOT the standard View$OnClickListener.onClick(view) path.
        // dialog_which: item index (>=0) for list rows, or the AOSP button
        // code BUTTON_POSITIVE(-1)/NEGATIVE(-2)/NEUTRAL(-3) for buttons.
        uint32_t dialog_owner_obj = 0;
        int dialog_which = -100;
        // EXP-060: Listener storage — the heap object_id of the
        // OnClickListener (or 0 if none). When dispatchClick is called
        // the runtime invokes listener.onClick(this_view) via try_recursive_invoke.
        // ── M3 FINDING-011: AOSP View tag law (View.java mTag/mKeyedTags) ──
        // androidx ViewTree* helpers (ViewTreeLifecycleOwner,
        // ViewTreeViewModelStoreOwner, SavedStateHandleSupport) cache their
        // per-view owner objects via View.setTag(R.id.view_tree_*, owner)
        // and retrieve them with View.getTag(R.id.*) — the keyed-tag call is
        // their "is the owner already installed?" dedupe contract. A silent
        // no-op here re-creates the owner on EVERY access (observed: dooz
        // registers SavedStateHandlesProvider twice → its own
        // IllegalArgumentException → 10-exception cascade → white screen).
        // Values preserve heap object identity (androidx check-casts the
        // retrieved tag and invokes methods on it).
        struct TagValue {
            enum Kind { NONE = 0, OBJECT = 1, STRING = 2, INT = 3 } kind = NONE;
            uint32_t object_id = 0;
            std::string object_class;  // runtime class of a tagged object
            std::string string_val;    // STRING-kind payload
            int32_t int_val = 0;       // INT-kind payload
        };
        TagValue default_tag;                        // View.setTag(Object) / getTag()
        std::map<int32_t, TagValue> keyed_tags;      // View.setTag(int, Object) / getTag(int)
        // R-NEW-339: memoized per-view AutofillId heap object —
        // View.getAutofillId() returns the SAME object every call
        // (AOSP: assigned once in the View ctor, API 26+).
        uint32_t autofill_id_obj = 0;
        uint32_t click_listener_id = 0;
        std::string click_listener_class;  // DEX descriptor of the listener class
        uint32_t long_click_listener_id = 0;
        std::string long_click_listener_class;
        uint32_t touch_listener_id = 0;
        std::string touch_listener_class;
        // EXP-095 (CM-019): Layout params captured from
        // addView(view, LayoutHelper.createLinear/createFrame(params)).
        // Per AOSP ViewGroup.LayoutParams / MarginLayoutParams:
        //   lp_width/lp_height: -1 = MATCH_PARENT, -2 = WRAP_CONTENT,
        //                        positive = exact px (density=1 on this runtime).
        //   lp_gravity: AOSP Gravity bits (CENTER_VERTICAL=0x10, CENTER_HORIZONTAL=1,
        //               CENTER=0x11, TOP=0x30, LEFT=3, RIGHT=5, BOTTOM=0x50).
        //   margins in px.
        // Sentinel INT_MIN = "no LayoutParams seen" (fall back to defaults).
        int lp_width = INT_MIN;
        int lp_height = INT_MIN;
        int lp_gravity = 0;
        int lp_margin_left = 0, lp_margin_top = 0;
        int lp_margin_right = 0, lp_margin_bottom = 0;
        // EXP-095: View.setGravity text alignment (TextView).
        int text_gravity = 0;
        // EXP-095: LinearLayout orientation (0=HORIZONTAL, 1=VERTICAL).
        // -1 = unset (default VERTICAL per LinearLayout docs).
        int orientation = -1;
        // EXP-095 (CM-020): Background color from setBackgroundColor(int).
        // 0xFFFFFFFF white is the View default; 0 = unset.
        uint32_t bg_color = 0;
        // S82-GFX F-NEW-158: programmatic setBackgroundResource(resid).
        // AOSP View.java: resid → drawable INFLATED ONCE (mBackground),
        // painted every draw. bg_resource_path = resolved APK path (set at
        // render stage); the old code reused image_resource_id which
        // clobbered ImageView src ids and was never consulted for bg.
        uint32_t bg_resource_id = 0;
        std::string bg_resource_path;
        // EXP-095: ScrollView scrolling container marker (content laid out
        // inside, potentially taller than screen).
        bool is_scroll_container = false;
        // EXP-098 (CM-027): RLottie animation frame RGBA buffer (rendered
        // by RLottieDecoder when setAnimation(R.raw.X, w, h) is called on
        // an RLottieImageView subclass). Stored as anim_w*anim_h*4 bytes
        // in scan order (R,G,B,A per pixel). When non-empty the renderer
        // draws these pixels at the view's bounds INSTEAD of the CM-022
        // placeholder.
        std::vector<uint8_t> anim_frame_rgba;
        int anim_w = 0;
        int anim_h = 0;
        int anim_total_frames = 0;  // total frames in the source animation
        int anim_current_frame = 0;  // current frame index for time-based playback
        // EXP-098 (CM-027): When setAnimation(R.raw.X, w, h) is observed
        // on an RLottieImageView, the engine stores the (raw_resid,
        // target_w, target_h) here. The render stage (which has access
        // to ApkParser) then resolves resid → APK path → JSON → rlottie
        // frame → RGBA buffer.
        int32_t anim_raw_resid = 0;
        int anim_target_w = 0;
        int anim_target_h = 0;
        bool anim_decode_attempted = false;  // avoid re-decoding on each frame

        // ===================================================================
        // UNIFIED_007: REAL inflation fields (set by resources::LayoutInflater
        // from AXML attributes; consumed by renderer + touch hit testing).
        // ===================================================================
        int padding_left = 0, padding_top = 0, padding_right = 0, padding_bottom = 0;
        float text_size_px = 0;          // 0 → renderer default
        uint32_t text_color = 0;         // 0 → renderer default (near-black)
        // M3 FIX-M3-005b: setTextColor(ColorStateList) heap object id — the
        // CSL default-color law resolves at draw time (0 = none captured).
        uint32_t text_color_state_object = 0;
        bool text_bold = false;
        bool text_italic = false;
        std::string bg_drawable_path;    // APK entry path of background drawable
        std::string fg_drawable_path;    // M3 F-005 FIX-B: foreground drawable
                                         // (View.setForeground — AOSP View.java
                                         // mForeground) — measured like src and
                                         // drawn over the content each frame.
        std::string src_drawable_path;   // APK entry path of ImageView src
        // F-142b (AOSP ImageView.java onMeasure L1141+ law): XML measure
        // caps — android:maxWidth/maxHeight (px, density-resolved at parse)
        // and android:adjustViewBounds. The wrap-content measure applies
        // them AFTER the density-scaled intrinsic size: min(max_*, desired)
        // with aspect-true rescale of the opposite axis. 0 = no cap.
        int  max_w = 0, max_h = 0;
        bool adjust_view_bounds = false;
        // F-053 (M9): GradientDrawable <shape> law — parsed ONCE at inflate
        // time by the live LayoutInflater from the bg .xml drawable (AOSP
        // GradientDrawable.inflate → GradientState). The render walk draws
        // solid/gradient fill + stroke ring with corner radii. Fields that
        // AOSP parses but no fixture exercises (ring/line kinds, dash) are
        // recorded honestly and reported DETECTED-NOT-EXERCISED.
        bool bg_shape_valid = false;     // bg drawable XML root was <shape>
        int bg_shape_kind = 0;           // GradientDrawable: 0 RECT, 1 OVAL, 2 LINE, 3 RING
        bool bg_shape_has_solid = false;
        uint32_t bg_shape_solid = 0;
        bool bg_shape_has_gradient = false;
        uint32_t bg_shape_grad_start = 0, bg_shape_grad_end = 0;
        int bg_shape_grad_angle = 0;     // degrees, AOSP law: multiple of 45
        float bg_shape_corner_radius = 0.0f;     // px @ device density
        float bg_shape_corner_tl = -1.0f;        // per-corner override (<0 = unset;
        float bg_shape_corner_tr = -1.0f;        //  AOSP GradientState cornerRadii)
        float bg_shape_corner_br = -1.0f;
        float bg_shape_corner_bl = -1.0f;
        bool bg_shape_has_stroke = false;
        float bg_shape_stroke_width = 0.0f;      // px
        uint32_t bg_shape_stroke_color = 0;
        // ── S83-GFX-BASE §14: VectorDrawable (parsed at inflate, painted at
        // draw by the F-053-adjacent vector law). One ViewNode carries the
        // whole vector: viewport + flattened path contours (group transforms
        // pre-applied), per-path fill/stroke state.
        struct VectorPathData {
            std::vector<std::vector<std::pair<float, float>>> contours;
            uint32_t fill_color = 0;       // ARGB
            bool has_fill = false;
            float fill_alpha = 1.0f;
            bool has_stroke = false;
            uint32_t stroke_color = 0;     // ARGB
            float stroke_width = 0.f;
            float stroke_alpha = 1.0f;
            int fill_type = 0;             // 0 winding, 1 even-odd
        };
        struct VectorDrawableData {
            float viewport_w = 0.f, viewport_h = 0.f;
            std::vector<VectorPathData> paths;
        };
        bool bg_vector_valid = false;
        VectorDrawableData bg_vector;
        bool bg_shape_has_dash = false;          // S83-B2 §14: dash strokes RENDER
        float bg_shape_dash_width = 0.0f;        //  (scanline dash law, f053 draw)
        float bg_shape_dash_gap = 0.0f;
        // ── S83-B2 §14: GradientDrawable RING state (AOSP GradientState).
        // innerRadius/thickness are px; ratio forms are "bounds dim / ratio"
        // (developer.android.com GradientDrawable law). <0 = unset.
        float bg_shape_inner_radius = -1.0f;
        float bg_shape_thickness = -1.0f;
        float bg_shape_inner_ratio = -1.0f;      // default 9.0 (AOSP doc law)
        float bg_shape_thick_ratio = -1.0f;      // default 9.0
        // ── S83-B2 §14: LayerDrawable (layer-list XML + code-level) law.
        // Items render bottom→top in DOCUMENT ORDER (AOSP LayerDrawable.draw).
        struct BgLayer {
            int left = 0, top = 0, right = 0, bottom = 0;   // setLayerInset px
            int kind = 0;              // 1 color, 2 shape, 3 bitmap/.9.png, 4 vector, 5 nested xml
            uint32_t color = 0;        // kind 1
            // shape state (kind 2) — GradientState subset
            int shape_kind = 0;
            bool shape_has_solid = false; uint32_t shape_solid = 0;
            bool shape_has_gradient = false; uint32_t shape_gs = 0, shape_ge = 0;
            int shape_ga = 0;
            float shape_radius = 0.0f;
            bool shape_has_stroke = false; float shape_sw = 0.0f; uint32_t shape_sc = 0;
            bool shape_has_dash = false; float shape_dw = 0.0f, shape_dg = 0.0f;
            float shape_inner_r = -1.0f, shape_thick = -1.0f;
            float shape_ir_ratio = -1.0f, shape_tk_ratio = -1.0f;
            // bitmap / nested xml / vector path (kinds 3/4/5)
            std::string path;
        };
        std::vector<BgLayer> bg_layers;         // XML layer-list items (document order)
        bool bg_layers_valid = false;
        // Code-level LayerDrawable children: heap object ids + insets
        // (captured at LayerDrawable.<init>(Drawable[]) / setLayerInset —
        // the same capture law F-NEW-158 established for ColorDrawable).
        struct CodeLayer {
            uint32_t drawable_obj = 0;
            int left = 0, top = 0, right = 0, bottom = 0;
        };
        std::vector<CodeLayer> bg_code_layers;
        bool bg_code_layers_valid = false;
        std::string onClick_handler;     // android:onClick method name (real DEX callback)
        int layout_weight = 0;           // LinearLayout weight
        // G04 §9: container weightSum (raw XML value; valid flag distinguishes
        // "declared 0" from "not declared" — AOSP mWeightSum law).
        float weight_sum = 0.0f;
        bool weight_sum_valid = false;
        int container_gravity = -1;      // android:gravity on container (-1 unset)
        int child_gravity = -1;          // android:layout_gravity on child
        bool gravity_set = false;
        bool bg_from_xml = false;        // background came from XML (color or drawable)
        int measured_left = 0, measured_top = 0;   // final geometry (measure/layout)
        int measured_width = 0, measured_height = 0;
        int measured_right = 0, measured_bottom = 0;
        bool laid_out = false;           // geometry computed
        // MASTER-2 FIX-MEASURE-002e (AOSP onLayout replay law): RelativeLayout
        // resolves a child's mLeft/mTop/mRight/mBottom edges DURING measure
        // (applySizeRules + positionChild*) and RelativeLayout.onLayout only
        // REPLAYS the cached edges — the child's measured size is NOT used
        // for anchor-constrained children (a view can measure 1x45 yet be
        // laid out 45x1860 when anchored alignParentTop + alignBottom to a
        // sibling; ground truth: org.billthefarmer.scope v140 YScale).
        int rl_cached_left = 0, rl_cached_top = 0;
        int rl_cached_right = 0, rl_cached_bottom = 0;
        bool rl_edges_valid = false;
        int num_lines = -1;
        float text_size_sp = 0;          // original sp (evidence)
        std::string android_id_name;     // resolved id name ("btn_roll") for evidence
        // FIX-2c: RelativeLayout dependency rules (names resolved against the
        // inflated tree). Captured from layout_below/layout_above/
        // layout_toRightOf/layout_toLeftOf raw values ("@id/name").
        std::string rel_below_name, rel_above_name;
        std::string rel_right_of_name, rel_left_of_name;
        // MASTER-2 FIX-MEASURE-002 (AOSP RelativeLayout measure law): the
        // ALIGN_* edge-alignment family is DISTINCT from the position
        // family (alignLeft aligns EDGES; toLeftOf positions BEFORE the
        // sibling) and alignParentLeft/Right had no representation at all
        // (ground truth: org.billthefarmer.scope v140 res/v9.xml — XScale's
        // layout_alignLeft was silently dropped, Scope/Unit lost
        // alignParentRight/Left, leaving the dependency graph incomplete).
        std::string rel_align_left_name, rel_align_right_name;
        std::string rel_align_top_name, rel_align_bottom_name;
        bool rel_align_parent_left = false, rel_align_parent_right = false;
        // MASTER-2 FIX-MEASURE-002d: explicit RL rule booleans. The legacy
        // gravity-bit encoding (TOP=0x30, BOTTOM=0x50, CENTER_V=0x10,
        // CENTER_IN=0x11) is AMBIGUOUS for RelativeLayout rules — the masks
        // overlap (0x50 & 0x30 = 0x10) so alignParentBottom triggered the
        // alignParentTop check. AOSP RelativeLayout reads RULES, not
        // Gravity; the RL paths consume these booleans only.
        bool rel_align_parent_top = false, rel_align_parent_bottom = false;
        bool rel_center_in_parent = false, rel_center_horizontal = false;
        bool rel_center_vertical = false;
        // F-148 (S72-W4): ConstraintLayout constraint params (AOSP
        // ConstraintLayout.LayoutParams, XML path). cl_*_to holds the
        // anchor target's id NAME ("" = unconstrained; "parent" = the
        // ConstraintLayout itself); cl_*_edge holds the TARGET's anchor
        // edge (1 = LEFT/TOP, 2 = RIGHT/BOTTOM). start/end map onto
        // left/right (LTR). Biases default 0.5.
        std::string cl_left_to, cl_right_to, cl_top_to, cl_bottom_to;
        int cl_left_edge = 0, cl_right_edge = 0;
        int cl_top_edge = 0, cl_bottom_edge = 0;
        float cl_bias_x = 0.5f, cl_bias_y = 0.5f;
        int text_style = 0;              // AOSP Typeface bits (bold=1, italic=2)
        // G32: android:fontFamily raw string ("monospace", "sans-serif", ...)
        // resolved to a system face via fonts::TextShaper::resolve_family().
        std::string font_family;
        // G47: AOSP TextView line-spacing state (TextView.java defaults:
        // mSpacingMult=1.0, mSpacingAdd=0, mIncludeFontPadding=true,
        // elegantTextHeight=false).
        float line_spacing_mult = 1.0f;
        float line_spacing_add_px = 0.0f;
        bool include_font_pad = true;
        bool elegant_text_height = false;
    };

    std::string name() const override { return "View"; }
    void init(HeapAllocator* heap) override { heap_ = heap; }

    bool handles_class(const std::string& class_name) const override {
        // EXP-075: Do NOT handle Activity subclasses — let ActivityShadow handle them.
        // This prevents ViewShadow from intercepting setContentView calls on Activities.
        if (class_name.find("Activity;") != std::string::npos) {
            return false;
        }
        // Match any class ending in "View;" or "ViewGroup;" or containing
        // well-known View subclasses. Specific dispatch is done by
        // method name.
        // EXP-060: Also match user-defined View subclasses by checking
        // if the class_name is NOT a known non-View framework class.
        // This is a heuristic — if the class isn't one of the known
        // non-View types, we try ViewShadow dispatch and return
        // not_handled if the method isn't a View method.
        if (class_name.find("View;") != std::string::npos ||
            class_name == "Landroid/widget/TextView;" ||
            class_name == "Landroid/widget/EditText;" ||
            class_name == "Landroid/widget/Button;" ||
            class_name == "Landroid/widget/ImageView;" ||
            class_name == "Landroid/view/View;" ||
            class_name == "Landroid/view/ViewGroup;" ||
            class_name == "Landroid/view/TextureView;" ||
            class_name == "Landroid/widget/ScrollView;" ||
            class_name == "Landroid/widget/FrameLayout;" ||
            class_name == "Landroid/widget/LinearLayout;") {
            return true;
        }
        // EXP-060: For user-defined classes (like IntroActivity$4 which
        // extends TextView), we can't check the hierarchy here. But if the
        // class name doesn't match any known non-View framework prefix,
        // it MIGHT be a View subclass. Let dispatch() figure it out by
        // method name. This is slightly broader than ideal but matches
        // how Robolectric handles View subclasses.
        if (class_name.find("Landroid/") == 0 ||
            class_name.find("Ljava/") == 0 ||
            class_name.find("Lkotlin/") == 0 ||
            class_name.find("Lcom/google/") == 0 ||
            class_name.find("Landroidx/") == 0) {
            // Standard framework class — let other shadows handle it.
            return false;
        }
        // User-defined class (e.g. Lorg/telegram/ui/...). Could be a
        // View subclass. Let dispatch() decide based on method name.
        return true;
    }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"<init>", "setId", "getId", "getParent",
                "addView", "addViewInLayout", "removeView",
                "removeViewInLayout", "removeAllViews",
                "getChildAt", "getChildCount",
                "findViewById", "findViewWithTag",
                "setVisibility", "getVisibility",
                // S55 F-082: ViewAnimator displayed-child family
                // (ViewSwitcher/ViewFlipper/ViewAnimator receivers).
                "setDisplayedChild", "getDisplayedChild",
                "showNext", "showPrevious",
                "setEnabled", "isEnabled",
                "setClickable", "isClickable",
                "setText", "getText",
                "setBackgroundColor", "setBackground",
                "setBackgroundResource", "setBackgroundDrawable",
                "setLayoutParams", "getLayoutParams",
                "measure", "layout", "draw",
                "requestLayout", "invalidate",
                // M3 FINDING-011: AOSP View tag law (mTag + mKeyedTags) —
                // the androidx ViewTree* owner-cache backbone.
                "setTag", "getTag",
                // EXP-060: Listener registration + click dispatch.
                "setOnClickListener",
                "setOnLongClickListener",
                "setOnTouchListener"};
    }
    std::vector<std::string> stubbed_methods() const override {
        return {"onMeasure", "onLayout", "onDraw", "onTouchEvent",
                "onAttachedToWindow", "onDetachedFromWindow"};
    }

    // Allocate a new ViewNode and bind it to a heap object_id.
    // Returns the view_id (= heap object_id).
    uint32_t create_view(const std::string& class_desc);

    // Get-or-create a ViewNode for an existing heap object_id.
    // Useful when the bytecode allocated the View via new-instance and
    // then called <init>.
    ViewNode* get_or_create_node(uint32_t view_id, const std::string& class_desc);

    // Lookup a ViewNode by id (const variant).
    const ViewNode* find_node(uint32_t view_id) const;
    ViewNode* find_node(uint32_t view_id);

    // EXP-090: Get all nodes for searching by class name
    const std::map<uint32_t, std::unique_ptr<ViewNode>>& all_nodes() const { return nodes_; }

    // ─────────────────────────────────────────────────────────────────────
    // R-NEW-347 (S42) — AOSP addViewInner child-attach pending queue.
    //
    // Oracle: aosp-mirror/platform_frameworks_base, core/java/android/view/
    // ViewGroup.java, addViewInner() (main branch, fetched S42):
    //     AttachInfo ai = mAttachInfo;
    //     if (ai != null &&
    //         (mGroupFlags & FLAG_PREVENT_DISPATCH_ATTACHED_TO_WINDOW) == 0) {
    //         ...
    //         child.dispatchAttachedToWindow(mAttachInfo,
    //                                        (mViewFlags&VISIBILITY_MASK));
    //     ...
    // i.e. adding a child to an ALREADY-ATTACHED parent dispatches the
    // attach to the child IMMEDIATELY at addView time (View
    // .dispatchAttachedToWindow first stores the AttachInfo, then invokes
    // onAttachedToWindow(), then the ViewGroup override recurses into the
    // child's own subtree).
    //
    // Shadows cannot run DEX code, so the ViewShadow only RECORDS the
    // pending attach here; the ENGINE consumes the record right after the
    // addView shadow call returns (bridge_to_api pending-consume law —
    // same shadow-flag/engine-callback split as the Room onCreate /
    // onUpgrade dispatch and ThreadShadow.consume_pending_start) and
    // drives the real onAttachedToWindow() DEX chain via
    // dispatch_attached_subtree_from().
    //
    // Real demand (dooz_23, PRIORITY-1): compose BOM 2026.06.01 creates
    // the AndroidComposeView during the first onMeasure
    // (ensureCompositionCreated → La72;.a pc=112 addView into the
    // already-attached ComposeView) and registers a PENDING composition
    // request via Lt4;.setOnReadyForComposition (field n0). On AOSP the
    // addView-attach fires AndroidComposeView.onAttachedToWindow(), whose
    // bytecode (pc 640-662) READS n0 and invokes it — THE composition
    // start. Without the child-attach dispatch the request is stored and
    // never consumed: content lambda never runs, first frame renders
    // blank (R-NEW-344 core).
    //
    // AOSP addTransientView applies the same law; the engine covers the
    // two addView entry points (addView/addViewInLayout) which is where
    // every framework and app code path adds children.
    // ─────────────────────────────────────────────────────────────────────
    void record_pending_child_attach(uint32_t parent_id, uint32_t child_id) {
        pending_child_attaches_.push_back({parent_id, child_id});
    }
    // FIFO consume — returns false when the queue is empty.
    bool consume_pending_child_attach(uint32_t& parent_id, uint32_t& child_id) {
        if (pending_child_attaches_.empty()) return false;
        auto front = pending_child_attaches_.front();
        parent_id = front.first;
        child_id  = front.second;
        pending_child_attaches_.erase(pending_child_attaches_.begin());
        return true;
    }
    bool has_pending_child_attaches() const {
        return !pending_child_attaches_.empty();
    }

    // ─────────────────────────────────────────────────────────────────────
    // R-NEW-349 (S43): AOSP FIRST-TRAVERSAL ORDERING LAW for
    // setContentView(View) — attach STRICTLY precedes measure.
    //
    // Oracle: AOSP ViewRootImpl.performTraversals — the first traversal
    // runs host.dispatchAttachedToWindow(mAttachInfo, 0) BEFORE
    // performMeasure, so on AOSP no measure pass ever observes an
    // unattached view. Compose relies on that order:
    // AbstractComposeView.onMeasure → ensureCompositionCreated →
    // View.windowRecomposer (WindowRecomposer.android.kt:288) opens with
    // checkPrecondition(isAttachedToWindow); measuring an unattached tree
    // throws ISE "Cannot locate windowRecomposer; View ... is not attached
    // to a window" and killed dooz23 MainActivity.onCreate (S43 baseline
    // evidence, stderr L242810/L242834).
    //
    // The shadow (no interpreter access) only RECORDS the
    // (attach-parent, measure-root) pair; the ENGINE consumes it right
    // after the setContentView shadow call returns — attach wave via
    // dispatch_attached_subtree_from, THEN the eager measure_layout that
    // used to run inline inside the shadow handler (the U007 law).
    // Same shadow-flag/engine-callback split as the R-NEW-347 addView
    // attach consume and the Room onCreate/onUpgrade dispatch.
    // ─────────────────────────────────────────────────────────────────────
    void record_pending_setcontent_attach_measure(uint32_t parent_id,
                                                   uint32_t root_id) {
        pending_setcontent_attach_measure_ = {parent_id, root_id};
    }
    // Consumes the pending record — returns false when none is stored.
    // Second field == 0 marks "no pending setContentView measure".
    bool consume_pending_setcontent_attach_measure(uint32_t& parent_id,
                                                    uint32_t& root_id) {
        if (pending_setcontent_attach_measure_.second == 0) return false;
        parent_id = pending_setcontent_attach_measure_.first;
        root_id   = pending_setcontent_attach_measure_.second;
        pending_setcontent_attach_measure_ = {0, 0};
        return true;
    }

private:
    // R-NEW-347 (S42): (parent, child) pairs whose child still needs the
    // AOSP addViewInner attach dispatch. Filled ONLY when the parent node
    // was attached_to_window at addView time; drained by the engine in
    // the same interpreter step (never crosses a frame boundary).
    std::vector<std::pair<uint32_t, uint32_t>> pending_child_attaches_;

    // R-NEW-349 (S43): pending setContentView(View) first-traversal record.
    // (attach_parent, measure_root); second == 0 means "nothing pending".
    // Recorded by ActivityShadow.setContentView, consumed by the engine
    // bridge right after the shadow call returns: attach wave, then the
    // eager measure_layout (AOSP ViewRootImpl.performTraversals ordering).
    std::pair<uint32_t, uint32_t> pending_setcontent_attach_measure_{0, 0};

public:
    // Add child to parent (updates both parent's children and child's parent_id).
    bool add_child(uint32_t parent_id, uint32_t child_id);
    bool remove_child(uint32_t parent_id, uint32_t child_id);

    // DFS search for a descendant with the given Android view_id.
    // Returns 0 if not found.
    uint32_t find_by_android_id(uint32_t root_id, int32_t android_id) const;
    // S83-GFX-BASE: lazily materialized window content root
    // (android.R.id.content law) — synthetic id space shared with dialogs.
    uint32_t next_window_content_id_ = 800100;
    // S83-GFX-BASE: window ViewTreeObserver object (getViewTreeObserver law).
    uint32_t view_tree_observer_id_ = 800200;
    uint64_t observer_listener_events_ = 0;

    // R-NEW-357 (S44): reverse lookup — the Android resource id VALUE for
    // the view whose android:id NAME matches (BFS from root). Answers 0
    // when no node carries that name. Backs
    // Resources.getIdentifier(name, "id", pkg).
    int32_t find_android_id_by_name(uint32_t root_id,
                                    const std::string& name) const;

    // EXP-060: Lookup a view by class descriptor (substring match).
    // Used to find the startMessagingButton (a TextView) without knowing
    // its Android view_id. Returns the most-recently-created match.
    uint32_t find_by_class_substring(const std::string& substring) const;

    // EXP-100 (UNIFIED_002): ALL matches for a class substring, ascending
    // view_id order. DIAGNOSTIC — used by dispatch_click_by_class to audit
    // candidate enumeration and selection (master request §9).
    std::vector<uint32_t> find_all_by_class_substring(const std::string& substring) const;

    // EXP-095 (CM-019): Store captured layout params on a ViewNode.
    // Called by the engine when addView(view, params) / setLayoutParams
    // is observed with a LayoutParams heap object carrying the fields
    // (width, height, gravity, leftMargin, topMargin, rightMargin,
    // bottomMargin) — produced by LayoutHelper.createLinear/createFrame or
    // by the generic *LayoutParams.<init> bridge (programmatic Android UIs).
    // R-NEW-302: also raises the requestLayout dirty flag (AOSP law —
    // View.setLayoutParams → requestLayout → performTraversals re-measure).
    void set_layout_params(uint32_t view_id, int w, int h, int gravity,
                           int ml, int mt, int mr, int mb,
                           float weight = 0.0f) {
        auto* n = get_or_create_node(view_id, "");
        if (n == nullptr) return;
        n->lp_width = w;
        n->lp_height = h;
        n->lp_gravity = gravity;
        n->lp_margin_left = ml;
        n->lp_margin_top = mt;
        n->lp_margin_right = mr;
        n->lp_margin_bottom = mb;
        n->layout_weight = weight;
        layout_dirty = true;
    }

    // R-NEW-302 FIX (AOSP requestLayout law): ViewGroup/view geometry
    // mutations raise this flag; the frame renderer re-runs the real
    // measure/layout pass (LayoutInflater::measure_layout) on the next
    // stage_render_frame and clears it. AOSP: ViewRootImpl.requestLayout()
    // schedules performTraversals (measure+layout+draw) — DEX-driven tree
    // changes (addView/removeView/setLayoutParams) must re-measure before
    // the next frame or every frame after the first reuses stale geometry.
    bool layout_dirty = false;

    // EXP-095: Store TextView.setGravity (text alignment inside the view).
    void set_text_gravity(uint32_t view_id, int gravity) {
        auto* n = get_or_create_node(view_id, "");
        if (n != nullptr) n->text_gravity = gravity;
    }

    // EXT-AOSP-001 (LinearLayout.setGravity): container gravity — AOSP
    // LinearLayout.java@1cdfff55 L1933-1945 stores mGravity and L1284/L1466
    // resolve child placement as `lp.gravity < 0 ? mGravity : lp.gravity`.
    // The live renderer consumes this when a child carries no explicit
    // layout_gravity (lp_gravity == 0 in this runtime).
    void set_container_gravity(uint32_t view_id, int gravity) {
        auto* n = get_or_create_node(view_id, "");
        if (n != nullptr) {
            n->container_gravity = gravity;
            n->gravity_set = true;
        }
    }

    // EXT-AOSP-002 (TextView.setTextSize): AOSP TextView.java@1cdfff55
    // L4720-4722 routes setTextSize(float) to COMPLEX_UNIT_SP and
    // L4752-4762 applies TypedValue.applyDimension → paint.setTextSize.
    // Bridge converts sp → px (scaledDensity) BEFORE calling this.
    void set_text_size_px(uint32_t view_id, float px) {
        auto* n = get_or_create_node(view_id, "");
        if (n != nullptr && px > 0.0f) {
            n->text_size_px = px;
            n->text_size_sp = px;  // density-scaled evidence value
        }
    }

    // EXP-095: Store LinearLayout.setOrientation (0=HORIZONTAL, 1=VERTICAL).
    void set_orientation(uint32_t view_id, int orientation) {
        auto* n = get_or_create_node(view_id, "");
        if (n != nullptr) n->orientation = orientation;
    }

    // EXP-095 (CM-020): Store View.setBackgroundColor(int).
    void set_bg_color(uint32_t view_id, uint32_t argb) {
        auto* n = get_or_create_node(view_id, "");
        if (n != nullptr) n->bg_color = argb;
    }

    // S82-GFX F-NEW-158: programmatic background family.
    // setBackgroundResource(int resid) — store the resid; the render stage
    // resolves it (ARSC select_file) to a state-list / shape / bitmap and
    // paints with the SAME draw laws the XML-inflated backgrounds use.
    void set_bg_resource(uint32_t view_id, uint32_t resid) {
        auto* n = get_or_create_node(view_id, "");
        if (n != nullptr) {
            n->bg_resource_id = resid;
            n->bg_from_xml = false;  // AOSP last-writer law
        }
    }
    // ColorDrawable color capture: obj id → color (AOSP mBackgroundState).
    void record_color_drawable(uint32_t drawable_obj, uint32_t color) {
        color_drawable_colors_[drawable_obj] = color;
    }
    // returns false when the object is not a color-carrying drawable we
    // captured (VectorDrawable/NinePatch/… — honest boundary).
    bool lookup_color_drawable(uint32_t drawable_obj, uint32_t* out) const {
        auto it = color_drawable_colors_.find(drawable_obj);
        if (it == color_drawable_colors_.end() || !out) return false;
        *out = it->second;
        return true;
    }

    // ── S83-B2 §14: code-level LayerDrawable + GradientDrawable capture ──
    // AOSP law: LayerDrawable.<init>(Drawable[]) stores the layer array;
    // setLayerInset(i,l,t,r,b) mutates layer i's insets; View.setBackground
    // parks the object as mBackground (drawn every draw). We mirror the
    // object graph on the shadow side: obj → children(+insets).
    struct GradientState {
        int shape = 0;                    // 0 RECT, 1 OVAL, 2 LINE, 3 RING
        bool has_color = false; uint32_t color = 0;
        float radius = -1.0f;
        bool has_stroke = false; float stroke_w = 0.0f; uint32_t stroke_color = 0;
        float inner_radius = -1.0f, thickness = -1.0f;
        float inner_ratio = -1.0f, thick_ratio = -1.0f;
    };
    void record_gradient_drawable(uint32_t drawable_obj, const GradientState& st) {
        gradient_states_[drawable_obj] = st;
    }
    void mutate_gradient_color(uint32_t drawable_obj, uint32_t color) {
        auto it = gradient_states_.find(drawable_obj);
        if (it != gradient_states_.end()) { it->second.has_color = true; it->second.color = color; }
    }
    bool lookup_gradient_drawable(uint32_t drawable_obj, GradientState* out) const {
        auto it = gradient_states_.find(drawable_obj);
        if (it == gradient_states_.end() || !out) return false;
        *out = it->second;
        return true;
    }
    void record_layer_children(uint32_t layer_obj, const std::vector<uint32_t>& kids) {
        auto& v = layer_children_[layer_obj];
        v.clear();
        for (uint32_t k : kids) v.push_back({k, 0, 0, 0, 0});
    }
    bool record_layer_inset(uint32_t layer_obj, int idx, int l, int t, int r, int b) {
        auto it = layer_children_.find(layer_obj);
        if (it == layer_children_.end() || idx < 0 ||
            idx >= (int)it->second.size()) return false;
        it->second[idx] = {it->second[idx].drawable_obj, l, t, r, b};
        return true;
    }
    const std::vector<ViewNode::CodeLayer>* lookup_layer_children(uint32_t layer_obj) const {
        auto it = layer_children_.find(layer_obj);
        return it == layer_children_.end() ? nullptr : &it->second;
    }

    // S83-B2 §14: materialize a code-level drawable object into the view's
    // background state (AOSP View.mBackground swap law). Resolution order:
    // LayerDrawable children → bg_layers (each child: GradientDrawable state
    // → shape layer, ColorDrawable → color layer; unsupported children skip
    // honestly), then direct GradientDrawable → bg_shape_*, then direct
    // ColorDrawable → bg_color. Returns false for untracked drawables
    // (caller records the honest UNSUPPORTED provenance bit).
    bool apply_code_background(uint32_t view_id, uint32_t drawable_obj) {
        auto* n = get_or_create_node(view_id, "");
        if (n == nullptr) return false;
        n->bg_from_xml = false;   // programmatic write = last-writer law
        auto lit = layer_children_.find(drawable_obj);
        if (lit != layer_children_.end()) {
            n->bg_layers.clear();
            for (const auto& cl : lit->second) {
                ViewNode::BgLayer L;
                if (std::getenv("MINIANDROID_SHAPE_TRACE"))
                    std::cerr << "[S83B2-MAT] child o" << cl.drawable_obj
                              << " grad=" << (gradient_states_.count(cl.drawable_obj) ? 1 : 0)
                              << " color=" << (color_drawable_colors_.count(cl.drawable_obj) ? 1 : 0)
                              << std::endl;
                L.left = cl.left; L.top = cl.top;
                L.right = cl.right; L.bottom = cl.bottom;
                auto git = gradient_states_.find(cl.drawable_obj);
                if (git != gradient_states_.end()) {
                    const auto& st = git->second;
                    L.kind = 2;
                    L.shape_kind = st.shape;
                    L.shape_has_solid = st.has_color;
                    L.shape_solid = st.color;
                    L.shape_radius = st.radius >= 0 ? st.radius : 0.0f;
                    L.shape_has_stroke = st.has_stroke;
                    L.shape_sw = st.stroke_w;
                    L.shape_sc = st.stroke_color;
                    L.shape_inner_r = st.inner_radius;
                    L.shape_thick = st.thickness;
                    L.shape_ir_ratio = st.inner_ratio;
                    L.shape_tk_ratio = st.thick_ratio;
                } else {
                    uint32_t col = 0;
                    if (!lookup_color_drawable(cl.drawable_obj, &col)) continue;
                    L.kind = 1;
                    L.color = col;
                }
                n->bg_layers.push_back(L);
            }
            if (!n->bg_layers.empty()) {
                n->bg_layers_valid = true;
                return true;
            }
            return false;
        }
        auto git = gradient_states_.find(drawable_obj);
        if (git != gradient_states_.end()) {
            const auto& st = git->second;
            n->bg_shape_valid = true;
            n->bg_shape_kind = st.shape;
            n->bg_shape_has_solid = st.has_color;
            n->bg_shape_solid = st.color;
            if (st.radius >= 0) n->bg_shape_corner_radius = st.radius;
            n->bg_shape_has_stroke = st.has_stroke;
            n->bg_shape_stroke_width = st.stroke_w;
            n->bg_shape_stroke_color = st.stroke_color;
            n->bg_shape_inner_radius = st.inner_radius;
            n->bg_shape_thickness = st.thickness;
            n->bg_shape_inner_ratio = st.inner_ratio;
            n->bg_shape_thick_ratio = st.thick_ratio;
            return true;
        }
        uint32_t col = 0;
        if (lookup_color_drawable(drawable_obj, &col)) {
            n->bg_color = col;
            return true;
        }
        return false;
    }

    // EXP-098 (CM-027): Store RLottie animation frame RGBA buffer on the
    // ViewNode. Called by the engine-side setAnimation intercept after
    // rlottie renders the requested frame(s). When the renderer visits
    // this view, it draws anim_frame_rgba at the view's bounds instead of
    // the CM-022 placeholder.
    void set_anim_frame(uint32_t view_id,
                        std::vector<uint8_t> rgba,
                        int w, int h, int total_frames) {
        auto* n = get_or_create_node(view_id, "");
        if (n == nullptr) return;
        n->anim_frame_rgba = std::move(rgba);
        n->anim_w = w;
        n->anim_h = h;
        n->anim_total_frames = total_frames;
        n->anim_current_frame = 0;
    }

    // EXP-098 (CM-027): Mark this view as a pending RLottie animation
    // target. The engine captures (raw_resid, w, h) when
    // RLottieImageView.setAnimation(R.raw.X, w, h) is called; the render
    // stage (with ApkParser access) performs the actual decode.
    void set_anim_pending(uint32_t view_id, int32_t raw_resid,
                          int w, int h) {
        auto* n = get_or_create_node(view_id, "");
        if (n == nullptr) return;
        n->anim_raw_resid = raw_resid;
        n->anim_target_w = w;
        n->anim_target_h = h;
        n->anim_decode_attempted = false;
    }

    // EXP-060: Return ALL view_ids whose class descriptor contains
    // `substring` AND that have a click listener registered.
    // Ordered by view_id descending (most-recently-created first).
    std::vector<uint32_t> find_all_with_click_listener(
        const std::string& class_substring) const;


    // Diagnostics: total node count.
    size_t node_count() const { return nodes_.size(); }

private:
    // WebSettings objects memoized per WebView object id (getSettings law:
    // one settings object per WebView, created at construction in AOSP).
    std::map<uint32_t, uint32_t> view_settings_;
    std::map<uint32_t, std::unique_ptr<ViewNode>> nodes_;
    // S82-GFX F-NEW-158: ColorDrawable object id → captured ARGB color
    // (recorded at ColorDrawable.<init>(I)/setColor(I); read by
    // setBackground(Drawable)/setBackgroundDrawable(Drawable) dispatch).
    std::map<uint32_t, uint32_t> color_drawable_colors_;
    // S83-B2 §14: code-level GradientDrawable states + LayerDrawable children.
    std::map<uint32_t, GradientState> gradient_states_;
    std::map<uint32_t, std::vector<ViewNode::CodeLayer>> layer_children_;
    // F-062: APK-captured compose_view_saveable_id_tag resource id
    // (set once by the interpreter's sget capture; single-threaded).
    static std::atomic<int32_t> compose_saveable_id_key_;
};

// ─────────────────────────────────────────────────────────────────────────
// WebSettingsShadow — S56 F-085: generic android.webkit.WebSettings model.
//
// The markdown/WebView family (billthefarmer Notes etc.) configures its
// WebView via WebSettings before any content loads. AOSP WebSettings is a
// property bag with symmetric accessors (setJavaScriptEnabled(boolean) /
// getJavaScriptEnabled()). This shadow mirrors that contract GENERICALLY:
// every setter stores its value under the property name derived from the
// method name, every getter returns the stored value (or an honest
// default). No app-specific knowledge.
// ─────────────────────────────────────────────────────────────────────────
class WebSettingsShadow : public Shadow {
public:
    std::string name() const override { return "WebSettings"; }
    bool handles_class(const std::string& class_name) const override {
        return class_name.rfind("Landroid/webkit/WebSettings", 0) == 0;
    }
    CallResult dispatch(const CallContext& ctx) override;
    std::vector<std::string> implemented_methods() const override {
        return {"getSettings", "setJavaScriptEnabled", "getJavaScriptEnabled",
                "getUserAgentString", "setLoadWithOverviewMode",
                "setUseWideViewPort", "setBuiltInZoomControls", "setTextZoom"};
    }

private:
    struct Prop {
        bool b = false;
        int64_t i = 0;
        std::string s;
    };
    // property bag per WebSettings object id: "JavaScriptEnabled" → value.
    std::map<uint32_t, std::map<std::string, Prop>> props_;
};

// ─────────────────────────────────────────────────────────────────────────
// CollectionShadow — real List/ArrayList/Map semantics with per-instance state.
//
// Instead of a global `List.isEmpty → true` stub, this shadow tracks real
// collection state per heap object. Each collection instance gets a
// CollectionState (vector of elements) keyed by object_id.
//
// Supported operations:
//   * List.add(item) → append, return true
//   * List.get(index) → return element at index
//   * List.size() → return count
//   * List.isEmpty() → return count == 0
//   * List.clear() → clear elements
//   * List.remove(index) → remove at index
//   * Map.put(key, value) → store key-value pair
//   * Map.get(key) → return value for key
//   * Map.size() → return count
//   * Map.isEmpty() → return count == 0
//   * Map.containsKey(key) → return true if key exists
//   * Iterator.hasNext() → check position < size
//   * Iterator.next() → return element at position++
//
// This is NOT a stub — it's real state-based semantics. The runtime's
// List objects actually hold elements and report correct sizes.
// ─────────────────────────────────────────────────────────────────────────
class CollectionShadow : public Shadow {
public:
    struct CollectionState {
        std::vector<uint32_t> elements;  // object_ids of elements
        std::map<std::string, uint32_t> map_entries;  // key → value object_id
        // EXP-071 Phase 7: Store string values for HashMap.put(key, String).
        // The original map_entries only stores object_ids, but many HashMap
        // usages store String values (e.g., shortname → country name).
        // Without this, HashMap.get returns null for string values.
        std::map<std::string, std::string> map_string_entries;  // key → string value
        size_t iterator_position = 0;
        bool is_map = false;
        // ── F-064 (R-NEW-288): typed elements for keySet()/values()/
        // entrySet() live views. Views must iterate TYPED elements —
        // string-typed map values and Map.Entry objects cannot live in
        // elements (object ids only). kind: 0=none, 1=object, 2=string,
        // 3=int — mirrors TagValue::Kind semantics.
        struct ViewElem {
            uint8_t kind = 0;
            uint32_t object_id = 0;
            std::string string_val;
            int32_t int_val = 0;
        };
        std::vector<ViewElem> view_elements;
        bool is_view = false;
    };

    std::string name() const override { return "Collection"; }
    void init(HeapAllocator* heap) override { heap_ = heap; }

    bool handles_class(const std::string& class_name) const override {
        return class_name == "Ljava/util/ArrayList;" ||
               class_name == "Ljava/util/LinkedList;" ||
               class_name == "Ljava/util/List;" ||
               class_name == "Ljava/util/Collection;" ||
               class_name == "Ljava/util/Iterable;" ||  // F-064: view iteration via interface call site
               class_name == "Ljava/util/CopyOnWriteArrayList;" ||
               class_name == "Ljava/util/HashMap;" ||
               // S83-B2 (R-NEW-403): dooz18 evidence — Glide's lifecycle
               // registry (Lg/b; = RequestManagerFragment Tracker) is a
               // WeakHashMap; with no handles_class entry every WeakHashMap
               // op REC-MISSed and keySet() answered null → Set.iterator()
               // NPE killed onCreate. Route the whole family to the real
               // CollectionShadow map laws (put/get/keySet/values/entrySet).
               class_name == "Ljava/util/WeakHashMap;" ||
               class_name == "Ljava/util/LinkedHashMap;" ||  // F-064: Kotlin Reflection clinit uses it directly
               class_name == "Ljava/util/Map;" ||
               class_name == "Ljava/util/Map$Entry;" ||  // F-064: entrySet() elements (getKey/getValue)
               class_name == "Ljava/util/HashSet;" ||
               class_name == "Ljava/util/Set;" ||
               // [R342-COWSET] java.util.concurrent CopyOnWrite family —
               // dooz23 evidence: MainActivity.<init> registers the Hilt
               // members-injector (Lae0; = LifecycleEventObserver) into the
               // androidx lifecycle registry's CopyOnWriteArraySet
               // (Ljm;.f → Leq;->a .add). A REC-MISS here silently dropped
               // the injector → deferred field injection never ran →
               // "lateinit property settings has not been initialized"
               // killed the Compose resume (Le;.q @944). Also fixes the
               // missing "concurrent/" segment in the COWAL path.
               class_name == "Ljava/util/concurrent/CopyOnWriteArrayList;" ||
               class_name == "Ljava/util/concurrent/CopyOnWriteArraySet;" ||
               class_name == "Ljava/util/Arrays$ArrayList;" ||
               class_name == "Ljava/util/Collections;" ||  // M3 F-ROOM-CHAIN: static factories
               class_name == "Ljava/util/Collections$UnmodifiableRandomAccessList;" ||
               class_name == "Ljava/util/Collections$SingletonList;" ||
               class_name == "Ljava/util/Iterator;" ||
               class_name == "Ljava/util/ListIterator;" ||
               class_name.find("/ArrayList;") != std::string::npos ||
               class_name.find("/HashMap;") != std::string::npos ||
               class_name.find("/HashSet;") != std::string::npos ||
               class_name.find("/LinkedHashMap;") != std::string::npos ||
               class_name.find("ConcurrentHashMap") != std::string::npos;
    }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"add", "get", "size", "isEmpty", "clear", "remove",
                "contains", "iterator", "hasNext", "next", "toArray",
                "put", "containsKey", "keySet", "values", "entrySet",
                "putAll", "getKey", "getValue", "singletonMap",
                "getIndex", "set"};
    }
    std::vector<std::string> stubbed_methods() const override {
        return {"subList", "listIterator", "sort"};
    }

    // Get or create CollectionState for a heap object.
    CollectionState* get_or_create(uint32_t object_id, bool is_map = false);

private:
    std::map<uint32_t, CollectionState> collections_;
};

}} // namespace miniandroid::framework

#endif // MINIANDROID_FRAMEWORK_ANDROID_SHADOWS_H
