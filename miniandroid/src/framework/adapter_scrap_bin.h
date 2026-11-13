// adapter_scrap_bin.h — F-S231-A (#585 §5): the AbsListView RecycleBin
// scrap contract, ONE mechanics definition shared by the engine, the
// shadows and the law test (header-only; no build-graph change).
#ifndef MINIANDROID_ADAPTER_SCRAP_BIN_H
#define MINIANDROID_ADAPTER_SCRAP_BIN_H

#include <algorithm>
#include <functional>
#include <map>
#include <vector>

namespace miniandroid {
namespace framework {

// ── F-S231-A (#585 §5): AbsListView RecycleBin scrap contract ───────────
// AOSP ListView.java RecycleBin (@android-14, frameworks/base/widgets):
//   * obtainView → ScrapData[viewType].scrapViews pops a converted view
//     and hands it to Adapter.getView(position, convertView, parent) —
//     the adapter REBINDS a previously materialized row instead of
//     inflating a new one every pass.
//   * scrap is keyed by item-view type: Adapter.getItemViewType(position)
//     ∈ [0, getViewTypeCount()); AdapterView.ITEM_VIEW_TYPE_IGNORE (-1)
//     rows are never recycled (AOSP ignores the returned view).
//   * out-of-range types violate the Adapter contract (AOSP throws
//     IllegalStateException at bind); this runtime records the violation
//     count and binds as type 0 — bounded-lenient, never silent.
//   * active views of a relayout go back to scrap; beyond mScrapCapacity
//     (AOSP prunes to ViewTypeCount per type when the count is set) the
//     oldest scrap is dropped — counted, not silent.
// Header-only so the engine, the renderer and the law test share ONE
// mechanics definition (single source of truth; no build-graph change).
class AdapterScrapBin {
public:
    static constexpr size_t kScrapCapPerType = 16;
    static constexpr int kIgnoreType = -1;  // AdapterView.ITEM_VIEW_TYPE_IGNORE

    // Relayout law: the ListView's previous active rows return to scrap
    // (keyed by the item-view type recorded at bind time).
    void stash(uint32_t listview_oid, uint32_t row_oid, int type) {
        if (type < 0) return;  // IGNORE rows are never recycled (AOSP law)
        auto& v = bins_[listview_oid][type];
        if (v.size() >= kScrapCapPerType) {
            v.erase(v.begin());  // drop-oldest (AOSP mScrapCapacity prune)
            ++dropped_;
        }
        v.push_back(row_oid);
    }
    // obtainView law: a scrap view of the SAME type pops as convertView.
    bool pop(uint32_t listview_oid, int type, uint32_t& out) {
        if (type < 0) return false;
        auto bit = bins_.find(listview_oid);
        if (bit == bins_.end()) return false;
        auto it = bit->second.find(type);
        if (it == bit->second.end() || it->second.empty()) return false;
        out = it->second.back();
        it->second.pop_back();
        return true;
    }
    // Drop bins of ListViews whose ViewShadow node no longer exists
    // (heap objects survive detach; bins must not accumulate forever).
    void prune(const std::function<bool(uint32_t)>& alive) {
        for (auto it = bins_.begin(); it != bins_.end();) {
            if (!alive(it->first)) it = bins_.erase(it);
            else ++it;
        }
    }
    size_t pending(uint32_t listview_oid) const {
        auto it = bins_.find(listview_oid);
        if (it == bins_.end()) return 0;
        size_t n = 0;
        for (const auto& [t, v] : it->second) n += v.size();
        return n;
    }
    void forget(uint32_t listview_oid) { bins_.erase(listview_oid); }
    uint64_t dropped() const { return dropped_; }
    size_t bin_count() const { return bins_.size(); }

private:
    std::map<uint32_t, std::map<int, std::vector<uint32_t>>> bins_;
    uint64_t dropped_ = 0;  // views dropped beyond capacity (global counter)
};


}  // namespace framework
}  // namespace miniandroid

#endif  // MINIANDROID_ADAPTER_SCRAP_BIN_H
