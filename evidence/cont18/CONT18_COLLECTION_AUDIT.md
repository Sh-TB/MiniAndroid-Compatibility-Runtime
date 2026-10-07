# CONT-18 COLLECTION AUDIT — T-02/T-03/T-04 (F-264 family, six laws)

Binary `a8761a482a186eac` · HEAD `d95b352f`→`012bd840` · fcol live baseline **3/18**
(PASS K7/K8/K10; FAIL K1–K6, K9, K11–K18) — matches recorded CONT-17 state exactly.

## T-02 — Six-law reconstruction table

| ID | Source contract (OpenJDK/ART) | Current MiniAndroid divergence | Generic? | First divergence (live rows) | Proposed law | Status |
|---|---|---|---|---|---|---|
| **LAW-A** read-your-mutation + missing readers | ArrayList.set returns prev (F-239 done); `remove(int)` fastRemove = ONE backing store, returns removed; `indexOf/lastIndexOf(Object)` = first/last i with `o.equals(elementData[i])`, -1 absent; `contains` = same equality | `remove(int)` erases ONLY `elements` — `elem_kinds/elem_strings/elem_ints` desync → post-remove `get` serves STALE element; `contains` skips kind-2/3 slots (`e==0` → no compare); **`indexOf`/`lastIndexOf` have NO handler** (generic-stub answer) | **YES** — no class/pkg names; pure store-coherence | fcol **K1** `ok=false` (live trace: `[F-NEW-238-SET] obj=13 idx=1 shadow_n=3 item=0 arg_kind=5 POISON` = diag false-positive for STRING; real killers = contains-kind-2 skip, no indexOf, remove desync) | **PARALLEL-STORE COHERENCE LAW**: the four stores (elements/kinds/strings/ints) are ONE logical backing array (OpenJDK elementData); every writer (add/insert/set/remove/clear) moves all four in lockstep; every reader (get/contains/indexOf/lastIndexOf/iterator) resolves kind-aware | **IMPLEMENTED this wave (T-05)** |
| **LAW-B** iterator write-back | ListIterator.set(Object) writes through to backing list at lastReturned index; ListIterator.add(Object) inserts at cursor and advances it; Iterator.remove() removes lastReturned; double remove → ISE | `ListIterator.set` args==1 → falls into LIST set(index,item) path → `handled_void` silent NO-OP; `ListIterator.add` on the iterator BOX mutates the box's own (wrong) state; `Iterator.remove` (0 args) → void no-op; no ISE law | YES | fcol K2 `prev/set ok=false` (prev works — read path real; set lost), K11 `threw2nd=false`, K12 `add law ok=false size=2` | ITERATOR WRITE-BACK LAW: box carries `__iterator_last_ret__`; set/add/remove route to the PARENT store per AbstractList.Itr contracts, ISE on invalid cursor state | PENDING (next) |
| **LAW-C** Java-8 default methods | removeIf/sort/removeAll/retainAll/merge/computeIfAbsent/forEach = interface defaults executed against the real store | No default-method machinery for these on the shadow channel | YES | fcol K13/K14/K16/K17/K18 FAIL | DEFAULT-METHOD FAMILY LAW (one machinery, seven faces) | PENDING |
| **LAW-D** deque views | LinkedList addFirst/addLast/getFirst/getLast/removeFirst + iteration order; ArrayDeque FIFO poll/peek | K4 order=`mnull` (addFirst/addLast mis-stored?), K5 peek=null | YES (view-order laws) | fcol K4/K5 | DEQUE ORDER LAW | PENDING |
| **LAW-E** hash view coherence | getOrDefault(key, def) returns mapping or def; HashSet dedup on add→put(e,PRESENT) | K6 ok=false (compound), K9 add2=false correct but contains missing? | YES | fcol K6/K9 | MAP-DEFAULT/SET-COHERENCE LAW | PENDING |
| **LAW-F** missing families | subList(int,int) = a VIEW (writes through both directions); Stream.of().filter().collect() | K3 threw NPE (subList unhandled); K15 threw NPE (stream family unhandled) | YES | fcol K3/K15 | SUBLIST-VIEW LAW / STREAM FAMILY LAW | PENDING |

## T-03 — Probe artifact vs runtime semantics (residual rows)

The WAVE-10 hypothesis "probe-bundled java.util double-bookkeeping" is **REFUTED for
fcol.apk**: `unzip -l run/w7/fcol.apk` shows ONE classes.dex, zero `java/util` entries —
no bundled collection classes exist. Every FAIL row is a real runtime gap or a real
probe-honesty face:

- **Runtime gaps (genuine)**: K1 (LAW-A ×3), K2/K11/K12 (LAW-B), K13/14/16/17/18 (LAW-C),
  K4/K5 (LAW-D), K6/K9 (LAW-E), K3/K15 (LAW-F).
- **Probe/diag artifacts (not runtime)**:
  - `[F-NEW-238-SET] … arg_kind=5 POISON` printed for LEGAL string writes — the diag's
    poison predicate counts `item==0 && kind==2` as poison, but kind-2 is the DESIGNED
    representation of string elements (value lives in elem_strings). Diag false-positive,
    fixed with LAW-A (semantics were already correct).
  - K14 detail `sorted [1,2,3] got Ljava/util/ArrayList;@77` — the sort machinery gap
    (LAW-C) is real, the printed detail is just the list's toString face (no
    AbstractCollection.toString law on the shadow channel — recorded as a LAW-C sub-face).
- **Never modify the runtime merely to make the probe green**: LAW-A is implemented from
  the OpenJDK store contract, not from K1's compound boolean — each of its three faces
  (remove-desync, contains-skip, missing indexOf) is independently derived from source
  law and independently probeable.

## T-04 — Source-law extraction for LAW-A (the implemented one)

```text
source contract   OpenJDK ArrayList: elementData is the SINGLE backing array;
                  set/remove/add move it wholesale; readers (get/indexOf/
                  contains/iterator) all resolve through the same array with
                  o.equals(elementData[i]) equality.
semantic rule     MiniAndroid's shadow store = 4 parallel vectors that
                  TOGETHER model elementData. Law: every writer updates all
                  four in lockstep; every reader resolves kind-aware
                  (kind1=object id, kind2=string content, kind3=int value).
MiniAndroid gap   remove(int) moved 1 of 4; contains read 1 of 4;
                  indexOf/lastIndexOf absent.
divergence        K1 ok=false (stale get after remove; contains("c")=false;
                  indexOf("B")=-1)
minimal fix       (1) remove(int): erase 4/4 + kind-faithful return;
                  (2) contains: consult elem_strings/elem_ints for kind-2/3;
                  (3) new indexOf/lastIndexOf handler (kind-aware, heap-array
                  fallback layering identical to contains/get);
                  (4) F-238 diag predicate exempt legal string/null writes.
```
