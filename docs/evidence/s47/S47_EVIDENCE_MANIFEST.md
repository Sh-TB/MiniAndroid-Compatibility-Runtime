# S47 EVIDENCE MANIFEST (briefing §23 format)

## R-NEW-363 — LifecycleRegistry.forwardPass / SafeIterableMap iterator re-entry

```text
ROOT-ID:        R-NEW-363
CLAIM:          M3-19-CYCLE active-invoke key omitted the method descriptor;
                javac bridge -> real covariant dispatch (same name, same
                receiver, protos next()Ljava/lang/Object; vs
                next()Ljava/util/Map$Entry;) was stubbed as a false cycle;
                the real body never advanced mCurrent; hasNext() stayed true;
                forwardPass spun to HALT-LOOP.
STATUS:         VERIFIED-FIXED (F-056)
APK:            org.secuso.privacyfriendly2048_100.apk
APK SHA256:     02c799d3d582669daf2acf920093c68d2933f60aa937bb72fa2a805557233fe8
COMMAND:        ./build/miniandroid run -o run/s47_2048_repro --execution-mode=real-dalvik apk_cache/s46/org.secuso.privacyfriendly2048_100.apk
FIRST DIVERGENCE: [M3-19-CYCLE] ...next#195 re-entered lifetime_calls=2 at the
                bridge's inner exact-descriptor dispatch of next()Map$Entry
UPSTREAM SOURCE: androidx.arch.core core-common 2.2.0 SafeIterableMap.java
                (IteratorWithAdditions implements Iterator<Map.Entry<K,V>>;
                upstream/SafeIterableMap.java committed as oracle); JLS
                15.12.4.5 bridge methods; ART ArtMethod identity
SEMANTIC LAW:   ArtMethod identity = (class, name, proto INCLUDING return
                type); two same-name methods with different protos are two
                distinct vtable slots; bridge delegation is legal, terminating
FIX:            F-056: m3_active_key += method_descriptor (try_recursive_invoke,
                dalvik_engine.cpp) — one line; genuine same-(class,name,proto,
                receiver,args) cycles still stubbed; MAX_RECURSION_DEPTH backstop
REGRESSION:     TicTacToe §29 ALL PASS (8 checks); battery 90/92 (EXT-01/02 only);
                dooz v23 0 AIOOBE 0 HALT-LOOP 0 M3-19-CYCLE
FRAME SHA:      run/s47_2048_fix1/screenshot.png (run completes; no timeout)
TRACE SHA:      run/s47_2048_repro_stderr.log (pre-fix, 55.3 MB, archived),
                run/s47_2048_fix1_stderr.log (post-fix)
RAW EVIDENCE:   scripts/s47_next_dispatch.py (all-dex raw-DIS disassembler);
                pre/post stderr logs archived with SHA256 in
                docs/evidence/ARCHIVE_MANIFEST.json
```

## R-NEW-364 — FragmentManager host-attach law (fragment 1.5.4 / activity 1.8.0)

```text
ROOT-ID:        R-NEW-364
CLAIM:          The fragment 1.5.4 host attach is a CONTEXT-AVAILABLE LISTENER
                (FragmentActivity.<init> line 140) fired by
                ComponentActivity.onCreate pc=7
                (ContextAwareHelper.dispatchOnContextAvailable). An EXP-044-era
                package-specific stub silenced that dispatch ("collection
                iteration not supported" — obsolete: shadow iterators, R342
                COWSET, F-056 keys) so mHost stayed NULL and the first
                transaction threw ISE "FragmentManager has not been attached
                to a host." at FragmentManager.ensureExecReady.
STATUS:         VERIFIED-FIXED (F-057: obsolete stub removed; real DEX executes)
APK:            org.secuso.privacyfriendly2048_100.apk (sha 02c799d3…)
COMMAND:        MINIANDROID_S47_TRACE=1 ./build/miniandroid run -o run/s47_2048_trace ...
FIRST DIVERGENCE: probe [S47-TOP] try_recursive_invoke returned via the stub
                before any class lookup while listeners=o55 was already populated
UPSTREAM SOURCE: androidx fragment 1.5.4 FragmentActivity.java:116-141,
                FragmentController.attachHost:116-119; androidx activity 1.8.0
                ComponentActivity.onCreate (performRestore ->
                dispatchOnContextAvailable -> super.onCreate)
SEMANTIC LAW:   framework lifecycle dispatch executes real DEX; a stub needs
                its own reproducible loop evidence
FIX:            F-057 (dalvik_engine.cpp): removed the ContextAwareHelper
                dispatchOnContextAvailable stub
REGRESSION:     §29 ALL PASS; battery 90/92; dooz v23 unchanged frontier, 0 new
                failure classes
RAW EVIDENCE:   run/s47_2048_trace_stderr.log ([S47-VIRT]/[S47-TOP]/[S47-TRI]
                probe chain: dispatchOnContextAvailable -> iterator ->
                FragmentActivity$$ExternalSyntheticLambda3.onContextAvailable ->
                attachHost -> attachController bc=369)
```

