# MINIANDROID UNIVERSAL COMPATIBILITY — MASTER ROADMAP

> The living control system for the whole runtime — NOT for one app.
> Telegram, WhatsApp, dooz, chess, klondike, FlappyCow, calculators … are
> **validation targets**. The product is the runtime base.
>
> Pipeline law: `SOURCE → SEMANTIC LAW → RUNTIME IMPLEMENTATION → UNIT TEST →
> CONTROL APK → REAL APK → REAL APP/GAME → CORPUS FAN-OUT → VERIFIED CAPABILITY`.
> No app-specific hacks; fix generic runtime laws.

## 0. THE BASE — self-knowing load order (the #1 user directive)

Every APK runs the SAME automatic base pipeline. The base knows what to load
where; sessions must never hand-load "one button" again:

```text
1. APK accept + manifest parse   package / activities / android:theme / action resolve
2. DEX parse + class load        app dex + bundled libraries clinit
3. Resource base                 framework-res pkg 0x01 router (ensure_framework_resources)
                                 + app ARSC multi-package table (SPARSE/OFFSET16 laws)
4. Application bind              AOSP handleBindApplication law (manifest App class)
5. Theme resolve                 ThemeEngine: android:theme overlays -> base theme
                                 -> framework bags (AssetManager2 Theme::ApplyStyle law)
6. LayoutInflater inflate        precedence: XML attrs > XML style= > defStyleAttr > theme
7. Traversal                     measure/layout/draw -> frame capture (SHA256 + pixel metrics)
8. Interaction                   input dispatch + state probes + autoplay drivers
```

Any frame that fails steps 5–7 is reported as a **LOAD FRONTIER** — it is never
called a render. A black/white or grey frame (WhatsApp, Telegram today) is
evidence of missing base capability, not of success.

## 1. Master rule — visible checkboxes

Every capability has a checkbox; every real app/game has a compatibility
checklist. A checkbox may be marked VERIFIED only when runtime evidence proves
it. Never VERIFIED merely because: class exists, method exists, code compiles,
rc=0, APK loads, DEX parses, a screenshot file exists, or an agent claims it.
**Claims of "100% rendered" are forbidden** — frames are labelled by what the
pixels + trace prove, and nothing more.

## 2. Status model

`IMPLEMENTED · TESTED · OBSERVED · PARTIAL · BLOCKED · PENDING · SUPERSEDED · VERIFIED`
`VERIFIED` requires runtime evidence (3-run byte-identical SHA protocol for
visual claims). Source-grep hits can only ever produce `IMPLEMENTED`.

## 3. Canonical registries (generated; no duplicates)

```text
canonical/capability_registry.json   CAP-### per capability (SS5-22)
canonical/app_registry.json          APP-### with L0-L7 checkpoints
canonical/game_registry.json         GAME-### with L0-L7 checkpoints
canonical/root_cause_registry.json   projection of live root_registry.json (420 roots)
canonical/evidence_registry.json     evidence waves + evidence law
canonical/compatibility_matrix.json  title x subsystems
canonical/master_worklist.json       MASTER WORKLIST (S128) — 480 deduplicated items,
                                     27 fields each, MC-001..MC-129 categories, P0-P4 queues
docs/MASTER_WORKLIST.md              the VISIBLE canonical worklist (roadmap, APK coverage
                                     matrix LOAD..REDRAW, root clustering, dependency graph)
```

`root_registry.json` remains the single writable store; the canonical file is a
generated read model so there is exactly one place to edit.

## 4. Title checkpoints

```text
L0 APK accepted   L1 runtime executes   L2 lifecycle works    L3 view tree builds
L4 rendering      L5 input              L6 state changes      L7 multi-feature/realistic
V  visual evidence verified (3-run)
```

Per-title subsystems: UI · Graphics · Text · Input · Audio · Video · Network ·
Storage · Native. A title may have different statuses per capability.

## 5. Capability layers

UI (View..state) · RENDERING (Canvas..screenshot) · TEXT (Paint..glyphs) ·
RESOURCES (Resources..NinePatch) · INFLATION (LayoutInflater..attrs) · INPUT ·
FRAMES (Choreographer) · ANIMATION · SCROLLING · THREADING · STORAGE · NETWORK ·
WEBVIEW · AUDIO · VIDEO · GAME · NATIVE/JNI · DATABASE.
Full per-capability table: `docs/CAPABILITY_MATRIX.md`.

## 6. Test architecture & closure

Every capability: SOURCE → UNIT TEST → CONTROL TEST → CONTROL APK → REAL APK →
CORPUS FAN-OUT. Closure requires: root cause proven + semantic law + generic fix
+ unit/control pass + real APK pass + runtime trace + visual/state evidence +
3-run reproducibility + fan-out evaluated. Issues are never closed with
"implemented".

## 7. Work loop (per issue / per wave)

Read laws → inspect → reproduce → trace → first divergence → upstream source
(AOSP/GitHub) → semantic law → generic fix → regression test → control APK →
affected real APKs/games → evidence → registries → matrix → fan-out → re-test →
close with evidence only.

## 8. Priorities

COMPATIBILITY → REUSE → CORRECTNESS → VERIFICATION → CORPUS FAN-OUT →
OPTIMIZATION. Deep source search before implementing complex behavior; reuse
upstream implementations where legal and technical (Skia/HarfBuzz/FreeType/ICU/
SQLite pattern). Roadmap 0→100 progress is COMPUTED from
`canonical/capability_registry.json` + registries (`docs/ROADMAP_STATUS.md`),
never estimated by hand.

## 9. Current honest frontiers (see ROADMAP_STATUS.md for numbers)

- WhatsApp: black/white frame = NOT A RENDER (AppContext.set injection frontier).
- Telegram: grey frame = NOT A RENDER (themed-icon SVG parsing + gms nulls).
- Compose (Recomposer) subsystem: execution works, first frame blank (R-NEW-344).
- Framework DRAWABLE files: windowBackground selectors resolve to an honest miss.
- Per-activity themes (SplashTheme vs AppTheme) — partial.
