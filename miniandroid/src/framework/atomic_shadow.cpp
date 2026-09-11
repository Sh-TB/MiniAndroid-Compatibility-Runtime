// M3 F-020 ROOT FIX — java.util.concurrent.atomic shadow implementation.
// See atomic_shadow.h for the Java/AOSP law mapping and the forensic
// root-gap record (Compose SnapshotKt.currentSnapshot reads the global
// snapshot out of an AtomicReference; a dropped constructor argument
// zeroed the whole snapshot id chain inside dooz's setContent).
#include "atomic_shadow.h"

#include <iostream>
#include <map>
#include <string>

namespace miniandroid { namespace framework {

// ── constructors ────────────────────────────────────────────────────────
// Java law: AtomicReference(T initial), AtomicInteger(int initial),
// AtomicLong(long initial), AtomicBoolean(boolean initial). The no-arg
// constructors store the JVM zero value (null / 0 / false). The bridge
// hands instance ctors ctx.args[0] = first parameter (receiver shifted).
CallResult AtomicShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;
    const uint32_t recv = ctx.has_receiver ? ctx.receiver_id : 0;

    // M4-F028h probe (env-gated): prove reachability of every dispatch.
    if (std::getenv("MINIANDROID_ATOMIC_DIAG")) {
        static thread_local uint64_t entry_log_n = 0;
        if (entry_log_n < 60) {
            ++entry_log_n;
            std::cerr << "[ATOMIC-DIAG] DISPATCH " << cls << "." << m
                      << " has_recv=" << ctx.has_receiver
                      << " recv=obj#" << recv
                      << " nargs=" << ctx.args.size()
                      << std::endl;
        }
    }

    const bool is_ref  = cls == "Ljava/util/concurrent/atomic/AtomicReference;";
    const bool is_int  = cls == "Ljava/util/concurrent/atomic/AtomicInteger;";
    const bool is_long = cls == "Ljava/util/concurrent/atomic/AtomicLong;";
    const bool is_bool = cls == "Ljava/util/concurrent/atomic/AtomicBoolean;";
    // M4 F-028d — the three field-updater families.
    const bool is_ref_upd  = cls == "Ljava/util/concurrent/atomic/AtomicReferenceFieldUpdater;";
    const bool is_long_upd = cls == "Ljava/util/concurrent/atomic/AtomicLongFieldUpdater;";
    const bool is_int_upd  = cls == "Ljava/util/concurrent/atomic/AtomicIntegerFieldUpdater;";
    // M4 F-028h — AtomicReferenceArray (SegmentedQueue cell grid law).
    const bool is_ref_array =
        cls == "Ljava/util/concurrent/atomic/AtomicReferenceArray;";
    if (!is_ref && !is_int && !is_long && !is_bool &&
        !is_ref_upd && !is_long_upd && !is_int_upd && !is_ref_array)
        return CallResult::not_handled();

