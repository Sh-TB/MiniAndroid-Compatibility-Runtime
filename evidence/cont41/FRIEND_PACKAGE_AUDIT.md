# CONT-41 — Friend Knowledge-Package Source-Level Audit
## "What did the friend genuinely achieve, what is already here, what is worth integrating?"

Date: 2026-10-10 · Session start: origin/main `43a3db9d` (CONT-40 highlight) · Registry 610 → 611
Directive frame: source-first audit · verify before patching · integrate only the smallest high-impact
generic fixes · friend numbering recorded as notes, never as root identity.

---

## 0. Package inventory (what was actually available)

`upload/miniandroid_deliverables.zip` (783,105 bytes, extracted to `upload/cont41_audit/`, original
untouched) contains **exactly 13 files**:

| File | Role |
|---|---|
| `COMPLETE_KNOWLEDGE_TRANSFER.md` (26,023 B) | Narrative snapshot A — **13 laws** (friend F-NEW-253..262 + R-NEW-466), "dooz 5/6 blockers fixed, white screen" |
| `knowledge_transfer_document.md` (11,402 B) | Narrative snapshot B — **9 laws** (friend F-NEW-253..259 + R-NEW-466), "dooz stuck at SaveableStateRegistry IAE" |
| `render_gallery_12apps.html`, `render_mosaic*.png`, `shots/*.png` (9 files) | Render gallery + screenshots — **image inspection out of scope per directive** |

**MISSING from the package (exact path, per directive §7):**
- The reported patch script **`/home/z/my-project/scripts/apply_all_patches.py` — NOT in the ZIP and
  NOT in the workspace** (`ls` confirms). No code files of any kind are in the ZIP (no `.py`, `.cpp`,
  `.java`). All code-level claims below were therefore verified against **canonical source only**,
  using the narratives as navigation hints.

**Contradiction resolution (directive Step 2):** the two documents are SEQUENTIAL snapshots of one
session, not competing histories. Doc B (11:06, smaller) ends at the SaveableStateRegistry IAE with 9
laws; Doc A (14:38, "Complete") adds F-NEW-260/261/262 and narrates that registry failure being
bypassed, the Recomposer resumed, and the screenshot still white. Doc A supersedes Doc B. Both claim
HEAD `f8d4088b` — **not trusted and irrelevant**: canonical main is `43a3db9d` and every claim was
matched by BEHAVIOR. Latest demonstrated Dooz state per the package: composition created, coroutine
resumed, white screenshot. Latest canonical Dooz state (CONT-40, already pushed): the getWindowToken
hypothesis REJECTED with DEX+runtime A/B evidence — composition creation happens with or without a
token; the true frontier is case E (first-composition completion within the execution budget; 14.3 M
instructions executed; 151 app-owned draw ops painted mid-draw before the F084 budget halt).

---

## 1. Claim matrix (friend numbering = notes; verification = source + probes)

