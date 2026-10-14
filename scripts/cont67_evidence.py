#!/usr/bin/env python3
"""cont67_evidence.py — assemble CONT-67 evidence bundle + registry entries.
Wave scope: 3-random-app generality verification (user directive) + the two
new laws the random apps exposed (F-NEW-363 Settings URI statics, F-NEW-364
Theme.applyStyle overlay) + the dooz playability live test + capaudit 22-row
re-verification at the wave binary.
"""
import json, os, shutil

BASE = '/home/z/my-project'
EV = f'{BASE}/evidence/cont67'
os.makedirs(EV, exist_ok=True)

# 1) copy the wave's visual evidence
files = {
    'chessclock_face_fixed.png':
        f'{BASE}/run/cont67/final_chessclock/screenshot.png',
    'klondike_menu_face.png':
        f'{BASE}/run/cont67/klondike20/screenshot.png',
    'klondike_game_face.png':
        f'{BASE}/run/cont67/final_klondike_game/screenshot.png',
    'notes_face.png': f'{BASE}/run/cont67/final_notes/screenshot.png',
    'capaudit_face.png': f'{BASE}/run/cont67/capaudit/screenshot.png',
    'dooz_play_face.png': f'{BASE}/run/cont67/dooz_play/screenshot.png',
}
for dst, src in files.items():
    if os.path.exists(src):
        shutil.copy(src, f'{EV}/{dst}')

# 2) the wave's measurement dossier
with open(f'{EV}/cont67_evidence.json', 'w') as f:
    json.dump({
        'wave': 'CONT-67 (3-random-app generality + F-NEW-363/364)',
        'binary_sha16': '5038bb6e74a883c2',
        'generality_verdict': {
            'capaudit_22_rows_at_wave_binary': '22/22 PASS (cb6373f68fabd702)',
            'anchor_wall': '36/36 byte-identical x3 ZERO DRIFT (cont67_gate.sh)',
            'random_apps': [
                {'app': 'com.chessclock.android (Simple Chess Clock 2.11.2)',
                 'before': '2a3e70bafce0878a — action-bar-only face, NPE at '
                           'ChessClock.setUpGame pc=321 '
                           '(Settings$System.DEFAULT_RINGTONE_URI typed-null -> '
                           'Uri.toString APP-BOUNDARY unwind)',
                 'after': 'fe3ae1167c9e968c rc=0 ZERO uncaught — real chess '
                          'clock face: settings gear + reset vector icons, '
                          'two 10:00 panels, dark theme',
                 'law': 'F-NEW-363'},
                {'app': 'eu.veldsoft.free.klondike (Klondike Solitaire 2.0.1)',
                 'before': '31ddd4d5b8e6d18e honest empty face (deferred-UI '
                           'pending at ready_at=5000ms — measurement-budget, '
                           'not an engine gap)',
                 'after': 'splash fires at 5000ms virtual (MenuActivity '
                          'a77038da303ed1b4), tap New Game @frame19 drives '
                          'MenuActivity$1.onClick -> Intent(GameActivity) -> '
                          'REAL GAME FACE 310b27515efb8acc: green felt, 8 '
                          'card slots, four ace bitmaps, card-back pile',
                 'law': 'F-NEW-314 budget law (fair virtual-clock budget)'},
                {'app': 'org.secuso.privacyfriendlynotes (2.2.2)',
                 'before': 'eb5ebd559cad1028 — ISE "You need to use a '
                           'Theme.AppCompat theme" at createSubDecor pc=404 '
                           '(F-093 resolved 125/127 AppCompatTheme attrs MISS)',
                 'after': 'applyStyle law lands ([F364-APPLYSTYLE] '
                          'resid=0x7f120252), appcompat chain reaches NEW '
                          'territory (NameNotFoundException properly caught, '
                          'TutorialActivity runs), but the gate ISE remains: '
                          'Theme.AppCompat.Empty is a SIZE-0 bag in this app '
                          'arsc — the AppCompatTheme attr-default source for '
                          'framework-parented themes is the named residual',
                 'law': 'F-NEW-364 ROOT-CAUSED-PARTIAL'},
            ],
        },
        'dooz_playability': {
            'verdict': 'NOT PLAYABLE YET (honest)',
            'test': '180s + real tap 820,1837 (New game label) at the wave '
                    'binary',
            'result': 'tap pipeline executes (UI-EVENT TOUCH, dispatchTouchEvent '
                      'arm, attached=1) but the hit-test consumes the zeroed '
                      'bounds (TOUCHWIN-LOC hop -1x-1 placeholder, '
                      'TOUCHWIN-SIZE 0) — face byte-identical '
                      'c94da5a928ea213b. F-NEW-267 lever #2 (the R8-inlined '
                      'zero-constraint measure decode) remains the named fix.',
        },
        'capaudit': {
            'rows': 22, 'pass': 22,
            'screenshot_sha16': 'cb6373f68fabd702',
        },
        'gate': {'rows': 12, 'runs_each': 3, 'verdict': '36/36 MATCH'},
    }, f, indent=1)