    // ── Atomic*FieldUpdater family (M4 F-028d) ─────────────────────────
    // Java/AOSP law (libcore/ojluni): newUpdater(tclass, vclass, fieldName)
    // is a STATIC factory returning an updater bound to the named field;
    // get/set/CAS on the updater read/write the TARGET object's field with
    // volatile semantics. Reference updaters compare by object identity
    // (== law, null matches null); numeric updaters compare by value.
    // The engine is single-threaded/deterministic: CAS succeeds exactly
    // when the read value matches.
    if (is_ref_upd || is_long_upd || is_int_upd) {
        // M4-F028g diag (env-gated): updater path forensics.
        if (std::getenv("MINIANDROID_ATOMIC_DIAG")) {
            static thread_local uint64_t upd_log_n = 0;
            if (upd_log_n < 300) {
                ++upd_log_n;
                std::cerr << "[ATOMIC-DIAG] UPD " << cls << "." << m
                          << " recv=obj#" << recv
                          << " has_recv=" << ctx.has_receiver
                          << " nargs=" << ctx.args.size();
                for (size_t i = 0; i < ctx.args.size() && i < 4; ++i) {
                    int k = (int)ctx.args[i].kind;
                    std::cerr << " a" << i << "=k" << k;
                    if (ctx.args[i].kind == CallContext::Arg::Kind::OBJECT)
                        std::cerr << "(obj#" << ctx.args[i].object_id << ")";
                }
                auto itu = updaters_.find(recv);
                std::cerr << " bound="
                          << (itu != updaters_.end() ? itu->second : std::string("NONE"))
                          << std::endl;
            }
        }
        auto arg_long = [&](size_t i) -> int64_t {
            if (i >= ctx.args.size()) return 0;
            if (ctx.args[i].kind == CallContext::Arg::Kind::LONG)
                return ctx.args[i].long_val;
            return static_cast<int64_t>(ctx.arg_as_int(i));
        };
        auto updater_field = [&](uint32_t id) -> const std::string& {
            static const std::string kEmpty;
            auto it = updaters_.find(id);
            return it != updaters_.end() ? it->second : kEmpty;
        };
        if (m == "newUpdater") {
            // Descriptor shapes: (Ljava/lang/Class;Ljava/lang/Class;
            //   Ljava/lang/String;) for Reference, (Ljava/lang/Class;
            //   Ljava/lang/String;) for Int/Long. The field name is the
            //   LAST string argument.
            std::string field_name;
            for (size_t i = ctx.args.size(); i-- > 0;) {
                if (ctx.args[i].kind == CallContext::Arg::Kind::STRING) {
                    field_name = ctx.args[i].string_val;
                    break;
                }
            }
            uint32_t oid = 0;
            if (heap_) oid = heap_->allocate(cls);
            if (oid != 0) updaters_[oid] = field_name;
            return CallResult::handled_object(oid, cls);
        }
        if (!ctx.has_receiver) {
            if (std::getenv("MINIANDROID_ATOMIC_DIAG"))
                std::cerr << "[ATOMIC-DIAG] UPD-BAIL no-receiver " << cls << "." << m << std::endl;
            return CallResult::not_handled();
        }
        const std::string& fname = updater_field(recv);
        if (fname.empty()) {
            if (std::getenv("MINIANDROID_ATOMIC_DIAG"))
                std::cerr << "[ATOMIC-DIAG] UPD-BAIL unbound recv=obj#" << recv
                          << " " << cls << "." << m << std::endl;
            return CallResult::not_handled();
        }
        // target = first argument
        if (ctx.args.empty() ||
            ctx.args[0].kind != CallContext::Arg::Kind::OBJECT) {
            if (std::getenv("MINIANDROID_ATOMIC_DIAG"))
                std::cerr << "[ATOMIC-DIAG] UPD-BAIL bad-target " << cls << "." << m << std::endl;
            return CallResult::not_handled();
        }
        const uint32_t target = ctx.args[0].object_id;
        // F-050 diag (env-gated): FULL op trace for updater families —
        // the BufferedChannel sendersAndCloseStatus packed long lost a
        // write between ops; every op + pre-value pair must be visible.
        if (std::getenv("MINIANDROID_ATOMIC_DIAG") && !is_ref_upd) {
            static thread_local uint64_t op_log_n = 0;
            if (op_log_n < 500) {
                ++op_log_n;
                int64_t cur = 0;
                heap_->get_object_long_field(target, fname, cur);
                std::cerr << "[ATOMIC-OP] " << cls << "." << m << " obj#"
                          << target << " field=" << fname
                          << " pre=0x" << std::hex << cur << std::dec
                          << " (" << cur << ")" << std::endl;
            }
        }
        if (is_ref_upd) {
            // reference updater: identity law
            if (m == "get") {
                uint32_t oid = 0; std::string ocls, ostr; bool isstr = false;
                if (heap_->get_object_ref_field(target, fname, oid, ocls, ostr, isstr)) {
                    if (isstr) return CallResult::handled_string(ostr);
                    if (oid == 0) return CallResult::handled_null();
                    return CallResult::handled_object(oid, ocls);
                }
                return CallResult::handled_null();
            }
            auto ref_arg = [&](size_t i, uint32_t& oid, std::string& ocls,
                               std::string& ostr, bool& isstr) {
                if (i >= ctx.args.size()) { oid = 0; return; }
                const auto& a = ctx.args[i];
                if (a.kind == CallContext::Arg::Kind::OBJECT) {
                    oid = a.object_id; ocls = a.object_class; isstr = false;
                } else if (a.kind == CallContext::Arg::Kind::STRING) {
                    oid = 0; ostr = a.string_val; isstr = true;
                } else {
                    oid = 0; isstr = false;
                }
            };
            auto ref_write = [&](size_t i) {
                uint32_t oid; std::string ocls, ostr; bool isstr;
                ref_arg(i, oid, ocls, ostr, isstr);
                heap_->set_object_ref_field(target, fname, oid, ocls,
                                            ostr, isstr);
            };
            auto ref_read = [&](uint32_t& oid, std::string& ocls,
                                std::string& ostr, bool& isstr) {
                oid = 0; ocls.clear(); ostr.clear(); isstr = false;
                heap_->get_object_ref_field(target, fname, oid, ocls, ostr, isstr);
            };
            if (m == "set" || m == "lazySet") { ref_write(1); return CallResult::handled_void(); }
            if (m == "getAndSet") {
                uint32_t eoid; std::string ecls, estr; bool eis;
                ref_read(eoid, ecls, estr, eis);
                ref_write(1);
                if (eis) return CallResult::handled_string(estr);
                if (eoid == 0) return CallResult::handled_null();
                return CallResult::handled_object(eoid, ecls);
            }
            if (m == "compareAndSet" || m == "weakCompareAndSet") {
                uint32_t coid, uoid; std::string ccls, ucls, cstr, ustr;
                bool cis, uis;
                ref_read(coid, ccls, cstr, cis);
                ref_arg(1, uoid, ucls, ustr, uis);
                bool matched = (cis == uis) && (coid == uoid) &&
                               (!cis || cstr == ustr);
                if (matched) ref_write(2);
                return CallResult::handled_bool(matched);
            }
            return CallResult::not_handled();
        }
        // numeric updaters (long / int)
        auto num_read = [&]() -> int64_t {
            int64_t v = 0;
            if (is_long_upd) heap_->get_object_long_field(target, fname, v);
            else {
                int32_t iv = 0;
                heap_->get_object_int_field(target, fname, iv);
                v = iv;
            }
            return v;
        };
        auto num_write = [&](int64_t v) {
            if (is_long_upd) heap_->set_object_long_field(target, fname, v);
            else heap_->set_object_int_field(target, fname,
                                             static_cast<int32_t>(v));
        };
        if (m == "get") {
            // M4-F028g diag (env-gated): long-updater get forensics —
            // SegmentedQueue state machine progress tracing (b2/n _state).
            if (std::getenv("MINIANDROID_ATOMIC_DIAG")) {
                static thread_local uint64_t get_log_n = 0;
                if (get_log_n < 400) {
                    ++get_log_n;
                    int64_t gv = num_read();
                    std::cerr << "[ATOMIC-DIAG] GET " << cls << " target=obj#"
                              << target << " field=" << fname
                              << " -> " << gv << " (0x" << std::hex << gv
                              << std::dec << ")" << std::endl;
                }
            }
            return CallResult::handled_long(num_read());
        }
        if (m == "set" || m == "lazySet") {
            num_write(is_long_upd ? arg_long(1)
                                  : static_cast<int64_t>(ctx.arg_as_int(1)));
            return CallResult::handled_void();
        }
        if (m == "getAndSet") {
            int64_t oldv = num_read();
            num_write(is_long_upd ? arg_long(1)
                                  : static_cast<int64_t>(ctx.arg_as_int(1)));
            return is_long_upd ? CallResult::handled_long(oldv)
                               : CallResult::handled_int(static_cast<int32_t>(oldv));
        }
        if (m == "compareAndSet" || m == "weakCompareAndSet") {
            int64_t oldv = num_read();
            int64_t expect = is_long_upd
                ? arg_long(1)
                : static_cast<int64_t>(ctx.arg_as_int(1));
            int64_t upd = is_long_upd
                ? arg_long(2)
                : static_cast<int64_t>(ctx.arg_as_int(2));
            bool matched = (oldv == expect);
            if (matched) num_write(upd);
            // M4-F028 diag (env-gated): updater CAS forensics.
            if (std::getenv("MINIANDROID_ATOMIC_DIAG")) {
                static thread_local uint64_t cas_log_n = 0;
                if (cas_log_n < 400) {
                    ++cas_log_n;
                    std::cerr << "[ATOMIC-DIAG] CAS " << cls << " target=obj#"
                              << target << " field=" << fname
                              << " old=" << oldv << " expect=" << expect
                              << " upd=" << upd
                              << " -> " << (matched ? "SWAP" : "FAIL")
                              << std::endl;
                }
            }
            return CallResult::handled_bool(matched);
        }
        if (m == "addAndGet" || m == "getAndAdd") {
            int64_t oldv = num_read();
            int64_t delta = is_long_upd ? arg_long(1)
                                        : static_cast<int64_t>(ctx.arg_as_int(1));
            num_write(oldv + delta);
            int64_t nv = oldv + delta;
            if (is_long_upd)
                return m == "addAndGet" ? CallResult::handled_long(nv)
                                        : CallResult::handled_long(oldv);
            return m == "addAndGet"
                ? CallResult::handled_int(static_cast<int32_t>(nv))
                : CallResult::handled_int(static_cast<int32_t>(oldv));
        }
        if (m == "incrementAndGet" || m == "getAndIncrement" ||
            m == "decrementAndGet" || m == "getAndDecrement") {
            // F-050c ROOT FIX — getAndIncrement wrote oldv - 1 (a DECREMENT).
            // The old code dispatched the delta by prefix match:
            //   m.rfind("increment", 0) == 0
            // which is TRUE only for "incrementAndGet" — "getAndIncrement"
            // does NOT start with "increment", so it took the -1 branch.
            // Live evidence (dooz v18, MINIANDROID_ATOMIC_DIAG): the
            // Recomposer's BufferedChannel sendersAndCloseStatus packed
            // long (senders counter | close status << 60) went 0 -> -1 on
            // the FIRST send's getAndIncrement; (state shr 60).toInt()
            // then read -1 and kotlinx.coroutines threw
            // IllegalStateException("unexpected close status: -1") at
            // BufferedChannel.isClosed, killing the Recomposer await chain
            // (cancellation → Choreographer.removeFrameCallback → the
            // first frame never composed → blank framebuffer).
            // OpenJDK law (AtomicLongFieldUpdater.java / AtomicLong.java):
            //   getAndIncrement()   { return getAndAdd(1); }  — adds +1,
            //   incrementAndGet()   { return addAndGet(1); }  — adds +1,
            //   getAndDecrement()   { return getAndAdd(-1); } — adds -1,
            //   decrementAndGet()   { return addAndGet(-1); } — adds -1;
            // getAnd* returns the OLD value, *AndGet returns the NEW one.
            // Exact-name dispatch (no prefix heuristics) — every method's
            // delta and return epoch is pinned to the upstream contract.
            const bool is_increment =
                (m == "incrementAndGet" || m == "getAndIncrement");
            const bool want_new =
                (m == "incrementAndGet" || m == "decrementAndGet");
            int64_t oldv = num_read();
            int64_t nv = oldv + (is_increment ? 1 : -1);
            num_write(nv);
            if (is_long_upd)
                return CallResult::handled_long(want_new ? nv : oldv);
            return CallResult::handled_int(
                static_cast<int32_t>(want_new ? nv : oldv));
        }
        return CallResult::not_handled();
    }

