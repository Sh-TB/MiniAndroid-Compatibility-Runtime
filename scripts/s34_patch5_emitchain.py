#!/usr/bin/env python3
"""S34 probe 5: full caller chain (top-8 frames) on the LayoutNode factory
emission (e$a.c) — pinpoints exactly which composable requested the single
node insert. Uses CallStack.snapshot_top_first(). Env MINIANDROID_NODE_CENSUS.
Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if (class_name == "Landroidx/compose/ui/node/e;" &&
                       method_name == "n") {"""

if '[S34-EMITCHAIN]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if (class_name == "Landroidx/compose/ui/node/e$a;" &&
                       method_name == "c") {
                // [S34-EMITCHAIN] node factory call — top-8 caller frames
                static thread_local uint64_t emit_count = 0;
                ++emit_count;
                if (emit_count <= 6) {
                    std::cerr << "[S34-EMITCHAIN] LayoutNode factory #" << emit_count
                              << " depth=" << recursion_depth_ << " chain:";
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 8; ++fi) {
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    }
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/node/e;" &&
                       method_name == "n") {"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('emit-chain probe applied')
