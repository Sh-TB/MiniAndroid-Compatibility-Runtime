# CONT-47 — The S83 else-chain leak family: BMI past the white screen to REAL_APP_CONTENT

**Continuation**: Issue #375 umbrella. CONT-46 closed with the honest
bound "BMI is NOT at REAL_APP_CONTENT yet — the delegate content-parent
attach leg is the next root, precisely located." This wave executed that
decode, re-rooted the symptom into a four-gate causal chain, fixed all
four with minimal generic laws, and flipped BMI to REAL_APP_CONTENT with
zero corpus drift.

## Phase 0 — reconciliation (all measured)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| Remote HEAD | TESTED | origin/main was already 60955f06 (CONT-46 closeout, d80351ed execution); local b4d3a493 (UUID checkpoint, tmp/ probe builds) pushed per convention → 60955f06..b4d3a493 | git push output |
| Binary identity | TESTED | build/miniandroid == a63bf3b53ac3c082 (the recorded CONT-46 post-fix SHA) — no rebuild needed at phase 0 | sha256sum |
| APK inventory | TESTED | all 7 real-APK SHA pins exact (bmi 2dbd8ebe, alex b1383bc9, notes 71e874f4, sol fdfaf7ca, dooz 299eab21, micro 79c6f730, unote be91103f) | sha256sum ×7 |
| Issue #375 | TESTED | closeout comment 6111267327 verified live on the issue; no newer execution directives | api.github.com issues/comments/6111267327 |
| Baseline face reproduction | TESTED | BMI on a63bf3b5 == 57159cc2293be8b0, `[P0-1-ORDER] root=78 attached=0` rows, 0 uncaught — the recorded shell face reproduced exactly | run/cont47/bmi_base |

