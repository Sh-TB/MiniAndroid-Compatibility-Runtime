// state_list.h — G06 §5 StateListDrawable law (AOSP android-14.0.0_r2).
//
// Drawable.java/StateListDrawable.java laws:
//  * StateListDrawable.getStateDrawableIndex(int stateSet): iterate items in
//    DOCUMENT ORDER; the FIRST item whose state spec is satisfied by the
//    view's current state wins (StateListDrawable L107+ / StateSet.
//    isStatefulMatching law: every declared state must match; undeclared
//    states are wildcards).
//  * android:state_pressed="true" requires pressed; "false" requires
//    !pressed; attribute absent → wildcard.
//  * drawableStateChanged → newDrawable/state re-pick happens on EVERY
//    state change, so the pick below is re-run per frame per node.
//
// Supported item value forms (what real APKs ship for button backgrounds):
//  * <item android:state_pressed="true" android:color="#RRGGBB[AA]"/>
//    (ColorStateList form)
//  * <item ...><shape ...><solid android:color="#..."/></shape></item>
//    (shape drawable form)
//  * <item ... android:drawable="@ref"/> → recorded as a drawable path via
//    the supplied resolver callback (no resolver → recorded, unresolved).

#ifndef MINIANDROID_FRAMEWORK_STATE_LIST_H
#define MINIANDROID_FRAMEWORK_STATE_LIST_H

#include "android_shadows.h"

#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace miniandroid {
namespace framework {

// Parse a compiled <selector> AXML into state items (document order).
// Returns false (and leaves *out untouched) if the XML is not a selector.
bool parse_state_list(const std::vector<uint8_t>& axml,
                      std::vector<ViewShadow::ViewNode::BgStateItem>* out);

// AOSP first-match law. Returns true when an item matched and fills the
// winner's color (when has_color) or drawable path.
bool pick_state_list(
    const std::vector<ViewShadow::ViewNode::BgStateItem>& items, bool pressed,
    bool enabled, bool selected, uint32_t* color_out, std::string* path_out);

}  // namespace framework
}  // namespace miniandroid

#endif  // MINIANDROID_FRAMEWORK_STATE_LIST_H