    auto arg_is_object = [&](size_t i) {
        return i < ctx.args.size() &&
               ctx.args[i].kind == CallContext::Arg::Kind::OBJECT;
    };
    auto arg_is_string = [&](size_t i) {
        return i < ctx.args.size() &&
               ctx.args[i].kind == CallContext::Arg::Kind::STRING;
    };
    auto arg_num = [&](size_t i) -> int64_t {
        if (i >= ctx.args.size()) return 0;
        if (ctx.args[i].kind == CallContext::Arg::Kind::LONG)
            return ctx.args[i].long_val;
        return static_cast<int64_t>(ctx.arg_as_int(i));
    };

    // ── AtomicReferenceArray family (M4 F-028h) ─────────────────────────
    // Java/AOSP law (libcore/ojluni AtomicReferenceArray): elementwise
    // get/set/getAndSet/compareAndSet/lazySet over a fixed-length grid of
    // reference slots. Reference identity law (== ; null matches null);
    // numeric cells (some producers store boxed/int markers) compare by
    // value. The engine is single-threaded: CAS succeeds exactly when the
    // read value matches. NOTE: is_ref_array is declared at the top guard.
    if (is_ref_array) {
        auto arg_num_of = [](const CallContext::Arg& a) -> int64_t {
            if (a.kind == CallContext::Arg::Kind::LONG) return a.long_val;
            if (a.kind == CallContext::Arg::Kind::INT) return a.int_val;
            if (a.kind == CallContext::Arg::Kind::BOOL) return a.bool_val ? 1 : 0;
            if (a.kind == CallContext::Arg::Kind::FLOAT) return (int64_t)a.float_val;
            if (a.kind == CallContext::Arg::Kind::DOUBLE) return (int64_t)a.double_val;
            return 0;
        };
        auto arr_len = [&](uint32_t oid) -> size_t {
            auto it = arrays_.find(oid);
            return it != arrays_.end() ? it->second.size() : 0;
        };
        auto arr_cell = [&](uint32_t oid, size_t idx) -> ArrayCell* {
            auto it = arrays_.find(oid);
            if (it == arrays_.end()) return nullptr;
            if (idx >= it->second.size()) return nullptr;
            return &it->second[idx];
        };
        auto arr_grow = [&](uint32_t oid, size_t n) -> std::vector<ArrayCell>& {
            std::vector<ArrayCell>& v = arrays_[oid];
            if (v.size() < n) v.resize(n);
            return v;
        };
        auto arr_store = [&](ArrayCell& cell, const CallContext::Arg& a) {
            if (a.kind == CallContext::Arg::Kind::OBJECT) {
                cell.kind = ArrayCell::Kind::REF;
                cell.ref_id = a.object_id;
                cell.ref_cls = a.object_class;
                cell.ref_str = a.string_val;
            } else if (a.kind == CallContext::Arg::Kind::STRING) {
                cell.kind = ArrayCell::Kind::STR;
                cell.ref_id = 0;
                cell.ref_cls.clear();
                cell.ref_str = a.string_val;
            } else if (a.kind == CallContext::Arg::Kind::NULL_REF) {
                cell.kind = ArrayCell::Kind::EMPTY;
                cell.ref_id = 0;
                cell.ref_cls.clear();
                cell.ref_str.clear();
                cell.num = 0;
            } else {
                cell.kind = ArrayCell::Kind::NUM;
                cell.num = arg_num_of(a);
            }
        };
        auto arr_load = [&](const ArrayCell& cell) -> CallResult {
            switch (cell.kind) {
                case ArrayCell::Kind::REF:
                    if (cell.ref_id != 0)
                        return CallResult::handled_object(cell.ref_id,
                                                          cell.ref_cls);
                    return CallResult::handled_null();
                case ArrayCell::Kind::STR:
                    return CallResult::handled_string(cell.ref_str);
                case ArrayCell::Kind::NUM:
                    return CallResult::handled_long(cell.num);
                case ArrayCell::Kind::EMPTY:
                default:
                    return CallResult::handled_null();
            }
        };

        if (m == "<init>") {
            // <init>(I): fixed length. <init>([Ljava/lang/Object;): copy
            // ctor — the bridge materializes source arrays as objects; the
            // copy law needs elementwise heap array reads that no real-APK
            // hit has required yet, so adopt length-only (logged, honest).
            int64_t n = ctx.args.empty() ? 0 : arg_num_of(ctx.args[0]);
            if (n < 0) n = 0;
            arrays_[recv].assign(static_cast<size_t>(n), ArrayCell{});
            return CallResult::handled_void();
        }
        if (!ctx.has_receiver) return CallResult::not_handled();
        if (m == "length") return CallResult::handled_int((int)arr_len(recv));
        // instance accessors: args[0] = index
        if (ctx.args.empty()) return CallResult::not_handled();
        const int64_t idx64 = arg_num(0);
        if (idx64 < 0) {
            if (std::getenv("MINIANDROID_ATOMIC_DIAG"))
                std::cerr << "[ATOMIC-DIAG] ARR-OOB " << cls << "." << m
                          << " idx=" << idx64 << " len=" << arr_len(recv)
                          << std::endl;
            return CallResult::handled_null();
        }
        const size_t idx = static_cast<size_t>(idx64);
        if (m == "get") {
            ArrayCell* c = arr_cell(recv, idx);
            if (!c) {
                if (std::getenv("MINIANDROID_ATOMIC_DIAG"))
                    std::cerr << "[ATOMIC-DIAG] ARR-OOB get idx=" << idx
                              << " len=" << arr_len(recv) << std::endl;
                return CallResult::handled_null();
            }
            if (std::getenv("MINIANDROID_ATOMIC_DIAG")) {
                static thread_local uint64_t arr_log_n = 0;
                if (arr_log_n < 200) {
                    ++arr_log_n;
                    std::cerr << "[ATOMIC-DIAG] ARR get arr=obj#" << recv
                              << " idx=" << idx << " kind="
                              << (int)c->kind
                              << " ref=" << c->ref_id << std::endl;
                }
            }
            return arr_load(*c);
        }
        if (m == "set" || m == "lazySet") {
            ArrayCell& c = arr_grow(recv, idx + 1)[idx];
            arr_store(c, ctx.args.size() > 1
                             ? ctx.args[1]
                             : CallContext::Arg{});
            return CallResult::handled_void();
        }
        if (m == "getAndSet") {
            std::vector<ArrayCell>& v = arr_grow(recv, idx + 1);
            ArrayCell old = v[idx];
            arr_store(v[idx], ctx.args.size() > 1
                                  ? ctx.args[1]
                                  : CallContext::Arg{});
            return arr_load(old);
        }
        if (m == "compareAndSet" || m == "weakCompareAndSet") {
            std::vector<ArrayCell>& v = arr_grow(recv, idx + 1);
            ArrayCell& c = v[idx];
            const CallContext::Arg& expect =
                ctx.args.size() > 1 ? ctx.args[1] : CallContext::Arg{};
            const CallContext::Arg& upd =
                ctx.args.size() > 2 ? ctx.args[2] : CallContext::Arg{};
            bool matched;
            if (expect.kind == CallContext::Arg::Kind::OBJECT ||
                expect.kind == CallContext::Arg::Kind::STRING ||
                expect.kind == CallContext::Arg::Kind::NULL_REF) {
                bool e_null = expect.kind == CallContext::Arg::Kind::NULL_REF;
                bool e_str = expect.kind == CallContext::Arg::Kind::STRING;
                bool c_null = c.kind != ArrayCell::Kind::REF &&
                              c.kind != ArrayCell::Kind::STR;
                if (e_null)
                    matched = c_null;
                else if (e_str)
                    matched = c.kind == ArrayCell::Kind::STR &&
                              c.ref_str == expect.string_val;
                else {
                    bool u_str = upd.kind == CallContext::Arg::Kind::STRING;
                    matched = c.kind == (u_str ? ArrayCell::Kind::STR
                                               : ArrayCell::Kind::REF) &&
                              c.ref_id == expect.object_id &&
                              (!u_str || c.ref_str == expect.string_val) &&
                              c.ref_cls == expect.object_class;
                    // Identity law ignores the recorded class when the id
                    // matches (same object): compare ids first.
                    if (!matched && !u_str)
                        matched = c.kind == ArrayCell::Kind::REF &&
                                  c.ref_id == expect.object_id;
                }
            } else {
                int64_t ev = arg_num_of(expect);
                matched = c.kind == ArrayCell::Kind::NUM && c.num == ev;
            }
            if (matched) arr_store(c, upd);
            if (std::getenv("MINIANDROID_ATOMIC_DIAG")) {
                static thread_local uint64_t cas_arr_n = 0;
                if (cas_arr_n < 150) {
                    ++cas_arr_n;
                    std::cerr << "[ATOMIC-DIAG] ARR-CAS arr=obj#" << recv
                              << " idx=" << idx
                              << " cell(k=" << (int)c.kind
                              << " ref=" << c.ref_id << " num=" << c.num << ")"
                              << " expect(k=" << (int)expect.kind << ")"
                              << " -> " << (matched ? "SWAP" : "FAIL")
                              << std::endl;
                }
            }
            return CallResult::handled_bool(matched);
        }
        return CallResult::not_handled();
    }

