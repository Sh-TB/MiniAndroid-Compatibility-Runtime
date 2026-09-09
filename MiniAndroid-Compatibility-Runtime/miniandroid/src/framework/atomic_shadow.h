// M3 F-020 ROOT FIX — java.util.concurrent.atomic shadow family.
//
// ROOT GAP (discovered via F-020 Compose snapshot forensics, dooz v18):
// Compose's snapshot system (R8-minified androidx.compose.runtime) stores
// its global snapshot in `new AtomicReference(globalSnapshot)` and counts
// snapshot writes through AtomicInteger subclasses. The runtime had NO
// atomic-family shadow, so:
//   * AtomicReference.<init>(Object) missed every shadow; the bridge's
//     view-parent retry then routed the CONSTRUCTOR to ViewShadow's
//     View.<init> catch-all (no receiver-ancestry law), which dropped the
//     initial value and minted a phantom view node.
//   * AtomicReference.get() then returned null, SnapshotKt.currentSnapshot()
//     returned null, and the fail-soft null-receiver iget law manufactured
//     snapshot id 0 — so every state record (id >= 1) failed the
//     `record.id != 0 && record.id <= snapshot.id` validity walk and
//     Compose's own readError threw ISE inside setContent (dooz PARTIAL).
//
// Java/AOSP laws transferred (libcore/ojluni java.util.concurrent.atomic):
//   * AtomicReference.get() returns the value stored by the constructor
//     or the last set/swap/CAS — object identity preserved (== law).
//   * compareAndSet(expect, update) uses REFERENCE EQUALITY (==), null
//     matches only null; returns true iff swapped.
//   * AtomicInteger.get()/set() give the stored int; incrementAndGet()
//     returns the NEW value, getAndIncrement() the OLD one (post/prefix
//     law); addAndGet/getAndAdd likewise; compareAndSet on ints compares
//     by VALUE.
//   * AtomicBoolean compares by boolean value; AtomicLong is the 64-bit
//     twin of AtomicInteger.
//   * Subclass instances (R8 minted classes extending AtomicInteger)
//     share the same field storage: the engine's heap field store is
//     name-keyed, so the shadow writes "value" on the receiver object
//     and inherited reads see it.
//
// Determinism: the engine is a deterministically serialized interpreter
// (ROADMAP family L vocabulary) — single thread, no spurious CAS
// failures. CAS therefore succeeds exactly when the identity/value laws
// above hold. No app-specific code: these are platform primitives used
// pervasively by Compose, Kotlin coroutines, and Room.
//
// Fixture: tests/semantic_pass3_bridge_test.cpp (group ATOMIC-F020).

#ifndef MINIANDROID_FRAMEWORK_ATOMIC_SHADOW_H_
#define MINIANDROID_FRAMEWORK_ATOMIC_SHADOW_H_

#include "shadow_registry.h"

#include <string>
#include <vector>

namespace miniandroid { namespace framework {

// ── AtomicShadow: exact-family claim on java.util.concurrent.atomic ──
class AtomicShadow : public Shadow {
public:
    std::string name() const override { return "AtomicShadow"; }

    // Exact prefix claim: every java.util.concurrent.atomic.Atomic* class.
    // Registered before ViewShadow so the catch-all view path can never
    // capture an atomic descriptor (same ordering law as LocksShadow /
    // PendingIntentShadow / DatabaseShadow).
    bool handles_class(const std::string& cls) const override {
        return cls.rfind("Ljava/util/concurrent/atomic/Atomic", 0) == 0;
    }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"<init>", "get", "set", "getAndSet",
                "compareAndSet", "weakCompareAndSet", "lazySet",
                // AtomicInteger / AtomicLong arithmetic
                "addAndGet", "getAndAdd",
                "incrementAndGet", "getAndIncrement",
                "decrementAndGet", "getAndDecrement",
                // conversions Kotlin code calls on boxers
                "intValue", "longValue", "booleanValue",
                // M4 F-028d: Atomic*FieldUpdater family
                "newUpdater",
                // M4 F-028h: AtomicReferenceArray family
                "length"};
    }
    std::vector<std::string> stubbed_methods() const override {
        return {"getAndUpdate", "updateAndGet", "accumulateAndGet",
                "getAndAccumulate"};
    }

private:
    // Per-heap-object atomic cell. Reference cells keep (object_id, class)
    // or a string payload (AtomicReference<T> is generic over any reference
    // type — strings included); numeric cells keep the 64-bit payload
    // (ints stored sign-extended). Instance-keyed: one registry per engine.
    struct AtomicCell {
        enum class Kind { EMPTY, REF, NUM } kind = Kind::EMPTY;
        uint32_t ref_id = 0;
        std::string ref_cls;
        std::string ref_str;
        int64_t num = 0;
    };
    std::map<uint32_t, AtomicCell> cells_;

    // M4 F-028d — field-updater descriptors keyed by the heap id of the
    // allocated Atomic*FieldUpdater object. The value is the TARGET FIELD
    // NAME captured from newUpdater(tclass, vclass, fieldName); access
    // goes through the HeapAllocator typed-field hooks (real heap fields,
    // real object identity).
    std::map<uint32_t, std::string> updaters_;

    // M4 F-028h — AtomicReferenceArray cell grid, keyed by the heap id of
    // the array object. Java/AOSP law (libcore/ojluni
    // AtomicReferenceArray): elementwise access with REFERENCE identity
    // semantics (get/set/getAndSet/compareAndSet/lazySet), length fixed
    // by the <init>(I) constructor. ROOT GAP this closes: kotlinx.coroutines
    // internal SegmentedQueue/Segment (the lock-free work queue under
    // Dispatchers.Default used by Compose's Recomposer) stores its slot
    // elements in an AtomicReferenceArray; with no engine implementation
    // the enqueue's set() was silently dropped and the dequeue's get()
    // always returned null, so the consumer spin loop (Segment cell
    // await) never observed progress — dooz livelocked at
    // Lb2/n;.d (629k+ null reads) right after the Material3 init layer.
    // Determinism: single-threaded engine, CAS succeeds iff the identity
    // law holds; OOB access logs and returns null (the engine's
    // bridge layer has no AIOOBE plumbing — honest soft law, logged).
    struct ArrayCell {
        enum class Kind { EMPTY, REF, STR, NUM } kind = Kind::EMPTY;
        uint32_t ref_id = 0;
        std::string ref_cls;
        std::string ref_str;
        int64_t num = 0;
    };
    std::map<uint32_t, std::vector<ArrayCell>> arrays_;
};

}} // namespace miniandroid::framework

#endif // MINIANDROID_FRAMEWORK_ATOMIC_SHADOW_H_
