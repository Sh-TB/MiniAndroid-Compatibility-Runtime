#!/usr/bin/env python3
"""F-099 (R-NEW-332): compose-owner draw dispatch at visit, not only at leaves.

LAW (upstream Compose 1.6.7, AndroidComposeView.dispatchDraw): the compose
owner draws its whole LayoutNode tree (measureAndLayout + canvasHolder
.drawInto { root.draw }) INDEPENDENT of platform view children — interop
children only display-list-update through the clip-to-zero super.dispatchDraw
path. The shadow tree may legitimately hold view children (AndroidViewsHandler
family, attached by real DEX addView once the deeper composition runs) without
invalidating the compose draw dispatch.

MINIMAL FIX: widen the draw-dispatch gate — a non-framework view node whose
class chain OVERRIDES dispatchDraw (the generic AOSP "my content flows through
my own dispatch" contract) gets the real draw dispatch at visit even when it
has children. No class names hardcoded; ops still originate from real DEX.
"""
import sys

P = '/tmp/my-project/miniandroid/src/runtime/execution_engine.cpp'
src = open(P).read()

if 'F-099' in src:
    print('F-099 already present')
    sys.exit(0)

anchor = """                                if ((!framework_class || compose_view_class) && node->children.empty() &&
                                    !has_own_content && w > 40 && h > 40 &&
                                    node->visibility == 0) {"""
assert anchor in src, 'leaf gate anchor not found'

new = """                                // F-099 (R-NEW-332): compose-owner dispatch
                                // at visit. Upstream AndroidComposeView
                                // .dispatchDraw (ui-android 1.6.7) draws the
                                // whole LayoutNode tree regardless of platform
                                // view children; a non-framework class that
                                // OVERRIDES dispatchDraw carries its own draw
                                // dispatch contract (AOSP ViewGroup law), so
                                // the presence of shadow-tree children (e.g.
                                // the AndroidViewsHandler attached by real DEX
                                // addView) must not suppress it. Generic
                                // override check — no class names hardcoded.
                                bool dispatchdraw_override =
                                    dalvik_engine_.chain_overrides_method(
                                        node->class_desc, "dispatchDraw");
                                bool f099_owner_gate =
                                    compose_view_class && dispatchdraw_override &&
                                    !node->children.empty() &&
                                    !has_own_content && w > 40 && h > 40 &&
                                    node->visibility == 0;
                                if (((!framework_class || compose_view_class) && node->children.empty() &&
                                    !has_own_content && w > 40 && h > 40 &&
                                    node->visibility == 0) || f099_owner_gate) {"""
src = src.replace(anchor, new, 1)
open(P, 'w').write(src)
print('F-099 applied')
