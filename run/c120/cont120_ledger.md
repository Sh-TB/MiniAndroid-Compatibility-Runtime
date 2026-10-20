# CONT-120 Ledger — «حل ۳۶۴ با این روش تمامشون رو حل بکن» landing wave: 10 wagons, all terminal

- **Wave:** CONT-120 · **Base:** origin/main `07166cce` (CONT-119) · Binary rebuilt (4 TUs changed); **9/9 anchors zero drift**

| Wagon | Problem carried | Verdict |
|---|---|---|
| W-01 | FIX-TTT tictactoe SIGSEGV root | تایید ROOT-CAUSED-FIXED (F-NEW-466 new row: libgdx.so x86_64 faults INSIDE host loader dlopen — fork-probe reproduced standalone; tower3d libgdx same family loads clean = per-library defect. Three-layer guarded-native law: fork pre-probe → sigsetjmp guard → poison-teardown. rc 139→1, honest UnsatisfiedLinkError into libGDX's own catch-all, 5 frames) |
| W-02 | FIX-D12 wrong-thread law | تایید LANDED (ViewShadow.checkThread: mutations from drained bg-thread body raise CalledFromWrongThreadException with AOSP message; posted runnables stay legal via Looper-drain identity re-bind; MINIANDROID_D12_LAW=0 opt-out. Probe: D12- PASS raised-and-typed + POSTED recovery legal) |
| W-03 | memory typed-catch ×24 (unified0113) | تایید LANDED (five reflective rows un-gated into the unconditional table → F106-CTOR delivers in-frame in the DEFAULT binary; app's own AOSP-verbatim catch log ran; uncaught 0; face 6da289aa == CONT-71 F368-only activation byte-for-byte; MCM lever stays honest PARTIAL) |
| W-04 | bouncy SurfaceHolder null (F-NEW-462 facet-2) | تایید LANDED (GLSurfaceView.getHolder holder-per-view law; setFormat-null NPE closed count=0; Set-add root isolated as independent — honest OPEN remains) |
| W-05 | FIX-449 walk isolation (lead lever) | تایید PROBE 3/3 (count-token law in-bounds; rotated-terminator reproduces EXACT S36 signature AOOB length=11 index=11; buffer 3-ints/field → walk ops engine-correct, divergence isolated to c3.<clinit> data construction — root narrowed, stays OPEN honestly) |
| W-06 | FIX-D05 unknown-field substrate | تایید PROBE 5/5 (byte-equal round-trip incl. unknown f15/f9 captured verbatim — UnknownFieldSchema contract executes on the substrate) |
| W-07 | Zero-drift wall after 4 engine changes | تایید 9/9 ANCHOR_MATCH (dooz/opencalc/unote/microtimer/chess/tower3d/sudoku/klondike/telegram) + negatives PASS + selftest PASS + registry 781 id-unique main==mirror |
| W-08 | Registry integrity | تایید (F-NEW-466 added honestly; F-NEW-368/F-NEW-449/F-NEW-462 evidence landed by ID; 780→781, no inflation, main==mirror row-equal) |
| W-09 | Teardown hang after loader poison | تایید (the _dl_fini walk over the partially-loaded lib hangs exit — the run command leaves via _exit after evidence flush when loader_poisoned; control app exits 1.7s unchanged) |
| W-10 | Honest rejections | تایيد-honest (Bouncy upstream source unreachable from this container — decode continues from the APK next wave; android-34 stub jar lacks CalledFromWrongThreadException — probe checks the raised type BY NAME; tictactoe app-level GdxRuntimeException path is the app's own handling without natives, the RUNTIME no longer dies) |

## Scorecard

- 10 wagons, all terminal. 4 product laws LANDED + 2 probe isolations + 1 new root-cause row; 9/9 anchors zero drift.
- Named-lever progress: FIX-TTT closed (first corpus process-death crash now honest); FIX-D12 closed (law + probe); memory fan-out-24 delivered in-frame (MCM visual lever stays open); bouncy GL-holder closed (Set-add isolated); FIX-449 root narrowed to data construction.
- Honest discipline: every open item stayed open (F-NEW-449 CONFIRMED_OPEN_GAP, F-NEW-368 PARTIAL, Set-add independent root, Signal BLOCKED) — no false closures.

## Next train cars

1. c3.<clinit> data-construction bisect (R337 rows) — FIX-449 endgame, unlocks the 16 telegram PARTIAL tasks.
2. bouncy Set-add root decode from the APK bytecode.
3. F-NEW-374 MCM per-container-trust lever (memory full visual completion).
4. B-cluster UNPROVEN dated re-scan (48 roots).
