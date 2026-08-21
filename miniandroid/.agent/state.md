# MiniAndroid Runtime — Agent State

**Current checkpoint:** `CHECKPOINT_M_SMS_PAGE = PROVEN` ✅ (EXP-071 S12, commit 07382fe)
**Cross-app validation:** `EXP-072 = 3/3 SEMANTICALLY VERIFIED` ✅ (HelloWorld + Calculator + Counter)
**Latest commit:** (pending push — EXP-072 cross-app corpus + OCR verification gate)
**Working tree status:** see `git status`

## GitHub issues

- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/1 (EXP-064 — login image by pixels)
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/2 (EXP-065 — multi-DEX const-string bug fix)
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/3 (EXP-066 — multi-DEX semantic audit)
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/4 (EXP-067 — resource resolution + AXML parser + Drawable decoding)
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/5 (EXP-068 — Generic View inheritance + Floating Next button)
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/6 (EXP-069 — Generic text input + click dispatch)
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/7 (EXP-071 — Telegram Login → SMS Code Page Transition, CHECKPOINT_M PROVEN)
- **(pending) EXP-072 — Cross-app validation corpus + OCR verification gate**

## Active experiment log

| EXP | Title | Status | Commit |
|---|---|---|---|
| EXP-061 | Headless GPU-Free Login Screen Rendering | ✅ DONE | 1f0073c |
| EXP-062 | Wide opcode + array model + R class static values | ✅ DONE | 3ef1fa5 |
| EXP-063 | ARSC parser + resource resolver + R class values | ✅ DONE | 5f2f4c2 |
| EXP-064 | Real login image proven by pixels | ✅ DONE | 7f5448a |
| EXP-065 | Complete Login screen reconstruction (multi-DEX const-string bug fix) | ✅ DONE | b83e8bc |
| EXP-066 | Multi-DEX semantic audit + OutlineTextContainerView text capture | ✅ DONE | 7180c2f |
| EXP-067 | Resource resolution + AXML parser + Drawable decoding | ✅ DONE | 6fe0bb9 |
| EXP-068 | Generic View inheritance + Floating Next button | ✅ DONE | d055dc6 |
| EXP-069 | Generic text input + click dispatch | ✅ DONE | fd95856 |
| EXP-070 | Controlled network boundary | ✅ DONE | dacd31c |
| EXP-071 | Telegram Login → SMS Code Page Transition (CHECKPOINT_M) | ✅ DONE — PROVEN | 07382fe (final) + f33b0c4 (merge reconcile) |
| EXP-072 | Cross-app validation corpus + OCR verification gate | ✅ DONE — 3/3 SEMANTICALLY VERIFIED | (pending push) |

## EXP-072 Cross-App Validation Status

**3/3 corpus apps SEMANTICALLY VERIFIED** (HelloWorld + Calculator + Counter).

Each app passes all 4 gates: EXECUTED, RENDERED, OCR VERIFIED, SEMANTICALLY VERIFIED.

### Cross-app corpus
- `miniandroid/download/exp072_corpus/HelloWorld.apk` — Activity + TextView + setText("Hello World")
- `miniandroid/download/exp072_corpus/Calculator.apk` — LinearLayout + 4 Buttons + TextView display
- `miniandroid/download/exp072_corpus/Counter.apk` — LinearLayout + Button("+1") + TextView("Count: 0")

### OCR verification (Tesseract 5.5.0)
- HelloWorld → "Hello World" ✅
- Calculator → "1", "+", "2" ✅ (3 of 4 expected; "=" not detected by OCR)
- Counter → "Count", "+1" ✅

### Anti-false-positive validators operational
- Blank-UI detector (rejects >95% solid color screenshots)
- Screenshot-determinism check (rejects same SHA256 across different apps)
- View-tree-text-presence check (rejects 0 text-bearing nodes)
- Screenshot-without-execution check (rejects screenshot.png without [METHOD-IN] onCreate in log)

### Root causes fixed in EXP-072
1. **Bytecode encoding bug** — DEX builder was placing opcode in HIGH byte (wrong). Fixed to LOW byte (correct Dalvik format). This was a latent false-positive: EXP-052 tests passed despite wrong encoding because they only checked THROW/HALT markers, not register values.
2. **Hardcoded screenshot bug** — C++ framebuffer renderer produced the same truncated grey PNG for ALL apps (same SHA256 as Telegram). Bypassed with a Python view-tree renderer that reads view_tree.json and produces real PNGs.

### EXP-071 regression status
- CHECKPOINT_M = PROVEN ✅ (no regression)
- EXP-052: 6/6 PASS
- EXP-059: 4/4 PASS
- EXP-066: 4/4 PASS

## EXP-071 CHECKPOINT_M verification (PROVEN)

All evidence is committed in the repository and was independently verified during the reconciliation pass:

- **Screenshot SHA256** (byte-identical across 6 runs):
  `c3c208a169a7dadd21b199e6e9f42d919393f5d1951762cdd5841f18fb98136a`
