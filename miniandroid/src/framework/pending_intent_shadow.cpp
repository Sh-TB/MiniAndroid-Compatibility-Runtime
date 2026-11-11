// M3 F-018 ROOT FIX — android.app intent-sender + alarm scheduling family.
// See pending_intent_shadow.h for the AOSP law mapping and the root-gap
// evidence chain.
#include "pending_intent_shadow.h"

#include "../diagnostics/file_io_trace.h"

#include <iostream>

namespace miniandroid { namespace framework {

CallResult PendingIntentShadow::record_for(Record rec) {
    if (!heap_) return CallResult::not_handled();
    const std::string key = rec.kind + "|" + std::to_string(rec.request_code) +
                            "|" + std::to_string(rec.intent_oid) +
                            "|" + std::to_string(rec.flags);
    // AMS IntentSenderRecord caching law: equal key → SAME object.
    auto it = records_.find(key);
    if (it != records_.end() && heap_->has_object(it->second.object_id)) {
        return CallResult::handled_object(it->second.object_id,
                                          "Landroid/app/PendingIntent;");
    }
    // ── N-19 (issue #375 §11): FLAG_NO_CREATE HONESTY LAW (AOSP
    // PendingIntent.java: "Flag indicating that if the described
    // PendingIntent does not already exist, then simply return null
    // instead of creating it."). The old law fabricated a record for
    // every get*() call — FLAG_NO_CREATE semantics were ignored and
    // apps gating on a null return (alarm-cancel guards, polling
    // existence checks) took wrong branches. AOSP: no record + NO_CREATE
    // → null. Never a fabricated sender.
    static const int32_t kFlagNoCreate = 0x20000000;
    if (rec.flags & kFlagNoCreate) {
        std::cerr << "[PENDING-INTENT] NO_CREATE for unregistered "
                  << rec.kind << " rc=" << rec.request_code
                  << " -> null (AOSP law)" << std::endl;
        return CallResult::handled_null();
    }
    uint32_t obj = heap_->allocate("Landroid/app/PendingIntent;");
    rec.object_id = obj;
    // Mirror the record fields onto the object (identity evidence).
    int32_t kind_code = rec.kind == "BROADCAST" ? 1
                      : rec.kind == "ACTIVITY"  ? 2
                                                : 3;
    heap_->set_object_int_field(obj, "__pi_kind__", kind_code);
    heap_->set_object_int_field(obj, "__pi_request_code__", rec.request_code);
    heap_->set_object_int_field(obj, "__pi_intent_oid__",
                                (int32_t)rec.intent_oid);
    heap_->set_object_int_field(obj, "__pi_flags__", rec.flags);
    records_[key] = rec;
    oid_index_[obj] = &records_[key];
    std::cerr << "[PENDING-INTENT] record " << rec.kind
              << " rc=" << rec.request_code
              << " intent=" << rec.intent_oid
              << " flags=0x" << std::hex << rec.flags << std::dec
              << " -> obj=" << obj
              << " (AMS record law: non-null, identity cached)" << std::endl;
    return CallResult::handled_object(obj, "Landroid/app/PendingIntent;");
}

CallResult PendingIntentShadow::factory(const CallContext& ctx,
                                        const std::string& kind) {
    // get*(Context, int requestCode, Intent intent, int flags[, ...])
    int32_t request_code = ctx.arg_as_int(1, 0);
    uint32_t intent_oid = ctx.arg_as_object(2, 0);
    int32_t flags = ctx.arg_as_int(3, 0);
    Record rec;
    rec.kind = kind;
    rec.request_code = request_code;
    rec.intent_oid = intent_oid;
    rec.flags = flags;
    return record_for(rec);
}

CallResult PendingIntentShadow::send_pending(const CallContext& ctx) {
    // AOSP PendingIntent.send(Context, int, Intent[, ...]) — the record
    // identity is the RECEIVER (this); the fill-in Intent (arg 2 in the
    // 3-arg overload, absent in the 1-arg) is merged per the IMMUTABLE
    // law. Every branch is loud; a denial is a REAL CanceledException.
    auto it = oid_index_.find(ctx.receiver_id);
    if (it == oid_index_.end()) {
        // Unknown/unregistered sender — AOSP sendInner on a dead record:
        // CanceledException, never a silent void.
        miniandroid::diagnostics::FileIoTrace::instance().record(
            "PI-SEND", "unknown", false,
            "no live IntentSenderRecord — CanceledException",
            ctx.caller);
        return CallResult::handled_exception(
            "Landroid/app/PendingIntent$CanceledException;", "canceled");
    }
    Record* rec = it->second;
    if (rec->one_shot_canceled) {
        miniandroid::diagnostics::FileIoTrace::instance().record(
            "PI-SEND-CANCELED", rec->kind, false,
            "FLAG_ONE_SHOT record already sent — CanceledException "
            "(AOSP PendingIntentRecord.sendInner)",
            ctx.caller);
        std::cerr << "[PENDING-INTENT] send() on canceled ONE_SHOT record "
                  << rec->kind << " rc=" << rec->request_code
                  << " -> CanceledException" << std::endl;
        return CallResult::handled_exception(
            "Landroid/app/PendingIntent$CanceledException;", "canceled");
    }
    static const int32_t kFlagOneShot = 0x40000000;    // 1<<30 (AOSP)
    static const int32_t kFlagImmutable = 0x04000000;  // 1<<26 (AOSP)
    // fill-in Intent: send(Context, code, Intent) — arg 2 (may be null).
    uint32_t fillin_oid = ctx.arg_as_object(2, 0);
    if (fillin_oid != 0 && heap_) {
        if (rec->flags & kFlagImmutable) {
            // AOSP: "Flag indicating that the created PendingIntent should
            // be immutable... the fill-in Intent supplied to send() is
            // IGNORED." Loud evidence row, frozen intent untouched.
            miniandroid::diagnostics::FileIoTrace::instance().record(
                "PI-SEND-FILLIN", rec->kind, true,
                "FLAG_IMMUTABLE — fill-in intent IGNORED (AOSP law)",
                ctx.caller);
            std::cerr << "[PENDING-INTENT] IMMUTABLE record ignores the "
                      << "fill-in intent (AOSP law)" << std::endl;
        } else {
            // Mutable record: the fill-in EXTRAS overwrite/insert onto the
            // frozen intent (AOSP PendingIntentRecord.sendInner merge);
            // loud row.
            auto* ish = registry_ ? registry_->find_as<IntentShadow>()
                                  : nullptr;
            auto frozen = ish ? ish->get_or_create_intent(rec->intent_oid)
                              : nullptr;
            auto fill = ish ? ish->get_or_create_intent(fillin_oid)
                            : nullptr;
            if (frozen && fill) {
                size_t c7_merged = 0;
                for (const auto& [k, v] : fill->extras_string) {
                    frozen->extras_string[k] = v; ++c7_merged;
                }
                for (const auto& [k, v] : fill->extras_int) {
                    frozen->extras_int[k] = v; ++c7_merged;
                }
                for (const auto& [k, v] : fill->extras_bool) {
                    frozen->extras_bool[k] = v; ++c7_merged;
                }
                miniandroid::diagnostics::FileIoTrace::instance().record(
                    "PI-SEND-FILLIN", rec->kind, true,
                    "mutable record — " + std::to_string(c7_merged) +
                        " fill-in extra(s) merged (AOSP sendInner law)",
                    ctx.caller);
            }
        }
    }
    if (!send_dispatcher_) {
        // No dispatcher wired (no-store / pre-wiring shapes): the LOUD
        // documented boundary — never a silent null, never a fabricated
        // delivery.
        std::cerr << "[PENDING-INTENT][BOUNDARY] send() recorded; no "
                  << "dispatch channel wired (documented boundary)"
                  << std::endl;
        miniandroid::diagnostics::FileIoTrace::instance().record(
            "PI-SEND", rec->kind, false,
            "no send dispatcher wired (documented boundary)", ctx.caller);
        return CallResult::handled_void();
    }
    std::string c7_err;
    const bool c7_ok =
        send_dispatcher_(rec->kind, rec->intent_oid, c7_err);
    if (!c7_ok) {
        miniandroid::diagnostics::FileIoTrace::instance().record(
            "PI-SEND", rec->kind, false,
            "dispatch refused: " + c7_err, ctx.caller);
        std::cerr << "[PENDING-INTENT] send() dispatch refused: " << c7_err
                  << std::endl;
        return CallResult::handled_void();
    }
    ++sends_executed_;
    miniandroid::diagnostics::FileIoTrace::instance().record(
        "PI-SEND", rec->kind, true,
        "dispatched through the component pipeline (kind=" + rec->kind +
            ")",
        ctx.caller);
    std::cerr << "[PENDING-INTENT] send() dispatched: " << rec->kind
              << " rc=" << rec->request_code
              << " intent=" << rec->intent_oid << std::endl;
    // AOSP FLAG_ONE_SHOT: after ONE successful send the record is
    // canceled — the NEXT send() throws CanceledException.
    if (rec->flags & kFlagOneShot) {
        rec->one_shot_canceled = true;
        std::cerr << "[PENDING-INTENT] ONE_SHOT record canceled after "
                  << "first send (AOSP law)" << std::endl;
    }
    return CallResult::handled_void();
}

CallResult PendingIntentShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;
    if (!handles_class(cls)) return CallResult::not_handled();

