#!/usr/bin/env python3
"""S33 probe 6: LayoutNode census (R-NEW-332 tree-depth evidence).
Counts LayoutNode (class e) constructor executions and draw entries;
env-gated MINIANDROID_NODE_CENSUS=1, bounded print. Also traces the
composition-side node insertion: androidx compose applies nodes through
the applier — count e.<init> + child-link entry points.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

if 'NODE-CENSUS' in src:
    print('already present')
    sys.exit(0)

anchor = """    // EXP-053: Clear pending exception at method entry."""
assert anchor in src

probe = """    // S33 (R-NEW-332): LayoutNode census — count LayoutNode constructions
    // and draw dispatches; bounded, env-gated. Distinguishes "composition
    // created few nodes" from "nodes created but not linked into the tree".
    {
        static thread_local const bool census_on =
            std::getenv("MINIANDROID_NODE_CENSUS") != nullptr;
        if (census_on) {
            static thread_local uint64_t ctor_count = 0;
            static thread_local uint64_t draw_count = 0;
            static thread_local uint64_t attach_count = 0;
            if (class_name == "Landroidx/compose/ui/node/e;" &&
                method_name == "<init>") {
                ++ctor_count;
                if (ctor_count <= 12) {
                    std::cerr << "[NODE-CENSUS] LayoutNode ctor #" << ctor_count
                              << " " << descriptor << " depth=" << recursion_depth_
                              << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/node/e;" &&
                       method_name == "n") {
                ++draw_count;
                if (draw_count <= 8) {
                    std::cerr << "[NODE-CENSUS] LayoutNode.draw #" << draw_count
                              << " " << descriptor
                              << " recv=" << (args.empty() ? 0 : args[0].object_id)
                              << std::endl;
                }
            } else if ((class_name == "Landroidx/compose/ui/node/e;" ||
                        class_name == "Lk0/T;") &&
                       (method_name == "attach" || method_name == "x0" ||
                        method_name == "N0" || method_name == "O0")) {
                ++attach_count;
                if (attach_count <= 12) {
                    std::cerr << "[NODE-CENSUS] link-candidate "
                              << class_name << "." << method_name
                              << " #" << attach_count
                              << " recv=" << (args.empty() ? 0 : args[0].object_id)
                              << " " << descriptor << std::endl;
                }
            }
        }
    }
    // EXP-053: Clear pending exception at method entry."""
src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('census probe applied')
