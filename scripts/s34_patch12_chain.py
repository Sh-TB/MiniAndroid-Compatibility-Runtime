#!/usr/bin/env python3
"""S34 probe 12: content-chain link probe.
N/a.j entered but R/f.a never ran. The chain: N/a.j -> N/a.a -> LL1/q.j
(interface dispatch) -> k0/s.j -> [R/f content]. Log entries of each link to
find the exact broken link.
Env-gated MINIANDROID_NODE_CENSUS. Bounded 10 per link. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if (class_name == "LN/a;" && method_name == "j" &&
                       descriptor.size() > 20) {"""

if '[S34-CHAINLINK]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if (class_name == "LN/a;" && method_name == "a" &&
                       descriptor == "(Ljava/lang/Object; LF/i; I)Ljava/lang/Object;") {
                static thread_local uint64_t naa_n = 0;
                ++naa_n;
                if (naa_n <= 10) {
                    std::cerr << "[S34-CHAINLINK] N/a.a #" << naa_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "Lk0/s;" && method_name == "j") {
                static thread_local uint64_t ksj_n = 0;
                ++ksj_n;
                if (ksj_n <= 10) {
                    std::cerr << "[S34-CHAINLINK] k0/s.j #" << ksj_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LN/a;" && method_name == "j" &&
                       descriptor.size() > 20) {"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('chain-link probe applied')
