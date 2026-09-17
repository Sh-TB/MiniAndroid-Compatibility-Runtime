#!/usr/bin/env python3
# S56 registry update:
#  - R-NEW-344 (dooz v23 recomposer/first-frame): refine the face with the
#    post-F-083/F-084 evidence chain (ScatterMap full-table probe spin;
#    halt containment shipped as F-084; next steps ranked).
#  - F-084 registered (HALT-RETURN containment law, root cause -> law -> proof).
import json

REG = 'root_registry.json'

with open(REG) as f:
    reg = json.load(f)

roots = reg['roots']

by_id = {}
for r in roots:
    by_id.setdefault(r.get('id'), []).append(r)

# --- R-NEW-344 refinement -------------------------------------------------
r344 = by_id.get('R-NEW-344', [])
if r344:
    r = r344[0]
    r['title'] = (
        "dooz23 first frame blank: post-F-083 the run reaches Recomposer/"
        "ControlledComposition; the current face is an androidx.collection "
        "ScatterMap insert into a FULL table (capacity 15, size 15, zero "
        "EMPTY metadata bytes) whose probe loop never terminates — the "
        "second grow (free-budget e==0 at size 14) entered the R8-inlined "
        "resize but computed newCapacity=15 instead of nextCapacity(15)=31 "
        "and re-filled the same arrays after convertMetadataForCleanup"
    )
    r['observed'] = (
        "S56 refinement (post F-083 + F-084): R-NEW-361 no longer appears in "
        "v23. MainActivity.onCreate now drives Recomposer (Lnb0;) / "
        "ControlledComposition (Lwo;) dirty-scope ScatterMap (Lbw0;) "
        "machinery. Full lifecycle traced (MINIANDROID_FIELD_TRACE=e + "
        "MINIANDROID_META_STORE_TRACE, obj o2658): <init>(6) -> f(6) cap 7 "
        "budget e=6 -> 6 inserts -> grow at e=0 via f(15) (resize #1 "
        "CORRECT: new metadata o4644, cap 15, e=loaded(15)-6=8) -> 8 more "
        "inserts (size 14) -> grow check at e=0 entered the R8-inlined "
        "resize: convertMetadataForCleanup ran (bit-exact vs upstream: "
        "0xfefefefefefe80fe written at d pc=235) and 14 entries were "
        "re-inserted INTO THE SAME ARRAYS (no new allocation, all "
        "meta-stores arr=o4644) -> resize epilogue wrote e=0 = "
        "loaded(15)-14, i.e. newCapacity stayed 15 (must be 31) -> table "
        "15/15 with zero EMPTY bytes -> probe spin (HALT-LOOP 2.4M insns at "
        "d pc=28 iget-object)."
    )
    r['root_cause_hypothesis'] = (
        "TWO engine-level laws: (1) PRIMARY (open): the second grow's "
        "nextCapacity computation (Lmg1;.b = mul-int/lit8 #2 + add-int/"
        "lit8 #1 -> cap*2+1) or its branch into f() mis-executed — the "
        "epilogue budget e=loaded(newCap)-14=0 pins newCap=15; cap-7 grow "
        "(nextCapacity(7)=15 via f) worked, so the failure is "
        "value/branch-specific, not a blanket lit8/2addr break. (2) "
        "SECONDARY (FIXED as F-084): the halted callee fed a stale "
        "last_invoke_return_ to the caller's move-result — the garbage "
        "slot index -733270216 face."
    )
    r['next'] = (
        "(1) Trace Lmg1;.b invocation + return values around insert #16 "
        "(MINIANDROID_FIELD_TRACE scope is insufficient for static helpers "
        "with single-letter fields — extend the S56 locals-diag to the "
        "Lmg1; frame). (2) Compare the cap-7 grow flow (e==0 -> f(15) "
        "RAN) vs the cap-15 grow flow (e==0 -> no f) at the d() pc=128 "
        "if-nez branch +531 — the divergence pinpoints the mis-executed "
        "op. (3) After the root fix, expect resize(31): new metadata "
        "LongArray(5) + values[31], budget e=loaded(31)-14=27-14=13."
    )
    r['evidence'] = (
        "docs/evidence/s56_dooz23/F084_EVIDENCE.md (full chain + key "
        "traces) + SHA256SUMS over the pre/post-fix stderr captures "
        "(s56_dooz23_refix). Deterministic: the pre-fix stderr is "
        "byte-stable across runs (same 11712384-byte log reproduced)."
    )

# --- F-084 registration ----------------------------------------------------
if not any(r.get('id') == 'F-084' for r in roots):
    roots.append({
        'id': 'F-084',
        'title': (
            "HALT-RETURN containment law: a callee frame that exits via the "
            "loop-detector/instruction-budget halt has NO defined return "
            "value — the engine must not deliver the stale "
            "last_invoke_return_ to the caller's move-result"
        ),
        'status': 'IMPLEMENTED+TESTED',
        'priority': 'P0',
        'discovered': 'S56',
        'fixed': 'S56',
        'evidence': (
            "Pre-fix: dooz v23 Lbw0;.d (ScatterMap probe) halted after 2.4M "
            "instructions; caller Lbw0;.a pc=8 consumed the stale word as a "
            "slot index (-733270216) -> aput-oob -> AIOOBE -> APP BOUNDARY "
            "death in MainActivity.onCreate. Fix: discriminate the abnormal "
            "halt (halted_ && !halted_on_return_ — every NORMAL return also "
            "sets halted_) and escalate as deferred VirtualMachineError "
            "(F084-HALT-RETURN). Proof: battery ALL PASS 96/96 (the first "
            "attempt without the discriminator broke corpus stages 59-63 "
            "and was fixed pre-commit); simplestopwatch rc=0 with zero F084 "
            "fires; dooz v23 face changed from garbage-index AIOOBE to the "
            "honest halt propagation. docs/evidence/s56_dooz23/."
        ),
    })

reg['summary'] = reg.get('summary', '')
# update open frontiers count text if present
text = json.dumps(reg.get('summary', ''))
reg['baseline_head'] = reg.get('baseline_head', '')

with open(REG, 'w') as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)

print(f"roots now: {len(roots)}")
print("R-NEW-344 refined; F-084 registered")
