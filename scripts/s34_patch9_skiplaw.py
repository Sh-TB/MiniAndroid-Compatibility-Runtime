#!/usr/bin/env python3
"""S34 probe 9: skipping-law forensics.
- LF/l.k()Z returns (skipping flag) — first 80, with caller. Upstream law:
  during a FRESH composition skipping must be FALSE for every group with
  content; TRUE skips the body (no nodes emitted).
- Unbounded counters for node-group methods: j=startNode, F=useNode,
  m=createNode, r/b/g/i=end variants — log first 40 of each.
Env-gated MINIANDROID_NODE_CENSUS. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if (class_name == "LF/l;") {
                // [S34-LALL] every ComposerImpl method entry, bounded"""

if '[S34-SKIPLAW]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if (class_name == "LF/l;" && method_name == "k" &&
                       descriptor == "()Z") {
                // [S34-SKIPLAW] skipping flag returns — fresh composition
                // must never skip content groups.
                static thread_local uint64_t skip_count = 0;
                ++skip_count;
                if (skip_count <= 80) {
                    std::cerr << "[S34-SKIPLAW] LF/l.k #" << skip_count
                              << " depth=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "LF/l;" &&
                       method_name == "j" && descriptor == "()V") {
                static thread_local uint64_t sn_count = 0;
                ++sn_count;
                if (sn_count <= 40)
                    std::cerr << "[S34-GROUPS] startNode #" << sn_count
                              << " depth=" << recursion_depth_ << std::endl;
            } else if (class_name == "LF/l;" &&
                       method_name == "F" && descriptor == "()V") {
                static thread_local uint64_t un_count = 0;
                ++un_count;
                if (un_count <= 40)
                    std::cerr << "[S34-GROUPS] useNode #" << un_count
                              << " depth=" << recursion_depth_ << std::endl;
            } else if (class_name == "LF/l;" &&
                       method_name == "m" && descriptor == "(LL1/a;)V") {
                static thread_local uint64_t cn_count = 0;
                ++cn_count;
                if (cn_count <= 40)
                    std::cerr << "[S34-GROUPS] createNode #" << cn_count
                              << " depth=" << recursion_depth_ << std::endl;
            } else if (class_name == "LF/l;" && method_name == "r" &&
                       descriptor == "()V") {
                static thread_local uint64_t en_count = 0;
                ++en_count;
                if (en_count <= 40)
                    std::cerr << "[S34-GROUPS] r() #" << en_count
                              << " depth=" << recursion_depth_ << std::endl;
            } else if (class_name == "LF/l;") {
                // [S34-LALL] every ComposerImpl method entry, bounded"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('skip-law probe applied')
