// view_ancestry.h — AOSP framework View-class ancestry law (FIX-G12-001).
//
// Law source: AOSP frameworks/base core/java/android/{view,widget}/*.java.
// The Android widget hierarchy is FIXED by the framework — every runtime
// that implements a framework subset must know the ancestry of the classes
// it implements, or superclass-based semantics (container classification,
// measure/layout behavior, dispatch) silently degrade:
//
//   G10 corpus evidence: app classes (CalculatorDisplay extends
//   LinearLayout) were classified through the app-DEX superclass chain, but
//   FRAMEWORK classes (TableLayout/TableRow extend LinearLayout,
//   ScrollView extends FrameLayout, ...) had NO ancestry layer and fell
//   back to descriptor-substring tests — "Landroid/widget/TableRow;" does
//   not contain the substring "Layout", so TableRow was classified as a
//   LEAF and measured 0x0 while its children measured 44px (G11/G12
//   headingcalculator display-grid failure).
//
// This table is the single authority for FRAMEWORK ancestry; app-DEX
// classes resolve through their DEX superclass chain first and fall into
// this table when the chain exits app code (CustomView -> LinearLayout ->
// ViewGroup -> View).
//
// Multi-hop chains work: callers walk one hop at a time
// (TableRow -> LinearLayout -> ViewGroup -> View).
#ifndef MINIANDROID_VIEW_ANCESTRY_H
#define MINIANDROID_VIEW_ANCESTRY_H

#include <string>
#include <unordered_map>

namespace miniandroid {
namespace framework {

// Direct-superclass law for the framework classes this runtime implements.
// Values are DEX descriptors exactly as written in AOSP `extends` clauses.
inline const std::unordered_map<std::string, std::string>&
framework_direct_superclass() {
    static const std::unordered_map<std::string, std::string> kTable = {
        // view hierarchy root
        {"Landroid/view/View;", "Ljava/lang/Object;"},
        {"Landroid/view/ViewGroup;", "Landroid/view/View;"},
        // core containers (AOSP: X extends Y as written)
        {"Landroid/widget/FrameLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/LinearLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/RelativeLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/TableLayout;", "Landroid/widget/LinearLayout;"},
        {"Landroid/widget/TableRow;", "Landroid/widget/LinearLayout;"},
        {"Landroid/widget/GridLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/AbsoluteLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/ScrollView;", "Landroid/widget/FrameLayout;"},
        {"Landroid/widget/HorizontalScrollView;", "Landroid/widget/FrameLayout;"},
        {"Landroid/widget/ViewAnimator;", "Landroid/widget/FrameLayout;"},
        {"Landroid/widget/ViewSwitcher;", "Landroid/widget/ViewAnimator;"},
        {"Landroid/widget/ViewFlipper;", "Landroid/widget/ViewAnimator;"},
        // text hierarchy (AOSP: Button extends TextView — NOT View)
        {"Landroid/widget/TextView;", "Landroid/view/View;"},
        {"Landroid/widget/Button;", "Landroid/widget/TextView;"},
        {"Landroid/widget/EditText;", "Landroid/widget/TextView;"},
        {"Landroid/widget/CompoundButton;", "Landroid/widget/Button;"},
        {"Landroid/widget/CheckBox;", "Landroid/widget/CompoundButton;"},
        {"Landroid/widget/RadioButton;", "Landroid/widget/CompoundButton;"},
        {"Landroid/widget/ToggleButton;", "Landroid/widget/CompoundButton;"},
        // image hierarchy
        {"Landroid/widget/ImageView;", "Landroid/view/View;"},
        {"Landroid/widget/ImageButton;", "Landroid/widget/ImageView;"},
        // spinner/adapterview (minimal, law-correct)
        {"Landroid/widget/AdapterView;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/ListView;", "Landroid/widget/AdapterView;"},
        {"Landroid/widget/GridView;", "Landroid/widget/AbsListView;"},
        {"Landroid/widget/AbsListView;", "Landroid/widget/AdapterView;"},
        {"Landroid/widget/Spinner;", "Landroid/widget/AbsSpinner;"},
        {"Landroid/widget/AbsSpinner;", "Landroid/widget/AdapterView;"},
    };
    return kTable;
}

// Descriptor form law (FIX-G12-001b): DEX internals (class_to_superclass_
// maps, method dispatch) use SLASH form (Lfoo/bar/Baz;); the UI layer
// (AXML tags → ViewNode.class_desc) uses DOT form (Lfoo.bar.Baz;). Every
// cross-layer descriptor comparison must normalize first — G11's
// constructor hook normalized for the class-index, but the superclass
// classifier compared raw dot-form keys against slash-form map keys and
// every app container fell through to leaf classification.
inline std::string normalize_class_desc(const std::string& desc) {
    if (desc.size() < 3 || desc.front() != 'L' || desc.back() != ';')
        return desc;
    if (desc.find('.') == std::string::npos) return desc;
    std::string out = desc;
    for (size_t i = 1; i + 1 < out.size(); ++i)
        if (out[i] == '.') out[i] = '/';
    return out;
}

// One-hop lookup: the direct framework superclass of `class_desc`, or "".
inline std::string framework_superclass_of(const std::string& class_desc) {
    const auto& t = framework_direct_superclass();
    auto it = t.find(normalize_class_desc(class_desc));
    return it == t.end() ? std::string() : it->second;
}

// Walks the FRAMEWORK table (multi-hop, cycle-safe): true when class_desc
// is-a ancestor_desc through the AOSP hierarchy. App classes whose DEX
// chain is unknown here simply return false — the caller (DEX classifier
// or descriptor fallback) layers its own resolution around this.
inline bool framework_is_subclass(const std::string& class_desc,
                                  const std::string& ancestor_desc) {
    if (ancestor_desc.empty()) return false;
    std::string current = normalize_class_desc(class_desc);
    const std::string want = normalize_class_desc(ancestor_desc);
    for (int hops = 0; hops < 16 && !current.empty(); ++hops) {
        if (current == want) return true;
        if (current == "Ljava/lang/Object;") return false;
        current = framework_superclass_of(current);
    }
    return false;
}

}  // namespace framework
}  // namespace miniandroid

#endif  // MINIANDROID_VIEW_ANCESTRY_H
