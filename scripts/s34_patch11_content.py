#!/usr/bin/env python3
"""S34 probe 11: content-lambda invoke forensics.
- LN/a.j(Object,Object,Object) entries — the Layout content lambda trampoline
  invoked by D/b.f. Did the content actually compose?
- LR/f;.k / any method of the content lambda body class R/f.
- k0/t.a return-class logging (what wraps R/f).
Env-gated MINIANDROID_NODE_CENSUS. Bounded 14. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if (class_name == "LD/b;" && method_name == "f") {"""

if '[S34-CONTENT]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if (class_name == "LN/a;" && method_name == "j" &&
                       descriptor.size() > 20) {
                // [S34-CONTENT] content-lambda trampoline entries
                static thread_local uint64_t naj_n = 0;
                ++naj_n;
                if (naj_n <= 14) {
                    std::cerr << "[S34-CONTENT] LN/a.j #" << naj_n
                              << " d=" << recursion_depth_ << " " << descriptor;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 4; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LR/f;" &&
                       (method_name == "k" || method_name == "j")) {
                // [S34-CONTENT] R/f (content body) method entries
                static thread_local uint64_t rf_n = 0;
                ++rf_n;
                if (rf_n <= 14) {
                    std::cerr << "[S34-CONTENT] LR/f." << method_name << " #"
                              << rf_n << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "LD/b;" && method_name == "f") {"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('content probe applied')