| # | Friend claim (behavior) | Canonical status on `43a3db9d` | Semantic correctness of friend's version | Evidence | Decision |
|---|---|---|---|---|---|
| 1 | F-NEW-253 Notification$Builder fluent setters + build() | **MISSING** — zero `Notification` handling in engine/shadows (`rg 'Notification'` → only NotificationManager service strings) | Correct AOSP reading (API 21+ fluent; build() non-null) | CONT-38v recorded the exact frontier; PRE A/B this wave (below) | **FIX → F-NEW-303, integrated** |
| 2 | F-NEW-254 FragmentTransaction.commit lifecycle drain | **MISSING** — `FragmentManagerShadow` commit → `handled_int(0)`, no dispatch (android_shadows.cpp:3376) | Plausible design (engine-callback pattern) but code not available; multi-file | tananaev log this wave: `REC-MISS FragmentTransaction.commit` = the real next blocker | **DEFER → recorded next wave (Fragment/Preference family)** |
| 3 | F-NEW-255 addPreferencesFromResource | **MISSING** — only `PreferenceManager.setDefaultValues` exists (dalvik_engine.cpp:41949+, a different contract) | Reasonable; depends on #2 | tananaev DEX strings: `Landroid/preference/PreferenceFragment;` + `addPreferencesFromResource` = the real main-UI path | **DEFER (same family)** |
| 4 | F-NEW-256 Preference tag mapping + title/summary extraction | **MISSING** in layout_inflater (zero preference-tag hits) | Tag mapping + text extraction generic; **the fixed geometry (w=1080 h=105 y+=105 color=0xFF333333 h=44) is a symptom hack** bypassing measure/layout | Canonical measure laws would size real widget tags; hard-coded geometry is screen-shape-dependent | **DEFER (generic part); REJECT the geometry hacks as-designed** |
| 4b | apply_element_attrs title-overwrite guard | Bug real (`node.text = a.text` unconditional, layout_inflater.cpp:1529) but has **no live consumer** without #4 | Correct but premature | source read | **TEST only with #4** |
| 5 | R-NEW-466 ServiceLoader.iterator dedicated Iterator object + CollectionShadow gate | **PRESENT** — dedicated iterator `__sld_service__` (dalvik_engine.cpp:46725) + F-NEW-252 decline law keyed on the `service` marker (android_shadows.cpp:441) | Canonical equivalent, different marker name | standing battery f259 49/0, f259g 84/7-known | **REUSE (already implemented)** |
| 6 | F-NEW-257 Class objects as map keys (`class:<descriptor>`) | **PRESENT, STRONGER** — F-069/R-NEW-293 stable const-class identity (dalvik_engine.cpp:16914) + F-103 heap-backed Class tokens + F-NEW-249 getClass + F-NEW-282 boundary materialization | Friend's string-key would fix maps but NOT `==` identity; canonical root-cause is strictly more general | **CONT-38v probe proof: CK-01..06 PASS ×3 on two binaries** (evidence/cont38v §1) | **REUSE (already implemented)** |
| 7 | F-NEW-258 listIterator non-null | **PRESENT** — F-NEW-255(CONT-7) listIterator law: real typed `Ljava/util/ListIterator;` box with `__iterator_parent__`+`__iterator_pos__` (android_shadows.cpp:2565-2600) + LAW-B write-back faces (set/remove/add + double-remove ISE, :461-540) + engine-side family (:38976-39031) | Friend's "self-as-iterator" exists only as the heap-null fallback branch in canonical and never fires on live runs; canonical typed box has independent cursor state | **CONT-38v probe proof: LI-01..08 PASS ×3** (full cursor contract, empty-list, mid-start, set-into-backing, add-at-cursor, remove+ISE, pre-next ISE, re-iterate) | **REUSE (already implemented)** |
| 8 | F-NEW-259 Bundle implements Parcelable/Serializable | **PRESENT** — framework_interfaces table Bundle→[Parcelable, Cloneable] (view_ancestry.h:335-345), Bundle→BaseBundle superclass edge (:163), `framework_implements()` consulted in is_subclass_of (dalvik_engine.cpp:1123, 25070) | Equivalent | source match | **REUSE (already implemented)** |
| 9 | F-NEW-260 SaveableStateRegistry canBeSaved suppression (intercept R8 `O/c.a()` → true, `O/c.b()` → void) | **OBSOLETE + UNSAFE** — canonical fixed the ROOT generically: the platform storable-type instanceof walk (framework_implements + DEX interfaces + F-NEW-292 libcore UUID/Enum rows) so canBeSaved answers honestly | **App-specific R8-class-name hardcoding that suppresses an exception instead of implementing storable-type semantics** — masks real classification bugs | canonical F-103 comment: dooz DisposableSaveableStateRegistry already passed on main | **REJECT** |
| 10 | F-NEW-261 getWindowToken non-null + isAttachedToWindow=true-without-node | **REJECTED BY CONT-40 WITH A/B EVIDENCE** — composition creation is NOT gated by the token (DEX decode: token stored raw, zero null-gates; runtime: 14.3 M instr + 151 draw ops both ways). Canonical isAttachedToWindow is the AOSP-accurate UC009 law (node state, false when detached, android_shadows.cpp:5556) | **Fabricates attachment state** (returns true with no node; synthetic token without window semantics) — exactly the risk class the directive flags | CONT-40: the prototype law REGRESSED composeStopwatch (visible text lost, 5c4a0172628849ba, causality proven via MINIANDROID_WTOKEN_NULL) and flipped dooz to an empty scheduling path | **REJECT (law parked; evidence evidence/cont40/DOOZ_WTOKEN_AUDIT.md)** |
| 11 | F-NEW-262 drain_park_queues in compose pump + virtual-clock advance | **PRESENT, MORE DISCIPLINED** — F100-IDLEDRAIN 64-round handler drain every tick (execution_engine.cpp:6289+), F-NEW-277 poll-timeout parity (advance-to-next-ready, but SCOPED: only when `fired_frames > 0` — launch-frame frozen law preserved), F-115b/F-NEW-232 quiescence honesty, drain_park_queues_bounded at park/bq-take sites (dalvik_engine.cpp:24883, 25830, 25953) | Friend's unguarded advance would break byte-deterministic launch frames | dooz case-E verdict stands (budget, not clock) | **REUSE (already implemented)** |
| 12 | F-NEW-256e text draw h≤0→44 fallback | Not needed standalone: canonical already has draw-side guards (e.g. anim rh=64) and real measure laws; magic 44 is screen-agnostic-by-luck | Symptom-level | source read | **DEFER with #4 family (re-test honestly)** |
| 13 | Doc B "next frontiers": DataStore ISE / DrawerLayout NPE / Compose rendering | DataStore: dooz-facing laws already on main (dalvik_engine.cpp:19256, 21171, 34105, 47714, 48300); DrawerLayout: handling exists (dalvik_engine.cpp:35995); Compose rendering: the standing CONT-40 case-E frontier | Stale snapshot claims | source hits | **REUSE/RECORDED** |

