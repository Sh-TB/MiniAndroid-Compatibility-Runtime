# CONT-42 — Fragment/Preference family, slice 1: the FragmentTransaction
# pending-op law + host-stage fragment lifecycle drain (F-NEW-304)
## "Dooz and the calculator must get past that screen" — the tananaev calculator wave

Date: 2026-10-10 · Session start: origin/main `3355f2f1` (CONT-41 + checkpoint) · Registry 611 → 612
Directive: back to our own blockers — Dooz past its white screen, the calculator past its
blocked screen. This wave = the calculator (com.tananaev.calculator v1.10); Dooz's case-E
budget stays the recorded next wave.

---

## 0. Static decode (scripts/cont42_decode.py — field-ref-exact, androguard 4.1.4)

`MainActivity.onCreate` (extends AppCompatActivity): `if (bundle == null) getFragmentManager()
.beginTransaction().replace(16908290 /*android.R.id.content*/, new PrefsFragment()).commit()`.
`PrefsFragment extends Landroid/preference/PreferenceFragment;` (PLATFORM), overriding ONLY
`onCreate` → `addPreferencesFromResource(0x7f110000)`. No onCreateView override — the platform
must supply the list UI. androidx `ReportFragment.injectIfNeededIn` rides the same platform
transaction path. The pre-law engine: ops DROPPED (fluent THIS), commit → 0 — the recorded
CONT-41 PARTIAL face (ContentFrameLayout children=0, DEFAULT_BACKGROUND_ONLY, next blocker
`REC-MISS FragmentTransaction.commit`).

## 1. The law (F-NEW-304) — generic, zero app knowledge

- **Shadow (FragmentManagerShadow)**: ops record on the transaction heap object
  (`__ftx_n__` + `__ftx_<i>_{type,container,frag,tag}__`); `commit/commitNow(AllowingStateLoss)`
  harvest into the queue with a real monotonic BackStackRecord id (AOSP mIndex contract);
  `executePendingTransactions` sets the drain request; `findFragmentByTag/Id` answer the
  fragment records (AOSP mActive walk); `Landroid/app/Fragment;` state getters
  (getTag/getId/getView/isAdded/getArguments) answer the drain-maintained fields.
- **Engine drain (dalvik_engine.cpp)** at the HOST lifecycle windows:
  - CREATED (after the app's onCreate returns, before the created fan-out): per add/replace op —
    replace detaches the container's current fragment view (single-active-content), then
    `onAttach(Context=host activity)` + `onCreate(Bundle=null)` (the app's
    addPreferencesFromResource fires HERE through real DEX), stage → 1, host stored.
  - STARTED (execution_engine.cpp, after the host's onStart dispatch, before the started
    fan-out): per stage-1 fragment — `onCreateView` (app-DEX override via
    try_recursive_invoke with the real LayoutInflater/container args; else the platform
    PreferenceFragment law builds REAL rows), `onViewCreated`, `onActivityCreated`, `onStart`;
    the returned view attaches into the container node (`add_child` → layout_dirty →
    the canonical measure/layout/draw owns it). Stage → 3.
  - RESUMED (after the host's onResume dispatch): `onResume`. Stage → 4.
- **PreferenceFragment laws (bridge_to_api)**: `addPreferencesFromResource(int)` — ARSC
  `select_file` → AXML parse → per-entry kind/title/summary/key (with `@string` ref
  resolution through the string pool) into `__pref_*__`; keyed on the DECLARING class OR the
  receiver chain (virtual calls arrive with the RECEIVER's runtime class — the F-114c
  contrast decode). Platform `onCreateView` law (`frag_build_preference_list_view`): REAL
  LinearLayout rows (VERTICAL, match/wrap lp fields) + title/summary TextViews — no fixed
  geometry; the measure laws size everything.

## 2. Probe evidence (fixtures/frag_tx_probe, com.probe.fragtx — real toolchain aapt2+ECJ+D8)

Rows FT-01..11 (fm non-null; tx non-null; fluent same-object; commit id≥0; onAttach activity
non-null; onCreate fired; onCreateView inflater+container+view; onViewCreated identity;
onActivityCreated; onStart isAdded+getView; onResume) + FT-10/11 (findFragmentByTag identity;
isAdded+view after the drain). w4_build_probes.sh now compiles the aapt2 `--java` gen sources
(generic recipe fix — R-referencing fixtures were uncompilable before).

- PRE (binary `e1fc1915e88fe2a8` — byte-exact the CONT-41 record, rebuilt at -j2 from the
  stashed pre-wave source): FT-01..03 PASS + FT-04 "id=0" (the fake contract), FT-05..09
  never fire, FT-10/11 FAIL — ×3 identical. tananaev ×3: `d602648e8e401895`,
  DEFAULT_BACKGROUND_ONLY ×3.
- POST ×3: **FT-01..11 = 12/0 ×3** (rc=0).

## 3. tananaev A/B on the POST source

- F-NEW-304 core: `addPreferencesFromResource 0x7f110000 → 4 entries (res/SF.xml)` (REAL
  titles: "Notification settings" / "Ongoing notification — Calculator Notification can not
  be dismissed" / "Lock screen notification — Show Calculator Notification on lock screen");
  created/started/resumed drains fire; the fragment tree ATTACHES (ContentFrameLayout
  children=1). Frame face: still `d602648e8e401895` (the ink gap — see §5).
- Companion native class-measure law (BUILT AND A/B'D, then REVERTED): routed no-DEX-override
  children through the native measure_node_raw class laws (the honest AOSP View.measure
  dispatch). Result: rows measured 1080x44 at real y-pitch, texts visited by the paint walk,
  run rc=0 SUCCESS, NEW frame `0f649804d6e0486d`. **But the full gate drifted**: opencalc
  `a976d2f9fb675cb3 → 0a0b26cf69b0f378` DETERMINISTICALLY ×3 — and the drift survived the
  ConstraintLayout scope-out (non-CL nodes move too). Per the zero-drift directive the
  companion law is REVERTED (closeout note marks the guarded insertion points in
  dalvik_engine.cpp); the opencalc re-baseline decode owns the re-landing.

## 4. Regression (binary `0a6e39f38abd8636`, head 3355f2f1)

ZERO DRIFT: anchors 24/24 ×3 byte-identical (dooz 31ddd4d5b8e6d18e, microtimer, unote, gmdice,
opencalc a976d2f9fb675cb3, tttdeluxe, flappycow, g2048); battery == CONT-28..41 records;
probes == records exactly (fcol 140/0 … fnew298 19/0 KEEP=5, fnew302 48/24 documented);
simplecalc ×3 rc=0 `7960bce447ac6d8f`; frag_tx_probe 12/0 ×3.

## 5. Honest bounds + next wave

- tananaev ships at the recorded PARTIAL frame WITH the fragment machinery live (drains in
  every log; tree attached; rows parsed). The last leg is the measure/overdraw face: under a
  DEX-measuring parent (appcompat's ContentFrameLayout), platform wrap-content subtrees
  default-measure to full-screen AND the ActionBarOverlay z-band overdraws the content band —
  the companion law proved the mechanism and its fix shape; the opencalc interaction must be
  decoded before it re-lands. Dooz (case E boot budget) untouched this wave — next.
- hide/show/detach/attach transaction ops: recorded, not yet consumed (visibility hops).
- The probe runner-side screenshot ink check (row 60 dark-pixel law) stays ad-hoc this wave.
