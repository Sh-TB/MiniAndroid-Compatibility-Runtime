# LAW — IME HARNESS (input-method surface law) — S162

Status: **LAW WRITTEN + BASELINE PINNED; implementation pinned next** (the
S152→S154 pattern: this document is the contract the implementation must
satisfy; the AWAIT-UP gate dependency it was queued behind is CLOSED as of
S160).

## 0) The finding being answered (Coder-2 #459, verified live this session)

Simple Keyboard v145 (`rkr.simplekeyboard.inputmethod`, pure-DEX, sha256
`d83060833dc2bc97…`) runs with 0 errors but renders NOTHING: 0
`[EXP092-RENDER]` nodes, uniform white face `31ddd4d5b8e6d18e` (the
NO_ROOT-family face). Reproduced byte-exact on the current W5-merged main
binary `512517269d9634a1` (S162 repro, fresh store). Coder-2's finding
STANDS: the input-method lane is structurally different, not "broken".

## 1) Root cause (S162 diagnosis, from the manifest + the run log)

The manifest declares TWO entry points:
| entry | class | what the engine does today |
|---|---|---|
| MAIN/LAUNCHER activity | `…latin.settings.SettingsActivity` (a `PreferenceActivity` subclass) | launched; `PreferenceActivity` is a framework STUB — `REC-MISS` on `<init>`/`onCreate`, nothing inflates, window stays white |
| IME service | `…latin.LatinIME` (action `android.view.InputMethod`, BIND_INPUT_METHOD) | **never launched by any run path** — the engine has no service-launch or InputMethodService lifecycle machinery at all (only a `getSystemService(INPUT_METHOD_SERVICE)` name mapping) |

The keyboard UI of an IME lives in the input-method surface, which on AOSP
is created by the SYSTEM (IMMS) binding the service and driving
`onCreateInputView()/onCreateCandidatesView()/onStartInputView()`. No host
editor + no IMMS ⇒ the surface is never born ⇒ white frame is the HONEST
result of the current engine, not a bug in the app.

## 2) The harness contract (what the implementation must do)

1. **IME package detection** (install time or run time): the manifest has a
   `<service>` whose intent-filter action is `android.view.InputMethod`
   (equivalently: BIND_INPUT_METHOD permission + `android.view.im` meta-data).
   Record the service class + `settingsActivity` (if any).
2. **No-IMMS lifecycle drive** (the law: the HARNESS plays the system's
   role, explicitly, in engine code):
   - instantiate the IME service class exactly like an activity (heap
     object + `attachBaseContext` + `onCreate`) — same handler-dispatch
     registry, same U0113-ACTIVITY recording;
   - call `onCreateInputView()` → attach the RETURNED view to the render
     root (the same window-root channel activities use);
   - call `onCreateCandidatesView()` (may return null — LatinIME does) and
     render the candidate bar region;
   - call `onStartInputView(EditorInfo, restarting=false)` with a harness
     EditorInfo (inputType=classText|variationNormal, imeOptions=0) — a
     REAL EditorInfo heap object, not a string hack;
   - `onEvaluateInputViewShown()` must answer true on this path.
3. **T61 law (no artifact masquerade)**: every harness-driven call must be
   logged as `[IME-HARNESS] …` so harness effects are never mistaken for
   app behavior; the app's own uncaught rows keep their meaning; the
   baseline census (uncaught=…) must be recorded pre/post harness.
4. **Face law**: the pre-harness standing pin is `31ddd4d5b8e6d18e` (white,
   byte-stable across three binary generations: Coder-2's build, S157-B
   908d5ba6-family runs, W5-merged 512517269d9634a1). The harness is
   successful ONLY when the face changes to keyboard CONTENT (keys visible,
   >0 non-white px in the lower half) and the 10/12 anchor wall stays
   byte-exact (the harness path arms ONLY for IME packages — byte-inert
   everywhere else by construction, proven the same way as the AWAIT-UP
   gate: no-tap/no-IME paths untouched).
5. **Phase 2 (REAL interaction)**: a host probe with one `EditText` (the
   Coder-2 option-1 probe APK) — focus it, verify the harness-driven
   surface receives `onStartInputView`, then `commitText` through the real
   `InputConnection` chain and screenshot the editor content. This is the
   IME family's equivalent of the S155 dooz placement probe.

## 3) Decision for Coder-2 (#459 options)

**Option 1 + 3 hybrid, executed in MY lane**: the runtime-side harness
(this law, §2) is mine — it is engine machinery, nobody else's lane. The
Coder-2 side stays: their 1-EditText probe APK (option 1) is the phase-2
host and is welcome the moment it exists. Until the harness lands, the
registry entry for IME packages stays `HARNESS_REQUIRED` (honest, no fake
success) with this law as the pointer.

## 4) Evidence (S162)

- Repro: run_s162_ime/repro — face `31ddd4d5b8e6d18e` (== #459 pin), 0
  [EXP092-RENDER], warnings 5, launch rows show SettingsActivity + REC-MISS
  on PreferenceActivity stubs.
- Manifest facts (binary AXML string pool, from the pinned APK):
  MAIN/LAUNCHER `…settings.SettingsActivity`; service `…latin.LatinIME`
  with `android.view.InputMethod`; receiver `…SystemBroadcastReceiver`.
- APK pin: sha256 d83060833dc2bc9705e140b310ba9dea3003b329ea12799a79bf5d7de6e786bd
  (== Coder-2's registry pin), 662,274 bytes, `upload/ime_probe/`.
