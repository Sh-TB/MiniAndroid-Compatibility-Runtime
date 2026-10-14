## CONT-47 execution-stage audit — the S83 else-chain leak family: BMI past the white screen to REAL_APP_CONTENT

Continued from remote HEAD `b4d3a493` (CONT-46 closeout `60955f06` + UUID checkpoint), per the "continue from the latest remote HEAD" directive. Every row is **STATUS — RESULT — EVIDENCE** with exact artifacts. Commit: `3a8e2c33`. Pre-fix binary `a63bf3b5…` (== the CONT-46 recorded post-fix SHA), post-fix binary `387390a0…`.

### Phase 0 — reconciliation (measured, not assumed)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | origin/main was already `60955f06` (CONT-46 closeout); local `b4d3a493` checkpoint pushed per convention | `git push 60955f06..b4d3a493` |
| TESTED | binary identity == recorded CONT-46 post-fix `a63bf3b53ac3c082` — no rebuild needed at phase 0 | sha256sum |
| TESTED | all 7 real-APK SHA pins exact (bmi `2dbd8ebe`, alex `b1383bc9`, notes `71e874f4`, sol `fdfaf7ca`, dooz `299eab21`, micro `79c6f730`, unote `be91103f`) | sha256sum ×7 |
| TESTED | Issue closeout comment `6111267327` live; no newer execution directives | GitHub API |
| TESTED | baseline face reproduced exactly: BMI `57159cc2`, `root=78 attached=0`, 0 uncaught | run/cont47/bmi_base |

### Phase 1 — the decode: the "delegate content-parent attach leg" was FOUR gates

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED (G1) | `[S83-APXACT]` setContentView shadow fired DESPITE the F-NEW-261 fall-through conditions — new permanent env-gated `MINIANDROID_S83_DIAG` diagnostic printed `f261_dex_body=1 f261_support_family=1 idx_has_class=1` at the same dispatch | run/cont47/bmi_diag/run.log:665-671 |
| TESTED (root) | else-chain bug: `if (f261) {} else if (onCreate)` — the setContentView/lifecycle/findViewById arms were INDEPENDENT ifs the fall-through never governed; the "fall through to execution" comment never held for them | dalvik_engine.cpp at 6893-6983 |
| TESTED | static proof: `AppCompatActivity.setContentView(I)` (0xc3dc0) → `AppCompatDelegateImpl.setContentView(I)` (0xc7664) = the exact AOSP chain; the runtime's `LayoutInflater.inflate(int,ViewGroup)` law already existed | cont46_disasm.py + android_shadows.cpp:5409 |
| TESTED | layout truth: `activity_bmimain` is ONE FrameLayout (views=1 correct); the real content is the committed fragment (`beginTransaction().add(R.id.container, PlaceholderFragment).commit()`) | aapt2 xmltree + BMIMain disasm |
| TESTED (G2) | after F-NEW-310 the machine still stalled: `BMIMain.onStart instructions=0` — the F-NEW-172 lifecycle-void arm intercepted the real `FragmentActivity.onStart` DEX (the fragment-state driver) | run/cont47/bmi_f311:1312 |
| TESTED (G3) | field traces: mHost obj#30 non-null, mFragmentManager obj#31 non-null, mCreated 0→1 — but `FragmentManagerImpl.mCurState` NEVER beyond 0: the EXP-045 `"FragmentManager"` substring stub voids `FragmentManagerImpl.dispatchStateChange` (the mCurState driver); support impl = 17-unit terminating try-catch method; BMI ships NO androidx | run/cont47/bmi_ft2..ft5; disasm 0x6ee94; classes.dex scan |
| TESTED (G4) | after F-NEW-312 mCurState reached 2 and `PlaceholderFragment.onCreateView` dispatched — but the host's real DEX `onGetLayoutInflater` ends in `cloneInContext` → REC-MISS → null inflater → `[ROOT-059]` null-recv inflate → result slot never wrote → `put Fragment.mView value=<unset>` (the F-NEW-262 signature) → container addView never ran | run/cont47/bmi_ft7:1396-1409 |

### Phase 2 — the fixes (minimal, generic, evidence-backed)

