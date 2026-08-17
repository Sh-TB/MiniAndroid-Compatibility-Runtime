# Hypotheses

## H1: getFragmentStack returns null because fragmentStack field not initialized
- Status: OPEN
- Evidence: [RET] getFragmentStack val=0 type=8 (NULL_REF)
- Test: Check if ActionBarLayout constructor initializes fragmentStack

## H2: isEmpty on null returns void → if-nez treats void as non-zero → branches to PC 970
- Status: OPEN
- Evidence: Execution reaches checkLayout after getFragmentStack
- Test: Add per-PC trace to verify exact branch decision

## H3: D8 hybrid mode causes wrong instruction size → wrong PC advancement
- Status: OPEN
- Evidence: Manual disasm of PC 680-730 was unreliable (D8 hybrid goto/16)
- Test: Use AOSP-spec instruction sizes for disassembly

## H4: The bytecode at PC 684 is NOT invoke-interface isEmpty
- Status: OPEN
- Evidence: Raw cu=0x0b14 at PC 684 is op=0x14 (const), NOT op=0x72 (invoke-interface)
- Test: Properly decode instruction sizes from PC 680

## Rejected Hypotheses (from prior experiments)
- D8 inverts branch semantics: REJECTED (EXP-056)
- isClientActivated returns wrong value: REJECTED (returns 1 correctly)
- getIntent should return null: REJECTED (fixed in EXP-056)