    // ── constructors ────────────────────────────────────────────────────
    if (m == "<init>") {
        AtomicCell& c = cells_[recv];
        if (is_ref) {
            c.kind = AtomicCell::Kind::REF;
            if (arg_is_object(0)) {
                c.ref_id = ctx.args[0].object_id;
                c.ref_cls = ctx.args[0].object_class;
                c.ref_str.clear();
            } else if (arg_is_string(0)) {
                c.ref_id = 0;
                c.ref_cls.clear();
                c.ref_str = ctx.args[0].string_val;
            } else {
                c.ref_id = 0;
                c.ref_cls.clear();
                c.ref_str.clear();
            }
        } else if (is_int) {
            c.kind = AtomicCell::Kind::NUM;
            c.num = ctx.args.empty() ? 0 : ctx.arg_as_int(0);
        } else if (is_long) {
            c.kind = AtomicCell::Kind::NUM;
            c.num = ctx.args.empty() ? 0 : arg_num(0);
        } else { // is_bool
            c.kind = AtomicCell::Kind::NUM;
            c.num = (!ctx.args.empty() && ctx.arg_as_bool(0)) ? 1 : 0;
        }
        return CallResult::handled_void();
    }

    AtomicCell& c = cells_[recv];
    if (c.kind == AtomicCell::Kind::EMPTY) {
        // Method call on an object whose constructor was never dispatched
        // (allocated before our registration). Adopt the JVM zero value
        // instead of failing — matches the field zero-initialization law.
        c.kind = is_ref ? AtomicCell::Kind::REF : AtomicCell::Kind::NUM;
    }

