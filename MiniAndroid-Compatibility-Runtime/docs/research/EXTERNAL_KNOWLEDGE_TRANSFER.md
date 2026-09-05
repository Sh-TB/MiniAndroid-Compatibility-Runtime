# EXTERNAL KNOWLEDGE TRANSFER — what we learned and what we did with it (§33)

Campaign law §33: separate DIRECTLY ADAPTED (implemented in MiniAndroid),
ARCHITECTURALLY ADAPTED (idea used, code not copied), REFERENCE ONLY,
REJECTED, FUTURE. Exact repository URLs required on every entry. This
document is the human-readable synthesis; provenance-detail lives in
MASTER_EXTERNAL_REFERENCE_MATRIX.md and the subsystem studies.

---

## 1. DIRECTLY ADAPTED — implemented in MiniAndroid, runtime-validated

### EXT-AOSP-001 — LinearLayout container-gravity law
- Source: https://android.googlesource.com/platform/frameworks/base/
  (revision 1cdfff55) `core/java/android/widget/LinearLayout.java`
  L1933-1945 (setGravity), L1284/L1466 (`lp.gravity < 0 ? mGravity :
  lp.gravity`), L1777-1778 (cross-axis gravity resolution).
- Adaptation (idea + exact fallback law; C++ not Java, structures differ):
  1. `bridge_to_api` setGravity intercept is class-aware: TextView-family
     receivers keep text-gravity semantics (unchanged); container receivers
     now write `container_gravity` + `gravity_set`.
  2. Child positioning falls back to container gravity when a child has no
     explicit layout_gravity — implemented in BOTH layout engines (the
     inflater's measure/layout pass used by modern trees, and the legacy
     render walk used by unmeasured trees).
- Implementation commit: `738ac50` (feat: AOSP gravity + text-size laws…)
- Test: `miniandroid/tests/fixtures/helloworld_golden/
  validate_helloworld_golden.sh` checks [2]/[3].
- Runtime evidence: `setGravity(0x11)` intercepted on the real DEX path;
  children horizontally centered at exactly (1080−child_w)/2 →
  x = 195 / 253 / 513; screenshot `docs/evidence/helloworld_golden/
  screenshot.png` (sha256 93b42621…).
- Regression: tictactoe_golden frames byte-identical; simplestopwatch
  BASELINE_MATCH; 94/94 semantic battery. One intended behavior change:
  unote 21eb0fd3→df92f1d9 (container `android:gravity` in its XML now
  positions children — FAB and search labels centered, AOSP-correct;
  exit code unchanged).

### EXT-AOSP-002 — TextView.setTextSize sp→px law
- Source: same tree/revision, `core/java/android/widget/TextView.java`
  L4720-4722 (`setTextSize(float)` → `COMPLEX_UNIT_SP`), L4752-4762
  (`setTextSizeInternal` → `TypedValue.applyDimension` → `setRawTextSize`).
- Adaptation: engine intercept converts sp → px with this runtime's
  scaledDensity (2.625 — the same factor the renderer uses for its
  14px default), stores `ViewNode.text_size_px` (+ `text_size_sp`
  evidence), handles both the (float) and (int unit, float) AOSP
  overloads, and defensively recovers raw-IEEE-bit floats arriving in
  INT32 slots (documented interpreter behavior from prior cycles).
- Implementation commit: `738ac50`.
- Test: helloworld_golden log assertion (28sp→73.5px, 14sp→36.75px) +
  pixel-band discriminator (headline ink band measurably taller).
- Runtime evidence: render log `[EXT-AOSP-002] setTextSize view=5 …
  px=73.5` and visible 2× glyph-height difference in the golden frame.

### EXT-EXEC-001 — Hello World permanent golden (§28)
- Not external knowledge, but the campaign's execution milestone that the
  two laws above are validated against: real ECJ+D8 APK (APK
  584cda57…, DEX 70298937…) → full §27 chain → 1080×1920 PNG
  (93b42621…), byte-identical deterministic replay, 18-check validator
  with zero-skip gate. Commit `738ac50`.

---

## 2. ARCHITECTURALLY ADAPTED — idea used, code not copied

### AOSP check-order discipline (ART DexFileVerifier) — diagnostics design
- Source: https://android.googlesource.com/platform/art/ (6484611f),
  `runtime/dex_file_verifier.cc`.
- Idea: validate in a fixed order (header → map → intra-chunk →
  inter-chunk) so every failure has a unique earliest cause. MiniAndroid's
  DEX load diagnostics follow the same ordering discipline.
- Evidence: aosp-runtime-study.md AOSP-015; queued hardening Q-7.

### WineDroid warning-accumulation + never-hard-fail inspection
- Source: https://github.com/rickbergs/winedroid (a784c0b, Apache-2.0),
  core/apk.rs + core/axml.rs warnings fields.
- Idea: an inspection pass NEVER fails on the first anomaly; it
  accumulates typed warnings. This matches MiniAndroid's zero-skip
  evidence philosophy and shapes the queued inspect-report work (Q-13).

