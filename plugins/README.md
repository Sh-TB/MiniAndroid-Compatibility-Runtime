# plugins/ — Standard Per-App Triage (miniandroid.plugins.v1)

**هدف (فارسی):** هر برنامه/بازی = یک خط در `apps.jsonl`. هر ایجنت یا انسانی با یک `grep` دقیقاً بفهمد:
۱) مشکل **کجاست** (`nx` = اولین چک‌پوینت مردود)، ۲) **چرا اجرا نشده** (`n` = یادداشت مبتنی بر شواهد)،
۳) **باید چه کار کند** (`next`). هیچ لاگ خام و هیچ APK در گیت آپلود نمی‌شود — فقط اشاره‌گر شواهد.
**حداقل توکن، حداقل زمان: سه قدم.**

## Onboarding — 3 steps (token-minimal)

```bash
# 1. WHERE is it stuck?
grep '"i":"GAME-014"' plugins/apps.jsonl
# 2. WHY?  -> read the line's `n` (evidence-backed note) + `nx` (failing checkpoint)
# 3. WHAT? -> do the `next` action; when fixed, update the line + canonical/ source
```

## Files

| File | Role |
|------|------|
| `_schema.plugin.json` | The standard: fields, checkpoint law, status vocabulary, laws |
| `apps.jsonl` | One line per app/game — the whole diagnosis (grep-able) |
| `_index.json` | Rollup: counts by load status + stuck-at landscape |
| `_artifacts_manifest.json` | sha256 + size of every artifact REMOVED from git (APKs, raw logs) |

## Laws

1. **One line per app** — never thousands of files; never a duplicated monolith.
2. **No raw logs, no APKs in git** (`.gitignore` law; #386). APKs are rebuildable via
   provenance recipes; raw evidence lives in the external archive with SHA-256 ledgers.
3. **Canonical data lives in `canonical/`** — `apps.jsonl` is the generated triage
   projection; regenerate with `python3 scripts/plugins1_generate.py`.
4. **Every claim carries an evidence pointer.** No pointer = no claim.
5. Checkpoint law (verbatim from `canonical/`): `L0` APK accepted · `L1` runtime executes ·
   `L2` lifecycle · `L3` view tree · `L4` rendering · `L5` input · `L6` state changes ·
   `L7` multi-feature interaction.

> Comment «مشکلش حل شد» on the tracking issue MUST link the updated `apps.jsonl` line.
