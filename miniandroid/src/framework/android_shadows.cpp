// SPDX-License-Identifier: MIT
// MiniAndroid Compatibility Runtime
// EXP-051 — Concrete Android framework shadows (implementation)

#include "android_shadows.h"

#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <queue>
#include <sstream>
#include <utility>

// EXP-087 Phase 3 (B2 FIX): JSON for layout_cache.json parsing
#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid { namespace framework {

using json = nlohmann::json;

// ============================================================================
// EXP-087 Phase 3 (B2 FIX): inflate_view_tree — recursively create ViewShadow
// nodes from the layout cache JSON. Each node has:
//   tag       → View class name (e.g. "LinearLayout", "TextView", "Button")
//   attributes → key-value pairs (e.g. "text" → "Push buttons to roll!")
//   children  → child nodes
// ============================================================================
static uint32_t inflate_view_tree(ViewShadow* vs, const json& node, uint32_t parent_id) {
    if (!vs || node.is_null()) return 0;

    std::string tag = node.value("tag", "");
    if (tag.empty()) return 0;

    // Map XML tag → DEX class descriptor
    std::string class_desc;
    if (tag == "LinearLayout") class_desc = "Landroid/widget/LinearLayout;";
    else if (tag == "TextView") class_desc = "Landroid/widget/TextView;";
    else if (tag == "Button") class_desc = "Landroid/widget/Button;";
    else if (tag == "ImageView") class_desc = "Landroid/widget/ImageView;";
    else if (tag == "ImageButton") class_desc = "Landroid/widget/ImageButton;";
    else if (tag == "EditText") class_desc = "Landroid/widget/EditText;";
    else if (tag == "FrameLayout") class_desc = "Landroid/widget/FrameLayout;";
    else if (tag == "ScrollView") class_desc = "Landroid/widget/ScrollView;";
    else if (tag == "ListView") class_desc = "Landroid/widget/ListView;";
    else if (tag == "RelativeLayout") class_desc = "Landroid/widget/RelativeLayout;";
    else if (tag == "TableLayout") class_desc = "Landroid/widget/TableLayout;";
    else if (tag == "TableRow") class_desc = "Landroid/widget/TableRow;";
    else if (tag == "merge") class_desc = "Landroid/view/ViewGroup;";
    else class_desc = "Landroid/view/View;";  // Generic fallback

    // Create the ViewShadow node
    uint32_t view_id = vs->create_view(class_desc);
    if (view_id == 0) return 0;

    // Get or create the ViewNode
    auto* vnode = vs->get_or_create_node(view_id, class_desc);
    if (!vnode) return 0;

    // Apply attributes
    if (node.contains("attributes") && node["attributes"].is_object()) {
        for (auto it = node["attributes"].begin(); it != node["attributes"].end(); ++it) {
            const std::string& attr_name = it.key();
            std::string attr_val = it.value().is_string() ?
                it.value().get<std::string>() :
                it.value().dump();

            if (attr_name == "text") {
                vnode->text = attr_val;
            } else if (attr_name == "id") {
                if (attr_val.size() > 4 && attr_val.substr(0, 4) == "@0x7") {
                    try {
                        vnode->android_view_id = std::stoul(attr_val.substr(1), nullptr, 16);
                    } catch (...) {}
                }
            } else if (attr_name == "layout_width") {
                if (attr_val == "-1") vnode->width = -1;  // MATCH_PARENT
                else if (attr_val == "-2") vnode->width = -2;  // WRAP_CONTENT
                else { try { vnode->width = std::stoi(attr_val); } catch (...) {} }
            } else if (attr_name == "layout_height") {
                if (attr_val == "-1") vnode->height = -1;
                else if (attr_val == "-2") vnode->height = -2;
                else { try { vnode->height = std::stoi(attr_val); } catch (...) {} }
            } else if (attr_name == "src") {
                // EXP-088 Phase A4: Capture drawable source path for
                // ImageView/ImageButton. The value is a direct APK path
                // like "res/drawable-mdpi-v4/lock.png".
                if (!attr_val.empty() && attr_val.find("res/") == 0) {
                    vnode->image_drawable_path = attr_val;
                    std::cerr << "[EXP088-A4] Captured image path: " << attr_val
                              << " for " << class_desc << std::endl;
                }
            } else if (attr_name == "background") {
                // Capture background drawable reference if it's a direct path
                if (!attr_val.empty() && attr_val.find("res/") == 0) {
                    // Store as a custom attribute for renderer
                }
            }
        }
    }

    // Add to parent if not root
    if (parent_id != 0) {
        vs->add_child(parent_id, view_id);
    }

    // Recursively inflate children
    if (node.contains("children") && node["children"].is_array()) {
        for (const auto& child : node["children"]) {
            inflate_view_tree(vs, child, view_id);
        }
    }

    return view_id;
}

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

    // EXP-056: Do not handle calls on null objects (object_id=0).
    // When a method returns null (e.g., getFragmentStack returns null
    // because the field was never initialized), calling isEmpty() on
    // that null should NOT create a fake empty collection — it should
    // fall through to the legacy bridge which returns void/default.
    // Otherwise, isEmpty() returns true on a null list, which causes
    // if-nez to branch incorrectly.
    if (obj_id == 0 && m != "<init>") {
        return CallResult::not_handled();
    }

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
        auto* state = get_or_create(obj_id);
        // EXP-071 Phase 7: For Map collections (HashMap, ConcurrentHashMap),
        // get(key) uses the key string to look up map_entries or
        // map_string_entries. For List collections (ArrayList, LinkedList),
        // get(index) uses the integer index to look up elements[].
        if (state->is_map) {
            std::string key = ctx.arg_as_string(0);
            if (key.empty() && !ctx.args.empty() &&
                ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
                key = "obj:" + std::to_string(ctx.args[0].object_id);
            }
            // EXP-071 diagnostic
            if (key.find("US") != std::string::npos) {
                std::cerr << "[EXP071-CS-GET] map=" << obj_id
                          << " key=\"" << key << "\""
                          << " is_map=" << state->is_map
                          << " str_entries=" << state->map_string_entries.size()
                          << " obj_entries=" << state->map_entries.size()
                          << " caller=" << ctx.class_name << std::endl;
            }
            // Check string entries first.
            auto sit = state->map_string_entries.find(key);
            if (sit != state->map_string_entries.end()) {
                return CallResult::handled_string(sit->second);
            }
            // Then check object entries.
            auto it = state->map_entries.find(key);
            if (it != state->map_entries.end() && it->second != 0) {
                return CallResult::handled_object(it->second, "Ljava/lang/Object;");
            }
            return CallResult::handled_null();
        }
        // List: get(index) → element
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
            // EXP-071 Phase 7: Count both object and string entries.
            return CallResult::handled_int(static_cast<int32_t>(
                state->map_entries.size() + state->map_string_entries.size()));
        }
        return CallResult::handled_int(static_cast<int32_t>(state->elements.size()));
    }

    if (m == "isEmpty") {
        auto* state = get_or_create(obj_id);
        if (state->is_map) {
            // EXP-071 Phase 7: Check both object and string entries.
            return CallResult::handled_bool(
                state->map_entries.empty() && state->map_string_entries.empty());
        }
        return CallResult::handled_bool(state->elements.empty());
    }

    if (m == "clear") {
        auto* state = get_or_create(obj_id);
        state->elements.clear();
        state->map_entries.clear();
        state->map_string_entries.clear();
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
            // Use key as the map key. For object keys, use object_id as string.
            if (key.empty() && ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
                key = "obj:" + std::to_string(ctx.args[0].object_id);
            }
            // EXP-071 Phase 7: Check if the value is a STRING or OBJECT.
            // For STRING values, store in map_string_entries.
            // For OBJECT values, store in map_entries.
            const auto& val_arg = ctx.args[1];
            if (val_arg.kind == CallContext::Arg::Kind::STRING) {
                state->map_string_entries[key] = val_arg.string_val;
                // Also remove from object entries if it was previously there.
                state->map_entries.erase(key);
                // EXP-071 diagnostic
                if (key.find("US") != std::string::npos || key == "US") {
                    std::cerr << "[EXP071-PUT-STR] map=" << obj_id
                              << " key=\"" << key << "\" val=\"" << val_arg.string_val << "\""
                              << " caller=" << ctx.class_name << std::endl;
                }
            } else {
                uint32_t value = ctx.arg_as_object(1, 0);
                state->map_entries[key] = value;
                // Also remove from string entries if it was previously there.
                state->map_string_entries.erase(key);
            }
        }
        return CallResult::handled_null();
    }

    if (m == "containsKey") {
        auto* state = get_or_create(obj_id, true);
        std::string key = ctx.arg_as_string(0);
        if (key.empty() && !ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
            key = "obj:" + std::to_string(ctx.args[0].object_id);
        }
        // EXP-071 Phase 7: Check both object and string entries.
        bool found = (state->map_entries.count(key) > 0) ||
                     (state->map_string_entries.count(key) > 0);
        return CallResult::handled_bool(found);
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
    // EXP-071 Phase 8: In our deterministic test runtime, we treat ALL
    // delays as zero. Real Android's Handler blocks until a message's
    // ready_at_ms is reached; our runtime drains everything that's been
    // queued at each well-defined synchronization point (after onCreate,
    // after click dispatch, etc.). This matches real Android's behavior
    // when the system is idle (the Looper fires the runnable as soon as
    // its ready_at_ms is reached, which for a busy main thread is "as
    // fast as possible").
    //
    // Without this, Lambda0 (scheduled with 400ms delay by animateProgress)
    // would never be drained because the drain loop runs within milliseconds
    // of the confirm click. The 400ms delay is meant to let the progress
    // animation complete visually; in a headless test with no animation,
    // there's no reason to wait.
    auto now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
    (void)now_ms;  // Not used in drain — we drain everything.

    size_t drained = 0;
    // Drain in enqueue order (FIFO). This preserves the relative ordering
    // of runnables posted by the application.
    while (!queue_.empty()) {
        auto q = std::move(queue_.front());
        queue_.pop_front();
        out_drained->push_back(q.runnable_id);
        std::cerr << "[QUEUE] Runnable id=" << q.runnable_id
                  << " dequeued (delay=" << (q.ready_at_ms - now_ms)
                  << "ms treated as 0 in deterministic mode)"
                  << std::endl;
        drained++;
    }
    return drained;
}

