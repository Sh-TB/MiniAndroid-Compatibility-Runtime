#!/usr/bin/env python3
"""F-098 (R-NEW-332 placement gate): instance-method identity refinement for
the active-cycle guard.

LAW: Kotlin visitor/observer/scope patterns (SnapshotObserver.observeReads,
forEach dispatches, listener dispatch) call the SAME method on the SAME
receiver with DIFFERENT payload object arguments — nested. Upstream
compose 1.6.7 nests observations per LayoutNode during the placement
cascade; the receiver-only key stubbed the 2nd observation, killing
onNodePlaced -> markNodeAndSubtreeAsPlaced -> isPlaced=false at draw.
Key refinement: instance-method key = receiver + up to 2 leading object-arg
identities (mirrors F-076 statics law). Same receiver + same payload
re-entry = genuine cycle (stub preserved); different payload = legal
nested dispatch. MAX_RECURSION_DEPTH (80) remains the backstop.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

if 'F-098' in src:
    print('F-098 already present')
    sys.exit(0)

anchor = """    std::string m3_active_key = class_descriptor + "." + method_name;
    if (!current_invoke_is_static_ && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF && args[0].object_id != 0) {
        m3_active_key += "#" + std::to_string(args[0].object_id);
    } else if (current_invoke_is_static_) {"""
assert anchor in src, 'key construction anchor not found'

new = """    std::string m3_active_key = class_descriptor + "." + method_name;
    if (!current_invoke_is_static_ && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF && args[0].object_id != 0) {
        m3_active_key += "#" + std::to_string(args[0].object_id);
        // ────────────────────────────────────────────────────────────────
        // F-098 (R-NEW-332 placement gate): instance-method identity
        // refinement — include up to 2 leading OBJECT-ARGUMENT identities
        // (excluding the receiver), mirroring F-076's statics law.
        //
        // SOURCE (upstream Compose 1.6.7):
        //   OwnerSnapshotObserver.observeLayoutModifierSnapshotReads(node,
        //   affectsLookahead, block) -> SnapshotObserver.observeReads(
        //   target, onChanged, block); called from
        //   LayoutNodeLayoutDelegate.MeasurePassDelegate
        //   .placeOuterCoordinator's not-yet-placed branch; the block runs
        //   outerCoordinator.place -> InnerNodeCoordinator.placeAt ->
        //   measurePassDelegate.onNodePlaced -> markNodeAndSubtreeAsPlaced
        //   (isPlaced=true). Observations NEST per LayoutNode during the
        //   placement cascade (child placement executes inside the parent's
        //   still-open observation), all on the ONE AndroidComposeView
        //   snapshot-observer singleton.
        //
        // OBSERVATION (dooz v18, MINIANDROID_ARG_TRACE=m0/T):
        //   call#1 executed: m0/T.a(recv=1198, p1=node#824, p2=#1209,
        //   p3=#1071); call#2 STUBBED: m0/T.a(recv=1198, p1=node#3101,
        //   p2=#1209, p3=#3126) — "[M3-19-CYCLE] Lm0/T;.a#1198 re-entered
        //   (depth=16)". Different target node, same receiver — legal
        //   upstream re-entrancy stubbed -> child's onNodePlaced never ran
        //   -> isPlaced=false at draw -> InnerNodeCoordinator.performDraw
        //   skipped every child -> 0 canvas ops (placeholder frame).
        //
        // SEMANTIC LAW: visitor/observer/scope dispatch methods take the
        // TARGET as a payload argument; nesting differs by payload
        // identity. Same receiver + same payload re-entry is a genuine
        // cycle (stub preserved); same receiver + different payload is
        // legal nested dispatch (execute real DEX).
        //
        // IMPACT: the entire Compose placement cascade (all Compose apps);
        // generic visitor/listener dispatch on shared receivers.
        //
        // PROOF: dooz [LIFEWIN-ZRET] e.G(3101)=FALSE before the fix;
        // TRUE + child draw recursion + real canvas ops after.
        // MAX_RECURSION_DEPTH (80) remains the backstop.
        // ────────────────────────────────────────────────────────────────
        {
            int appended = 0;
            for (size_t i = 1; i < args.size() && appended < 2; ++i) {
                if (args[i].type == DalvikType::OBJECT_REF &&
                    args[i].object_id != 0 && !args[i].is_null) {
                    m3_active_key += "#" + std::to_string(args[i].object_id);
                    ++appended;
                }
            }
        }
    } else if (current_invoke_is_static_) {"""
src = src.replace(anchor, new, 1)
open(P, 'w').write(src)
print('F-098 applied')
