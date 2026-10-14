# CONT-14 — FRIEND FINDINGS AUDIT (F-NEW-271..277 + 55/100 claim)

Audit wave: independent audit of the friend-agent's reported "7 new roots"
(F-NEW-271..277), its 14-APK batch claims, and its 55/100 score.
Method: canonical-tree inspection + live runs at HEAD + registry reconciliation.
No fix was attempted in this wave (audit-only, per directive).

**Audit basis disclosure (honest):** the friend-agent's original report was carried in
the prior conversation that was severed mid-run; only a preserved claim digest
survived (F-NEW-271 premise, F-NEW-276/277 suppression descriptions, 14-APK counts,
55/100). The audit therefore grounds every verdict in (a) the canonical tree,
(b) live runtime evidence at HEAD, (c) repo-recorded evidence — and marks every
claim that cannot be cross-checked as UNVERIFIABLE rather than guessing.

---

## 1. Baseline (PHASE 0 — locked)

| Item | Value |
|---|---|
| HEAD | `e99c2fbd8f4e2496bb47c964c2fb6cd83d05b252` (CONT-10 WAVE 6, remote main lineage) |
| Binary rebuilt from source | `aed46450c103f2ea` (132,737,232 B; Makefile -j1; build log `run/cont14_build_full.log`) |
| Binary recorded at CONT-10 | `ea8827584f191dfa` — rebuild SHA differs (link-env nondeterminism), **behavior proven identical via anchors below** |
| dooz APK | `299eab21ac8b3c61` (io.github.yamin8000.dooz_23.apk, 1,840,400 B) |
| tictactoe APK | `760fe5acf7b39435` (com.emmanuelmess.tictactoe_3.apk) |
| Telegram APK | `3baeecb3288577e9` (forkgram_709208.apk, org.forkgram.classic vc 709208) |
| Registry | 566 roots; last IDs F-NEW-259 / F-NEW-259b; generated 2026-10-04 |

**Dooz baseline ×3 at HEAD (fallback-free by construction):**

| run | rc | screenshot sha16 | uncaught | verdict |
|---|---|---|---|---|
| run1 | 1 | `d602648e8e401895` | 6 | DEFAULT_BACKGROUND_ONLY |
| run2 | 1 | `d602648e8e401895` | 6 | DEFAULT_BACKGROUND_ONLY |
| run3 | 1 | `d602648e8e401895` | 6 | DEFAULT_BACKGROUND_ONLY |

- Anchor `d602648e8e401895` ×3 **byte-identical to the recorded canonical anchor**
  (CONT-7/8/9/10 worklogs) — zero drift, the CONT-10 F-NEW-259/259b state is
  reproduced exactly.
- Frame truth: `app_draw_ops=0`, `first_missing_stage=APP_DRAW_OPS`
  (F-NEW-233 frame-truth engine verdict), stub census 5,155,446 IMPLEMENTED /
  1,150 STUBBED / 0 MISSING.
- The 6 uncaught are the known `La;` SETUP-phase CancellationException cascade
  (`Lzs;.m / Lte1;.f / Lse1;.s / Lg;.q / Lg;.h / Lat;.a` unwind chain) — recorded
  since CONT-9 as PRE-composition; suppression is canonically REFUTED as a fix.

---

## 2. F-NEW-271 audit — "AbstractComposeView ctor Context resolution / hardcoded `Lr;`"

**Claim (digest):** friend reported a root in the AbstractComposeView constructor
Context resolution, fixed by replacing a hardcoded `Lr;`.

**Canonical-tree findings:**

1. `grep '"Lr;"' src/` → **0 hits** in the whole engine (cpp/h). The claimed
   hardcode does not exist in the canonical tree.
2. The engine's View-ctor Context law is generic and pre-existing:
   `src/framework/android_shadows.cpp:4421` (F-031, AOSP View.mContext law) —
   `View.<init>` stores **its FIRST constructor Context argument** and
   `getContext()` returns it for the view's lifetime; the doc-comment names the
   dooz Compose chain as the first real-APK hit. There is no class-identity-based
   Context selection anywhere (`grep Context argument` → the F-031 block only).
