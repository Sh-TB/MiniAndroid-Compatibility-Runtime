# CONT-50 — solitaire past the receiver wall: two generic interpreter laws

Continued from remote HEAD `a9a7297b` (CONT-49 closeout + UUID checkpoint), per the
"continue from the latest remote HEAD" directive. Every row is **STATUS — RESULT —
EVIDENCE** with exact artifacts. Work binary: rebuilt-from-HEAD identity proof
`6c478a224ab1b3f4` → fix binaries `aababdec3585da5c` (first draft) → final
`d19d5ba63c47a19f` (raw mirror + qualified-first read). No APK-specific hacks, no
fake objects, no forced lifecycle transitions — both laws are structural.

## Phase 0 — reconciliation (measured, not assumed)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | local container was the CONT-10-era snapshot `e99c2fbd` again (the recurring recovery class); fetched + reset → `HEAD == origin/main == a9a7297b` | git fetch + rev-parse |
| TESTED | binary REBUILT from HEAD == recorded CONT-49 closing `6c478a224ab1b3f4` — build reproducibility proven after the reset | sha256sum |
| TESTED | registry 630 (last F-NEW-319); canonical 535-block is the known stale summary layer | root_registry.json census |
| TESTED | APK pins: dooz `299eab21`, bmi `2dbd8ebe`, alex `b1383bc9`, notes `71e874f4`, micro `79c6f730`, unote `be91103f`, gmdice `1621eda1`, opencalc `26426138`, tananaev `294a68bd`, simplecalc `68da25fd`, composeStopwatch `dbf937eb` (tmp APKs refetched SHA-exact) | sha256sum ×11 |
| TESTED | **solitaire ORIGINAL store bytes RECOVERED**: F-Droid repo `de.tobiasbielefeld.solitaire_71.apk` = `fdfaf7cad18e4416…` — the exact CONT-46 pin ("lost" per CONT-49); reproduces the recorded face `ba50a4d28ea62fe7` ×3 byte-identically on the CONT-49 binary → re-pinned to the ORIGINAL bytes; the CONT-49 substitution note is superseded | upload/cont50_apks/; run/cont50/sol_orig/r1..r3 |
| TESTED | Issue #375 comments fully read (15 rows, oldest CONT-2 → newest CONT-49 closeout 6116119789); the CONT-49 closeout is the newest execution directive; its recorded next-wave frontiers (the two solitaire null-recvs) became this wave's decode targets | GitHub API /tmp/i375_all.json |

## Phase 1 — the decode: two separate roots behind the recorded "divergence wall"

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED (F-NEW-320 root) | `DrawerLayout.computeScroll` ran with **`this` = UNSET**: METHOD-TRACE printed `p0=<unset>` from pc=0; the frame's args vector was EMPTY (call_compute_scroll built `std::vector<DalvikValue> args;` and passed it) — every iget on the unbound receiver silently answered null (no FIELD-TRACE row: the receiver is not a live heap object), the loop body never executed, and the first field/invoke pair raised the per-frame `ah;.a` NPE at pc=35 | run/cont50/mt_cs.log; dalvik_engine.cpp:12205 |
| TESTED (convention proof) | the engine-wide try_recursive_invoke convention is receiver-first: onDraw args={this, canvas}, onSizeChanged args={this,w,h,0,0}, the onScrollChange LISTENER arm passes {view,…} — call_compute_scroll and the onScrollChanged override arm were the only violations | dalvik_engine.cpp:11476/11518/12262 |
| TESTED (F-NEW-321 root) | `c$b.f pc=27` read key `Landroid/support/design/internal/c$b;->a` obj#402 **hit=Y val=ay$b#403** — the qualified key was CORRECT and its slot was CORRUPTED: the c$b ctor stored the outer presenter (obj#304, FIELD-TRACE put row), then the SUPER ay$a ctor's `ay$a.a` iput (mObservable obj#403) landed its bare legacy mirror through the F-NEW-251 runtime-class redirect → key re-resolved to the receiver's most-derived declarer `Lc$b;->a` → clobbered the outer | run/cont50/q2.log (S134-QGET); run/cont50/ft_cba.log |
| TESTED (identity census) | DEX-wide `new-instance internal/c;` census: exactly ONE site (NavigationView ctor) — the "second presenter" hypothesis was REFUTED by tool; obj#403's real identity = `ay$b` (RecyclerView$AdapterDataObservable) via the NULLFIELD probe's heap class print | scripts/cont50_newpresenter_scan.py; run/cont50/nf_b.log |

## Phase 2 — probe FIRST (fnew320_probe, real aapt2/ECJ/D8)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | probe APK built BEFORE patching (`91711cd6ae3de9cf`): the exact R8-shadowing shape (SubA extends SupA, both declare `a` of different types; super ctor writes Inner, sub ctor writes Outer) + Flinger (a View overriding computeScroll that reads its own ctor field inside the override) | fixtures/fnew320_probe; scripts/cont50_build_probe.sh |
| TESTED | PRE faces ×3 deterministic: **P4-CS-RECV FAIL** ("computeScroll ran with tag=null = unbound receiver") ×6 rows; **N2-SUB-UNTOUCHED FAIL** ("s1.outer() after super write==null" — the solitaire c$b face in miniature); P1/P2/P3/N1 PASS (the un-shadowed faces were already healthy — the defect is exactly the shadow+mirror interaction) | run/cont50/probe_pre/r1..r3 |

