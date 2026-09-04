# MASTER_CHANGELOG_KNOWLEDGE_011 — full history & provenance-graded knowledge

Generated: 2026-08-30 (UTC+3), CAMPAIGN 011. Companion: `MASTER_PROJECT_STATE_011.md`.

Provenance vocabulary (CAMPAIGN 011 §4):

- **VERIFIED** — re-confirmed in this session from Git / on-disk evidence / fresh execution.
- **PARTIALLY_VERIFIED** — core re-confirmed, some claims not re-executable here.
- **HISTORICAL** — recorded in on-disk archives/docs from earlier sessions; not re-executed now.
- **UNVERIFIED** — claimed in conversation history only; no artifact on disk could re-confirm it.
- **REJECTED** — checked and found false or not actually done.

> **Scope note (honest):** Git history in this repository starts at `b6ef143`
> (EXP-092 era). The EXP-001…EXP-091 epochs are documented extensively in
> `docs/` (121 files) but their commits predate the current repository
> history (an earlier re-initialization truncated them). They are recorded
> below as a single pre-history row. Archives `UNIFIED_003`, `UNIFIED_004`,
> `UNIFIED_006` are not on disk; `UNIFIED_005`, `UNIFIED_007` (code recovered),
> `UNIFIED_008…010` survive only as conversation-level knowledge — graded
> accordingly per §7 DO NOT INVENT.

---

## 1. Pre-history (EXP-001 … EXP-091) — HISTORICAL

| field | value |
|---|---|
| Campaign | EXP-001 … EXP-091 (numbered experiments) |
| Date | before 2026-08-23 |
| Commit | NOT IN CURRENT HISTORY (docs only) |
| What was established | APK/ZIP+DEX parsing; Dalvik opcode bring-up (EXP-031/032); Telegram API research (EXP-037/043); corpus anti-false-positive OCR gates (EXP-071/072); SQLite shadow (EXP-088 C); AXML inflation v1 via layout_cache sidecar (EXP-087/088 A1/A2); completion gates |
| Evidence | `docs/EXP0*.md`…`docs/EXP09*_*.md` (121 files, tracked) |
| Known limitation | commits unrecoverable; treat docs as primary record |
| Provenance | HISTORICAL (docs on disk; not re-executed) |

## 2. EXP-092 era — Telegram v12 first contact (history starts `b6ef143`)

| Campaign | Date | Commit(s) | Problem → Fix | Result |
|---|---|---|---|---|
| EXP-092 | 2026-08 ~ | `b6ef143`,`dd25e18`,`7a99e9a`,`cb6cd54`,`bd7ae8d`,`475923a` | v12 rendering garbage → skip full-screen container backgrounds, BitmapFont expansion, `resource_values.json`, `small_int getString`; `onNextPressed needShowAlert` root-cause fix; DIRECT tracing of `setPage`/`fillNextCodeParams`/`RequestDelegate.run` | 3-run proof PASS, `login_sms.png`; SMS-family screen first rendered on a never-seen v12.10.1 |
| EXP-093 | 2026-08 ~ | ~15 commits (`00c64d0`…`58a0534`, F007/F008/F011/F014 …) | Coder-3 F-list fixes: halt loops, missing defaults, stub debt | systematic F-item closures; `docs/` F-index |
| EXP-095 | 2026-08 ~ | `47b9143`,`6e66d2f` | visual oracle attempts | Robolectric oracle experiment (AOSP semantics compare); Paparazzi deferred (disk) |
| EXP-096 | 2026-08 ~ | `eb55fa2`,`36047cb`,`9f66b8c`,`769ac08`,`7a2d278` | streaming ZIP (data descriptor) + CRC; ImageView placeholder BEFORE/AFTER/DIFF; FreeType vs BitmapFont; palette PNG (PLTE/tRNS); SFS-009 silent-false map | generic ZIP fix; image pipeline established |
| EXP-097 | 2026-08 ~ | `72e8425`,`b862301`,`44c1bc2` | WebP+JPEG decoders (libwebp/libjpeg); truncated-APK hang fix; RLottie frames | real Lottie frames decoded |
| EXP-098 | 2026-08 ~ | `bbe0ce3` (= current `origin/main`) | RLottieImageView → RLottieDecoder runtime wiring | real Lottie on SMS screen |

Provenance: **VERIFIED** (commits + docs tracked; `bbe0ce3` confirmed on remote this session).

## 3. UNIFIED campaign 2026-08-27 (WS-C2/C3/C4/C5)

