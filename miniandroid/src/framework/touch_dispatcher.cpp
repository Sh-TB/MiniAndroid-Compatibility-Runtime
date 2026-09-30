// touch_dispatcher.cpp — G06 canonical input pipeline implementation.
// Every branch cites its AOSP law anchor (see touch_dispatcher.h header).

#include "touch_dispatcher.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <functional>
#include <iostream>

namespace miniandroid {
namespace framework {

namespace {
bool node_at(const ViewShadow::ViewNode* n, int x, int y) {
    if (!n) return false;
    return x >= n->x && x < n->x + std::max(1, n->width) && y >= n->y &&
           y < n->y + std::max(1, n->height);
}
constexpr uint32_t kTokenCheckLongPress = HandlerShadow::kFrameworkTokenBase + 1;
constexpr uint32_t kTokenPerformClick   = HandlerShadow::kFrameworkTokenBase + 2;
constexpr uint32_t kTokenUnsetPressed   = HandlerShadow::kFrameworkTokenBase + 3;
}  // namespace

const char* touch_action_name(TouchAction a) {
    switch (a) {
        case TouchAction::DOWN: return "ACTION_DOWN";
        case TouchAction::MOVE: return "ACTION_MOVE";
        case TouchAction::UP: return "ACTION_UP";
        case TouchAction::CANCEL: return "ACTION_CANCEL";
    }
    return "?";
}

// S128 (R-NEW-424, CAP-INPUT-100): run onInterceptTouchEvent along the
// TouchTarget chain — AOSP ViewGroup.dispatchTouchEvent asks EVERY ViewGroup
// in the chain, root-most FIRST (the outermost container decides before its
// descendants). Returns the intercepting view id (0 = nobody intercepted).
// requestDisallowInterceptTouchEvent is a documented boundary (no child-set
// disallow flag API in this runtime yet — recorded in the master worklist).
uint32_t TouchDispatcher::run_intercept_chain(int action, int x, int y,
                                              nlohmann::json* rec) {
    if (!intercept_fn_ || gesture_chain_.size() < 2) return 0;
    for (auto it = gesture_chain_.rbegin(); it != gesture_chain_.rend(); ++it) {
        const auto* n = views_->find_node(*it);
        if (!n || !n->overrides_intercept_touch_event) continue;
        bool intercepted = false;
        const bool dispatched =
            intercept_fn_(*it, action, float(x), float(y), intercepted);
        if (rec) {
            nlohmann::json ask;
            ask["view_id"] = *it;
            ask["dispatched"] = dispatched;
            ask["intercepted"] = intercepted;
            (*rec)["intercept_asked"].push_back(ask);
        }
        if (dispatched && intercepted) return *it;
    }
    return 0;
}

TouchDispatcher::TouchDispatcher(ViewShadow* views, HandlerShadow* handler,
                                 const Config& cfg)
    : views_(views), handler_(handler), cfg_(cfg) {}

// View.java L17044-17047 — touchable = CLICKABLE || LONG_CLICKABLE. The
// explicit `clickable` flag, an android:onClick handler, a registered
// OnClickListener, or a LongClickListener each set the respective AOSP flag
// (setOnLongClickListener → setLongClickable, View.java L5930+).
bool TouchDispatcher::view_touchable(const ViewShadow::ViewNode& n) const {
    // S113 law (AOSP WebView.onTouchEvent): a WebView IS a touch target —
    // the browser event pipeline consumes touches inside its bounds.
    if (n.class_desc.find("Landroid/webkit/WebView;") != std::string::npos)
        return true;
    // S122 (R-NEW-417): a DEX-defined view whose class chain OVERRIDES
    // onTouchEvent is a touch target — AOSP View.dispatchTouchEvent walks
    // to the deepest view under the point and runs ITS onTouchEvent; no
    // listener registration is required (klondike GameView board evidence:
    // the custom board view had no listener, so the touchable gate answered
    // false and every board tap resolved target=0).
    if (n.overrides_touch_event) return true;
    // F-110e (S62+): a view with an OnTouchListener IS a touch target.
    // AOSP View.dispatchTouchEvent (View.java L16741+): the mOnTouchListener
    // gate runs BEFORE clickability matters — `li.mOnTouchListener != null &&
    // mViewFlags ENABLED && li.mOnTouchListener.onTouch(this, event)` — so a
    // plain (non-clickable) view that called setOnTouchListener receives
    // DOWN. First real hit: anuto GameView (game board) is tap-dead without
    // this arm (target=0 at its own screen coords).
    return n.clickable || n.long_clickable || !n.onClick_handler.empty() ||
           n.click_listener_id != 0 || !n.click_listener_class.empty() ||
           n.long_click_listener_id != 0 || n.touch_listener_id != 0;
}

uint32_t TouchDispatcher::schedule(TokenState& slot, const char* label,
                                   int64_t delay_ms) {
    unschedule(slot);  // AOSP re-posts a single callback object per view slot.
    if (!handler_) return 0;
    uint32_t token = 0;
    if (std::string(label) == "CheckForLongPress") token = kTokenCheckLongPress;
    else if (std::string(label) == "PerformClick") token = kTokenPerformClick;
    else token = kTokenUnsetPressed;
    slot.id = token;
    slot.label = label;
    handler_->enqueue_framework(slot.id, delay_ms,
                                std::string("framework:") + label);
    return slot.id;
}

void TouchDispatcher::unschedule(TokenState& slot) {
    if (slot.id != 0 && handler_) handler_->remove_callbacks(slot.id);
    slot.id = 0;
}

void TouchDispatcher::reset_gesture() {
    unschedule(tok_check_long_press_);
    unschedule(tok_perform_click_);
    unschedule(tok_unset_pressed_);
    gesture_target_ = 0;
    gesture_chain_.clear();
    pressed_ = false;
    has_performed_long_press_ = false;
    touch_listener_owns_ = false;  // F-110e
}

void TouchDispatcher::press(uint32_t view_id, int x, int y,
                            nlohmann::json* rec) {
    if (auto* n = views_->find_node(view_id)) {
        if (!n->pressed) {
            n->pressed = true;
            // View.setPressed → drawableStateChanged → the state-list
            // background re-resolves against the new state on the next draw
            // (G06 §5: input → state → render).
            if (rec) (*rec)["state_changes"].push_back("setPressed(true)");
        }
    }
    (void)x; (void)y;
}

void TouchDispatcher::unpress(uint32_t view_id, nlohmann::json* rec) {
    if (auto* n = views_->find_node(view_id)) {
        if (n->pressed) {
            n->pressed = false;
            if (rec) (*rec)["state_changes"].push_back("setPressed(false)");
        }
    }
}

nlohmann::json TouchDispatcher::dispatch(uint32_t root_id,
                                         const TouchEvent& ev) {
    nlohmann::json rec;
    rec["action"] = touch_action_name(ev.action);
    rec["x"] = ev.x;
    rec["y"] = ev.y;
    rec["virtual_ms"] = handler_ ? handler_->virtual_now_ms() : 0;
    rec["state_changes"] = nlohmann::json::array();
    rec["root_id"] = root_id;

    switch (ev.action) {
        case TouchAction::DOWN: {
            // A fresh DOWN starts a new gesture (a stray DOWN without a
            // preceding UP/CANCEL is hostile — reset defensively so no
            // stale callbacks of the old gesture leak into the new one).
            reset_gesture();
            down_x_ = ev.x;
            down_y_ = ev.y;

            // Touch-target law: deepest VISIBLE view under the point that is
            // CLICKABLE/LONG_CLICKABLE. Target selection ignores `enabled`
            // (ViewGroup.getTouchTarget → canViewReceivePointerEvents checks
            // visibility only); the response gating is the disabled law.
            // ────────────────────────────────────────────────────────────
            // R-NEW-399 (S79) — AOSP ViewGroup child-dispatch law: children
            // are bounds-checked INDEPENDENTLY of their ancestors. In AOSP,
            // ViewGroup.dispatchTouchEvent iterates the child list and asks
            // isTransformedTouchPointInView(x, y, child) PER CHILD; the
            // parent's own bounds never gate the descent. The previous walk
            // returned (pruned the subtree) whenever an ANCESTOR's node
            // geometry did not contain the point — so any stale/unmeasured
            // ancestor (e.g. a custom-view root inflated as -1x-1, or an
            // inflated-but-shadow-unmeasured RelativeLayout chain) made
            // every descendant tap-dead (target=0) even though the render
            // layout placed the children correctly on screen. Evidence:
            // fishrings board taps at (540,960)/(270,960)/(810,960) →
            // target=0 while the board paints (run/s79_reproofs/fishrings_s10).
            // MINIANDROID_HITPROBE=1 logs every walked node (render-neutral,
            // stderr-only probe) to keep the producer trace inspectable.
            // ────────────────────────────────────────────────────────────
            // S128 (R-NEW-424, CAP-INPUT-102 TouchTarget law): children are
            // iterated in REVERSE draw order (AOSP ViewGroup.dispatchTouchEvent
            // walks `for (int i = childrenCount - 1; i >= 0; i--)`): the
            // TOPMOST-drawn sibling at the point wins — first-in-order used to
            // win overlaps, which hands the gesture to a view painted UNDER
            // its later sibling (z-order inversion).
            uint32_t target = 0;
            const bool hitprobe = getenv("MINIANDROID_HITPROBE") != nullptr;
            std::function<void(uint32_t, int)> walk = [&](uint32_t id,
                                                          int depth) {
                const auto* n = views_->find_node(id);
                if (!n || n->visibility != 0) return;
                const bool at = node_at(n, ev.x, ev.y);
                if (hitprobe)
                    std::cerr << "[HITPROBE] d=" << depth << " id=" << id
                              << " " << n->class_desc << " (" << n->x << ","
                              << n->y << " " << n->width << "x" << n->height
                              << ") at=" << at << " touchable="
                              << view_touchable(*n) << " kids="
                              << n->children.size() << std::endl;
                if (at && view_touchable(*n)) target = id;  // deepest wins
                for (auto cit = n->children.rbegin();
                     cit != n->children.rend(); ++cit)
                    walk(*cit, depth + 1);
            };
            walk(root_id, 0);
            gesture_target_ = target;
            // S128 (CAP-INPUT-102): capture the TouchTarget chain — the
            // target plus every ancestor up to the dispatch root. AOSP: each
            // ViewGroup in the chain holds its own mFirstTouchTarget; MOVE/UP
            // dispatch through the chain (and the intercept pass runs along
            // it) instead of re-hit-testing.
            gesture_chain_.clear();
            for (uint32_t cur = target; cur != 0;) {
                gesture_chain_.push_back(cur);
                const auto* cn = views_->find_node(cur);
                if (!cn || cn->parent_id == 0 || cn->view_id == root_id) break;
                cur = cn->parent_id;
            }
            rec["target_view_id"] = target;
            rec["touch_target_chain"] = gesture_chain_;
            if (const auto* tn = views_->find_node(target))
                rec["target_class"] = tn->class_desc;
            if (target == 0) {
                rec["consumed"] = false;
                rec["law"] = "no touch target — dispatchTouchEvent returns "
                             "false, no listener dispatch";
                break;
            }
            // S128 (CAP-INPUT-100): intercept pass at DOWN. AOSP
            // ViewGroup.dispatchTouchEvent asks onInterceptTouchEvent(DOWN)
            // on the ViewGroups of the chain (root-most first) BEFORE the
            // child is handed the event; a true return retargets the gesture
            // to the intercepting ViewGroup itself (its own onTouchEvent
            // processing follows — pressed/long-press arms below if it is
            // touchable).
            if (const uint32_t interceptor =
                    run_intercept_chain(0 /*ACTION_DOWN*/, ev.x, ev.y, &rec)) {
                gesture_target_ = interceptor;
                gesture_chain_.clear();
                for (uint32_t cur = interceptor; cur != 0;) {
                    gesture_chain_.push_back(cur);
                    const auto* cn = views_->find_node(cur);
                    if (!cn || cn->parent_id == 0 || cn->view_id == root_id)
                        break;
                    cur = cn->parent_id;
                }
                rec["intercepted_at_down"] = true;
                rec["intercept_view_id"] = interceptor;
                rec["target_view_id"] = interceptor;
                rec["touch_target_chain"] = gesture_chain_;
                target = interceptor;
                const auto* tn2 = views_->find_node(target);
                if (tn2) rec["target_class"] = tn2->class_desc;
            }
            const auto* n = views_->find_node(target);
            const bool touchable = view_touchable(*n);

            if (!n->enabled) {
                // DISABLED law (View.java L17049-17057): a disabled touchable
                // view CONSUMES the sequence but does not respond — no press,
                // no long-press scheduling.
                rec["consumed"] = touchable;
                rec["disabled_law"] = true;
                rec["law"] = "View.java L17049-17057: disabled view consumes "
                             "without response";
                break;
            }

            // F-110e (S62+): OnTouchListener DOWN arm. AOSP
            // View.dispatchTouchEvent (View.java L16741-16760): if the
            // listener exists and ENABLED, onTouch(DOWN) runs FIRST; when it
            // returns true the result is consumed and the internal
            // touch-event processing (pressed feedback, long-press arming,
            // PerformClick) is skipped entirely.
            // F-110e (S62+) + S122 (R-NEW-417): OnTouchListener DOWN arm,
            // extended to the view's OWN onTouchEvent override — AOSP
            // View.dispatchTouchEvent: no listener OR listener returning
            // false falls into onTouchEvent(ACTION_DOWN); a custom board
            // view (klondike GameView) handles the gesture there.
            if ((n->touch_listener_id != 0 || n->overrides_touch_event) &&
                touch_fn_) {
                bool consumed_by_listener = false;
                const bool dispatched =
                    touch_fn_(target, 0 /*ACTION_DOWN*/, ev.x, ev.y,
                              consumed_by_listener);
                rec["touch_dispatched"] = dispatched;
                rec["touch_listener_consumed"] = consumed_by_listener;
                if (dispatched && consumed_by_listener) {
                    touch_listener_owns_ = true;
                    rec["consumed"] = true;
                    break;
                }
            }
            // Enabled + touchable: DOWN shows pressed feedback immediately
            // (non-scrolling-container law, View.java L17119-17125) and arms
            // the 500ms long-press check (checkForLongClick).
            press(target, ev.x, ev.y, &rec);
            has_performed_long_press_ = false;
            schedule(tok_check_long_press_, "CheckForLongPress",
                     cfg_.long_press_timeout_ms);
            rec["consumed"] = true;
            rec["long_press_armed_ms"] = cfg_.long_press_timeout_ms;
            break;
        }

        case TouchAction::MOVE: {
            if (gesture_target_ == 0) {
                rec["consumed"] = false;
                break;
            }
            // S128 (CAP-INPUT-100): mid-gesture interception. AOSP
            // ViewGroup.dispatchTouchEvent runs onInterceptTouchEvent(MOVE)
            // along the chain BEFORE handing MOVE to the captured target; a
            // true return sends ACTION_CANCEL to the child and the ViewGroup
            // owns the gesture from that point (scrolling containers law).
            if (const uint32_t interceptor =
                    run_intercept_chain(1 /*ACTION_MOVE*/, ev.x, ev.y, &rec)) {
                if (touch_listener_owns_ && touch_fn_) {
                    bool consumed_by_listener = false;
                    touch_fn_(gesture_target_, 3 /*ACTION_CANCEL*/, ev.x,
                              ev.y, consumed_by_listener);
                    rec["cancel_dispatched_to_listener"] = true;
                }
                unpress(gesture_target_, &rec);
                unschedule(tok_check_long_press_);
                rec["intercepted_mid_gesture"] = true;
                rec["intercept_view_id"] = interceptor;
                rec["cancel_sent_to"] = gesture_target_;
                gesture_target_ = interceptor;
                gesture_chain_.clear();
                for (uint32_t cur = interceptor; cur != 0;) {
                    gesture_chain_.push_back(cur);
                    const auto* cn = views_->find_node(cur);
                    if (!cn || cn->parent_id == 0 || cn->view_id == root_id)
                        break;
                    cur = cn->parent_id;
                }
                rec["touch_target_chain"] = gesture_chain_;
                touch_listener_owns_ = false;
                const auto* in = views_->find_node(interceptor);
                if (in && in->enabled && view_touchable(*in)) {
                    press(interceptor, ev.x, ev.y, &rec);
                    has_performed_long_press_ = false;
                    schedule(tok_check_long_press_, "CheckForLongPress",
                             cfg_.long_press_timeout_ms);
                }
                rec["consumed"] = true;
                rec["law"] = "ViewGroup.dispatchTouchEvent: mid-gesture "
                             "interception CANCELs the child target and "
                             "retargets the ViewGroup";
                break;
            }
            const auto* n = views_->find_node(gesture_target_);
            const bool touchable = n ? view_touchable(*n) : false;
            if (!n || !n->enabled || !touchable) {
                rec["consumed"] = touchable;
                break;
            }
            // Lenient move law (View.java L17198-17208): leaving the button
            // bounds beyond touch slop removes the tap + long-press callbacks
            // and clears pressed (AOSP pointInView + mTouchSlop margin).
            const int slop = cfg_.touch_slop_px;
            const bool inside =
                ev.x >= n->x - slop && ev.x < n->x + std::max(1, n->width) + slop &&
                ev.y >= n->y - slop && ev.y < n->y + std::max(1, n->height) + slop;
            if (!inside) {
                unschedule(tok_check_long_press_);
                unpress(gesture_target_, &rec);
                rec["moved_outside"] = true;
                rec["law"] = "View.java L17198-17208: MOVE outside touch slop "
                             "cancels press + long-press";
            }
            rec["consumed"] = true;
            break;
        }

        case TouchAction::UP: {
            if (gesture_target_ == 0) {
                rec["consumed"] = false;
                break;
            }
            auto* n = views_->find_node(gesture_target_);
            const bool touchable = n ? view_touchable(*n) : false;
            rec["target_view_id"] = gesture_target_;
            if (!n || !touchable) {
                rec["consumed"] = false;
                reset_gesture();
                break;
            }
            if (!n->enabled) {
                // DISABLED law: UP consumes, clears any pressed state,
                // never clicks (View.java L17051-17054).
                unpress(gesture_target_, &rec);
                rec["consumed"] = touchable;
                rec["disabled_law"] = true;
                reset_gesture();
                break;
            }
            // F-110e (S62+): OnTouchListener UP arm — when the listener
            // consumed the DOWN it owns the whole gesture (AOSP law: no
            // internal handling → no PerformClick post).
            if (touch_listener_owns_ && touch_fn_) {
                bool consumed_by_listener = false;
                const bool dispatched =
                    touch_fn_(gesture_target_, 1 /*ACTION_UP*/, ev.x, ev.y,
                              consumed_by_listener);
                rec["touch_dispatched"] = dispatched;
                rec["touch_listener_consumed"] = consumed_by_listener;
                rec["consumed"] = dispatched;
                reset_gesture();
                break;
            }
            const bool was_pressed = n->pressed;
            rec["was_pressed"] = was_pressed;
            if (was_pressed) {
                // View.java L17152-17154: removeLongPressCallback.
                unschedule(tok_check_long_press_);
                // View.java L17140-17143: focus is taken FIRST; focusTaken
                // suppresses the PerformClick post (that is the law by which
                // a focusable-in-touch-mode view (EditText) takes focus on
                // tap without firing onClick).
                bool focus_taken = false;
                if (n->focusable && n->focusable_in_touch_mode && !n->focused) {
                    n->focused = true;
                    focus_taken = true;
                    rec["state_changes"].push_back("requestFocus(true)");
                }
                if (!focus_taken && !has_performed_long_press_) {
                    // View.java L17163-17168: post(PerformClick) — the click
                    // runs on the ONE main queue AFTER pending state updates.
                    schedule(tok_perform_click_, "PerformClick", 0);
                    rec["click_posted"] = true;
                }
                // View.java L17174-17179: UnsetPressedState is posted on
                // every pressed-UP (long-press or not) at
                // PRESSED_STATE_DURATION — pressed clears from the queue.
                schedule(tok_unset_pressed_, "UnsetPressedState",
                         cfg_.pressed_state_duration_ms);
            }
            // A consumed long press suppresses the UP click
            // (mHasPerformedLongPress law — GOLDEN-02 regression anchor).
            if (has_performed_long_press_) rec["up_click_suppressed"] = true;
            rec["consumed"] = true;
            break;
        }

        case TouchAction::CANCEL: {
            // View.java L17172-17184: setPressed(false) + removeTapCallback +
            // removeLongPressCallback + flag reset. The gesture ends; the
            // next DOWN starts clean.
            unschedule(tok_check_long_press_);
            unschedule(tok_perform_click_);
            unschedule(tok_unset_pressed_);
            if (gesture_target_ != 0) unpress(gesture_target_, &rec);
            rec["consumed"] = gesture_target_ != 0;
            reset_gesture();
            rec["law"] = "View.java L17172-17184: CANCEL cleanup";
            break;
        }
    }

    trace_.push_back(rec);
    return rec;
}

bool TouchDispatcher::fire_framework_callback(uint32_t token,
                                              nlohmann::json* record) {
    if (token < HandlerShadow::kFrameworkTokenBase) return false;
    nlohmann::json rec;
    rec["virtual_ms"] = handler_ ? handler_->virtual_now_ms() : 0;

    if (token == kTokenCheckLongPress) {
        rec["callback"] = "CheckForLongPress";
        tok_check_long_press_.id = 0;
        const uint32_t t = gesture_target_;
        const auto* n = t ? views_->find_node(t) : nullptr;
        rec["target_view_id"] = t;
        if (n && n->pressed && !has_performed_long_press_ && n->enabled) {
            bool consumed = false;
            bool dispatched =
                long_click_fn_ ? long_click_fn_(t, consumed) : false;
            // View.java CheckForLongPress:
            //   if (performLongClick()) mHasPerformedLongPress = true;
            // → the UP click is suppressed.
            if (dispatched && consumed) {
                has_performed_long_press_ = true;
                rec["long_press_consumed"] = true;
            } else {
                rec["long_press_consumed"] = false;
            }
            rec["dispatched"] = dispatched;
        }
    } else if (token == kTokenPerformClick) {
        rec["callback"] = "PerformClick";
        tok_perform_click_.id = 0;
        const uint32_t t = gesture_target_;
        rec["target_view_id"] = t;
        if (t != 0) {
            const auto* n = views_->find_node(t);
            if (n && n->enabled) {
                // View.performClick → dispatch onClick through real DEX.
                rec["click_dispatched"] = click_fn_ ? click_fn_(t, down_x_, down_y_) : false;
            } else {
                rec["click_dispatched"] = false;
                rec["disabled_law"] = true;
            }
        }
    } else if (token == kTokenUnsetPressed) {
        rec["callback"] = "UnsetPressedState";
        tok_unset_pressed_.id = 0;
        const uint32_t t = gesture_target_;
        rec["target_view_id"] = t;
        if (t != 0) unpress(t, &rec);
    } else {
        // Unknown/stale framework token — hostile-input safe: ignore.
        rec["callback"] = "UNKNOWN_TOKEN";
        rec["token"] = token;
        if (record) *record = rec;
        trace_.push_back(rec);
        return false;
    }
    if (record) *record = rec;
    trace_.push_back(rec);
    return true;
}

}  // namespace framework
}  // namespace miniandroid
