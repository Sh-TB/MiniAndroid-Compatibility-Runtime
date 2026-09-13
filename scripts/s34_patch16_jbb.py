#!/usr/bin/env python3
"""S34 probe 16: why the p.a:0fc8 invoke-static/range Lj/b;->b misses.

Probe (bounded, env-gated):
  [S34-JBB]  at try_recursive_invoke entry when declaring_class == Lj/b;
             (print class found? method match? depth)
  [S34-RANGE] in the 3rc range handler when class_name == Lj/b;
             (print argc, first-reg, resolved proto, descriptor)
Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

# 1. RANGE handler probe
a1 = """                // Resolve method name
                std::string method_name = "<range_method:" + std::to_string(method_idx) + ">";"""
if '[S34-RANGE]' in src:
    print('RANGE already present')
    sys.exit(1)
assert a1 in src, 'a1 missing'

p1 = """                {
                    static thread_local uint64_t rng_n = 0;
                    std::string rng_cls = dex_report_
                        ? resolve_method_class_for_dex(method_idx, current_dex_index_)
                        : std::string("<nodex>");
                    if (rng_cls == "Lj/b;" || rng_cls == "Lj/i;" || rng_cls == "LC0/b;") {
                        ++rng_n;
                        if (rng_n <= 12) {
                            std::cerr << "[S34-RANGE] " << rng_cls << "."
                                      << (dex_report_
                                              ? resolve_method_name_for_dex(method_idx, current_dex_index_)
                                              : "?")
                                      << " argc=" << (int)argc
                                      << " first_reg=" << first_reg
                                      << " caller=" << current_class_ << "."
                                      << current_method_
                                      << " depth=" << recursion_depth_
                                      << std::endl;
                        }
                    }
                }
                // Resolve method name
                std::string method_name = "<range_method:" + std::to_string(method_idx) + ">";"""
src = src.replace(a1, p1, 1)

# 2. try_recursive_invoke probe for j/b
a2 = """    // M3 FINDING-016 (strict mode): an exception already escaped the app"""
if '[S34-JBB]' in src:
    print('JBB already present')
    sys.exit(1)
assert a2 in src, 'a2 missing'

p2 = """    if (declaring_class == "Lj/b;" && method_name == "b") {
        static thread_local uint64_t jbb_n = 0;
        ++jbb_n;
        if (jbb_n <= 12) {
            std::cerr << "[S34-JBB] try_recursive_invoke j/b.b #" << jbb_n
                      << " depth=" << recursion_depth_
                      << " argc=" << args.size()
                      << " dex_desc=" << (method_descriptor.empty() ? "<none>" : method_descriptor)
                      << " caller=" << current_class_ << "." << current_method_;
            bool cls_found = class_info_index_.count(declaring_class) > 0;
            std::cerr << " cls_found=" << (cls_found ? 1 : 0);
            if (cls_found) {
                const dex::ClassInfo& ci =
                    dex_report_->classes[class_info_index_[declaring_class]];
                for (const auto& m : ci.all_methods()) {
                    if (m.name == "b")
                        std::cerr << " [cand " << m.descriptor
                                  << " bsz=" << m.bytecode.size() << "]";
                }
            }
            std::cerr << std::endl;
        }
    }
    // M3 FINDING-016 (strict mode): an exception already escaped the app"""
src = src.replace(a2, p2, 1)
open(P, 'w').write(src)
print('JBB probes applied')
