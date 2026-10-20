# CONT-116 RESULT — «یوز فیل قطار» · F-NEW-465 ROOT-CAUSED-FIXED (two ctor-dispatch laws: Constructor.newInstance varargs+descriptor forwarding at BOTH shim sites + F-NEW-464's inverted dispatch condition corrected) · F-NEW-449 decode deepened (array identity + complete walk profile) · full battery green, zero drift · registry 780 (no inflation)

**Wave:** CONT-116 (elephant batch) · **Base:** origin/main `492df09a` (CONT-115) · **Final binary:** `3ecd381cda214dcd` (lineage: `9b5d38f5` → +Constructor varargs/descriptor ×2 shims → +F464 condition fix) · **Registry:** 780 id-unique (no new roots) · **Evidence:** `evidence/cont116/evidence.json`

## Lever 1 — F-NEW-465 ROOT-CAUSED-FIXED (fixture-first decode → minimal generic fix)

- **Decode (runtime forensics, all env-gated diagnostics that already exist):** tower3d's post-CONT-114 death = `Array.add pc=4 ARR-LEN-NULL` at AndroidLauncher.onCreate invoke_pc=25. Allocation-site pinning (`MINIANDROID_ALLOC_TRACE`) proved TWO distinct shell sources: obj#347 (pc=0 frame=453 — shim layer) and obj#393 (`R414-INIT-DEFAULT` materialized at pc=0 frame=0 — the materializer). FIELD-TRACE (`items`) proved obj#38's ctor DID store items — the shells were specific dispatch faces, not a general ctor failure.
- **Root (a) — Constructor.newInstance drops its varargs:** the hot shim (34079) unboxed nothing in the ancestor line and dispatched `"<init>"` with NO descriptor; the cold shim (54705) never fired. The no-descriptor heuristic can cross-bind same-arity overloads (libGDX Array has `<init>(I)V` AND `<init>(Lcom/badlogic/gdx/utils/Array;)V`). **Fix:** both shims now unbox the `Object[] initargs` (heap `__array_length__`/`array[i]` law), select the `<init>` whose parameter count matches + primitive-shape tie-break, and dispatch through the F-023 exact-descriptor authority path. A DEX-defined dispatch miss is now LOUD (`[F465-CTOR-MISS]` with pinned allocation site — the named lever).
- **Root (b) — F-NEW-464's condition was INVERTED (CONT-116 find):** `materialize_init_default` gated the ()V execution on `!class_has_no_arg_ctor(...)` — i.e. it ran the ()V body only for classes that HAVE NO ()V ctor (a ctor that does not exist) and skipped every class that has one. libGDX Array has `()V` → the materialized `lights` Array (obj#393) stayed a zero-field shell forever. **One-condition fix:** run the ()V ctor exactly when it exists (the F-NEW-274 gate upstream already refuses fabrication for ctor-less classes — honest null path preserved).
- **Bracket (honest):** pre-fix death chain `R414-INIT-DEFAULT → Array.add pc=4 ARR-LEN-NULL → AndroidLauncher APP-BOUNDARY` (3/3 deterministic) → post-fix `ARR-LEN-NULL` **absent**, IGET-MISS `keys:<none>` **2 → 0**, FIELD-TRACE shows `Array.<init>` storing `items` on every materialized shell. The run advances to a NEW deeper death: `Array.<init> getClass-null` in the attribute copy-ctor chain (registered as the continuation fixture target — no false closure; the visible face stays `11a38a5a` = the draw-op frontier).

## Lever 2 — F-NEW-449 decode deepened (stays CONFIRMED_OPEN_GAP, no false closure)

- OOB array identified: **o5042 `[Ljava/lang/Object;` len=11** (`[S36-AOOB]`), built by **exactly 11 STRING_REF stores idx 0..10** (`[EXP093-APUT]`); filled-new-array EXCLUDED (98 FNA rows, all `[I`, all later); copyOf not in the window.
- Walk profile complete: **20 `[R337-UNSAFE]` rows = ALL 11 p3 instance fields consumed** (10 real: zze/zzg/zzh/zzi/zzf/zzj/zzk/zzl/zzm/zzn + aux zzd read 10× interleaved), then `entries[11]` = the **post-field terminator read**. The engine's `s2.b` parse demands one more entry than the constructed array carries.
- Residual fork (needs full n2.r disassembly or an ART reference run): which 12th store ART executes, or whether the terminator demand is string-derived. Fixture per CONT-107 plan: MessageInfo-shape probe asserting two count sources agree. Both my disassembler copies desync on this method — the fixture-first gate stands.

## Battery at 3ecd381c — zero unadjudicated drift

wall **4/4 MATCH** (dooz `d602648e` / opencalc `d5f3c7b5` / unote `90a67cc1` / microtimer `bbd350b6`) · chess `a0319686` / tower3d `11a38a5a` / solitaire `ba50a4d2` byte-identical · c448 **6/6** rows · c449 **4/4** rows · goldens **4/4** · negatives **19/19** (canonical gate_a probe store regenerated per the documented CONT-111 remedy; interim 9/19 = documented fresh-container sequence artifact) · reinstall **8/8** · MG-310 **7/7** · MG-150 **3/3** · selftest **13/13**

## Honest pendings (named next)

1. **tower3d next layer:** the attribute copy-ctor `getClass`-null chain (post-F465 death; fixture = DirectionalLightsAttribute copy-path probe).
2. **F-NEW-449 fixture:** MessageInfo-shape two-count-sources probe; the n2.r full disassembly tooling (both dumpers desync) is part of the lever.
3. **F-NEW-256 family:** compose AndroidCanvas bridge (dooz draw frontier — unchanged).
4. **D8-optimized zero-default ints:** `Array.size` IGET-MISS rows are the field-default law surface (engine answers 0 — verify against DEX spec in the same fixture).

(issue #364 CONT-116, elephant batch, fixture-first, zero-drift wall)
