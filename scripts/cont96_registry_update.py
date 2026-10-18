#!/usr/bin/env python3
"""cont96_registry_update.py — register the CONT-96 wave outcomes.

F-NEW-398: F084 forward-progress false halt on invoke-containing loops
  (try_recursive_invoke restored only pc_visit_count_; the callee's
  frame-entry clear left the caller's branch-signature map empty and
  epoch/checkpoint at 0, so every loop whose body calls anything froze
  frame_progress_epoch_ at 0 and died at the 50001st visit as a false
  stall. Fixture com.probe.perf1 benchVirtual: [SPIN-REGS] v2=50000 —
  the loop counter ADVANCED — while the halt claimed "Infinite loop".
  Fix: save/restore the full F084 state set; A/B proven (pre: F084 halt
  at 50001 visits + truncated fixture; post: 4/4 rows DONE, checksums
  byte-identical). Plus CONT-96 throughput hygiene:
  INFRA-DIAGENV-1 (per-op getenv cached by literal-pointer identity),
  INFRA-DIAGFIND-1 (always-on debug string::find prints env-gated),
  INFRA-F084-FLAT (per-pc map state -> flat arrays, swap save/restore),
  INFRA-METHODRES-MEMO ((dex,method_idx) -> name/class/proto/params
  memo — MUTF-8 decode + proto parse once per method).
"""
import json
import shutil

REG = 'root_registry.json'
MIRROR = 'canonical/root_cause_registry.json'

with open(REG) as f:
    reg = json.load(f)
roots = reg['roots'] if isinstance(reg, dict) else reg

by_id = {r['id']: r for r in roots}

def entry(new):
    if new['id'] in by_id:
        by_id[new['id']].update(new)
        return
    roots.append(new)
    by_id[new['id']] = new

entry({
    "id": "F-NEW-398",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "title": "F084 forward-progress law false-halted every invoke-containing loop at the 50001st visit: try_recursive_invoke restored only pc_visit_count_, leaving the caller's branch-signature map cleared and frame_progress_epoch_ frozen at 0",
    "layer": "interpreter/forward-progress",
    "root_cause": "execute_method_internal's frame-entry law clears all four F084 members (pc_visit_count_, pc_branch_sig_, frame_progress_epoch_, pc_epoch_checkpoint_). try_recursive_invoke saved and restored ONLY pc_visit_count_ across the recursive callee (EXP-052-era save set predates the F-NEW-084 signature law). After each callee return the caller's pc_branch_sig_ was EMPTY, so the loop's conditional branch re-recorded its operand signature as a first visit every iteration — frame_progress_epoch_ stayed 0 — and pc_epoch_checkpoint_ (also reset to 0 by the callee) equaled it, so the 50001st visit classified a LIVE loop as a stall. Fixture evidence (com.probe.perf1 benchVirtual, apk sha16 8cbe1d87b7a68cff): [HALT-LOOP] 'Infinite loop at PC=0x3 ... visited 50001 times' with op_at_pc=0x34 (if-lt v2, v5) while [SPIN-REGS] showed v2=50000 — the loop counter ADVANCED every visit; the signature mechanism could never have fired on a correct execution. Every app loop whose body calls any method (i.e. essentially every real loop) was exposed: the same frame shape as SvgHelper$ParserHelper.advance.",
    "fix": "try_recursive_invoke now saves and restores the FULL F084 state set (pc_visit_count_, pc_branch_sig_, pc_branch_sig_seen_, frame_progress_epoch_, pc_epoch_checkpoint_) alongside the existing EXP-052 saves. CONT-96 W3-A additionally converted the per-pc F084 state from std::map to flat vectors sized to bytecode_.size() (a red-black find/insert per instruction and a whole-map COPY per invoke before; swap save/restore now) with a seen-flag replicating the map's insert-vs-compare law — identical counting, signatures, window resets, halt messages, and dumps.",
    "evidence": {
        "fixture": "fixtures/cont96_perf_probe (com.probe.perf1, real aapt2/ECJ/D8; apk run/cont96/perf1.apk sha16 8cbe1d87b7a68cff)",
        "pre": "binary aa9ade61b147c12b: [F084] false halt in benchVirtual at 50001 visits (SPIN-REGS v2=50000); fixture run truncated at the 120s budget with only 2/4 rows",
        "post": "binary 79d93a6ada630e73: rows 4/4 verdict=DONE (charat 2690ms / chararray 438ms / virtual 3340ms / total 6474ms), HALT-LOOP count 0, checksums byte-identical to host-Java semantics (charat 3688000, chararray 31744000, virtual 14534196240)",
        "battery": "wall 12/12 MATCH (anchors byte-identical), goldens 4/4, negatives 19/19 (gate-A probe 98 PASS/1 INFO/0 FAIL), reinstall 8/8, MG-310 7/7, MG-150 3/3, selftests 13/13, F-NEW-376 70/70, sax1 PASS, clock1 4/4, clinit1 rows law-correct (UT2 NCDFE), swipe1 setup OK, c74esc containment OK, perf1 rows 4/4",
        "logs": "evidence/cont96/, run/cont96/"
    },
    "wave": "CONT-96"
})