| Law | Change | Scope guard |
|-----|--------|-------------|
| F-NEW-310 | S83 setContentView arm gated with `!(f261_dex_body && f261_support_family)` | androidx + no-DEX-body dispatches keep the exact pre-fix S83 behavior |
| F-NEW-311 | F-NEW-172 lifecycle-void arm gated the same way | androidx keeps the arm — notes `eb5ebd55` ×3 byte-identical measured |
| F-NEW-312 | EXP-045 dispatchStateChange stub scope: `"FragmentManager"` substring → `rfind("Landroidx/fragment/app/FragmentManager",0)==0` (its actual SpecialEffectsController-loop corpus) | the support machine executes; Telegram-era androidx guard preserved |
| F-NEW-313 | `LayoutInflater.cloneInContext` → the shared F-021 singleton (AOSP observable contract in the shadow model: a functional inflater) | 3-line branch; no fake objects; setFactory2 REC-MISS left (no measured harm) |

NO APK-specific hacks, NO fake objects, NO forced lifecycle transitions. F-056/M3-19/MAX_RECURSION untouched. The findViewById arm stays deferred (no harm evidence; own probe + A/B before dispatch changes — same discipline as the sibling EXP-058 stubs).

### Phase 3 — POST verification (binary `387390a0…`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **BMI REAL_APP_CONTENT**: screenshot `b52252c2de19b03a` ×3 deterministic, rc=0, 0 uncaught, 9.9% non-background pixels, BMI button blue (111,168,220) present | run/cont47/bmi_f313 + bmi_det_r1..r3 |
| TESTED | window tree: ActionBarOverlayLayout → **ContentFrameLayout → FrameLayout → RelativeLayout(6)** → 2×EditText + 2×Spinner + Button "Calculate BMI" (real text) + result TextView — app layout AND fragment view under the sub-decor with real geometry | run/cont47/bmi_f313:1872-1879 |
| TESTED | fragment machine: mCurState 0→1→2 (ft6), onCreateView → real inflate → mView non-null → container addView (post-F-NEW-313) | run/cont47/bmi_ft6/ft7 |
| TESTED | canonical regression gate **33/33 MATCH** — dooz/micro/unote/gmdice/opencalc/tttdeluxe/flappycow/g2048/tanana ×3 byte-identical + csw ×3 + simplecalc ×3 — ZERO DRIFT | run/cont47/regression_f313.log |
| TESTED | probe battery == records exactly: fcol 140/0, f259 49/0, f259g 84/7 (known F259-L row), f266 42/0, fnew298 19/0 KEEP=5, fnew302 48/24, fnew260 13/0, fnew262 19/0 (CK identity rows intact) | regression_f313.log + run/cont47/probe_* |
| TESTED | skill self-test 13/13 rc=0 | run/cont47/skill.log |
| TESTED | support-v7 neighbor: solitaire `ba50a4d2` ×3 byte-identical, 0 uncaught | run/cont47/sol_r1..r3 |
| TESTED | androidx bypass scope: notes `eb5ebd55` ×3, alexcalc `c8d69f81` ×3 — held through all four engine changes | run/cont47/notes_r1..r3, alex_r1..r3 |

### Cross-app impact (the standing directive, now measured on ONE binary)

BMI improved (`57159cc2` shell → `b52252c2` real content); **every other corpus member byte-identical ×3** (13 anchors/controls + solitaire + notes + alexcalc). The four laws help exactly the apps whose dispatch paths were broken and drift nothing else.

### Honest bounds

1. BMI is at REAL_APP_CONTENT for the LAUNCH page; input behavior (tap → compute → result text) is NOT yet exercised — next wave's natural target.
2. solitaire F-NEW-309 (drawer gravity) remains CLASSIFIED, not fixed — its face stayed stable; the drawer fix needs its own decode + A/B.
3. F-NEW-262 m3 (notes) remains BLOCKED behind the androidx fall-through A/B — the standing scope decision, unchanged.
4. The findViewById S83 arm remains an independent if — deferred with no harm evidence.

Registry 620→624 (F-NEW-310/311/312/313 ROOT-CAUSED-FIXED). Evidence: `evidence/cont47/CONT47_RESULT.md`; scripts: `scripts/cont47_{registry.py}`; runs: `run/cont47/`.
