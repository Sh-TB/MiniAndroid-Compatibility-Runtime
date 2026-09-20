# S70 REPORT — RUNTIME UNDERSTANDING / ACTIVE SOURCE-LINKED DIAGNOSTIC ENGINE

Campaign question (user §"OUTPUT REQUIRED"): **after this campaign, when
MiniAndroid stalls on a new app or fixture, does the system actually help us
understand WHERE, WHY, through WHICH API/class, under WHICH semantic law, and
with WHAT blast radius?**

Answer: **yes — with named, measured limits** (below).

---

## 1. WHAT WAS UNKNOWN BEFORE (S69 end-state)

S69 produced a large *inventory*: 3,674 APIs × 213,251 call sites (static), a
372-root failure index, source pins for 10/11 APKs, per-app live traces. But
the S70 USE-first census (campaign Rule 2 — run the tools before building
anything) proved the inventory **could not answer the mandated questions**:

| mandated query | S69 state | verdict |
|---|---|---|
| "Why did this pixel become wrong?" | runtime_graph.json was a narrative chain, no per-hop evidence links | NOT ANSWERABLE |
| "Why is this API still stubbed?" | api_matrix status law existed, but… | MISLEADING (below) |
| "What breaks if I change this function?" | no function→API→consumer→fixture mapping | NOT ANSWERABLE |
| failure drill-down (§17 sections) | registry fields only, no auto bundle | NOT ANSWERABLE |
| silent-wrong vs explicit-stub | silent-wrong registry absent | NOT ANSWERABLE |

**Census finding (matrix integrity bug):** the S69 matrix labeled
`Canvas.clipRect`, `Canvas.scale`, `Color.rgb` as `UNSERVED` although the live
engine implements all of them (dalvik_engine.cpp:18290, canvas_shadow.cpp:1347
— verified in source). Root cause chain found in S70:

1. `engine_extractor.py` function parser could not parse `Class::method(...)`
   or multi-line signatures → parsed **19 of ~600** functions in the
   30k-line dalvik_engine.cpp;
2. guard extraction ran on **string-blanked** text (`""` everywhere) → served
   surface was **0 pairs by construction**;
3. therefore the SERVED-STATIC status layer was dead and implemented APIs
   fell through to UNSERVED — **priority intelligence was corrupted**;
4. additionally the live-status join under-counted (163 LIVE-IMPL recorded vs
   929 actual) because descriptor-keyed census keys never matched
   descriptor-less trace keys.

## 2. WHAT THE NEW SYSTEM CAN NOW EXPLAIN

Repaired + upgraded tooling (Rule 2: upgraded in place, no v2 duplicates):

- `engine_extractor.py` — brace-agnostic parser (multi-line signatures),
  variable-agnostic string-guard extraction on string-KEEPING bodies,
  nearest-preceding-class ordered pairing, shadow-binding law
  (`handles_class()` in headers × `m == "..."` in shadow .cpp), OR-aware
  ±4-line substring-class proximity law resolved to descriptor keys at
  graph-build time. **Served surface: 0 → 2,921 pairs.**
- `graph_build.py` → `docs/foundation/knowledge_graph.json` — one fused,
  queryable graph: **6,396 APIs** (929 LIVE-IMPL / 136 LIVE-STUB / 2,264
  SERVED-STATIC / rest EXERCISED-OK-or-SUSPECT with weak run corroboration —
  see status law below), 62 fixtures with per-assert verification, 384
  failures, 9 apps with pins + live summaries, upstream doc links, the
  engine's own `warn_noop()` deferred-behavior declarations as the silent-wrong
  surface.
- Status law v2 (honest reconciliation of bridge-trace blindness): interpreter
  intrinsics never reach the dispatch bridge, so "no trace + no guard" no
  longer means UNSERVED. New weak-evidence statuses: **EXERCISED-OK**
  (exercised by ≥1 SUCCESS run without bridge proof — weak, flagged) and
  **SUSPECT-FAIL-ONLY** (exercised ONLY by non-success runs — prime-suspect
  signal, e.g. `android.os.Trace` family, exercised only by stuck dooz).
