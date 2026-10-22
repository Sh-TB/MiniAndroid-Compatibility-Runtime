# CONT-11 / WAVE 7 — batch-of-20 executed; F-NEW-261 ROOT-CAUSED-FIXED (problem solved)

## What happened this wave (issue #380 + the user's 20-by-20 directive)

The user's directive: work **20 apps+games at a time**, strengthen the base, fix the
generic problems, then **comment that the problem is solved** and move forward.

### Batch-20 screening (10 games + 10 apps, LAW-001 clean)

Games: bouncy, fishrings, tripeaks, tictactoe_em, opmt, secuso_memory, stacktower,
quelltext_mem, andstatus2048, solitaire_tb.
Apps: alexcalc, bmi, compose_stopwatch (Compose 1.11.3 — independent Compose
consumer), smt_calc, tananaev_calc, mueller_stopwatch, fossify_math (Compose 1.9.2),
deskclock, etar, textpad.

Screening at the reproduced CONT-10 binary (`aed46450c103f2ea`, dooz anchor
`d602648e8e401895` ×3): **6/20 REAL_APP_CONTENT**, 14 blocked — 10 of them crashing
at `Activity.onCreate` with **145 uncaught exceptions total**.

### One generic root under all 10 crashes — F-NEW-261 (ROOT-CAUSED-FIXED)

`bridge_to_api`'s Context-family guard (P0.12 `getSharedPreferences` /
`getPreferences`) matched the receiver by **runtime-class name substring**
(`"Context"`/`"Activity"` in the descriptor). Real APK hierarchies — e.g.
`GameSelector` extending the R8-renamed support-v7/v4 chain — carry **neither**
substring, so the guard missed, `getSharedPreferences` answered **null**, and the
app's own bundled `PreferenceManager` (which executes its own DEX — `dex_report=YES`)
then read prefs off the **NULL receiver**. Every exception below is downstream of
that one null:

| APK | uncaught before → after | decisive chain |
|---|---|---|
| solitaire_tb | 35 → **0** | own `PreferenceManager.getDefaultSharedPreferences` → `getSharedPreferences` NULL → getInt-on-null |
| andstatus2048 | 27 → **0** | Context-chain prefs NULL → Kotlin model `<clinit>` NPE cascade |
| etar | 37 → **0** | androidx.preference `Preference.<init>` on null context family |
| deskclock | 23 → **0** | Material Toolbar/FAB/BottomNav ctor NPEs (same null) |
| tictactoe_em | 9 → **0** | libGDX launcher onCreate chain |
| stacktower | 6 → **0** | libGDX SharedLibraryLoad face |
| textpad | 5 → **0** | locale-config REC-MISS chain + FragmentActivity NPE |
| fossify_math | 5 → **0** | Compose splash lifecycle IAE |
| alexcalc | 4 → **0** | lifecycle observer fan-out ISE |
| bmi | 3 → **0** | support-v4 `BackStackRecord.add` ISE |
| bouncy (already content) | 12 → **0** | prefs reads in the physics loop |

**The fix (generic, no app-specific code):** ancestry fallback in the guard — the
same bounded 16-hop DEX-chain walk as F-NEW-259's slot resolution — accepting any
receiver whose runtime chain reaches a Context-family shadow root
(Activity/Application/Service/ContextWrapper/Context).

**Runtime effect:** all 10 crash-family APKs now run with **0 uncaught exceptions**;
`secuso_memory` flipped **DEFAULT_BACKGROUND_ONLY → REAL_APP_CONTENT**
(`4e6e59ecfb910187` ×3 byte-identical, 558,942 content px = 26.96%, 329 colors).
Batch verdict: **6 → 7 REAL_APP_CONTENT, 20/20 zero uncaught.**

### Probe (real toolchain: aapt2 + ECJ + D8)

`fixtures/fnew261_probe` — **5/5 PASS**: F261-A direct-Activity baseline ·
F261-B the fix face (receiver class with no Context/Activity substring) ·
F261-C two-hop ancestry · F261-D cross-receiver per-name identity (S99 law) ·
F261-E cross-file negative (no leak).

### Regression at the fixed binary (`8f45e4eca7d142fa`)

- Anchors **5/5 ×3 byte-identical** (opencalc `a976d2f9` / chess `b5a7a35d` /
  dooz `d602648e` / microtimer `da73010a` / unote `4f1a9e4e`)
- F-NEW-259 probe rebuilt and re-run: **A..G all PASS**
- Negatives **19/19** (gate_a_probe rebuilt `4454e26cad06ca76` + probe results
  populated first — harness-order lesson recorded)
- Skill self-test **13/13** (restored via the gate_a_probe rebuild, W5 lesson)
- Gate A **98 PASS / 0 FAIL / 1 INFO** (matches W5)

### Registry

`root_registry.json` 566 → **567**: F-NEW-261 `ROOT-CAUSED-FIXED` (single root, no
inflation). Evidence: `evidence/cont11/{batch20_ledger.json, regression_summary.json}`.

### Honest remaining frontier (next wave owns)

13/20 still `DEFAULT_BACKGROUND_ONLY` — **zero exceptions now, but content still not
attached/rendered**: compose_stopwatch (Compose 1.11.3 — the F-NEW-256
AndroidCanvas-bridge family, now with an independent second consumer),
andstatus2048 (Kotlin model-init chain), tananaev_calc (fragment/Prefs), plus the
post-survival view-attach faces of the others. Issue #380 §6 (AndroidCanvas first
divergence) and §9 (reuse decision matrix) stay open — this wave closed the
shared crash root first because the batch data ranked it P0 by fan-out.
