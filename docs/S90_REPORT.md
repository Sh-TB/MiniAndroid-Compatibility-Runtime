# S90 REPORT — FOUNDATION RESET (in-wave snapshot)

All numbers from canonical artifacts; nothing hand-computed.

## §28 the 25 questions

1. **Titles in canonical registry:** 225 (`run/s88/corpus/profiles.json`) + 148 legacy per-title achievement records (`docs/evidence/canonical/registry.json`).
2. **Real execution:** 66 batch-executed (S89 EXEC_RESULTS) + named title sessions (Telegram, Signal, torchlight, snakes, chess, no.thanks).
3. **Meaningful state changes:** 12 VERIFIED-INTERACTIVE (canonical registry).
4. **Validated GIFs:** 11 game GIFs + 1 app GIF (`docs/evidence/canonical/`, SHA-pinned, multi-frame verified).
5. **Apps:** 60 (canonical registry) / 110 app queue (corpus).
6. **Games:** 87 (canonical registry) / 110 game queue (corpus).
7. **Source-linked titles:** corpus profiles carry `upstream` URLs from the F-Droid index harvest (110+110 queue); named titles carry exact upstream + version + APK SHA (Telegram b6a13e87…, Signal 46cd670d… official manifest).
8. **Exact classes extracted:** 200 persisted in `registry/api_inventory.json` (top by fan-out; full type table per title in profiles).
9. **Exact methods:** 400 exact `class.method(params)return` entries; 8,639 per-title entries corpus-wide; 0 parse failures.
10. **Top classes by title fan-out:** Object 213 · String 212 · Context 211 · Bundle 205 · CharSequence 201 · Intent 200 · StringBuilder 200 · Activity 198 · Class 195 · View 193 · Build$VERSION 179 · Integer 178 · Exception 172 · Iterator 172 · List 171 · Uri 170 · Runnable 169 · ArrayList 169 · Resources 167 · System 167.
11. **Top methods:** Object.<init> 209 · StringBuilder.toString 200 · StringBuilder.append(String) 198 · Activity.<init> 197 · StringBuilder.<init> 195 · Activity.onCreate(Bundle) 191 · String.equals 188 · Iterator.hasNext/next 172 · StringBuilder.append(I) 171 · String.length 166 · ArrayList.<init> 165 · Integer.valueOf 164 · Object.getClass 164 · Intent.<init>(String) 163 · Object.toString 162 · Intent.getAction 156 · Integer.intValue 154 · List.iterator 153 · HashMap.<init> 151 · String.substring(I) 150.
12. **Top root causes (open, exact):** ConstraintLayout.onLayout null-widget (f141) · Notification family absent (0 support, 52 titles) · Telegram j$/desugar + MessagesController · Compose (21 titles) · WebView content (83 titles family, DEFERRED) · native engines Godot/libGDX (recorded boundary).
13. **Root-cause title counts:** see `registry/api_inventory.json` families + divergence_methods (f141 java-family divergences: 9 batch titles).
14. **Laws implemented this wave:** F-NEW-190 (Class.getDeclaredMethods/getInterfaces never-null, real dex arrays) · F-NEW-190b (Class.getSuperclass real hierarchy) · F-NEW-191 (dex method-annotation table parse + Method.getAnnotation/isAnnotationPresent). Plus the §4 parser fix (commit a6e8d911) and the API-inventory/achievements infrastructure (8fab769b).
15. **Laws A/B verified:** F-NEW-190/190b/191 — no.thanks ComponentActivity.<init> 11-frame RuntimeException APP-BOUNDARY escape eliminated; execution now reaches ConstraintLayout.onLayout. Regression: battery ALL PASS 96/96, chess hold, torchlight hold. Parser fix cross-validated against androguard (recall 1.0/1.0).
16. **Graphics pipelines proven:** canonical 11 game GIFs + 24 JPGs remain SHA-verified (0 mismatch); DialogShadow builder chain confirmed present (setTitle/Message/Buttons/setView/create/show + Toast.makeText).
17. **Shell-only titles:** canonical OBSERVED set (S85 near-blank gate) — count 148-title registry OBSERVED rows.
18. **Native-engine blockers:** snakes 0.2.0 Godot (Java fragment layer cleared by F-NEW-188/188b; Godot native runtime = recorded boundary); libGDX EGL frontier (F-NEW-157 family).
19. **AndroidX blockers:** F-NEW-162 root CLEARED this wave; remaining androidx: ConstraintLayout solver (onLayout), Notification family, Compose.
20. **Telegram-specific:** j$/util desugar stream + F084 lambda halt + MessagesController/UserConfig requireNonNull (S89 frontier unchanged this wave).
21. **Achievement assets:** 937 images repo-wide.
22. **Canonical assets:** 36 (12 GIF + 24 JPG).
23. **Duplicates/orphans:** 48 duplicate groups (historical, recorded in manifest, not deleted) · 0 orphan canonical · 0 referenced-but-missing · 0 SHA mismatch.
24. **Achievement navigation centralized:** YES — `docs/achievements/INDEX.md` hub → per-title records, GAMES_WITH_GIFS, APPS_EXECUTED, ASSET_MANIFEST; all views generated from the canonical machine registry.
25. **Corpus as regression matrix:** infrastructure live — profiles keyed by SHA/queue; inventory merges dex-references × execution evidence; law→affected-title selection demonstrated for the lifecycle family (fanout re-run of the full S87 title list is the next scheduled step).

## Measurement honesty

- Method fan-out counts are lower bounds (per-title top-40 persisted).
- `runtime_class_present` in the first inventory build was a naive grep; known false negatives were verified by hand (AlertDialog$Builder, Intent extras) — treat the column as advisory until regenerated with shadow-aware search.
- The S87 12-title family fanout re-run and the Notification-family law (F-NEW-192 candidate) are the next scheduled attacks.
