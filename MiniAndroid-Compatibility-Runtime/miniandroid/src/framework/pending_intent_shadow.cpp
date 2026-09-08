// M3 F-018 ROOT FIX — android.app intent-sender + alarm scheduling family.
// See pending_intent_shadow.h for the AOSP law mapping and the root-gap
// evidence chain.
#include "pending_intent_shadow.h"

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
            // DOCUMENTED BOUNDARY: in-run broadcast dispatch is not
            // demanded by the corpus; the stub is LOUD, never silent.
            std::cerr << "[PENDING-INTENT][BOUNDARY] send() recorded; "
                      << "in-run receiver dispatch not supported "
                      << "(documented boundary, never silent)" << std::endl;
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
