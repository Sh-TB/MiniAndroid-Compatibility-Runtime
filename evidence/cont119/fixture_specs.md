# CONT-119 fixture specs (registered, ready for next code wave)

## FIX-449 — play_billing MessageInfo two-count-sources probe (F-NEW-449)
- Root (decoded): runtime lacks the protobuf-lite **RawMessageInfo → MessageSchema walk**. The generated
  `n2;.r` builds the schema by splitting the MessageInfo info-string on `\u0000`; count source (1) = the
  integer count token inside the info string; count source (2) = the `Object[]` entries length.
  At HEAD the walk consumes all 11 p3 field tokens (10 real fields + aux) then reads `entries[11]`
  as the rotated-loop terminator → `[S36-AOOB] len=11 idx=11` (o5042, 11 STRING_REF stores, walk rows
  R337/EXP093 in run/c116_tg_s36.log). Ready-source grounding: protobuf java/core MessageSchema.java
  (buffer[] = 3 ints per field: field#, type+offset, presence; objects[] metadata; RawMessageInfo
  string-parse vs StructuralMessageInfo FieldInfo[]).
- Probe: minimal generated-lite trio (one proto with 10 string fields) compiled with the real
  ECJ/D8 toolchain (precedent: fixtures/cont112_lawderef, c449); assert: (a) our walk parses exactly
  count-token fields, (b) terminator read stays in-bounds or is absent by contract, (c) schema buffer
  layout matches 3-ints-per-field.
- Unblocks: 16 PARTIAL telegram tasks sharing this root.

## FIX-TTT — tictactoe native SIGSEGV (CONT-118 W-06)
- 3/3 deterministic rc=139 at HEAD bd7e7b97 (run/c119/tictactoe{1,2,3}.log), S100-CRASH-FORENSICS
  native frames pinned: #0 off=0x40f26e (our binary), #1 host addr. Death context:
  `SharedLibraryLoader.isLoaded` → `mapLibraryName` → native frames (libGDX native-load chain,
  gdx-native dlopen family — bouncy proved the identical chain renders menu when dlopen succeeds).
- Probe: GATEA-NATIVE-style probe calling `SharedLibraryLoader.load` on a stub lib with an unresolved
  symbol vs a valid lib; assert runtime bridges dlopen errors as UnsatisfiedLinkError (graceful) and
  never segfaults; then bisect which mapLibraryName output path triggers the crash.

## FIX-D12 — wrong-thread CalledFromWrongThreadException law (D-12 gap)
- Ready-source: Robolectric ShadowView.checkThread — "Only the original thread that created a view
  hierarchy can touch its views." Law: a View-tree mutation from a non-creator thread raises
  CalledFromWrongThreadException; record thread identity at view creation (attachInfo.handler looper),
  compare at mutate-time, synth-exc with AOSP message, env-gated to avoid noise.
- Probe: fixture app posting a background-thread TextView.setText; assert synth-exc type+message and
  that the app's handler.post fallback recovers (AOSP behavior).

## FIX-D05 — protobuf unknown-field path (D-05 gap)
- Ready-source: protobuf-lite UnknownFieldSchema contract: unknown field bytes are captured into an
  unknownFields sink and re-emitted on re-serialization; never dropped silently.
- Probe: proto with a field number absent from the schema; assert parse keeps the bytes (byte-equal
  round-trip) — currently no runtime handling exists (grep zero hits, CONT-117 D-05).
