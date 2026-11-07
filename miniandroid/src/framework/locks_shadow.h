// M3 FAMILY-L ROOT FIX — java.util.concurrent.locks shadow family.
//
// ROOT GAP (discovered via the F-016 exception-honesty law + F-012 guard):
// microtimer's Room insert path (R8-obfuscated Kotlin) executes
//   Database.h.readLock() → Intrinsics.checkNotNullExpressionValue
// and the runtime had NO ReentrantReadWriteLock shadow at all, so the
// unresolved virtual call silently returned NULL, the Kotlin Intrinsics
// null-check threw NPE, and (under the pre-F-016 FRAME-2 policy) the
// failure was masked by "caller continues with null".
//
// AOSP/Java laws transferred (libcore/ojluni java.util.concurrent.locks):
//   * ReentrantReadWriteLock.readLock()/writeLock() return the lock's
//     ReadLock/WriteLock objects — NEVER null, and the SAME object on
//     every call (object identity, ROADMAP family CF).
//   * lock() acquires; unlock() releases; in a deterministically
//     serialized engine (ROADMAP family L vocabulary:
//     DETERMINISTICALLY SERIALIZED) uncontended acquisition always
//     succeeds, so tryLock() is true.
//   * Reentrancy: repeated lock() by the same (single) thread increments
//     the hold count; unlock() decrements it. Java law: unlock without
//     hold throws IllegalMonitorStateException — the deterministic
//     engine records the imbalance in the diagnostic channel instead of
//     throwing (documented boundary; never silent).
//   * lockInterruptibly() == lock() under a single serialized thread
//     (no interrupt source exists).
//   * [S191-C8] F-C8-153 — calls DECLARED on the java.util.concurrent.locks
//     Lock INTERFACE (the javac emit shape for `Lock l = new
//     ReentrantLock()`) are resolved to the receiver's RUNTIME class
//     (EXP-059 receiver-identity law) before the family dispatch — decode
//     evidence: Lock.lock/unlock = 295 call sites across 5 canonical APKs.
//   * [S191-C8] F-C8-152 — newCondition() returns a REAL Condition object
//     (heap identity + owning-lock binding + pending-signal counter).
//     signal/signalAll require the owning lock held (JDK IMSE law, REAL
//     throw via the shadow exception channel); await consumes a pending
//     signal or records a loud PARKED boundary (AOSP blocks there);
//     awaitNanos advances the deterministic virtual clock when unsignaled
//     and answers ≤0 (JDK timeout contract). The old handled_null stub
//     was replaced — it answered NULL and the corpus NPE'd downstream.
//
// No fixture-specific code: these are platform classes any Kotlin/R8
// APK may reference (Room-generated code uses ReentrantReadWriteLock
// for its transactional read/write paths).
//
#ifndef MINIANDROID_FRAMEWORK_LOCKS_SHADOW_H
#define MINIANDROID_FRAMEWORK_LOCKS_SHADOW_H

#include "shadow_registry.h"

#include <map>
#include <string>

namespace miniandroid { namespace framework {

class LocksShadow : public Shadow {
public:
    std::string name() const override { return "LocksShadow"; }

    bool handles_class(const std::string& cls) const override {
        // Exact family claims — the catch-all view path must never see
        // these descriptors (registration order also keeps them early).
        // [S191-C8] + Lock interface and Condition objects (F-C8-152/153).
        return cls.rfind("Ljava/util/concurrent/locks/ReentrantReadWriteLock;", 0) == 0 ||
               cls.rfind("Ljava/util/concurrent/locks/ReentrantLock;", 0) == 0 ||
               cls.rfind("Ljava/util/concurrent/locks/Lock;", 0) == 0 ||
               cls.rfind("Ljava/util/concurrent/locks/Condition;", 0) == 0;
    }

    CallResult dispatch(const CallContext& ctx) override;

    // ── accessors for evidence / diagnostics ────────────────────────────
    struct LockState {
        int read_holds = 0;    // shared-lock hold count (ReadLock)
        int write_holds = 0;   // exclusive-lock hold count (WriteLock)
        uint32_t read_lock_id = 0;   // identity of the ReadLock object
        uint32_t write_lock_id = 0;  // identity of the WriteLock object
    };
    const LockState* state_by_id(uint32_t obj_id) const {
        auto it = rw_states_.find(obj_id);
        return it == rw_states_.end() ? nullptr : &it->second;
    }
    size_t live_lock_objects() const { return rw_states_.size() + reentrant_states_.size(); }

private:
    // ReentrantReadWriteLock states keyed by the RWLock heap object id.
    std::map<uint32_t, LockState> rw_states_;
    // ReentrantLock states keyed by the lock heap object id.
    std::map<uint32_t, LockState> reentrant_states_;
    // ReadLock/WriteLock object id → owning RWLock object id (0 = orphan).
    std::map<uint32_t, uint32_t> read_lock_owner_;
    std::map<uint32_t, uint32_t> write_lock_owner_;
    // [S191-C8] F-C8-152 Condition state: condition oid → owning
    // ReentrantLock oid; condition oid → pending signal count
    // (signal +1, signalAll = wake-all marker LONG_MAX/2).
    std::map<uint32_t, uint32_t> condition_locks_;
    std::map<uint32_t, int64_t> condition_pending_signals_;

    LockState& rw_state(uint32_t id) { return rw_states_[id]; }
    LockState& reentrant_state(uint32_t id) { return reentrant_states_[id]; }
    LockState& state_for_read_lock(uint32_t read_id);
    LockState& state_for_write_lock(uint32_t write_id);
};

}} // namespace miniandroid::framework

#endif // MINIANDROID_FRAMEWORK_LOCKS_SHADOW_H
