#!/usr/bin/env python3
"""S123 GitHub report posting (#354 primary, #353 mirror)."""
import json, os, subprocess

TOKEN = open("/tmp/.gh_token").read().strip()
BASE = "https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s123_themed_apps"

REPORT = f"""S123 — THEMED-APPS WAVE (themes/templates load law family + user's requested batch: Flappy-Bird-type game, calculator app, Telegram/WhatsApp load-progress test)

Per the directive: (1) apps that use templates/themes must load — the runtime must know their structure; (2) continue the bird-through-pipes game; (3) add an Android calculator app; (4) test load progress on Telegram and WhatsApp.

## New generic engine laws (zero package checks)

**R-NEW-419 — View.setFrame onSizeChanged dispatch (AOSP View.java layout law).** When a view's frame size changes during layout, `View.setFrame` dispatches `onSizeChanged(newW, newH, oldW, oldH)` BEFORE the first `onDraw`. Custom views compute ALL their draw geometry there. Without this dispatch every `drawBitmap` dst-Rect built in `onSizeChanged` stayed null and landed at (0,0) natural size — FlappyCow's start screen rendered its four buttons as corrupt stacked tiles (before/after evidence below). Dedup: re-fires only when (w,h) actually changes. This is the theme/template structure law for the whole custom-view family: the runtime now executes the app's own layout code, not a guess.

**S123 STRING-ARG-SHAPE — Intent(String action) constructor.** A const-string register may reach the shadow bridge as kind=STRING or as a materialized String OBJECT carrying string_val (EXP-091 translation law). `new Intent("com.quchen.flappycow.Game")` left the action EMPTY (kind=OBJECT) and every action-string second-activity launch dead-ended "no component set".

**S123 ACTION-RESOLVE registration (cmd_run path parity).** The manifest's full action → activity map (PackageManager.queryIntentActivities law) is now registered on the ExecutionEngine path too; previously only the ApplicationRuntime path had it, so component-less Intents never resolved. Short names normalize against the package (PackageParser.fullActivityName law).

**R-NEW-421 — app-bundled library clinit (support/arch/databinding).** `Landroid/support/**`, `Landroid/arch/**`, `Landroid/databinding/**` are APP-BUNDLED LIBRARY bytecode, not platform stubs. The unconditional `Landroid/*` skip marked them initialized without running their `<clinit>`, so `ContainerHelpers.EMPTY_INTS/EMPTY_OBJECTS` (the backing arrays of every SimpleArrayMap) stayed null and the first `SimpleArrayMap.put` died in `System.arraycopy(null)`. LAW (AOSP ClassLinker): initialization is decided by WHERE THE BYTECODE LIVES. Both gates fixed (ensure_class_initialized + the interpreter's clinit choke point).

**R-NEW-422 — android.util.Pair.** AOSP `Pair(F,S)` stores first/second on the receiver; `Pair.create(A,B)` is the static factory. Without it every Pair field read stayed null and the first unboxing (`pair.first.intValue()`) NPE'd.

## 1) FlappyCow 3.1.1 (vc28) — bird-through-pipes game, FULL-LOAD + agent chain

- Start screen: **100% rendered** after R-NEW-419 — title, splash, PLAY, sign-in, speaker, info, socket buttons all at their lawful relative positions (the app's own `onSizeChanged` geometry executed as real bytecode).
- Agent tap on PLAY (541,910) → the app's `StartscreenView.onTouchEvent` region check ran → `startActivity(new Intent("com.quchen.flappycow.Game"))` → action resolved through the manifest map → **Game activity launched** → full lifecycle dispatch (onCreate 976 instructions, onStart, onResume) → 23,472 px state change on tap.
- **3-run repeatability: byte-identical frames** (frame SHA 13cf4746… ×3).
- Honest frontier (documented, not faked): the Game activity's `BaseGameActivity.onCreate` aborts inside `GoogleApiClient.Builder.build()` — the bundled BaseGameUtils `GameHelper.setup()` has NO try/catch (source-verified: `mSetupDone = true` only after `build()` returns), so the gms games_lite scope-validation ISE kills onCreate exactly as real ART would on a device WITHOUT Google Play Services. The gameplay canvas (cow through pipes) is reachable only after a gms-compat law family; this is the next frontier for this title.

## 2) Heading Calculator 1.0 (vc1) — themed Android calculator app

- Full load, 0 recorded errors on the tap path; themed keypad (style-driven blue buttons) fully rendered.
- Agent tap chain 1→2→3 (targets 79/80/81, `CalculatorKeypad$1` listener dispatched): `getTag` identified each key, the calculator model recomputed, and the display fields updated — before/after frames differ.
- **3-run repeatability: byte-identical frames** (frame SHA 8c6bf751… ×3) — the whole tap→display chain is deterministic.
- Honest notes: the display is a custom `CalculatorDisplay`/`ExplainableTextView` composite; its field labels still draw the honest "custom view (not rendered)" placeholder while the values render — the composite's internal TextView measure chain is the next pixel frontier.

## 3) Telegram 12.10.1 (vc70389, official universal) — load progress test

- APK parses (73MB), LaunchActivity dispatches, `ApplicationLoader`/`LaunchActivity.onCreate` bytecode executes (applicationContext statics live, DispatchQueue worker threads spawn through the Thread shadow).
- Current blockers, exactly quantified: `LocationController.getInstance` NPEs on `Api$BaseClientBuilder.getImpliedScopes` (a gms LocationServices static returned null) — repeated 6×, but LaunchActivity.onCreate proceeds through its own catch-alls to invoke_pc 548+ before the frame ends. 47 uncaught in-flight exceptions recorded; frame paints blank (theme-attr/text-draw pixel frontier unchanged from the S115 forkgram baseline).
- Verdict: **progress is real but pre-pixel** — the app executes its own init bytecode deeper than any previous wave; the render stage is still the frontier.

## 4) WhatsApp 2.26.38.74 (vc263807433, 147MB) — load progress test

- Freshly downloaded official APK (SHA-256 a013d2250a28c8f2…), analyze parses the 10+ DEX universe, `com.whatsapp.Main` activity dispatch attempted.
- Only TWO distinct exception types across the whole run (10 in-flight): the app's own `AppContext.set has not been invoked` (its context-injection singleton idiom) and one downstream `INVOKE_RETURN must not be null`. For a 147MB obfuscated app this is a narrow, well-defined frontier — not a parsing/ZIP/DEX failure.
- Verdict: **first full-load attempt, narrow app-idiom frontier, no pixels yet**. The AppContext injection law is the next single fix with the highest leverage.

## 5) Evidence (460px, English-only; before/after for the layout law)

- flappycow0 (BEFORE R-NEW-419 — corrupt stacked button tiles): {BASE}/flappycow0_before_law_corrupt_tiles.jpg
- flappycow1 (AFTER — start screen 100% lawful): {BASE}/flappycow1_start_screen_full.jpg
- flappycow2 (Game activity after PLAY tap — launched + state change): {BASE}/flappycow2_game_activity_after_play_tap.jpg
- calc1 (themed keypad, initial): {BASE}/calc1_themed_keypad_initial.jpg
- calc2 (after agent keypad input — display model updated): {BASE}/calc2_display_after_keypad_input.jpg
- telegram1 (LaunchActivity frame — honest blank + markers): {BASE}/telegram1_launch_activity_frame.jpg
- whatsapp1 (Main launch frame — honest blank): {BASE}/whatsapp1_main_launch_frame.jpg

Honest labels: FlappyCow menu EXECUTED+RENDERED VERIFIED_3RUN, launch chain EXECUTED; calculator EXECUTED+RENDERED+INTERACTIVE VERIFIED_3RUN; Telegram/WhatsApp EXECUTED-PRE-PIXEL (documented frontiers). No gameplay GIFs per directive.

Note: per the standing directive this report ends with an explanation section (the confirmation-images links above are always delivered at the end), and every fix remains a generic AOSP law with zero package checks.
"""

def post(issue):
    url = f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments"
    payload = json.dumps({"body": REPORT})
    r = subprocess.run(
        ["curl", "-s", "-X", "POST",
         "-H", f"Authorization: Bearer {TOKEN}",
         "-H", "Content-Type: application/json",
         "--data-binary", payload, url],
        capture_output=True, text=True, timeout=60)
    try:
        cid = json.loads(r.stdout).get("id")
        print(f"issue #{issue}: comment id {cid}")
    except Exception as e:
        print(f"issue #{issue}: FAILED {e}\n{r.stdout[:300]}")

post(354)
post(353)
