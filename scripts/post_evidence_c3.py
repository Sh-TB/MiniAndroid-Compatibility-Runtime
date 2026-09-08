#!/usr/bin/env python3
"""post_evidence_c3.py — publish the UNPUBLISHED MASTER-3 evidence (sessions 6-8)
as evidence comments on Issue #9, with DIRECT URLs per roadmap §0.5."""
import json, os, urllib.request

TOKEN = open("/home/z/.gh_token").read().strip()
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"

def comment(number, body):
    req = urllib.request.Request(f"{BASE}/issues/{number}/comments",
        data=json.dumps({"body": body}).encode(), method="POST", headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "miniandroid-campaign"})
    with urllib.request.urlopen(req) as r:
        out = json.loads(r.read().decode())
        print(f"comment posted: {out['html_url']}")

REG = "https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/docs/evidence/m3_campaign/FINDINGS_REGISTRY.md"
C = lambda sha: f"https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/commit/{sha}"

c1 = f"""## MASTER-3 UNPUBLISHED RECORD (1/3) — SESSIONS 6–7: REPRODUCIBILITY + F-ROOM-CHAIN + GATE F CLOSURE

> This evidence was produced in sessions 6–7 but could not be published then
> (`GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT` in the registry). It is now
> published retroactively with DIRECT URLs, per ROADMAP §0.5. Full registry:
> {REG}

### Commits (previously unpushed, now on `main`)
| Commit | Content |
|---|---|
| [{C('3ea265be9f8baf5640ee7d0adf02d1621ff8423d')} | 3ea265be] | F-ROOM-CHAIN: token-overload postDelayed law + full java.lang.Math surface (FINDING-004/007) |
| [{C('a0d71c15ff00d885101416c97a6e9c7db4814e7c')} | a0d71c15] | MicroTimer tick visual closure: String.subSequence/Object.toString laws, looper clock quantum, LinearLayout content-measure flag, foreground drawable chain (FINDING-005/006/008a) |
| [{C('8cd76a176555a7fec5978ba5065b7b724e793ef9')} | 8cd76a17] | FINDING-009/010 — poll-timeout fast-forward law + mutation-keyed tick frames → **GATE F FULLY CLOSED** |
| [{C('5bbca4e958398f59eeddf90d6f511204802cad60')} | 5bbca4e9] | FINDING-011 — AOSP View keyed-tag law lands (AndroidX ViewTree* backbone) |
| [{C('19343076e33684581a3015c23e27ea657eda46bc')} | 19343076] | session-7 worklog |
| [{C('c59a9552204544b29eb93ffcfc359bb65e63e20c')} | c59a9552] | FORGOTTEN-001..020 end-of-campaign missed-items pass |
| [{C('d86184fcf435f9104b6e7e27a3defea8482e7603')} | d86184fc] | FINDING-008 registry entry + field-value trace extension |

### Findings closed (details in registry)
- **FINDING-001** (P3, toolchain reproducibility): container reset wiped aapt2 → `scripts/bootstrap_toolchain.sh` idempotent hash-verifiable restore. REGRESSION-VERIFIED.
- **FINDING-002** (P3, corpus cache): 7 wave-2 APKs unrestorable → `scripts/fetch_master_campaign.py` SHA-256-verified restore. IMPLEMENTED/TESTED.
- **FINDING-003** (P2, diagnostics): spec-conformant DEX disassembler `scripts/m3_disasm.py`, cross-validated 28/30 against androguard + AOSP instruction-formats. RUNTIME-PROVEN.
- **FINDING-004** (P0, Handler): hidden AOSP token overload `postDelayed(Runnable, Object, long)` misread as delay → token identity + `remove_by_token` multi-timer-safe cancellation. IMPLEMENTED/TESTED.
- **FINDING-005** (P1, Layout): horizontal LinearLayout (wrap,match) child measured 1080x0 — main/cross axis crossing → content-measure flag. TESTED + 92-frame visual proof.
- **FINDING-006** (P2, Layout): dynamic addView first-frame off-screen geometry → gone at fixed HEAD, 92/92 frames sane. TESTED.
- **FINDING-007** (P0, Java core): Math.ceil silent-stub returned 0.0 → full Math surface (OpenJDK law). MicroTimer label 00:01:22→00:00:01. IMPLEMENTED/TESTED.
- **FINDING-008** (P0, Handler/Renderer): "00:01:null" label + missing per-tick re-render → (a) String.subSequence/Object.toString laws (zero null texts in 92 frames × 3 runs); (b) closed by FINDING-009/010. VISUALLY-PROVEN.
- **FINDING-009** (P0, Looper): AOSP MessageQueue.next poll-timeout law — quiescence = EMPTY queue, not "nothing due now"; stranded 999ms tick re-post now dispatched via clock fast-forward. VISUALLY-PROVEN + REGRESSION-VERIFIED.
- **FINDING-010** (P0, visual gate): mutation-keyed tick frames — 84 per-second mutating frames, 3-run byte-identical (agg SHA 2a425979ef7d32bf2acf). VISUALLY-PROVEN.
- **FINDING-011** (P0, View/AndroidX): View keyed-tag law (mTag + mKeyedTags SparseArray) landed — tag round-trip identity-preserving; dooz double-registration cascade no longer from tags; second-attach driver identified later (FINDING-013). PARTIAL→superseded.
- **GATE F micro-timer: FULLY CLOSED** (session-7 scorecard): INSERT/Room/DEX ✓ token postDelayed ✓ tick chain ✓ countdown 00:00:82→00:00:00 per-second visible ✓ finish-branch red expired state ✓ zero null texts ✓ sane row geometry from first frame ✓ 3-run byte-identical ✓
"""

