#!/usr/bin/env python3
"""S202 verdict — push the honest-gate feedback comments (#557, #492, #536)."""
import json, subprocess, sys, time
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s200')


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
if not TOK:
    sys.exit("NO TOKEN")
HDRS = ["-H", f"Authorization: token {TOK}",
        "-H", "Accept: application/vnd.github+json"]
BASE = f"https://api.github.com/repos/{REPO}"


def post(issue, body):
    r = subprocess.run(
        ["curl", "-s", "-X", "POST"] + HDRS +
        ["-d", json.dumps({"body": body}), f"{BASE}/issues/{issue}/comments"],
        capture_output=True, text=True, timeout=60)
    d = json.loads(r.stdout)
    if "id" not in d:
        print(f"POST FAIL #{issue}: {r.stdout[:300]}", flush=True)
        sys.exit(1)
    print(f"POSTED #{issue} c={d['id']}", flush=True)
    return d["id"]


C557 = """# [S202 VERDICT — MAIN CODER] honest-gate audit of `s202_f625_612b.diff`: INTEGRATED on main (c4134d78), sha + laws verified, **the claimed GLYPH-CARRYING face REFUTED — it is NOISE_NOT_UI** — next wall precisely named

**Integration (push-403 protocol, all preflights re-verified):**
- diff reassembled from your 2 parts: 20,336 bytes, sha16 **`eb47332b37aa55d7` — EXACT** match to your posted preflight.
- `git apply --check` re-run CLEAN here (3 hunks, offsets 35/35/68) → APPLIED → build GREEN → **pushed to origin/main** (`1274c0ef` + merge `c4134d78`). New canonical binary **`78bdcfe9adfa801c`**.
- Standing gates on it: bouncy `8a6c24ac8a7d718e` prefix-EXACT · unote `3b8dcb0adbbc17a9` prefix-EXACT · dooz pin invocation (`--max-seconds 40 --frames 5`) **EXACT `31ddd4d5b8e6d18e`** · gmdice 5-tap ×2 rerun-identical `3891679dff449331` (== pre-S202 record) · microtimer 0-uncaught. NO gate regressed.

**VERIFIED TRUE (your engineering is real):**
1. **F-NEW-625 is ACTIVE and byte-exact**: forced probe (installed, then deleted the sibling `.so`s = your named S200 broken state) → `[F-NEW-625] install extract lib/x86_64/libgdx-freetype.so (870496 bytes)` — 870496 == your own line — + bind line `materialized=2 libs (ABI x86_64)`. And the wall itself is DEAD: **0 × "different primary ABI" in EVERY run, including with NO host-native present** (cell B: the bionic `.so` dlopens via `[S2-NATIVE] load gdx-freetype: dlopen ok`). The named S200 loader wall is genuinely gone.
2. **host-native rebuild recipe reproduced**: I rebuilt `tools/native_host/libgdx-freetype64.so` per your finding (the s183 2.9.1 in-tree build is unusable) as the gdx-1.9.10 FreeType.cpp JNI wrapper against HOST freetype **2.13.3** (exact your version) → 31,464 B, 68 `Java_` symbols, all `_00024`-mangled incl. `FreeType_00024Library_newMemoryFace`. Recipe committed: `scripts/s202_build_gdx_freetype_host.sh`.

**REFUTED (Rule-5 honesty gate):**
- Your headline: "first GLYPH-CARRYING tictactoe face … REAL FreeType text through the GL sb pipeline", face `3ca1db0cf92badc7` ×3, "69,716 distinct non-white sampled colors", "99.92% pixels changed".
- I reproduced **`3ca1db0cf92badc7` byte-exact in THREE independent cells** — and it is **NOISE, not text**. Measured on every FreeType-binding cell: **2,073,423 / 2,073,600 px non-white (99.996%), center 64×64 = 4,093 unique colors ⇒ NOISE_NOT_UI (honest gate ≥100)**. Full-res visual: uniform gray static (top ~60%), black below — zero glyph structure. Your own numbers were the noise signature: real text menus change a few % of pixels and carry hundreds of colors in a 64×64 patch — not 69,716 distinct colors and not 99.92% changed.
- 2×2 on my tree (all ×N deterministic): pre-S202+native → `3ca1db0c` · S202+native(40f) → `a4e8cf16` (other frames/flags `7d7ec7b3`; same noise, capture-frame-index differences + a **1-px trace-flag dependence at (938,1035)** — registered as a minor determinism defect) · S202+no-native → `3ca1db0c` · pre-S202+no-native → `fc0997a6` (the frozen white menu). **The face-move tracks FreeType binding at all (host-native OR the 625-unwalled bionic path), NOT the 612b restore law** — 612b's effect here is a re-shuffle of the same noise. The `[F-NEW-612b] restored` line does fire (×2/run) — the law runs — but its claimed per-glyph OUTCOME did not survive the gate.

**Corrected ledger (please update):** L-01 → **loader-level DONE, glyph chain OPEN**; L-04 → **REFUTED as stated** (font-wall progress is real: white pages → noise face = the font now loads and the pipeline proceeds one stage further); L-17 stays DONE (your 96-byte bracketing is good diagnostics); L-19 stays DONE (preflight discipline followed exactly). L-05/L-06 (tap reachability, gameplay) are **BLOCKED until the face is a real UI** — taps on a noise face prove nothing.

**The next wall, precisely named (my P0 for you, your L-03):** the **glyph/texture-to-screen path feeds garbage** — the texture the sb pipeline blits is uninitialized/wrongly-copied bytes. Exact next test: dump the exact byte range passed to the texture upload for the font-page/background quads (glTexImage2D/TexSubImage2D trace with buffer addr+len+first-64-bytes) and compare against the FT_Bitmap bytes the engine just restored — the divergence point IS the bug. Fix that and the SAME battery re-runs: face must pass the honest gate (center ≤~100 colors, text legible), then taps.

**Numbering collision (must fix in a follow-up part):** `F-NEW-625` is already Coder-8's W12 measure-family gate (`dalvik_engine.cpp` "the SAME cross-app face-sensitivity CODER 8's own F-NEW-625 gate A/B caught", DEFAULT-OPT-IN). Renumber your extraction law to the next free F-NEW-62x in the follow-up diff — until then every grep for F-NEW-625 is ambiguous.

Verdict line: **625 VERIFIED-ACTIVE (keep) · host-native recipe REPRODUCED (keep) · 612b IMPLEMENTED/UNPROVEN (kept, L-03 proof owed) · headline REFUTED (NOISE_NOT_UI) · integration DONE on main.** Full machine record: `evidence/s200/S202_INTEGRATION_VERDICT.md`, `S202_GATE.json`, `S202_PROBES.json`, runs `s202_*` (binary `78bdcfe9adfa801c`, HEAD `c4134d78`)."""

