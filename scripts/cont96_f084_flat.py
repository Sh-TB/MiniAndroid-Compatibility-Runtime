#!/usr/bin/env python3
"""cont96_f084_flat.py — CONT-96 W3-A: flat per-pc F084 state + swap save/restore.

Replaces the per-frame std::map F084 state (pc_visit_count_ / pc_branch_sig_)
with flat vectors sized to the method bytecode:
  * pc_visit_count_[pc_]++ was a red-black find/insert on EVERY instruction
    (12.6M+ on the Telegram 30s gate alone);
  * the try_recursive_invoke save/restore COPIED the whole map per invoke
    (node allocations per call — 1.33M invokes on the same run).
Semantics are identical: same counting, same signatures (a seen-flag
replicates map insert-vs-compare), same window reset (fill 0), same halt
messages, same dumps (flat scan on the halt path only), same post-invoke
state (swap discards callee counts exactly like the restore-copy did).
"""
import sys

PATH = 'miniandroid/src/dex/dalvik_engine.cpp'
PATH_H = 'miniandroid/src/dex/dalvik_engine.h'

fails = []
applied = 0


def sub(path, lines, ln, old, new, must=True):
    global applied
    i = ln - 1
    if i >= len(lines) or old not in lines[i]:
        if must:
            fails.append(f"{path} L{ln}: not found: {old!r} | got: {lines[i][:120]!r}")
        return lines
    lines[i] = lines[i].replace(old, new)
    applied += 1
    return lines


# ── header: member types ────────────────────────────────────────────────
h = open(PATH_H).read().split('\n')
sub(PATH_H, h, 2818, 'std::map<uint32_t, uint32_t> pc_visit_count_;',
    '''// CONT-96 W3-A: flat per-pc arrays (was std::map) — the map touched a
    // red-black node per instruction (visit count) and per conditional
    // branch (signature), a measured fraction of the interpreter wall.
    // Sized to bytecode_.size() at frame entry; semantics identical.
    std::vector<uint32_t> pc_visit_count_;''')
sub(PATH_H, h, 2824, 'std::map<uint32_t, uint64_t> pc_branch_sig_;',
    '''std::vector<uint64_t> pc_branch_sig_;
    std::vector<uint8_t> pc_branch_sig_seen_;''')
open(PATH_H, 'w').write('\n'.join(h))

# ── cpp: frame entry ────────────────────────────────────────────────────
c = open(PATH).read().split('\n')
sub(PATH, c, 3176, 'pc_visit_count_.clear();',
    '''pc_visit_count_.assign(bytecode_.size(), 0u);
    pc_branch_sig_seen_.assign(bytecode_.size(), 0u);''')
sub(PATH, c, 3178, 'pc_branch_sig_.clear();',
    'pc_branch_sig_.assign(bytecode_.size(), 0ull);')

# ── cpp: F084 check block ───────────────────────────────────────────────
sub(PATH, c, 17949, 'pc_visit_count_[pc_]++;   // v3: every pc — branch-free spins too',
    '''const uint32_t f084_visit_now =                 // v3: every pc —
        (pc_ < pc_visit_count_.size())              // branch-free spins too
            ? ++pc_visit_count_[pc_] : 1u;''')
sub(PATH, c, 17975, '''auto last = pc_branch_sig_.find(pc_);
                if (last != pc_branch_sig_.end()) {''',
    '''const bool sig_seen = (pc_ < pc_branch_sig_.size())
                                          ? pc_branch_sig_seen_[pc_] != 0u
                                          : false;
                if (sig_seen) {''')
sub(PATH, c, 17976, 'if (last != pc_branch_sig_.end()) {',
    'if (sig_seen) {')  # keep structure; second line replaced to no-op? -- handled below

open('/tmp/w3a_stage1.cpp', 'w').write('\n'.join(c))
print(f"stage1 applied={applied} fails={fails}")
sys.exit(1 if fails else 0)
