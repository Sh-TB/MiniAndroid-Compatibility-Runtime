# PASS3_OPCODE_AUDIT — engine opcode table vs independent AOSP reference

Method: `scripts/audit_opcode_table.py` (embedded canonical Dalvik table from
AOSP art/libdexfile dex_instruction_list + dalvik-bytecode.html) compared
name-by-name and value-by-value against `src/dex/dalvik_engine.h`.

## BEFORE this pass (at 272f216c)
- 11 SHIFTED names (whole lit8 family +3; REM_DOUBLE_2ADDR +1).
- 19 mismatched bytes — real bytecode 0xD8..0xE2 mis-dispatched:
  0xD8 add-int/lit8 -> SHL_INT_LIT16 (invented opcode), 0xDA mul-int/lit8 ->
  USHR_INT_LIT16 (invented), 0xDB div-int/lit8 -> ADD_INT_LIT8, etc.
- REM_DOUBLE_2ADDR (0xD0) collided with ADD_INT_LIT16 (0xD0).

## AFTER this pass
=== NAME-BASED CHECK (engine constant vs AOSP value) ===
  shifted names: 0

=== VALUE-BASED CHECK (what actually dispatches at each byte) ===
  0x06: AOSP=MOVE_WIDE_16             ENGINE=-
  0xA5: AOSP=USHRT_LONG               ENGINE=USHR_LONG
  0xC5: AOSP=USHRT_LONG_2ADDR         ENGINE=USHR_LONG_2ADDR
  0xD1: AOSP=RSUB_INT                 ENGINE=RSUB_INT_LIT16
  0xE2: AOSP=USHRT_INT_LIT8           ENGINE=USHR_INT_LIT8
  mismatched bytes: 5

## Residual deltas (COSMETIC ONLY — no dispatch impact)
- 0x06 MOVE_WIDE_16 alias not present in engine constants (opcode unused by dispatch; noted in KNOWLEDGE_RECONCILIATION §9).
- USHR_LONG / USHR_LONG_2ADDR / USHR_INT_LIT8: engine spelling "USHR" vs AOSP list macro "USHRT" — same opcode, same semantics.
- 0xD1 RSUB_INT_LIT16 (engine) = AOSP rsub-int — same opcode; name kept for the lit16/lit8 symmetry.

Verdict: ZERO semantic table shifts remain (user master request §6 satisfied).
