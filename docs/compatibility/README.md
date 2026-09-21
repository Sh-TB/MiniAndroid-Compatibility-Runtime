# Compatibility Platform — MiniAndroid's Operational Memory (S74)

> **Core architectural law: Runtime Core is shared. Compatibility Status is
> app-specific.** One runtime implementation serves every application; each
> application independently records what works, what fails, what was observed,
> and what remains blocked. Never confuse a shared runtime capability with
> proof that every application is compatible.

This directory is the fast-access layer of the platform. Raw research files
(745+ tracked MD files) remain the preserved history; the canonical records
below are what an agent reads FIRST (taskbook §16, §21, §67).

## The five connected layers

| Layer | What | Where |
|---|---|---|
| **A** | Application Compatibility Dossiers | `apps/*.json` (one per important APK) |
| **B** | Helper / Tool / Source Dossiers | `tools/*.json` |
| **C** | Canonical Verified Knowledge Records | `docs/knowledge/laws/*.json` + `docs/knowledge/KNOWLEDGE_RECORDS.json` |
| **D** | Reusable Android Execution Skill | `docs/execution-skill/SKILL.md` |
| **E** | Capability Matrix / Knowledge Graph | `CAPABILITY_MATRIX.md` (generated) + cross-referenced IDs in every record |

Graph law (how records link):

```
APP --requires--> CAPABILITY --implemented-by--> RUNTIME COMPONENT
    --governed-by--> SEMANTIC LAW --derived-from--> SOURCE
    --verified-by--> TEST --produces--> EVIDENCE --tracked-by--> ISSUE
```

## Single source of truth (ownership rule)

| Artifact | Owns |
|---|---|
| GitHub `[EXEC]` Issue | living execution/project state (dated evidence checkpoints) |
| `apps/*.json` | structured compatibility state (this directory) |
| `docs/knowledge/laws/*.json` | semantic knowledge |
| `capabilities/*.json` | reusable runtime capability records |
| evidence bundles (`docs/evidence/...`) | proof |
| `docs/ACHIEVEMENTS.md` / `docs/ROADMAP_STATUS.md` / `docs/KNOWLEDGE_INDEX.md` | canonical navigation docs |
| `root_registry.json` | F-number registry (source of truth for registry IDs) |

Statuses are not duplicated freely: the dossier is the structured mirror of
the issue, updated together (see the validator below).

## Status model

Applications/capabilities: `DONE / IMPLEMENTED / TESTED / OBSERVED / PARTIAL /
BLOCKED / PENDING / SUPERSEDED`. Knowledge records: `RAW / CANDIDATE /
RESEARCHED / OBSERVED / TESTED / VERIFIED / SUPERSEDED / REJECTED` — only
`VERIFIED` records are canonical semantic laws.

Never use: "almost done", "basically works", "should work", "probably fixed".
`OBSERVED` ≠ `VERIFIED`. `IMPLEMENTED` ≠ `TESTED`. `TESTED` ≠ real-APK proven.
No numeric compatibility scores — explicit per-criteria statuses only.

## App dossier schema (v1)

Each `apps/<app_id>.json` carries: identity (name/package/source/APK
SHA256/build recipe), manifest summary, lifecycle, framework APIs, view
hierarchy, resources, layout, rendering, input, state, concurrency, storage,
persistence, network, security (DECLARED/OBSERVED/ALLOWED/BLOCKED/NOT_OBSERVED/
UNKNOWN — never "declared → used"), evidence (trace/screenshot SHA/
determinism/replay), regression, current blocker, next executable task,
completion criteria C1–C14, and links: GitHub issue, laws, capabilities,
evidence files.

Completion criteria (taskbook §8): C1 APK load · C2 manifest/lifecycle ·
C3 view/framework · C4 measure/layout · C5 render · C6 input · C7 state
change · C8 re-render · C9 persistence · C10 concurrency · C11 security/
sandbox · C12 determinism · C13 regression · C14 evidence. An `[EXEC]` issue
closes only when its dossier criteria actually pass.

## Agent read order (token-efficiency law)

```
APP PROFILE (apps/<id>.json)
→ ISSUE (linked [EXEC] issue, latest evidence comment)
→ CURRENT BLOCKER (dossier field)
→ RELATED CAPABILITY (capabilities/<id>.json)
→ RELATED SEMANTIC LAW (docs/knowledge/laws/<id>.json)
→ SOURCE (tool profile -> upstream)
→ CODE (only now)
```

An agent must never reread the entire repository to solve one app blocker when
verified knowledge already exists.

## Validation

`python3 tools/validate_compatibility_graph.py` — fails on: JSON/schema
errors, invalid statuses, duplicate IDs/packages, broken app↔law↔capability↔
tool↔issue references, VERIFIED laws without tests/provenance, missing
evidence paths, registry-count drift (`root_registry.json` roots vs summary),
index/file mismatches.

Knowledge promotion: `python3 tools/promote_knowledge.py --help`
(RAW → CANDIDATE → RESEARCHED → OBSERVED → TESTED → VERIFIED; never blindly
marks knowledge verified).
