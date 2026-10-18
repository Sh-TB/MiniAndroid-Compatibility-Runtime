#!/usr/bin/env python3
"""cont96_apply_edits.py — apply the CONT-96 hot-path edits with exact-text
verification. Fails loudly on any mismatch (no silent guessing).

Edit classes:
  F-NEW-398  complete the F084 save/restore in try_recursive_invoke
  W1         std::getenv("F") presence-check -> diag_env("F") at hot lines
  W2         gate ALWAYS-ON debug prints behind diag_env flags
  HELPER     insert diag_env() definition once
"""
import sys

PATH = 'miniandroid/src/dex/dalvik_engine.cpp'

with open(PATH) as f:
    lines = f.read().split('\n')

fails = []
applied = 0


def sub(ln, old, new, must=True):
    """Replace old->new on 1-based line ln; verify old exists."""
    global applied
    i = ln - 1
    if old not in lines[i]:
        if must:
            fails.append(f"L{ln}: pattern not found: {old!r} | line: {lines[i][:120]!r}")
        return
    lines[i] = lines[i].replace(old, new)
    applied += 1


# ────────────────────────────────────────────────────────────────────────
# HELPER: diag_env definition (inserted after the includes block).
# Find the first line after the last #include at file top.
# ────────────────────────────────────────────────────────────────────────
last_inc = 0
for i, l in enumerate(lines[:200]):
    if l.startswith('#include'):
        last_inc = i
helper = '''
// ────────────────────────────────────────────────────────────────────────
// CONT-96 W1 (F-074 throughput law): diagnostic env presence-checks used
// to call std::getenv() on EVERY interpreter instruction / method entry —
// an environ walk per opcode (measured as a real fraction of the ~310K
// ins/s interpreter wall on the 30s Telegram gate; see the 14530-site
// note for the single-site precedent). Diagnostic flags are
// process-constant: diag_env() caches the first-use answer keyed by the
// literal POINTER (every diagnostic call site passes a string literal;
// literals are stable for the process lifetime). Identical answers,
// identical stderr when a flag is set — only the per-op environ walk is
// gone. Value-using sites (find(getenv(...)), env[0]=='0') keep their
// raw getenv by design.
// ────────────────────────────────────────────────────────────────────────
static bool diag_env(const char* name) {
    struct Entry { const char* name; bool value; };
    static thread_local Entry table[96];
    static thread_local uint32_t count = 0;
    for (uint32_t i = 0; i < count; ++i)
        if (table[i].name == name) return table[i].value;
    const bool v = std::getenv(name) != nullptr;
    if (count < 96) {
        table[count].name = name;
        table[count].value = v;
        ++count;
    }
    return v;
}'''
lines[last_inc + 1:last_inc + 1] = helper.split('\n')
applied += 1

# Line numbers below were inventoried BEFORE the helper insertion
# (helper adds ~31 lines after line ~last_inc+1). All target lines are
# AFTER the insertion point, so they shift by the helper length.
SHIFT = len(helper.split('\n'))


def sub2(ln, old, new):
    sub(ln + SHIFT, old, new)