c2 = f"""## MASTER-3 UNPUBLISHED RECORD (2/3) — SESSION-8: DETERMINISM SOUNDNESS + PROVENANCE CLASS-INIT + RECEIVER-DOMAIN LAW

### Commits
| Commit | Content |
|---|---|
| [{C('e27fe846c5ffa809ae29eb2b1cb96147dc996753')} | e27fe846] | session-7→8 boundary marker |
| [{C('53e474e7ff8df864fc9c945051a4e4b4fba2c8f4')} | 53e474e7] | FINDING-012 — app-data-root law (--data-root / MINIANDROID_DATA_ROOT); durable-persistence + fresh-state byte-determinism golden; battery 60/60 |
| [{C('0e8b96cc854bd8a1e7a3d894f4a870ff64d126f9')} | 0e8b96cc] | FINDING-013/014/015 — clinit provenance law (both choke points), Class.getName law, ViewShadow receiver-domain equals/hashCode guard; dooz cascade eliminated; battery 60/60 |

### Findings closed (details in registry)
- **FINDING-012** (P0, Storage/Determinism): app-data root anchored to CWD → same-CWD 3-run replay produced 3 DIFFERENT frame sets (Room `alarm` table leaked one INSERT per run; run 2 rendered run 1's row). Fix: ONE process-wide app-data root (src/storage/data_root.cpp), all four consumers derive from Storage::app_data_root(); corpus runs hermetic. New golden pair law: (1) durable persistence — run B frame_000 renders run A's committed row; (2) byte determinism — frames(A)≡frames(C), frames(B)≡frames(D) 92/92. **REGRESSION-VERIFIED.** The session-7 byte-identical claim had a hidden CWD precondition — now guaranteed BY CONSTRUCTION.
- **FINDING-013** (P0, ClassLinker): namespace-based `<clinit>` skip (`Landroidx/ Lkotlin/…`) vs law = PROVENANCE-based (app-bundled androidx IS application bytecode). Two choke points fixed (ensure_class_initialized + execute_method_internal); Lifecycle.State enum constants materialize; dooz savedstate double-registration IAE eliminated; dooz reaches ComposeView.setContent 1080x1920. **REGRESSION-VERIFIED.**
- **FINDING-014** (P1, Reflection): `Class.getName()` missing from the Ljava/lang/Class; bridge — the single most fundamental reflective accessor; fixed (dotted binary name per OpenJDK). IMPLEMENTED/TESTED.
- **FINDING-015** (P0, Shadow dispatch): ViewShadow answered equals/hashCode for ANY receiver (two distinct string constants both heap id 0 → 0==0 → TRUE). Receiver-domain guard landed (answer only for registered View nodes); dooz AIOOBE 7→0. **REGRESSION-VERIFIED.**
- **SESSION-8 GATE SCORECARD** (registry): A/B/C/D/E/F/G/H/J/K/L/M PASS; GATE H **FULLY CLOSED** (real-APK image pipeline golden, IoU 0.959/0.997, 3-run byte-identical); GATE I PARTIAL (2nd-APK shape golden open).

Details: {REG}
"""

