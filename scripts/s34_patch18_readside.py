#!/usr/bin/env python3
"""S34 probe 18: the visibleEntries read side.

The push machinery writes the flows, but p.a's read (F/f1.getValue →
z1/r.A lastOrNull at 0e2e → 0e78 gate) apparently sees empty. Probe:
  - F/w.b RETURNS (the F/f1 object id) — first 12
  - F/f1.getValue entries (recv id) — first 20
  - z1/r.A (lastOrNull) returns — first 20 with recv+ret
  - Z1/z method entries (the transitions tracker) — first 16
Bounded; idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if ((class_name == "Lh1/t;") ||"""

if '[S34-READSIDE]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if ((class_name == "LF/w;" && method_name == "b") ||
                       (class_name == "LF/f1;" && method_name == "getValue") ||
                       (class_name == "Lz1/r;" && method_name == "A") ||
                       (class_name == "LZ1/z;")) {
                // [S34-READSIDE] visibleEntries read side
                static thread_local std::map<std::string, uint64_t> rsd_n;
                std::string rsd_key = class_name + "." + method_name;
                uint64_t n = ++rsd_n[rsd_key];
                if (n <= 20) {
                    std::cerr << "[S34-READSIDE] " << rsd_key << " #" << n
                              << " d=" << recursion_depth_;
                    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                        std::cerr << " recv=o" << args[0].object_id;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " <" << frames[0].first << "."
                                  << frames[0].second << ">";
                    std::cerr << std::endl;
                }
            } else if ((class_name == "Lh1/t;") ||"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('READSIDE probes applied')
