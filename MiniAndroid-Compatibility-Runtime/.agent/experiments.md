# Experiments

## EXP-050: Return value propagation fix
- Result: +136 unique methods (200→336)

## EXP-051: Shadow Registry + Thread Identity
- Result: 7 shadows, 0 HALT, 339 methods

## EXP-052: Exception diagnostic + Thread identity
- Result: 339 methods, exception tries table captured

## EXP-053: Catch-all handler + overload fix
- Result: 343 methods, catch-all jump works

## EXP-054: Memory safety + Collection semantics + class init
- Result: 421 methods, 52 CLASS_INIT, CollectionShadow with real state

## EXP-055: Return value propagation + OBJECT_REF(0)=null
- Result: 445 methods, isClientActivated returns 1

## EXP-056: getIntent() null fix + CollectionShadow null handling
- Result: 442 methods, getIntent returns non-null, D8 inversion rejected

## EXP-057: IN PROGRESS
- Target: Reach getClientNotActivatedFragment()
- Blocker: getFragmentStack returns null → isEmpty on null → jumps to checkLayout
