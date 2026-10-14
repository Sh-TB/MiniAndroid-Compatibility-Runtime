# R-NEW-361 — S51 forensic increment: live-table metadata dump + write-path trace

Status after S51: **OBSERVED-FAIL — root cause structurally characterized; fix pending.**
All evidence below produced at S51 HEAD (post fd51d119 + probe commits), dooz v18
(SHA `d81292cd…` re-verified), run `timeout 420s --execution-mode real-dalvik`.

## 1. Reproduction (S51)

* v18: EXIT=124, `[HALT-LOOP] Infinite loop at PC=0x1c in Lh/r;.c (visited 50001,
  op_at_pc=0x54 iget-object)` + `[SYNTH-EXC] aput-oob length=7 index=613985991
  method=LP/v$a;.c pc=28` — signature IDENTICAL to S49/S50 records (index value
  varies run-to-run, consistent with identity-hash provenance).

## 2. NEW instrumentation (S51, env-gated, compact — committed to runtime)

* `MINIANDROID_R361_HALT_DUMP=1` → HALT-time `this`-object field dump to
  `/tmp/r361_halt_dump.json` (bounded: 64 fields, 40+4 array elems, 2 levels).
* `MINIANDROID_R361_TRACE=1` → `[R361-MW]` metadata aput-wide writes from the
  ScatterMap family (≤96) + `[R361-HC]` hashCode() call-sites from same (≤64).

## 3. The live failing table (first direct observation in campaign history)

```json
{"class":"Lh/r;","method":"c","pc":28,"obj_id":5051,
 "fields":{
   "a":{"len":2,"elements_sampled":["0xff00000000000000"]},
   "b":{"len":7},"c":{"len":7},
   "d":7,
   "f":0}}
```

* metadata word0 = `0xff00000000000000` = **Sentinel shl 56 with NO Empty (0x80)
  bytes anywhere** ("ghost bytes" of S49 finding D, now precisely characterized).
* metadata word1 (the clone/continuation word) **absent from the heap object**
  even though len=2 — probe fetch of `metadata[1]` returns the engine default (0).
* `b`/`c` (keys/values) len=7, `_size=7`, `growthLimit=0`.

## 4. Upstream semantic laws (androidx.collection ScatterMap.kt, androidx-main)

```
EmptyGroup = longArrayOf(0x80808080808080FF /*Sentinel,Empty×7*/, -1L)
// "Since our lookups always fetch 2 longs from the array, we make sure
//  we have enough [sentinels]"                      (ScatterMap.kt L176-184)
convertMetadataForCleanup():
  metadata[lastIndex-1] = (Sentinel shl 56) or (metadata[lastIndex-1] and 0x00ff_ffff_ffff_ffffL)
  metadata[lastIndex] = metadata[0]        // ← MANDATORY CLONE WORD (L606)
```

Two violated laws, now proven ON THE LIVE OBJECT:

* **LAW-A (clone word)**: final metadata word must exist and mirror word0 so
  every SWAR group fetch (`metadata[i] ushr b | metadata[i+1] shl (64-b)`,
  L828) is defined. Dead table: word1 missing → straddle reads 0 →
  `maskEmpty()==0` forever → probe can never reach the sentinel →
  `probeOffset` never advances (single-group wrap) → **the spin**.
* **LAW-B (Empty fill)**: every metadata word carries Empty (0x80) bytes except
  written h2 slots. Dead table: 7× 0x00 (neither Empty nor legal h2) + lone
  sentinel at byte 7 (MSB).

## 5. Write-path trace (healthy vs dead — same run, same classes)

Healthy tables (written by `Lh/r;.d` = init/resize path and `Lh/r;.c` = insert):
```
[R361-MW] caller=Lh/r;.d arr=obj#908  len=2 idx=0 val=0x80808080808080ff  ← EmptyGroup[0] EXACT
[R361-MW] caller=Lh/r;.d arr=obj#3384 len=2 idx=0 val=0xff80808080808080  ← capacity-7 sentinel+Empty fill
[R361-MW] caller=Lh/r;.c arr=obj#3320 len=2 idx=0 val=0xff80018025801c80  ← h2 stores (0x25, 0x1c, 0x03 …)
[R361-MW] caller=Lh/r;.c arr=obj#3320 len=2 idx=1 val=0x8080018025808080  ← word1 maintained
```
Dead table: NO `[R361-MW]` line ever targets its object id; its word0 pattern
(`Sentinel shl 56` over zeros) matches a `convertMetadataForCleanup`-class
sentinel-restore landing on a **zero-default array whose convert loop and clone
store never landed** — the healthy path proves `.d`/`.c` write different array
objects than the one later probed (compose-snapshot clone churn class,
S49 NEXT-2/3).

