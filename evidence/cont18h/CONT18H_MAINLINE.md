# CONT-18h — MAIN LINE: F-265 decomposition wave 1 (arms a+b verified, arm (c) re-rooted, F-270 fixed)

Binary lineage: `8ee839e718877216` (CONT-18/18f) → `be95a47f797d3d99` (CONT-18g) → **`f882ca1832b955e3`** (CONT-18h; F-270 fix + F-265 arm-(c) diag extension).

Directive: 80% main campaign line (F-265 → F-267 tap gate), 20% other. This document records the main-line work.

## 1. Live state of the F-265 chain at HEAD

Reproduction: dooz canonical anchor invocation with `MINIANDROID_F141_DIAG=1 MINIANDROID_DRAW_WINDOW_TRACE=1` at `be95a47f797d3d99` (run/cont18h/dooz_f265).

Findings, link by link:

| F-265 recorded link | State at HEAD | Live evidence |
|---|---|---|
| (a) deferred-throw continues the throwing frame | **GONE** — the throwing frame aborts (ART-faithful) | `[SYNTH-EXC] ... → uncaught (deferred frame unwind + propagate)`; every cascade hop shows `uncaught (frame unwind + propagate)` or a handler jump |
| (b) catch-handler argument must be the real in-flight throwable | **WORKING** — handlers receive the real NPE | `[EXC-PROPAGATE] Ljava/lang/NullPointerException; caught at caller Lnb0;.n invoke_pc=84 handler=0x0x5b type=<catch-all>` with the true message carried through ([EXCEPTION] lines quote the same message at the handler) |
| measure pass dies mid-flight (Lzs.m unwind) | **STILL TRUE** | `[EXC-UNWIND] La; unwound Lzs;.m invoke_pc=0x4a depth=17` (and Lte1.f/Lse1.s/Lg.q/Lg.h/Lat.a trail), anchor = blank `d602648e8e401895` |
| first face = Lm7.<init> null-text | **NOT FIRED this run** — the death happens earlier in composition | no Lm7 null-text SYNTH-EXC in the log; Lvs0.c executed, Lkc.<init> constructed without the null-text NPE |

## 2. New first death face and its engine root (F-NEW-270)

Pre-fix chain (run/cont18h/dooz_f265):

```
[ROOT-059] null-recv routed to shadow law: Lhv0;.h     ← user class routed!
[ROOT-059] null-recv routed to shadow law: Lhv0;.d     ← self-call inside callee
[SYNTH-EXC] iget-null-recv: ... 'Lrh0;.d' ... method=Lhv0;.d pc=17 → uncaught
[EXC-PROPAGATE] ... caught at caller Lnb0;.n invoke_pc=84 handler=0x0x5b
... cascade ... → uncaught at MainActivity.onCreate → APP BOUNDARY unwind
```

Source-first identification (scripts/cont3_disasm_full.py, scripts/cont18h_newinst_xref.py, raw unit decode):

- `Lhv0;` extends `Lrh0;` — fields `d:I, a:[J, b:[I, c:[Ljava/lang/Object;` — a Compose-family **LongSet/ScatterMap** (`Lhv0.h(I,Object)` = put: pc=0 self-calls `d(I)`, then `aput` into `Lrh0.b`/`Lrh0.c`).
- The two ROOT-059 lines are ONE chain: code invoked `Lhv0.h` on a null receiver → routed (not thrown) → shadow `not_handled` → **real DEX body ran with this=null** → its `invoke-virtual Lhv0.d` (still this=null) → routed again → `d`'s body → `iget Lrh0.d:I` at pc=17 → wrong-site NPE **inside the callee** (ART throws at the invoke site, message "invoke virtual ... on null"), plus the paired silent-swallow of the `h` put.
- Law defect: `claims_class()` routing is ungated; ViewShadow's EXP-060 heuristic claims **every non-framework class** ("could be a View subclass; let dispatch() decide by method name"). `Lhv0;` is not a View. The route also existed only at invoke-virtual 35c (f141 sites at invoke-virtual/range, invoke-direct, invoke-super, invoke-interface never route) — format-inconsistent.

### Fix (main code)

`miniandroid/src/dex/dalvik_engine.h`: new `f141_is_framework_class()` prefix allowlist (Landroid/, Landroidx/, Ljava/, Ljavax/, Lkotlin/, Lkotlinx/, Lcom/google/, Lorg/xmlpull/, Lorg/json/) — the same domain the ViewShadow heuristic itself excludes; `miniandroid/src/dex/dalvik_engine.cpp` (invoke-virtual f141 site): route requires `f141_is_framework_class(declaring_class) && claims_class(...)`; ROOT-059 log line now carries `caller=` identity.

### Post-fix verification (run/cont18h/dooz_f270, dooz_f270b)

