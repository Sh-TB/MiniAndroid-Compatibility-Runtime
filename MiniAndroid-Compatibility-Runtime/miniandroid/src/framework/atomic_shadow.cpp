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

    const bool is_ref  = cls == "Ljava/util/concurrent/atomic/AtomicReference;";
    const bool is_int  = cls == "Ljava/util/concurrent/atomic/AtomicInteger;";
    const bool is_long = cls == "Ljava/util/concurrent/atomic/AtomicLong;";
    const bool is_bool = cls == "Ljava/util/concurrent/atomic/AtomicBoolean;";
    // M4 F-028d — the three field-updater families.
    const bool is_ref_upd  = cls == "Ljava/util/concurrent/atomic/AtomicReferenceFieldUpdater;";
    const bool is_long_upd = cls == "Ljava/util/concurrent/atomic/AtomicLongFieldUpdater;";
    const bool is_int_upd  = cls == "Ljava/util/concurrent/atomic/AtomicIntegerFieldUpdater;";
    if (!is_ref && !is_int && !is_long && !is_bool &&
        !is_ref_upd && !is_long_upd && !is_int_upd) return CallResult::not_handled();

    // ── Atomic*FieldUpdater family (M4 F-028d) ─────────────────────────
    // Java/AOSP law (libcore/ojluni): newUpdater(tclass, vclass, fieldName)
    // is a STATIC factory returning an updater bound to the named field;
    // get/set/CAS on the updater read/write the TARGET object's field with
    // volatile semantics. Reference updaters compare by object identity
    // (== law, null matches null); numeric updaters compare by value.
    // The engine is single-threaded/deterministic: CAS succeeds exactly
    // when the read value matches.
    if (is_ref_upd || is_long_upd || is_int_upd) {
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
        if (!ctx.has_receiver) return CallResult::not_handled();
        const std::string& fname = updater_field(recv);
        if (fname.empty()) return CallResult::not_handled();
        // target = first argument
        if (ctx.args.empty() ||
            ctx.args[0].kind != CallContext::Arg::Kind::OBJECT)
            return CallResult::not_handled();
        const uint32_t target = ctx.args[0].object_id;
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
        if (m == "get") return CallResult::handled_long(num_read());
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
            int64_t oldv = num_read();
            int64_t nv = oldv + ((m.rfind("increment", 0) == 0) ? 1 : -1);
            num_write(nv);
            bool want_new = (m.rfind("getAnd", 0) != 0);
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
            // Reference law: compare by identity (== for objects, value for
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
            if (matched) ref_set(ctx);
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