// EXP-088 Phase F: Real removeCallbacks implementation.
// Previously this was a no-op stub — removeCallbacks(R) was acknowledged
// but did nothing. Now it actually removes matching Runnables from the
// queue. This is necessary for the user's Phase F acceptance scenario:
//   post(A), post(B), postDelayed(C), removeCallbacks(B), drain → A, C
//
// Returns the number of Runnables removed.
size_t HandlerShadow::remove_callbacks(uint32_t runnable_id) {
    if (runnable_id == 0) return 0;
    size_t removed = 0;
    auto it = queue_.begin();
    while (it != queue_.end()) {
        if (it->runnable_id == runnable_id) {
            std::cerr << "[QUEUE] Runnable id=" << runnable_id
                      << " removed (was at depth=" << std::distance(queue_.begin(), it)
                      << ")" << std::endl;
            it = queue_.erase(it);
            removed++;
        } else {
            ++it;
        }
    }
    return removed;
}

// EXP-088 Phase F: removeCallbacksAndMessages(null) — clear entire queue.
size_t HandlerShadow::remove_all() {
    size_t n = queue_.size();
    std::cerr << "[QUEUE] Clearing " << n << " queued Runnables" << std::endl;
    queue_.clear();
    return n;
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
        if (m == "removeCallbacks" || m == "removeMessages" || m == "hasMessages" || m == "hasCallbacks") {
            // EXP-088 Phase F: removeCallbacks(Runnable) — actually remove
            // matching Runnables from the queue. Previously this was a no-op.
            uint32_t r = extract_runnable(ctx, 0);
            if (r != 0) {
                size_t removed = remove_callbacks(r);
                std::cerr << "[QUEUE] removeCallbacks(runnable=" << r
                          << ") removed " << removed << " entries" << std::endl;
            }
            return CallResult::handled_void();
        }
        if (m == "removeCallbacksAndMessages") {
            // removeCallbacksAndMessages(null) clears the entire queue.
            // The token arg (often null) is currently ignored — we always
            // clear everything, which is correct for the null-token case
            // that is by far the most common usage.
            size_t removed = remove_all();
            std::cerr << "[QUEUE] removeCallbacksAndMessages cleared "
                      << removed << " entries" << std::endl;
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
        // EXP-071 Phase 8: handle BOTH overloads:
        //   * runOnUIThread(Runnable)             — delay=0
        //   * runOnUIThread(Runnable, long delay) — delay=arg[1]
        // The animateProgress() and lambda$onConfirm$1() callers use the
        // 2-arg overload with delays of 400ms and 150ms respectively.
        // Without honoring the delay, the runnables would all drain at once,
        // which is actually fine for our deterministic runtime — but we
        // still respect the relative ordering by capturing the delay
        // timestamp so future code that drains incrementally works correctly.
        if (m == "runOnUIThread" || m == "executeOnUIThread") {
            uint32_t r = extract_runnable(ctx, 0);
            // EXP-071: handle (Runnable, long) overload — read delay from
            // ctx.args[1].long_val. The single-arg form passes delay=0.
            int64_t delay = 0;
            if (ctx.args.size() >= 2) {
                // The second arg can be either a LONG (delay) or an OBJECT
                // (some overloads pass a second Runnable as a continuation).
                if (ctx.args[1].kind == CallContext::Arg::Kind::LONG) {
                    delay = ctx.args[1].long_val;
                } else if (ctx.args[1].kind == CallContext::Arg::Kind::INT) {
                    delay = static_cast<int64_t>(ctx.args[1].int_val);
                }
            }
            if (r == 0) return CallResult::handled_void();
            int64_t delay_ms = 0;
            if (ctx.args.size() >= 2) {
                // The second argument is the delay (J = long).
                // dalvik_value_to_arg stores it as long_val.
                delay_ms = ctx.args[1].long_val;
            }
            enqueue(r, delay_ms, /*cls=*/"AndroidUtilities");
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
        // EXP-056: Real Android returns null from Intent.getAction() when
        // no action is set.
        if (pi->action.empty()) {
            return CallResult::handled_null();
        }
        return CallResult::handled_string(pi->action);
    }
    if (m == "getData") {
        // EXP-056: No URI set on the default Intent — return null.
        return CallResult::handled_null();
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
    // EXP-088 Phase B debug
    std::cerr << "[EXP088-B-DISPATCH] ActivityShadow.dispatch: method=" << m
              << " class=" << ctx.class_name << std::endl;
    // EXP-075: Debug trace to confirm ActivityShadow is being called
    if (m == "setContentView" || m == "findViewById") {
        std::cerr << "[EXP075-ACTIVITY] ActivityShadow.dispatch: method=" << m
                  << " class=" << ctx.class_name
                  << " args=" << ctx.args.size();
        if (!ctx.args.empty()) {
            std::cerr << " arg0_kind=" << (int)ctx.args[0].kind;
            if (ctx.args[0].kind == CallContext::Arg::Kind::INT) {
                std::cerr << " arg0_int=" << ctx.args[0].int_val;
            } else if (ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
                std::cerr << " arg0_obj=" << ctx.args[0].object_id;
            }
        }
        std::cerr << std::endl;
    }
    // Activity instance methods
    if (m == "setContentView") {
        // setContentView(View) or setContentView(int layoutResId).
        if (!ctx.args.empty()) {
            if (ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
                content_view_id_ = ctx.args[0].object_id;
            } else if (ctx.args[0].kind == CallContext::Arg::Kind::INT) {
                // EXP-087 Phase 3 (B2 FIX): setContentView(int layoutResId)
                // now loads the layout_cache.json and creates real ViewShadow
                // nodes from the AXML view tree, with ARSC-resolved text strings.
                layout_resource_id_ = ctx.args[0].int_val;
                std::cerr << "[EXP087-B2] setContentView(layoutResId=0x" << std::hex
                          << ctx.args[0].int_val << std::dec << ")" << std::endl;

                // Try to load layout_cache.json from the APK's directory
                if (!apk_path_.empty()) {
                    // Find layout_cache.json or *_layout_cache.json next to APK
                    std::string apk_dir = apk_path_.substr(0, apk_path_.find_last_of("/"));
                    // Try several naming patterns
                    // EXP-088: Use APK-stem-specific cache filename first,
                    // then fall back to generic layout_cache.json.
                    std::string apk_stem = apk_path_;
                    size_t slash = apk_stem.find_last_of('/');
                    if (slash != std::string::npos) apk_stem = apk_stem.substr(slash+1);
                    size_t dot = apk_stem.find_last_of('.');
                    if (dot != std::string::npos) apk_stem = apk_stem.substr(0, dot);

                    std::vector<std::string> cache_candidates = {
                        apk_dir + "/" + apk_stem + "_layout_cache.json",  // per-APK (preferred)
                        apk_dir + "/layout_cache.json",                   // generic fallback
                    };

                    // Try all layout cache files in the directory
                    for (const auto& cache_path : cache_candidates) {
                        std::ifstream cache_file(cache_path);
                        if (!cache_file.is_open()) continue;

                        std::cerr << "[EXP087-B2] Loading layout cache: " << cache_path << std::endl;
                        try {
                            json cache_json;
                            cache_file >> cache_json;
                            cache_file.close();

                            const auto& layouts = cache_json["layouts"];
                            // Find layout matching the resource ID
                            for (auto it = layouts.begin(); it != layouts.end(); ++it) {
                                const auto& layout = it.value();
                                if (layout.contains("resource_id_int") &&
                                    layout["resource_id_int"].get<int32_t>() == layout_resource_id_) {

                                    std::cerr << "[EXP087-B2] Found layout: " << it.key()
                                              << " (resource_id=0x" << std::hex
                                              << layout_resource_id_ << std::dec << ")" << std::endl;

                                    // Create ViewShadow nodes from the cached view tree
                                    if (registry_ && layout.contains("view_tree")) {
                                        auto* view_shadow = registry_->find_as<ViewShadow>();
                                        std::cerr << "[EXP087-B2] registry_=" << registry_
                                                  << " view_shadow=" << (void*)view_shadow
                                                  << " has_view_tree=" << layout.contains("view_tree")
                                                  << std::endl;
                                        if (view_shadow) {
                                            uint32_t root_id = inflate_view_tree(
                                                view_shadow, layout["view_tree"], 0);
                                            if (root_id != 0) {
                                                content_view_id_ = root_id;
                                                std::cerr << "[EXP087-B2] Inflated view tree root_id="
                                                          << root_id << std::endl;
                                            } else {
                                                std::cerr << "[EXP087-B2] inflate_view_tree returned 0"
                                                          << std::endl;
                                            }
                                        }
                                    } else {
                                        std::cerr << "[EXP087-B2] registry_=" << registry_
                                                  << " has_view_tree=" << layout.contains("view_tree")
                                                  << std::endl;
                                    }
                                    break;
                                }
                            }
                            break;  // Found and loaded cache
                        } catch (const std::exception& e) {
                            std::cerr << "[EXP087-B2] Error parsing layout cache: " << e.what() << std::endl;
                        }
                    }
                }
            }
        }
        return CallResult::handled_void();
    }
    if (m == "getContentView") {
        if (content_view_id_ == 0) return CallResult::handled_null();
        return CallResult::handled_object(content_view_id_, "Landroid/view/View;");
    }
    if (m == "findViewById") {
        // EXP-088 Phase B FIX: Search the ViewShadow tree from content_view_id_
        // to find the view with the matching android:id.
        int32_t target_id = ctx.arg_as_int(0, 0);
        std::cerr << "[EXP088-B-DBG] findViewById: target=0x" << std::hex << target_id
                  << " content_view_id=" << content_view_id_
                  << " registry=" << (registry_ ? "YES" : "NO")
                  << std::dec << std::endl;
        if (registry_ && content_view_id_ != 0) {
            auto* view_shadow = registry_->find_as<ViewShadow>();
            if (view_shadow) {
                uint32_t found = view_shadow->find_by_android_id(content_view_id_, target_id);
                if (found != 0) {
                    std::cerr << "[EXP088-B] findViewById(0x" << std::hex << target_id
                              << std::dec << ") → view_id=" << found << std::endl;
                    return CallResult::handled_object(found, "Landroid/view/View;");
                } else {
                    std::cerr << "[EXP088-B-DBG] find_by_android_id returned 0" << std::endl;
                }
            } else {
                std::cerr << "[EXP088-B-DBG] view_shadow is null" << std::endl;
            }
        }
        return CallResult::handled_null();
    }
    if (m == "getIntent") {
        // EXP-056: Real Android ALWAYS passes a non-null Intent to onCreate.
        if (heap_) {
            uint32_t intent_id = heap_->get_or_create("Landroid/content/Intent;");
            std::cerr << "[EXP057-INTENT] getIntent → intent_id=" << intent_id << std::endl;
            return CallResult::handled_object(intent_id, "Landroid/content/Intent;");
        }
        std::cerr << "[EXP057-INTENT] getIntent → null (heap_ is null!)" << std::endl;
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
    // EXP-071: prefer ctx.receiver_class over ctx.class_name.
    // The caller passes the static class_name (from the DEX method_ids
    // table), which may be a parent class like "Landroid/view/View;" used
    // as a fallback for shadow dispatch. The receiver_class (the runtime
    // type of the actual View object) is more accurate for the ViewNode
    // — without this, downstream lookups by class substring (e.g.
    // "FragmentFloatingButton") fail because the node has the parent class.
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

// EXP-060: Find the most-recently-created view whose class descriptor
// contains `substring`. Used to locate the startMessagingButton (a
// TextView subclass like IntroActivity$4) without knowing its Android
// view_id. Walks the nodes_ map in descending id order so the latest
// match wins.
uint32_t ViewShadow::find_by_class_substring(const std::string& substring) const {
    uint32_t best = 0;
    uint32_t best_seq = 0;
    for (const auto& [id, node] : nodes_) {
        if (node->class_desc.find(substring) != std::string::npos) {
            // Tie-break by view_id (which monotonically increases with
            // allocation order — later allocations have higher IDs).
            if (id >= best) {
                best = id;
                best_seq = id;
            }
        }
    }
    (void)best_seq;
    return best;
}

// EXP-060: Return all views with a click listener whose class matches
// the substring. Used to dispatch synthetic clicks on multiple candidate
// Views (e.g. startMessagingButton + switchLanguageTextView) when we
// can't identify the exact one. Ordered by view_id descending so the
// most-recently-created View is tried first.
std::vector<uint32_t> ViewShadow::find_all_with_click_listener(
    const std::string& class_substring) const {
    std::vector<uint32_t> result;
    for (const auto& [id, node] : nodes_) {
        if (node->click_listener_id == 0) continue;
        if (!class_substring.empty() &&
            node->class_desc.find(class_substring) == std::string::npos) continue;
        result.push_back(id);
    }
    // Sort descending by view_id (most-recently-created first).
    std::sort(result.begin(), result.end(), std::greater<uint32_t>());
    return result;
}

CallResult ViewShadow::dispatch(const CallContext& ctx) {
    const auto& m = ctx.method;
    // View instance methods — receiver_id is the View heap object_id.

    if (m == "<init>") {
        // View(Context), View(Context, AttributeSet), View(Context, AttributeSet, int)
        // Allocate a fresh node bound to this receiver.
        get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        return CallResult::handled_void();
    }
    if (m == "setId") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
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
        // EXP-061: Trace addView to debug why PhoneView's children aren't connected
        std::cerr << "[EXP061-ADDVIEW] parent=" << ctx.receiver_id
                  << " parent_class=" << ctx.class_name
                  << " child=" << child
                  << std::endl;
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
        // EXP-088 Phase B FIX: Search from the Activity's content_view_id
        uint32_t search_root = ctx.receiver_id;
        if (registry_) {
            auto* act_shadow = registry_->find_as<ActivityShadow>();
            if (act_shadow && act_shadow->content_view_id() != 0) {
                search_root = act_shadow->content_view_id();
            }
        }
        std::cerr << "[EXP088-B-VS] findViewById: target=0x" << std::hex << target_id
                  << " search_root=" << search_root << std::dec << std::endl;
        uint32_t found = find_by_android_id(search_root, target_id);
        if (found != 0) {
            std::cerr << "[EXP088-B-VS] FOUND view_id=" << found << std::endl;
            return CallResult::handled_object(found, "Landroid/view/View;");
        }
        std::cerr << "[EXP088-B-VS] NOT FOUND" << std::endl;
        return CallResult::handled_null();
    }
    if (m == "findViewWithTag") {
        // Tag is an Object — we don't track tags.
        return CallResult::handled_null();
    }
    if (m == "setVisibility") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->visibility = ctx.arg_as_int(0, 0);
        return CallResult::handled_void();
    }
    if (m == "getVisibility") {
        const auto* n = find_node(ctx.receiver_id);
        return CallResult::handled_int(n ? n->visibility : 0);
    }
    if (m == "setEnabled") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->enabled = ctx.arg_as_bool(0, true);
        return CallResult::handled_void();
    }
    if (m == "isEnabled") {
        const auto* n = find_node(ctx.receiver_id);
        return CallResult::handled_bool(n ? n->enabled : true);
    }
    if (m == "setClickable") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->clickable = ctx.arg_as_bool(0, false);
        return CallResult::handled_void();
    }
    if (m == "isClickable") {
        const auto* n = find_node(ctx.receiver_id);
        return CallResult::handled_bool(n ? n->clickable : false);
    }
    if (m == "setImageResource") {
        // EXP-067: ImageView.setImageResource(int resid)
        // Store the resource ID so the renderer can look up the drawable path.
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->image_resource_id = ctx.arg_as_int(0, 0);
        std::cerr << "[EXP067-SETIMAGE] view_id=" << ctx.receiver_id
                  << " resid=0x" << std::hex << n->image_resource_id << std::dec
                  << std::endl;
        return CallResult::handled_void();
    }
    // EXP-071: View.getContext() → returns the Context (Activity) that created this View.
    // This is needed by BaseFragment.getParentActivity() which does:
    //   getView().getContext() instanceof Activity
    // We store the context_object_id when the View constructor is called with a Context arg.
    if (m == "getContext") {
        const auto* n = find_node(ctx.receiver_id);
        if (n && n->context_object_id != 0) {
            return CallResult::handled_object(n->context_object_id, "Landroid/content/Context;");
        }
        // Fall back to returning null — no context stored
        return CallResult::handled_null();
    }
    // EXP-071: View constructor — capture Context argument.
    // When a View subclass <init>(Context, ...) is called, the first arg is the Context
    // (usually the Activity). We store it so getContext() can return it later.
    if (m == "<init>" && ctx.args.size() >= 1 &&
        ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        // Check if the first arg looks like a Context/Activity (it usually is)
        uint32_t ctx_id = ctx.args[0].object_id;
        if (ctx_id != 0 && ctx_id != ctx.receiver_id) {
            n->context_object_id = ctx_id;
        }
    }
    if (m == "setImageDrawable" || m == "setImageBitmap" ||
        m == "setImageIcon" || m == "setImageURI") {
        // For now, just mark that an image was set (we don't decode drawables yet).
        return CallResult::handled_void();
    }
    if (m == "setBackgroundResource") {
        // EXP-067: View.setBackgroundResource(int resid)
        // Store the resource ID for color/drawable resolution.
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        int32_t resid = ctx.arg_as_int(0, 0);
        n->image_resource_id = resid;  // reuse field for background
        std::cerr << "[EXP067-SETBGRES] view_id=" << ctx.receiver_id
                  << " resid=0x" << std::hex << resid << std::dec
                  << std::endl;
        return CallResult::handled_void();
    }
    if (m == "setText") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        // EXP-091: Log ALL setText calls for diagnostics
        std::string text_val = ctx.arg_as_string(0);
        std::cerr << "[EXP091-SETTEXT] view_id=" << ctx.receiver_id
                  << " class=" << (ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class)
                  << " arg_kind=" << static_cast<int>(ctx.args.empty() ? CallContext::Arg::Kind::NULL_REF : ctx.args[0].kind)
                  << " text=\"" << text_val << "\""
                  << std::endl;
        // EXP-074: When setText(int resourceId) is called, capture the resource ID.
        // The Python renderer will resolve it via the ARSC string table.
        if (!ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::INT) {
            n->text_resource_id = ctx.args[0].int_val;
            // Don't overwrite text if it was already set by a string setText
            if (n->text.empty()) {
                n->text = "[resid:0x" + std::to_string(ctx.args[0].int_val) + "]";
            }
        } else if (!ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
            // EXP-091: For OBJECT_REF args, try string_val first (may be populated
            // by dalvik_value_to_arg), then try resolving from the heap.
            if (!ctx.args[0].string_val.empty()) {
                n->text = ctx.args[0].string_val;
            } else {
                // Try to resolve the string from the heap
                // The object_id may point to a String created by LocaleController.getString()
                // For now, set a placeholder so the renderer knows there's text
                n->text = "[obj:" + std::to_string(ctx.args[0].object_id) + "]";
            }
        } else {
            n->text = ctx.arg_as_string(0);
        }
        return CallResult::handled_void();
    }
    // EXP-065: Capture setHint / setHintText — EditText hint text is
    // important for the Login UI (e.g., "Phone number" appears as a hint).
    // Previously setHintText was stubbed at the engine level; now it's
    // allowed to dispatch here and we store the hint on the ViewNode.
    if (m == "setHint" || m == "setHintText") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->hint = ctx.arg_as_string(0);
        std::cerr << "[EXP065-SETHINT] view_id=" << ctx.receiver_id
                  << " class=" << ctx.class_name
                  << " hint=\"" << n->hint << "\""
                  << std::endl;
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
    // EXP-060: Listener registration — store the listener object_id on the
    // ViewNode so a later synthetic CLICK event can dispatch through the
    // listener's onClick method. The listener is an OBJECT_REF passed as
    // arg 0.
    if (m == "setOnClickListener") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        uint32_t listener_id = ctx.arg_as_object(0, 0);
        n->click_listener_id = listener_id;
        // The listener's class descriptor is not always known here (the
        // CallContext only sees receiver_class, not arg types). The
        // dispatcher (dalvik_engine) will look it up from the heap at
        // dispatch time.
        n->click_listener_class.clear();
        n->clickable = true;  // setClickable(true) is implied
        std::cerr << "[EXP060-LISTENER] setOnClickListener view_id=" << ctx.receiver_id
                  << " class=" << ctx.class_name
                  << " listener_id=" << listener_id
                  << std::endl;
        return CallResult::handled_void();
    }
    if (m == "setOnLongClickListener") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        uint32_t listener_id = ctx.arg_as_object(0, 0);
        n->long_click_listener_id = listener_id;
        n->long_click_listener_class.clear();
        return CallResult::handled_void();
    }
    if (m == "setOnTouchListener") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        uint32_t listener_id = ctx.arg_as_object(0, 0);
        n->touch_listener_id = listener_id;
        n->touch_listener_class.clear();
        return CallResult::handled_void();
    }
    if (m == "setOnApplyWindowInsetsListener" ||
        m == "setOnFocusChangeListener" ||
        m == "setOnLayoutChangeListener" ||
        m == "setOnDragListener" ||
        m == "setOnHoverListener" ||
        m == "setOnGenericMotionListener" ||
        m == "setOnContextClickListener" ||
        m == "setOnScrollChangeListener" ||
        m == "setOnCapturedPointerListener") {
        // Other listeners — acknowledge but don't store. None are
        // dispatched by the runtime today.
        return CallResult::handled_void();
    }
    if (m == "onMeasure" || m == "onLayout" || m == "onDraw" ||
        m == "onTouchEvent" || m == "onAttachedToWindow" ||
        m == "onDetachedFromWindow") {
        return CallResult::handled_void();
    }
    if (m == "toString") {
        // EXP-094 (CM-018): Only claim toString for objects that are actually
        // registered View nodes. Previously this returned the literal "View"
        // for ANY dispatch that reached ViewShadow — including the
        // view_parents fallback in bridge_to_api, which tries
        // "Landroid/view/View;" for EVERY unhandled method. That made
        // StringBuilder.toString() return "View", poisoning every string
        // concatenation in the app (Object→toString silent false success).
        const ViewNode* n = (ctx.receiver_id != 0) ? find_node(ctx.receiver_id) : nullptr;
        if (n != nullptr) {
            // Per AOSP View.toString(): "android.view.View{<hex> ...}" debug
            // string. We return the class-desc debug form for registered nodes.
            return CallResult::handled_string(
                (n->class_desc.empty() ? std::string("View") : n->class_desc) +
                "{" + std::to_string(ctx.receiver_id) + "}");
        }
        return CallResult::not_handled();
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
