// A-R6 R30 — KOTLIN WELL-KNOWN-TYPES SHADOW (implementation).
//
// See kotlin_shadow.h for the finding, the laws, and the documented
// boundaries. This file implements the four well-known-type claims:
//   Lkotlin/Unit;      — the object-declaration singleton identity
//   Lkotlin/Pair;      — verbatim 2-argument product + componentN + toString
//   Lkotlin/Triple;    — verbatim 3-argument product + componentN + toString
//   Lkotlin/jvm/internal/Intrinsics; — the null-safety contract face
//
// State model: <init> writes the constructor arguments into the HEAP
// OBJECT's field map ("first"/"second"/"third") through the HeapAllocator
// set_value_field law (A-R6, heap_adapter) — the SAME storage the
// interpreter's iget-object reads — so direct field readers
// (p.first in DEX) and shadow-dispatched componentN() readers observe one
// state. No shadow-side parallel store (the F-NEW-510 lesson: parallel
// stores drift from the heap).

#include "kotlin_shadow.h"

#include <array>
#include <iostream>
#include <unordered_map>

namespace miniandroid {
namespace framework {

namespace {

// Arg → the CallResult face (componentN returns the stored value verbatim).
CallResult arg_to_result(const CallContext::Arg& a) {
    switch (a.kind) {
        case CallContext::Arg::Kind::STRING:
            return CallResult::handled_string(a.string_val);
        case CallContext::Arg::Kind::OBJECT:
            return CallResult::handled_object(a.object_id, a.object_class);
        case CallContext::Arg::Kind::INT:
            return CallResult::handled_int(a.int_val);
        case CallContext::Arg::Kind::LONG:
            return CallResult::handled_long(a.long_val);
        case CallContext::Arg::Kind::BOOL:
            return CallResult::handled_bool(a.bool_val);
        case CallContext::Arg::Kind::FLOAT:
            return CallResult::handled_float(a.float_val);
        case CallContext::Arg::Kind::DOUBLE:
            return CallResult::handled_double(a.double_val);
        case CallContext::Arg::Kind::NULL_REF:
        default:
            return CallResult::handled_null();
    }
}

// Kotlin string-template rendering of a stored value: String → content;
// null → "null"; anything else → the runtime class readable form (no
// fabricated content — the documented boundary; identity semantics live
// in componentN).
std::string arg_render(const CallContext::Arg& a) {
    switch (a.kind) {
        case CallContext::Arg::Kind::STRING:
            return a.string_val;
        case CallContext::Arg::Kind::INT:
            return std::to_string(a.int_val);
        case CallContext::Arg::Kind::LONG:
            return std::to_string(a.long_val);
        case CallContext::Arg::Kind::BOOL:
            return a.bool_val ? "true" : "false";
        case CallContext::Arg::Kind::NULL_REF:
            return "null";
        case CallContext::Arg::Kind::OBJECT: {
            std::string cls = a.object_class;
            // "Lkotlin/Unit;" → "kotlin.Unit" (the readable form the
            // engine's to_readable_class law derives).
            if (cls.size() >= 2 && cls.front() == 'L' && cls.back() == ';')
                cls = cls.substr(1, cls.size() - 2);
            for (auto& ch : cls)
                if (ch == '/') ch = '.';
            return cls;
        }
        default:
            return "null";
    }
}

bool is_kotlin_well_known(const std::string& cls) {
    return cls == "Lkotlin/Unit;" || cls == "Lkotlin/Pair;" ||
           cls == "Lkotlin/Triple;" ||
           cls == "Lkotlin/jvm/internal/Intrinsics;";
}

}  // namespace

bool KotlinShadow::handles_class(const std::string& class_name) const {
    return is_kotlin_well_known(class_name);
}

std::vector<std::string> KotlinShadow::implemented_methods() const {
    return {"Lkotlin/Unit;.INSTANCE",
            "Lkotlin/Pair;.<init>",
            "Lkotlin/Pair;.component1",
            "Lkotlin/Pair;.component2",
            "Lkotlin/Pair;.toString",
            "Lkotlin/Triple;.<init>",
            "Lkotlin/Triple;.component1",
            "Lkotlin/Triple;.component2",
            "Lkotlin/Triple;.component3",
            "Lkotlin/Triple;.toString",
            "Lkotlin/jvm/internal/Intrinsics;.checkNotNullParameter",
            "Lkotlin/jvm/internal/Intrinsics;.checkNotNullExpressionValue",
            "Lkotlin/jvm/internal/Intrinsics;.checkNotNull"};
}

std::vector<std::string> KotlinShadow::stubbed_methods() const {
    return {"Lkotlin/Pair;.hashCode (needs the receiver-value hashCode "
            "chain — documented boundary)",
            "Lkotlin/Triple;.hashCode (same boundary)"};
}

CallResult KotlinShadow::dispatch(const CallContext& ctx) {
    if (!is_kotlin_well_known(ctx.class_name))
        return CallResult::not_handled();
    const std::string& m = ctx.method;

    // ── kotlin.jvm.internal.Intrinsics — the null-safety contract ──────
    if (ctx.class_name == "Lkotlin/jvm/internal/Intrinsics;") {
        if (m != "checkNotNullParameter" && m != "checkNotNullExpressionValue" &&
            m != "checkNotNull")
            return CallResult::not_handled();
        // checkNotNull(Object, String message) variant: the message IS the
        // first argument. The parameter-name variants carry (value, name).
        bool value_first = (m != "checkNotNull");
        const CallContext::Arg& value =
            value_first ? ctx.args[0]
                        : (ctx.args.empty() ? CallContext::Arg{}
                                            : ctx.args[0]);
        // Kotlin null face: the reference-typed parameter slot carries the
        // null literal. Dalvik mints null as `const/4 vN, 0`; the bridge's
        // arg form may deliver it as NULL_REF or as INT 0 (the register's
        // int zero with the reference typing applied only at the descriptor
        // level). At THIS boundary the parameter IS reference-typed
        // (Ljava/lang/Object;), so INT 0 in the value slot IS the null
        // literal — ART's proto-typing law, documented here per K-6.
        const bool value_is_null =
            value.kind == CallContext::Arg::Kind::NULL_REF ||
            (value.kind == CallContext::Arg::Kind::INT &&
             value.int_val == 0);
        if (value_is_null) {
            // Kotlin law: "Parameter specified as non-null is null: <name>"
            // (checkNotNull: the caller-supplied message stands alone).
            std::string msg;
            if (value_first) {
                std::string name = ctx.args.size() >= 2
                                       ? ctx.args[1].string_val
                                       : std::string("(unknown parameter)");
                msg = "Parameter specified as non-null is null: " + name;
            } else if (ctx.args.size() >= 2) {
                msg = ctx.args[1].string_val;
            } else {
                msg = "Parameter specified as non-null is null";
            }
            return CallResult::handled_exception(
                "Ljava/lang/NullPointerException;", msg);
        }
        // Non-null → no-op (the contract holds; execution continues).
        return CallResult::handled_void();
    }

    // ── kotlin.Unit — object declaration: not constructible ────────────
    if (ctx.class_name == "Lkotlin/Unit;") {
        // The singleton identity is served by the sget-object INSTANCE law
        // (dalvik_engine). <init> is private in the stdlib; a guest-world
        // direct call would be an illegal-access face — the honest answer
        // is the void no-op with the object already seeded (documented).
        return CallResult::handled_void();
    }

    // ── kotlin.Pair / kotlin.Triple — the product semantics ────────────
    const bool is_pair = (ctx.class_name == "Lkotlin/Pair;");
    const size_t arity = is_pair ? 2 : 3;
    static const char* kFieldNames[3] = {"first", "second", "third"};

    if (m == "<init>") {
        if (!ctx.has_receiver || ctx.receiver_id == 0 ||
            ctx.args.size() < arity)
            return CallResult::not_handled();
        for (size_t i = 0; i < arity; ++i) {
            if (!heap_->set_value_field(ctx.receiver_id, kFieldNames[i],
                                        ctx.args[i])) {
                // Adapter cannot write (no heap bound) — the components
                // would read null; honest loud diagnostic, per K-6.
                std::cerr << "[KOTLIN-SHADOW] " << ctx.class_name
                          << ".<init> could not persist field "
                          << kFieldNames[i] << " on o"
                          << ctx.receiver_id << std::endl;
            }
        }
        return CallResult::handled_void();
    }

    if (m.rfind("component", 0) == 0 && m.size() > 9) {
        // component1/component2/component3 → ordinal N.
        int n = m[9] - '1';
        if (n < 0 || n >= static_cast<int>(arity) || !ctx.has_receiver ||
            ctx.receiver_id == 0)
            return CallResult::not_handled();
        CallContext::Arg out;
        if (!heap_->get_value_field(ctx.receiver_id, kFieldNames[n], out))
            return CallResult::handled_null();
        return arg_to_result(out);
    }

    if (m == "toString" && ctx.has_receiver && ctx.receiver_id != 0) {
        std::array<CallContext::Arg, 3> vals;
        for (size_t i = 0; i < arity; ++i)
            heap_->get_value_field(ctx.receiver_id, kFieldNames[i], vals[i]);
        std::string out = "(";
        for (size_t i = 0; i < arity; ++i) {
            if (i) out += ", ";
            out += arg_render(vals[i]);
        }
        out += ")";
        return CallResult::handled_string(out);
    }

    // hashCode needs the receiver-value hashCode chain (documented
    // boundary — see stubbed_methods()); everything else unhandled.
    return CallResult::not_handled();
}

}  // namespace framework
}  // namespace miniandroid