3. Live check at HEAD: the dooz composition chain runs with MainActivity as the
   caller-provided Context (composition machinery executes; the 6 uncaught are the
   SETUP-phase cascade, not a Context NPE; the ComposeView getContext→null family
   was already closed by F-031 historically).

**Verdict: NOT-A-ROOT in the canonical tree (NON-REPRODUCIBLE).** The claimed
defect (a hardcoded `Lr;` needing replacement) is absent; the claimed fix would be
a no-op here. The prior session's own investigation (preserved digest) agrees:
ComposeView/AbstractComposeView/AndroidComposeView already receive MainActivity.
Classification: **REFUTED / MISDIAGNOSIS of a diverged fork state.** Not registered
in the canonical registry (correct: no evidence could exist for a defect that is
absent).

---

## 3. F-NEW-272 audit

**Claim content:** not preserved (report lost with the severed context).
**Canonical state:** F-NEW-272 does not exist in `root_registry.json` (566 roots
end at F-NEW-259b); no code artifact, probe, or evidence directory matches the ID.

**Verdict: UNVERIFIABLE — no claim, no code, no evidence.** If the friend re-supplies
the report, this ID must be re-audited from scratch under the standard evidence
bar (source evidence + runtime trace + first divergence + semantic law + generic
implementation + positive + negative + real-APK + 3-run).

## 4. F-NEW-273 audit
Same evidentiary situation as §3. **Verdict: UNVERIFIABLE.**

## 5. F-NEW-274 audit
Same evidentiary situation as §3. **Verdict: UNVERIFIABLE.**

## 6. F-NEW-275 audit
Same evidentiary situation as §3. **Verdict: UNVERIFIABLE.**

---

## 7. F-NEW-276 audit (CRITICAL) — "Compose internal error helper → suppress (`LF/r;.c`)"

**Claim (digest):** friend suppressed an internal Compose error helper (`LF/r;.c`);
self-reported consequence: Dooz exceptions 15→0 but **0 draw ops / 0 pixels**.

**Canonical-tree findings:**

1. No suppression site exists: `grep suppress` in `src/runtime/` +
   `src/framework/` yields only (a) the AOSP touch-dispatcher PerformClick
   suppression law and (b) the REAL_DALVIK synthetic-renderer suppression law
   (`frame_census_.synthetic_suppressed` — that is the REAL_APP_CONTENT honesty
   law, the opposite of an error suppressor). No `LF/r;`-named or
   Compose-error-helper interception exists.
2. Live check at HEAD: dooz still reports **6 uncaught** — the engine refuses to
   hide them (`EXC-UNCAUGHT-TOP` strict latch, F-016 exception honesty).
3. Semantic analysis: an exception count going to zero while
   `app_draw_ops` stays 0 is exactly the PHASE-9 regression lesson
   (exception count ≠ compatibility; the master chain is execution → state →
   ViewTree → measure → layout → placement → draw → pixels). A suppressed
   exception in a Compose error helper changes no node, no layout, no canvas op.
4. The canonical root for the same symptom area is F-NEW-256 (CLASSIFIED): the
   composition materializes destination nodes (CONT-10) but the AndroidCanvas
   bridge (`Ljt1;`) is never constructed — a REAL draw-path root, not an
   exception path.

**Verdict: INVALID — SYMPTOM SUPPRESSION.** Without source-level evidence that the
suppressed helper is semantically non-fatal in MiniAndroid (it is not — Compose's
internal error helpers guard real invariant violations), this is rejected. If the
friend's tree carries it, it must be reverted from any core runtime. Not
registered canonically (correct).

---

## 8. F-NEW-277 audit (CRITICAL) — "short-name R8 exception suppressed at THROW site"

**Claim (digest):** friend suppressed an exception at its THROW site on the ground
that the class name is short (R8-named / compat context).

**Canonical-tree findings:**

1. No THROW-site suppression exists in the engine (grep over the throw/unwind
   paths finds no skip/ignore/swallow; the unwind path is the ART process-death
   honesty law with `compatibility-continue` explicitly labeled in output).
