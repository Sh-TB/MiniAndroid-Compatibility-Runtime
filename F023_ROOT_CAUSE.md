# F-023 Root Cause — DOOZ M1/i.f NPE (Compose composition blocker)

## Reproduction (OBJ-1) — VERIFIED at HEAD 7dc70e9c
`MINIANDROID_DISPATCH_ATTACH=1 ./build/miniandroid run dooz.apk -o run/ -v`
→ PARTIAL SUCCESS, ComposeView children=0, framebuffer 0/2073600 non-white.
Unwind: M1/i.f pc=99 NPE → y1/j.getValue (lazy catch-all, rethrow) →
AbstractComposeView.c catch-all → rethrow → uncaught at MainActivity.onCreate
invoke_pc=109 → APP BOUNDARY unwind.

## Exact root cause (OBJ-3)
Obfuscated class map (dooz classes.dex, R8):
- LC1/f  = kotlin.coroutines.CoroutineContext (iface)
- LC1/f$a= CoroutineContext.Element (iface)   — declares getKey()LC1/f$b;
- LC1/f$b= CoroutineContext.Key (iface)
- LC1/a  = AbstractCoroutineContextElement    — getKey reads field i (the key)
- LC1/h  = EmptyCoroutineContext
- LC1/g  = the CoroutineContext.plus fold-lambda class (impls LL1/p = Function2)
- LW1/y  = Compose runtime element base (abstract class extends LC1/a)
- LJ     = AndroidUiDispatcher (extends LW1/y)
- LF/b0  = MonotonicFrameClock (iface) with DEFAULT METHOD getKey() → sget LF/b0$a.i (companion Key)
- LF/b0 impl K = AndroidUiFrameClock (extends Object, implements LF/b0; NO own getKey)
- y1/j   = SynchronizedLazyImpl holding AndroidUiDispatcher.MonotonicFrameClock

Chain: attach → ensureCompositionCreated → Recompressor ctx assembly →
y1/j.getValue → J$a.c (lazy init: Choreographer.getInstance + Handler.createAsync
+ J.<init> + K.<init>) → C1/f$a$a.c = Element.DefaultImpls.plus → K.o (fold) →
C1/g.k (fold lambda: checkNotNull(acc/element) OK; then `element.getKey()`
invoke-interface LC1/f$a.getKey with receiver = K) → MiniAndroid
execute_invoke_interface: (a) interface class no code, (b) receiver class by
NAME no getKey, (c) signature walk follows ONLY class_to_superclass_
(K → java/lang/Object → break) — IMPLEMENTS chain never consulted →
fall-through bridge_to_api STUB → null key → `acc.get(null)` →
LW1/y;.q(null) → Kotlin Intrinsics.checkNotNullParameter("key") → NPE pc=99.

## AndroidX contract (OBJ-2)
androidx.compose.runtime.MonotonicFrameClock: `interface MonotonicFrameClock :
CoroutineContext.Element { companion object Key : CoroutineContext.Key<...> }`
Element's `val key` compiles to a DEX DEFAULT INTERFACE METHOD on the
interface (key getter). Implementors MAY omit it (R8 keeps K without getKey).
Art resolution: invoke-interface consults the receiver's iftable (all
transitively implemented interfaces incl. default methods). kotlin.coroutines
CoroutineContext.plus law relies on element.getKey() during fold.
Version cross-check: dooz bundles Compose UI 1.x with this exact shape
(F/b0.getKey verified = sget companion + return).

## The missing MiniAndroid law (OBJ-3 classification)
DEX DEFAULT-INTERFACE-METHOD DISPATCH LAW:
invoke-interface resolution, after (a) interface-class code and (b) receiver
class+superclass chain fail, MUST walk the receiver's implemented-interfaces
set (direct interfaces per class in the extends chain, transitively through
super-interfaces, bounded) and dispatch a method matching the EXACT
descriptor with non-abstract code (default method).
Generic benefit: every Kotlin `interface ... : CoroutineContext.Element`,
every default-method interface in R8-minified APKs.

## Fix design (OBJ-4)
In execute_invoke_interface, after the existing signature walk, add an
interface-set walk (bounded depth) using dex_report class defs'
interface list. No DOOZ/Compose special-casing.
