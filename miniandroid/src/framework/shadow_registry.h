// SPDX-License-Identifier: MIT
// MiniAndroid Compatibility Runtime
// EXP-051 — Android Framework Shadow Registry
//
// A Robolectric-inspired "Shadow" architecture that lets Android API
// behavior be registered, dispatched, and tracked separately from the
// DEX bytecode interpreter.
//
// Design goals:
//   * Each Android framework concept (Thread, Looper, Activity, Intent,
//     View, Handler, ...) lives in its own Shadow subclass.
//   * Shadows register handlers for (class_name, method_name) pairs.
//   * The bridge consults the registry BEFORE falling through to the
//     legacy ad-hoc if/else chain in bridge_to_api.
//   * Every dispatched call is recorded for stub-debt measurement
//     (IMPLEMENTED vs STUBBED vs FALLBACK).
//   * Shadows own their persistent state (singletons, queues, registries)
//     so the engine itself stays free of framework-specific knowledge.
//
// Thread-safety: shadows are NOT thread-safe. The runtime is
// single-threaded (see EXP-051 thread-identity model); all shadow
// state is mutated only from the main interpreter thread.

#ifndef MINIANDROID_FRAMEWORK_SHADOW_REGISTRY_H
#define MINIANDROID_FRAMEWORK_SHADOW_REGISTRY_H

#include <cstdint>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <ostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

// Forward-declare DalvikValue to avoid header coupling.
namespace miniandroid { namespace dalvik { struct DalvikValue; }}

namespace miniandroid { namespace framework {

// ─────────────────────────────────────────────────────────────────────────
// ApiCallStatus — mirrors ApiCallTrace::Status in dalvik_engine.h.
// Duplicated here so the registry is dependency-free; the bridge maps
// between the two on return.
// ─────────────────────────────────────────────────────────────────────────
enum class ApiCallStatus {
    IMPLEMENTED,   // shadow provided a real return value
    STUBBED,       // shadow acknowledged the call but returned a default
    FALLBACK,      // no shadow handled this call; legacy chain ran
    UNHANDLED      // nobody handled this call; default null/void returned
};

// ─────────────────────────────────────────────────────────────────────────
// CallContext — arguments + environment passed to every shadow handler.
// ─────────────────────────────────────────────────────────────────────────
struct CallContext {
    std::string class_name;       // DEX descriptor, e.g. "Landroid/os/Looper;"
    std::string method;           // method name, e.g. "getMainLooper"
    std::string descriptor;       // DEX prototype, e.g. "()Landroid/os/Looper;"

    // Receiver (this) for instance methods. For static methods, receiver
    // is null. object_id is the heap-allocated object ID assigned by the
    // DalvikHeap; class_desc is the runtime-verified class.
    bool has_receiver = false;
    uint32_t receiver_id = 0;
    std::string receiver_class;

    // Argument list. Position 0 is the first parameter (after `this`).
    // The bridge converts each DalvikValue into one of these Arg slots.
    struct Arg {
        enum class Kind { INT, LONG, FLOAT, DOUBLE, BOOL, STRING, OBJECT, NULL_REF };
        Kind kind = Kind::NULL_REF;
        int32_t  int_val = 0;
        int64_t  long_val = 0;
        float    float_val = 0.0f;
        double   double_val = 0.0;
        bool     bool_val = false;
        std::string string_val;
        uint32_t object_id = 0;
        std::string object_class;
    };
    std::vector<Arg> args;

    // Helper: get the i-th argument as int (with default if missing/wrong type).
    int32_t arg_as_int(size_t i, int32_t default_val = 0) const;
    bool   arg_as_bool(size_t i, bool default_val = false) const;
    std::string arg_as_string(size_t i, const std::string& default_val = "") const;
    uint32_t arg_as_object(size_t i, uint32_t default_val = 0) const;
};

// ─────────────────────────────────────────────────────────────────────────
// CallResult — what a shadow handler returns.
// ─────────────────────────────────────────────────────────────────────────
struct CallResult {
    bool handled = false;             // false = "I don't handle this; try next shadow"
    ApiCallStatus status = ApiCallStatus::UNHANDLED;

    // Return value (only meaningful when handled == true and the called
    // method is non-void).
    enum class RetKind { VOID, INT, LONG, FLOAT, DOUBLE, BOOL, STRING, OBJECT, NULL_REF };
    RetKind ret_kind = RetKind::VOID;
    int32_t  int_val = 0;
    int64_t  long_val = 0;
    float    float_val = 0.0f;
    double   double_val = 0.0;
    bool     bool_val = false;
    std::string string_val;
    uint32_t object_id = 0;
    std::string object_class;