## 6. Refined NEXT (supersedes S49 (E))

1. Instrument **who allocates** the metadata array the dead table points to
   (NEW_ARRAY/filled-new-array site + frame stack).
2. Verify `java.util.Arrays.fill/ copyOf/ copyInto` long[] handlers for
   end-index handling (capacity+7 shr 3 vs metadata.size) against the upstream
   resizeStorage/convertMetadataForCleanup sequence.
3. Extend r361_metadata_probe fixture with the `convertMetadataForCleanup`
   SWAR sequence (inv/add/ushr/and chain) — the only upstream law not yet
   JVM-compared.

## Companion evidence (SHA256 pinned in proof registry)

* `s51_r361_halt_dump.json` — live-table dump (verbatim, 268 B)
* `s51_r361_trace.txt` — first 30 [R361-MW]/[R361-HC] lines (verbatim, 2.4 KB)

---

## 7. S51 RESOLUTION — root cause proven, fix landed

The probes in §2 (RINVOKE / RSTEP / FILL / FILLENTRY / FILLSHAPE /
DEEP-REFUSE + allocation ring) closed the chain this session:

```
[R361-RINVOKE] Ln/a;.r arr=obj#5052 t=7 depth=80 caller=Lh/r;.d
[R361-DEEP-REFUSE] depth=80 <various> (silent-bridge fallback)
[R361-MW] caller=Lh/r;.d arr=obj#5052 len=2 idx=0 val=0xff00000000000000   ← the dead word0
```

* `Ln/a;.r` = Kotlin stdlib fill helper: `Intrinsics.checkNotNullParameter`
  + `Arrays.fill(data, 0, len, 0x8080808080808080L)` (method_ids 16083 →
  M1/i.f, 14069 → Arrays.fill([J I I J), disassembled from the v18 DEX —
  tool: scripts/s51_dump_hrx.py).
* The helper was invoked at recursion depth EXACTLY 80 = MAX_RECURSION_DEPTH
  (EXP-053 backstop: ~80KB C++ stack per interpreter frame on the 8MB main
  stack). try_recursive_invoke refused it; bridge_to_api has no `Ln/a;.r`
  handler → SILENT VOID (no REC-MISS, no exception — invisible for 4
  sessions). Arrays.fill never ran. The zero-default metadata array then
  received ONLY the sentinel write (§3/§4 state machine: convert of a
  filled table gives 0xFF80..80 — the observed 0xFF00000000000000 is
  sentinel-over-ZEROS) — LAW-A/LAW-B violated by omission, not corruption.
* The healthy-trace writes in §5 are reinterpreted: `.d` writing
  0x80808080808080ff into obj#908 is initializeTable(capacity=0) aliasing
  the EmptyGroup template (benign same-value rewrite), NOT corruption.

FIX (committed at S51):

* `main.cpp`: `cmd_run` executes on a dedicated 512MB-stack pthread
  (real ART keeps interpreted frames off the native stack; ~80KB/frame is
  an engine-local cost — 512 × 80KB ≈ 40MB worst case).
* `dalvik_engine.h`: MAX_RECURSION_DEPTH 80 → 512.
* `dalvik_engine.cpp`: `[R361-DEEP-REFUSE]` — every depth-guard refusal is
  now printed (bounded 16); a silent fallback can never hide again.

POST-FIX VERIFICATION (clean run, no trace env, v18 d81292cd):

* ENGINE_EXIT=0, **Status: SUCCESS — the launch completes for the first
  time in campaign history** (pre-fix: HALT-LOOP timeout, never reached
  the end). Zero HALT-LOOP events; 56 fill invocations, all depths < 80.
* Battery: ALL PASS (94 stages) at the fix head.
* HONEST REMAINING: the first framebuffer is still blank (0 non-white
  pixels — matches the historical blank record). Compose UI rendering is
  the NEXT frontier; Dooz runtime-playable certification remains PENDING
  on that work. The dead-table spin is FIXED.
