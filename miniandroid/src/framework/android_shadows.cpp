// SPDX-License-Identifier: MIT
// MiniAndroid Compatibility Runtime
// EXP-051 — Concrete Android framework shadows (implementation)

#include "android_shadows.h"

#include <algorithm>
#include <chrono>
#include <iostream>
#include <queue>
#include <sstream>
#include <utility>

namespace miniandroid { namespace framework {

// ─────────────────────────────────────────────────────────────────────────
// Helpers — convert CallContext args into CallResult values
// ─────────────────────────────────────────────────────────────────────────
namespace {

// True if class_name matches an Android Context-derived class.
bool is_context_class(const std::string& class_name) {
    return class_name.find("Context;")   != std::string::npos ||
           class_name.find("Activity;")   != std::string::npos ||
           class_name.find("Application;")!= std::string::npos;
}

} // anonymous namespace

// ─────────────────────────────────────────────────────────────────────────
// CollectionShadow — real List/ArrayList/Map semantics.
// ─────────────────────────────────────────────────────────────────────────
CollectionShadow::CollectionState* CollectionShadow::get_or_create(uint32_t object_id, bool is_map) {
    auto it = collections_.find(object_id);
    if (it != collections_.end()) {
        if (is_map) it->second.is_map = true;
        return &it->second;
    }
    auto& state = collections_[object_id];
    state.is_map = is_map;
    return &state;
}

CallResult CollectionShadow::dispatch(const CallContext& ctx) {
    const auto& m = ctx.method;
    uint32_t obj_id = ctx.receiver_id;

    // <init> — no-op, just mark the collection as existing.
    if (m == "<init>") {
        bool is_map = (ctx.class_name.find("Map") != std::string::npos ||
                       ctx.class_name.find("Set") != std::string::npos);
        get_or_create(obj_id, is_map);
        return CallResult::handled_void();
    }

    // List operations
    if (m == "add") {
        // add(item) or add(index, item)
        auto* state = get_or_create(obj_id);
        if (ctx.args.size() >= 2) {
            // add(index, item)
            int32_t idx = ctx.arg_as_int(0);
            uint32_t item = ctx.arg_as_object(1, 0);
            if (idx >= 0 && (size_t)idx <= state->elements.size()) {
                state->elements.insert(state->elements.begin() + idx, item);
            }
        } else if (ctx.args.size() >= 1) {
            // add(item)
            uint32_t item = ctx.arg_as_object(0, 0);
            state->elements.push_back(item);
        }
        return CallResult::handled_bool(true);
    }

    if (m == "get") {
        // get(index) → element
        auto* state = get_or_create(obj_id);
        int32_t idx = ctx.arg_as_int(0, -1);
        if (idx >= 0 && (size_t)idx < state->elements.size()) {
            uint32_t elem = state->elements[idx];
            if (elem != 0) {
                return CallResult::handled_object(elem, "Ljava/lang/Object;");
            }
            return CallResult::handled_null();
        }
        return CallResult::handled_null();
    }

    if (m == "size") {
        auto* state = get_or_create(obj_id);
        if (state->is_map) {
            return CallResult::handled_int(static_cast<int32_t>(state->map_entries.size()));
        }
        return CallResult::handled_int(static_cast<int32_t>(state->elements.size()));
    }

    if (m == "isEmpty") {
        auto* state = get_or_create(obj_id);
        if (state->is_map) {
            return CallResult::handled_bool(state->map_entries.empty());
        }
        return CallResult::handled_bool(state->elements.empty());
    }

    if (m == "clear") {
        auto* state = get_or_create(obj_id);
        state->elements.clear();
        state->map_entries.clear();
        state->iterator_position = 0;
        return CallResult::handled_void();
    }

    if (m == "remove") {
        auto* state = get_or_create(obj_id);
        if (ctx.args.size() >= 1) {
            int32_t idx = ctx.arg_as_int(0, -1);
            if (idx >= 0 && (size_t)idx < state->elements.size()) {
                state->elements.erase(state->elements.begin() + idx);
            }
        }
        return CallResult::handled_void();
    }

    if (m == "contains") {
        auto* state = get_or_create(obj_id);
        uint32_t item = ctx.arg_as_object(0, 0);
        for (uint32_t e : state->elements) {
            if (e == item) return CallResult::handled_bool(true);
        }
        return CallResult::handled_bool(false);
    }

    if (m == "iterator") {
        auto* state = get_or_create(obj_id);
        state->iterator_position = 0;
        // Return the same object as the iterator (simplified).
        return CallResult::handled_object(obj_id, ctx.class_name);
    }

    if (m == "hasNext") {
        auto* state = get_or_create(obj_id);
        return CallResult::handled_bool(state->iterator_position < state->elements.size());
    }

    if (m == "next") {
        auto* state = get_or_create(obj_id);
        if (state->iterator_position < state->elements.size()) {
            uint32_t elem = state->elements[state->iterator_position++];
            if (elem != 0) {
                return CallResult::handled_object(elem, "Ljava/lang/Object;");
            }
            return CallResult::handled_null();
        }
        return CallResult::handled_null();
    }

    // Map operations
    if (m == "put") {
        auto* state = get_or_create(obj_id, true);
        if (ctx.args.size() >= 2) {
            std::string key = ctx.arg_as_string(0);
            uint32_t value = ctx.arg_as_object(1, 0);
            // Use key as the map key. For object keys, use object_id as string.
            if (key.empty() && ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
                key = "obj:" + std::to_string(ctx.args[0].object_id);
            }
            state->map_entries[key] = value;
        }
        return CallResult::handled_null();
    }

    if (m == "containsKey") {
        auto* state = get_or_create(obj_id, true);
        std::string key = ctx.arg_as_string(0);
        if (key.empty() && !ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
            key = "obj:" + std::to_string(ctx.args[0].object_id);
        }
        return CallResult::handled_bool(state->map_entries.count(key) > 0);
    }

    if (m == "set") {
        // set(index, item) — replace element at index
        auto* state = get_or_create(obj_id);
        if (ctx.args.size() >= 2) {
            int32_t idx = ctx.arg_as_int(0, -1);
            uint32_t item = ctx.arg_as_object(1, 0);
            if (idx >= 0 && (size_t)idx < state->elements.size()) {
                state->elements[idx] = item;
            }
        }
        return CallResult::handled_void();
    }

    // Generic stubs for less common methods.
    if (m == "keySet" || m == "values" || m == "entrySet" ||
        m == "subList" || m == "listIterator" || m == "toArray" ||
        m == "sort" || m == "getIndex") {
        return CallResult::handled_void();
    }

    return CallResult::not_handled();
}

// ─────────────────────────────────────────────────────────────────────────
// ArchTaskExecutorShadow
// ─────────────────────────────────────────────────────────────────────────
CallResult ArchTaskExecutorShadow::dispatch(const CallContext& ctx) {
    const auto& m = ctx.method;
    if (m == "getInstance") {
        // Returns the singleton ArchTaskExecutor instance.
        if (instance_id_ == 0 && heap_) {
            instance_id_ = heap_->get_or_create("Landroidx/arch/core/executor/ArchTaskExecutor;");
        }
        return CallResult::handled_object(instance_id_,
                                           "Landroidx/arch/core/executor/ArchTaskExecutor;");
    }
    if (m == "isMainThread") {
        // Real semantics: mDelegate.isMainThread() which (for DefaultTaskExecutor)
        // does: return Looper.getMainLooper().getThread() == Thread.currentThread().
        //
        // We don't have an mDelegate instance to call into, but we DO have the
        // ThreadShadow + LooperShadow identity contract. Both Looper.getThread()
        // and Thread.currentThread() return the SAME object_id. So this is true.
        //
        // To prove the identity, look up both shadows via the registry and
        // verify they're bound to the same id.
        if (registry_) {
            if (auto* ts = registry_->find_as<ThreadShadow>()) {
                if (auto* ls = registry_->find_as<LooperShadow>()) {
                    uint32_t main_thread = ts->main_thread_id();
                    uint32_t bound = ls->bound_thread_id();
                    if (main_thread != 0 && main_thread == bound) {
                        // Identity contract holds — return true.
                        return CallResult::handled_bool(true);
                    }
                }
            }
        }
        // Identity not yet established — return false (matches real Android
        // when mDelegate is null, which would NPE).
        return CallResult::handled_bool(false);
    }
    if (m == "executeOnDiskIO" || m == "postToMainThread" ||
        m == "delegate" || m == "setDelegate") {
        // executeOnDiskIO(Runnable) → enqueue on disk thread (we use a no-op).
        // postToMainThread(Runnable) → enqueue via HandlerShadow.
        if (m == "postToMainThread" && registry_) {
            if (auto* hs = registry_->find_as<HandlerShadow>()) {
                uint32_t r = HandlerShadow::extract_runnable(ctx, 0);
                if (r != 0) hs->enqueue(r, 0, /*cls=*/"ArchTaskExecutor");
            }
        }
        return CallResult::handled_void();
    }
    return CallResult::not_handled();
}

// ─────────────────────────────────────────────────────────────────────────
// ThreadShadow
// ─────────────────────────────────────────────────────────────────────────
CallResult ThreadShadow::dispatch(const CallContext& ctx) {
    const auto& m = ctx.method;
    if (m == "currentThread") {
        return CallResult::handled_object(main_thread_id_, "Ljava/lang/Thread;");
    }
    if (m == "getName") {
        return CallResult::handled_string(MAIN_THREAD_NAME);
    }
    if (m == "getId") {
        return CallResult::handled_long(MAIN_THREAD_TID);
    }
    if (m == "getStackTrace") {
        // Return null for now — array-length handler in the engine returns 0
        // for null arrays, which lets Intrinsics.createParameterIsNullExceptionMessage
        // terminate its stack-walk loop. (See EXP-043 Phase 3 fix.)
        return CallResult::handled_null();
    }
    if (m == "isAlive")      return CallResult::handled_bool(true);
    if (m == "isDaemon")     return CallResult::handled_bool(false);
    if (m == "isInterrupted")return CallResult::handled_bool(false);
    if (m == "interrupt" || m == "join" || m == "start" || m == "run" ||
        m == "setDaemon" || m == "setName" || m == "setPriority" ||
        m == "sleep" || m == "yield" || m == "holdsLock" ||
        m == "getContextClassLoader" || m == "setContextClassLoader" ||
        m == "getUncaughtExceptionHandler" || m == "setUncaughtExceptionHandler") {
        return CallResult::handled_void();
    }
    if (m == "equals") {
        uint32_t other = ctx.arg_as_object(0, 0);
        return CallResult::handled_bool(other == main_thread_id_);
    }
    if (m == "hashCode") {
        return CallResult::handled_int(static_cast<int32_t>(main_thread_id_));
    }
    if (m == "toString") {
        std::string s = std::string("Thread[") + MAIN_THREAD_NAME +
                        ",5,main]";
        return CallResult::handled_string(s);
    }
    return CallResult::not_handled();
}

// ─────────────────────────────────────────────────────────────────────────
// LooperShadow
// ─────────────────────────────────────────────────────────────────────────
CallResult LooperShadow::dispatch(const CallContext& ctx) {
    const auto& m = ctx.method;
    if (ctx.class_name == "Landroid/os/Looper;") {
        if (m == "getMainLooper" || m == "myLooper") {
            return CallResult::handled_object(main_looper_id_, "Landroid/os/Looper;");
        }
        if (m == "getThread") {
            // Critical identity contract: Looper.getThread() must return
            // the SAME object_id as Thread.currentThread(). The bridge
            // binds this id at startup via bind_to_thread().
            uint32_t tid = bound_thread_id_;
            if (tid == 0 && heap_) {
                // Lazy bind: ask the heap for the main Thread singleton.
                tid = heap_->get_or_create("Ljava/lang/Thread;");
                bound_thread_id_ = tid;
            }
            return CallResult::handled_object(tid, "Ljava/lang/Thread;");
        }
        if (m == "getQueue" || m == "myQueue") {
            return CallResult::handled_object(main_queue_id_, "Landroid/os/MessageQueue;");
        }
        if (m == "prepare" || m == "loop" || m == "prepareMainLooper" ||
            m == "quit" || m == "quitSafely") {
            return CallResult::handled_void();
        }
        if (m == "isCurrentThread") {
            return CallResult::handled_bool(true);
        }
        if (m == "getMainLooperId" || m == "toString" || m == "dump") {
            return CallResult::handled_void();
        }
    }
    if (ctx.class_name == "Landroid/os/MessageQueue;") {
        // MessageQueue — no real implementation needed.
        if (m == "<init>" || m == "quit" || m == "enqueueMessage" ||
            m == "removeMessages" || m == "hasMessages") {
            return CallResult::handled_void();
        }
        if (m == "next" || m == "pollOnce") {
            // No real messages — return null. Engine's null check will exit
            // Looper.loop() immediately if a real loop is reached.
            return CallResult::handled_null();
        }
    }
    return CallResult::not_handled();
}

// ─────────────────────────────────────────────────────────────────────────
// HandlerShadow
// ─────────────────────────────────────────────────────────────────────────
uint32_t HandlerShadow::extract_runnable(const CallContext& ctx, size_t arg_idx) {
    if (arg_idx >= ctx.args.size()) return 0;
    const auto& a = ctx.args[arg_idx];
    if (a.kind == CallContext::Arg::Kind::OBJECT)  return a.object_id;
    if (a.kind == CallContext::Arg::Kind::NULL_REF) return 0;
    return 0;
}

void HandlerShadow::enqueue(uint32_t runnable_id, int64_t delay_ms,
                            const std::string& cls) {
    if (runnable_id == 0) return;
    QueuedRunnable q;
    q.runnable_id = runnable_id;
    q.enqueue_seq = next_seq_++;
    auto now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
    q.ready_at_ms = now_ms + delay_ms;
    q.runnable_class = cls;
    queue_.push_back(std::move(q));
    // EXP-052: Trace queue activity for diagnostics.
    std::cerr << "[QUEUE] Runnable id=" << runnable_id
              << " enqueued (delay=" << delay_ms << "ms"
              << ", queue_depth=" << queue_.size()
              << (cls.empty() ? "" : (", source=" + cls))
              << ")" << std::endl;
}

size_t HandlerShadow::drain_ready(std::vector<uint32_t>* out_drained) {
    if (!out_drained) return 0;
    auto now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();

    size_t drained = 0;
    // Note: we walk the deque in FIFO order, NOT priority-queue order.
    // This matches real Android Handler behavior — messages are queued
    // in the order they're posted, with delay acting as a minimum
    // "ready" timestamp. Real Android sorts by ready_at, but in our
    // single-threaded deterministic model we process everything in
    // enqueue order to keep behavior reproducible.
    std::vector<QueuedRunnable> ready;
    std::vector<QueuedRunnable> not_ready;
    while (!queue_.empty()) {
        auto q = std::move(queue_.front());
        queue_.pop_front();
        if (q.ready_at_ms <= now_ms) {
            ready.push_back(std::move(q));
        } else {
            not_ready.push_back(std::move(q));
        }
    }
    // Re-enqueue the not-ready ones, preserving order.
    for (auto& q : not_ready) queue_.push_back(std::move(q));
    // Drain ready ones in enqueue order.
    std::sort(ready.begin(), ready.end(),
              [](const QueuedRunnable& a, const QueuedRunnable& b) {
                  if (a.ready_at_ms != b.ready_at_ms) return a.ready_at_ms < b.ready_at_ms;
                  return a.enqueue_seq < b.enqueue_seq;
              });
    for (auto& q : ready) {
        out_drained->push_back(q.runnable_id);
        std::cerr << "[QUEUE] Runnable id=" << q.runnable_id
                  << " dequeued (ready for execution)"
                  << std::endl;
        drained++;
    }
    return drained;
}

CallResult HandlerShadow::dispatch(const CallContext& ctx) {
    const auto& m = ctx.method;

    if (ctx.class_name == "Landroid/os/Handler;") {
        if (m == "<init>") {
            // Handler() and Handler(Looper) and Handler(Callback) — no-op,
            // the heap object already exists (allocated by new-instance).
            return CallResult::handled_void();
        }
        if (m == "post" || m == "postAtFrontOfQueue") {
            uint32_t r = extract_runnable(ctx, 0);
            if (r == 0) return CallResult::handled_bool(false);
            enqueue(r, 0, /*cls=*/"");
            return CallResult::handled_bool(true);
        }
        if (m == "postDelayed") {
            uint32_t r = extract_runnable(ctx, 0);
            int64_t delay = ctx.args.size() >= 2 ? ctx.args[1].long_val : 0;
            if (r == 0) return CallResult::handled_bool(false);
            enqueue(r, delay, /*cls=*/"");
            return CallResult::handled_bool(true);
        }
        if (m == "postDelayed") {
            return CallResult::handled_bool(true);
        }
        if (m == "removeCallbacks" || m == "removeCallbacksAndMessages" ||
            m == "removeMessages" || m == "hasMessages" || m == "hasCallbacks") {
            return CallResult::handled_void();
        }
        if (m == "getLooper") {
            // Return the main Looper singleton (not strictly correct if
            // this Handler was created with a worker Looper, but we have
            // only one Looper in the model).
            if (heap_) {
                uint32_t lid = heap_->get_or_create("Landroid/os/Looper;");
                return CallResult::handled_object(lid, "Landroid/os/Looper;");
            }
            return CallResult::handled_null();
        }
        if (m == "sendEmptyMessage" || m == "sendMessage" ||
            m == "sendMessageDelayed" || m == "sendMessageAtTime" ||
            m == "obtainMessage") {
            return CallResult::handled_bool(true);
        }
        if (m == "toString") return CallResult::handled_string("Handler");
    }

    if (ctx.class_name == "Lorg/telegram/messenger/AndroidUtilities;") {
        // Telegram-specific UI scheduling wrappers.
        if (m == "runOnUIThread" || m == "executeOnUIThread") {
            uint32_t r = extract_runnable(ctx, 0);
            if (r == 0) return CallResult::handled_void();
            enqueue(r, 0, /*cls=*/"");
            return CallResult::handled_void();
        }
        if (m == "cancelRunOnUIThread") {
            // Remove a Runnable from the queue by object_id.
            uint32_t r = extract_runnable(ctx, 0);
            if (r != 0) {
                std::deque<QueuedRunnable> kept;
                while (!queue_.empty()) {
                    auto q = std::move(queue_.front()); queue_.pop_front();
                    if (q.runnable_id != r) kept.push_back(std::move(q));
                }
                queue_ = std::move(kept);
            }
            return CallResult::handled_void();
        }
    }
    return CallResult::not_handled();
}

// ─────────────────────────────────────────────────────────────────────────
// IntentShadow
// ─────────────────────────────────────────────────────────────────────────
std::shared_ptr<IntentShadow::PendingIntent> IntentShadow::get_or_create_intent(uint32_t object_id) {
    auto it = intents_.find(object_id);
    if (it != intents_.end()) return it->second;
    auto p = std::make_shared<PendingIntent>();
    intents_[object_id] = p;
    return p;
}

CallResult IntentShadow::dispatch(const CallContext& ctx) {
    const auto& m = ctx.method;
    // The Intent object_id is the receiver for instance methods.
    if (m == "<init>") {
        // Intent(), Intent(String action), Intent(Context, Class),
        // Intent(String action, Uri) — all initialize the receiver.
        auto pi = get_or_create_intent(ctx.receiver_id);
        if (ctx.args.size() >= 1) {
            // First arg can be action (String) or Context (Object).
            const auto& a = ctx.args[0];
            if (a.kind == CallContext::Arg::Kind::STRING) {
                pi->action = a.string_val;
            }
        }
        return CallResult::handled_void();
    }
    auto pi = get_or_create_intent(ctx.receiver_id);
    if (pi == nullptr) return CallResult::not_handled();

    if (m == "setAction") {
        pi->action = ctx.arg_as_string(0);
        return CallResult::handled_object(ctx.receiver_id, "Landroid/content/Intent;");
    }
    if (m == "getAction") {
        return CallResult::handled_string(pi->action);
    }
    if (m == "setClass" || m == "setClassName" || m == "setComponent") {
        // setClass(Context, Class), setClassName(Context, String),
        // setComponent(ComponentName). We treat the class-name arg.
        if (m == "setClass") {
            // Arg 1 is a Class object — its heap class_desc is the Activity class.
            if (ctx.args.size() >= 2 && ctx.args[1].kind == CallContext::Arg::Kind::OBJECT) {
                pi->component_class = ctx.args[1].object_class;
            }
        } else {
            // setClassName(Context, String) or setComponent(ComponentName).
            std::string s = ctx.arg_as_string(ctx.args.size() >= 2 ? 1 : 0);
            if (!s.empty()) pi->component_class = s;
        }
        return CallResult::handled_object(ctx.receiver_id, "Landroid/content/Intent;");
    }
    if (m == "getComponent") {
        if (pi->component_class.empty()) return CallResult::handled_null();
        // Return a ComponentName heap object.
        if (heap_) {
            uint32_t cn = heap_->get_or_create("Landroid/content/ComponentName;");
            return CallResult::handled_object(cn, "Landroid/content/ComponentName;");
        }
        return CallResult::handled_null();
    }
    if (m == "putExtra") {
        if (ctx.args.size() >= 2) {
            const auto& key = ctx.args[0];
            const auto& val = ctx.args[1];
            std::string k = (key.kind == CallContext::Arg::Kind::STRING) ? key.string_val : "";
            if (val.kind == CallContext::Arg::Kind::STRING) {
                pi->extras_string[k] = val.string_val;
            } else if (val.kind == CallContext::Arg::Kind::INT) {
                pi->extras_int[k] = val.int_val;
            } else if (val.kind == CallContext::Arg::Kind::BOOL) {
                pi->extras_bool[k] = val.bool_val;
            } else if (val.kind == CallContext::Arg::Kind::LONG) {
                pi->extras_int[k] = static_cast<int32_t>(val.long_val);
            }
        }
        return CallResult::handled_object(ctx.receiver_id, "Landroid/content/Intent;");
    }
    if (m == "getStringExtra") {
        std::string k = ctx.arg_as_string(0);
        auto it = pi->extras_string.find(k);
        if (it != pi->extras_string.end()) return CallResult::handled_string(it->second);
        return CallResult::handled_null();
    }
    if (m == "getIntExtra") {
        std::string k = ctx.arg_as_string(0);
        int32_t def = ctx.arg_as_int(1, 0);
        auto it = pi->extras_int.find(k);
        return CallResult::handled_int(it != pi->extras_int.end() ? it->second : def);
    }
    if (m == "getBooleanExtra") {
        std::string k = ctx.arg_as_string(0);
        bool def = ctx.arg_as_bool(1, false);
        auto it = pi->extras_bool.find(k);
        return CallResult::handled_bool(it != pi->extras_bool.end() ? it->second : def);
    }
    if (m == "setFlags" || m == "addFlags") {
        int32_t f = ctx.arg_as_int(0);
        if (m == "setFlags") pi->flags = f; else pi->flags |= f;
        return CallResult::handled_object(ctx.receiver_id, "Landroid/content/Intent;");
    }
    if (m == "getFlags") {
        return CallResult::handled_int(pi->flags);
    }
    if (m == "setPackage") {
        pi->package_name = ctx.arg_as_string(0);
        return CallResult::handled_object(ctx.receiver_id, "Landroid/content/Intent;");
    }
    return CallResult::not_handled();
}

// ─────────────────────────────────────────────────────────────────────────
// ActivityShadow
// ─────────────────────────────────────────────────────────────────────────
CallResult ActivityShadow::dispatch(const CallContext& ctx) {
    const auto& m = ctx.method;
    // Activity instance methods
    if (m == "setContentView") {
        // setContentView(View) or setContentView(int).
        if (!ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
            content_view_id_ = ctx.args[0].object_id;
        }
        return CallResult::handled_void();
    }
    if (m == "getContentView") {
        if (content_view_id_ == 0) return CallResult::handled_null();
        return CallResult::handled_object(content_view_id_, "Landroid/view/View;");
    }
    if (m == "findViewById") {
        // No real view hierarchy yet — return null.
        return CallResult::handled_null();
    }
    if (m == "getIntent") {
        // Return null Intent. Telegram checks for null and falls through.
        return CallResult::handled_null();
    }
    if (m == "setIntent") {
        return CallResult::handled_void();
    }
    if (m == "finish") {
        state_ = LifecycleState::DESTROYED;
        return CallResult::handled_void();
    }
    if (m == "getApplicationContext") {
        if (heap_) {
            uint32_t ctx_id = heap_->get_or_create("Landroid/content/Context;");
            return CallResult::handled_object(ctx_id, "Landroid/content/Context;");
        }
        return CallResult::handled_null();
    }
    if (m == "getResources" || m == "getPackageManager" || m == "getPackageName" ||
        m == "getClassLoader" || m == "getFilesDir" || m == "getCacheDir" ||
        m == "getSharedPreferences" || m == "getWindow" || m == "getWindowManager" ||
        m == "getFragmentManager" || m == "getCallingActivity" || m == "getCallingPackage" ||
        m == "startActivityForResult" || m == "startActivityFromChild" ||
        m == "startActivityIfNeeded" || m == "startNextMatchingActivity") {
        // Let these fall through to the legacy bridge which has more
        // specific handlers (e.g. getResources → Resources singleton).
        return CallResult::not_handled();
    }
    // startActivity(Intent) — record the pending intent on the IntentShadow.
    // The ApplicationRuntime will read pending_ on the next drain point and
    // invoke the target Activity's onCreate.
    if (m == "startActivity" || m == "startActivityForResult") {
        // Find the IntentShadow via the registry.
        if (registry_) {
            if (auto* intent_shadow = registry_->find_as<IntentShadow>()) {
                // First arg (after `this`) is the Intent heap object.
                uint32_t intent_id = 0;
                if (!ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
                    intent_id = ctx.args[0].object_id;
                }
                if (intent_id != 0) {
                    auto pi = intent_shadow->get_or_create_intent(intent_id);
                    intent_shadow->set_pending(pi);
                    if (!pi->component_class.empty()) {
                        std::cerr << "[INTENT] startActivity called → "
                                  << pi->component_class << std::endl;
                    } else {
                        std::cerr << "[INTENT] startActivity called (no component set)"
                                  << std::endl;
                    }
                }
            }
        }
        return CallResult::handled_void();
    }
    if (m == "runOnUiThread") {
        // Defer to HandlerShadow — return void so the call doesn't
        // recurse into AndroidUtilities.runOnUIThread (which the engine
        // might have a stub for already).
        return CallResult::handled_void();
    }
    return CallResult::not_handled();
}

// ─────────────────────────────────────────────────────────────────────────
// ViewShadow
// ─────────────────────────────────────────────────────────────────────────
uint32_t ViewShadow::create_view(const std::string& class_desc) {
    if (!heap_) return 0;
    uint32_t id = heap_->allocate(class_desc);
    auto node = std::make_unique<ViewNode>();
    node->view_id = id;
    node->class_desc = class_desc;
    nodes_[id] = std::move(node);
    return id;
}

ViewShadow::ViewNode* ViewShadow::get_or_create_node(uint32_t view_id,
                                                      const std::string& class_desc) {
    auto it = nodes_.find(view_id);
    if (it != nodes_.end()) return it->second.get();
    auto node = std::make_unique<ViewNode>();
    node->view_id = view_id;
    node->class_desc = class_desc;
    auto* raw = node.get();
    nodes_[view_id] = std::move(node);
    return raw;
}

const ViewShadow::ViewNode* ViewShadow::find_node(uint32_t view_id) const {
    auto it = nodes_.find(view_id);
    if (it != nodes_.end()) return it->second.get();
    return nullptr;
}

ViewShadow::ViewNode* ViewShadow::find_node(uint32_t view_id) {
    auto it = nodes_.find(view_id);
    if (it != nodes_.end()) return it->second.get();
    return nullptr;
}

bool ViewShadow::add_child(uint32_t parent_id, uint32_t child_id) {
    auto* parent = find_node(parent_id);
    auto* child  = find_node(child_id);
    if (!parent || !child) return false;
    // Remove from previous parent if any.
    if (child->parent_id != 0 && child->parent_id != parent_id) {
        if (auto* prev = find_node(child->parent_id)) {
            prev->children.erase(
                std::remove(prev->children.begin(), prev->children.end(), child_id),
                prev->children.end());
        }
    }
    child->parent_id = parent_id;
    parent->children.push_back(child_id);
    return true;
}

bool ViewShadow::remove_child(uint32_t parent_id, uint32_t child_id) {
    auto* parent = find_node(parent_id);
    auto* child  = find_node(child_id);
    if (!parent || !child) return false;
    parent->children.erase(
        std::remove(parent->children.begin(), parent->children.end(), child_id),
        parent->children.end());
    if (child->parent_id == parent_id) child->parent_id = 0;
    return true;
}

uint32_t ViewShadow::find_by_android_id(uint32_t root_id, int32_t android_id) const {
    // BFS
    std::vector<uint32_t> frontier = {root_id};
    while (!frontier.empty()) {
        std::vector<uint32_t> next;
        for (uint32_t id : frontier) {
            const auto* n = find_node(id);
            if (!n) continue;
            if (n->android_view_id == android_id) return id;
            for (uint32_t c : n->children) next.push_back(c);
        }
        frontier = std::move(next);
    }
    return 0;
}

CallResult ViewShadow::dispatch(const CallContext& ctx) {
    const auto& m = ctx.method;
    // View instance methods — receiver_id is the View heap object_id.

    if (m == "<init>") {
        // View(Context), View(Context, AttributeSet), View(Context, AttributeSet, int)
        // Allocate a fresh node bound to this receiver.
        get_or_create_node(ctx.receiver_id, ctx.class_name);
        return CallResult::handled_void();
    }
    if (m == "setId") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.class_name);
        n->android_view_id = ctx.arg_as_int(0);
        return CallResult::handled_void();
    }
    if (m == "getId") {
        const auto* n = find_node(ctx.receiver_id);
        return CallResult::handled_int(n ? n->android_view_id : 0);
    }
    if (m == "getParent") {
        const auto* n = find_node(ctx.receiver_id);
        if (!n || n->parent_id == 0) return CallResult::handled_null();
        return CallResult::handled_object(n->parent_id, "Landroid/view/ViewParent;");
    }
    if (m == "addView" || m == "addViewInLayout") {
        uint32_t child = ctx.arg_as_object(0, 0);
        if (child == 0) return CallResult::handled_void();
        add_child(ctx.receiver_id, child);
        return CallResult::handled_void();
    }
    if (m == "removeView" || m == "removeViewInLayout") {
        uint32_t child = ctx.arg_as_object(0, 0);
        if (child != 0) remove_child(ctx.receiver_id, child);
        return CallResult::handled_void();
    }
    if (m == "removeAllViews" || m == "removeAllViewsInLayout") {
        auto* n = find_node(ctx.receiver_id);
        if (n) {
            for (uint32_t c : n->children) {
                if (auto* child = find_node(c)) child->parent_id = 0;
            }
            n->children.clear();
        }
        return CallResult::handled_void();
    }
    if (m == "getChildAt") {
        auto* n = find_node(ctx.receiver_id);
        if (!n) return CallResult::handled_null();
        int32_t idx = ctx.arg_as_int(0, -1);
        if (idx < 0 || (size_t)idx >= n->children.size()) return CallResult::handled_null();
        return CallResult::handled_object(n->children[idx], "Landroid/view/View;");
    }
    if (m == "getChildCount") {
        const auto* n = find_node(ctx.receiver_id);
        return CallResult::handled_int(n ? static_cast<int32_t>(n->children.size()) : 0);
    }
    if (m == "findViewById") {
        int32_t target_id = ctx.arg_as_int(0, 0);
        uint32_t found = find_by_android_id(ctx.receiver_id, target_id);
        if (found == 0) return CallResult::handled_null();
        return CallResult::handled_object(found, "Landroid/view/View;");
    }
    if (m == "findViewWithTag") {
        // Tag is an Object — we don't track tags.
        return CallResult::handled_null();
    }
    if (m == "setVisibility") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.class_name);
        n->visibility = ctx.arg_as_int(0, 0);
        return CallResult::handled_void();
    }
    if (m == "getVisibility") {
        const auto* n = find_node(ctx.receiver_id);
        return CallResult::handled_int(n ? n->visibility : 0);
    }
    if (m == "setEnabled") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.class_name);
        n->enabled = ctx.arg_as_bool(0, true);
        return CallResult::handled_void();
    }
    if (m == "isEnabled") {
        const auto* n = find_node(ctx.receiver_id);
        return CallResult::handled_bool(n ? n->enabled : true);
    }
    if (m == "setClickable") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.class_name);
        n->clickable = ctx.arg_as_bool(0, false);
        return CallResult::handled_void();
    }
    if (m == "isClickable") {
        const auto* n = find_node(ctx.receiver_id);
        return CallResult::handled_bool(n ? n->clickable : false);
    }
    if (m == "setText") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.class_name);
        n->text = ctx.arg_as_string(0);
        return CallResult::handled_void();
    }
    if (m == "getText") {
        const auto* n = find_node(ctx.receiver_id);
        return CallResult::handled_string(n ? n->text : "");
    }
    if (m == "setBackgroundColor" || m == "setBackground" ||
        m == "setBackgroundResource" || m == "setBackgroundDrawable" ||
        m == "setLayoutParams" || m == "getLayoutParams" ||
        m == "measure" || m == "layout" || m == "draw" ||
        m == "requestLayout" || m == "invalidate" ||
        m == "post" || m == "postDelayed" || m == "removeCallbacks") {
        return CallResult::handled_void();
    }
    if (m == "getLayoutParams") {
        return CallResult::handled_null();
    }
    if (m == "onMeasure" || m == "onLayout" || m == "onDraw" ||
        m == "onTouchEvent" || m == "onAttachedToWindow" ||
        m == "onDetachedFromWindow") {
        return CallResult::handled_void();
    }
    if (m == "toString") {
        return CallResult::handled_string("View");
    }
    if (m == "equals") {
        uint32_t other = ctx.arg_as_object(0, 0);
        return CallResult::handled_bool(other == ctx.receiver_id);
    }
    if (m == "hashCode") {
        return CallResult::handled_int(static_cast<int32_t>(ctx.receiver_id));
    }
    return CallResult::not_handled();
}

}} // namespace miniandroid::framework