    // Convenience factories
    static CallResult handled_int(int32_t v);
    static CallResult handled_long(int64_t v);
    static CallResult handled_float(float v);
    static CallResult handled_double(double v);
    static CallResult handled_bool(bool v);
    static CallResult handled_string(const std::string& s, uint32_t ref_id = 0);
    static CallResult handled_object(uint32_t obj_id, const std::string& cls);
    static CallResult handled_null();
    static CallResult handled_void();
    static CallResult not_handled();   // pass-through to next shadow
};

// ─────────────────────────────────────────────────────────────────────────
// HeapAllocator — abstract over DalvikHeap so shadows can allocate objects
// without depending on the engine header.
// ─────────────────────────────────────────────────────────────────────────
class HeapAllocator {
public:
    virtual ~HeapAllocator() = default;
    // Allocate a fresh heap object with the given class descriptor.
    // Returns the new object_id.
    virtual uint32_t allocate(const std::string& class_desc) = 0;
    // Look up an existing singleton by class descriptor. Returns 0 if
    // no such singleton exists yet.
    virtual uint32_t get_singleton(const std::string& class_desc) = 0;
    // Get-or-create: allocates if missing, returns existing otherwise.
    virtual uint32_t get_or_create(const std::string& class_desc) = 0;
    // Test whether an object exists in the heap.
    virtual bool has_object(uint32_t object_id) = 0;
};

// Forward-declare so Shadow can hold a back-pointer to the registry.
class ShadowRegistry;

// ─────────────────────────────────────────────────────────────────────────
// Shadow — base class for all Android framework shadows.
//
// A Shadow groups handlers for one or more related Android classes.
// Examples: ThreadShadow, LooperShadow, ActivityShadow, IntentShadow,
// ViewShadow, HandlerShadow.
//
// Subclasses override handles_class() to claim ownership of a class
// descriptor, and dispatch() to actually handle a method call.
// ─────────────────────────────────────────────────────────────────────────
class Shadow {
public:
    virtual ~Shadow() = default;

    // Name of this shadow (for diagnostics).
    virtual std::string name() const = 0;

    // Called once at startup with a HeapAllocator the shadow can use
    // to allocate persistent objects (singletons, queues, etc.).
    virtual void init(HeapAllocator* heap) { heap_ = heap; }

    // EXP-051: Called by the registry after registration so shadows
    // can do cross-shadow lookups (e.g. ActivityShadow.startActivity
    // needs to mark the IntentShadow's pending intent).
    void set_registry(ShadowRegistry* reg) { registry_ = reg; }

    // Does this shadow want to handle calls to the given class?
    // Default: false — the shadow must explicitly claim classes.
    virtual bool handles_class(const std::string& class_name) const = 0;

    // Dispatch a method call. Returns CallResult with handled=true if
    // the shadow consumed the call, or handled=false to fall through.
    virtual CallResult dispatch(const CallContext& ctx) = 0;

    // Diagnostics: list of method names this shadow actually implements
    // (returns real values for). Used for stub-debt measurement.
    virtual std::vector<std::string> implemented_methods() const { return {}; }
    // Methods this shadow acknowledges but only stubs (returns default).
    virtual std::vector<std::string> stubbed_methods() const { return {}; }

protected:
    HeapAllocator* heap_ = nullptr;
    ShadowRegistry* registry_ = nullptr;
};

// ─────────────────────────────────────────────────────────────────────────
// ShadowRegistry — collection of shadows consulted in registration order.
//
// Usage:
//   ShadowRegistry reg;
//   reg.set_heap(&my_heap_allocator);
//   reg.register_shadow<ThreadShadow>();
//   reg.register_shadow<LooperShadow>();
//   ...
//   CallResult r = reg.dispatch(ctx);
//   if (r.handled) { ... use r ... }
//
// Thread-safety: NOT thread-safe. Single-threaded runtime.
// ─────────────────────────────────────────────────────────────────────────
class ShadowRegistry {
public:
    ShadowRegistry() = default;

    void set_heap(HeapAllocator* heap) { heap_ = heap; }

    // Register a shadow. The registry takes ownership. Shadows are
    // consulted in registration order; first handled=true wins.
    template <typename T, typename... Args>
    T* register_shadow(Args&&... args) {
        auto shadow = std::make_unique<T>(std::forward<Args>(args)...);
        T* raw = shadow.get();
        shadow->set_registry(this);
        shadows_.push_back(std::move(shadow));
        if (heap_) raw->init(heap_);
        return raw;
    }

    // Also support pre-built shadows (for tests).
    void add_shadow(std::unique_ptr<Shadow> shadow) {
        shadow->set_registry(this);
        if (heap_) shadow->init(heap_);
        shadows_.push_back(std::move(shadow));
    }

    // Dispatch a method call. Walks shadows in registration order.
    // Returns the first CallResult with handled=true, or a
    // handled=false CallResult if nobody claimed the call.
    CallResult dispatch(const CallContext& ctx);

    // Aggregate stub-debt statistics across all shadows.
    struct Stats {
        size_t shadow_count = 0;
        size_t total_implemented = 0;  // sum of implemented_methods()
        size_t total_stubbed = 0;      // sum of stubbed_methods()
        size_t calls_dispatched = 0;   // runtime counter (since init)
        size_t calls_handled = 0;      // runtime counter
        size_t calls_fallback = 0;     // runtime counter (fell through to legacy)
    };
    Stats stats() const;

    // Lookup a registered shadow by name (for direct configuration).
    Shadow* find(const std::string& name) const;

    // Direct typed accessor (returns nullptr if not registered).
    template <typename T>
    T* find_as() const {
        for (const auto& s : shadows_) {
            if (auto p = dynamic_cast<T*>(s.get())) return p;
        }
        return nullptr;
    }

    // For testing: clear all state.
    void reset_counters() {
        calls_dispatched_ = 0;
        calls_handled_ = 0;
        calls_fallback_ = 0;
    }

private:
    HeapAllocator* heap_ = nullptr;
    std::vector<std::unique_ptr<Shadow>> shadows_;
    // Runtime counters (mutable so stats() can be const).
    mutable size_t calls_dispatched_ = 0;
    mutable size_t calls_handled_ = 0;
    mutable size_t calls_fallback_ = 0;
};

// ─────────────────────────────────────────────────────────────────────────
// Diagnostic dump (for the EXP-051 report).
// ─────────────────────────────────────────────────────────────────────────
std::string format_shadow_report(const ShadowRegistry& reg);

}} // namespace miniandroid::framework

#endif // MINIANDROID_FRAMEWORK_SHADOW_REGISTRY_H
