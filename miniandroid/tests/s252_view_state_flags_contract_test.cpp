// s252_view_state_flags_contract_test — W20-K (S237-WS9, independent coder
// cODER-ohc): AOSP View state-flag family law (@android-14 View.java
// setFlags + refreshDrawableState):
//   setSelected/setPressed/setActivated/setLongClickable/setHovered STORE
//   the flag; the is* getters read it (all five previously silent no-ops);
//   the stored flags reach pick_state_list first-match (state_selected /
//   state_activated / state_window_focused enforce exactly, wildcard only
//   when undeclared).
#include "../src/framework/android_shadows.h"
#include "../src/framework/state_list.h"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::framework::CallContext;
using miniandroid::framework::CallResult;
using miniandroid::framework::ViewShadow;

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) ++g_pass; else ++g_fail;
}

static CallResult drive(ViewShadow& vs, uint32_t recv, const std::string& m,
                        bool arg) {
    CallContext c;
    c.has_receiver = true;
    c.receiver_id = recv;
    c.receiver_class = "Landroid/widget/Button;";
    c.class_name = c.receiver_class;
    c.method = m;
    CallContext::Arg a;
    a.kind = CallContext::Arg::Kind::BOOL;
    a.bool_val = arg;
    c.args.push_back(a);
    return vs.dispatch(c);
}

int main() {
    std::cout << "== s252_view_state_flags_contract ==\n";
    ViewShadow vs;
    uint32_t v = 30001;

    // round-trips through the REAL dispatch the DEX call reaches
    drive(vs, v, "setSelected", true);
    auto sel = drive(vs, v, "isSelected", false);
    record("ws9_selected_roundtrip",
           sel.handled && sel.ret_kind == CallResult::RetKind::BOOL &&
               sel.bool_val,
           "setSelected(true) → isSelected()==true (was handled=0)");
    auto clear = drive(vs, v, "setSelected", false);
    auto sel2 = drive(vs, v, "isSelected", false);
    record("ws9_clear_selected",
           clear.handled && sel2.handled && !sel2.bool_val,
           "setSelected(false) clears");

    drive(vs, v, "setPressed", true);
    auto prs = drive(vs, v, "isPressed", false);
    record("ws9_pressed_roundtrip",
           prs.handled && prs.bool_val, "setPressed → isPressed true");

    drive(vs, v, "setActivated", true);
    auto act = drive(vs, v, "isActivated", false);
    record("ws9_activated_roundtrip",
           act.handled && act.bool_val, "setActivated → isActivated true");

    drive(vs, v, "setHovered", true);
    auto hov = drive(vs, v, "isHovered", false);
    record("ws9_hovered_roundtrip",
           hov.handled && hov.bool_val, "setHovered → isHovered true");

    drive(vs, v, "setLongClickable", true);
    auto lc = drive(vs, v, "isLongClickable", false);
    record("ws9_long_clickable_roundtrip",
           lc.handled && lc.bool_val, "setLongClickable → isLongClickable");

    // ── the stored flags reach pick_state_list first-match ──
    // items: [0] requires state_selected="true" color 0xFF112233
    //        [1] wildcard color 0xFF445566
    std::vector<ViewShadow::ViewNode::BgStateItem> items(2);
    items[0].state_selected = 1;
    items[0].has_color = true;
    items[0].color = 0xFF112233u;
    items[1].has_color = true;
    items[1].color = 0xFF445566u;

    uint32_t c_out = 0;
    std::string p_out;
    const ViewShadow::ViewNode::BgStateItem* win = nullptr;
    bool unselected_hits_wildcard =
        miniandroid::framework::pick_state_list(items, false, true, false,
                                                &c_out, &p_out, false, false,
                                                false, false, true, &win) &&
        c_out == 0xFF445566u;
    record("ws9_unselected_wildcard_wins", unselected_hits_wildcard,
           "not selected → wildcard 0xFF445566 (state_selected skipped)");

    bool selected_hits_first =
        miniandroid::framework::pick_state_list(items, false, true, true,
                                                &c_out, &p_out, false, false,
                                                false, false, true, &win) &&
        c_out == 0xFF112233u;
    record("ws9_selected_drives_state_list", selected_hits_first,
           "selected → first-match 0xFF112233 (node flag → render state)");

    // state_activated enforcement (was: declared item matched as wildcard)
    std::vector<ViewShadow::ViewNode::BgStateItem> items2(2);
    items2[0].state_activated = 1;
    items2[0].has_color = true;
    items2[0].color = 0xFFAA0000u;
    items2[1].has_color = true;
    items2[1].color = 0xFF00AA00u;
    bool inactive_wildcard =
        miniandroid::framework::pick_state_list(items2, false, true, false,
                                                &c_out, &p_out, false, false,
                                                false, false, true, &win) &&
        c_out == 0xFF00AA00u;
    bool active_first =
        miniandroid::framework::pick_state_list(items2, false, true, false,
                                                &c_out, &p_out, false, false,
                                                false, true, true, &win) &&
        c_out == 0xFFAA0000u;
    record("ws9_activated_state_matches", inactive_wildcard && active_first,
           "state_activated=enforced: inactive→0xFF00AA00, active→0xFFAA0000");

    // window_focused default TRUE (the plain default view state)
    std::vector<ViewShadow::ViewNode::BgStateItem> items3(1);
    items3[0].state_window_focused = 1;
    items3[0].has_color = true;
    items3[0].color = 0xFF0000FFu;
    bool wf_default =
        miniandroid::framework::pick_state_list(items3, false, true, false,
                                                &c_out, &p_out, false, false,
                                                false, false, true, &win) &&
        c_out == 0xFF0000FFu;
    record("ws9_window_focused_default_true", wf_default,
           "window_focused default true → state_window_focused item matches");

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