## R-NEW-365 — check* identity law (Preconditions.checkNotNull)

```text
ROOT-ID:        R-NEW-365
CLAIM:          androidx.core.util.Preconditions.checkNotNull(T,Object) is
                IDENTITY on non-null input and throws NPE on null. An
                EXP-058-era stub ("overload loop") returned false -> bridge ->
                NULL, destroying the checked reference at every checkNotNull(x)
                call site. The guarded "overload loop" is exactly what F-056
                descriptor-aware cycle keys fixed generically.
STATUS:         VERIFIED-FIXED (F-058: obsolete stub removed)
APK:            org.secuso.privacyfriendly2048_100.apk (sha 02c799d3…)
COMMAND:        MINIANDROID_S47_TRACE=1 ./build/miniandroid run -o run/s47_2048_trace ...
FIRST DIVERGENCE: [S47-TRI] FragmentController;.<init> a1=NULL — the host
                reference decayed to NULL across checkNotNull + move-result +
                check-cast inside createController
UPSTREAM SOURCE: androidx.core 1.13.0 Preconditions.checkNotNull (identity law)
SEMANTIC LAW:   check* helpers are identity-on-non-null; a stub must never
                destroy a checked reference
FIX:            F-058 (dalvik_engine.cpp): removed the Preconditions
                checkNotNull stub
REGRESSION:     §29 ALL PASS; battery 90/92; dooz v23 0 new failure classes
RESULT CHAIN:   ISE count on the SplashActivity chain 14 -> 6 -> 0; post-fix
                probe: FragmentController.<init> a1=o129(HostCallbacks),
                attachController recv=o131, ensureExecReady mHost=o129 (HOST
                ATTACHED), full attach -> transaction -> AppCompat decoration
                reached
RAW EVIDENCE:   run/s47_2048_trace_stderr.log, run/s47_2048_fix3_stderr.log
```

## R-NEW-366 — 2048 next frontier (OPEN, registered)

```text
ROOT-ID:        R-NEW-366 (OBSERVED-FAIL)
FRONTIER:       with mHost attached, the SplashActivity chain reaches fragment
                transactions + AppCompat decoration and hits an independent
                exception layer:
                (a) IAE "Window callback may not be null"
                    WindowCallbackWrapper.<init> pc=12
                (b) ISE "Restarter must be created only during owner's
                    initialization stage" SavedStateRegistryController
                    .performAttach pc=43 (attach-timing law)
                (c) ISE "You need to use a Theme.AppCompat theme (or
                    descendant)" AppCompatDelegateImpl.createSubDecor pc=404
                (d) ISE "LifecycleOwner ... already garbage collected"
                    LifecycleRegistry.sync pc=94
EVIDENCE:       run/s47_2048_fix3_stderr.log THROWABLE-MSG lines
                855112/855362/855391/855522/855554
NEXT ATTACK:    per item; each is a distinct semantic law (window-callback
                identity, saved-state attach timing, theme attribute
                resolution, lifecycle GC-guard). Upstream sources: appcompat
                1.7.0, fragment 1.5.4, lifecycle 2.x — fetch before any fix.
```

## Dooz R-NEW-362 — re-verified at S47 fixes (unchanged frontier)

```text
ROOT-ID:        R-NEW-362 (OBSERVED-FAIL, re-verified)
STATUS:         0 M3-19-CYCLE, 0 AIOOBE, 0 HALT-LOOP at F-056/057/058
FRONTIER:       Ljb1;.f pc=21 IAE "Can't put value with type null into saved
                state" -> caught catch-all at Lfb1;.a invoke_pc=77 ->
                APP BOUNDARY at MainActivity.onCreate invoke_pc=317
EVIDENCE:       run/s47_dooz_fix_stderr.log; APK io.github.yamin8000.dooz_23
NEXT ATTACK:    saved-state registry value/type resolution (unchanged from S46
                registration; the S47 laws neither fix it nor regress it)
```

## TicTacToe anchor (§29) — re-verified

```text
9/9 clicks: PASS (§29 script) · X→O→X alternation: PASS · X WINS: PASS ·
deterministic replay: PASS (all 10 frames byte-identical, 613cfccc0f27…)
GATE: bash tests/fixtures/tictactoe_golden/validate_tictactoe_golden.sh build/miniandroid
```
