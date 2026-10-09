# CONT-30 — THE FRAME-1 GROUP-DELETION ROOT FIXED + THE REFLECTION ANNOTATION NEVER-NULL LAW:
# ZERO-PAYLOAD RE-ENTRANT DISPATCH IS UPSTREAM-LEGAL

Wave: CONT-30. Opens at the divergence CONT-29 pinned as the next wave's fix
target: `GapComposer.end()` differ group-accounting across skipped inner
scopes ("the differ deletes slot groups the re-execution did NOT re-visit
while they were LIVE — skip-advance accounting law").

**VERDICT UP FRONT (no success inflation):** the CONT-29-pinned root is
ROOT-CAUSED-FIXED as **F-NEW-286** — the divergence was never inside the
differ's own accounting; the engine's M3-19 active-cycle guard was STUBBING
the legal nested `recomposeToGroupEnd()` calls on the same composer (the
skip-advance), so `end()`'s upstream tail loop saw an un-advanced reader and
deleted the live destination groups. A second root (**F-NEW-287**,
Method.getAnnotations never-null + annotation-proxy type identity) was fixed
en route. The oracle frame MOVED deterministically (`b270ff040b3601dc`
uniform fef7ff → `b5a7a35d5fe0564b` ×3 uniform 2C2C2C — the
post-recomposition state), the two uncaught NPE faces of the interim binary
are GONE, and the next divergence is proven + registered (**F-NEW-288**, the
TextUnit value-class spin in the text-measure chain). Real app-owned
CONTENT pixels: NOT claimed this wave — the chain advanced one full stage
(deleted-content → post-recomposition text-measure frontier), Track A
honestly PARTIAL.

---

## 0. TRUTH LOCK (Phase 0)

| item | value |
|---|---|
| git HEAD | `fafa9aab` == origin/main (CONT-29); fast-forwarded from the stale local CONT-10-era clone — the container had lost CONT-11..29; **the whole lineage was recovered from the remote, zero local divergence** (`git rev-list --count origin/main..HEAD` = 0 before ff) |
| baseline binary | clean rebuild from HEAD source: **BYTE-EXACT `d35a60d43f83331c`** (134,656,256 bytes == CONT-29 record) |
| oracle APK | rebuilt from surviving inputs (54 AARs + kotlinc-dist + `tmp/cont12_oracle_build/dex/`): `run/w8/oracle12.apk` **8,233,173 bytes == the recorded size**; rclasses.jar 168,155 bytes == recorded; `view_tree_lifecycle_owner = 0x7f05005a` == recorded id (sha16 ebb8729f7091a0b8 — size+id+behavior identity, the known zip-drift honesty rule) |
| oracle baseline ×3 | rc=1, screenshot `b270ff040b3601dc` ×3 byte-identical == CONT-29 exactly |
| dooz APK | sha16 `299eab21ac8b3c61` == registry |
| registry at lock | 594 rows; F-NEW-286/287/288 absent (dedup-checked) |
| new tools | `scripts/cont30_disasm.py` (androguard DalvikVMFormat ground-truth disassembler), `scripts/cont30_build_probe.sh` |

## 1. THE CHAIN — RUNTIME-PROVEN LINK BY LINK (pre-fix)

METHOD-IN census (`MINIANDROID_METHOD_TRACE=1`, 248,647 lines,
`run/cont30/trace1`):

```
191331 skipCurrentGroup                        (invalidations NON-empty arm)
191369 recomposeToGroupEnd call#1 REAL
191423   RecomposeScopeImpl.isInvalidFor
192253   RecomposeScopeImpl.compose(3953)
192265     NavHost$lambda$80 → NavHost re-runs
192274       startReplaceGroup
192344       RecomposeScopeImpl.start → setSkipped  (AnimatedContent scope SKIPPED)
192478       GapComposer.skipToGroupEnd
192498       [M3-19-CYCLE] recomposeToGroupEnd STUBBED (depth 18, lifetime_calls=2)
192502     endGroup → 192504 end(isNode=false)
192530       SlotReader.isGroupEnd == FALSE
             → tail loop: recordDelete ×2 → Operation$RemoveCurrentGroup ×2
194065   (second scope — same pattern)
194206   [M3-19-CYCLE] STUBBED (depth 19, lifetime_calls=3)
         → second deletion pair; apply executes RemoveCurrentGroup ×2
```

The stub key was `Landroidx/compose/runtime/GapComposer;.recomposeToGroupEnd()V#2149`
— receiver-only, zero payload parts.

## 2. SOURCE-FIRST LAW (upstream/s43, compose-runtime 1.11.4)

`GapComposer.kt` (line refs from the committed sources):

```kotlin
override fun skipToGroupEnd() {
    if (!inserting) {
        currentRecomposeScope?.scopeSkipped()
        if (invalidations.isEmpty()) skipReaderToGroupEnd()
        else recomposeToGroupEnd()        // ← LEGAL same-composer re-entry
    }
}
override fun skipCurrentGroup() {
    if (invalidations.isEmpty()) skipGroup()
    else { ...; startReaderGroup(...); recomposeToGroupEnd(); ... }
}
private fun recomposeToGroupEnd() {
    while (firstInRange != null) { ...; scope.compose(this); ... }
    if (recomposed) reader.skipToGroupEnd() else skipReaderToGroupEnd()
    // ↑ EVERY exit path advances the reader to the group end
}
private fun end(isNode: Boolean) {
    ...
    while (!reader.isGroupEnd) {          // ← the tail loop fired ONLY
        recordDelete(); skipGroup();      //   because the reader never
        changeListWriter.removeNode(...)  //   advanced (the stub)
    }
}
```

The guard's own refinement history states the law it violates: F-098/S122/
S137/F-076 all append payload identity so "the guard only ever fires LESS
often; genuine same-argument cycles still collide". For a zero-payload
method the engine has NO evidence that a re-entrant call is the same
computation — upstream distinguishes nestings by the slot-table reader
position, invisible to any argument-identity key.

## 3. THE FIXES (generic, zero app knowledge)

### F-NEW-286 — zero-payload re-entrant dispatch executes real DEX
`dalvik_engine.cpp`, M3-19 guard only: count payload identity parts
(`m3_payload_parts`: F-098 object args excl. receiver, S122 primitives,
S137 class refs, F-076 static object args); the stub fires ONLY when
`m3_payload_parts > 0`. Zero-payload keys NEVER stub — real DEX executes;
`[RECURSION-LIMIT]` backstop still bounds genuine unbounded recursion (loud,
observable). Payload-distinct keys keep the stub (S22 law: same-payload
re-entry IS same-computation evidence). dooz M3-19 firings 5 → 1 (the
remaining one is a payload-distinct key — the law working).

### F-NEW-287 — Method.getAnnotations never-null + annotation type identity
`dalvik_engine.cpp`, three generic pieces:
1. `Method.getAnnotations()/getDeclaredAnnotations()` law — resolves the
   parsed `annotations_directory_item method_annotations` table (the
   F-NEW-191 authority), materializes every runtime-visible annotation as a
   proxy, answers an EMPTY array when none — NEVER null (the oracle's
   `LocalSavedStateRegistryOwnerKt.<clinit>` probe then completes
   upstream-faithfully; the NPE face is gone).
2. The new proxies carry the `__annotation_proxy__` marker (the F-087c
   contract — previously only the Class.getAnnotation bridge stamped it).
3. F-087c gains the `Annotation.annotationType()` arm (OpenJDK law: the
   Class token of the annotation interface) — identity-comparable against
   app-side `Mark.class` literals.

## 4. POST-FIX RUNTIME STATE (honest)

| item | value |
|---|---|
| oracle frame | `b5a7a35d5fe0564b` ×3 byte-identical, deterministic (uniform 2C2C2C dark surface — the post-recomposition theme state; NOT content) |
| clinit NPE face | GONE (0 rows) |
| interim getDensity NPE face | GONE after F-NEW-287 (it was the spin's fabricated unwind) |
| remaining faces | 3 benign deferred CNFEs (kotlin-reflect/TestMainDispatcher — recorded honest misses) + **F-NEW-288** |
| F-NEW-288 | the TextUnit value-class packed-value chain spins to `[RECURSION-LIMIT]` depth-2048 inside `Density.toPx--R2X_6o` / `TextUnit.getType-UIouoOA` / `TextUnitType.unbox-impl` / `getSp` / `equals-impl0` — first divergence proven, primitive not yet identified (candidates: packed-long bit ops, FontScaling interface-default dispatch, mangled-name overload selection) |
| real app-owned content pixels | NOT achieved (no claim) |

## 5. REGRESSION GATE (final binary `b84114cd6f8bad1d`)

| gate | result |
|---|---|
| anchors ×3 | **24/24 BYTE-IDENTICAL** (dooz `d602648e8e401895`, microtimer, unote, gmdice, opencalc, tttdeluxe, flappycow, g2048) |
| probe battery | fcol 140/0, f259 49/0, f259g 84/7-known, f266 42/0, f268 96/0, fnew253 147/0 — == CONT-28/29 records EXACTLY |
| new probe | fixtures/fnew286_probe (real aapt2/ECJ/D8) **10/10 PASS** |
| binary lineage | `d35a60d43f83331c` (HEAD rebuild) → `5a88d092af28e74f` (+F-NEW-286) → `cc58632f7c401e86` (+F-NEW-287) → `b84114cd6f8bad1d` (final: +proxy marker/annotationType) |

Probe rows (fixtures/fnew286_probe, `run/cont30/probe286d`):
R1 nested zero-payload re-entries all execute (visits==3) · R2 real nested
returns + v1v2v3 trace · R6 clean depth unwind · R3/R3b/R3c/R3d/R3e
getAnnotations never-null + len==1 + annotationType()==Mark.class (and
getAnnotation F-191 parity) · R4 plain → non-null EMPTY · R5 payload-distinct
re-entry still terminates.

## 6. STATUS LEDGER

| item | status |
|---|---|
| Phase-0 truth lock (HEAD/binary/APKs/registry dedup) | TESTED |
| CONT-29 frame-1 group-deletion root reproduced (b270ff040b3601dc ×3) | TESTED |
| Root F-NEW-286 root-caused + fixed + probed | TESTED |
| Root F-NEW-287 root-caused + fixed + probed | TESTED |
| F-NEW-288 first divergence proven + registered | OBSERVED (CLASSIFIED, not fixed) |
| Oracle real app-owned CONTENT pixels | NOT ACHIEVED (no claim — Track A PARTIAL) |
| Full regression at final binary | TESTED (this file §5) |
