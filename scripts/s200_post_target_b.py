#!/usr/bin/env python3
"""S200 — push the Target B progress + wave-record comments (golden rule)."""
import json, subprocess, sys, time
import urllib.request
import pathlib

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""


TOK = token()
HDRS = {"Authorization": f"token {TOK}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "s200-main-integration-coder"}

TTT = """## S200 P0 Target B — tictactoe GLES bridge: THREE shared laws landed (honest frontier: board pixels still not landing)

Binary **`6c808c7448850756`** (HEAD `00783ccd`). The shape-render board wall moved **three laws deep** — each probe-first on real dispatch traces, each fixed at the shared GLES boundary, zero app-specific branches:

**1. F-NEW-622 — HEAP-STRING OBJECT RESOLUTION at the GLES marshal.** gdx `VertexAttribute.alias` Strings and the `fetchAttributes` decoded names arrive as HEAP String **objects** (kind OBJECT), not STRING-kind args. The pre-622 marshal chased them as buffers → marshal-fail → `glGetAttribLocation` answered the unhandled default → the app's attribute map got garbage keys. Law: a String object IS its chars — resolved via the F-NEW-580 identity fields (`__string_value__`/`value`) at the GLES boundary, one law for every String-taking GLES20 static.

**2. F-NEW-624 — ARG-LAYOUT LAW for `glGetActiveAttrib`.** The real chain (pinned on bytecode + dispatch): gdx `GL20.glGetActiveAttrib` → AndroidGL20's delegate (own `int[]` scratch `ints/int2/int3` + `byte[] buffer`) → ART `glGetActiveAttribNative` with the **(array, offset) PAIR convention** — the observed context is 11 slots: `[prog, idx, bufsize, [I len, 0, [I type, 0, [I ?, 0, [B name, 0]`. The pre-624 handler read FIXED slots 2/3/4 → the name buffer never received the canonical bytes → the app decoded an **all-NUL String**. Law: the out-holders are **TYPED, not positional** — length = the first `[I`, type = the second `[I`, name = **THE `[B`** (the delegate builds its returned String from exactly that byte[] — its content IS the app-visible name).

**3. F-NEW-623 — the VBO OFFSET FORM at the bridge.** `GLES20.glVertexAttribPointer` has the `(…, Buffer pointer)` client form AND the `(…, int offset)` VBO form; gdx `VertexBufferObject.bind` issues the int form and **offset 0** (the position attribute) must not be skipped as a null pointer.

**Verified effect (dispatch-level):**
- `fetchAttributes` name decode now returns `a_position` / `a_color` / `a_texCoord0` — attrib-loc mints **0/1/2 for BOTH programs** (probe: `prog=1 name=a_position -> 0 … prog=2 name=a_position -> 0`).
- The shape program's attribute map is FILLED — the map-only `getAttributeLocation` hits (the real bytecode's `location<0 → continue` silent skip is dead).
- gfx trace: **129/129 `glVertexAttribPointer` calls handled, 0 marshal misses, 0 unhandled GL ops.**
- The shape's draws execute with REAL vertex data: `DRAW count=66 attrib0 v0=330,1064` — board coordinates reaching PGL.

**Honest frontier (not claimed fixed):** the shape draw's raster output still does not land in the framebuffer — the face is byte-identical to the S199 first-glyphs pin (`fc0997a63f3b2dec`). The remaining question is now NARROW and named: the fragment path for the shape program (the sb_frag texture-multiply vs the shape's own v_color semantics, or clip/raster state). That is the next P0 task — no board-render success is claimed.

**Gates on the same binary (fresh stores):** goldens **3/3 ALL HOLD** (bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz `31ddd4d5`), floor **11/11 CLEAN**, gmdice 5-tap **PASS** (5 distinct states, rerun identical), and the Target-A microtimer acceptance **re-verified end-to-end** (same tap signature `[134,147,148,264,270,253]`, pause-frozen/resume/delete all correct, SQLite restore `00:00:07`, 0 uncaught) — the GLES changes regressed nothing.

Evidence: dispatch traces (`/tmp/ttt_dbg2*.log` patterns reproduced in `evidence/s200/`), gfx trace (947 rows, 0 misses), worklog S200 Target-B entry, commit `00783ccd`."""

CENTRAL = """## S200 wave record — Target A COMPLETE, Target B three laws deep

**Target A (microtimer) — declared core feature 100% VERIFIED end-to-end** on binary `97628b00d237f9eb` → re-verified on **`6c808c7448850756`** after the Target-B GLES laws: keypad entry → label, START → Room/SQLite INSERT + TimerControl row, Handler countdown, pause-freeze (0 px churn) / resume (the swapped-in button object hit by the tap), delete, cold-restart SQLite restore (`00:00:07`), **3+1 equivalent clean runs, 0 uncaught**. First divergence fixed at the root as **F-NEW-621 device-clock law** (SystemClock.elapsedRealtime monotonic across runs sharing a data-root; AOSP monotonic-since-boot semantics; offset only at the SystemClock boundary). Full report in the Target-A comment above + `evidence/s200/S200_MICROTIMER_E2E.md`.

**Target B (tictactoe) — three shared GLES laws landed** (F-NEW-622 heap-String resolution at the GLES marshal, F-NEW-624 typed arg-layout law for the glGetActiveAttrib delegate chain, F-NEW-623 VBO offset form incl. offset 0): the fetchAttributes name decode is real (a_position/a_color/a_texCoord0 → mints 0/1/2 for both programs), the attribute maps are filled, **129/129 vap handled / 0 marshal misses**, the shape draws carry real board vertex data. Honest frontier: the board's pixels do not land in the framebuffer yet (face `fc0997a63f3b2dec` unchanged) — the named next question is the shape program's fragment path. Full report on #557.

**Gates on the final binary `6c808c7448850756`:** goldens 3/3 ALL HOLD · floor 11/11 CLEAN · gmdice 5-tap PASS · microtimer acceptance re-verified. Commits `3da4f796` (Target A) + `00783ccd` (Target B laws)."""

posted = {}
IDS = pathlib.Path('/home/z/my-project/evidence/s200/posted_comment_ids.json')
if IDS.exists():
    posted = json.loads(IDS.read_text())

for num, body, key in [(557, TTT, '557_targetB'), (536, CENTRAL, '536_wave_record')]:
    if posted.get(key):
        print(f"#{num} already posted: {posted[key]}")
        continue
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{num}/comments",
        data=json.dumps({"body": body}).encode(),
        headers=HDRS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.load(r)
        posted[key] = j.get("id")
        IDS.write_text(json.dumps(posted, indent=1))
        print(f"#{num}: POSTED {j.get('id')} -> {j.get('html_url')}")
    except Exception as e:
        print(f"#{num}: FAILED {e}")
    time.sleep(1)
