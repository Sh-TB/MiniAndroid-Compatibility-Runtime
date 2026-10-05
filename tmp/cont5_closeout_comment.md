# cont375 CONT-5 — FINAL CLOSEOUT: evidence-backed status, honest exit

Commit **6c791377**, binary `1177e1d08e09ee72` (clean rebuild at HEAD = 1c2ccdfd + tmp comment copy, zero code delta; equivalence proven by screenshot-SHA gates, not asserted).

## Final status table (ROOT / CONTRACT — STATUS — SOURCE — RUNTIME — 3-RUN — FAN-OUT — BLOCKER)

| Root/Contract | Status | Source evidence | Runtime evidence | Test | 3-run | Corpus fan-out | Remaining blocker |
|---|---|---|---|---|---|---|---|
| F-NEW-235 (all faces) | ROOT-CAUSED-CLOSED | registry chain 236a-d→243 | every face has a post-fix run | anchors+probe SHAs | byte-identical ×3 | fairymahjong real APK | none — fully closed |
| F-NEW-243 org.json | ROOT-CAUSED-FIXED | F-NEW-243 block + AOSP comments | [F243-DIAG] content dump; Lr5 NPE 0/3 post-fix | f235 probe ea31dc0d | ×3 identical | fairymahjong save chain | — |
| F-NEW-244 clinit spin | ROOT-CAUSED-FIXED | CLASS_REF normalization ×3 sites + token materialization | chess n3b-halts 1→0; clock HALT 1→0 | anchors/counter | anchors ×3 identical | chess + Fossify Clock (2 real APKs) | chess post-spin face (new, named) |
| F-NEW-245 System.out/err | ROOT-CAUSED-FIXED | sget synthesis + PrintStream bridge | raumballer println-NPE death → passes | NATX/f235 SHAs | ×3 | raumballer (real APK) | — |
| F-NEW-246/246b Vector/Hashtable | ROOT-CAUSED-FIXED | store+snapshot Enumeration laws | defineMedia/stopAudio pass | NATX/f235 SHAs | ×3 | raumballer (real APK) | — |
| F-NEW-239..242 | ROOT-CAUSED-FIXED (CONT-4) | law comments + OpenJDK cites | solver/artwork/reader/writer chains | f235/f084 probes | ×3 identical | fairymahjong | independent-consumer note: 240-242 exercised by fairymahjong + probes only |
| Independent game (PHASE 2) | PROVEN for raumballer | F-NEW-245/246 laws | exit=0 SUCCESS ×3, JGView.onDraw ops=3, sha a7a73cc61722497c | 3-run | byte-identical | real APK, previously L0 | menu-level content; interaction not proven |
| Independent app (PHASE 3) | PARTIAL — advanced, face named | — | clock: spin fixed, reaches provider chain; sudoku: composition→decor attach (R005-DECOR 1574/1075) but APP_DRAW_OPS missing | 3-run deterministic (clock 31ddd4d5b8e6d18e) | ×3 | real APKs | Compose draw frontier; provider chain |
| Unknown-APK gate | MEASURED | preflight CLI | 56 live rows: 5 LIVE-PROVEN / 2 OBSERVED / 5 not-exercised / 3 dead branches | matrix jsonl | n/a | 56 APKs | dead branches = tooling gap |
| Contract-98 | CLASSIFIED A-F | CONT5_CONTRACT98_AF_CLASSIFICATION | reachability per row | targets named | n/a | — | no blind implementation |

## Explicit answers

- **A. F-NEW-235 completely classified?** YES — and CLOSED. The last residual (Lr5;.g pc=150) is category D (missing generic framework contract), fixed by F-NEW-243; every face of the chain is now a registered generic law.
- **B. F-NEW-239..242 independently validated?** PARTIALLY — each has runtime proof on fairymahjong (real APK) + probe; F-NEW-239/243 also regression-covered by the f235 probe; a second independent APK consumer for 240/241/242 specifically remains open.
- **C. Fairy Mahjong genuinely fixed?** YES — exit=0 SUCCESS ×3 byte-identical 76e097244767d6c3, full-screen content, its own save chain now emits real JSON (NPE 0/3).
- **D. Another independent game genuinely fixed?** YES — **raumballer** (previously L0 LOADED_ONLY): exit=0 SUCCESS ×3 byte-identical a7a73cc61722497c, the game's OWN JGView.onDraw rendering (REAL_UI). Two new generic roots (245/246) landed from it. Interaction not yet proven; not overclaimed.
- **E. Another independent app genuinely fixed?** PARTIAL — Fossify Clock advanced past the (fixed) clinit spin to a named provider-chain face; chess spin fixed (post-spin face named). Not fully fixed.
- **F. Compose independently proven?** NO — sudokusolver proves composition creation + materialization + decor attach (R005-DECOR), but no app draw ops yet. Honest: NOT proven.
- **G. Fossify Clock independently proven?** NO — advanced materially (spin root fixed), provider-chain face remains.
- **H. Full 124 battery run?** NO — runner absent from repo (proven blocker, P3). Strongest reconstructible battery executed: foundation 16/24 (harness prerequisites for 8; f54 = harness artifact), 56-APK gate matrix, all recorded gates green.
- **I. Foundation sections PARTIAL/PENDING?** 24 PARTIAL + 2 PENDING → now all 26 classified A-F (8 F ready, 4 A genuine-capability clusters, 11 C profile-boundary, 2 D, 1 B).
- **J. Runtime-proven generic roots unresolved?** Named open frontiers: Compose draw (F-NEW-221 family), GL-surface (F-144/157), chess post-spin face, clock provider chain, R-NEW-381 dooz content — 15 open_frontiers in the registry (validator-enforced).
- **K. Source-only discoveries remain?** The dead-branch verdict classes (MEDIA/NETWORK/INPUT) + contract-98 F rows are source-level, NOT runtime-proven (explicitly marked).
- **L. Highest-fan-out remaining runtime root?** **Compose draw path** (every modern Android app) — composition reaches decor attach; the draw ops → framebuffer link is the single widest unlock.
- **M. Next best root to attack?** Compose draw (L), then SAF/MediaStore (§69, F-ready), AndroidKeyStore (§70, F-ready), split-APK (§46, plan UPP-004).

## EXIT CONDITION: **NOT COMPLETE**

Evidence supports "targeted laws + independent proofs with explicit blockers", not completion. Ranked blockers:

- **P0** (blocks broad compatibility): Compose draw ops → framebuffer (sudokusolver/dooz/mentalmath family).
- **P1** (high fan-out): GL-surface/libGDX family (TicTacToe, retrowars); F-NEW-239-243 second-consumer validation; chess post-spin face; clock provider chain; SAF/MediaStore; Keystore; MediaCodec surface; IME; split-APK.
- **P2**: multiapp interaction proofs (raumballer tap-through); 240-242 second consumers; notification channels; job persist+fire; compat-change table.
- **P3** (tooling/docs): reconstructible 124-battery runner in-repo; gate dead-branch removal (or wiring) for MEDIA/NETWORK/INPUT; S67 fixture prerequisites; f54 engine.log harness path; continuous golden-SHA oracle gate.

"Implemented" vs "proved on a real APK" vs "proved across multiple APKs" is distinguished per row above. All generic changes committed; checklist + phases 0-10 in the worklog; validator V1-V9 ALL PASS at 552 roots.
