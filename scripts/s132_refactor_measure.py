#!/usr/bin/env python3
"""s132_refactor_measure.py — R-NEW-440 canonical-measure refactor (S132).
Mechanically converts the measure_raw/measure lambdas inside
LayoutInflater::measure_layout into member functions:
  measure_node_raw (the law) / measure_node (the memo wrapper)
and adds measure_view_spec (the shared entry the engine's DEX measure
bridge delegates container subtrees to). Idempotent: exits 0 without
changes when the refactor is already applied.
"""
import re
import sys

P = "/home/z/my-project/miniandroid/src/resources/layout_inflater.cpp"
src = open(P).read()

if "LayoutInflater::measure_node_raw" in src:
    print("already refactored — no changes")
    sys.exit(0)

# ---------------------------------------------------------------- helpers
def cut(src, start_marker, end_marker, include_end=True, occ=1):
    """Cut the region [start_marker, end_marker] (inclusive) and return
    (new_src, cut_text)."""
    i = -1
    for _ in range(occ):
        i = src.index(start_marker, i + 1)
    j = src.index(end_marker, i)
    if include_end:
        j += len(end_marker)
    return src[:i] + src[j:], src[i:j]


# 1) delete the local enum/struct (types now live in the header)
src, _ = cut(
    src,
    "    enum Mode { M_UNSPEC = 0, M_EXACTLY, M_AT_MOST };\n"
    "    struct Spec { int size; Mode mode; };\n",
    "",
    include_end=False,
)

# 2) cut the three helper lambdas (child_spec/resolve_final/is_container_node)
src, helpers = cut(
    src,
    "    auto child_spec = [](const Spec& p, int padding, int child_dim) -> Spec {",
    "               cd.find(\"RecyclerView\") != std::string::npos;\n    };\n",
)

# 3) cut the measure_raw body: from the orphaned G12 diagnostic down to the
#    raw-lambda terminator "return {n->measured_width, n->measured_height};\n    };"
src, body = cut(
    src,
    "        // G12 diagnostic (opt-in): incoming specs + container classification — level 3.",
    "        return {n->measured_width, n->measured_height};\n    };\n",
)

# 4) cut the memo-wrapper lambda
src, wrapper = cut(
    src,
    "    // M3 §7 memo wrapper: every measure(…) call (root + all recursive",
    "        m3_measure_memo.emplace(k, r);\n        return r;\n    };\n",
)

# 5) fix call sites inside the cut body/wrapper + the remaining function
def fix_calls(text):
    # recursive measure( … ) calls → measure_node(views, … )
    text = re.sub(r"\bmeasure\((kids\[i\]|root_id|vid)\b", r"measure_node(views, \1", text)
    return text

body_fixed = fix_calls(body)

# the root call and the two layout-phase weight re-measures
src = src.replace(
    "        root_size_first = measure(root_id, {rws, rwm}, {rhs, rhm}, 0);",
    "        root_size_first = measure_node(views, root_id, {rws, rwm}, {rhs, rhm}, 0);",
)
src = src.replace(
    "                        measure(kids[i], {std::max(0, final_w[i]), M_EXACTLY}, rsh, 0);",
    "                        measure_node(views, kids[i], {std::max(0, final_w[i]), M_EXACTLY}, rsh, 0);",
)
src = src.replace(
    "                        measure(kids[i], rsw, {std::max(0, final_h[i]), M_EXACTLY}, 0);",
    "                        measure_node(views, kids[i], rsw, {std::max(0, final_h[i]), M_EXACTLY}, 0);",
)

# 6) drop the now-duplicated root_size_first decl (it moved with the cut?
#    No — the decl stayed; verify we did not cut it)
assert "std::pair<int,int> root_size_first;" in src, "root decl must remain"

# 7) build the member functions and insert them before measure_layout
members = '''
// ───────────────────────────────────────────────────────────────────────────
// R-NEW-440 (S132): ONE CANONICAL MEASURE LAW — member functions.
// The former measure_layout lambda, promoted so the engine's DEX measure
// bridge (real container onMeasure → child.measure) can delegate container
// subtrees to the SAME law the render walk uses. AOSP ground truth:
// View.measure dispatches the node's own law — ViewGroup containers run
// their child negotiation INSIDE it; the runtime models those laws once.
// ───────────────────────────────────────────────────────────────────────────
std::pair<int, int> LayoutInflater::measure_node(
    framework::ViewShadow* views, uint32_t vid, const MeasureSpec2& sw,
    const MeasureSpec2& sh, int depth) {
    // M3 §7 convergence memo: identical (view, specs) inside one pass are
    // computed exactly ONCE and replayed byte-identically thereafter
    // (convergence law + DEX-hook single-execution law + complexity bound
    // for the match-parent second pass). The memo is a MEMBER so nested
    // measure_view_spec entries (DEX measure bridge during this pass)
    // dedupe against the same table (purity + termination).
    M3MemoKey k{vid, sw.size, (int)sw.mode, sh.size, (int)sh.mode};
    auto it = m3_measure_memo_.find(k);
    if (it != m3_measure_memo_.end()) return it->second;
    auto r = measure_node_raw(views, vid, sw, sh, depth);
    m3_measure_memo_.emplace(k, r);
    return r;
}

bool LayoutInflater::measure_view_spec(framework::ViewShadow* views,
                                       uint32_t vid, int wspec_word,
                                       int hspec_word, int& out_w,
                                       int& out_h) {
    auto* n = views ? views->find_node(vid) : nullptr;
    if (!n) return false;
    // R-NEW-302 companion: a dirty layout invalidates remembered (view,
    // spec) results — the memo must not replay stale geometry.
    if (views->layout_dirty) m3_measure_memo_.clear();
    auto decode = [](int w) -> MeasureSpec2 {
        return MeasureSpec2{w & 0x3FFFFFFF,
                            (MeasureMode)(((uint32_t)w) >> 30)};
    };
    measure_node(views, vid, decode(wspec_word), decode(hspec_word), 0);
    out_w = n->measured_width;
    out_h = n->measured_height;
    return true;
}

std::pair<int, int> LayoutInflater::measure_node_raw(
    framework::ViewShadow* views, uint32_t vid, const MeasureSpec2& sw,
    const MeasureSpec2& sh, int depth) {
    using Spec = MeasureSpec2;
    const MeasureMode M_UNSPEC = MS_UNSPEC, M_EXACTLY = MS_EXACTLY,
                      M_AT_MOST = MS_AT_MOST;
    auto& m3_measure_memo = m3_measure_memo_;
    auto* n = views->find_node(vid);
    if (!n) return {0, 0};
'''

tail = '''
    return {n->measured_width, n->measured_height};
}
'''

members += helpers + body_fixed.rstrip() + "\n" + tail

anchor = "void LayoutInflater::measure_layout(framework::ViewShadow* views, uint32_t root_id) {"
src = src.replace(anchor, members + "\n" + anchor, 1)

open(P, "w").write(src)
print("refactor applied: measure_node_raw/measure_node/measure_view_spec extracted")
