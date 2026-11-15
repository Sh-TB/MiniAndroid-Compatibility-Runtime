#!/usr/bin/env python3
"""F-LISTACTIVITY-GV (Wave-5, #588): ListActivity.getListView arm.

The setListAdapter drain (F-LISTACTIVITY) existed; the getListView half
was missing — K-9 Accounts.onCreate calls getListView() on its
ListActivity and the bridge had no arm (the Wave-5 F-NEW-634 pair:
getListView/setListAdapter). Law: AOSP ListActivity resolves the managed
ListView through findViewById(android.R.id.list) and caches it in mList;
getListView() returns that handle. The inflated ListView node carries
android_view_id == android.R.id.list (0x0102000A per the shadow law), so
the arm resolves it from the ViewShadow tree (rooted BFS + the
R-NEW-441b full-node fallback) and returns the view object; no list yet
→ the honest null (mList unset).
"""
from pathlib import Path

P = Path("/tmp/w238_int/miniandroid/src/dex/dalvik_engine.cpp")
s = P.read_text()

old = """            if (method == "setListAdapter" && shadow_registry_ != nullptr) {"""
new = """            // ── F-LISTACTIVITY-GV (Wave-5, #588): ListActivity.
            // getListView — the other half of the F-NEW-634 pair. AOSP
            // ListActivity.getListView() returns mList, the managed
            // ListView resolved through findViewById(android.R.id.list);
            // the inflated node carries android_view_id ==
            // android.R.id.list (0x0102000A, the shadow's law), so the
            // arm resolves it from the ViewShadow tree (the same walk
            // the setListAdapter drain reads) and returns the view
            // object. No list materialized yet → the honest null.
            if (method == "getListView" && shadow_registry_ != nullptr) {
                uint32_t gv_id = 0;
                if (auto* act = shadow_registry_->find_as<
                        framework::ActivityShadow>()) {
                    gv_id = act->list_activity_list_id();
                    if (gv_id == 0 && args.size() >= 1) {
                        if (auto* vs = shadow_registry_->find_as<
                                framework::ViewShadow>()) {
                            // rooted-BFS misses → the R-NEW-441b full-node
                            // scan covers the appcompat delegate roots.
                            gv_id = vs->find_by_android_id(0, 0x0102000A);
                        }
                    }
                }
                status = ApiCallTrace::Status::IMPLEMENTED;
                if (gv_id != 0) {
                    DalvikValue r;
                    r.type = DalvikType::OBJECT_REF;
                    r.object_id = gv_id;
                    r.class_desc = "Landroid/widget/ListView;";
                    result = r;
                } else {
                    result = DalvikValue::make_null();
                }
                return true;
            }
            if (method == "setListAdapter" && shadow_registry_ != nullptr) {"""
assert old in s, "setListAdapter anchor"
P.write_text(s.replace(old, new, 1))
print("F-LISTACTIVITY-GV ported (getListView arm)")
