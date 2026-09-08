// M3 F-020 ROOT FIX — java.util.concurrent.atomic shadow implementation.
// See atomic_shadow.h for the Java/AOSP law mapping and the forensic
// root-gap record (Compose SnapshotKt.currentSnapshot reads the global
// snapshot out of an AtomicReference; a dropped constructor argument
// zeroed the whole snapshot id chain inside dooz's setContent).
#include "atomic_shadow.h"

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
    if (!is_ref && !is_int && !is_long && !is_bool) return CallResult::not_handled();

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