    // ── reference payload readers/writers ───────────────────────────────
    auto ref_get = [&]() -> CallResult {
        if (c.ref_id != 0)
            return CallResult::handled_object(c.ref_id, c.ref_cls);
        if (!c.ref_str.empty())
            return CallResult::handled_string(c.ref_str);
        return CallResult::handled_null();
    };
    auto ref_set = [&](const CallContext& cc) {
        c.kind = AtomicCell::Kind::REF;
        if (arg_is_object(0)) {
            c.ref_id = cc.args[0].object_id;
            c.ref_cls = cc.args[0].object_class;
            c.ref_str.clear();
        } else if (arg_is_string(0)) {
            c.ref_id = 0;
            c.ref_cls.clear();
            c.ref_str = cc.args[0].string_val;
        } else {
            c.ref_id = 0;
            c.ref_cls.clear();
            c.ref_str.clear();
        }
    };

    // ── AtomicReference semantics ───────────────────────────────────────
    if (is_ref) {
        // F-072 diag (env-gated): plain-reference cell forensics.
        if (std::getenv("MINIANDROID_ATOMIC_DIAG")) {
            static thread_local uint64_t ref_log_n = 0;
            if (ref_log_n < 400) {
                ++ref_log_n;
                std::cerr << "[ATOMIC-DIAG] REF " << m << " recv=obj#" << recv
                          << " cell(k=" << (int)c.kind
                          << " ref=" << c.ref_id
                          << " str=\"" << c.ref_str << "\")"
                          << " nargs=" << ctx.args.size();
                for (size_t i = 0; i < ctx.args.size() && i < 3; ++i) {
                    int k = (int)ctx.args[i].kind;
                    std::cerr << " a" << i << "=k" << k;
                    if (k == (int)CallContext::Arg::Kind::OBJECT)
                        std::cerr << "(obj#" << ctx.args[i].object_id << ")";
                }
                std::cerr << std::endl;
            }
        }
        if (m == "get") return ref_get();
        if (m == "set" || m == "lazySet") {
            ref_set(ctx);
            return CallResult::handled_void();
        }
        if (m == "getAndSet") {
            CallResult old = ref_get();
            ref_set(ctx);
            return old;
        }
        if (m == "compareAndSet" || m == "weakCompareAndSet") {
            // F-072 (R-NEW-296) — CAS UPDATE-VALUE LAW (OpenJDK
            // java.util.concurrent.atomic.AtomicReference.compareAndSet(
            // expected, update)): arg0 = expected, arg1 = update. On match
            // the cell must store **arg1**. The previous code stored the
            // FIRST argument via ref_set(ctx) — for the common CAS(null →
            // values) idiom it wrote the expected value (null) back,
            // leaving the reference permanently null after a "successful"
            // CAS. Real-APK impact (dooz, compose 1.5.x
            // CompositionImpl.recordModificationsOf): CAS(null → values)
            // returned true but stored null, so the immediately following
            // drainPendingModificationsLocked() read null and threw
            // ComposeRuntimeError "calling recordModificationsOf and
            // applyChanges concurrently is not supported" — the second
            // dooz first-frame blocker. The numeric family already
            // implemented this law (c.num = update); the array and
            // field-updater families use arg1/arg2 respectively. Identity
            // law: compare by object identity (== for objects, value for
            // the engine's string model), null matches only null.
            bool matched;
            if (c.ref_id != 0) {
                matched = arg_is_object(0) && ctx.args[0].object_id == c.ref_id;
            } else if (!c.ref_str.empty()) {
                matched = arg_is_string(0) && ctx.args[0].string_val == c.ref_str;
            } else {
                matched = ctx.args.empty() ||
                          ctx.args[0].kind == CallContext::Arg::Kind::NULL_REF;
            }
            if (matched) {
                // Store the UPDATE (arg1) with the same payload-shape law
                // as ref_set, but addressed at index 1.
                c.kind = AtomicCell::Kind::REF;
                if (arg_is_object(1)) {
                    c.ref_id = ctx.args[1].object_id;
                    c.ref_cls = ctx.args[1].object_class;
                    c.ref_str.clear();
                } else if (arg_is_string(1)) {
                    c.ref_id = 0;
                    c.ref_cls.clear();
                    c.ref_str = ctx.args[1].string_val;
                } else {
                    c.ref_id = 0;
                    c.ref_cls.clear();
                    c.ref_str.clear();
                }
            }
            return CallResult::handled_bool(matched);
        }
        return CallResult::not_handled();
    }