```
grep ROOT-059 → (zero lines; framework routes still lawful, none in dooz)
[SYNTH-EXC] f141-null-recv (deferred): ... 'Lhv0;.h' on a null object reference)
            method=Lnb0;.S pc=185 → uncaught   ← ART-faithful site + true caller
anchor: d602648e8e401895 (byte-identical to recorded)
```

## 3. Arm (c) root-cause progress → F-NEW-271

With F-270 fixed, the ART-honest trail names the exact next surface:

- Failing frame: `Lnb0;.S(I,I,Object,Object)` (CompositionImpl composeContent family) at **pc=185 (0xb9)**: `invoke-virtual Lhv0.h` on a null receiver.
- Source chain: `pc=0xa3 iget-object v2 ← this.j:Lqb0` → `pc=0xa5 if-eqz` (non-null j, branch not taken) → `pc=0xb2 iget-object v4 ← v2.e:Lhv0` → `pc=0xb9 invoke-virtual Lhv0.h` on v4=null.
- **The corruption**: the F141-DIAG register window at the failing site shows `v2:t5/o0` — **STRING_REF/0 in a register whose DEX value must be `:Lqb0;`** (t7=OBJECT_REF, t8=NULL_REF; t5=STRING_REF). An alien-typed value:
  - slips past `f141_is_null_receiver` (covers NULL_REF / OBJECT_REF-0 / INT32-0 — not STRING_REF/0), so the 0xb2 field read answers NULL_REF instead of throwing at 0xb2,
  - which then legitimately dies at f141 on 0xb9.
- Bytecode coherence PROVEN (payload-aware scans + raw unit decode):
  - `Lnb0.j` written only by iput-object(0x5b) sites in `Lnb0.S` (pc=0x147/0x609-family) — register-coherent with `new-instance v11 Lqb0` (0xf9) → `invoke-direct {v11,v2,v5} Lqb0.<init>` (0x144) → `iput-object v11 → v0.j` (0x147); second site likewise (0x394/0x3a1).
  - Both `Lqb0.<init>` invocations RAN (`[TRI-F040] Lqb0;.<init> argc=3 ... caller=Lnb0;.S depth=13` ×2, objects **o3108/o3131**) with healthy inner chains (`Lhv0;.<init>` ×2 + `Arrays.fill` through `Lhv0.f`).
  - `Lqb0.<init>` unconditionally iputs a fresh `Lhv0` into `e` (pc=0x3b, fidx 6617); `Lvx1.<init>` likewise for its `a` (fidx 8989) — no null-by-design fields.
- Therefore the corruption is engine-side state on `o2838` (a DIFFERENT Lnb0 instance than the two healthy constructions' owner): either a wrong-typed default written by the R-NEW-414 initializer-materialization / F-NEW-251 bare-vs-qualified field-key machinery, or `o2838`'s j was never DEX-initialized and its default is typed wrong. Suspects ranked: (i) `materialize_init_default` bare-name store vs qualified read split-brain for single-letter R8 fields, (ii) an engine default-answer path (`make_string("",0)` family) leaking into an object field slot, (iii) o2838's construction path skipping `<init>` while leaving a string-typed zero default in j.

Registered as **F-NEW-271 (CLASSIFIED, P0)** with the next arms: heap-dump the failing iget's source object; audit R-NEW-414/F-NEW-251 store keys for single-letter fields; verify Lnb0 ownership of the two healthy constructions.

## 4. F-267 dependency note

F-267 (Compose tap hit-test bridge) remains gated by placed-node bounds. The live evidence still shows `isPlaced=false` family behavior (blank anchor + Lzs.m unwind), so F-267's probe stays PENDING until F-265's arm (c) chain is closed. No F-267 work attempted this wave — dependency honest.

## 5. Regression at f882ca1832b955e3 (full battery, fresh installs)

| Suite | Result | Recorded CONT-18g state |
|---|---|---|
| anchors ×3 (dooz, microtimer, unote, gmdice, opencalc, chess) | **18/18 MATCH byte-identical** | 18/18 |
| fcol (K1–K18) | **18/18** | 18/18 |
| f259 (F259-A..G) | **7/7** | 7/7 |
| f259g (F259-H..O) | **12/13** (known honest L row) | 12/13 |
| f266 (F266-A..F) | **6/6** | 6/6 |
| f268 (exception laws) | **12/12** | 12/12 |
| gate_a negatives | **19/19** | 19/19 |
| reinstall matrix | **8/8** | 8/8 |
| skill selftest | **13/13** | 13/13 |

Scripts: `scripts/cont18h_regression.py` (probe battery), `scripts/cont18_anchors.sh` (anchors), `scripts/cont18h_newinst_xref.py` (payload-aware new-instance xref tool).

## 6. Registry / queue

- F-NEW-270 → ROOT-CAUSED-FIXED (registry 578→579).
- F-NEW-271 → CLASSIFIED (registry →580; queue 256 queued / 324 terminal).
- F-NEW-265 evidence appended: arms (a)+(b) verified at HEAD; arm (c) re-rooted to F-NEW-271; measure-pass death still reproduced.