# ────────────────────────────────────────────────────────────────────────
# W1: presence-check getenv -> diag_env (hot regions only)
# ────────────────────────────────────────────────────────────────────────
W1 = [
    # execute_method_internal
    (3027, 'std::getenv("MINIANDROID_F282_TRACE") != nullptr', 'diag_env("MINIANDROID_F282_TRACE")'),
    (3165, 'std::getenv("MINIANDROID_S22_TRACE")', 'diag_env("MINIANDROID_S22_TRACE")'),
    (3262, 'std::getenv("MINIANDROID_J_ENTRY")', 'diag_env("MINIANDROID_J_ENTRY")'),
    (3285, 'std::getenv("MINIANDROID_WAVEC_TRACE")', 'diag_env("MINIANDROID_WAVEC_TRACE")'),
    (3378, 'std::getenv("MINIANDROID_COMPWIN_TRACE") != nullptr', 'diag_env("MINIANDROID_COMPWIN_TRACE")'),
    (3403, 'std::getenv("MINIANDROID_CVPARI") != nullptr', 'diag_env("MINIANDROID_CVPARI")'),
    (3460, 'std::getenv("MINIANDROID_CVPARI") != nullptr', 'diag_env("MINIANDROID_CVPARI")'),
    (3488, 'std::getenv("MINIANDROID_NODE_CENSUS") != nullptr', 'diag_env("MINIANDROID_NODE_CENSUS")'),
    (4062, 'std::getenv("MINIANDROID_METHOD_TRACE") != nullptr', 'diag_env("MINIANDROID_METHOD_TRACE")'),
    (4073, 'std::getenv("MINIANDROID_DRAW_WINDOW_TRACE") != nullptr', 'diag_env("MINIANDROID_DRAW_WINDOW_TRACE")'),
    (4091, 'std::getenv("MINIANDROID_ATTACH_WATCH") != nullptr', 'diag_env("MINIANDROID_ATTACH_WATCH")'),
    (4108, 'std::getenv("MINIANDROID_LIFEWIN_TRACE") != nullptr', 'diag_env("MINIANDROID_LIFEWIN_TRACE")'),
    (4348, 'std::getenv("MINIANDROID_APP_TRACE") != nullptr', 'diag_env("MINIANDROID_APP_TRACE")'),
    (4656, 'std::getenv("MINIANDROID_CLINIT_PATH_TRACE") != nullptr', 'diag_env("MINIANDROID_CLINIT_PATH_TRACE")'),
    (4673, 'std::getenv("MINIANDROID_CLINIT_PATH_TRACE") != nullptr', 'diag_env("MINIANDROID_CLINIT_PATH_TRACE")'),
    (5563, 'std::getenv("MINIANDROID_WAVEC_TRACE")', 'diag_env("MINIANDROID_WAVEC_TRACE")'),
    (5581, 'std::getenv("MINIANDROID_WAVEC_TRACE")', 'diag_env("MINIANDROID_WAVEC_TRACE")'),
    (6588, 'std::getenv("MINIANDROID_F074_TRACE") != nullptr', 'diag_env("MINIANDROID_F074_TRACE")'),
    # try_recursive_invoke
    (6776, 'std::getenv("MINIANDROID_COMPOSE_MEASURE_TRACE") != nullptr', 'diag_env("MINIANDROID_COMPOSE_MEASURE_TRACE")'),
    (6806, 'std::getenv("MINIANDROID_F040_DIAG")', 'diag_env("MINIANDROID_F040_DIAG")'),
    (6838, 'std::getenv("MINIANDROID_S24_TRACE") != nullptr', 'diag_env("MINIANDROID_S24_TRACE")'),
    (6859, 'std::getenv("MINIANDROID_APP_TRACE") != nullptr', 'diag_env("MINIANDROID_APP_TRACE")'),
    (6861, 'std::getenv("MINIANDROID_METHOD_TRACE") != nullptr', 'diag_env("MINIANDROID_METHOD_TRACE")'),
    (6869, 'std::getenv("MINIANDROID_ARG_TRACE") != nullptr', 'diag_env("MINIANDROID_ARG_TRACE")'),
    (6926, 'std::getenv("MINIANDROID_TRIE_TRACE") != nullptr', 'diag_env("MINIANDROID_TRIE_TRACE")'),
    (6988, 'std::getenv("MINIANDROID_R330_TRACE") != nullptr', 'diag_env("MINIANDROID_R330_TRACE")'),
    (7119, 'std::getenv("MINIANDROID_COMPOSE_MEASURE_TRACE") != nullptr', 'diag_env("MINIANDROID_COMPOSE_MEASURE_TRACE")'),
    (7267, 'std::getenv("MINIANDROID_S83_DIAG") != nullptr', 'diag_env("MINIANDROID_S83_DIAG")'),
    # invoke_virtual
    (21706, 'std::getenv("MINIANDROID_S24_TRACE") != nullptr', 'diag_env("MINIANDROID_S24_TRACE")'),
    (21720, 'std::getenv("MINIANDROID_CLASS_LAW_TRACE") != nullptr', 'diag_env("MINIANDROID_CLASS_LAW_TRACE")'),
    (21824, 'std::getenv("MINIANDROID_S24_TRACE") != nullptr', 'diag_env("MINIANDROID_S24_TRACE")'),
    (21888, 'std::getenv("MINIANDROID_F141_DIAG")', 'diag_env("MINIANDROID_F141_DIAG")'),
    (22204, 'std::getenv("MINIANDROID_F271_COLL_TRACE")', 'diag_env("MINIANDROID_F271_COLL_TRACE")'),
    # invoke_direct
    (22584, 'std::getenv("MINIANDROID_F040_DIAG") != nullptr', 'diag_env("MINIANDROID_F040_DIAG")'),
    (22713, 'std::getenv("MINIANDROID_E1_DIAG")', 'diag_env("MINIANDROID_E1_DIAG")'),
    # invoke_static
    (22807, 'std::getenv("MINIANDROID_F040_DIAG")', 'diag_env("MINIANDROID_F040_DIAG")'),
    (22851, 'std::getenv("MINIANDROID_R350_TRACE") != nullptr', 'diag_env("MINIANDROID_R350_TRACE")'),
    (23242, 'std::getenv("MINIANDROID_R350_TRACE") != nullptr', 'diag_env("MINIANDROID_R350_TRACE")'),
    # invoke_interface
    (23597, 'std::getenv("MINIANDROID_UV_WATCH") != nullptr', 'diag_env("MINIANDROID_UV_WATCH")'),
    (23736, 'std::getenv("MINIANDROID_UV_WATCH")', 'diag_env("MINIANDROID_UV_WATCH")'),
    (23757, 'std::getenv("MINIANDROID_IFACE_FAIL_TRACE")', 'diag_env("MINIANDROID_IFACE_FAIL_TRACE")'),
    (23853, 'std::getenv("MINIANDROID_F281_TRACE") != nullptr', 'diag_env("MINIANDROID_F281_TRACE")'),
    (24067, 'std::getenv("MINIANDROID_IFACE_FAIL_TRACE")', 'diag_env("MINIANDROID_IFACE_FAIL_TRACE")'),
    # try_shadow_dispatch
    (25949, 'std::getenv("MINIANDROID_TOUCH_WINDOW_TRACE") != nullptr', 'diag_env("MINIANDROID_TOUCH_WINDOW_TRACE")'),
    (25976, 'std::getenv("MINIANDROID_CANVAS_DRAW_WIN_TRACE") != nullptr', 'diag_env("MINIANDROID_CANVAS_DRAW_WIN_TRACE")'),
    (26004, 'std::getenv("MINIANDROID_LAWCEF_TRACE") != nullptr', 'diag_env("MINIANDROID_LAWCEF_TRACE")'),
    # main switch + post-switch + s44 site
    (15526, 'std::getenv("MINIANDROID_F040_DIAG")', 'diag_env("MINIANDROID_F040_DIAG")'),
    (17768, 'std::getenv("MINIANDROID_F040_DIAG")', 'diag_env("MINIANDROID_F040_DIAG")'),
    (14769, 'std::getenv("MINIANDROID_S44_R351") != nullptr', 'diag_env("MINIANDROID_S44_R351")'),
    # arith macros (per-op execution)
    (16043, 'std::getenv("MINIANDROID_WIDE_DIAG")', 'diag_env("MINIANDROID_WIDE_DIAG")'),
    (16142, 'std::getenv("MINIANDROID_S44_R351") != nullptr', 'diag_env("MINIANDROID_S44_R351")'),
    (16362, 'std::getenv("MINIANDROID_WIDE_DIAG")', 'diag_env("MINIANDROID_WIDE_DIAG")'),
    (16385, 'std::getenv("MINIANDROID_WIDE_DIAG")', 'diag_env("MINIANDROID_WIDE_DIAG")'),
    (16408, 'std::getenv("MINIANDROID_WIDE_DIAG")', 'diag_env("MINIANDROID_WIDE_DIAG")'),
    (16598, 'std::getenv("MINIANDROID_WIDE_DIAG")', 'diag_env("MINIANDROID_WIDE_DIAG")'),
    (16650, 'std::getenv("MINIANDROID_WIDE_DIAG")', 'diag_env("MINIANDROID_WIDE_DIAG")'),
    (17640, 'std::getenv("MINIANDROID_WIDE_DIAG")', 'diag_env("MINIANDROID_WIDE_DIAG")'),
]
for ln, old, new in W1:
    sub2(ln, old, new)

