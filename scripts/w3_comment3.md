## WAVE 3 CHECKPOINT 3 — P0 COMPLETE: original APK executed through the normal runtime path, genuine first screen + real interaction (TESTED/OBSERVED)

**Commit:** `5e7090e3` (evidence committed under `evidence/wave3_guess/`)

### A. Provenance (original artifact, never rebuilt/modified)
- **App:** Guess (UgadaY) — the simplest already-considered candidate, carried over from Issue #614 (not an arbitrary new selection)
- **Package:** `ru.zxalexis.ugaday` · **Version:** 0.15 (versionCode 15)
- **F-Droid page:** https://f-droid.org/packages/ru.zxalexis.ugaday/ · **Upstream source:** https://github.com/zxalexis/guess
- **APK SHA-256:** `000ae2e5751f9a85c331d6205881d3db5dc81a00d10522485d9026b0494f8c3d`
- Prebuilt original artifact from the verified handoff set (`upload/handoff_apks/`); no rebuild, no repackaging, no patching.

### B. Exact execution command (normal APK-loading path, production `-O2` binary `build/miniandroid`)
```
./build/miniandroid run -v --max-seconds 70 --frames 3 --dump-view-tree --trace \
  -o evidence/wave3_guess/run1 upload/handoff_apks/ru.zxalexis.ugaday_15.apk
```

### C. Execution chain trace (console.log, every stage reached — no failure at any stage)
1. **ZIP/resources:** APK opened, resources parsed (`S124-FWRES` framework-res degrade → generated attr-default table — recorded, not a failure)
2. **Manifest:** components parsed; `EXP093-APP`: no custom Application class → `R341-APP` default Application bound (obj#14)
3. **DEX:** `[EXP086-P1]` configured engine with 1 DEX file for `ru.zxalexis.ugaday.activity_main`; **`[DalvikEngine] DEX classes: 1228`** with per-method code tracing (`METHOD [HAS CODE]` / `code_off=…`)
4. **Class resolution:** `EXP068` class→superclass map **1278 entries** (1228 APK + 50 framework); field resolution proven: `✅ FIELD RESOLVED: activity_main;.etInput type=EditText`
5. **Lifecycle:** `EXP088-B-DISPATCH` Activity.onCreate → setContentView dispatched via framework-boundary shadow calls (F-NEW-471 super-call law)
6. **View creation/layout:** layout inflater stats in `view_tree.json` (7 views created, 3 strings + 1 dimens resolved, 1 documented warning: framework `TextAppearance 0x103003e` not in verified law table)
7. **Rendering/screenshots:** 3 frames @ +300 ms virtual; `Status: SUCCESS ✅` with stub census (12 IMPLEMENTED, 2 STUBBED, 0 MISSING — success is stubby-bounded, per-call truth in api_trace.json)

### D. ViewTree provenance (view_tree.json)
LinearLayout → RelativeLayout → EditText → RelativeLayout → TextView → **TextView `"Guess the number (1 – 100)"`** → **Button `"Put the number"` (clickable=true)** — 7 views

### E. Screenshot (actual rendered first screen)
- **Run 1 screenshot SHA-256:** `87fe26766fc48d06c59d2c197a2ba34c…`; visually verified: title "Guess the number (1 – 100)" centered, dark EditText input box, blue "Put the number" button on dark background — **matches the app's genuine expected first screen** (strings/layout from the app's own APK resources)

### F. Meaningful interaction + observed state change (OBSERVED)
`--click-test` run (canonical DOWN/UP input pipeline → real clicks on clickable views):
- The app's own **`onClick(Landroid/view/View;)V` dalvik bytecode executed** (dispatch logged with `code_off`)
- **ViewTree changed: result TextView `'   '` → `'Invalid number'`** (the app's own validation logic reacting to a click with empty input)
- Interaction screenshot SHA-256 differs from run 1 (`204f8970cb238b5d39c5…` vs `87fe26766fc48d06…`) — state change is real, rendered, and captured

### G. Three repeat runs / determinism
| Run | Mode | Status | Screenshot SHA-256 |
|---|---|---|---|
| 1 | baseline | SUCCESS ✅ | `87fe26766fc48d06…` |
| 2 | +click-test | SUCCESS ✅ | `204f8970cb238b5d39c5…` (state changed by design) |
| 3 | repeat of 1 | SUCCESS ✅ | `87fe26766fc48d06…` — **byte-identical to run 1 (deterministic)** |

### First divergence
**None at the L3 chain level** — the complete chain (APK → resources → manifest → DEX → class resolution → Application → Activity lifecycle → View creation → Layout → Rendering → interaction) executed without a stopping failure. Remaining rough edges recorded honestly: 2 stubbed calls in the census, EditText inset callbacks logged as REC-MISS (non-fatal), framework TextAppearance law-table warning.

**Definition-of-success criterion for this wave: MET for one simple original APK (TESTED with commands, logs, hashes). Next checkpoint: Dalvik pilot extraction (or documented blocker).**