## 2. The integrated fix (the only one justified this wave)

**F-NEW-303 — AOSP Notification$Builder fluent-chain object law** (`dalvik_engine.cpp`, bridge_to_api,
after the MediaPlayer block): `<init>` → void; `set*`/`addAction`/`addPerson`/`addExtras`/`extend` →
`args[0]` (fluent THIS); `build()` → fresh `Landroid/app/Notification;` heap object (`__from_builder__`).
Plus `Landroid/app/Notification;` `<init>` honest void. Zero app knowledge; same §12 family as the
existing AudioAttributes$Builder / LineBreakConfig$Builder laws.

**Why this one:** it is (a) a RECORDED canonical frontier (CONT-38v §4: tananaev PARTIAL, the whole
NotificationCompat family gated at MainActivity.onCreate), (b) the smallest generic point in the
friend's package that canonical lacks, (c) contract-faithful (AOSP fluent + non-null build), and
(d) probe-verifiable end-to-end.

## 3. PRE/POST evidence (commands + results)

**PRE binary** `d3d6a5412a696122` (pre-law build of `43a3db9d`; the session environment was restored,
so the PRE frame-truth baseline was RE-ESTABLISHED first — see §4):

- `scripts/cont41_pre.sh` ×3: probe NB-01 PASS, NB-02 FAIL (NPE), NB-03 FAIL (build null), NB-04 FAIL
  (NPE), NB-05 FAIL (wrapper null), NB-06/07/08 PASS — identical ×3 (28/28 markers; 4 dead rows).
  tananaev ×3: rc=1, `setSmallIcon` hit ×1, frame `d602648e8e401895` (== the CONT-38v record, byte-exact).
- PRE regression (`scripts/cont37_regression.sh` stages, run/cont41/cont37_regression/): anchors
  **24/24 MATCH** byte-identical; composeStopwatch `3442d9a9dc0fa0f9` ×3; battery == CONT-28..40
  records EXACTLY; simplecalc ×3 rc=0 `7960bce447ac6d8f`.

**POST binary** `e1fc1915e88fe2a8`:

- `scripts/cont41_post.sh` ×3: **NB-01..08 ALL PASS ×3** (56/0 markers) — fluent identity, build()
  non-null + distinct, post-build reuse, wrapper face, void-context, identity, direct ctor.