## Phase 3 — the fixes (minimal, generic, evidence-backed)

| Law | Change | Scope guard |
|-----|--------|-------------|
| F-NEW-320 | `call_compute_scroll` binds the receiver `args[0] = make_object(view_object_id, node->class_desc)`; the `onScrollChanged` override arm binds it the same way (its (IIII)V signature had ins=5) | both dispatches in dalvik_engine.cpp; no other arm touched |
| F-NEW-321 | (1) `set_object_field_raw` in the heap — the S134 dual-write legacy mirror is now a RAW exact-key write (no F-NEW-251 redirect) in BOTH dual-write sites; (2) QUALIFIED-FIRST read in `get_object_field` — for a resolvable bare name on a DEX-defined object the qualified slot is authoritative, the plain slot is the legacy channel; framework-owned objects keep bare keys end to end | dalvik_engine.h heap; no reader/writer semantics changed outside DEX-declared fields |

Honest intermediate: the first draft (raw mirror WITHOUT the qualified-first read)
regressed fnew252 to 21/35 — the Atomic*FieldUpdater family read the now-populated
stale plain slot (the F-NEW-251 split-brain reborn in read order). The
qualified-first law restored it to 56/0; the draft is recorded, not hidden.

## Phase 4 — POST verification (final binary `d19d5ba63c47a19f`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **fnew320 probe 11/0 ×3** (P1 sub slot / P2 super slot / P3 per-instance / N1 round-trip / N2 sub-untouched / P4-CS-RECV receiver bound ×6 rows) | run/cont50/probe_post2, f320_r1..r3 |
| TESTED | solitaire ×3 on the fix binary: **ah-NPE = 0** (was 6/run), **menu-hub NPE = 0** (was 1/run); the RecyclerView fill chain now RUNS (first `EXP095-ADDVIEW-LP child=406`); screenshot face UNCHANGED `ba50a4d28ea62fe7` ×3 (honest) | run/cont50/sol_final/r1..r3 |
| TESTED | NEW first divergence recorded (next-wave root): `ay$w.q` null-recv at `ay$h.a pc=8` ×9/run — `ay.e(View)` (AOSP getChildViewHolderInt: `(RecyclerView.LayoutParams) child.getLayoutParams()).c = mViewHolder`) answers null; upstream face `NavigationView.onMeasure spec=0 FAILED(no write-back)` PRE-EXISTING (identical rows in PRE and POST — not a regression) | run/cont50/sol_final/r1/run.log:3963 |
| TESTED | canonical regression gate on the FINAL binary: **33/33 anchors ×3 byte-identical ZERO DRIFT** (dooz 31ddd4d5 / micro da73010a / unote 4f1a9e4e / gmdice f3b483fe / opencalc a976d2f9 / tttdeluxe af609429 / flappycow 13cf4746 / g2048 59ca1526 / tanana 5f7e0114 / csw 3442d9a9 / simplecalc e847ca03) | /tmp/cont50_gate.log stages |
| TESTED | probe battery == records exactly: fcol 140/0, f259 49/0, f259g 84/7 (known), f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, ckey 105/0, cpipe 119/0, fnew302 48/24, **fnew252 56/0**, fnew290..297 (56/56/70/56/77/49/42/42), fnew298 19/0 KEEP=5, **fnew309 8/0 ×3** (rebuilt after the reset, `7c6162780f201a74`) | /tmp/cont50_gate.log; run/cont50/f309_r1..r3 |
| TESTED | support group ×3 byte-identical to the CONT-46/47 records on ONE binary: **BMI `b52252c2de19b03a`** (REAL_APP_CONTENT held), **alex `c8d69f811b23f245`**, **notes `eb5ebd559cad1028`** — both androidx scope faces held through two interpreter laws | run/cont50/support |
| TESTED | skill self-test 13/13 rc=0 (after the reset-lost gate_a_probe rebuild `f6102f06…`, libprobe `ad413625925ed8e5`) | /tmp/cont50_skill3.log |

## Cross-app impact + honest bounds

One binary carries two generic interpreter laws; the whole canonical corpus is
byte-identical ×3 — the laws touch exactly the unbound-instance-dispatch surface
(only views overriding computeScroll/onScrollChanged execute differently) and the
shadowed-field mirror surface (only DEX classes that shadow a superclass field by
name read different values; the corpus's recorded faces prove none of the recorded
pipelines did). BMI improved in CONT-47/48 and stayed; nothing regressed. Honest
bounds: (1) solitaire's screenshot face is UNCHANGED `ba50a4d2` ×3 — the MACHINE
moved two divergence layers deeper (per-frame NPE wall + menu-hub NPE both gone;
the RecyclerView adapter/menu machinery now runs); (2) the NEW first divergence
(ay$w.q / ay.e mViewHolder law) is recorded for the next wave — same law family
as F-NEW-309's LP generation, NOT fixed this wave (no fix without its own decode
cycle); (3) the NavigationView.onMeasure spec=0 face is PRE-EXISTING and recorded
for the same decode; (4) the original solitaire bytes are re-pinned — future
waves no longer need the substitution caveat.

**Registry 630→632** (F-NEW-320, F-NEW-321 appended ROOT-CAUSED-FIXED; F-NEW-309
next_wave refreshed). Evidence: `evidence/cont50/CONT50_RESULT.md`.
