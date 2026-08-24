// SPDX-License-Identifier: MIT
// MiniAndroid Compatibility Runtime
// EXP-051 — Android Framework Shadow Registry (implementation)

#include "shadow_registry.h"

#include <algorithm>
#include <iomanip>
#include <sstream>

namespace miniandroid { namespace framework {

// ─────────────────────────────────────────────────────────────────────────
// CallContext argument helpers
// ─────────────────────────────────────────────────────────────────────────
int32_t CallContext::arg_as_int(size_t i, int32_t default_val) const {
    if (i >= args.size()) return default_val;
    const auto& a = args[i];
    switch (a.kind) {
        case CallContext::Arg::Kind::INT:   return a.int_val;
        case CallContext::Arg::Kind::LONG:  return static_cast<int32_t>(a.long_val);
        case CallContext::Arg::Kind::BOOL:  return a.bool_val ? 1 : 0;
        case CallContext::Arg::Kind::FLOAT: return static_cast<int32_t>(a.float_val);
        case CallContext::Arg::Kind::DOUBLE:return static_cast<int32_t>(a.double_val);
        default: return default_val;
    }
}

bool CallContext::arg_as_bool(size_t i, bool default_val) const {
    if (i >= args.size()) return default_val;
    const auto& a = args[i];
    switch (a.kind) {
        case CallContext::Arg::Kind::BOOL: return a.bool_val;
        case CallContext::Arg::Kind::INT:   return a.int_val != 0;
        case CallContext::Arg::Kind::LONG:  return a.long_val != 0;
        default: return default_val;
    }
}

std::string CallContext::arg_as_string(size_t i, const std::string& default_val) const {
    if (i >= args.size()) return default_val;
    const auto& a = args[i];
    if (a.kind == CallContext::Arg::Kind::STRING) return a.string_val;
    // EXP-091: Support OBJECT_REF strings — when setText(CharSequence) is called
    // with a String object from move-result-object (e.g., from LocaleController.getString()),
    // the arg is OBJECT kind with object_id pointing to a heap String.
    // We need to resolve the actual string value from the object's string_val field.
    if (a.kind == CallContext::Arg::Kind::OBJECT && a.string_val.empty() == false) {
        return a.string_val;
    }
    return default_val;
}

uint32_t CallContext::arg_as_object(size_t i, uint32_t default_val) const {
    if (i >= args.size()) return default_val;
    const auto& a = args[i];
    if (a.kind == CallContext::Arg::Kind::OBJECT) return a.object_id;
    if (a.kind == CallContext::Arg::Kind::NULL_REF) return 0;
    return default_val;
}

// ─────────────────────────────────────────────────────────────────────────
// CallResult factories
// ─────────────────────────────────────────────────────────────────────────
CallResult CallResult::handled_int(int32_t v) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::INT; r.int_val = v; return r;
}
CallResult CallResult::handled_long(int64_t v) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::LONG; r.long_val = v; return r;
}
CallResult CallResult::handled_float(float v) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::FLOAT; r.float_val = v; return r;
}
CallResult CallResult::handled_double(double v) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::DOUBLE; r.double_val = v; return r;
}
CallResult CallResult::handled_bool(bool v) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::BOOL; r.bool_val = v; return r;
}
CallResult CallResult::handled_string(const std::string& s, uint32_t ref_id) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::STRING; r.string_val = s; r.object_id = ref_id; return r;
}
CallResult CallResult::handled_object(uint32_t obj_id, const std::string& cls) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::OBJECT; r.object_id = obj_id; r.object_class = cls; return r;
}
CallResult CallResult::handled_null() {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::NULL_REF; return r;
}
CallResult CallResult::handled_void() {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::VOID; return r;
}
CallResult CallResult::not_handled() {
    CallResult r; r.handled = false; r.status = ApiCallStatus::UNHANDLED; return r;
}

// ─────────────────────────────────────────────────────────────────────────
// ShadowRegistry
// ─────────────────────────────────────────────────────────────────────────
CallResult ShadowRegistry::dispatch(const CallContext& ctx) {
    calls_dispatched_++;
    for (auto& s : shadows_) {
        if (!s->handles_class(ctx.class_name)) continue;
        CallResult r = s->dispatch(ctx);
        if (r.handled) {
            calls_handled_++;
            return r;
        }
    }
    calls_fallback_++;
    return CallResult::not_handled();
}

ShadowRegistry::Stats ShadowRegistry::stats() const {
    Stats s;
    s.shadow_count = shadows_.size();
    for (const auto& sh : shadows_) {
        s.total_implemented += sh->implemented_methods().size();
        s.total_stubbed     += sh->stubbed_methods().size();
    }
    s.calls_dispatched = calls_dispatched_;
    s.calls_handled    = calls_handled_;
    s.calls_fallback   = calls_fallback_;
    return s;
}

Shadow* ShadowRegistry::find(const std::string& name) const {
    for (const auto& s : shadows_) {
        if (s->name() == name) return s.get();
    }
    return nullptr;
}

// ─────────────────────────────────────────────────────────────────────────
// Diagnostic dump
// ─────────────────────────────────────────────────────────────────────────
std::string format_shadow_report(const ShadowRegistry& reg) {
    std::ostringstream os;
    auto st = reg.stats();
    os << "Shadow Registry Report\n";
    os << "======================\n";
    os << "Shadows registered:        " << st.shadow_count << "\n";
    os << "Methods fully implemented:  " << st.total_implemented << "\n";
    os << "Methods stubbed:           " << st.total_stubbed << "\n";
    os << "Calls dispatched:           " << st.calls_dispatched << "\n";
    os << "  handled by a shadow:      " << st.calls_handled << "\n";
    os << "  fell through to legacy:   " << st.calls_fallback << "\n";
    if (st.calls_dispatched > 0) {
        double coverage = 100.0 * st.calls_handled / st.calls_dispatched;
        os << "Shadow coverage:            " << std::fixed << std::setprecision(1)
           << coverage << "%\n";
    }
    return os.str();
}

}} // namespace miniandroid::framework
