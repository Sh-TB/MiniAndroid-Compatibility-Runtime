# ROOT DISCOVERY GUIDE — how MiniAndroid locates a root candidate
# (MASTER CAMPAIGN 4 — permanent methodology, §13/§34 of the campaign brief)

The runtime must be able to answer, for ANY failing APK:

```text
APK
 ↓
class
 ↓
method
 ↓
DEX PC
 ↓
opcode / API
 ↓
runtime bridge
 ↓
missing semantic
 ↓
ROOT CANDIDATE
```

— not just "timeout". This document is the operating manual for the
discovery pipeline, written from the F-044 battle (the worked example in
docs/research/ROOT_DISCOVERY_EVIDENCE.md).

---

## 1. The telemetry layers (all env-gated, zero cost when off)

| Layer | Gate | What it shows |
|---|---|---|
| `MINIANDROID_METHOD_TRACE` | 1 | every DEX method entry/exit — the execution spine |
| `MINIANDROID_ARG_TRACE` | 1 | invoke arguments with TAGS (t7=ref, t1=int, t8/t9=bool/null, t2=wide) |
| `MINIANDROID_FIELD_TRACE` | 1 | every iget/iput with value+tag — object-graph truth |
| `MINIANDROID_TRACE_COMPOSE` | 1 | compose-class dispatch attempts (COMPOSE-TRY/MISS) |
| `MINIANDROID_DISPATCH_ATTACH` | 1 | **BEHAVIORAL**: enables the attach dispatch (UC009). Default off for golden protection. Without it the Compose frontier is silently bypassed — a run can look SUCCESS while never reaching the frontier |
| `MINIANDROID_F044_DIAG` | 1 | the F-044 battle probes: law-method returns + register-file dump (the precedent for targeted, capped probes) |
| `[INVOKE-MISS]` / `[REC-MISS]` | always-on (capped) | every API the DEX asks for that has no handler — the fail-soft inventory |
| `crash.log` + F-016 honesty | always-on | uncaught exceptions past the app boundary; rc=0 + blank frame is NEVER success |

**Rule (§43):** `rc=0` + "SUCCESS" + 0 non-white pixels = PARTIAL, never
success. The framebuffer is the truth: SHA256 + non-white count + 3-run
reproducibility.

## 2. The discovery loop (used for F-044; reuse verbatim)

1. **Reproduce honestly.** Fresh run at current HEAD, record rc, final
   exception chain, framebuffer SHA, non-white count.
2. **Ground truth the failure site.** Disassemble the failing method from
   the real APK DEX (androguard; per-instruction). NEVER fix from the log
   alone.
3. **Read the law from the bytecode.** The DEX is the specification of
   what the app expects the runtime to do.
4. **Instrument, don't guess.** Env-gated, capped probes AT the law's
   return/branch sites (the F044-DIAG precedent: method returns, then a
   register-file dump). Compare the engine's live values against the law
   decoded in step 3.
5. **Name the root generically.** Not "dooz crashes at X" but "per-frame
   context Y leaks across recursive frames" / "API Z is fail-soft where
   the spec defines semantics".
6. **Fix the law, not the symptom.** No app/class/package special-casing.
7. **Micro-proof.** ECJ+D8 real-DEX fixture, 7-band visual golden,
   3-run byte-identical determinism.
8. **Regression.** Full battery (currently 88 stages) MUST stay green.
9. **Real APK re-run.** The lighthouse APK re-executed; metrics before/
   after recorded; the frontier moved or did not — report honestly.
10. **Document + commit** with the law, evidence chain, and commit hash.

## 3. Root-candidate classes to scan for (§18 sweep targets)

- `REC-MISS` / `INVOKE-MISS` entries (fail-soft where semantics exist)
- `return false / 0 / null / void` bridges with no law comment
- env-gated BEHAVIORAL switches that change execution shape (document each
  one — a gate that silently bypasses the frontier is a discovery hazard)
- per-frame engine context set at entry but not restored across recursive
  invokes (the F-044 class — audit EVERY such field)
- value tags that leak across opcode boundaries (F-028/F-030/F-044 family)