## Phase 1 — the decode: from "attach leg" to a four-gate chain

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| G1 — S83 shadow steal | TESTED | `[S83-APXACT] setContentView semantic shadow` fired despite the F-NEW-261 fall-through conditions; env-gated gate diagnostic (MINIANDROID_S83_DIAG, a permanent engine diagnostic in the EXP-055/S24/F040 style) printed f261_dex_body=1 f261_support_family=1 idx_has_class=1 at the SAME dispatch | run/cont47/bmi_diag/run.log:665-671 |
| Root of G1 | TESTED | the else-chain bug: `if (f261..) {} else if (onCreate) {...}` — the setContentView/lifecycle/findViewById arms are INDEPENDENT ifs outside the chain; the "fall through to execution" comment never governed them | dalvik_engine.cpp read at 6893-6983 |
| Static proof | TESTED | AppCompatActivity.setContentView(I) code_off=0xc3dc0 delegates to AppCompatDelegateImpl.setContentView(I) code_off=0xc7664 = the exact AOSP chain (ensureSubDecor → findViewById(16908290) → removeAllViews → mLayoutInflater.inflate(resId, contentParent)); LayoutInflaterShadow already implements the AOSP inflate(int,ViewGroup) law | scripts/cont46_disasm.py + android_shadows.cpp:5409-5434 |
| Layout truth | TESTED | activity_bmimain is a single FrameLayout (views=1 is CORRECT); the real content is the committed fragment (BMIMain.onCreate: getSupportFragmentManager().beginTransaction().add(R.id.container, new PlaceholderFragment()).commit()) | aapt2 dump xmltree + BMIMain disasm |
| G2 — lifecycle void | TESTED | after F-NEW-310 the fragment machine still stalled: BMIMain.onStart "instructions=0" — the F-NEW-172 lifecycle-void arm intercepted the real FragmentActivity.onStart DEX (the state driver: mCreated guard → dispatchActivityCreated → noteStateNotSaved → execPendingActions → dispatchStart) | run/cont47/bmi_f311/run.log:1312 |
| G3 — stub over-match | TESTED | field traces: mHost/mFragmentManager chain alive (obj#30/obj#31), mCreated 0→1, but FragmentManagerImpl.mCurState NEVER beyond 0 — the EXP-045 `class_descriptor.find("FragmentManager")` stub voids FragmentManagerImpl.dispatchStateChange (mCurState driver); support impl is a 17-unit terminating try-catch method; BMI has NO androidx at all | run/cont47/bmi_ft2-ft5; disasm 0x6ee94; classes.dex scan |
| G4 — null inflater | TESTED | after F-NEW-312 mCurState reached 2 and PlaceholderFragment.onCreateView dispatched — but the host's real DEX onGetLayoutInflater ends in cloneInContext → REC-MISS → null inflater → [ROOT-059] null-recv inflate → result slot never wrote → `put Fragment.mView value=<unset>` (the F-NEW-262 signature) → container addView never ran | run/cont47/bmi_ft7/run.log:1396-1409 |

## Phase 2 — the fixes (minimal, generic, evidence-backed)

| Law | Change | Scope guard |
|-----|--------|-------------|
| F-NEW-310 | gate the S83 setContentView arm with `!(f261_dex_body && f261_support_family)` | androidx + no-DEX-body dispatches keep the exact pre-fix S83 behavior |
| F-NEW-311 | gate the F-NEW-172 lifecycle-void arm the same way | androidx keeps the arm (notes eb5ebd55 ×3 byte-identical measured) |
| F-NEW-312 | EXP-045 dispatchStateChange stub scope: `"FragmentManager"` substring → `rfind("Landroidx/fragment/app/FragmentManager", 0) == 0` | the androidx loop premise (SpecialEffectsController) is the guard's actual corpus |
| F-NEW-313 | LayoutInflaterShadow gains cloneInContext → the shared F-021 singleton | AOSP observable contract in the shadow model: a functional inflater |

NO APK-specific hacks, NO fake objects, NO forced lifecycle transitions.
The F-056/M3-19/MAX_RECURSION laws untouched. The S83-DIAG diagnostic kept
(env-gated, evidence-only). The findViewById arm left on its independent if
(no harm evidence; own probe + A/B before dispatch changes).

## Phase 3 — POST verification (binary 387390a00f2de498)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| BMI REAL_APP_CONTENT | TESTED | screenshot **b52252c2de19b03a ×3 deterministic**, rc=0, 0 uncaught; 9.9% non-background pixels; top colors = content bg (225,225,225) + action bar (48,48,48) + BMI button blue (111,168,220) at 44,730 px | run/cont47/bmi_f313 + bmi_det_r1..r3 |
| BMI window tree | TESTED | window root → ActionBarOverlayLayout → **ContentFrameLayout → FrameLayout(78-successor) → RelativeLayout(6)** → 2×EditText + 2×Spinner + Button "Calculate BMI" (real text) + result TextView — the app layout AND the fragment view both under the sub-decor, real geometry (817x231 etc.) | run/cont47/bmi_f313/run.log:1872-1879 |
| Fragment machine | TESTED | mCurState 0→1→2 (ft6), PlaceholderFragment onCreateView → real inflate → mView non-null → container addView (post-F-NEW-313) | run/cont47/bmi_ft6/ft7 |
| Canonical regression gate | TESTED | **33/33 MATCH** — dooz 31ddd4d5, micro da73010a, unote 4f1a9e4e, gmdice f3b483fe, opencalc a976d2f9, tttdeluxe af609429, flappycow 13cf4746, g2048 59ca1526, tanana 5f7e0114 (each ×3 byte-identical) + csw 3442d9a9 ×3 + simplecalc e847ca03 ×3 — ZERO DRIFT | run/cont47/regression_f313.log |
| Probe battery | TESTED | == records exactly: fcol 140/0, f259 49/0, f259g 84/7 (the documented F259-L row), f266 42/0, fnew293..297 PASS, fnew298 19/0 KEEP=5 corner=PASS, fnew302 48/24 (documented counts), **fnew260 13/0, fnew262 19/0** (CK-1/2/3 identity law rows intact) | regression_f313.log + run/cont47/probe_fnew260/262 |
| Skill self-test | TESTED | 13/13 PASS rc=0 | run/cont47/skill.log |
| Support-v7 neighbor (solitaire) | TESTED | ba50a4d28ea62fe7 ×3 byte-identical (its recorded face unchanged through the delegate-path activation), 0 uncaught | run/cont47/sol_r1..r3 |
| Androidx bypass scope | TESTED | notes eb5ebd559cad1028 ×3 (recorded anchor), alexcalc c8d69f811b23f245 ×3 — the S83 androidx bypass law held through all four engine changes | run/cont47/notes_r1..r3, alex_r1..r3 |

## Cross-app impact answer (standing CONT-42 directive, now measured on THIS wave)

The four laws are framework-family generics (support-v7 dispatch scope,
stub scope, LayoutInflater law). Measured A/B matrix on one binary:
**BMI improved** (shell face 57159cc2 → real content b52252c2); **every
other corpus member byte-identical ×3** (13 anchors/controls + solitaire +
notes + alexcalc). The changes help exactly the apps whose dispatch paths
were broken, and drift nothing else — the strongest form of the genericity
evidence the standing directive asks for.

## Honest bounds

1. BMI is at REAL_APP_CONTENT for the LAUNCH page. Input behavior
   (button tap → BMI computation → result text) is NOT yet exercised —
   next wave's natural target (the click machinery exists: --click-test).
2. solitaire's face is unchanged — its F-NEW-309 drawer-gravity root is
   still CLASSIFIED, not fixed (its setContentView dispatch path is the
   same AppCompatActivity machine, but its recorded face stayed stable;
   the drawer fix needs its own decode + A/B).
3. F-NEW-262 m3 (notes) remains BLOCKED behind the androidx fall-through
   A/B — the standing scope decision, unchanged this wave.
4. The findViewById S83 arm is still an independent if — deferred with
   no harm evidence, same discipline as the sibling EXP-058 stubs.
