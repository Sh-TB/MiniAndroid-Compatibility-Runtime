# MINIANDROID MASTER QUEUE

> **Canonical for what to do next, in order** (S95-CTRL, 2026-09-25).
> Ranked by the §25 scoring law: **(1) APK fan-out (2) source-reuse potential
> (3) current failure count (4) cross-subsystem value (5) implementation
> complexity (6) evidence availability (7) contributor accessibility.**
> One law affecting 20 APKs outranks a cosmetic fix for one APK.
> Ticket state is canonical in [TICKET_REGISTRY.json](TICKET_REGISTRY.json);
> this queue orders it, never re-defines it.

## Scoring snapshot (evidence-based)

| Rank | Ticket | Priority | Why it scores here (measured, not felt) | First move |
|---|---|---|---|---|
| 1 | **NET-001** real HTTP(S) stack | **P0** | Fan-out: urlchecker's core function + Telegram + every networked future app; reuse: curl/openssl are drop-in ADAPT candidates; failure count: 1 recorded frontier with on-screen evidence; cross-subsystem value: unlocks NET-002/003/004/005 and WEB-001 fetch path | Offline fixtures → minimal blocking HTTP/1.1+TLS through the existing shadow API |
| 2 | **GFX-001** programmatic UI execution | P1 | ROOT_CAUSE_FOUND with named first divergence (`[C013-ONDRAW] dispatched=NO`); blocks custom-view family (unmeasured but universal); fixture-ready plan | View.draw onDraw dispatch + paint mutation wiring |
| 3 | **GFX-002** LinearLayout weight measure | P1 | ROOT_CAUSE_FOUND (dodge panel ~1645px children); AOSP weight law is a small port; every weighted layout exposed | 3-weighted-button fixture → leftover/sum-weights |
| 4 | **WEB-001** simple browser reuse matrix | P1 | Directive target (§13); reuse potential extreme (litehtml/lexbor exist — minimum new code); instrument for text/layout/image | Reuse matrix doc BEFORE any code (license-pinned) |
| 5 | **GFX-003** GIF disposal semantics | P1 | Measured fan-out 12 titles (highest measured open count); wuffs test corpus 437 files available for port | Port disposal table + Pillow fixtures |
| 6 | **TEXT-001** shaping wire-up | P1 | POC proven (FriBidi+HarfBuzz+FreeType linked); unblocks RTL/Indic family; DIRECT_REUSE candidate | Script-gated shaping path + Arabic fixture |
| 7 | **NET-002** Internet diagnostic APK | P1 | Instrument that converts NET-001 into per-stage measured evidence (like in-house games instrument graphics) | Build diagnostic app skeleton against shadow API |
| 8 | **COMPOSE-001/DEX-001** frontier triage | P1 | Blocks modern app families (dooz, Telegram at L1); large but ranked by fan-out; needs idiom frequency data first | Call-graph idiom frequency ranking |
| 9 | **GFX-005** glyph-truth verifier | P2 | Verifier-trust risk (false positives); scope small; S93 tamper battery guards regressions | OCR-grade check overriding ink floor |
| 10 | **AUDIO-001** real-APK audio trace | P2 | Engine implemented at E2; E4 evidence missing; cheapest media win | Audio-title state-trace capture |
| 11 | **GFX-004** NinePatch fixture | P2 | High-predicted fan-out; zero fixture cost (good first task) | aapt2 NinePatch fixture |
| 12 | **CONC-001** coroutine fixture | P2 | Predictive; kotlinx.coroutines PORT_TEST available | Coroutine UI-state fixture |
| 13 | **STORE-001** sqlite depth | P2 | Room fixture green; transactions unproven | Rollback fixture |
| 14 | **JNI-001** hello-JNI fixture | P2 | Bridge exists; E4 missing | Tiny .so fixture |
| 15 | **WEB-002** callback-order fixture | P2 | Small; guarded by shadow layer | Order golden |
| 16 | TEXT-002 / TEXT-003 / GFX-006 / NET-003 / DEX-002 / AUDIO-002 | P2/P3 | Predictive smallest-tests (UNTESTED class) | fixtures per ticket |

## Execution law

1. **No wave starts without** `python3 tools/source_lookup.py <category>` +
   the ticket's upstream map (CONSTITUTION §170).
2. **Every implementation wave** must touch: ticket → law → fixture →
   ≥2 target APKs + 2 controls → battery → ROI record.
3. **Fan-out is measured, never projected.** Improved = executed with a
   failure-count delta on the same binary/protocol.
4. **A closed queue item needs** its ticket CLOSED (or status-updated) in
   TICKET_REGISTRY.json in the same commit — one problem state, one place.
5. **Priority re-ranking** happens at wave close using fresh measured
   fan-out — not intuition.

## Queue health (2026-09-25)

- Open tickets: **29** of 33 (4 CLOSED: GAME-0003..0006 family).
- ROOT_CAUSE_FOUND with plans ready: GFX-001, GFX-002 (execute first —
  cheapest verified wins).
- Smallest-test UNTESTED pool: 10 tickets — ideal contributor on-ramp.
- Evidence floor respected: nothing here claims a fix before E4+.
