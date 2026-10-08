# CONT-20 — F-NEW-271 CLOSED: the null-element representation leak

Binary lineage: `b4937c81aba0998c` (CONT-19) → **`b6ee41e77acb88ec`** (CONT-20; F-271 root fix + F271-COLL diag).

Directive: investigate F-NEW-271 as a GENERIC runtime root — reproduce the
exact first divergence, audit the heap/field representation, apply the
source-first semantic law, prove genericity BEFORE patching, minimal generic
fix, runtime proof + cross-target regression. No Compose modification, no
Dooz-specific rule, no exception suppression.

---

## A. First divergence (exact, evidence-backed)

| Item | Value |
|---|---|
| APK | `io.github.yamin8000.dooz_23.apk` sha256 `299eab21ac8b3c61…` |
| Engine | b6ee41e77acb88ec (pre-fix b4937c81aba0998c); commit 0b019608+ |
| Failing frame (old face) | `Lnb0;.S(I,I,Object,Object)` pc=185 `invoke-virtual Lhv0.h` on null |
| First INCORRECT state | `Lnb0;.p pc=1553` stored `STRING_REF ""` into `Lnb0;.j:Lqb0;` on o2838 — **before** any of the recorded pc=163/0xb2/185 chain ran |
| Store source | `v3` = result of `ArrayList.remove(size-1)` at `Lnb0;.p pc=1537` on list **o2839** (field `Lnb0;.i` of composition o2838) |
| Who filled the list | `Lnb0;.u pc=4` (`i.add(this.j); this.j = p1` — enqueue-current-holder idiom): real `Lqb0` holders o3108/o3131 AND **six legal `NULL_REF` elements** (`a1:t8/o0`) |
| Served value (pre-fix) | `t5/o0 ("")` — a fabricated String |
| Served value (post-fix) | `t8/o0` — **typed null** (ART/OpenJDK law) |
| Expected semantic | OpenJDK `ArrayList.remove(int)` returns the stored element AS null; the consumer's `check-cast` (null passes) + `if-eqz` handle it — no crash, by design |
| Masking defect (secondary) | `execute_check_cast` is a documented optimistic pass (no CCE) — it let the fabricated `""` pass as `Lqb0`. Kept as a separate known gap (F-268 family scope); NOT on the fixed path anymore |

Key evidence lines:

```
[F271-READ]  Lnb0;.S pc=163 field=Lnb0;.j : Lqb0; answered STRING_REF len=0 str=""
             recv#2838 readkey=Lnb0;->j declarer=Lnb0; dex_defined=1 heap_cls=Lnb0;
[F271-WRITE] Lnb0;.p pc=1553 field=Lnb0;.j : Lqb0; <- STRING_REF len=0 str=""
[F271-COLL]  add   recv_id=2839 a1:t7/o3108 (real Lqb0)   caller=Lnb0;.u pc=4
[F271-COLL]  add   recv_id=2839 a1:t7/o3131 (real Lqb0)   caller=Lnb0;.u pc=4
[F271-COLL]  add   recv_id=2839 a1:t8/o0   (NULL_REF) ×6  caller=Lnb0;.u pc=4
[F271-COLL]  remove recv_id=2839 a1:t1/o0 -> served t5/o0("")  caller=Lnb0;.p pc=1537   ← pre-fix
[F271-COLL]  remove recv_id=2839 a1:t1/o0 -> served t8/o0      caller=Lnb0;.p pc=1537   ← post-fix
```

The registered suspicions are resolved:
- **NOT** `materialize_init_default`/field-key split-brain: the qualified read
  `Lnb0;->j` HIT a genuinely stored value; the heap machinery faithfully
  stored and returned what the shadow channel handed it.
- **NOT** `make_string` default-answer leak into the slot.
- **ROOT**: the CollectionShadow null-element encoding (kind 2 + `""`) is
  **lossy** — indistinguishable from a genuine empty-string element — and the
  remove serve materializes it as `STRING_REF/0`. CONT-18h's "only two writers
  of j" was incomplete: the third writer is `Lnb0.p pc=1553` (found by
  `cont3_disasm_full.py`, which aligns with the engine decode).

## B. Semantic law

| Aspect | Content |
|---|---|
| Local implementation (before) | `lawb_classify_arg`/add tails: NULL_REF or zero-ref object → `kind=2`, `elem_strings=""` ("documented null-element representation"); serve sites (`lawa_remove_index`, `lawa_serve_slot`, `slot_to_arg`, iterator next): `kind==2` → `handled_string(sval)` → `STRING_REF/0` |
| Violated invariant | OpenJDK `ArrayList` "permits all elements, including null" — `remove(int)`/`get(int)` return **the stored element**; a null element comes back as **typed null**, never as a `String` object. ART: `move-result-object` yields a null register; `check-cast` null-pass; consumer `if-eqz` takes the null branch |
| Authoritative reference | OpenJDK `java.util.ArrayList` (`elementData` + null contract); ART interpreter object-register semantics; app side verified null-tolerant by design (`Lnb0.p` pops with explicit `if-eqz`) |
| Exact correction | **NULL-ELEMENT KIND LAW**: introduce kind 4 = null element. Writers classify `NULL_REF`/zero-ref args as kind 4 (STRING args — including `""` — stay kind 2). Readers serve kind 4 as typed null. Genuine-`""` round-trip preserved bit-for-bit (K20 proves both) |