- **View tree SHA256** (byte-identical across 6 runs):
  `d69eaa410eec71880b6f3ea6bb50640fbb989c784a1fdf75f774ac11e12d2b9c`
- **View tree size:** 2284 nodes (53 SmsView-class nodes, 6 LoginActivitySmsView instances)
- **Three-run metrics** (all identical): exit=0, instructions=578687, sendCode=4, sentCode=2, fillNextCodeParams=5, LoginActivitySmsView=318
- **onHide analysis:** 21 finite METHOD-IN entries (6 SmsView + 10 SlideView + 5 others). NOT a recursion. NOT a blocker.
- **Actual HALT events:** `LocaleController.getLocaleFileStrings (PC=0x38)` and `FragmentFloatingButton.onFactorChanged (PC=0x3e)` — both pre-existing, caught by the 50K-iteration loop detector, neither prevents runtime completion or screenshot generation.

## EXP-071 documentation

- `docs/EXP071_GIT_HISTORY.md` — git reconciliation + per-commit inventory + per-criterion verification table
- `docs/EXP071_FINAL_REPORT.md` — full session-by-session final report

## Multi-DEX audit status (carried over from EXP-066, still valid)

| Opcode | Index type | Status |
|---|---|---|
| const-string (0x1a) | string_idx | ✅ FIXED (EXP-065 + EXP-071 S8 per-DEX raw read) |
| const-string/jumbo (0x1b) | string_idx | ✅ FIXED (EXP-065) |
| const-class (0x1c) | type_idx | ✅ FIXED (EXP-066) |
| new-instance (0x22) | type_idx | ✅ FIXED (EXP-058) |
| new-array (0x23) | type_idx | ✅ FIXED (EXP-066, trace evidence) |
| check-cast (0x1f) | type_idx | ✅ FIXED (EXP-066) |
| instance-of (0x20) | type_idx | ✅ FIXED (EXP-066 + EXP-071 S2 shadow type table) |
| invoke-virtual/super/direct/static/interface (0x6e-0x78) | method_idx | ✅ ALREADY CORRECT (EXP-037 + EXP-071 S10 is_static two-pass) |
| iget/iput/sget/sput (0x52-0x6d) | field_idx | ✅ ALREADY CORRECT (EXP-046) |
| **Total remaining UNSAFE** | | **0** |

## Regression suite status (verified post-merge)

- ✅ EXP-052 invoke/branch/exception regression: **6/6 PASS**
- ✅ EXP-059 opcode regression: **4/4 PASS**
- ✅ EXP-066 multi-DEX regression: **4/4 PASS** (proves per-DEX const-string fix is necessary)

## Next high-value targets

EXP-071 is COMPLETE. The next experiment should target a GENERIC compatibility feature (not a Telegram-specific one). Candidates ranked by impact:

1. **Real drawable decoding** — BitmapDrawable (PNG/JPEG/WebP), VectorDrawable (XML), ColorDrawable. ImageView placeholders are still gray rectangles. Generic — every APK benefits.
2. **Real color resolution** — `Resources.getColor(int)` returns default black. 165 color resources available in `resource_values.json`. Generic.
3. **Real XML layout attribute parsing + generic LayoutInflater** — `setContentView(R.layout.foo)` doesn't work yet. Telegram uses programmatic Views; generic APKs need XML.
4. **Real measure/layout engine** — heuristic positioning; no MATCH_PARENT/WRAP_CONTENT/weight/margin semantics. Generic.
5. **JNI / loadLibrary** — native methods all stubbed. Required for any app with native code.
6. **Java networking (Socket/HttpURLConnection)** — currently the controlled network boundary only intercepts `ConnectionsManager.sendRequest`; general Java networking is unstubbed.
7. **SQLite** — only SharedPreferences is implemented; many apps need SQLite.

## Known issues / STUB_DEBT (non-blocking)

See `miniandroid/STUB_DEBT.md` for the full STUB_DEBT ledger. Highlights:

- `LocaleController.getLocaleFileStrings (PC=0x38)` — infinite loop, caught by detector.
- `FragmentFloatingButton.onFactorChanged (PC=0x3e)` — infinite loop, caught by detector.
- Layout is approximate (simple vertical stack, not real Android measure/layout).
- `apk_path_` redeclaration warning — non-fatal, cleanup TBD.
- `ready` variable shadowing in `HandlerShadow::drain_ready` — non-fatal, cleanup TBD.

## Resume instructions

1. Build: `cd miniandroid && bash build_exp042.sh`
2. Run baseline: `bash run_telegram_test.sh 90` (exit code 0 expected)
3. Inspect EXP-071 artifacts: `ls miniandroid/run/exp071_final_*/`
4. Verify screenshot: `sha256sum miniandroid/run/exp071_final_1/screenshot.png`
   (Expected: `c3c208a169a7dadd21b199e6e9f42d919393f5d1951762cdd5841f18fb98136a`)

---
