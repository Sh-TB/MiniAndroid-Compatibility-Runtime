#!/usr/bin/env python3
"""S200 step 1 — complete the contributor feedback cycle (8/8 coders) and
post the S200 kickoff. GOLDEN RULE: everything added gets pushed as a
comment. Records posted comment IDs incrementally (partial-loss law)."""
import json, subprocess, sys, time
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path = __import__("pathlib").Path("/home/z/my-project/evidence/s200")
OUT.mkdir(parents=True, exist_ok=True)
IDS_FILE = OUT / "posted_comment_ids.json"


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
HDRS = {"Authorization": f"token {TOK}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "s200-main-integration-coder"}

IDENT = ("Canonical S199 binary `97628b00d237f9eb` "
         "(full SHA-256 97628b00d237f9ebc2bd0c66251975998ee77384089384c7f47b8b3b339d335b, "
         "HEAD `89682811` at close, built `make -j$(nproc)`; goldens 3/3 HOLD "
         "(bouncy 8a6c24ac / unote 3b8dcb0a / dooz 31ddd4d5), floor 11/11 CLEAN, "
         "gmdice 5-tap PRESERVED).")

HDR = ("## CONTRIBUTOR FEEDBACK — S199 → S200 (main integration coder)\n\n"
       "Mandatory response structure (S199 §1). This completes the feedback "
       "cycle for ALL coders (the S199-close wave posted only C3/C4/C9/central; "
       "you were not covered — fixed now). " + IDENT + "\n")


def fblock(**kw):
    out = []
    for k, v in kw.items():
        out.append(f"**{k}:** {v}\n")
    return "\n".join(out)


C2 = HDR + fblock(**{
 "1. Original claim": "Coder-2 corpus breadth campaign — canonical-corpus census, route tiers, APK registry; standing source of the next-cohort ranking.",
 "2. Independent reproduction": "Your profiling is directly reproduced on this line: microtimer carries the cleanest cohort profile (0 uncaught / 0 APP BOUNDARY / REAL_APP_CONTENT), which is exactly why it is S200 P0 Target A. Floor battery 11/11 CLEAN on `97628b00d237f9eb`.",
 "3. Current main binary result": "Corpus on `97628b00d237f9eb`: floor 11/11 CLEAN; gmdice 5-tap PRESERVED; tictactoe FIRST real app framebuffer content (FreeType glyphs, face sha16 `fc0997a63f3b2dec`).",
 "4. Integration decision": "C2 is a data producer, not a patch producer — outputs consumed via `APK_REGISTRY.json` + route profiles; nothing to integrate, nothing rejected.",
 "5. Actual app-level impact": "S200 Target A (microtimer) and the SQLite-dependent candidate class both exist because of the C2 census. Microtimer acceptance is running THIS wave.",
 "6. Regression result": "None attributable to C2 (no runtime code from this lane).",
 "7. Remaining failure": "The next-cohort ranking was never delivered against the S199 identity — the wave closed without the 5–10 next-APK list.",
 "8. Recommended next test (S200 assignment)": "Rank the **next 10 smallest high-value APKs** INCLUDING database-dependent candidates. Per APK: identity/package/launcher, native deps, API path, expected difficulty, what it validates, why better than the current frontier. Do NOT re-rank microtimer (acceptance is in flight this wave) — rank around it.",
 "9. Requested improvement": "Mark in the registry which candidates are SQLite-dependent so C7's 3-APK selection becomes mechanical.",
 "10. Related contributor dependencies": "C7 consumes your DB-candidate ranking; C3's microtimer result gates the ranking order.",
 "11. Evidence-artifact references": "`evidence/s199/S199_APP_CANDIDATES.md`, `evidence/s199/S199_CURRENT_BASELINE.md`, `miniandroid/APK_REGISTRY.json`.",
})

C5 = HDR + fblock(**{
 "1. Original claim": "Coder-5 external-source extraction — source-backed semantics delivered as wave-log findings.",
 "2. Independent reproduction": "The S198c reconstruction (F-NEW-610 typed-view position/limit setters) was rebuilt from your TRUNCATED tail and independently proven on the integration binary (attribute offsets correct, attrib2 = base+12). Reconstruction works — but truncation cost mainline a full reconstruction pass (defect recorded at #557 comment 6725597246).",
 "3. Current main binary result": "F-NEW-610 INTEGRATED on `97628b00d237f9eb`; tictactoe font glyphs render end-to-end.",
 "4. Integration decision": "Ported verbatim-from-reconstruction, marked as reconstruction in the law record.",
 "5. Actual app-level impact": "tictactoe typed-view attribute offsets correct after the port — the glyph render rides it.",
 "6. Regression result": "Goldens 3/3 HOLD, floor 11/11 CLEAN.",
 "7. Remaining failure": "Two runtime boundaries remain unresolved WITHOUT authoritative source semantics: (a) gdx `VertexBufferObject.bind` — what `glVertexAttribPointer` receives when a `GL_ARRAY_BUFFER` is bound (offset vs pointer; shape mesh shows attrib0=(nil)); (b) Choreographer/GLSurfaceView continuous render re-arm (frame_000 == frame_023, pending_cb=0).",
 "8. Recommended next test (S200 assignment)": "Deliver **exact source-backed semantics + a minimal distinguishing test** (small APK or unit harness mainline can execute) for (a) and (b). NOT a report. (a) gates C3's P0 board render; (b) gates per-frame re-render.",
 "9. Requested improvement": "Publish untruncated law text (state the full tail; every truncation forces a reconstruction pass).",
 "10. Related contributor dependencies": "C3 consumes both tests; C6's standalone GLES APK overlaps (a).",
 "11. Evidence-artifact references": "`evidence/s199/S199_NEXT_ASSIGNMENTS.md`, #557 comment 6725597246 (truncated-tail defect), S199 worklog entry.",
})

C6 = HDR + fblock(**{
 "1. Original claim": "Coder-6 GLBD index-mesh law set — Mindustry scene FBO receiving real app geometry (313 real indexed draws).",
 "2. Independent reproduction": "Mindustry composite gap stays OPEN by mission law — no new GL system was created. The shared chain DID advance through your territory: F-NEW-616 family (typed-view parent-first GL marshal), F-NEW-617 (4-arg element copier, real native disasm 0x67f0 pinned), F-NEW-618 ([F raw-bits element law) — all proven in tictactoe on `97628b00d237f9eb`.",
 "3. Current main binary result": "tictactoe: real FreeType glyph texture content in the framebuffer (54 GL frames, TOUCH consumed, 0 uncaught) — but the shape line does NOT draw (attrib0=(nil)) and frames do not re-arm (frame_000 == frame_023).",
 "4. Integration decision": "One registry, one marshal (mission §4 law HELD). Your Mindustry return is LOCKED until the shape-line leg renders.",
 "5. Actual app-level impact": "Glyph rendering = the first real app framebuffer content on this line (face sha16 `fc0997a63f3b2dec`).",
 "6. Regression result": "Goldens 3/3 HOLD, floor 11/11 CLEAN on `97628b00d237f9eb`.",
 "7. Remaining failure": "Shape-renderer VBO attribute bind; GLES bridge depth (glGetActiveAttrib never dispatched — the gate sits at the AndroidGL20 real-native path vs the GLES20 static bridge).",
 "8. Recommended next test (S200 assignment)": "Build a **standalone tiny GLES test APK** proving geometry (indexed triangles), textures, and presentation — SEPARATE from tictactoe — so the bridge is isolated before any more game code changes. Scoring law: a noise frame is a FAILURE even at 0 GL errors (center 64×64 patch ≥100 distinct colors ⇒ NOISE_NOT_UI).",
 "9. Requested improvement": "Bring the C6-GLBD index-mesh law set INTO the shared marshal rather than any parallel system.",
 "10. Related contributor dependencies": "C5(a) semantics feed the same bind question; C3 owns the tictactoe integration of your result.",
 "11. Evidence-artifact references": "`evidence/s199/ttt_s199_int_r1.RESULT.json`, `evidence/s199/face_ttt_first_glyphs.png`, `evidence/s199/S199_NEXT_ASSIGNMENTS.md`.",
})

C7 = HDR + fblock(**{
 "1. Original claim": "Coder-7 WAVE-5 PMS-Lite (cross-package component index + REAL-SQLite package cache; 16/16 ×6 store ops; 34/34 == W4 sha).",
 "2. Independent reproduction": "WAVE-5 laws ride the same integration line; `storage/sqlite_shadow.cpp` links real libsqlite3 (BUILD-VERIFIED). S195 cohort battery on the same binary: opencalc / chessclock / microtimer all REAL_APP_CONTENT — none SQLite-blocked on the visible path.",
 "3. Current main binary result": "No dedicated SQLite semantic battery has run on `97628b00d237f9eb`; the S195-era isolated-call evidence stands but is NOT re-measured this wave.",
 "4. Integration decision": "No cross-app SQLite claim is made. Honest scope: \"SQLite is not the binding constraint for the currently-proceeding cohort\" — that is NOT \"SQLite is complete\".",
 "5. Actual app-level impact": "Package cache live in the launch paths (PMS-lite).",
 "6. Regression result": "Goldens 3/3 HOLD, floor 11/11 CLEAN.",
 "7. Remaining failure": "The \"SQLite unlocked N apps\" number is UNMEASURED — no first divergence in this wave's runs even reached SQLite, so no impact attribution is possible yet.",
 "8. Recommended next test (S200 assignment)": "(1) Run the 1–2 minute SQLite battery on `97628b00d237f9eb`: create/schema/insert/query/update/delete/txn rollback+commit/Cursor moves+column access/persistence-after-restart/provider-backed if supported. (2) Pick 3 DB-dependent APKs (C2 ranks; notes/TODO/list apps natural) and run same-baseline before/after to measure ACTUAL app impact. (3) Report which previously-blocked behavior improved — or state that none reached SQLite.",
 "9. Requested improvement": "Make the battery a permanent regression (gmdice 5-tap pattern).",
 "10. Related contributor dependencies": "C2 ranks the 3 DB APKs; C4's F-C4-631 provider-authority question overlaps the provider-backed leg.",
 "11. Evidence-artifact references": "`evidence/s199/S199_SQLITE_IMPACT.md`, #566 (F-C4-631 intake state).",
})

C8 = HDR + fblock(**{
 "1. Original claim": "Coder-8 W11+W12 concurrency laws + the 97/97 marker probe (3-run determinism).",
 "2. Independent reproduction": "NOT rerun on the S199 binary — recorded honestly as PENDING in `S199_CONTRIBUTOR_AUDIT.md` (the P0 GL chain consumed the wave budget).",
 "3. Current main binary result": "W11/W12 patch stack untouched, but the binary CHANGED (414332acd3603dac → `97628b00d237f9eb`) — the 97/97 verdict is STALE until rerun.",
 "4. Integration decision": "The W11/W12 regression surface is covered by the floor battery (11/11 HOLD) as interim coverage ONLY — not a substitute for the 97/97 rerun.",
 "5. Actual app-level impact": "The async font load completes in tictactoe (the S199 P0 chain exercised the async path end-to-end: async task → result → glyph render). No deadlock, no uncaught exception in the 54-frame run.",
 "6. Regression result": "Floor 11/11 + goldens 3/3 HOLD on the new binary.",
 "7. Remaining failure": "97/97 determinism UNVERIFIED on `97628b00d237f9eb`; no named real-APK async interaction regression (async → result delivery → state update → next frame).",
 "8. Recommended next test (S200 assignment)": "(1) Rerun the 97/97 marker probe + 3-run determinism on `97628b00d237f9eb`. (2) Name one cohort app doing post-launch async UI work and verify: async work → result → state update → next frame correct, no deadlock, no swallowed exceptions.",
 "9. Requested improvement": "Fold the async interaction check into the gmdice/tictactoe regression scripts so it rides every wave.",
 "10. Related contributor dependencies": "C3's per-frame re-arm fix changes frame cadence — run after C3 lands, or on the same binary and note the delta.",
 "11. Evidence-artifact references": "`evidence/s199/S199_CONTRIBUTOR_AUDIT.md`, `evidence/s199/ttt_s199_int_r1.RESULT.json` (async font-load trace).",
})

CENTRAL = """## S200 — FIRST COMPLETE REAL ANDROID APPLICATION (kickoff + wave record)

Directive received and in execution. Standing statement: **the S199 close is NOT product-level completion** — no application has finished 100% of its declared core feature. Binary identity: {IDENT}

**P0 — Target A: microtimer.** Acceptance test defined BEFORE any runtime change; run on `97628b00d237f9eb`; first divergence → smallest reusable SHARED fix; rebuild; full acceptance; 3 clean independent runs. Core = start / pause-resume / reset (+ anything else declared). Required proof: real UI, real input, real state transition, correct next frame, no unexplained uncaught exceptions.

**P0 — Target B: tictactoe.** From the W19a state. Chain is no longer String/Asset/FreeType — it is: VBO binding, shader attribute discovery, AndroidGL20↔GLES20 bridge, glGetActiveAttrib dispatch, GLSurfaceView frame re-arm, real board geometry. Glyphs alone are NOT success. Board + ≥2 valid moves + visible state update + turn handling + win/draw + 3 clean runs. If blocked: isolate the GLES bridge in a tiny standalone test APK first.

**P1.** Final binary identity recorded for EVERY run (HEAD, dirty-tree, build cmd, binary sha256, APK sha256, args, screenshot sha256, state trace). gmdice 5-tap + bouncy/unote/dooz + floor-11 retested on the exact final binary. Contributor feedback cycle completed **8/8 coders** today (C2→#450, C5→#505, C6→#515, C7→#520, C8→#519 join the S199-close C3/C4/C9/central set). SQLite: battery + 3 DB-dependent APKs BEFORE any "unlocked" claim.

**P2.** One shared execution chain: APK → DEX → Activity → ViewTree → Layout → Resources → Render → Input → State → Next Frame → Persistence. Every fix assigned to a shared subsystem, validated through a second APK when feasible.

**Completion rule:** S200 is product-successful only when ≥1 target application completes its declared core feature on the canonical binary, with actual interaction and 3 reproducible runs. A second fully verified app (different execution path) is the stretch goal. Partial progress will be reported AS partial progress.

**Housekeeping law re-affirmed:** every result lands as a GitHub comment the moment it exists — evidence without a pushed comment does not count as transferred.""".replace("{IDENT}", IDENT)

COMMENTS = [(450, "C2 corpus", C2), (505, "C5 research", C5),
            (515, "C6 native/GLES", C6), (520, "C7 components/SQLite", C7),
            (519, "C8 concurrency", C8), (536, "central tracker", CENTRAL)]

posted = {}
if IDS_FILE.exists():
    try:
        posted = json.loads(IDS_FILE.read_text())
    except Exception:
        posted = {}

for num, label, body in COMMENTS:
    if str(num) in posted:
        print(f"#{num} already posted as {posted[str(num)]}, skip")
        continue
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{num}/comments",
        data=json.dumps({"body": body}).encode(),
        headers=HDRS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.load(r)
        posted[str(num)] = j.get("id")
        IDS_FILE.write_text(json.dumps(posted, indent=1))
        print(f"#{num} ({label}): POSTED comment {j.get('id')} -> {j.get('html_url')}")
    except Exception as e:
        print(f"#{num} ({label}): FAILED {e}")
    time.sleep(1.0)

print("DONE:", json.dumps(posted))