# 3) registry entries
reg_path = f'{BASE}/root_registry.json'
reg = json.load(open(reg_path))
roots = reg['roots']
existing = {r.get('id') for r in roots}

new_entries = [
 {
  "id": "F-NEW-363",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P1",
  "layer": "dalvik engine (framework static-field seeding — Settings URI family)",
  "title": "SETTINGS DEFAULT-SOUND URI STATICS LAW (CONT-67, discovered by the "
           "user's 3-random-app generality directive): Settings.System."
           "DEFAULT_RINGTONE_URI / DEFAULT_NOTIFICATION_URI / "
           "DEFAULT_ALARM_ALERT_URI are FRAMEWORK statics — AOSP Settings.java "
           "mints them via Uri.withAppendedPath(CONTENT_URI, ...) = "
           "content://settings/system/{ringtone|notification_sound|"
           "alarm_alert} and they are NEVER null on any device. The engine's "
           "framework static space lacked the family: the sget answered "
           "typed-null. Live evidence (chessclock 29, first divergence): "
           "ChessClock.setUpGame reads sget DEFAULT_RINGTONE_URI then invokes "
           "Uri.toString (pc=321) — f141-null-recv NPE 'invoke Uri.toString on "
           "a null object reference' → APP-BOUNDARY unwind → the app's entire "
           "content never inflates (2a3e70bafce0878a action-bar-only face, 1 "
           "uncaught exception). FIX (one generic site): "
           "seed_framework_device_statics seeds the three URIs as REAL heap "
           "Uri objects carrying uri_raw (the Uri.parse/toString law's "
           "canonical field) — toString answers the true URI string, and the "
           "app's SharedPreferences prefAlertSound roundtrip stores a real "
           "string. VERIFIED: chessclock rc=0, ZERO uncaught exceptions, face "
           "fe3ae1167c9e968c = real chess clock (settings gear + reset vector "
           "icons + two 10:00 panels, dark theme). Wall: 36/36 byte-identical "
           "x3 (the seed is render-neutral corpus-wide).",
  "evidence": "evidence/cont67/{cont67_evidence.json, chessclock_face_fixed.png}",
  "discovered_by": "user 3-random-app generality test (CONT-67)"
 },
 {
  "id": "F-NEW-364",
  "status": "ROOT-CAUSED-PARTIAL",
  "priority": "P1",
  "layer": "resources/resource-runtime (Theme.applyStyle overlay record)",
  "title": "THEME.APPLYSTYLE OVERLAY LAW (CONT-67, notes_secuso 105): the "
           "appcompat 1.4+ attachBaseContext2 chain wraps every AppCompatActivity "
           "context (ContextThemeWrapper with R.style.Theme_AppCompat_Empty) "
           "and applies the style through ContextThemeWrapper."
           "onApplyThemeResource → Resources$Theme.applyStyle. AOSP Theme.java: "
           "applyStyle(resid, force=false) merges the style's attr bag onto the "
           "theme state (fills only missing values). The engine had NO law — "
           "the application no-op'd → F-093 obtainStyledAttributes resolved "
           "125/127 AppCompatTheme attrs as MISS → AppCompatDelegateImpl."
           "createSubDecor (pc=404) fired ISE 'You need to use a Theme.AppCompat "
           "theme (or descendant) with this activity.' → SplashActivity "
           "APP-BOUNDARY unwind, blank face. FIX LANDED (two generic sites): "
           "(1) Resources$Theme.applyStyle bridge law records 0x7f-pkg style "
           "resids onto a per-apk applied-styles record; (2) "
           "resolve_theme_attr_typed consults the record on the base-theme "
           "miss path (the exact force=false merge subset) via "
           "arsc_.bag_value. MEASURED: [F364-APPLYSTYLE] resid=0x7f120252 "
           "records; the appcompat chain reaches NEW territory (PackageManager$"
           "NameNotFoundException properly caught by AppLocalesMetadataHolder"
           "Service; TutorialActivity code runs). HONEST RESIDUAL: the "
           "createSubDecor gate ISE remains — Theme.AppCompat.Empty is a "
           "SIZE-0 bag (no items, no parent) in this app's arsc, so the "
           "AppCompatTheme attr DEFAULTS the real device serves for "
           "framework-parented themes must come from another source "
           "(candidates: the Base.V7 theme chain application via mThemeId, "
           "ResourcesCompat$ThemeCompat.rebase semantics, or the framework-"
           "table appcompat-attr equivalents) — the named next decode. Wall: "
           "36/36 byte-identical x3 (the record+miss-path consult is "
           "render-neutral for the anchor corpus).",
  "evidence": "evidence/cont67/{cont67_evidence.json, notes_face.png}",
  "discovered_by": "user 3-random-app generality test (CONT-67)"
 },
]
added = 0
for e in new_entries:
    if e['id'] not in existing:
        roots.append(e)
        added += 1
reg['total_roots'] = len(roots)
json.dump(reg, open(reg_path, 'w'), indent=1, ensure_ascii=False)
print(f'registry: {len(roots)-added} -> {len(roots)} (+{added})')
print('evidence bundle:', EV)
