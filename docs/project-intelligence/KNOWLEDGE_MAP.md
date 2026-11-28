# KNOWLEDGE_MAP.md — technical discoveries ↔ subsystems ↔ APKs

Cross-references: what is known, where it lives, which apps exercise it.

## Subsystem map (main architecture, verified T281)

| Subsystem | Canonical location (main, DALVIK_SPLIT=1) | Notes |
|---|---|---|
| Bridge dispatch (bridge_to_api) | dalvik_bridge.cpp:82-339 — THE live definition; chain jdk→android_core→ui_graphics→app_runtime→io_lang | callers: opcodes_invoke(7), engine_invoke(4), engine_core(3), interpreter(1), domains(re-dispatch) |
| Bridge domain laws | dalvik_bridge_domain_*.cpp (5 files) | LIVE production path — verified via MINIANDROID_BRIDGE_ROUTE |
| Engine core/interpreter/opcodes | dalvik_engine_core/_invoke/_tail.cpp, dalvik_interpreter.cpp, dalvik_opcodes*.cpp | split TUs; monolith dalvik_engine.cpp = DALVIK_SPLIT=0 fallback mirror (NOT compiled by default — T281 banner) |
| Choreographer | choreographer_shadow.cpp | ms/ns law (T280, KA-KYK-028) |
| SQLite/ContentProvider | sqlite_shadow.cpp | NOT split — s236 fixes land here nearly verbatim |
| Route diagnostic | MINIANDROID_BRIDGE_ROUTE=1 | [BRIDGE-ROUTE] chain-entry/domain/rectf-law |

## Known frontier defects (highest impact first)

| Defect | Issue | Apps | State |
|---|---|---|---|
| Compose host not materialized in ViewShadow tree | #707 (T280 CIP-1) | pfdicer, itsfrz, janken family | OPEN — top UI frontier |
| NavHostFragment attach-order NPE | #707, T279-C2 | itsfrz, janken | CLASSIFIED (needs nav state-machine emulation) |
| ArrayAdapter backing store | #707 KA-KYK-031 | compose/list apps | PENDING |
| TableRow layout_span | #707 KA-KYK-032 | table UIs | PENDING |
| TableLayout column law | #713 | table UIs | LOST fix — re-implement (L-004) |
| TextView span/attr surface gaps (F-NEW-804..805) | #597 W27 wave | text-heavy apps | main has W27 waves; wave-9 probe results on issue |
| Provider stack laws (UriMatcher #, ContentValues mirror, INSERT) | audit/s236 | chess, opensudoku, any provider app | branch-tested, needs re-port (L-001) |
| getXml leak-shape law (0xFF…) | audit/s236 | chess, opencalc | branch-tested (boot uncaughts 12→0), needs re-port |
| java.time.Instant | audit/s236 | opensudoku | branch-tested, needs re-port |

## APK ↔ subsystem hotspots (from trackers + T281 route evidence)

- gmdice/bouncy/opencalc: shallow chain depth (shadows+engine laws cover; chain reached late)
- pfdicer/pfludo/itsfrz: deep chain traffic from frame 1 (40/40-cap chain-entry) — compose/SECUSO family exercises the full domain surface
- chess/opensudoku: provider + getXml + Instant frontiers (s236 evidence)