2. R8 names are semantically meaningless by the campaign's own law: identity is
   decided by inheritance/interfaces/signatures/behavior — never by name length,
   prefix, or pattern. "Short class name" is exactly the forbidden matcher class.
3. The frame-truth engine itself downgrades runs honestly
   (`DEFAULT_BACKGROUND_ONLY`) instead of hiding failures — the same discipline
   F-NEW-277 would violate.

**Verdict: INVALID — symptom suppression with a forbidden matcher.** Any app
exception suppressed this way (it would suppress *arbitrary* application
exceptions, i.e. break the app's own error handling semantics) must be removed.
Not registered canonically (correct).

---

## 9. Auxiliary claims — P0-B ("F-NEW-236 JNI slot binding") and P0-C (Firebase/Billing stubs)

**P0-B — ID collision proven.** Canonical F-NEW-236 is
"JDK FRAMEWORK INTERFACE HIERARCHY + SET-FAMILY COHERENCE (fairymahjong face)"
(ROOT-CAUSED-FIXED, probe `fixtures/f235_set_probe` 14/14 ×3) — **not** JNI slot
binding. No JNI-slot-binding root exists anywhere in the registry (searched
`jni`/`slot` in titles+summaries). The friend either reused a canonical ID for a
different root (registry divergence) or invented the numbering. Its claim that
"F-NEW-236 JNI affects libtmessages/libgdx/Telegram/tictactoe_emmanuel" therefore
has no canonical referent. The underlying area (real JNI slot binding for
registered natives) may be a genuine future root, but it must be re-derived and
registered under a fresh ID with probes — the friend's version cannot be adopted.

**P0-C — absent from the canonical tree.** `grep FirebaseInitProvider |
BillingController | GoogleApiAvailability | GmsClient` over `src/` → **0 hits**.
No provider-stub or GMS-availability code exists to audit. The AOSP-contract
judgment stands as recorded guidance for any future implementation: without GMS
the honest `GoogleApiAvailability` answer is UNAVAILABLE (not SUCCESS), and a
FirebaseInitProvider stub must first be shown to satisfy the provider-init
contract rather than merely decrement exception counts. Claims NOT INTEGRATED.

---

## 10. Telegram status comparison

**Friend's implied trajectory (digest):** progress toward login → main → chat list
under its unregistered fixes.

**Canonical live truth at HEAD (this wave's runs ×1 each, binary aed46450):**

| metric | value |
|---|---|
| package / activity | `org.forkgram.classic` / `org.telegram.ui.LaunchActivity` |
| verdict (engine frame truth) | **REAL_APP_CONTENT** |
| app_draw_ops / app-owned pixels | 11 / 117,133 (all inside content bounds) |
| rendered content | real settings fragment: `LowPowerEnabledTitle` (twice — the recorded title-overlap law still open) + blue `Disable` action |
| lifecycle | LaunchActivity full created-phase + fragment onStart/onResume fan-out live |
| exceptions | 6 `EXC-UNCAUGHT-TOP`, 44 in-flight (compatibility-continue) |
| deferred | `deferred_ui_pending=True` (queue 2) |

- Recorded history: s115 run4 = first fully clean execution (0 errors) with the
  login tree **measured but not painted**. At HEAD the app has advanced to
  **REAL_APP_CONTENT pixels** — this is the canonical lineage's own progression
  (recorded waves), with no friend patch present.
- The friend's counts cannot be verified as stated: its 14-APK set is not in this
  tree, and no friend artifact exists here. Any claim that Telegram reached
  login/main/chat-list under friend fixes is **contradicted by the canonical
  tree** (those fixes are absent; the canonical state still shows a partially
  laid-out settings screen with title overlap and deferred UI pending — not the
  login flow, not a chat list).

## 11. Dooz / Janken comparison

- **Dooz:** friend claimed exceptions 15→0 via F-NEW-276-style suppression. At
  HEAD dooz still reports 6 uncaught and the honest verdict stays
  DEFAULT_BACKGROUND_ONLY with `app_draw_ops=0` (anchor byte-identical to the
  recorded canonical lineage). The only true Dooz frontier is F-NEW-256's
  AndroidCanvas-bridge gap. **Friend claim not reproducible; even if achieved it
  would not be a draw fix.**
- **Janken:** recorded canonical evidence `evidence/s107_games/
  com.attenomy.janken_run{1,2}/screenshot.png` shows the C013 placeholder face —
  a grey screen with the literal label **"custom view (not rendered)"** and
  Status SUCCESS. Under the registered law (C013: placeholders never produce
  SUCCESS/real content), Janken is **placeholder-only**, i.e. NOT real pixels.
  Any friend row counting Janken as real pixels is contradicted by recorded
  pixels. (APK itself is not in this container — `/tmp/s107_apks` purged —
  re-supply pending for a live recheck.)

## 12. tictactoe_emmanuel — JNI frontier (NAMED, not patched, per directive)

Live at HEAD (apk 760fe5acf7b39435): rc=1, screenshot `b5a7a35d5fe0564b`
(= the pure default-background frame), verdict DEFAULT_BACKGROUND_ONLY,
`app_draw_ops=0`, **9 uncaught**. Precise first-divergence chain:

1. `AndroidGraphics.preserveEGLContextOnPause` does `Class.getMethod` for
   `GLSurfaceView20.setPreserveEGLContextOnPause` → **F-NEW-219 NOT-RESOLVED**
   (registered root) → `NoSuchMethodException` at pc=34.
2. Propagation: AndroidGraphics.<init> (pc 0x1/0x60) → AndroidApplication.init /
   initializeForView → **APP-BOUNDARY at `AndroidLauncher.onCreate`**.
3. Parallel face: `GdxRuntimeException` at
   `com.badlogic.gdx.utils.SharedLibraryLoader.loadFile` +
   `AndroidApplication.<clinit>` — the **libgdx native-library
   extraction/load family** (real JNI/native-registration frontier).
4. Minor face: `RelativeLayout.addView` REC-MISS from onCreate.

**Contrast with the friend's claim:** the friend attributed the residual ~8
exceptions to its "F-NEW-236 JNI slot binding". The canonical first divergence is
**reflection resolution for the GL-surface family (F-NEW-219) + libgdx
SharedLibraryLoader**, not method/field slot identity. This wave hands the
precise chain to the next JNI wave as required — no patch attempted here.

## 13. "7 new roots" count re-check

- Canonical registry: 566 roots; highest F-NEW IDs = 259/259b.
- **F-NEW-271..277 present: 0/7.** The friend's ID space jumped to 271+ without
  any canonical registration; nothing between 260 and 271 exists canonically
  either. The "7 new roots" exist only in the friend's diverged fork/report.
- Adjacent bookkeeping note: registry `total` field = 564 while `total_roots` =
  566 (stale counter after the CONT-10 additions) — cosmetic, flagged for the
  next registry-touching wave.

## 14. Corpus retest at HEAD (measurable scoreboard; no rubric scores)

| APK | sha16 | verdict (engine) | app_draw_ops | uncaught | vs recorded |
|---|---|---|---|---|---|
| dooz ×3 | 299eab21 | DEFAULT_BACKGROUND_ONLY | 0 | 6 | anchor `d602648e` ×3 == recorded (zero drift) |
| tictactoe_emmanuel | 760fe5ac | DEFAULT_BACKGROUND_ONLY | 0 | 9 | first divergence freshly named (§12) |
| telegram (forkgram) | 3baeecb3 | **REAL_APP_CONTENT** | 11 | 6 | advanced beyond s115's not-painted state |
| gmdice | 1621eda1 | **REAL_APP_CONTENT** | 6 | 0 | `f3b483fe` == recorded batch367 anchor |
| Janken | (not in container) | placeholder per recorded pixels | — | — | s107 evidence = "custom view (not rendered)" |

Canonical scoreboard (recorded, CONT-8/10 lineage): **9 explicit REAL_APP_CONTENT
rows** (2048, SnakeDeluxe, MiniCraft, Tetris, SnakeNeon, gmdice, opencalc,
microtimer, unote) + FishRings (time-driven capture) + **12 3-run-verified APKs**;
dooz honestly DEFAULT_BACKGROUND_ONLY with the F-NEW-256 draw-path root standing.

## 15. Registry discipline

- Zero registry changes this wave (audit-only). F-NEW-271..277 **must not** be
  registered: three of seven are refuted/invalid by content, four are
  unverifiable, and registering unevidenced IDs would inflate the registry —
  the exact failure mode the discipline forbids.
- Canonical F-NEW-256 (CLASSIFIED) remains the single Compose draw-path root;
  F-NEW-219 remains the registered GL-reflection root hit by tictactoe.
- Same-semantic-law clustering: no duplicate registrations were created for the
  friend's claims (they either collide with existing roots — 271→F-031 family,
  276/277→suppression-refuted law, "F-NEW-236-JNI"→F-NEW-219/SharedLibraryLoader
  family — or carry no content).

## 16. Score audit — "55/100"

The 55/100 (and any percentage like 43%) has **no rubric, no per-item evidence
map, no reproducible formula** — rejected per the measurable-metrics law.
Replacements used in this audit: engine frame-truth verdicts (REAL_APP_CONTENT /
DEFAULT_BACKGROUND_ONLY), `app_draw_ops`, app-owned pixel counts, uncaught
exception counts, byte-identical anchors ×3, and registered-root counts. Any
future batch claim must ship its per-APK rubric rows next to the number, or the
number is not auditable and is discarded.

## 17. Verdict table and next highest-ROI root

**Required success statement:**

> Of the 7 reported roots (F-NEW-271..277): **0 are proven real generic semantic
> laws; 0 are valid compatibility/environment shims (no code exists in the
> canonical tree to audit); 2 are INVALID symptom suppressions (276, 277 —
> rejected with source-level reasons); 1 is a REFUTED non-root (271 — premise
> absent from the canonical tree); 4 are UNVERIFIABLE (272–275 — report content
> lost with the severed context, never registered, never integrated).**
> Additionally: the P0-B "F-NEW-236 JNI" claim is an **ID collision** with an
> unrelated canonical root, and the P0-C Firebase/Billing stubs are
> **not integrated**. The 55/100 score is **rejected** (no rubric).

| ID | classification | one-line reason |
|---|---|---|
| F-NEW-271 | REFUTED NON-ROOT | no `Lr;` exists; F-031 generic ctor-Context law already covers it |
| F-NEW-272 | UNVERIFIABLE | no claim content survives; absent from registry/tree |
| F-NEW-273 | UNVERIFIABLE | idem |
| F-NEW-274 | UNVERIFIABLE | idem |
| F-NEW-275 | UNVERIFIABLE | idem |
| F-NEW-276 | INVALID — symptom suppression | exception→0 with 0 draw ops proves nothing; no suppression site exists canonically |
| F-NEW-277 | INVALID — symptom suppression | R8 short-name is a forbidden matcher; no THROW-site suppression exists |
| "F-NEW-236 JNI" | ID COLLISION | canonical F-NEW-236 = JDK Set-Family |
| Firebase/Billing stubs | NOT INTEGRATED | 0 hits in canonical tree |
| 55/100 | REJECTED | no rubric |

**Next highest-ROI root (unchanged by the audit, sharpened by it):**
F-NEW-256 — the Compose draw path (layer drawContent runs; AndroidCanvas bridge
`Ljt1;` never constructed → 0 canvas ops), which gates every Compose APK
including dooz. Second: the freshly-named tictactoe_emmanuel chain
(F-NEW-219 GLSurfaceView20 reflection + libgdx SharedLibraryLoader native-load
family) as the JNI wave's entry probe. Third: Telegram's remaining layout face
(title overlap + deferred UI), which now has REAL_APP_CONTENT pixels to iterate
against.

*Evidence: `evidence/cont14/cont14_audit_evidence.json`, `run/cont14/` (dooz ×3 +
corpus retest runs), `run/cont14_build_full.log`. No engine source was modified.*