- `graph_query.py` — the mandated queries, each answer citing its evidence:
  `api`, `why-stubbed`, `why-pixel`, `blast-radius`, `failure`, `gaps`
  (fan-out × risk ranking), `classify` (P0–P3 triage).
- `diagnose.py` — §17 drill-down: `diagnose <failure-id>` and
  `diagnose --live <app>` produce the 17-section bundle (FAILURE /
  FIRST DIVERGENCE / DEX / CLASS·METHOD / API / IMPLEMENTATION / CALLERS /
  CONSUMERS / STATE CHANGE / VIEW·LAYOUT / RENDER / UPSTREAM LAW / EXISTING
  TESTS / MISSING TEST / FANOUT / LIKELY ROOT CAUSE / EVIDENCE). Missing links
  print `GAP:` + what is required — **never invented (§25)**.
- `build_upstream_oracle.py` → `docs/foundation/upstream_oracle.json` — 7 law
  records (F-135 OpenJDK Double/Float family lines 1031/1048/1538/631/1324
  grep-verified in the pinned files; F-136 AOSP Context.java:945-978 +
  Resources.java:464-592 fetched and pinned; F-120 Button gravity) with
  implementation sites, fixtures, consumer counts.

## 3. ROOT CAUSES FOUND THIS CAMPAIGN

| id | root cause | law | status |
|---|---|---|---|
| (census) | served-surface extraction structurally broken (3 defects above) | — | FIXED (tool) |
| (registry audit) | S67/S69 F-numbers + R-NEW-388 + A7 never entered root_registry.json — registry↔docs split | single-source-of-truth | FIXED (registered: F-121..F-124, A2, A4, C3, F-135, R-NEW-388, A7; registry 372→384) |
| **F-136** | string resolution used the legacy name-keyed cache as PRIMARY (violating the ARSC-first law that F-080 already applied to colors); Resources formatted overload silently ignored args; `getText` unserved | AOSP Context.java:945-978 → Resources.java:464-592 (single resolution path) | **FIXED, full §17 cycle** |
| **R-NEW-389** | bouncy 81-px top-band (3,0)-(93,4) dark→yellow divergence across builds; **dispatch traces + ViewTree IDENTICAL**; per-binary determinism ×3 on both sides; cause NOT identified (paint-path layout sensitivity suspected, unproven) | — | **OPEN, P1** (blocks any "zero collateral" claim on bouncy) |

## 4. GENERIC FIX MADE — F-136 (full §17 cycle)

- **CONTRACT**: `Context.getString/getText` delegate to `Resources`;
  `Resources` resolves through the asset manager (ARSC) — any resid, any
  package; formatted overload == `String.format(raw, args)`.
- **UPSTREAM**: pinned `docs/upstream/aosp/CONTEXT_STRING_LAW.md` (fetched
  from googlesource main, exact lines cited).
- **IMPLEMENTATION** (no app special-casing): dalvik_engine.cpp
  - Resources block: ARSC-first (`rt.arsc().resolve_string`) → name-map
    fallback → `java_format_walk` for formatted overload; receiver-first
    resid law (F-080 pattern); `getText` served.
  - Context-family block: ARSC-first primary, legacy path strictly fallback.
- **FIXTURE**: `f53_getstring` — three law paths in one app (Context plain,
  Context formatted `%1$s/%2$d`, Resources direct). ViewTree carries the
  three resolved strings; row-ink regions asserted; independent PIL verifier.
- **PROOF**: f53 **PASS 5/5**; determinism ×3 byte-identical
  (`8c11659a7ca24512`).
- **REGRESSION**: foundation battery **23/23 PASS**; corpus A/B (fresh
  pre-F-136 build vs F-136, same recipes): **9/10 apps byte-identical**;
  bouncy delta → R-NEW-389 (registered, not hidden).
- **IMPACT**: `Context.getString` 130 static sites × 8 APKs (unote alone 111);
  `Resources.getString` 47 × 4; every formatted-string consumer unblocked.

