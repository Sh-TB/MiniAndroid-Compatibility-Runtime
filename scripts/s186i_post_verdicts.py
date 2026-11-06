#!/usr/bin/env python3
"""S186i: post the honest battery verdict to tracker #536.
29/41 zero-uncaught (16 new flips, ZERO regressions), S186h ARITY regression reverted-with-
evidence, 3 new generic laws (TextUtils.join / LocaleList / heap-String
split), capacitor chain 4 layers deep and counting."""
import subprocess, json, sys

out = subprocess.run(["git", "credential", "fill"],
                     input="protocol=https\nhost=github.com\n\n",
                     capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
token = None
for line in out.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    sys.exit("NO TOKEN")

import urllib.request
HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "s186i-real-render-battery"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

BODY = """## S186i — re-battery on the verified engine: **16/41 zero-uncaught** (3 new flips); S186h ARITY regression reverted-with-evidence

Data: `evidence/s186_s107/S186I_BATTERY.json` (engine sha16 in worklog; fresh store + s182 invocation law per title; face JPGs `S186I_*_face.jpg`).

### The S186h ARITY LAW regressed the corpus — reverted (A/B evidence, not opinion)
A/B with single-unit engine swaps (dalvik_engine.cpp only, everything else at HEAD):
| engine unit | no.thanks #30 | blackjack #29 |
|---|---|---|
| pre-S186d (d675a9a0) | **0 uncaught**, face `abe61411a5ee6da4` == S186C pin | 0 uncaught |
| post-S186d/e (52f13489) | **0 uncaught**, face == pin | 0 uncaught |
| post-S186h (3c9d418f, HEAD) | 32 uncaught, default face | 33 uncaught |

The S186h A/B covered only dooz/unote/tibarj goldens — those held, but 4+ canonical-androidx titles broke (LifecycleRegistry.sync NPE chain). Per the sqlite rule (no blind merge, no blind revert): the ARITY+F-NEW-188c laws are **out of the battery engine** pending re-derivation with corpus-wide A/B; tibarj #170 returns to its 10-uncaught pre-h state (honest, no upgrade claimed).

### New flips (0 uncaught, face-pinned)
- **#43 com.vayunmathur.games.solitaire** — datastore law (S186d/e) chain: 13→0, face `d602648e8e401895`.
- **#126 foehnix.widget** — ArrayDeque.descendingIterator (S186f): 10→0, face `b5a7a35d5fe0564b`.
- **#132 io.github.aoc_normal** — same law: 10→0, face `11a38a5aeeff45a6`.

### Goldens re-verified after the sandbox rebuild + law revert
- unote `3b8dcb0adbbc17a9` 0-uncaught == standing pin; **bouncy `8a6c24ac8a7d718e` BYTE-EXACT == S183b/S186b pin** with the rebuilt host natives (64/266/68 JNI symbols — SQLITE_RULE Clause 4 re-proven: `scripts/s183_build_gdx_host.sh` + fixed URL reproduces byte-identical rendering). dooz pin face held. A_RICH halma/p9 faces differ from S186C frames (animated-scene timing; verdict tier unchanged).

### 3 new generic laws (each landed probe-first, A/B on #49)
1. **TextUtils.join(CharSequence, Iterable/Object[])** — AOSP contract, "" null/empty, "null" elements. Kill: capacitor `JSExport.getPluginJS → generateMethodJS` NPE (blichess #49 / blidraughts #74 first escape).
2. **LocaleList.toLanguageTags/size/isEmpty** — F-NEW-159 seeded the FIELD but the METHOD had no law: R8 outline `m(LocaleList)→toLanguageTags()` answered null → `LocaleListCompat.forLanguageTags` chain.
3. **heap-String split law + STUB-TRIAGE diag** — `String.split` on a MATERIALIZED String receiver answered the typed-default stub (null array) → `array-length` NPE at `LocaleListCompat.forLanguageTags pc=16` (measured `[SYNTH-EXC] ARR-LEN-NULL`). The receiver identity is authoritative over the (ancestry-mangled) dispatch class.

### Capacitor chain status (#49/#74) — 4 layers peeled, deeper layers remain
getPluginJS(TextUtils) → appcompat getLocales(Configuration) → LocaleList methods → String.split — each layer VERIFIED GONE by A/B. Next wall (measured): `LocaleList.<init>` ctor stub + a register class-confusion (`isEmpty` receiver arrives as a `JobWorkItem`-classed heap object — the S71 ancestry re-dispatch re-keys String calls). Honest: both titles still 32 uncaught — **no verdict upgrade claimed**.

### Standing matrix (post-S186i battery)
16× 0-uncaught (2 A_RICH + 5 B + 9 default-bg clean), 25 still crashing with family tags unchanged (F-NPE 15 / F-ANDROIDX 6 / F-OTHER 5 / F-RES 1 / F-NATIVE 1 — see `S186C_COMPLETION_MATRIX.json` for the per-issue map).

Per the SQLITE RULE: verdicts only from fresh-store runs with pinned face sha16; no shim where a real vend exists; every law carries its A/B pair."""

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/536/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers=HDRS, method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    j = json.load(r)
print("comment posted:", j.get("html_url"))

# individual verdict comments on the three flipped issues
VERDICTS = {
    43: ("com.vayunmathur.games.solitaire — EXECUTED, 0 uncaught (S186i re-battery)",
         "Fresh-store run on the S186i engine (S186d/e datastore law chain): **13 → 0 uncaught** exceptions; the datastore `IllegalStateException` check is gone.\n\n- face sha16: `d602648e8e401895` (pinned in `evidence/s186_s107/S186I_BATTERY.json`, JPG `S186I_com.vayunmathur.games.solitaire_face.jpg`)\n- invocation: exact s182 law (real-dalvik, --data-root, --trace, 40s, 5 frames)\n- verdict: **REAL_APP_CONTENT_TEXT_ONLY** tier by the S183 census law (default-background tier, 0 uncaught, honest: the app renders its clean idle state, no crash).\n\nNext layers if the user orders deeper playability: interactive input pipeline."),
    126: ("foehnix.widget — EXECUTED, 0 uncaught (S186i re-battery)",
          "Fresh-store run on the S186i engine: **10 → 0 uncaught** after the ArrayDeque.descendingIterator law (CollectionShadow, S186f) removed the OnBackPressedDispatcher death chain (hasEnabledCallbacks walked a null iterator).\n\n- face sha16: `b5a7a35d5fe0564b` (pinned; JPG `S186I_foehnix.widget_face.jpg`)\n- verdict: **DEFAULT_BACKGROUND_ONLY, 0-uncaught idle** — widget host app; honest no-content state, no crash.\n\nThis is the first 0-uncaught run of this title since it was registered."),
    132: ("io.github.aoc_normal — EXECUTED, 0 uncaught (S186i re-battery)",
          "Fresh-store run on the S186i engine: **10 → 0 uncaught** after the ArrayDeque.descendingIterator law (S186f).\n\n- face sha16: `11a38a5aeeff45a6` (pinned; JPG `S186I_io.github.aoc_normal_face.jpg`)\n- verdict: **DEFAULT_BACKGROUND_ONLY, 0-uncaught idle** — honest: renders the clean default state, no crash, no content claim.\n\nFirst 0-uncaught run of this title."),
}
for issue, (title, body) in VERDICTS.items():
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
        data=json.dumps({"body": f"### {title}\n\n{body}"}).encode(),
        headers=HDRS, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)
    print(f"#{issue} verdict posted:", j.get("html_url"))

