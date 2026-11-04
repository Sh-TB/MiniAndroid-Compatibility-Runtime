# CONT-16 — FRIEND FINDINGS AUDIT #2 (post-S153, user directive: one-time check)

Directive: check whether the coder friends solved problems the main runtime line
could not or had no time for. Audit-only wave (no fix attempted). Evidence basis:
every open+closed issue fetched via API at post-S153 HEAD `5484f511`
(400 issues: 307 open / 93 closed; 47 coder-tagged). Bodies read; verdicts below
grounded only in claims that carry reproducible commands + sha-pinned artifacts.

**Honest scope disclosure:** the coder tokens are Issues-only — Coder-6 states
explicitly (issue #445) their engine commits are LOCAL ("push blocked by the
Issues-only token"). So every achievement below is PROVEN-BY-DOCUMENTATION
(their run artifacts + confirm/reject recipes), NOT yet merged into origin/main.
Merging is the follow-up decision (§5).

---

## 1. SOLVED BY CODERS — beyond my frontier (verified claim shape)

| # | Achievement | Who | Why it beats my frontier |
|---|---|---|---|
| 1 | **Mindustry FIRST REAL VISUAL RENDER** through full GL pipeline (5 generic roots: VBO-rebind stale-pointer SIGSEGV, TypedView limit/position law, engine GLSL programs never reached PGL, GL-frame compositing; + wave-1 String-regex family, false ArrayStoreException ancestry fix) | Coder-6 (#445,#444,#442,#441) | Mindustry never got past loading in any of my waves; render now has DRAW PASS rows + non-uniform screenshot with accept/refute criteria |
| 2 | **GLES-constant translation + app-GLSL-as-C-shaders** (bouncy 186 GL errors → 0 across 60 frames; bouncy's own .vert/.frag extracted and translated 1:1; attrib/uniform slot tables) | Coder-3 (#443) | My GLES bridge carried wrong enum values — a real engine-layer bug I had not found; Dodge full-session 170/170 animated |
| 3 | **Termux roots** (`android.system.Os` stat family over real host syscalls; framework-ancestry fix for false ArrayStoreException — nested `SimpleEntry` extends Object law) | Coder-6 (#444,#442) | Termux was never in my proven set |
| 4 | **VLC const-class token root** (both dispatch sites resolve token from `args[1].class_desc`; Intrinsics frontier GONE) | Coder-6 (#438 via #444) | VLC never ran in my line |
| 5 | **libGDX distinct static-init root** (missing EGL10 constant → GdxRuntimeException → `Gdx.app` SGET-MISS; ≠ #388 SharedLibraryLoad family) | Coder-2 (#451) | New family member with confirm/reject one-liners |
| 6 | **Registry drift ×2 diagnosed** (Telegram pin no longer fetchable — live link serves HTML sha-mismatch; Tiny Music Player v1 gone from F-Droid) + frozen-mirror law + `registry_link_check.py` proposal | Coder-2 (#449,#458) | I had not detected either drift; ACTION ON ME (§6) |
| 7 | **Cross-sandbox determinism proof of MY anchor wall** — Coder-2 independently reproduced byte-identical frames: uNote screenshot sha256 `7481e9b4…` == my unote pin sha16 `7481e9b4`; MicroTimer `bbd350b6…` == my pin | Coder-2 (#454,#453) | Validates S151 anchor-wall pins on foreign hardware |

## 2. IN PROGRESS (honest mid-state, not solved)

- Coder-4 four-app program: Thunderbird/Tusky/Nextcloud/ConnectBot all at
  **M0 DONE → M1 in progress** (#430-#436, E3 run records, first divergences recorded).
- Coder-5: NewPipe `NP-M0 NOT STARTED`, Joplin `JP-M0 NOT STARTED` (#422,#423; JP-G0 Hermes gate undecided).
- Organic Maps: native load planned (Stage G1/G2) — still blocked (#442).
- Mindustry 1080p perf (software rasterizer vs 150 s budget) + full GLSL→C translation — declared frontier, not fixed.

## 3. NOT TOUCHED BY CODERS — still my exclusive frontiers

| Frontier | Mentions in coder issues |
|---|---|
| **AWAIT-UP GATE** (post-DOWN UP-dispatch starvation; my S152 pinned next law) | **0** |
| **NO_ROOT Compose family face `31ddd4d5` / WindowRoot** | context mentions only (#459, #395) — no fix |
| trackbook download truncation | 0 |

## 4. Decision REQUESTED from me (coder → main coder)

- **#459 IME harness decision** (Simple Keyboard v145: 0 ViewTree nodes, white frame, 0 errors — IME apps need an input-view harness). ACCEPTED IN PRINCIPLE: an IME harness law is queued behind the AWAIT-UP gate law; the harness must inflate the input view hierarchy explicitly (no IMMS) and render the candidate bar.

## 5. The merge gap (single biggest follow-up)

Coder fixes live in their local sandboxes. Options: (a) they attach
`git format-patch` bundles to issues; (b) I re-apply from their LAW+VERIFY
recipes (each fix ships a one-command verify — feasible but duplicated work).
Recommended: (a) for Coder-6 GL stack + Coder-3 GLES translation (large diffs),
(b) for small laws (const-class token, regex family, registry checker).

## 6. Actions queued on me from this audit

1. `frozen_url` + `frozen_sha256` fields in APK_REGISTRY + `scripts/registry_link_check.py` (#449/#458).
2. AWAIT-UP GATE law (unchanged pinned next; nobody else is on it).
3. IME harness decision implementation (#459).
4. Merge path decision for coder patches (§5).

Verdict: **YES — the friends solved real problems I could not or had no time for**
(Mindustry render, GLES constants, Termux/VLC roots), plus they re-proved my
anchor wall byte-exact. Engine diffs not merged yet; merging is the next decision.

## 7. S158 VERIFICATION LOOP (2026-11-04) — first confirm/reject cycle under the 40/60/20 law

| Coder item | What I actually ran | Verdict |
|---|---|---|
| **#514 W5 (Coder-4, F-C4-566/567/568, CHM compute-bypass)** | extracted the delivered 314-line `w5_only` block from comment 6616230230; `git apply --check` CLEAN on detached `eb72df8b`; full -O2 rebuild (`build_w5`, binary `254a9be71721d961`, insurance copy kept); Gate B dooz E5 -> face `11a38a5a` byte-inert; Gate C ConnectBot stderr A/B ref-vs-W5 **normalized-identical** (method: strip ASLR ptrs/RSS/ms/store-paths/ns-timestamps + thread-order sort; validated by a same-binary-twice control — raw stderr is nondeterministic even for one binary, so their stderr sha16 pins are normalized by construction); Gate E microtimer face == standing pin `bbd350b6` prefix-exact, g2048 W5 == ref byte-exact (`ec0f05ad` both — ledger pin `f43face08` uses s151 wall flags not used in this smoke) | **تایید (APPROVED) at the delta level** — merge-safe on `eb72df8b`; F-C4-566 substance (TB Koin 510 put -> 596 nodes) remains coder-attested: TB/NC/TK APKs purged in S153, and the claimed 1610-line `w5_full` stack was NOT actually delivered in the comments (only the 314-line delta is present) |
| **Coder-4 #510 W3** | (S157-B, carried) clean-apply + compile + 12/12 anchors byte-exact | تایید at merge-gate level; 4APP numbers unverifiable |
| **Coder-5 #503 COMPOSE RENDER CLUSTER** | still PENDING in their own issue — nothing to test | رد نیست؛ awaiting artifact |

New ready-made-lever verdicts this session (dooz 40% leg, "don't reinvent the wheel"):
- jemalloc 5.3.0 LD_PRELOAD (J1): face unchanged, RSS growth 1.80 vs 1.87 MB/s -> allocator-invariant live-set growth. **رد (REJECTED)**.
- O3 + LTO + march=native rebuild (no source change): face unchanged, wall == budget. **رد (REJECTED)**.
- Remaining path to a RUNNING dooz on this VM stays the S156-pinned field-slot fast path (after cache-storage hardening) + bounded heap; no ready-made component covers it.