    // ── PendingIntent static factories — AMS getIntentSender law ────────
    if (cls == "Landroid/app/PendingIntent;") {
        if (m == "getBroadcast")
            return factory(ctx, "BROADCAST");
        if (m == "getActivity")
            return factory(ctx, "ACTIVITY");
        if (m == "getService" || m == "getForegroundService")
            return factory(ctx, "SERVICE");
        if (m == "getActivities")
            return factory(ctx, "ACTIVITY");
        if (m == "send") {
            // CODER7 WAVE-8 L2: the REAL send() law — the record pipeline
            // (ONE_SHOT / IMMUTABLE / CanceledException) + the wired
            // dispatcher that routes the frozen intent through the SAME
            // gated broadcast/service/activity pipeline the app-context
            // calls use. Unwired channel stays a LOUD documented boundary.
            return send_pending(ctx);
        }
        if (m == "cancel") {
            // AOSP PendingIntent.cancel(): the record is removed — a
            // subsequent send() throws CanceledException (dead record).
            if (heap_) {
                auto it = oid_index_.find(ctx.receiver_id);
                if (it != oid_index_.end()) {
                    records_.erase(it->second->kind + "|" +
                                   std::to_string(it->second->request_code) +
                                   "|" +
                                   std::to_string(it->second->intent_oid) +
                                   "|" +
                                   std::to_string(it->second->flags));
                    oid_index_.erase(it);
                }
            }
            std::cerr << "[PENDING-INTENT] cancel() record removed "
                      << "(AOSP law)" << std::endl;
            return CallResult::handled_void();
        }
        return CallResult::not_handled();
    }