    // ── AtomicInteger / AtomicLong numeric semantics ────────────────────
    if (is_int || is_long) {
        const bool wide = is_long;
        if (m == "get") {
            return wide ? CallResult::handled_long(c.num)
                        : CallResult::handled_int(static_cast<int32_t>(c.num));
        }
        if (m == "set" || m == "lazySet") {
            c.num = arg_num(0);
            return CallResult::handled_void();
        }
        if (m == "getAndSet") {
            int64_t old = c.num;
            c.num = arg_num(0);
            return wide ? CallResult::handled_long(old)
                        : CallResult::handled_int(static_cast<int32_t>(old));
        }
        if (m == "compareAndSet" || m == "weakCompareAndSet") {
            // Numeric law: compare by VALUE.
            int64_t expect = arg_num(0);
            int64_t update = arg_num(1);
            bool matched = (c.num == expect);
            if (matched) c.num = update;
            return CallResult::handled_bool(matched);
        }
        if (m == "addAndGet") {
            c.num += arg_num(0);
            return wide ? CallResult::handled_long(c.num)
                        : CallResult::handled_int(static_cast<int32_t>(c.num));
        }
        if (m == "getAndAdd") {
            int64_t old = c.num;
            c.num += arg_num(0);
            return wide ? CallResult::handled_long(old)
                        : CallResult::handled_int(static_cast<int32_t>(old));
        }
        if (m == "incrementAndGet") {
            c.num += 1;
            return wide ? CallResult::handled_long(c.num)
                        : CallResult::handled_int(static_cast<int32_t>(c.num));
        }
        if (m == "getAndIncrement") {
            int64_t old = c.num;
            c.num += 1;
            return wide ? CallResult::handled_long(old)
                        : CallResult::handled_int(static_cast<int32_t>(old));
        }
        if (m == "decrementAndGet") {
            c.num -= 1;
            return wide ? CallResult::handled_long(c.num)
                        : CallResult::handled_int(static_cast<int32_t>(c.num));
        }
        if (m == "getAndDecrement") {
            int64_t old = c.num;
            c.num -= 1;
            return wide ? CallResult::handled_long(old)
                        : CallResult::handled_int(static_cast<int32_t>(old));
        }
        if (m == "intValue")
            return CallResult::handled_int(static_cast<int32_t>(c.num));
        if (m == "longValue") return CallResult::handled_long(c.num);
        return CallResult::not_handled();
    }

    // ── AtomicBoolean semantics ─────────────────────────────────────────
    if (is_bool) {
        if (m == "get") return CallResult::handled_bool(c.num != 0);
        if (m == "set" || m == "lazySet") {
            c.num = ctx.arg_as_bool(0) ? 1 : 0;
            return CallResult::handled_void();
        }
        if (m == "getAndSet") {
            int64_t old = c.num;
            c.num = ctx.arg_as_bool(0) ? 1 : 0;
            return CallResult::handled_bool(old != 0);
        }
        if (m == "compareAndSet" || m == "weakCompareAndSet") {
            bool expect = ctx.arg_as_bool(0);
            bool update = ctx.arg_as_bool(1);
            bool matched = ((c.num != 0) == expect);
            if (matched) c.num = update ? 1 : 0;
            return CallResult::handled_bool(matched);
        }
        return CallResult::not_handled();
    }

    return CallResult::not_handled();
}

}} // namespace miniandroid::framework