entry({
    "id": "INFRA-DIAGENV-1",
    "status": "INFRA-LANDED",
    "priority": "P1",
    "title": "Diagnostic env presence-checks called std::getenv() per interpreter instruction / per method entry — an environ walk per opcode (arith-2addr macro WIDE_DIAG, post-switch F040_DIAG, invoke-family S24/CLASS_LAW/F141/F040 sites, execute_method_internal's 18 frame-entry sites)",
    "layer": "interpreter/diagnostics-hygiene",
    "root_cause": "60 hot-region sites re-walked environ on every execution; the ARITH_2ADDR_CASE macro (add/sub/mul-int/2addr — the highest-frequency opcode family in char-parsing loops) did it per arithmetic op. Precedent: the 14530-site F040 cache note already called this 'a measurable fraction of the 310K ins/s interpreter wall'; this wave completes that law engine-wide for the invoke family.",
    "fix": "diag_env(name) — process-lifetime cache keyed by the string-literal POINTER (all diagnostic sites pass literals; stable). Identical answers, env read at first use. 60 sites converted; value-using sites (find(getenv(...)), env[0]=='0') intentionally keep raw getenv.",
    "evidence": {"scripts": "scripts/cont96_hotpath_cleanup.py, scripts/cont96_apply_edits.py (73 verified edits)", "wave": "CONT-96"}
})

entry({
    "id": "INFRA-DIAGFIND-1",
    "status": "INFRA-LANDED",
    "priority": "P2",
    "title": "ALWAYS-ON debug stderr prints guarded by per-invocation string::find (EXP-062 PhoneView x2, EXP-061, EXP-081, EXP-079 x3, EXP-082, EXP-088, EXP-058 addFragmentToStack) — F-074 hygiene violation surviving in the invoke family",
    "layer": "interpreter/diagnostics-hygiene",
    "root_cause": "Unconditional substring scans per invoke (current_class_.find(\"PhoneView\") on EVERY invoke-virtual; method_name.find() chains on invoke-direct/static) plus unbounded stderr prints when the class matched.",
    "fix": "Gated behind cached diag_env flags (MINIANDROID_EXP058_TRACE / EXP061 / EXP062 / EXP079 / EXP081 / EXP082 / EXP088). Same format, bounded, S58-hygiene precedent. Behavioral find sites (shadow dispatch class laws, R$ resource law) intentionally untouched.",
    "evidence": {"scripts": "scripts/cont96_apply_edits.py", "wave": "CONT-96"}
})

entry({
    "id": "INFRA-METHODRES-MEMO",
    "status": "INFRA-LANDED",
    "priority": "P1",
    "title": "Per-invoke DEX table re-resolution: resolve_method_{name,class,proto}_for_dex re-decoded MUTF-8 strings and re-assembled the proto descriptor on EVERY call, and all four 35c invoke arms re-parsed proto param types per call",
    "layer": "interpreter/resolution",
    "root_cause": "The resolvers memcpy'd DexHeader/DexMethodId and rebuilt std::strings from raw DEX bytes per call (3-4 materializations per invoke), and each invoke arm called parse_proto_param_types on the freshly built descriptor. DEX tables are immutable after set_per_dex_raw_data_ — the work was repeated 1.33M times on the Telegram 30s gate.",
    "fix": "(dex_index, method_idx) -> {name, cls, proto, parsed params} memo (lazy fill, uncached originals byte-identical and used only by the fill); invoke arms build args from the memoized params. Out-of-range indexes keep exact uncached behavior.",
    "evidence": {"wave": "CONT-96", "measured": "tri.resolve phase 8.1G ticks -> ~4.8K ticks/call; fixture virtual row 3506->3340ms; telegram rate 341K->423K ins/s at the 30s gate"}
})

reg['roots'] = roots
if isinstance(reg, dict):
    json.dump(reg, open(REG, 'w'), ensure_ascii=False, indent=1)
else:
    json.dump({'roots': roots}, open(REG, 'w'), ensure_ascii=False, indent=1)

shutil.copy(REG, MIRROR)
print('registry now:', len(roots), 'roots; mirrored to', MIRROR)
