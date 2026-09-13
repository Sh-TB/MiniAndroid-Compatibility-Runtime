#!/usr/bin/env python3
"""S34 probe 8: ALL ComposerImpl (LF/l) method entries, bounded — reveals the
exact composer call sequence and where it goes silent after the first node.
Env-gated MINIANDROID_NODE_CENSUS. Bounded 220 lines. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if (class_name == "LF/l;" &&
                       ((method_name == "j" || method_name == "F" ||"""

if '[S34-LALL]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if (class_name == "LF/l;") {
                // [S34-LALL] every ComposerImpl method entry, bounded
                static thread_local uint64_t lall_count = 0;
                ++lall_count;
                if (lall_count <= 220) {
                    std::cerr << "[S34-LALL] #" << lall_count << " LF/l."
                              << method_name << descriptor
                              << " d=" << recursion_depth_;
                    if (lall_count >= 200 && lall_count <= 220) {
                        auto frames = call_stack_.snapshot_top_first();
                        if (!frames.empty())
                            std::cerr << " caller=" << frames[0].first << "."
                                      << frames[0].second;
                    }
                    std::cerr << std::endl;
                }
            } else if (class_name == "LF/l;" &&
                       ((method_name == "j" || method_name == "F" ||"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('LALL probe applied')
