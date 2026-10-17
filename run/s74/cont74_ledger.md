# CONT-74 RESULT — FULL #364 SWEEP (29 comments, every card classified) + F-NEW-377 TAIL-JOIN ESCAPE FIXED + #364-ROI VERDICT

Direct answer to "کل ۳۶۴ رو کامل کامل بررسی بکن" (review #364 completely, completely) and "did this method actually help, or is it wasted time — continue or stop?"

- **Wave:** CONT-74
- **HEAD at work start:** `3b6430ac20e45395` (== origin/main, synced, clean tree)
- **Binary (pre-fix):** `1ecb1949e5fa59cf` · **Binary (post-fix):** `2b3bf0bab3770c50`
- **Registry:** 682 → **683** roots (`F-NEW-377 ROOT-CAUSED-FIXED P1`), id-unique, mirrored to `canonical/`, validator PASS
- **New probe:** `fixtures/cont74_escape_probe` → `run/cont74/c74esc.apk` sha16 `8e528f6aa9b71938`, self-contained (reads its OWN bytes back through escape spellings — no fixture coupling)

---

## 1. Full sweep — all 29 comments classified against CURRENT HEAD

Every row below was re-checked against `3b6430ac` source + registry, not against the card's own snapshot. Nine-value vocabulary.

| Comment | Card | Verdict (current HEAD) | Where it stands |
|---|---|---|---|
| 5961202333 | Protocol anchor | standing contract | always applied |
| 5962053554 | UPSTREAM-REUSE 33-row campaign | CLOSED (prior wave) | ledger posted |
| 5966306728 | HEAD/binary record | historical snapshot | superseded by later records |
| 6201160604 | Deep upstream mining 50+ | PARTIALLY_CONFIRMED, consumed | CONT-71 wave 1: 7 audited rows in `docs/UPSTREAM_SOURCE_MINING.jsonl`; rest = known backlog, not lost |
| 6201220386 / 6201265437 / 6201323228 | already-solved addenda | ALREADY_TRACKED_OR_DUPLICATE | cross-referenced by mining ledger |
| 6201554037 | **FOUNDATION 1 — View invalidation** | ALREADY_FIXED_AND_TESTED (CONT-72) | alleged breakage **REFUTED** (c72draw fence PASS ×3 at unmodified record binary); trial fix A/B-disproven and REVERTED; MG-116 **CLOSED** with its first dedicated law fence |
| 6201700020 | **FOUNDATION 2 — Compose Recomposer** | STALE_OR_SUPERSEDED (CONT-72) | CONT-25-era premise; F-NEW-256 superseded, F-NEW-265 re-rooted, F-NEW-316/317 prove real canvas PATH ops; next lever named (deriveStateLocked → F-NEW-277) |
| 6201774895 | Operating contract | standing | applied every wave |
| 6202665605 | **FOUNDATION 3 — package identity** | ALREADY_FIXED_AND_TESTED | P0-A → **F-NEW-375** (caller-identity + lexical containment), P0-B → **F-NEW-376** (staged-generation atomicity, 70/70 fault battery), P0-C NOT_APPLICABLE (single-app path per process) |
| 6203183051 | CONT-71 result | result | exception-delivery + measure laws |
| 6207830469 | **FOUNDATION 4 — DEX `<clinit>` state machine** | **CONFIRMED_OPEN_GAP** | MG-310 `PARTIAL`, EVIDENCE/TEST empty — "implemented; dedicated fence pending" is **accurate at this HEAD**. No runtime failure alleged. Fence stays a P2 backlog item; NOT re-registered as a duplicate root |
| 6207846702 | **FOUNDATION 5 — native lib + JNI (UPP-001)** | **ALREADY_TRACKED_OR_DUPLICATE** | UPP-001 `PENDING_RESEARCH` is the canonical root; the card itself says "reuse existing root"; CONT-73's Ball2Box/OpenSurge ARM-only rows are its app-layer evidence |
| 6207963395 | **MG-150/MG-147 transformed hit-testing** | **CONFIRMED_OPEN_GAP** | both rows still `PARTIAL` with "not individually fenced" accurate at this HEAD. Real fence backlog (P2), no runtime bug alleged |
| 6207991401 | **FOUNDATION 6 — 1–2 min first-divergence runner** | **SOURCE_LEVEL_CANDIDATE_ONLY** | tooling proposal; existing harness already has resume checkpoints + probe tier. `scripts/test/run_semantic_probe.sh` stays a named candidate — honestly NOT built this wave |
| 6208015426 | **FOUNDATION 7 — storage-sandbox escape** | **PARTIALLY_CONFIRMED at wave start → FIXED this wave** | branches 1–4 + volume sibling-prefix were already F-NEW-375. The two **residual tail-join branches are real**: volume `..` escape was runtime-REACHABLE → **F-NEW-377 ROOT-CAUSED-FIXED below**; font tail-join was resolve-ALLOWED, now also fenced |
| 6208052394 | FOUNDATION 8 — 2D-game forensic wave | ALREADY_TRACKED_OR_DUPLICATE | its batch-triage methodology is exactly what CONT-73 executed (ten-app shared harness) |
| 6208094322 | FOUNDATION 9 — LibGDX native bootstrap | ALREADY_TRACKED_OR_DUPLICATE | no LibGDX APK in corpus; the class it describes is the UPP-001 frontier already evidenced by Ball2Box/OpenSurge rows |
| 6208114888 | FOUNDATION 10 — specific game fix | ALREADY_TRACKED_OR_DUPLICATE | same family as 9/4 + 12/4; no new root |
| 6208135022 | FOUNDATION 11 — Memory (eu.quelltext) | ALREADY_FIXED_AND_TESTED | CONT-73: `35295a57` REAL_APP_CONTENT — the blank-candidate concern is **disproven at current HEAD** |
| 6208159991 | FOUNDATION 12 — Ball2Box (Godot) | ALREADY_TRACKED_OR_DUPLICATE | CONT-73: ARM-only PREREQUISITE_MISMATCH = UPP-001 domain, honestly logged |
| 6208293717 | FOUNDATION 13 — ChessClock | ALREADY_FIXED_AND_TESTED | CONT-73: `fe3ae1167` == recorded face — the app already renders real content |
| 6208316922 | FOUNDATION 14 — five-APK batch | EXECUTED (CONT-73) | merged into the ten-app shared-harness triage |
| 6208340668 | FOUNDATION 15 — five corpus games | EXECUTED (CONT-73) | 6 REAL_APP_CONTENT rows + 2 honest mismatches + 2 named frontiers |
| 6208446700 | CONT-72 result | result | three-card independent review |
| 6208489127 | CONT-73 request | satisfied | ten-app triage executed, ledger 6229605065 |
| 6218720139 | CONT-73 independent audit | satisfied | all four closeout items hold at `3b6430ac` |
| 6229605065 | CONT-73 result | result | F-NEW-376 fix + triage closeout |

**Sweep bottom line:** after this wave, **zero unclassified comments** remain in #364. Open-but-registered items (not silently dropped): MG-310 fence (P2), MG-150/MG-147 transform-hit-test fence (P2), F-NEW-277 Compose continuation lever (P0), kotlin-reflect `ReflectionFactoryImpl` candidate root (from CONT-73), UPP-001 native frontier, FOUNDATION-6 probe runner (tooling candidate), upstream-mining backlog rows.

---

## 2. Researcher Review — ChatGPT's Three Cards (+ the twelve later cards)

Mandatory section. What the researcher got right, what was unsupported, what was stale, what was overconfident.

**Card 1 — View invalidation (6201554037).** *Right:* the card correctly identified MG-116 as an open fence gap — the registry row agreed, and the gap was real. *Unsupported/overconfident:* the implied allegation that invalidation→traversal→draw was BROKEN did not survive contact with the runtime — the c72draw DEX fence passed ×3 at the unmodified record binary, and the card's proposed `invalidate→layout_dirty` direction was A/B-**disproven** and reverted (the failed experiment is kept in-tree as evidence). *Stale:* nothing. *Net:* the card's value was the fence it triggered (MG-116 now has its first dedicated law test), not the bug it alleged — the alleged bug did not exist.

**Card 2 — Compose Recomposer (6201700020).** *Stale:* the premise was CONT-25-era; it did not check the current state of F-NEW-256/265/316/317 before writing. Destinations materialize via F-NEW-259/259b; the measure pass was re-rooted; real canvas PATH ops are proven. dooz `31ddd4d5` ×3 and dooz180 `c94da5a9` ×2 MATCH at review time. *Right:* even a stale card produced a usable next lever (deriveStateLocked recorded as F-NEW-277's next mechanism). *Lesson already fed back into the ROI verdict:* a source/registry freshness check before writing the card would have saved a full review round-trip.

**Card 3 — package identity (6202665605).** *Right — the sharpest of the three:* P0-A was a real, live leak (probe read victim A's TOPSECRET72 bytes through absolute / user-0-alias / 2×-relative spellings), P0-B was a real atomicity hole (fault-injection proven: chmod-444 record → V2 bytes under V1 record → runtime executes V2 code under V1 identity). *Overconfident:* P0-C (cross-user) was NOT_APPLICABLE in this runtime's single-app-per-process model — the card presented it at the same severity as A/B. *Net:* two P1 laws (F-NEW-375, F-NEW-376) came directly from this card; both runtime-proven before fixing.

**Cards 4–15 (the later batch).** 4/4 and the MG-150/147 addendum correctly read the registry's honest PARTIAL rows — both are real fence backlogs and are now explicitly ledgered as such (P2), not inflated into bug claims. 5/4 correctly said "reuse UPP-001, do not re-open" — good discipline. 6/4 is a tooling proposal, honestly classified as a candidate, not built this wave. 7/4 was the most precise card of the entire set: its five-branch enumeration predicted exactly where F-NEW-375's fence would be incomplete — the two residual branches are today's F-NEW-377. 8/4–13/4 and 14/4–15/4 overlap heavily on one native-blank-game family + one triage batch; one ten-app shared-harness run covered them all (six of fifteen cards, one run).

**The independent audit (6218720139)** caught something important: a lost session had claimed F-NEW-376 was fixed, but the claim was never committed to remote. The audit's "remote does not yet contain the fix" was correct and forced the work to be redone from the synced tree — that is the review loop working as designed.

---

## 3. New work THIS wave — F-NEW-377 (FOUNDATION-7 residual, pre-proven then fixed)

**Claim:** the volume and system-font tail-join branches of `resolve_android_path` joined a caller-controlled tail under a backing directory with **no containment check** — F-NEW-375 fenced four branches + the volume *sibling-prefix* boundary, but not `..` *inside* the tail.

**Proof of leak (binary `1ecb1949e5fa59cf`):** probe run `run/cont74/esc_pre3`:

```
[C74-VOL-ESC]  LEAK ESCAPE read own marker via
  /storage/emulated/0/../../../data/data/com.probe.c74esc/files/own.txt len=13
[C74-VOL-ESC2] LEAK ESCAPE read own marker via
  /storage/emulated/0/../0/../../../data/data/com.probe.c74esc/files/own.txt len=13
```

Honesty notes on the proof itself: (a) two-`..` spellings land in non-existent directories and prove NOTHING — the escape needs three `..` because the volume backing exists from boot, which is what makes it **reachable today, not theoretical**; (b) FONT-ESC was resolve-**ALLOWED** (no `PATH-LAW DENIED` line) but IO-unreachable only while `<store>/system` is absent — classified as a law-hygiene row, fenced pre-emptively so the virtual system image cannot turn it into a live escape; (c) the ALLOW/DENY distinction rests on the `PATH-LAW` stderr line, cross-checked against `/etc/passwd` which DID print it in the same run.

**Fix (resolver-only, no engine change):** `data_root.cpp` VIRTUAL_EXTERNAL + SYSTEM_IMAGE branches now run the **same `path_contained` helper** F-NEW-375 introduced — no new concept, the containment law applied to the two branches it had not reached. Denied spellings surface the canonical AOSP `FileNotFoundException` face.

**Proof of fix (binary `2b3bf0bab3770c50`, ×3 runs `esc_post_1..3`):** every escape spelling DENIED with `PATH-LAW DENIED` lines; volume positive control `VOL-OK` round-trip intact ×3.

**Regression at `2b3bf0bab3770c50`:** c72priv fence **13/13** OK (F-NEW-375 behavior unchanged) · negatives **19/19** · reinstall **8/8** · goldens **4/4** (`helloworld` canonical `83720c1028f832d0`) · wall rows dooz `31ddd4d5b8e6d18e` ×3 + opencalc `f25b754c4565c38b` ×3 + unote `90a67cc1ddda57b7` ×3 = **9/9 MATCH zero drift** · s82 validator **PASS**. Probe screenshots are the default splash (`31ddd4d5...`) — the probe is a behavior probe with no visual surface; the evidence is the stderr row log. Mosaic: `evidence/cont74/cont74_mosaic.png` sha16 `380ea4e6c0a743c3`.

---

## 4. ROI verdict — did #364 help, how, and is continuing worth it?

**Hard outputs of this loop since 2026-10-15 (three waves, CONT-71/72/73/74):**

| Output | Source | Status |
|---|---|---|
| F-NEW-375 (cross-package isolation, 4 leak spellings) | Card 3 P0-A | ROOT-CAUSED-FIXED, runtime-proven |
| F-NEW-376 (install/update atomicity, 70/70 fault battery) | Card 3 P0-B + independent audit | ROOT-CAUSED-FIXED, fault-proven |
| F-NEW-377 (volume tail-join escape) | Card 7 residual | ROOT-CAUSED-FIXED this wave, LEAK len=13 pre-proven |
| MG-116 closed + c72draw law fence | Card 1 review | CLOSED, fence PASS ×3 |
| F-NEW-368/370 laws + F-NEW-374 registered | CONT-71 cards | implemented, env-gated |
| Ten-app triage (6 real-content, 2 mismatch, 2 frontiers) | Cards 11–15 | executed, ledger posted |
| 1 wrong allegation refuted before a bad fix landed | Card 1's proposed fix | refutation = saved bug |
| 1 lost session's uncommitted claim caught | independent audit | forced honest redo |

**Where the loop wasted time (honest accounting):** six of the fifteen FOUNDATION cards overlap on a single native-blank-game family — one triage run covered them all, the cards did not need to exist separately. Card 2 was stale on arrival. The methodology card (6/4) produces no code by design and its runner remains unbuilt. These are real costs.

**Verdict: NOT wasted time — CONTINUE.** The method's hit-rate on cards that alleged runtime-reachable defects is 3-for-3 (Card 3 P0-A, Card 3 P0-B, Card 7 residual), every fix carries pre/post binaries + negative controls + cross-app regression, and the two wrong/stale claims (Card 1's alleged breakage, the lost session's claim) were caught **by the loop's own review discipline before they could harden into false confidence**. Two process corrections from this point: (1) overlapping game-family cards collapse into one triage row each — no more duplicate roots; (2) every card gets a source/registry freshness check **before** it is answered (would have saved the stale Card 2 round-trip).

**Not executed this wave (honest pendings, no silent drops):** MG-310 dedicated `<clinit>` fence (P2, needs a deterministic concurrency fixture before any code claim); MG-150/MG-147 transform hit-test fence (P2, needs a rotated/translated hit-probe fixture); FOUNDATION-6 semantic-probe runner (tooling candidate, not built); upstream-mining backlog rows beyond wave-1's seven; UPP-001 native execution (architectural frontier); kotlin-reflect `ReflectionFactoryImpl` candidate root from CONT-73 (fixture-first discipline — no fix without a fixture).
