# SUCCESS PATH CURRENT — CONT-8 WAVE 4 (evidence/current_head/SUCCESS_PATH_CURRENT.md)

Success path: `APK → install → activity → tree → measure → layout → schedule → draw → framebuffer → content`
HEAD `50b63bc7` · binary `c0fa65ccc7f284e7` · LAW-001 applied (no ARM-only APK in the tested set; zero ABI flips)

| APK | ABI | install | launch | tree | measure | layout | schedule | draw ops | framebuffer | REAL_APP_CONTENT | 3-run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048 (com.miniandroid.g2048) | PURE_DEX | OK | RESUMED | YES | YES | YES | YES | 34 | YES | **YES** (REAL_APP_UI 1,175,590 px) | yes (goldens, deterministic) |
| Snake Deluxe | PURE_DEX | OK | RESUMED | YES | YES | YES | YES | 262 | YES | **YES** (1,425,075 px) | yes |
| MiniCraft House Builder | PURE_DEX | OK | RESUMED | YES | YES | YES | YES | 735 | YES | **YES** (1,211,493 px) | yes |
| Tetris | PURE_DEX | OK | RESUMED | YES | YES | YES | YES | 70 | YES | **YES** (sha 26ccfce917c0e24c = recorded) | yes |
| Snake-Neon | PURE_DEX | OK | RESUMED | YES | YES | YES | YES | — | YES | **YES** (477bb95e1e6398ce) | yes |
| gmdice | PURE_DEX | OK | RESUMED | YES | YES | YES | YES | 6+ | YES (full frame) | **YES** (ad35f81bd02328b2 ×3) | **yes** |
| FishRings (time-driven capture) | MIXED | OK | RESUMED | YES | YES | YES | **YES** (5 s Timer → virtual-time → GameActivity) | ImageView family | YES | **YES** (a341e3ad9092f640 ×3; fish pieces pixel-proven to APK drawables) | **yes** |
| FishRings (default 2-frame window) | MIXED | OK | RESUMED | YES | YES | YES | **NO — 5000 ms timer not reached** | 0 | default bg | NO (DEFAULT_BACKGROUND_ONLY — honest for the window) | n/a |
| chess | MIXED | OK | RESUMED | YES | YES | YES | partial | 0 | default bg | NO (recorded frontier; anchor b5a7a35d byte-identical) | yes |
| opencalc | PURE_DEX | OK | RESUMED | YES | YES | YES | YES | — | YES | **YES** (anchor e364b001ee7abd66) | yes |
| microtimer | PURE_DEX | OK | RESUMED | YES | YES | YES | YES | — | YES | **YES** (anchor da73010a37dd0189) | yes |
| unote | PURE_DEX | OK | RESUMED | YES | YES | YES | YES | — | YES | **YES** (anchor 4f1a9e4e8f64fae8) | yes |
| W4 Ladder Probe A+B (native View + ViewGroup) | PURE_DEX | OK | RESUMED | YES | YES | YES | YES | 5 (rect/circle/text/path/bitmap) | YES (color-exact) | **YES** (b525b4b67fdb86f4) | yes |
| Dooz (Compose) | MIXED | OK | RESUMED | YES (View) / **1-node LayoutNode tree** | YES | YES | YES (frames pump) | **0** | default bg | NO — F-NEW-256 refined divergence: composition applies mid-content-pass, records only 4 changes/1 node | yes (anchor d602648e ×3) |
| FairyMahjong (Compose) | — | artifact lost in reset | — | — | — | — | — | — | — | PENDING re-supply (recorded SUCCESS 76e097244767d6c3) | n/a |
| BlockBlast | — | artifact lost in reset | — | — | — | — | — | — | — | PENDING re-supply | n/a |

REAL_APP_CONTENT APK count (this scoreboard, current HEAD): **9 explicit rows** —
2048, Snake Deluxe, MiniCraft, Tetris, Snake-Neon, gmdice, opencalc, microtimer, unote
(+ FishRings REAL content under time-driven capture; + W4 ladder probes A/B)
3-RUN VERIFIED count: **12** (all the above with triple-run byte-identical or golden-gate determinism)

Definition note: "work" = the row's explicit stage columns; no claim rests on exit code, RESUMED, or PNG existence alone.
