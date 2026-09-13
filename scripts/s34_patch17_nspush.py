#!/usr/bin/env python3
"""S34 probe 17: NavigatorState push + flow forensics.

p.a:0e78 skips AnimatedContent because visibleEntries.lastOrNull() == null.
The list is filled by e.d → h1/t.e(entry) (NavigatorState.push). Probe:
  - h1/t method dispatches (e/b/c/d declared on concrete c$a or h1/t)
  - Z1/M.getValue / setValue (the flows) — first 30
  - the e.d pc-progress: instrument execute_invoke_virtual when caller is
    compose/e;.d — log the dispatch target + result per call
Bounded; idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if ((class_name == "Lj/b;" && method_name == "b") ||"""

if '[S34-NSPUSH]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if ((class_name == "Lh1/t;") ||
                       (class_name == "Landroidx/navigation/c$a;")) {
                // [S34-NSPUSH] NavigatorState method dispatches
                static thread_local std::map<std::string, uint64_t> nsp_n;
                std::string nsp_key = class_name + "." + method_name;
                uint64_t n = ++nsp_n[nsp_key];
                if (n <= 10) {
                    std::cerr << "[S34-NSPUSH] " << nsp_key << " #" << n
                              << " d=" << recursion_depth_
                              << " argc=" << args.size();
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 2; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if ((class_name == "LZ1/M;") &&
                       (method_name == "getValue" || method_name == "setValue")) {
                // [S34-FLOW] MutableStateFlow get/set
                static thread_local uint64_t flw_n = 0;
                ++flw_n;
                if (flw_n <= 40) {
                    std::cerr << "[S34-FLOW] Z1/M." << method_name << " #" << flw_n
                              << " d=" << recursion_depth_;
                    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                        std::cerr << " recv=o" << args[0].object_id;
                    if (method_name == "setValue" && args.size() > 1 &&
                        args[1].type == DalvikType::OBJECT_REF)
                        std::cerr << " val=o" << args[1].object_id;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " <" << frames[0].first << "."
                                  << frames[0].second << ">";
                    std::cerr << std::endl;
                }
            } else if ((class_name == "Lj/b;" && method_name == "b") ||"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('NSPUSH probes applied')
