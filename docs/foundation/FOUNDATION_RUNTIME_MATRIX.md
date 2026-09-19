# FOUNDATION_RUNTIME_MATRIX — canonical (S67)

Verified via f38 (object identity), f45 (exceptions), f39_44 (null/arrays/
multi-dim/primitive arrays/reflection/super/interface/static-init/field-init/
wide), f26 (ctor/field-init order), f21/f27 (click→state→render),
f27_nav (startActivity semantic). Text evidence from ViewTree dumps =
executed DEX results, not logs alone.

| Contract | Status | Evidence |
|---|---|---|
| Object identity (==, aliasing, field mutation through alias) | PROVEN | f38 "IDENT=true,false,v=42" |
| Null checks / null compare | PROVEN | f39 "NULLOK" |
| Arrays (new/multidim aget/aput OOB guard) | PROVEN | f45 CAUGHT_AIOOBE; f39 arr values |
| Primitive arrays (long[]/int[][] descriptors, F-119 family) | PROVEN | f39 larr/grid |
| Reflection (getMethod on real DEX, F-029 law) | PROVEN | f39 "REFLOK" |
| Superclass dispatch (virtual override) | PROVEN | f39 "SUB" |
| Interface dispatch | PROVEN | f39 area=9 |
| Static initializer (<clinit>) | PROVEN | f39 staticInit=11 |
| Field initializers + ctor-before-onCreate order (F-118) | PROVEN | f26 "INIT=6,5"; f27 <init> dispatch |
| Wide values (long/J 64-bit, F-042) | PROVEN | f39 wide=4000000001 |
| Exceptions (try/catch/finally, propagation) | PROVEN | f45 CAUGHT_AIOOBE |
| startActivity == initial-Activity semantics | PROVEN (S67 F-121 fix) | f27: click→G08 launch→B tree rendered (2073273 px change, B bg #CCEEFF); pending-launch was previously consumed only at final boundary |
| startService / Fragment lifecycle | PARTIAL | Fragment superclass table exists; no dedicated micro-test yet (queued WAVE 8) |
| Compose foundation (snapshot/LayoutNode) | BLOCKED | Dooz LayoutNode measure-precondition ISE (registered, own campaign) |
| Interpreter opcode coverage | PROVEN (breadth) | 95 distinct Opcode:: sites + family macros (ARITH_*/ARRAY_*/IF_*/INVOKE_*); batch fetch/decode |
| Determinism | PROVEN ×3 | 6 fixtures frame+ViewTree SHA identical across 3 runs |
