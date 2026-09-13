#!/usr/bin/env python3
"""S34 probe 6: ComposerImpl node-emit counter — LF/l.m(LL1/a;)V is the
interface implementation of composer.m(factory) (ReusableComposeNode/Layout
emission). Counting its executions answers: did the app composables request
ONE node or MANY (app-side early exit vs changelist truncation)?
Env-gated MINIANDROID_NODE_CENSUS. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if (class_name == "Landroidx/compose/ui/node/e$a;" &&
                       method_name == "c") {"""

if '[S34-NODEEMIT]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if (class_name == "LF/l;" && method_name == "m" &&
                       descriptor == "(LL1/a;)V") {
                // [S34-NODEEMIT] ComposerImpl.m(factory) — node emission count
                static thread_local uint64_t emit_call_count = 0;
                ++emit_call_count;
                if (emit_call_count <= 24) {
                    std::cerr << "[S34-NODEEMIT] composer.m #" << emit_call_count
                              << " depth=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi) {
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    }
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/node/e$a;" &&
                       method_name == "c") {"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('node-emit probe applied')