c3 = f"""## MASTER-3 UNPUBLISHED RECORD (3/3) — FORGOTTEN AUDIT + CAMPAIGN RESTART BASELINE (this session)

### Commit
[{C('eadaf695c4a64d8f2c006de20a6ccd01c3122805')} | eadaf695] — M3 FINDING-016 registry + GATE H real-APK image golden (IoU 0.959/0.997) + session-8 scorecard + FORGOTTEN-019 audit; **battery 61/61**

### FINDING-016 (P1, registered, design recorded)
Uncaught-exception swallowing: `§18` propagation deliberately continues the caller when NO handler exists at ANY level → dooz reported `SUCCESS ✅` with 8 in-flight exceptions (real ART: process death). Proposed law: unwind past the outermost APP frame → CRASH status + crash.log + nonzero rc. Implementation deferred pending full-corpus compat pass.

### FORGOTTEN-001..020 (missed-items audit, all evidence-grounded — see registry)
P1: FORGOTTEN-002 (17 STUBBED shadows lack demand evidence), 007 (Math.random determinism law), 008 (HashMap iteration law), 015 (Room UPDATE/DELETE law tests), 017 (foreground drawable pipeline), 019 (invoke-return single-slot hazard — AUDITED session-8: save/re-assign discipline verified on live chains, downgraded to watch-item).
P2: 003 (TextWatcher), 004 (onRequestPermissionsResult), 005 (packed-switch non-zero first_key), 006 (tap-mode clickable dump), 009 (stack-frame-count law), 010 (SQLite WAL determinism), 012 (tap-landed-on-nothing diagnostic), 014 (stable stage IDs), 016 (ColorStateList tint pipeline).
P3: 011 (tap token base reset), 013 (aapt2 checksum gate), 018 (foregroundGravity), 020 (Intrinsics fast-path).

### CAMPAIGN RESTART BASELINE (2026-09-08, this session — per ROADMAP §0.1)
- HEAD verified: `eadaf695c4a64d8f2c006de20a6ccd01c3122805` — NOT the previously reported `c59a9552` (stale report confirmed).
- Working tree: CLEAN. Branch: `main`.
- **11 previously unpushed commits (0b6f85bb..eadaf695) pushed to origin/main this session** — remote now equals local HEAD: {C('eadaf695c4a64d8f2c006de20a6ccd01c3122805')}
- Container reset re-encountered (aapt2 + build dir wiped) → restored via FINDING-001/002 scripts (toolchain bootstrap: aapt2 2.20-14304508, ecj, r8/d8, android-34.jar).
- **Full regression battery re-run: 61/61 ALL PASS** at HEAD eadaf695 (incl. F-012 persistence+fresh-state determinism golden + GATE H real-APK image golden).
- ROADMAP v3 published as this issue (living document, §102).

**Publish-debt status: CLEARED.** All registry entries previously marked `GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT` are now covered by this record + the now-pushed commits.
"""

comment(9, c1)
comment(9, c2)
comment(9, c3)
