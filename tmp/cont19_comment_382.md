# FINAL REVIEW — A1–A104 knowledge transfer (primary-coder audit, closed at HEAD `0b019608`)

This is the claim-by-claim audit the transfer requested. It was **not** previously posted (the issue had only the two owner comments). Method: source inspection at HEAD for every individually-described A-item, plus one targeted runtime battery for A103 (no wholesale re-runs; no A105+ work started). Full record: `evidence/cont19/CONT19_BASE_FIRST.md` §3–§4.

## Claim verdicts

| Claim | Verdict | Source/evidence basis at HEAD |
|---|---|---|
| A1–A50 Compose setup | PARTIAL (historical) — cause narrative **SUPERSEDED BY EVIDENCE** | Host bridges exist (`android_shadows.cpp` ComposeView/AndroidComposeView/WrappedComposition laws); runtime proof shows the APK's own Compose classes execute (see #383 audit) |
| A51/A52 File null-receiver guards | PARTIAL / SUPERSEDED | No per-method guard at a cited site; the engine-wide f141 null-receiver law (hardened by F-270) now covers all shadow calls generically |
| A61 dialog get_or_create_node | **ACCEPTED** | `dialog_shadow.cpp:97,103,130` |
| A62 in-process ZIP, no popen | **ACCEPTED** | Law comments `dalvik_engine.cpp:4702,49387`; zero live `popen` calls remain |
| A64 Storage::package_data_dir | **ACCEPTED** | `storage/data_root.h:78`; `dalvik_engine.cpp:27122` |
| A68 finish clears stale ViewTree | PARTIAL | Mechanism is now the G07 `request_finish` lifecycle cascade + F-NEW-174 finisher identity (`android_shadows.cpp:4447`), not a direct `content_view_id` clear; stale-tree absence supported by reinstall matrix 8/8 |
| A91 onPostCreate Path A only | ACCEPTED (as historical PARTIAL) | Superseded by A93 |
| A92 1080×1920 tooling (no source change) | **ACCEPTED** | S92 verification law; used for all current batteries |
| A93 onPostCreate Path B | **ACCEPTED** | `[A93-POSTCREATE]` marker at `dalvik_engine.cpp:1993` |
| A94 Display.getWidth/getHeight + getDisplayInfo | **REJECTED — absent at HEAD** | Zero hits for the claimed patch in the current tree; only the Resources.getDisplayMetrics law exists (`dalvik_engine.cpp:38719`). Recorded as a re-implementable root if a target needs it |
| A95 ViewShadow pre-layout width fallback | **ACCEPTED** | `android_shadows.cpp:6158–6165` (measured_right-first fallback) |
| A101 HashMap.size counts real entries | **ACCEPTED** (dual-route note) | CollectionShadow map size = `map_entries + map_string_entries` (`android_shadows.cpp:1790–1793`); a stub-0 remains only in the no-shadow-registry `bridge_to_api` fallback (`dalvik_engine.cpp:47482`, its own comment: never reached when CollectionShadow handles the call) |
| A102 ArrayDeque/LinkedList collection gate | **ACCEPTED** | `handles_class`: LinkedList `android_shadows.h:2390`; ArrayDeque `:2464` (LAW-D, CONT-18) |
| A102-unresolved Map.keySet view-class bug | PARTIAL — CARRIED | F-064 law sites present; no live reproduction this wave; minos stays FRAME_CAPTURED; no promotion |
| A103 seven-app three-run SHA256 | **ACCEPTED — re-proven at current binary** | Battery (24 runs, §7 invocation): 2048 `59ca1526611c4622`, tetris `f360daa244cfca8d`, snake_deluxe `34a712689ce66e58`, snakeneon `cc986d4b4d3ec3f3`, tictactoe_deluxe `af6094295ecb50e3`, minicraft `b0876952f41e4af2`, gmdice `f3b483fe7b7cf51b` — **all ×3 byte-identical, all MATCH the claimed hashes** |
| A104 dooz Compose boundary | PARTIAL — boundary re-proven, cause superseded | dooz anchor `d602648e8e401895` ×3 re-verified (1 unique color — FRAME_CAPTURED, honest); cause chain superseded, see the #383 comment |
| A53–A60, A63, A65–A67, A69–A90, A96–A100 | SOURCE GAP (as instructed) | Not individually described in the transfer; nothing invented |

## Counts

- ACCEPTED (from source/evidence, incl. re-proven): **9** (A61, A62, A64, A92, A93, A95, A101, A102, A103)
- PARTIAL / SUPERSEDED: **6** (A1–A50 grouped, A51/A52, A68, A91, A102-unresolved keySet, A104)
- REJECTED: **1** (A94 — patch absent at HEAD)
- SOURCE GAP: **48** ids

## Contradictions found and settled

1. **snakeneon hash**: the local record `evidence/cont15/sixgame_validation.json` held `24fb7694eb64634a ×3`, contradicting the transfer's `cc986d4b4d3ec3f3 ×3`. The fresh battery reproduces **`cc986d4b4d3ec3f3 ×3`** — the transfer claim stands; the cont15 row was the mis-provenanced outlier (superseded).
2. **App-count arithmetic**: the "13 apps" table + blockblast (`com.sidhant.blockblast`, FAILURE report `evidence/diff366/root_a/blockblast_com.sidhant.blockblast/report.md`) reconciles the "14 apps / 5 FRAME_CAPTURED" statement: blockblast is the 5th FRAME_CAPTURED target.

## Binary provenance note

The battery binary was rebuilt at HEAD in this container: sha16 `b4937c81aba0998c` (recorded CONT-18h binary was `f882ca1832b955e3` — cross-container byte drift on identical source). Every screenshot anchor and all seven A103 hashes reproduce **byte-identically**, re-confirming that behavior anchors, not binary bytes, are the portable verification contract. No promotion was made on a stale binary; every hash above is from the fresh battery.

## Remaining blockers / next smallest step

Blockers: Map.keySet view-class bug (minos); Compose chain root F-NEW-271 (dooz); WebView HTML5 canvas (blockbuster). Next smallest, highest-value step: the F-NEW-271 heap-dump probe — a generic engine heap/field-identity law, not Compose work (tracked in #383).