# ────────────────────────────────────────────────────────────────────────
# W2: gate ALWAYS-ON debug prints (S58-hygiene precedent)
# ────────────────────────────────────────────────────────────────────────
sub2(4325, 'if (class_name.find("PhoneView") != std::string::npos &&',
     'if (diag_env("MINIANDROID_EXP062_TRACE") && class_name.find("PhoneView") != std::string::npos &&')
sub2(4370, 'if (current_method_.find("addFragmentToStack") != std::string::npos ||',
     'if (diag_env("MINIANDROID_EXP058_TRACE") && current_method_.find("addFragmentToStack") != std::string::npos ||')
sub2(21742, 'if (current_class_.find("PhoneView") != std::string::npos &&',
     'if (diag_env("MINIANDROID_EXP062_TRACE") && current_class_.find("PhoneView") != std::string::npos &&')
sub2(22601, 'if (method_name.find("lambda") != std::string::npos || method_name.find("createView") != std::string::npos) {',
     'if (diag_env("MINIANDROID_EXP081_TRACE") && (method_name.find("lambda") != std::string::npos || method_name.find("createView") != std::string::npos)) {')
sub2(22611, 'if (current_class_.find("PhoneView") != std::string::npos &&',
     'if (diag_env("MINIANDROID_EXP061_TRACE") && current_class_.find("PhoneView") != std::string::npos &&')