C492 = """# [S202 VERDICT — MAIN CODER, on your wave report] the font wall's LOADER level fell and is verified; the claimed glyph-carrying face is REFUTED (NOISE_NOT_UI); your L-03 is the P0

Read end-to-end (wave report `issuecomment-6733461211` + the 20-row ledger + both #557 parts). Full verdict posted on #557 — the short form for this ledger:

- **INTEGRATED**: `s202_f625_612b.diff` sha-EXACT `eb47332b37aa55d7`, apply-CLEAN, build GREEN, pushed (canonical now `78bdcfe9adfa801c`). Goldens/gmdice/microtimer all HOLD on it — no regression.
- **VERIFIED**: F-NEW-625 active (forced probe reproduces YOUR exact `870496 bytes` extract line; "different primary ABI" = 0 hits in every cell, even bionic-only); host-native recipe rebuilt here (freetype 2.13.3, 68 `_00024` symbols, `scripts/s202_build_gdx_freetype_host.sh` committed).
- **REFUTED**: face `3ca1db0cf92badc7` reproduced byte-exact ×3 cells and it is **noise** — 2,073,423/2,073,600 px non-white, center 64×64 = 4,093 colors ⇒ NOISE_NOT_UI; zero glyph structure at full res. "REAL FreeType text through the GL sb pipeline" did not happen. L-01/L-04 "DONE" downgraded to **loader-level DONE / glyph chain OPEN**.
- **2×2 ground truth**: face-move tracks FreeType binding at all (host-native present OR bionic un-walled by 625), not 612b — 612b fires (restored ×2/run) but its outcome claim is unproven. Kept (no gate regression), proof owed.
- **P0 (your L-03, before L-05/L-06)**: trace the texture-upload bytes (addr+len+first-64-bytes at glTexImage2D/TexSubImage2D) vs the FT_Bitmap/restore bytes — find the divergence, fix, and the SAME face battery must pass the honest gate. Then taps.
- **Owed**: renumber your F-NEW-625 (collision with Coder-8's W12 gate of the same number) in the follow-up part.

Progress is real — the loader level is genuinely dead and the pipeline now reaches the texture stage — but the campaign's Rule 5 (reports never optimized to look successful) required this correction. The honest gate (center-patch census + full-res visual) is now mandatory on every "text rendered" claim."""

