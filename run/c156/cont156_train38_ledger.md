# CONT-156 Trains 3-8 — cohort crossings + corpus re-battery (116 apps)

Binary chain: d7d3d61a (rebuild #10) → 2dc7f5b4 (F-NEW-486 WindowMetrics) → 9a36acf0 (F-NEW-487 FNA fallback) → dd2622762 (F-NEW-488 PM.getApplicationInfo). Wall 9/9 MATCH at every step; negatives 19/19; selftest 13/13.

## WINDOW_ROOT cohort (17 apps): 9/17 → 12/17 render
New crossings: aat (F-NEW-486, 99.3%), librecontactsbackup (74.1%, rendered alongside the 486 build), ghostsq commander (F-NEW-487, 99.4%), + the CONT-155 six (flashlight/voyager/how2vote/fossify-contacts/fossify-filemanager/subster) and leradar/exodusprivacy/todolist (F-NEW-484) measured fresh at 99.4%.
Remaining 5 blanks — all honestly CLASSIFIED: ricochlime (FLUTTER-BOUNDARY, F-NEW-489), goodtime (Constructor.newInstance silent-null family, F-NEW-490), readrops (Koin vararg-null, F-NEW-491), fdroid-pe (attach ok=false, F-NEW-492), shizuwall (Shizuku binder IPC boundary, F-NEW-493).

## fdroid_batch re-battery (94 apps, fresh, binary dd2622762)
- >=50% real-content: **85/94** (c154: 73/94) — **12 crossings, 0 regressions**.
- >1% (c154 metric): **86/94**.
- Blanks: sparkledns (73 exc — old default-background family), ricochlime, goodtime, shizuwall, readrops, lexica, termux.api (19.5%), dmfs.tasks, fdroid-pe.

## canonical 22 (fresh runs, run/c156/canon/)
17/21 non-white>1% (klondike/stopwatch = byte-stable boundary faces, wall-MATCHed; forkgram/telegram = UPP-001 dlopen APP-BOUNDARY; whatsapp = corrupt artifact, honest NO-SHOT). The 9 anchors byte-identical across ALL THREE intermediate binaries.

## scorecard -> run/c156/big/scorecard.json (94 rows, face_pct + rc + exceptions per app)