sub2(22699, 'if (method_name.find("createView") != std::string::npos ||',
     'if (diag_env("MINIANDROID_EXP079_TRACE") && (method_name.find("createView") != std::string::npos ||')
sub2(22721, 'if (method_name.find("createView") != std::string::npos ||',
     'if (diag_env("MINIANDROID_EXP079_TRACE") && (method_name.find("createView") != std::string::npos ||')
sub2(22728, 'if (method_name.find("createView") != std::string::npos ||',
     'if (diag_env("MINIANDROID_EXP079_TRACE") && (method_name.find("createView") != std::string::npos ||')
sub2(22922, 'if (method_name.find("$r8$lambda") != std::string::npos || method_name.find("createView") != std::string::npos) {',
     'if (diag_env("MINIANDROID_EXP082_TRACE") && (method_name.find("$r8$lambda") != std::string::npos || method_name.find("createView") != std::string::npos)) {')
sub2(23032, 'if (method_name.find("$default$") != std::string::npos) {',
     'if (diag_env("MINIANDROID_EXP088_TRACE") && method_name.find("$default$") != std::string::npos) {')

# The 22699/22721/22728 gates open a paren that must close: conditions were
# `if (A || B || ...)` -> `if (FLAG && (A || B || ...)`. The closing paren
# sits on the line with the final `!= std::string::npos) {`. Fix those.
# 22699 block ends at 22705; 22721 block ends at 22723; 22728 block ends 22730.
sub2(22705, 'method_name.find("onBackPressed") != std::string::npos) {',
     'method_name.find("onBackPressed") != std::string::npos)) {')
sub2(22723, 'method_name.find("presentFragment") != std::string::npos) {',
     'method_name.find("presentFragment") != std::string::npos)) {')
sub2(22730, 'method_name.find("presentFragment") != std::string::npos) {',
     'method_name.find("presentFragment") != std::string::npos)) {')

# ────────────────────────────────────────────────────────────────────────
# F-NEW-398: complete the F084 state save/restore in try_recursive_invoke
# ────────────────────────────────────────────────────────────────────────
sub2(11013, 'auto saved_pc_visit_count = pc_visit_count_;',
     '''auto saved_pc_visit_count = pc_visit_count_;
        // F-NEW-398 (CONT-96): the F084 forward-progress state belongs to
        // the CALLER frame too. execute_method_internal's frame-entry law
        // clears all four members (pc_visit_count_, pc_branch_sig_,
        // frame_progress_epoch_, pc_epoch_checkpoint_); the recursive
        // invoke used to restore only the visit map, leaving the caller's
        // branch-signature map EMPTY and epoch/checkpoint at 0. Every
        // invoke-containing loop then re-recorded its branch signature as
        // a "first visit" after each call — frame_progress_epoch_ frozen
        // at 0 — and the 50001st visit classified a LIVE loop as a stall.
        // Fixture evidence (com.probe.perf1 benchVirtual): [SPIN-REGS]
        // v2=50000 — the loop counter ADVANCED — while the halt claimed
        // "Infinite loop ... visited 50001 times" (op_at_pc=0x34, if-lt
        // v2, v5). Save + restore the full F084 state set.
        auto saved_pc_branch_sig = pc_branch_sig_;
        auto saved_frame_progress_epoch = frame_progress_epoch_;
        auto saved_pc_epoch_checkpoint = pc_epoch_checkpoint_;''')

sub2(11818, 'pc_visit_count_ = saved_pc_visit_count;',
     '''pc_visit_count_ = saved_pc_visit_count;
        pc_branch_sig_ = saved_pc_branch_sig;               // F-NEW-398
        frame_progress_epoch_ = saved_frame_progress_epoch; // F-NEW-398
        pc_epoch_checkpoint_ = saved_pc_epoch_checkpoint;   // F-NEW-398''')

if fails:
    print("FAILURES:")
    for f_ in fails:
        print(" ", f_)
    sys.exit(1)

with open(PATH, 'w') as f:
    f.write('\n'.join(lines))
print(f"OK: {applied} edits applied")
