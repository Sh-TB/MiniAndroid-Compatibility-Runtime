#!/usr/bin/env python3
"""S34 probe 7: ComposerImpl state-machine trace — log startNode (j), useNode
(F), createNode (m), and isInserting reads (C) with the O (inserting) and
q (nodeStarted) field values. Answers WHY only one createNode was recorded:
where exactly the inserting flag flips or the machine diverges from upstream.
Env-gated MINIANDROID_NODE_CENSUS. Bounded 100 lines. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if (class_name == "LF/l;" && method_name == "m" &&
                       descriptor == "(LL1/a;)V") {"""

if '[S34-STATEM]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if (class_name == "LF/l;" &&
                       (method_name == "j" || method_name == "F" ||
                        method_name == "C" || method_name == "b" ||
                        method_name == "g" || method_name == "r") &&
                       descriptor == "()V" || (class_name == "LF/l;" &&
                       method_name == "C" && descriptor == "()Z")) {
                // [S34-STATEM] ComposerImpl state machine: j=startNode,
                // F=useNode, m=createNode (logged elsewhere), C=isInserting,
                // r=endNode-ish. O/q are private fields — read via the
                // receiver object storage at known offsets is not portable;
                // instead log the method + depth + caller only.
                static thread_local uint64_t statem_count = 0;
                ++statem_count;
                if (statem_count <= 120) {
                    std::cerr << "[S34-STATEM] LF/l." << method_name
                              << " depth=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "LF/l;" && method_name == "m" &&
                       descriptor == "(LL1/a;)V") {"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('state-machine probe applied')