## 5. HOW MANY REAL CONSUMERS IMPROVED

- f53 fixture: 3 of 3 law paths resolve (was: formatted overload returned the
  raw specifiers, `getText` unimplemented, non-seeded resIds returned "").
- Foundation battery: 23/23 (22 pre-existing + f53) — zero regressions.
- Corpus: 9/10 byte-identical; bouncy's delta is registered R-NEW-389 and its
  rendered pixels are otherwise the S69 golden (same frame nonwhite
  2,073,600; delta confined to the registered 81-px band).
- `Context.getSystemService` (84 sites × 6 APKs) corrected in the matrix from
  UNSERVED to SERVED-STATIC with real implementation sites (17466/24460) —
  priority intelligence repaired.

## 6. BEFORE/AFTER IMPACT MEASUREMENT (§PHASE 18)

Diagnose bundles for ten historical failures now reproduce the investigation
chain from records + graph in one command (evidence lines / GAP markers):

```
F-121 25/11   F-122 25/11   F-123 25/11   F-124 25/11
A2    25/11   A4    25/11   C3    25/11
F-135 41/8    F-136 42/7    R-NEW-388 41/7
```

Old path (session records): F-122 required a canvas-probe + pixel-census
investigation before the REC-MISS was even visible. New path: `diagnose F-122`
reproduces the chain (api status law → served site → f01/f08 fixtures →
consumer census) in one command; the GAP markers are exactly the parts the
records never captured (first_divergence pairs, per-failure state snapshots) —
honest deficits, now visible per-failure instead of invisible.

The remaining GAPs are the next tooling frontier: FIRST DIVERGENCE needs
per-failure expected/observed pairs recorded at REGISTRATION time (registry
schema v2), and RENDER needs per-frame draw-op provenance (op-level trace).

## 7. WHAT REMAINS, AND WHY (honest §22 closure)

- **R-NEW-389 (P1, open)** — bouncy 81-px band: dispatch-identical,
  ViewTree-identical, per-binary deterministic. Suspected paint-path layout
  sensitivity (UB class); requires renderer-side instrumentation. Until it
  closes, F-136's collateral claim is bounded as above.
- **LIVE-STUB tail (136)** — classified: **P0 = 10** (Enum.valueOf 260 sites,
  String.<init> 81, TextView.setTextSize 63, List.contains, Arrays.sort,
  ThreadLocal ×3, Random, LinkedHashSet), **P1 = 126** (getViewTreeObserver,
  Uri.parse, ByteOrder.nativeOrder, ByteArrayOutputStream, WindowManager…).
  None deleted for low usage (P2/P3 empty because LIVE-STUB status itself
  proves live reachability).
- **SUSPECT-FAIL-ONLY (1,797 APIs)** — exercised ONLY by partial-success runs;
  weak signal by design; the top of the list (Trace family) is dooz's stuck
  compose, not proven root cause (candidates ≠ verdicts, §0).
- **FOUNDATION COMPLETE = NO** (same verdict as S69, now with the gap surface
  *measured* instead of asserted): P0/P1 classes above remain; dooz compose
  remains its own campaign (§19 boundary).

## 8. EVIDENCE REGISTER

- `docs/foundation/knowledge_graph.json` (fused graph, status law v2)
- `docs/foundation/upstream_oracle.json` (7 law records, grep-verified)
- `docs/foundation/graph/{served_api,functions,class_graph,subsystem_graphs}.json`
- `docs/foundation/failure_index.json` (384 roots, canonical registry source)
- `docs/evidence/foundation/fixtures/f53_getstring/` + VERIFICATION.json
- `root_registry.json` (384 roots; R-NEW-388/A7/F-121..F-124/A2/A4/C3/F-135/
  F-136/R-NEW-389 registered with provenance)
- tools: `tools/architecture/{graph_build,graph_query,diagnose,build_upstream_oracle}.py`
- scripts: `scripts/s70_register_r388_a7.py`, `scripts/s70_register_f136_r389.py`,
  `scripts/s70_register_s67_s69_fixes.py`
