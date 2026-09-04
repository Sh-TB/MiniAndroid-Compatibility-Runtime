# MASTER RECONCILIATION — real-APK evidence (PHASE 6, 2026-09-03)

Engine state: commit 9d095f9 (FIX-01..FIX-05). Runner: `build/miniandroid run`
with MINIANDROID_APK_CACHE=/tmp/.../apk_cache/corpus (external, zero-APK repo).
Pre-fix baseline for the corpus default screen: `eb16ab5c…`.

## Extended corpus (8 APKs)

| APK | exit | time | screenshot SHA-16 | vs pre-fix |
|---|---|---|---|---|
| chessclock | 0 | 0.3 s | ba017f5183ac5747 | **CHANGED** — left the shared default screen (eb16ab5c); now renders dark theme + SeekBar UI (real app content) |
| headingcalculator | 0 | 0.2 s | 7d2a68606ae18d76 | **CHANGED** — now renders a resource-backed ListView with app strings (long-text overlap = known SFS-010 font limitation) |
| bgclockhansdezwart | 0 | 0.6 s | 2f85dd74aa54e463 | **CHANGED** — renders its themed window background (previously stopped early at the WebView boundary L6) |
| bouncy | 0 | 0.7 s | dc6a565ee96ed5d7 | renders (graphics campaign app) |
| simplekeyboard | 0 | 0.3 s | eb16ab5c68fa9b6c | unchanged (default screen — entry-chain gap, CONFIRMED_OPEN) |
| openlauncher | 0 | 1.3 s | eb16ab5c68fa9b6c | unchanged (default screen) |
| tictactoeemmanuelmess | 0 | 0.9 s | 31ddd4d5b8e6d18e | deterministic blank — libGDX backend boundary (BLOCKED, same family as dooz) |
| droidify | 1 | 0.1 s | — | APK itself is a truncated download (5,242,880 bytes, missing ZIP central directory) — data-loss family (K-26), NOT a code regression |

## Golden matrix (unchanged law)

simplestopwatch **2a12587a0acf196c** BASELINE_MATCH ×3 (determinism);
gmdice 4fd3ce0e · microtimer eb16ab5c · unote d6b854c4 · dooz 31ddd4d5 —
all byte-identical to the pre-fix run (ZERO regression). dooz runtime
0.9 s → 69.9 s (K-33: more Compose bytecode now executes; same final frame).

## Interpretation

The lit8-table correction (K-31), switch dispatch (K-18) and parse bridge
(K-19/K-20) let chessclock / headingcalculator / bgclock execute REAL app
bytecode far past their previous halts — first app-specific renders for these
apps. This is the intended effect of PHASE 4; screenshots + (truncated) run
logs in this directory are the evidence set.
