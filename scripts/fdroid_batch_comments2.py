#!/usr/bin/env python3
"""Per-issue run receipts phase 2 (#618, #619, #621, #623, #624, #620)."""
import json, subprocess, re

cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def post(n, body):
    url = f"https://api.github.com/repos/{REPO}/issues/{n}/comments"
    out = subprocess.run(
        ["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {tok}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"body": body}), url],
        capture_output=True, text=True).stdout
    d = json.loads(out)
    print(f"#{n}: {d.get('html_url', d.get('message','ERR'))}")

HEAD = """## F-DROID-APK BATCH — run receipt on the fresh build

**Runtime:** `make -j1` rebuild including the ISSUE-617 bootstrap-namespace forName law, binary sha16 `4da7ef519052e174`. **Directive honored:** no source builds — every app ran from a downloaded, hash-verified APK artifact.
"""

def sub(pkg, apk, sha, note=""):
    s = f"- **APK:** `{pkg}` from the official F-Droid repo → `{apk}`\n- **SHA-256:** `{sha}` — exact match with the F-Droid index entry ✓"
    if note: s += f"\n- **Substitution reason:** {note}"
    return s

post(618, HEAD + f"""
**Substitution:** pinned upstream `mahamshamail/Android_Counter_App` publishes no APK. Closest F-Droid counter artifact used:

{sub("io.github.herrerad85.tallybook (Tallybook, vc94)", "upload/handoff_apks/io.github.herrerad85.tallybook_94.apk", "364f14fa30d37884c0be… (full value recorded with the artifact)")}

**Result: Status: PARTIAL SUCCESS ⚠️ — boot reached, content view not painted** (3 nodes; `evidence/batch618_counter/`). First divergences, in order:
1. `java.lang.IllegalArgumentException (Unknown color: #DE000000)` via `Color.parseColor` in the app's ui/view code — NOTE: the engine's parseColor law handles 8-digit `#AARRGGBB` (S89 law), so this exact call took a path that still rejected it; the caller/args trace is the next diagnostic (may be a secondary formatting wrapper).
2. `NullPointerException` (uncaught at caller `<unknown>.<unknown>`) — follows the color failure into theme/asset init.
3. `PackageManager$NameNotFoundException (androidx.appcompat.app.AppLocalesMetadataHolderService)` — F275-SVCINFO: the appcompat per-app-locales service probe; on ART this probe is normally caught, our deferred path escalates.

**Next engine work:** parseColor caller trace + F275 service-probe catch-parity; then re-run → tally counter render + increment/decrement battery (the TextView+Toast contract of this issue).""")

post(619, HEAD + f"""
**Substitution chain (documented honestly):**
- Pinned upstream `JamieDawson/Tic_Tac_Toe` publishes no APK.
- First F-Droid substitute tried: `com.emmanuelmess.tictactoe_3.apk` — but that app is a **libGDX GL game** (FreeType font generator, custom surface), NOT the plain Java/XML 3×3 button-grid contract this issue describes. Not a valid substitute.
- Final substitute: **Classic Tic Tac Toe** (`com.itsfrz.tictactoe`, vc5):

{sub("com.itsfrz.tictactoe (Classic Tic Tac Toe, vc5)", "upload/handoff_apks/com.itsfrz.tictactoe_5.apk", "2a057a9a519acd81dc54af9b3c9f58e40ebd0ce92f949aca65f6c439e8f74d45")}

**Result: Status: PARTIAL SUCCESS ⚠️ — boot reached, content not painted** (5 nodes; `evidence/batch619_ttt/`). First divergences:
1. `PackageManager$NameNotFoundException (i.I)` — F275-SVCINFO service probe (catch-parity gap, same family as #618).
2. `ClassNotFoundException (kotlin.reflect.jvm.internal.ReflectionFactoryImpl)` — **this one is ART-FAITHFUL**: verified the class is NOT shipped in the APK (0 byte-pattern hits in `classes.dex`); the Kotlin-stdlib probe must throw CNFE and catch it. Kept as expected-behavior, listed for the record.
3. **Real engine bug found:** `STREAM-OPEN FileNotFoundException (runtime/data/data/data/com.itsfrz.tictactoe/files/dat…)` — the data-dir path was assembled as `data/data/data/<pkg>` (duplicated segment) — a path-joining law defect, to fix next.
4. `F-NEW-219 NoSuchMethodException FitWindowsLinearLayout.makeOptionalFitsSystemWindows` + `f141-null-recv NPE (ArrayList…)` — the appcompat probe family + a downstream NPE.

**Next engine work:** data-dir path assembly + F275 catch-parity; then re-run → 3×3 grid render + win/draw/reset battery.""")

post(621, HEAD + f"""
**Substitution:** pinned upstream `setharvila/AndroidRockPaperScissors` publishes no APK. Closest F-Droid rock-paper-scissors game used:

{sub("com.attenomy.janken (Janken — Rock Paper Scissors, vc1)", "upload/handoff_apks/com.attenomy.janken_1.apk", "7c18c2b21096a1029cae…")}

**Result: Status: PARTIAL SUCCESS ⚠️ — boot reached, content not painted** (2 nodes; `evidence/batch621_janken/`). First divergences:
1. `ClassNotFoundException (kotlin.reflect.jvm.internal.ReflectionFactoryImpl)` — **ART-faithful** (verified absent from `classes.dex`; stdlib probes for optional kotlin-reflect and catches). Listed for the record only.
2. `java.lang.IllegalStateException` uncaught at `Lcom/attenomy/janken/MainActivity;.onCreate invoke_pc=234` → APP BOUNDARY — the real blocker; the exact invoke chain at pc=234 (a Kotlin lazy/state check inside onCreate) is the next trace target.

**Next engine work:** pc=234 invoke trace (Kotlin property/state law); then re-run → ImageButton gameplay + score/reset battery.""")

post(623, HEAD + f"""
**Substitution:** pinned upstream `weikaaai/RandomNumberGenerator` publishes no APK. Closest F-Droid random-number artifact used (Randomix does bounded random numbers from a range + result display — the same contract):

{sub("com.minar.randomix (Randomix, vc42)", "upload/handoff_apks/com.minar.randomix_42.apk", "8f137be5228c14766e7a…")}

**Result: Status: PARTIAL SUCCESS ⚠️ — PARTIAL RENDER: view tree has 12 nodes with the app's real onboarding controls `SKIP` / `DONE`**, but the frame painted white background only (text/drawable paint layer not composited; `evidence/batch623_rng/`). First divergences:
1. `PackageManager$NameNotFoundException (com.minar.randomix.h6)` — F275-SVCINFO probe (catch-parity family).
2. `ClassNotFoundException (kotlin.reflect.jvm.internal.ReflectionFactoryImpl)` — ART-faithful probe (class verified absent; record only).
3. `NoSuchMethodException FitWindowsLinearLayout.makeOptionalFitsSystemWindows` ×2 — appcompat probe family.

**Next engine work:** the white-paint face (text/drawable compositor on the onboarding layout) + F275; then re-run → range input + random result battery.""")

post(624, HEAD + f"""
**Substitution:** pinned upstream `dhairyachandra/CoinToss` publishes no APK. Closest F-Droid coin-toss app used:

{sub("org.ecos.logic.flip_a_coin (Flip a coin, vc3)", "upload/handoff_apks/org.ecos.logic.flip_a_coin_3.apk", "63730ec2ac320ecb3100…")}

**Result: Status: PARTIAL SUCCESS ⚠️ — boot reached, content not painted** (3 nodes; `evidence/batch624_coin/`). First divergences:
1. `PackageManager$NameNotFoundException (androidx.appcompat.app.AppLocalesMetadataHolderService)` — F275-SVCINFO probe family.
2. `NullPointerException — f141-null-recv: invoke on NULL org.ecos.logic.flip_a_coin.databinding.ActivityMainBinding` — the **ViewBinding inflate law gap** (databinding classes must return real binding objects; same receiver-null family as #616's FragmentManager).
3. `NoSuchMethodException FitWindowsLinearLayout.makeOptionalFitsSystemWindows` + `ClassNotFoundException (kotlin.reflect.jvm.internal.ReflectionFactoryImpl)` — probe family / ART-faithful (record only).

**Next engine work:** ViewBinding inflate law (unblocks #624 AND helps every databinding app); then re-run → coin flip + rotation animation battery.""")

post(620, HEAD + """
**MAIN CODER DIRECTIVE — status under the F-Droid-APK directive (no-build path)**

The build-toolchain blocker is GONE: per the new directive, no source builds were attempted — every app ran from a downloaded, hash-verified F-Droid/release artifact. Full batch receipts are on #614/#616/#617/#618/#619/#621/#622/#623/#624. Summary:

| App | Artifact | Status | Render |
|---|---|---|---|
| #614 Guess | pinned F-Droid apk | **SUCCESS 0 errors** | **REAL** (title + EditText + button) |
| #616 Dice Roller | **exact pinned repo release** (ogaskell/diceRoller v1.0 app-debug.apk) | PARTIAL | **REAL** (16 nodes: "Number of Die:", "Sides on Die:") |
| #617 Minos | pinned F-Droid apk | PARTIAL | blank — EventBus CNFE **FIXED by the new bootstrap-forName law** (2→1 exceptions); remaining = MazeFactory nextInt(0) |
| #618 Counter | Tallybook (sub) | PARTIAL | blank — parseColor/NPE/F275 chain |
| #619 Tic Tac Toe | Classic Tic Tac Toe (sub) | PARTIAL | blank — **real engine bug: data-dir assembled as `data/data/data/<pkg>`** |
| #621 RPS | Janken (sub) | PARTIAL | blank — IllegalStateException onCreate pc=234 |
| #622 Calculator | OpenCalc (sub) | **SUCCESS 0 errors** | **REAL — full scientific keypad, 67 nodes (√ π ! DEG sin)** |
| #623 RNG | Randomix (sub) | PARTIAL | **partial render — real SKIP/DONE nodes, white paint** |
| #624 Coin Toss | Flip a coin (sub) | PARTIAL | blank — ViewBinding inflate NPE |

**Engine law queue (from the batch, in impact order):** (1) F275-SVCINFO service-probe catch-parity (#618/#619/#623/#624), (2) ViewBinding/databinding inflate returns real object (#624), (3) getSupportFragmentManager → FragmentManager/FragmentTransaction (#616), (4) data-dir path assembly dedup (#619), (5) MazeFactory resource-bound trace (#617), (6) F-NEW-219 makeOptionalFitsSystemWindows as deferrable probe family (multiple).""")
print("PHASE2 DONE")