| field | value |
|---|---|
| Date | 2026-08-27 |
| Commits | `86bd646` (UC-CM-001: type-aware STUBBED defaults in `bridge_to_api` catch-all — closes F012), `f2e8ad9` (20 knowledge docs) |
| Evidence | regression 3/3 identical SHA, 12,582 trace events unchanged; rlottie built from source (Samsung/rlottie `43075538`) |
| Result | F012 closed; typography POC (FriBidi→HarfBuzz→FreeType) 4/4; WS-C3 audit (95 bridged classes, Uri/SystemClock absent); v12 forward-compat proven (12,544 classes, 41,233 px, SMS screen, SHA `06fb40da…`) |
| Known limitation | PUSH_PENDING; resource values per-version fragile (SFS-010) |
| Provenance | **VERIFIED** (commits in history + worklog) |

## 4. Archive epoch 0–2 (on-disk, VERIFIED)

| archive | contents (files) | zip SHA-256 (first 16) | provenance |
|---|---|---|---|
| UNIFIED_000 | campaign files 000–023 + 6 master docs | `d4a7bd57fb142c95` | VERIFIED (zip on disk, byte-checked) |
| UNIFIED_001 | + knowledge set 024–038 (click analysis, evidence matrix, gap analysis…) | `e45e1035fda20820` | VERIFIED |
| UNIFIED_002 | + numbered 039–064 (EXP-100 click/chain audit, EXP-101 corpus+RTL, EXP-102 oracles) | `6fb9a963131e702d` | VERIFIED |