`SOURCE-FIRST ≠ PORT-FIRST`: no ArrayList port, no queue reimplementation —
one kind law on the existing four-store abstraction.

## C. Genericity (proven BEFORE the patch)

1. **Independent non-Dooz repro**: new fcol rows K19/K20 — pure
   `java.util.ArrayList` + null/`""` elements, zero Compose, zero dooz code.
   Pre-fix binary: `K19|FAIL headNull=false lastNull=false poppedNull=false`,
   `K20|FAIL secondNull=false` (run/cont20/fcol_before).
2. **Who else hits the primitive**: any app enqueuing null into a
   list/deque and later removing/reading it — work queues, holder-swap
   idioms, adapter recycling, tree builders, callback buffers. The Compose
   invalidation queue is one live instance.
3. **Why NOT a Dooz fix**: no class/package/app checks; the law lives in the
   shared four-store element model used by every collection shadow consumer;
   verified by the generic fixture, not by a dooz screenshot.

## D. Patch

Files changed (engine `miniandroid/src/framework/android_shadows.cpp` —
one law, eleven sites):

- Writers: `lawb_classify_arg`; `ArrayList.add` tail; `add(index, e)`;
  List `set` face; stream materialization ("unknown element" row) →
  **kind 4** for NULL_REF/zero-ref args (STRING stays kind 2).
- Readers: `lawa_remove_index`; `lawa_serve_slot`; `slot_to_arg`;
  iterator `next` (state path; view path already null-falls-through);
  `removeAll/retainAll` `member_of_other` (null==null element equality);
  `contains` (`contains(null)` matches kind-4 slots only) → **typed null**.
- Diagnostics: `dalvik_engine.cpp` — `MINIANDROID_F271_COLL_TRACE`
  (bounded 100): add/remove channel with live arg kinds + served value +
  caller. Tooling: `scripts/cont20_field_xref.py`.
- Fixture: `fixtures/fcol_audit_probe` K19 (null-element round-trip) +
  K20 (null vs empty-string distinction) rows.
- NOT changed: Compose surface, check-cast law (separate known gap),
  touch/dispatch paths.

## E. Runtime proof

| Check | Pre-fix | Post-fix |
|---|---|---|
| `remove` serve on o2839 | `t5/o0 ("")` | `t8/o0` typed null (×2 runs: dooz_after, dooz_after2) |
| `Lnb0;.j` slot content | `STRING_REF ""` | typed null written via real iput; no F271-WRITE alien store (0 lines) |
| `Lnb0;.S pc=185` death face | fires (f141, uncaught) | **GONE** ×2 |
| Composition progress | dies at pc=185 | `Lnb0.S` pc=913/190 activity; deeper worker/coroutine faces (`Lwg0;.y`, `Lse1;.m`, `Ltx;.run`) |
| fcol K19/K20 | FAIL/FAIL | **PASS/PASS** |
| dooz anchor | d602648e8e401895 | unchanged (next root blocks visuals — honest) |

Next frontier (registered **F-NEW-272**, CLASSIFIED, P0): the app's
crash-report path runs `UncaughtExceptionHandler.uncaughtException` on a
NULL default handler (no `Thread` handler law exists in the engine) and the
reporter NPE reaches `MainActivity.onCreate` uncaught → APP BOUNDARY.
AOSP law: the default handler is non-null (RuntimeInit LoggingHandler /
KillApplicationHandler). Generic Thread/runtime work — NOT Compose.

## F. Regression

| Suite | Result at b6ee41e77acb88ec | Recorded baseline |
|---|---|---|
| anchors ×3 (dooz, microtimer, unote, gmdice, opencalc, chess) | **18/18 MATCH byte-identical** | 18/18 |
| fcol (K1–K20) | **20/20** | 18/18 + new rows |
| f259 | **7/7** | 7/7 |
| f259g | **12/13** (known honest L row) | 12/13 |
| f266 | **6/6** | 6/6 |
| f268 | **12/12** | 12/12 |
| gate-A negatives | 9/19 — A/B: **same at pre-fix binary b4937c81aba0998c** (identical failing rows) → pre-existing harness drift, not a regression | 19/19 historical; harness needs re-calibration (registered work item) |

## G. Decision

**IMPLEMENTED + PARTIAL**

- The F-NEW-271 primitive is root-caused, fixed generically, proven on the
  independent fixture and on the live dooz channel (typed null serve ×2,
  death face gone ×2, composition advances).
- The dooz VISUAL state is unchanged (anchor byte-identical) because the
  next divergence (F-NEW-272, the Thread default UncaughtExceptionHandler
  law gap) blocks after composition work advances — that is the next wave's
  P0, with the same source-first workflow.
