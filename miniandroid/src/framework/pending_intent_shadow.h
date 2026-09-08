// M3 F-018 ROOT FIX — android.app intent-sender + alarm scheduling family.
//
// ROOT GAP (discovered via the F-012 second-run protocol at HEAD 4f0c9e1b):
// microtimer's second-run path (MainActivity.onResume with 1 persisted
// alarm row) re-registers each alarm through MainActivity.b:
//   new Intent → setAction → putExtra ×2 → setFlags →
//   PendingIntent.getBroadcast(...) → Intrinsics.checkNotNullExpressionValue
// The runtime had NO PendingIntent shadow and NO AlarmManager shadow, so
// the static factory fell through the dispatch chain ([EXP088-B-DISPATCH]
// MainActivity → Activity ...) and silently returned NULL. The Kotlin
// Intrinsics null-check ("getBroadcast(...) must not be null") then threw
// NPE in the obfuscated throw helper La/e;.g (pc=17), uncaught at
// MainActivity.onCreate → APP-BOUNDARY unwind → PARTIAL (rc-law failure
// of the F-012 golden). DEX ground truth (bounded probe of the APK):
//   PendingIntent.getBroadcast            ← MainActivity.b pc=46
//   AlarmManager.cancel                   ← MainActivity.onResume pc=58
//   AlarmManager.setExactAndAllowWhileIdle← MainActivity.onPause pc=123
//   AlarmManager.canScheduleExactAlarms   ← Lk/b;.a pc=0
//   PendingIntent.getActivity             ← AlarmReceiver.onReceive pc=80
//
// AOSP laws transferred (frameworks/base android.app.PendingIntent +
// android.app.AlarmManager):
//   * FACTORY NON-NULL LAW: getBroadcast/getActivity/getService/
//     getForegroundService delegate to ActivityManagerService
//     .getIntentSender(...) which either returns a live PendingIntent
//     record or throws SecurityException — the factory NEVER returns
//     null on the success path.
//   * RECORD IDENTITY LAW: AMS caches IntentSenderRecords keyed by
//     (type, requestCode, intent, flags); an equal get* call returns the
//     SAME PendingIntent object (PendingIntent.equals is target identity
//     equality). MiniAndroid deterministic mapping: cache keyed by
//     (kind, requestCode, intent-oid, flags) → heap object id; the
//     record fields are mirrored onto the object so later send()/
//     cancel() semantics can read them.
//   * CANCEL LAW: AlarmManager.cancel(PendingIntent) removes the alarm
//     whose IntentSender matches; unknown senders are ignored (void,
//     no exception). The deterministic runtime records the cancel and
//     drops the scheduled-alarm marker.
//   * EXACT-ALARM CAPABILITY LAW (API 31+): canScheduleExactAlarms()
//     returns true iff the app targets < S, OR declares USE_EXACT_ALARM
//     (auto-granted on 33+), OR was granted SCHEDULE_EXACT_ALARM.
//     MiniAndroid's INSTALL-TIME GRANT identity: manifest-declared
//     special permissions are granted (deterministic emulator law), so
//     the capability is derived from the RUNNING APK's manifest
//     permission list (execution_engine stage_load_apk plumbing via
//     set_manifest_exact_alarm_capable). Never hardcoded per-app.
//   * SCHEDULING BOUNDARY: set*/setExact*/setAndAllowWhileIdle* record
//     the alarm schedule and return void. The runtime has no external
//     alarm dispatch source — alarms do not fire in-run. This is a
//     DOCUMENTED BOUNDARY (loud diagnostic, never silent).
//   * send(): NOT demanded by the corpus (broadcast receivers are not
//     dispatched in-run). LOUD boundary stub — never a silent null.
//
// No fixture-specific code: android.app.PendingIntent/AlarmManager are
// platform classes any alarm/reminder/notification-scheduling APK may
// reference.
//
#ifndef MINIANDROID_FRAMEWORK_PENDING_INTENT_SHADOW_H
#define MINIANDROID_FRAMEWORK_PENDING_INTENT_SHADOW_H

#include "shadow_registry.h"

#include <map>
#include <string>

namespace miniandroid { namespace framework {

class PendingIntentShadow : public Shadow {
public:
    std::string name() const override { return "PendingIntentShadow"; }

    bool handles_class(const std::string& cls) const override {
        // Exact family claims only — the catch-all view path must never
        // see these descriptors (registration keeps them early).
        return cls == "Landroid/app/PendingIntent;" ||
               cls == "Landroid/app/AlarmManager;";
    }

    CallResult dispatch(const CallContext& ctx) override;

    // ── manifest-derived exact-alarm capability (AOSP API 31+ law) ──────
    // Set by execution_engine stage_load_apk from the RUNNING APK's
    // parsed manifest permission list. Generic derivation, no app names.
    void set_manifest_exact_alarm_capable(bool granted) {
        manifest_exact_alarm_capable_ = granted;
    }
    bool manifest_exact_alarm_capable() const {
        return manifest_exact_alarm_capable_;
    }

    // ── accessors for evidence / diagnostics ────────────────────────────
    struct Record {
        std::string kind;        // BROADCAST / ACTIVITY / SERVICE
        int32_t request_code = 0;
        uint32_t intent_oid = 0;
        int32_t flags = 0;
        uint32_t object_id = 0;  // heap identity of the PendingIntent
    };
    size_t live_records() const { return records_.size(); }
    const Record* record_by_oid(uint32_t oid) const {
        auto it = oid_index_.find(oid);
        return it == oid_index_.end() ? nullptr : it->second;
    }

private:
    // IntentSenderRecord cache: (kind|requestCode|intent-oid|flags) → record.
    std::map<std::string, Record> records_;
    // heap object id → record (identity lookups from cancel()).
    std::map<uint32_t, Record*> oid_index_;
    bool manifest_exact_alarm_capable_ = false;

    CallResult factory(const CallContext& ctx, const std::string& kind);
    CallResult record_for(Record rec);
};

}} // namespace miniandroid::framework

#endif // MINIANDROID_FRAMEWORK_PENDING_INTENT_SHADOW_H