### Screenshot-testing triage ladder (Robolectric/Paparazzi/Shot lineage)
- Sources: https://github.com/robolectric/robolectric (fc357fec, MIT),
  https://github.com/cashapp/paparazzi (716755fb, Apache-2.0),
  https://github.com/takahirom/roborazzi (6abd5fc0, Apache-2.0),
  https://github.com/Karumi/Shot (e102d797, Apache-2.0),
  https://github.com/dropbox/dropshots (70b8cbfd, Apache-2.0).
- Ideas adopted as methodology (no dependencies): (a) when a frame hash
  mismatches, triage in a fixed ladder — dimensions → pixel config →
  per-pixel diff count → first-N differing coordinates; (b) write a
  failure-artifact directory (expected/actual/delta images + JSON);
  (c) keep exact-match as the default oracle and loudly disclose any
  future tolerance; (d) pair pixel evidence with a UI-tree sidecar
  (MiniAndroid already emits view_tree.json — the pairing discipline is
  the borrowed part).

### droidsaw byte-exact round-trip preservation
- Source: https://github.com/droidsaw/droidsaw (50eb045b).
- Idea: a format model is trustworthy when parse → re-emit → byte-diff
  is empty. Queued as the ARSC round-trip harness (Q-10); shapes how
  arsc/axml parser changes must be validated.

### Android-Dex deterministic boot ladder + failure classifier
- Source: https://github.com/Shrey113/Android-Dex (c57cbc8, NO LICENSE).
- Idea only (zero code/text reuse): staged boot checkpoints with
  timeouts, and a failure classifier that decides whether recovery is
  meaningful. Relevant to MiniAndroid's runner diagnostics roadmap.

---

## 3. REFERENCE ONLY — useful for understanding, not transferred

- WineDroid AOT compilation model (APK→DEX→C→ELF):
  https://github.com/rickbergs/winedroid — opposite execution model;
  understanding it sharpens MiniAndroid's interpreter design tradeoffs.
- CrosVM/Cuttlefish/AVF/qemu host-guest splits: see repository matrix —
  sandboxing concepts for a future hardening roadmap only.
- Skydnir release-gate methodology:
  https://github.com/ryo100794/skydnir — custom license; zero reuse;
  the already-adopted zero-skip gates embody the same idea.
- dexterpreter (https://github.com/vimalloc/dexterpreter, b83d1513,
  NO LICENSE): DEX interpreter skeleton implementing only the
  return-family; its DEX→s-expression dump pipeline is a neat debugging
  pattern; zero reuse (license + scope).
- DaliVM opcode coverage tables (GPL-3.0): coverage-matrix oracle only,
  zero import.
- Waydroid (https://github.com/waydroid/waydroid): instructive inverse —
  what a FULL Android container needs that MiniAndroid deliberately does
  not (LXC, full system services, Binder daemon); clarifies the
  compatibility-runtime boundary.

## 4. REJECTED — investigated, deliberately not used (with reasons)

- **RRO overlay semantics** (https://github.com/mirzachi/android-rro,
  a113f0a, MIT): proper RRO requires an OMS/PMS/AMS system layer;
  MiniAndroid is a single-APK userspace runtime. The Res_value edge
  semantics harvested there were salvaged into the ARSC fixture queue
  (see ADAPTABLE rows RRO-006).
- **Waydroid container model** (GPL-3.0): identity mismatch — full
  Android in LXC vs minimal userspace runtime.
- **DroidVM** (https://github.com/Droid-VM/DroidVM, GPL-3.0): inverse
  problem (hypervisor management ON Android).
- **Bundletool split-APK machinery** (Apache-2.0): no AAB-derived corpus
  APKs exist; queued concept only.

## 5. FUTURE — useful, outside current scope

- WineDroid synthetic-DEX-in-code test tooling (WINEDROID-019) — port
  when the test-harness budget allows.
- Per-method link/reject graph report (WINEDROID-009 → Q-12) — the
  richest single diagnostics upgrade identified for the interpreter.
- ARSC SPARSE/OFFSET16 fixtures + round-trip harness (Q-8/Q-10) —
  resource-format hardening wave.
- Font Case-F distinct-event fixture (Q-11, FONT-002) — upstream
  two-failure-mode semantics already pinned; fixture pending.
- Crosvm/cuttlefish-style process isolation — for the (future)
  untrusted-APK hardening roadmap (GFX-004/G9).
- METH-001..003 tooling (failure dirs, sidecars, triage ladders) as
  concrete validators around frames_manifest.json.

---

Exact-URL law note: every URL above is the mandated canonical one from
the campaign instruction or was URL-discovery-verified with the recorded
evidence trail (dexterpreter: prior record + GitHub HTML search after
api.github.com rate-limiting; AndroidRecomp/ReSource/Reveree remain
URL_UNVERIFIED — no canonical upstream could be verified, none invented).
sim-use remains UNAVAILABLE (second consecutive session).