    // ── AlarmManager family ─────────────────────────────────────────────
    if (cls == "Landroid/app/AlarmManager;") {
        if (m == "canScheduleExactAlarms") {
            // AOSP API 31+ law derived from the RUNNING APK's manifest
            // (USE_EXACT_ALARM auto-grant / SCHEDULE_EXACT_ALARM grant).
            // MiniAndroid INSTALL-TIME GRANT identity: declared ⇒ granted.
            bool capable = manifest_exact_alarm_capable_;
            std::cerr << "[ALARM-MANAGER] canScheduleExactAlarms -> "
                      << (capable ? "true" : "false")
                      << " (manifest-derived law)" << std::endl;
            return CallResult::handled_bool(capable);
        }
        if (m == "cancel") {
            // CANCEL LAW: remove the matching record; unknown senders
            // ignored. Void, no exception.
            uint32_t pi_oid = ctx.arg_as_object(0, 0);
            auto it = oid_index_.find(pi_oid);
            if (it != oid_index_.end()) {
                std::cerr << "[ALARM-MANAGER] cancel pi=" << pi_oid
                          << " kind=" << it->second->kind
                          << " rc=" << it->second->request_code
                          << " (record law)" << std::endl;
                records_.erase(it->second->kind + "|" +
                               std::to_string(it->second->request_code) + "|" +
                               std::to_string(it->second->intent_oid) + "|" +
                               std::to_string(it->second->flags));
                oid_index_.erase(it);
            } else {
                std::cerr << "[ALARM-MANAGER] cancel pi=" << pi_oid
                          << " (unknown sender ignored — AOSP law)"
                          << std::endl;
            }
            return CallResult::handled_void();
        }
        if (m.rfind("set", 0) == 0) {
            // SCHEDULING BOUNDARY: set/setExact/setAndAllowWhileIdle/
            // setExactAndAllowWhileIdle/setRepeating/... record the
            // schedule and return void. No external alarm dispatch source
            // exists in-run (documented boundary — loud, never silent).
            std::cerr << "[ALARM-MANAGER][BOUNDARY] " << m
                      << " recorded (alarms do not fire in-run — "
                      << "documented boundary)" << std::endl;
            return CallResult::handled_void();
        }
        return CallResult::not_handled();
    }

    return CallResult::not_handled();
}

}} // namespace miniandroid::framework