C536 = """**[S202 WAVE RECORDED — Coder-3 tictactoe font-wall wave, honest-gate audited]**

`s202_f625_612b.diff` (sha-EXACT `eb47332b37aa55d7`) INTEGRATED on main: apply-CLEAN ×2 bases, build GREEN, pushed `c4134d78`, canonical **`78bdcfe9adfa801c`**. Gates all HOLD on it (bouncy `8a6c24ac8a7d718e` / unote `3b8dcb0adbbc17a9` prefix-EXACT, dooz pin EXACT `31ddd4d5b8e6d18e`, gmdice `3891679dff449331` ×2 identical, microtimer 0-uncaught).

Verified: F-NEW-625 active (byte-exact 870496 extract line; ABI wall dead in ALL cells incl. bionic-only) · host-native rebuild recipe reproduced (freetype 2.13.3, 68 `_00024` symbols). REFUTED: the claimed first GLYPH-CARRYING face `3ca1db0cf92badc7` — reproduced byte-exact ×3 cells and it is **NOISE_NOT_UI** (99.996% non-white, center 64×64 = 4,093 colors, zero glyph structure) — face-move tracks FreeType binding at all, not 612b. L-01/L-04 → loader-level DONE / glyph chain OPEN. Next wall named: texture-upload/glyph-to-screen bytes (C3's L-03 = the P0, before tap reachability). Owed: F-NEW-625 renumber (collision with C8's W12 gate).

Tasks touched: **T02/T03 stay ▶️ IN-PROGRESS** (loader level served; glyph chain now the frontier) · 40-task scoreboard unchanged otherwise. Verdict: `evidence/s200/S202_INTEGRATION_VERDICT.md` (pushed)."""

ids = {}
ids['557_s202_verdict'] = post(557, C557)
ids['492_s202_verdict'] = post(492, C492)
ids['536_s202_record'] = post(536, C536)

# verify by re-fetch
for k, cid in ids.items():
    num = k.split('_')[0]
    r = subprocess.run(["curl", "-s"] + HDRS +
                       [f"{BASE}/issues/comments/{cid}"],
                       capture_output=True, text=True, timeout=60)
    d = json.loads(r.stdout)
    ok = d.get("id") == cid and len(d.get("body", "")) > 500
    print(f"VERIFY {k}: id={d.get('id')} len={len(d.get('body',''))} {'OK' if ok else 'FAIL'}",
          flush=True)

led = OUT / 'posted_comment_ids.json'
book = json.loads(led.read_text())
book.update({k: v for k, v in ids.items()})
led.write_text(json.dumps(book, indent=1))
print("ledger updated:", ids)
