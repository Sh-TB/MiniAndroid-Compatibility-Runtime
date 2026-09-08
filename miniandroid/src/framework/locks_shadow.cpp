// M3 FAMILY-L ROOT FIX — java.util.concurrent.locks shadow implementation.
// See locks_shadow.h for the AOSP/Java law mapping.
#include "locks_shadow.h"

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
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;
    const uint32_t recv = ctx.has_receiver ? ctx.receiver_id : 0;

    const bool is_rwl  = cls == "Ljava/util/concurrent/locks/ReentrantReadWriteLock;";
    const bool is_read = cls == "Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;";
    const bool is_write = cls == "Ljava/util/concurrent/locks/ReentrantReadWriteLock$WriteLock;";
    const bool is_rl   = cls == "Ljava/util/concurrent/locks/ReentrantLock;";
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
            // EXPLICITLY UNSUPPORTED: Condition await/signal queues are not
            // demanded by the corpus. Loud STUBBED status (never silent 0).
            std::cerr << "[LOCKS][UNSUPPORTED] " << cls << ".newCondition — "
                      << "Condition semantics outside declared base boundary"
                      << std::endl;
            return CallResult::handled_null();
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
            std::cerr << "[LOCKS][UNSUPPORTED] ReentrantLock.newCondition — "
                      << "Condition semantics outside declared base boundary"
                      << std::endl;
            return CallResult::handled_null();
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
