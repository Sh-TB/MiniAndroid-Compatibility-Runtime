#!/usr/bin/env python3
# cont56_reapply.py — re-apply the four surviving CONT-56b engine changes
# (F-NEW-331 S83 fragment-attach state; F-NEW-332 Handler queue routing;
#  F-NEW-333 Preconditions identity; F-NEW-334 SparseArray) onto the clean
# origin/main lineage. Duplicate-of-parallel-wave changes (F-NEW-260 inner
# class law, F-021/F-NEW-313 inflater laws) are NOT re-applied.
import sys

P = "/home/z/my-project/miniandroid/src/dex/dalvik_engine.cpp"
s = open(P).read()
n0 = s

# ── 1. F-NEW-331: S83 onCreate shadow — fragment attach + mCurState ──────
A1 = """            // A/B: secuso dame/2048, mykanji, no.thanks blank→rendered.
            return_val = DalvikValue::make_void();"""
B1 = """            // A/B: secuso dame/2048, mykanji, no.thanks blank→rendered.
            //
            // F-NEW-331 (CONT-56b): the bypassed support onCreate is ALSO
            // where the fragment-host attach happens — AOSP
            // FragmentActivity.onCreate first instruction:
            //     mFragments.attachHost(null)
            //   → FragmentController.attachHost: mHost.mFragmentManager
            //     .attachController(mHost, mHost, parent)
            //   → FragmentManagerImpl.attachController: mHost = host;
            //     mContainer = container;
            // The semantic shadow skipped that write, so every app that
            // actually USES the support FragmentManager died at its first
            // transaction commit: enqueueAction found mHost == null →
            // ISE "Activity has been destroyed" → BMIMain.onCreate
            // [APP-BOUNDARY] → uniform dark frame (measured at the
            // CONT-56b baseline: bmi_402, alexcalc_20). Repair =
            // reproduce the OBSERVABLE attach state at the same framework
            // boundary (same sanctioned semantic-shadow tool class):
            // walk activity.mFragments → controller.mHost (HostCallbacks)
            // → hostCallbacks.mFragmentManager (FragmentManagerImpl) →
            // write mHost AND mContainer = the HostCallbacks object
            // (attachController law: attachController(mHost, mHost,
            // parent) sets both). Absent objects (apps that never touch
            // support fragments) → silent skip, no state invented.
            {
                uint32_t act331 = (args[0].type == DalvikType::OBJECT_REF)
                                      ? args[0].object_id
                                      : 0;
                if (act331 != 0 && heap_.has_object(act331)) {
                    auto fc331 = heap_.get_object_field(
                        act331,
                        "Landroid/support/v4/app/FragmentActivity;->"
                        "mFragments");
                    if (!fc331)
                        fc331 = heap_.get_object_field(
                            act331,
                            "Landroidx/fragment/app/"
                            "FragmentActivity;->mFragments");
                    if (fc331 && fc331->type == DalvikType::OBJECT_REF &&
                        fc331->object_id != 0 &&
                        heap_.has_object(fc331->object_id)) {
                        auto hc331 = heap_.get_object_field(
                            fc331->object_id,
                            "Landroid/support/v4/app/FragmentController;->"
                            "mHost");
                        if (!hc331)
                            hc331 = heap_.get_object_field(
                                fc331->object_id,
                                "Landroidx/fragment/app/"
                                "FragmentController;->mHost");
                        if (hc331 && hc331->type == DalvikType::OBJECT_REF &&
                            hc331->object_id != 0 &&
                            heap_.has_object(hc331->object_id)) {
                            uint32_t host_cb331 = hc331->object_id;
                            auto fm331 = heap_.get_object_field(
                                host_cb331,
                                "Landroid/support/v4/app/"
                                "FragmentHostCallback;->mFragmentManager");
                            if (!fm331)
                                fm331 = heap_.get_object_field(
                                    host_cb331,
                                    "Landroidx/fragment/app/"
                                    "FragmentHostCallback;->mFragmentManager");
                            if (!fm331)
                                fm331 = heap_.get_object_field(
                                    host_cb331,
                                    "Landroid/support/v4/app/"
                                    "HostCallbacks;->mFragmentManager");
                            if (fm331 &&
                                fm331->type == DalvikType::OBJECT_REF &&
                                fm331->object_id != 0 &&
                                heap_.has_object(fm331->object_id)) {
                                uint32_t fmi331 = fm331->object_id;
                                std::string fmi_cls =
                                    heap_.get(fmi331)
                                        ? heap_.get(fmi331)->class_descriptor
                                        : std::string();
                                if (fmi_cls.empty()) fmi_cls =
                                    "Landroid/support/v4/app/"
                                    "FragmentManagerImpl;";
                                DalvikValue cb_val331 =
                                    DalvikValue::make_object(
                                        host_cb331,
                                        "Landroid/support/v4/app/"
                                        "HostCallbacks;");
                                heap_.set_object_field(
                                    fmi331, fmi_cls + "->mHost",
                                    cb_val331);
                                heap_.set_object_field(
                                    fmi331, fmi_cls + "->mContainer",
                                    cb_val331);
                                // F-NEW-331b: the same bypassed onCreate
                                // tail is where the support host ADVANCES
                                // the fragment manager state:
                                // FragmentActivity.onCreate →
                                // mFragments.dispatchCreate() →
                                // FragmentManagerImpl.dispatchCreate() →
                                // dispatchStateChange(CREATED=1, false) →
                                // moveToState(mCurState=1). The Activity
                                // onStart face (F-NEW-172 shadow) then
                                // suppresses dispatchStart — so without a
                                // state reproduction the fragment ladder
                                // never reaches ACTIVITY_CREATED and
                                // performCreateView/onCreateView never runs
                                // (measured: transaction executed green but
                                // the fragment stayed INITIALIZING →
                                // container empty → dark frame). The
                                // honest observable: mCurState =
                                // ACTIVITY_CREATED (support-28 Fragment
                                // constants: INITIALIZING=0, CREATED=1,
                                // ACTIVITY_CREATED=2) — executeOps'
                                // moveToState(f, mCurState) then walks the
                                // full ladder incl. view creation.
                                // Remaining honest gap (recorded): the
                                // STARTED face (dispatchStart →
                                // performStart/performResume) is NOT
                                // reproduced — fragment.onStart/onResume
                                // overrides do not run.
                                heap_.set_object_field(
                                    fmi331, fmi_cls + "->mCurState",
                                    DalvikValue::make_int(2));
                                std::cerr << "[F-NEW-331] support fragment"
                                          << " attach state reproduced at"
                                          << " the S83 boundary: FM obj#"
                                          << fmi331
                                          << " mHost/mContainer = HostCb obj#"
                                          << host_cb331
                                          << ", mCurState=ACTIVITY_CREATED"
                                          << std::endl;
                            }
                        }
                    }
                }
            }
            return_val = DalvikValue::make_void();"""
assert s.count(A1) == 1, "S83 anchor not unique: %d" % s.count(A1)
s = s.replace(A1, B1)

# ── 2. F-NEW-333 + F-NEW-334: bridge top — Preconditions + SparseArray ──
A2 = """    uint64_t f107_t0 = 0; phase_clock().enter(phase_clock().bridge, f107_t0);
    struct F107Guard { PhaseClock::Phase& ph; uint64_t t0; ~F107Guard(){{ phase_clock().exit(ph, t0);}} } f107_guard{phase_clock().bridge, f107_t0};"""
with open("/home/z/my-project/scripts/cont56_bridge_block.inc") as f:
    B2_TAIL = f.read()
B2 = A2 + B2_TAIL
assert s.count(A2) == 1, "bridge anchor not unique: %d" % s.count(A2)
s = s.replace(A2, B2)

open(P, "w").write(s)
print("part 1+2 applied; delta bytes:", len(s) - len(n0))
