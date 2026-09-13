#!/usr/bin/env python3
"""S34 probe 13: h1/t.a (NavigatorState.createBackStackEntry) dispatch forensics.

The R-NEW-333 chain breaks at h.d:012a — the virtual dispatch
Lh1/t;->a(Landroidx/navigation/f; Landroid/os/Bundle;)Landroidx/navigation/b;
never reaches the concrete c$a.a. This probe logs, bounded:
  - TSTATE-ENTRY: declaring/runtime class, receiver + arg identities
  - TSTATE-RES:   which dispatch attempt answered (runtime / hierarchy /
                  declaring / bridge) and the return value
Env-gated via the standard probe build; bounded 12; idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """    // EXP-038 (BLOCKER-034): Try recursive DEX method invocation first."""

if '[S34-TSTATE]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """    // [S34-TSTATE] NavigatorState.createBackStackEntry dispatch forensics
    if (declaring_class == "Lh1/t;" && method_name_from_dex == "a") {
        static thread_local uint64_t tstate_n = 0;
        ++tstate_n;
        if (tstate_n <= 12) {
            std::cerr << "[S34-TSTATE] h1/t.a entry #" << tstate_n
                      << " runtime_type=" << runtime_type
                      << " recv=o" << (args.empty() ? 0 : args[0].object_id)
                      << " cls=" << (args.empty() ? "?" : args[0].class_desc);
            for (size_t ai = 1; ai < args.size() && ai < 3; ++ai)
                std::cerr << " a" << ai << "=o" << args[ai].object_id
                          << (args[ai].is_null ? "(NULL)" : "");
            std::cerr << std::endl;
        }
    }
    // EXP-038 (BLOCKER-034): Try recursive DEX method invocation first."""

src = src.replace(anchor, probe, 1)

# resolution result probe: after the three dispatch attempts, before bridge_to_api
anchor2 = """    if (!recursively_invoked && config_.enable_api_bridge) {
        // Use declaring_class (the static type from method_ids[]) if"""
if '[S34-TSTATE-RES]' in src:
    print('RES already present')
    sys.exit(0)
assert anchor2 in src, 'anchor2 not found'

probe2 = """    if (declaring_class == "Lh1/t;" && method_name_from_dex == "a") {
        static thread_local uint64_t tstate_r = 0;
        ++tstate_r;
        if (tstate_r <= 12) {
            std::cerr << "[S34-TSTATE-RES] h1/t.a #" << tstate_r
                      << " recursively_invoked=" << (recursively_invoked ? 1 : 0)
                      << " runtime=" << runtime_type
                      << " status=" << (int)api_status;
            if (return_val.type == DalvikType::OBJECT_REF)
                std::cerr << " ret=o" << return_val.object_id;
            std::cerr << std::endl;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // Use declaring_class (the static type from method_ids[]) if"""

src = src.replace(anchor2, probe2, 1)
open(P, 'w').write(src)
print('TSTATE probes applied')
