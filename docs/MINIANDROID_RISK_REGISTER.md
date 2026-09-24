# MINIANDROID RISK REGISTER

> **Canonical for predictive compatibility risk** (S95-CTRL, 2026-09-25).
> This register does NOT only record bugs that already happened — it predicts
> likely divergence from AOSP/ART/libcore/AndroidX/Kotlin/Compose semantics,
> real-corpus composition, engine families and MiniAndroid's own
> architecture. **A ticket here means "this semantic area must be verified" —
> it does NOT automatically mean it is broken.**
> Machine state: [TICKET_REGISTRY.json](TICKET_REGISTRY.json) (validated by
> `tools/validate_control_system.py`). Ticket statuses: `UNKNOWN, UNTESTED,
> OBSERVED, PARTIAL, FAILED, ROOT_CAUSE_FOUND, IMPLEMENTED, TESTED, VERIFIED,
> BLOCKED, PENDING, CLOSED, SUPERSEDED`.
> Risk classes: KNOWN FAILURE (KF) · LIKELY FAILURE (LF) · HIGH-RISK UNTESTED
> (HR) · DEPENDENCY RISK (DR) · SEMANTIC RISK (SR) · PERFORMANCE RISK (PR) ·
> CORPUS RISK (CR).

## GRAPHICS

| Risk | Class | Ticket | Basis | Smallest determining test |
|---|---|---|---|---|
| Programmatic UI (onDraw dispatch + runtime color mutation) never executes → placeholder screens | **KF** (E4) | GFX-001 | simplestopwatch `[C013-ONDRAW] dispatched=NO ops=0`; S95 §7.1 | custom-view fixture; simplestopwatch flip |
| LinearLayout weight measure distributes full leftover per child | **KF** (E4) | GFX-002 | dodge panel children ~1645 px, y=6737 | 3-weighted-buttons fixture |
| GIF disposal 0–3 edge semantics unproven (12 animated titles exposed) | LF | GFX-003 | wuffs/Pillow laws; minimal compositor | disposal fixture port |
| NinePatch stretch fidelity | HR | GFX-004 | law registered, no dedicated fixture | NinePatch fixture APK |
| Thin-glyph false UNREADABLE_TEXT flags erode verifier trust | **KF** (verifier-level) | GFX-005 | urlchecker chevrons 0.0033/0.0016 < 0.004 floor | glyph-truth oracle check |
| Shader/ColorFilter silently ignored at raster | HR | GFX-006 | Paint shader acceptance untested | gradient fixture |
| Vector pathData arc-command coverage gaps | HR | GFX-007* | 933-LOC decoder new in S95; full grammar untested | arc-heavy vector fixture |
| Density bucket boundary (e.g. 2.625) rounding on new devices | SR | GFX-008* | L-S94-DENSITY laws cover mapped cases only | bucket-matrix fixture |

\* Tickets GFX-007/GFX-008 are registered in this register as P3 predictive
items; promote to full tickets when an APK or fixture first diverges.

## TEXT

| Risk | Class | Ticket | Basis | Smallest determining test |
|---|---|---|---|---|
| Complex scripts render as isolated forms (no shaping) | **LF→KF for RTL apps** | TEXT-001 | HarfBuzz+FriBidi+FreeType linked; R4 POC not wired | Arabic fixture APK |
| RTL mirroring absent (padding/alignment/order) | HR | TEXT-002 | fribidi linked; layout mirror untested | RTL layout fixture |
| Ellipsize/lines/lineSpacing laws diverge | HR | TEXT-003 | corpus shows multi-line apps | ellipsize fixture |
| Font fallback across families (CJK+emoji+symbol mixing) | SR | TEXT-004* | S93 tofu law covers detection, not full fallback ordering | mixed-script fixture |

## MEDIA

| Risk | Class | Ticket | Basis | Smallest determining test |
|---|---|---|---|---|
| Audio state machine unproven at real-APK level | HR | AUDIO-001 | engine IMPLEMENTED+TESTED (E2) only | audio title state trace |
| SoundPool concurrency eviction | HR | AUDIO-002 | AOSP max-streams law | overlap fixture |
| Video pipeline absent (decode/PTS/surface) | **KF (frontier)** | VIDEO-001 | no video subsystem | 5s clip fixture |
| Container/metadata (MediaMetadataRetriever) absent | HR | MEDIA-001 | frontier | MP4 header fixture |
| Codec availability/license constraints block ports | DR | MEDIA-002* | ffmpeg LGPL/GPL gate | license audit doc |

## NETWORK

