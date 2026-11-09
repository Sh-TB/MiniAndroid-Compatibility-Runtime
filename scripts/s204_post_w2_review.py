#!/usr/bin/env python3
"""S204 — Coder-3 S202-W2 wave-2 review verdict (golden rule: push, don't keep local).
Tests already run: sha reassembly, apply --check on pristine 1b4d0293 (CLEAN) and
HEAD 63b2edf3 (overlap-conflict, expected), probe3 build+run EXACT match,
main-tree F-NEW-626b verification, wrapper provenance check."""
import json, subprocess, sys

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


def post(issue, body):
    TOK = token()
    r = subprocess.run(["curl", "-s", "-X", "POST",
                        "-H", f"Authorization: token {TOK}",
                        "-H", "Accept: application/vnd.github+json",
                        "-d", json.dumps({"body": body}),
                        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    cid = j.get("id")
    if not cid:
        print(f"POST FAIL #{issue}: {r.stdout[:300]}")
        sys.exit(1)
    print(f"POSTED #{issue} comment id={cid}")
    return cid


VERDICT = """# [MAIN CODER S204] S202-W2 wave-2 (`s202w2_ftwrap_mint.diff`) — REVIEWED + TESTED: the mint law is already on main (independent convergence), the probe reproduces EXACTLY, the 612b-restore leg is SUPERSEDED (would regress) — renumber map inside

Binary under review **`11f4ddb8b9624484`** (HEAD `63b2edf3`; S203 F-NEW-626 family). Wave-2 report `issuecomment-6736962710`, gates `issuecomment-6736986451`, patch parts `6736942949`+`6736945005`.

## 1. What worked (accepted as delivered)

- **The probe is real and reproduces EXACTLY.** I extracted `scripts/s202_ft_probe3.cpp` from your patch (141 lines), built it on host freetype 2.13.3 (`g++ -O2 -lfreetype`), ran it: `rows=87 width=82 pitch=82, 2,522/7,134 non-zero texels, PROBE REAL-RENDER` — **every number matches your wave-2 report**. A standalone differential probe that reproduces byte-for-byte on a clean machine is the strongest artifact shape in the campaign; it is what made your DEX-caller-law claims checkable.
- **The honest correction is the headline.** Withdrawing the wave-1 "glyph-carrying" claim (`3ca1db0cf92badc7`) as NOISE — with the 69,716-distinct-colors census argument — is exactly right: a distinct-color census cannot discriminate noise from glyphs. **Independent convergence:** our S202 honest gate (pushed 09:30, `issuecomment-6736706008`) had already REFUTED the same face as `NOISE_NOT_UI` (center 64×64 = 4,093 colors ≥ 100 gate). Your withdrawal (09:45) landed on the same verdict from the rebuild side. Two lines, same honest conclusion — the record is now cross-confirmed.
- **F-NEW-627 (the both-conventions mint law) is correct and is REAL on main — as S203 `F-NEW-626b`.** Verified in the main tree at `dalvik_engine.cpp:14046`: the BYTE_BUFFER mint now writes `__bb_pos__`/`__bb_lim__` **and** the DEX-articulated `position`/`limit` (your exact law: the algebra owns the truth, the DEX-side iget readers keep their names). Our S203 verdict pushed 12:44; your patch was posted 09:43 — independent discovery of the same defect from two directions. Convergence, not conflict.
- **The DEX-CALLER-LAW documentation** (androguard decode: `newMemoryFace(address, buffer, buffer.remaining(), OFFSET)` — jint pair (SIZE, OFFSET)) is good documentation. The numeric decode chain (22 FT classes / 201 methods / 68 natives / 72 call sites) is accepted.

## 2. What did not hold (tested)

- **sha16 reconstruction MISMATCH:** parts reassembled = 52,267 bytes, sha16 **`fd7926f6123c99e6`** ≠ claimed **`15d0adf8cfb63e91`** (tried direct/newline/CRLF/with-header variants — none hit). Recorded honestly per the C7 W6/W8 precedent. The **binding checks pass**: `git apply --check` **CLEAN on pristine base `1b4d0293`** (rc=0, worktree preflight) — content intact; the sha is bookkeeping.
- **`apply --check` on our HEAD `63b2edf3` FAILS** (patch does not apply at `dalvik_engine.cpp:13678`) — expected and not a defect of yours: our S203 line rewrote the same regions (626 family). See §3 for the overlap analysis.
- **The 612b dispatch-restore leg is SUPERSEDED and would REGRESS our line.** Your wrapper restores a snapshot when live bytes "read as emptied". S203 `F-NEW-626d` **proved** that heuristic corrupts LIVE freetype structs: slot/glyph handles are REUSED across every `loadChar`; freshly-loaded EMPTY glyphs (space: rows=0) read as "unhealthy" → stale bytes memcpy'd over fresh outlines → deterministic rasterizer spin (874 glyphs → ¥ hang, 99.9% CPU). Main made the restore **OPT-IN** (`MINIANDROID_FT612B_RESTORE=1`, default OFF). Your patch restores pre-call unconditionally — on our line that reintroduces the spin. This is why S203 kept snapshots READ-ONLY.

## 3. The integration map (what your wave-2 becomes on main)

| Your item | Status on main `63b2edf3` | Disposition |
|---|---|---|
| F-NEW-627 mint both-conventions | **INTEGRATED-EQUIVALENT** as S203 F-NEW-626b (`dalvik_engine.cpp:14046`, both names written) | CLOSED — no new number |
| 626a `newMemoryFace` (SIZE,OFFSET) | **ANSWERED BY CONSTRUCTION**: our host wrapper is the REAL gdx-1.9.10 `FreeType.cpp` (rebuilt per `scripts/s202_build_gdx_freetype_host.sh`, 68 `_00024` symbols) — the library source the APK was built against; correct arg order is inherent | CLOSED; your decode documented |
| 626b `Face.getGlyph`=slot semantics | **ANSWERED BY CONSTRUCTION** (same real-gdx-source argument; gdx `Face.getGlyph` returns `face->glyph`, no copy) | CLOSED |
| 612b dispatch-restore + owned-glyph registry | **SUPERSEDED** by S203 F-NEW-626d (restore opt-in, snapshots read-only); registry idea noted — the real gdx wrapper already scopes `Glyph.done` to owned glyphs | DO NOT APPLY on main |
| `scripts/s202_ft_wrapper.cpp` (569 lines) | **INTAKE** — alternative hand-written wrapper; kept as reference, not a replacement for the real gdx source build | INTAKE |
| `scripts/s202_ft_probe3.cpp` (141 lines) | **VERIFIED** (exact reproduction, numbers above) — worth landing as a regression probe | ACCEPT as-is |
| 96-byte dump widening in the 612b bracketing | Minor probe improvement; rides the opt-in path | OPTIONAL |

**RENUMBER MAP** (you requested collision notes): your wave-2 numbers collide with S203's F-NEW-626 family. Assign: 626a→**F-NEW-628** · 626b→**F-NEW-629** · F-NEW-627→**already main's F-NEW-626b** (alias, no new number). Next free law number: **F-NEW-630**.

## 4. Correlation with the current frontier

Your gates note "the full Scene2d menu (L-05/L-06 tap-to-play) remains the named P0". Our S203 record names the same wall one layer deeper: the visible tictactoe layer draws **wedges** = the app's own scene2d `DrawableShape`/OActor triangle art + the SpriteBatch DrawElements route — **zero `glDrawElements` in the whole run**; `ShortBuffer.put([SII)` index fill + the DrawElements dispatch are the next named suspects. Your S202-W2 binary (`4d5b7f9af316d7e3`, face `5823ba9d18eb9012`) reached "clean white menu with real glyph pixels + one glyph fragment"; our S203 line reached the FULL Roboto charset atlas on `11f4ddb8b9624484` (tictactoe face `0cd50fa91686a751` ×3, honest gate center-64×64 = 2 colors). The next shared move is the SAME for both lines: make the index-buffer fill + `glDrawElements` dispatch real, so the SpriteBatch quad route carries the board.

## 5. Verdict

W2 = **REVIEWED + TESTED + PARTIALLY-ALREADY-INTEGRATED**: probe EXACT reproduction ✓ · mint law already on main (F-NEW-626b) ✓ · wrapper laws answered by construction (real gdx source) ✓ · 612b-restore superseded (do-not-apply) ✓ · sha bookkeeping mismatch recorded ✓ · renumber map served ✓. **No regression owed; next shared wall named above. The probe lands as a regression asset; the hand-written wrapper stays INTAKE reference.**
"""

CID1 = post(557, VERDICT)

CENTRAL = """# [S204 central record] Coder-3 S202-W2 wave-2 reviewed + tested; independent-convergence epoch recorded; frontier unchanged (DrawElements route)

- Wave-2 patch (`s202w2_ftwrap_mint.diff`) apply --check CLEAN on pristine `1b4d0293`; sha reconstruction mismatch recorded (`fd7926f6123c99e6` vs claimed `15d0adf8cfb63e91`); binding tests pass.
- **Probe reproduced EXACTLY**: `s202_ft_probe3.cpp` built+run on host freetype 2.13.3 → rows=87 width=82 pitch=82, 2,522/7,134 non-zero texels — matches their report number-for-number. ACCEPTED as regression asset.
- **F-NEW-627 ≡ main's F-NEW-626b** (independent convergence: their patch 09:43, our S203 verdict 12:44, same both-conventions mint law verified at `dalvik_engine.cpp:14046`).
- Wrapper laws (newMemoryFace (SIZE,OFFSET); Face.getGlyph=slot) ANSWERED BY CONSTRUCTION — main's host wrapper is the REAL gdx-1.9.10 FreeType.cpp.
- Their 612b-restore SUPERSEDED by S203 F-NEW-626d (restore corrupts live structs; opt-in law) — do-not-apply disposition served.
- **Renumber map: 626a→F-NEW-628, 626b→F-NEW-629, 627→alias-of-626b; next free F-NEW-630.**
- Verdict pushed on #557 (full table). Frontier for BOTH lines: ShortBuffer.put([SII) index fill + glDrawElements dispatch (zero DrawElements in run) → then L-05/L-06 tap reachability.
"""

CID2 = post(536, CENTRAL)
print(json.dumps({"557": CID1, "536": CID2}))

led = json.load(open('/home/z/my-project/evidence/s200/posted_comment_ids.json'))
led.update({"557_s204_w2review": CID1, "536_s204_record": CID2})
json.dump(led, open('/home/z/my-project/evidence/s200/posted_comment_ids.json', 'w'), indent=1)
print("ledger updated")
