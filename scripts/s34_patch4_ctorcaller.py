#!/usr/bin/env python3
"""S34 probe 4: LayoutNode ctor caller trace — who builds the (only) two
LayoutNode objects? Extends the census probe lines with the direct caller
frame + object id. Env-gated by the same MINIANDROID_NODE_CENSUS. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """                ++ctor_count;
                if (ctor_count <= 12) {
                    std::cerr << "[NODE-CENSUS] LayoutNode ctor #" << ctor_count
                              << " " << descriptor << " depth=" << recursion_depth_
                              << std::endl;
                }"""

if '[S34-CTORCALLER]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'ctor anchor not found'

replacement = """                ++ctor_count;
                if (ctor_count <= 12) {
                    std::cerr << "[NODE-CENSUS] LayoutNode ctor #" << ctor_count
                              << " " << descriptor << " depth=" << recursion_depth_;
                    // [S34-CTORCALLER] direct caller of the LayoutNode ctor
                    if (!call_stack_.empty()) {
                        const StackFrame& cfr = call_stack_.top();
                        std::cerr << " caller=" << cfr.class_name << "."
                                  << cfr.method_name;
                    }
                    std::cerr << std::endl;
                }"""

src = src.replace(anchor, replacement, 1)
open(P, 'w').write(src)
print('ctor-caller probe applied')