| Risk | Class | Ticket | Basis | Smallest determining test |
|---|---|---|---|---|
| No real HTTP(S): every networked app's core function is shadow-recorded | **KF — TOP P0** | NET-001 | android_shadows URL capture; no socket | urlchecker real HEAD request |
| DNS failure/timeout propagation semantics | HR | NET-003 | shadow layer returns failure paths only | offline error fixture |
| TLS certificate behavior (verification, error surfaces) | HR | NET-004* | depends on NET-001 stack choice | self-signed fixture |
| IPv4/IPv6 dual-stack behavior | HR | NET-005* | unmeasured | diagnostic app stage |

## WEB

| Risk | Class | Ticket | Basis | Smallest determining test |
|---|---|---|---|---|
| Browser/HTML/CSS engine absent (target registered) | **KF (frontier)** | WEB-001 | no engine; directive forbids from-scratch | reuse matrix → local page render |
| WebView callback order fidelity | HR | WEB-002 | shadow tracks loadUrl only | callback-order fixture |

## DEX / RUNTIME / API

| Risk | Class | Ticket | Basis | Smallest determining test |
|---|---|---|---|---|
| Compose-era ART idioms block modern apps | **KF (frontier)** | DEX-001 | dooz/Telegram L1 OBSERVED | idiom triage top-N |
| Reflection edge signatures (generic/arrays/varargs) | SR | DEX-002 | f103 covers Class laws | reflection fixture battery |
| Multi-DEX / large-dex resolution order | HR | DEX-003* | corpus titles carry 1–3 dex | multi-dex fixture |
| Try/catch/finally depth interactions | SR | DEX-004* | 21 roots fixed; depth stress untested | nested-try fixture |

## CONCURRENCY

| Risk | Class | Ticket | Basis | Smallest determining test |
|---|---|---|---|---|
| Coroutine dispatch/cancellation unverified | HR | CONC-001 | locks/atomic shadows only | coroutine fixture |
| JMM visibility (volatile/synchronized) under interpreter threads | HR | CONC-002 | single-thread path proven only | two-thread stress |
| Handler looper starvation/lag laws | SR | CONC-003* | choreographer proven; looper depth untested | post-flood fixture |

## STORAGE

| Risk | Class | Ticket | Basis | Smallest determining test |
|---|---|---|---|---|
| SQLite transactions/locking beyond Room fixture | HR | STORE-001 | F-026+F-027 fixture green only | transaction rollback fixture |
| Path/encoding edge cases (unicode filenames, .. escape) | SR | STORE-002* | sandbox exists; adversarial paths untested | path traversal fixture |

## JNI / NATIVE

| Risk | Class | Ticket | Basis | Smallest determining test |
|---|---|---|---|---|
| System.loadLibrary + JNIEnv table semantics | HR | JNI-001 | jni_bridge.h present, unproven E4 | hello-JNI fixture |
| Native game engines (libgdx native backends) | DR | JNI-002* | corpus game-engine family | reuse matrix first |

## ANDROIDX / COMPOSE

| Risk | Class | Ticket | Basis | Smallest determining test |
|---|---|---|---|---|
| Compose composition frontier | **KF (frontier)** | COMPOSE-001 | dooz OBSERVED at L1 | depends on DEX-001 triage |
| AppCompat version drift (attribute table growth) | DR | COMPOSE-002* | pinned framework tables S68-era | new-appcompat fixture |

## PROJECT-LEVEL RISKS

| Risk | Class | Mitigation owner | Note |
|---|---|---|---|
| Screenshot-based claims drifting into false positives | SR | S92/S93 law set + adversarial battery (in force) | non-negotiable; see CONSTITUTION |
| Registry/doc count contradictions (README vs registries) | SR | `tools/validate_control_system.py` (S95-CTRL) | fails on any mismatch |
| Repo bloat (APKs/logs/toolchains in git) | PR/CR | zero-APK law; .gitignore; secret guard | pre-receive 100MB limit already bit backup branch |
| Upstream license contamination | DR | license_map.json pinned-SHA evidence (S94) | check before every reuse |
| Single-maintainer bus factor on engine internals | CR | contributor system (S95-CTRL §9 docs) | ticket guide routes by skill+time |
| Corpus cache outside repo lost on container reset | CR | registry downloader + SHA re-pin (exercised this session) | recorded in BATTERY_INDEX notes |

\* = pre-registered predictive entry; promoted to a full TICKET_REGISTRY.json
ticket on first divergence. All other IDs above exist as full tickets in
[TICKET_REGISTRY.json](TICKET_REGISTRY.json) now.

## Triage law

1. New observed failure → add sub-ticket under the app/game master record;
   never overwrite old evidence.
2. New predictive risk → add register row with the smallest determining test;
   status UNTESTED/UNKNOWN.
3. Every KF/LF row must carry either a fixture plan or an executed-APK
   evidence link before the next wave closes.