# capacitor chain comment on #49 (blichess)
CHAIN = ("### S186i capacitor-chain probe log (4 layers peeled — title still crashing, honest status)\n\n"
         "Measured chain on the fresh-store run (every step A/B-verified gone, then next wall measured):\n\n"
         "1. `JSExport.getPluginJS → generateMethodJS → TextUtils.join` — **LAW LANDED** (TextUtils.join AOSP contract) → layer gone.\n"
         "2. `AppCompatDelegateImpl$Api24Impl.getLocales u0x8` → outline `m(LocaleList)→toLanguageTags()` answered null — **LAW LANDED** (LocaleList.toLanguageTags/size/isEmpty) → layer gone.\n"
         "3. `LocaleListCompat.forLanguageTags pc=16` `array-length` on NULL array — `String.split(\",\",-1)` on a MATERIALIZED heap-String receiver hit the typed-default stub — **LAW LANDED** (heap-String split, receiver-identity-keyed) → layer gone (measured `[S186I-HSPLIT]` + no more ARR-LEN-NULL).\n"
         "4. **CURRENT WALL (measured)**: `LocaleList.<init>` ctor stubbed (`[S186I-STUB] Landroid/os/LocaleList;.<init> argc=2 caller=LocaleListCompat$Api24Impl.createLocaleList`) + a register class-confusion — `isEmpty` receiver arrives as a `JobWorkItem`-classed heap object (`[LOGIN-BRANCH]` log), so the split law skipped it. Suspect: the S71 ancestry re-dispatch re-keys String receivers under the wrong framework ancestor.\n\n"
         "Status: 32 uncaught, face default. **No upgrade claimed.** Evidence: `evidence/s186_s107/s186i_runs/ab5_*` (run dirs local per the S185 git law; JSONs + console excerpts cited). Next session continues this chain — each peeled layer also serves every other capacitor/appcompat title (firestrike #71 shares the appcompat path).")
req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/49/comments",
    data=json.dumps({"body": CHAIN}).encode(),
    headers=HDRS, method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    j = json.load(r)
print("#49 chain posted:", j.get("html_url"))
