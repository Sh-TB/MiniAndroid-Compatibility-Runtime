// M3 FAMILY-L ROOT FIX — java.util.concurrent.locks shadow implementation.
// See locks_shadow.h for the AOSP/Java law mapping.
#include "locks_shadow.h"

#include "android_shadows.h"  // [S191-C8] HandlerShadow (virtual clock, awaitNanos)

#include <cstdint>
#include <iostream>

namespace miniandroid { namespace framework {

// Resolve the RWLock-level state behind a ReadLock/WriteLock receiver.
LocksShadow::LockState& LocksShadow::state_for_read_lock(uint32_t read_id) {
    auto it = read_lock_owner_.find(read_id);
    uint32_t owner = (it != read_lock_owner_.end()) ? it->second : 0;
    // Orphan ReadLocks (constructed directly by app bytecode) get their
    // own state record keyed by their own object id.
    return owner != 0 ? rw_states_[owner] : rw_states_[read_id];
}

LocksShadow::LockState& LocksShadow::state_for_write_lock(uint32_t write_id) {
    auto it = write_lock_owner_.find(write_id);
    uint32_t owner = (it != write_lock_owner_.end()) ? it->second : 0;
    return owner != 0 ? rw_states_[owner] : rw_states_[write_id];
}

CallResult LocksShadow::dispatch(const CallContext& ctx) {
    const std::string& m = ctx.method;
    // [S191-C8] F-C8-153 — Lock-INTERFACE keyed calls resolve to the
    // receiver's RUNTIME class (EXP-059 receiver-identity law). javac
    // emits `Lock l = new ReentrantLock(); l.lock();` as an invoke on
    // Ljava/util/concurrent/locks/Lock; — the concrete family below only
    // answers when the effective class is the runtime one.
    const uint32_t recv = ctx.has_receiver ? ctx.receiver_id : 0;
    std::string eff = ctx.class_name;
    // [S191-C8] F-C8-153 + [S192-C8] F-C8-172 — interface-keyed calls
    // resolve to the receiver's RUNTIME class (EXP-059 receiver-identity
    // law). javac emits `Lock l = new ReentrantLock(); l.lock();` and
    // `ReadWriteLock rwl = new ReentrantReadWriteLock(); rwl.writeLock();`
    // as invokes on the INTERFACE type — the concrete family below only
    // answers when the effective class is the runtime one. klondike
    // consumes the ReadWriteLock interface for readLock/writeLock (22
    // sites, decode evidence).
    if (ctx.has_receiver &&
        (eff == "Ljava/util/concurrent/locks/Lock;" ||
         eff == "Ljava/util/concurrent/locks/ReadWriteLock;" ||
         eff == "Ljava/util/concurrent/locks/Condition;")) {
        if (!ctx.receiver_class.empty() &&
            ctx.receiver_class != eff) {
            eff = ctx.receiver_class;
        } else if (heap_ &&
                   heap_->get_object_class(ctx.receiver_id, eff)) {
            // resolved through the heap fallback
        } else {
            std::cerr << "[LOCKS][C8] " << eff
                      << "-interface call with UNRESOLVED receiver class "
                         "— method=" << m << " obj="
                      << ctx.receiver_id << " (not handled, LOUD)"
                      << std::endl;
            return CallResult::not_handled();
        }
    }

    // ── [S191-C8] F-C8-152 — REAL Condition objects ─────────────────────
    // JDK law (AbstractQueuedSynchronizer.ConditionObject): created by
    // ReentrantLock.newCondition() / WriteLock.newCondition() (ReadLock
    // throws UnsupportedOperationException); signal/signalAll require
    // the owning lock HELD (IllegalMonitorStateException otherwise);
    // await releases the lock, parks, re-acquires; awaitNanos returns
    // ≤0 on timeout. Serialized engine: a pending signal (program-order
    // earlier signal on the same condition) is consumed; an unsignaled
    // awaitNanos advances the deterministic virtual clock and answers 0;
    // an unsignaled await records the loud PARKED boundary.
    if (eff == "Ljava/util/concurrent/locks/Condition;") {
        const uint32_t cond = ctx.has_receiver ? ctx.receiver_id : 0;
        const uint32_t lock_oid =
            condition_locks_.count(cond) ? condition_locks_[cond] : 0;
        auto owner_holds = [&]() -> int {
            auto it = reentrant_states_.find(lock_oid);
            return it != reentrant_states_.end() ? it->second.write_holds : 0;
        };
        auto consume_signal = [&]() -> bool {
            auto it = condition_pending_signals_.find(cond);
            if (it != condition_pending_signals_.end() && it->second > 0) {
                it->second--;
                return true;
            }
            return false;
        };
        if (m == "signal" || m == "signalAll") {
            if (owner_holds() <= 0) {
                // JDK law: REAL throw (AbstractOwnableSynchronizer).
                CallResult r = CallResult::handled_void();
                r.is_exc = true;
                r.exc_class = "Ljava/lang/IllegalMonitorStateException;";
                r.exc_msg = " signalling Condition without holding the "
                            "owning lock";
                return r;
            }
            condition_pending_signals_[cond] =
                (m == "signalAll") ? (1LL << 62)
                                   : (condition_pending_signals_[cond] + 1);
            std::cerr << "[LOCKS][C8] " << m << " cond=o" << cond
                      << " lock=o" << lock_oid << " pending="
                      << condition_pending_signals_[cond] << std::endl;
            return CallResult::handled_void();
        }
        if (m == "await" || m == "awaitUninterruptibly") {
            if (owner_holds() <= 0) {
                CallResult r = CallResult::handled_void();
                r.is_exc = true;
                r.exc_class = "Ljava/lang/IllegalMonitorStateException;";
                r.exc_msg = " awaiting Condition without holding the "
                            "owning lock";
                return r;
            }
            // release-all → park window → re-acquire (JDK law).
            auto& st = reentrant_states_[lock_oid];
            const int saved_holds = st.write_holds;
            st.write_holds = 0;
            const bool signaled = consume_signal();
            if (!signaled)
                std::cerr << "[LOCKS][C8] await PARKED (no signal) cond=o"
                          << cond << " — AOSP blocks here (documented "
                                     "boundary)" << std::endl;
            st.write_holds = saved_holds;
            return CallResult::handled_void();
        }
        if (m == "awaitNanos") {
            if (owner_holds() <= 0) {
                CallResult r = CallResult::handled_void();
                r.is_exc = true;
                r.exc_class = "Ljava/lang/IllegalMonitorStateException;";
                r.exc_msg = " awaiting Condition without holding the "
                            "owning lock";
                return r;
            }
            auto& st = reentrant_states_[lock_oid];
            const int saved_holds = st.write_holds;
            st.write_holds = 0;
            int64_t nanos = 0;
            for (const auto& a : ctx.args)
                if (a.kind == CallContext::Arg::Kind::LONG) nanos = a.long_val;
            int64_t remaining = 0;
            if (consume_signal()) {
                remaining = nanos;  // signaled: JDK returns an estimate ≥0
            } else {
                // Unsignaled timed await: advance the deterministic virtual
                // clock (same time law as Thread.sleep) and answer ≤0 —
                // the JDK timeout contract.
                if (auto* hs = registry_
                                   ? registry_->find_as<HandlerShadow>()
                                   : nullptr)
                    hs->advance_virtual(nanos / 1000000LL);
                remaining = 0;
                std::cerr << "[LOCKS][C8] awaitNanos TIMED-OUT cond=o" << cond
                          << " nanos=" << nanos << " (virtual clock advanced)"
                          << std::endl;
            }
            st.write_holds = saved_holds;
            return CallResult::handled_long(remaining);
        }
        return CallResult::not_handled();
    }

    const bool is_rwl  = eff == "Ljava/util/concurrent/locks/ReentrantReadWriteLock;";
    const bool is_read = eff == "Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;";
    const bool is_write = eff == "Ljava/util/concurrent/locks/ReentrantReadWriteLock$WriteLock;";
    const bool is_rl   = eff == "Ljava/util/concurrent/locks/ReentrantLock;";
    if (!is_rwl && !is_read && !is_write && !is_rl) return CallResult::not_handled();

    // ── constructors ────────────────────────────────────────────────────
    // AOSP: ReentrantReadWriteLock()/ReentrantReadWriteLock(boolean fair)
    // and ReentrantLock()/ReentrantLock(boolean fair) construct the sync
    // object. The deterministic engine records the state record here.
    if (m == "<init>") {
        if (is_rwl) {
            LockState& st = rw_state(recv);
            st.read_lock_id = 0;
            st.write_lock_id = 0;
        } else if (is_rl) {
            reentrant_state(recv);
        }
        return CallResult::handled_void();
    }

    // ── ReentrantReadWriteLock.readLock()/writeLock() ───────────────────
    // Java law: return the SAME non-null ReadLock/WriteLock object for the
    // lifetime of this ReentrantReadWriteLock (object identity, family CF).
    if (is_rwl && (m == "readLock" || m == "writeLock")) {
        LockState& st = rw_state(recv);
        uint32_t& cached = (m == "readLock") ? st.read_lock_id : st.write_lock_id;
        if (cached == 0 || !heap_ || !heap_->has_object(cached)) {
            const char* desc = (m == "readLock")
                ? "Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;"
                : "Ljava/util/concurrent/locks/ReentrantReadWriteLock$WriteLock;";
            uint32_t lock_obj = heap_ ? heap_->allocate(desc) : 0;
            cached = lock_obj;
            if (m == "readLock") read_lock_owner_[lock_obj] = recv;
            else                 write_lock_owner_[lock_obj] = recv;
        }
        const char* kind = (m == "readLock") ? "READ" : "WRITE";
        std::cerr << "[LOCKS] ReentrantReadWriteLock." << m << " rwl=" << recv
                  << " → " << kind << "Lock obj=" << cached << " (identity held)"
                  << std::endl;
        return CallResult::handled_object(cached,
            (m == "readLock")
                ? "Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;"
                : "Ljava/util/concurrent/locks/ReentrantReadWriteLock$WriteLock;");
    }

    // ── ReadLock / WriteLock acquire-release family ─────────────────────
    if (is_read || is_write) {
        LockState& st = is_read ? state_for_read_lock(recv) : state_for_write_lock(recv);
        if (m == "lock" || m == "lockInterruptibly") {
            // DETERMINISTICALLY SERIALIZED law: no contention source exists.
            if (is_read) st.read_holds++;
            else         st.write_holds++;
            return CallResult::handled_void();
        }
        if (m == "tryLock") {
            return CallResult::handled_bool(true);  // uncontended law
        }
        if (m == "unlock") {
            int& holds = is_read ? st.read_holds : st.write_holds;
            if (holds > 0) {
                holds--;
            } else {
                // Java law: IllegalMonitorStateException. Deterministic
                // engine: honest diagnostic instead of a thrown stub
                // (documented boundary — never silent).
                std::cerr << "[LOCKS][UNBALANCED-UNLOCK] "
                          << (is_read ? "ReadLock" : "WriteLock")
                          << " obj=" << recv << " unlocked with hold count 0"
                          << std::endl;
            }
            return CallResult::handled_void();
        }
        if (m == "newCondition") {
            // [S191-C8] F-C8-152 — REAL Condition object (was handled_null:
            // the null NPE'd every corpus consumer downstream). JDK law:
            // WriteLock supports conditions; identity + owning-lock binding
            // recorded for the signal/await contract below.
            uint32_t cond_id = heap_ ? heap_->allocate(
                "Ljava/util/concurrent/locks/Condition;") : 0;
            condition_locks_[cond_id] = recv;
            std::cerr << "[LOCKS][C8] " << eff << ".newCondition → cond=o"
                      << cond_id << " lock=o" << recv
                      << " (REAL condition object)" << std::endl;
            return CallResult::handled_object(
                cond_id, "Ljava/util/concurrent/locks/Condition;");
        }
    }

    // ── ReentrantLock acquire-release family ────────────────────────────
    if (is_rl) {
        LockState& st = reentrant_state(recv);
        if (m == "lock" || m == "lockInterruptibly") {
            st.write_holds++;   // exclusive semantics
            return CallResult::handled_void();
        }
        if (m == "tryLock") return CallResult::handled_bool(true);
        if (m == "unlock") {
            if (st.write_holds > 0) st.write_holds--;
            else std::cerr << "[LOCKS][UNBALANCED-UNLOCK] ReentrantLock obj="
                           << recv << " unlocked with hold count 0" << std::endl;
            return CallResult::handled_void();
        }
        if (m == "getHoldCount") return CallResult::handled_int(st.write_holds);
        if (m == "isLocked" || m == "isHeldByCurrentThread")
            return CallResult::handled_bool(st.write_holds > 0);
        if (m == "isFair") return CallResult::handled_bool(false);  // default ctor law
        if (m == "newCondition") {
            // [S191-C8] F-C8-152 — REAL Condition object (was handled_null).
            uint32_t cond_id = heap_ ? heap_->allocate(
                "Ljava/util/concurrent/locks/Condition;") : 0;
            condition_locks_[cond_id] = recv;
            std::cerr << "[LOCKS][C8] ReentrantLock.newCondition → cond=o"
                      << cond_id << " lock=o" << recv
                      << " (REAL condition object)" << std::endl;
            return CallResult::handled_object(
                cond_id, "Ljava/util/concurrent/locks/Condition;");
        }
    }

    // ── ReentrantReadWriteLock introspection ────────────────────────────
    if (is_rwl) {
        LockState& st = rw_state(recv);
        if (m == "getReadHoldCount") return CallResult::handled_int(st.read_holds);
        if (m == "getWriteHoldCount") return CallResult::handled_int(st.write_holds);
        if (m == "getReadLockCount") return CallResult::handled_int(st.read_holds > 0 ? 1 : 0);
        if (m == "isReadLocked") return CallResult::handled_bool(st.read_holds > 0);
        if (m == "isWriteLocked") return CallResult::handled_bool(st.write_holds > 0);
        if (m == "isFair") return CallResult::handled_bool(false);
    }

    return CallResult::not_handled();
}

}} // namespace miniandroid::framework