- tananaev ×3: **setSmallIcon hit 0, uncaught 0, Errors: 0, Status PARTIAL SUCCESS** — first_missing
  stage APP_DRAW_OPS; the log's next blocker is `REC-MISS Landroid/app/FragmentTransaction;.commit
  caller=MainActivity.onCreate` (exactly the friend's documented post-253 position, now independently
  reproduced on canonical). Frame stays `d602648e8e401895` — **no render claim made**.
- POST regression: anchors **24/24 MATCH**; composeStopwatch ×3 MATCH; battery == records EXACTLY
  (fcol 140/0, f259 49/0, f259g 84/7-known, f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0,
  fnew289 28/0, ckey 105/0, cpipe 119/0, fnew302 48/24 documented, fnew252 56/0, fnew290..297 ==,
  fnew298 19/0 KEEP=5); simplecalc ×3 rc=0. **ZERO DRIFT.**

## 4. Session environment recovery (recorded for reproducibility)

- Disk was 100% full: old-era backup bundles/logs (logs/, gc_work/, mc4_sweep/, >50 MB bundles in
  download/, tmp/) deleted; 3.5 GB freed. Local checkout was 73 commits behind → fast-forwarded to
  `43a3db9d` (tracked-file "modifications" were content-identical to origin; a root-owned
  `miniandroid/runtime/` was moved aside for the checkout).
- The environment restore had wiped probe APKs and app APKs: all standing probes rebuilt from
  fixtures/ (cont21/w4/cont30 builders); F-Droid apps re-downloaded **SHA-exact** (tananaev
  `294a68bd00debbdc`, headingcalc `274ec873098eea51`, simplecalc `68da25fd9fdf54b4`,
  composeStopwatch `dbf937ebbe7c0b3d`).
- A root-owned empty `/home/z/my-project/runtime/` (restore artifact, mode drwx------ root:root)
  blocked the engine's relative data-root creation → microtimer (and any app needing a data dir)
  failed with `Permission denied` on `runtime/data/data/data/<pkg>`. Moved aside; microtimer
  immediately reproduced its recorded anchor. Not an engine bug — an environment artifact.
- Binary SHA changed `111340a583d48d92` → `d3d6a5412a696122` for the same source (restore artifact;
  no `__DATE__`/`__TIME__` in src; build is fully current per `make -n`). The frame-truth gate, not
  the binary hash, is the behavior contract — re-baselined PRE before any edit.

## 5. Dooz / Compose state (reconciled, unchanged)

Canonical CONT-40 verdict stands: the friend's getWindowToken/Recomposer causal chain is REJECTED
(both transitions happen without a token; A–D REJECTED, F subordinate-REJECTED, **E = the real
frontier** — first-composition completion within the execution budget). The parked law stays parked
(shipping it was proven to regress composeStopwatch's visible text). The friend-package's "5/6
blockers fixed → white" narrative is CONSISTENT with that state but its F-NEW-260/261 mechanisms are
superseded/unsafe, and its F-NEW-262 is already present in a stricter form. The unverified rendering
frontier is unchanged: **case E** — dooz paints 151 app-owned ops mid-draw before the budget halt;
the honest white anchor is kept until the boot composition completes within budget.

## 6. Decision summary

- **KEEP/INTEGRATED (1):** F-NEW-303 Notification$Builder fluent-chain law (friend F-NEW-253 analog).
- **REUSE — already implemented, canonical equal or stronger (6):** ServiceLoader dedicated iterator
  + gate; Class stable identity (F-069 family, probe-proven); listIterator typed box + LAW-B
  (probe-proven); Bundle parcel-family interfaces; compose-pump drain + scoped virtual-clock advance
  (F100-IDLEDRAIN + F-NEW-277); DataStore/DrawerLayout facing laws for the recorded faces.
- **REJECT — unsafe or superseded (2):** canBeSaved app-specific suppression (F-NEW-260);
  fabricated attachment/synthetic token (F-NEW-261 — also REJECTED on the merits by CONT-40).
- **DEFER with a recorded next action (3):** Fragment commit drain + addPreferencesFromResource +
  preference tag mapping (ONE family — the tananaev main-UI path; generic parts only, geometry
  hacks re-designed through the real measure laws before any integration).
- **NOT IN PACKAGE:** `apply_all_patches.py` (path reported in §0; audit proceeded on narratives +
  canonical source).