Key UNIFIED_002 results (from `current/` docs + this session's re-checks):
- EXP-100: v12 SMS chain **UNKNOWN→PROVEN at controlled boundary** (click#3 →
  IntroActivity$4 "StartMessaging" → LoginActivity; mocked `TL_auth_sentCode`).
- EXP-101: 14-APK F-Droid corpus ×2 passes; 12 exit-0; uNote default-screen
  truth (23,472 px shared screen, not uNote UI); API demand (Uri 12/14,
  SystemClock 9/14); Persian/RTL proof 6/6; font matrix.
- EXP-102: Robolectric 4.14.1 oracle built/run 1/1; androguard census 14/15;
  docker/emulator/adb absent → NOT RUN recorded.

## 5. Archive gap — UNIFIED_003 / 004 / 006 — NOT AVAILABLE

No zips, no files, no worklog rows. Existence and content unknown.
Recorded as NOT AVAILABLE (not guessed).

## 6. UNIFIED_005 — HISTORICAL

Referenced by the campaign charter as an approved-changes source. No artifacts
on disk. Claims preserved as conversation-level knowledge only.

## 7. UNIFIED_007 — recovered & VERIFIED this session ★

| field | value |
|---|---|
| Origin | uncommitted working tree left by the interrupted session (~4,300 lines: `src/resources/{arsc,axml,layout_inflater,resource_runtime}` + shadows/engine/Makefile wiring) |
| This session | clean build OK; A/B against HEAD baseline; **UNIFIED_011 guard added** (reject non-substantive inflations); committed `23900f8` |
| Proof | GMDice real UI (`6425c0f6…`, 158,040 px, "Push buttons to roll!"/"Roll it!"); simplestopwatch real controls (`ef334f7c…`, 930,980 px); telegram v12 unchanged `06fb40da…` ×3; headingcalc/unote guarded fallback = baseline `c200c521…` |
| Known limitation | `@string/` refs unresolved (strings=0 cases); obfuscated `res/0s.xml` trees unsupported; U007 path not reached in telegram v12 journey |
| Provenance | **VERIFIED** (executed end-to-end this session) |

## 8. UNIFIED_008 / 009 / 010 — HISTORICAL, with re-check outcomes

Charter knowledge (conversation-level) said:

| claim | re-check this session | grade |
|---|---|---|
| R1: custom PNG decoder deleted, replaced by libpng | libpng **linked** (Makefile FONTS_LIBS) but renderer decode path is still the custom PNGDecoder | **REJECTED as "done"** — recorded as open action |
| R3: custom layout → Yoga adapter | no Yoga files anywhere in repo | **REJECTED as "done"** — research only (HISTORICAL) |
| R9/R10: PortableGL GLES backend | no PortableGL files in repo | **REJECTED as "done"** — research only (HISTORICAL) |
| Dooz analysis (Kotlin Intrinsics, NPE root causes, Compose blocker) | consistent with UNIFIED_002 docs (Compose-family blank renders reproduce byte-identically this session) | PARTIALLY_VERIFIED |
| Font stack retained (FriBidi/HarfBuzz/FreeType/Noto) | libs linked 1.0.16 / 10.2.0 / 2.13.x; POC proven (EXP-101) | VERIFIED (POC-level) |
| ARSC work | = UNIFIED_007 recovery above | VERIFIED |

## 9. UNIFIED_011 (this session) — VERIFIED

| item | detail |
|---|---|
| Recovery | fetched remote (`bbe0ce3` confirmed); working-tree UNIFIED_007 verified, guarded, committed `23900f8`; `.gitignore` fix `288ff6f` |
| Tests | 8-APK matrix ×(dev + clean clone): identical results; telegram 3/3 `06fb40da…` BASELINE_MATCH |
| Hygiene | ZERO-APK enforced (0 tracked APKs; external cache `apk_cache/`); `make clean` no longer deletes tracked `run/` evidence; no tracked images >100 KB; secrets scan clean (worktree; history scan below) |
| Docs | README rewritten; MASTER_PROJECT_STATE_011 / MASTER_CHANGELOG_KNOWLEDGE_011 / MASTER_HANDOFF_011; OPEN_SOURCE_MASTER; DO_NOT_REINVENT; TEST_MATRIX; APK_REGISTRY.json; status.json; release notes; evidence index with provenance |
| Backup | `git bundle` + format-patch exported OUTSIDE the source tree (see §10 of MASTER_PROJECT_STATE) |
| Tag / push | tag `v0.11-unified-011` local; PUSH_PENDING (no credentials) |
| Handoff | `UNIFIED_011_CANONICAL_HANDOFF.zip` (source + .git + docs; ZERO APK/AAB/secret) |

---

## 10. ACHIEVEMENTS table (§13)

| Achievement | Campaign | Commit / Evidence | Current status |
|---|---|---|---|
| Real APK parse incl. multi-DEX (5-DEX Telegram) | EXP-03x era + EXP-066 | docs + daily runs | VERIFIED |
| GMDice real state-changing execution → real UI render | EXP-07x era; **re-proven UNIFIED_011** | `6425c0f6…` screenshot, 158,040 px | VERIFIED |
| Telegram v12 deterministic journey (12,544 classes, 41,233 px) | EXP-092 → UNIFIED_002 → UNIFIED_011 | 3/3 SHA `06fb40da…` | VERIFIED |
| Telegram sendCode→SMS chain (controlled boundary) | EXP-092/100 | api_trace + EXP-100 click records | VERIFIED (boundary) |
| ARSC/AXML real layout inflation | UNIFIED_007 → recovered UNIFIED_011 `23900f8` | GMDice/simplestopwatch real UI | VERIFIED (partial @string) |
| Font pipeline POC (FriBidi/HarfBuzz/FreeType, Persian 6/6) | UNIFIED_002 EXP-101 | proof.png `c15673b6…` | VERIFIED (POC) |
| Touch/click dispatch + audit instrumentation | EXP-088/089 + EXP-100 `7cc4254` | click records JSONL | VERIFIED |
| Audio | research phase only (no corpus audio APK proven) | — | PARTIAL/UNVERIFIED |
| Software 3D rendering | renderer + EXP docs | docs | PARTIALLY_VERIFIED |
| Lottie animations (rlottie) | EXP-097/098 | `44c1bc2`,`bbe0ce3` | VERIFIED |
| Browser persistent jobs / WebView-family | EXP-101 bgclock fullscreen WebView render | 2,073,600 px evidence | PARTIALLY_VERIFIED |
| Observability (api_trace, evidence PNG, matrix JSON) | EXP-031.5 → UNIFIED_011 | every run | VERIFIED |
| Deterministic journeys (3-run proofs) | EXP-092/095 → UNIFIED_011 | SHA equality | VERIFIED |
| libpng replacing custom PNG decode | CAMPAIGN 010 R1 claim | linked, NOT wired | REJECTED as done / open |
| Yoga layout adapter | CAMPAIGN 010 R3 | not in repo | HISTORICAL only |
| PortableGL GLES backend | CAMPAIGN 010 R9/R10 | not in repo | HISTORICAL only |
| Dooz root-cause findings (Kotlin Intrinsics, Compose blocker) | UNIFIED_002 + 010 | blank render reproduces `c035e9ba…` | PARTIALLY_VERIFIED |
