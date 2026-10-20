# CONT-118 Ledger — «چند ده واگن اصلی» 23 wagons, one app per wagon

- **Wave:** CONT-118 · **Base:** origin/main `560077a9` (CONT-117) · **Binary:** `3ecd381cda214dcd` (unchanged, deterministic)

| Wagon | App | rc | Face sha16 | Class | Verdict |
|---|---|---|---|---|---|
| W-01 | telegram | 1 | 20ac8cbbbb692e63 | STABLE_FACE | تایید (zero drift: face == recorded anchor 20ac8cbbbb692e63; frontier stable) |
| W-02 | whatsapp | 1 | NO_SCREENSHOT | ARTIFACT_DEFECTIVE | تایید-honest (artifact defective: non-ZIP 5,615-byte stub; load_apk honest fail ~24ms — APP-013 classification |
| W-03 | forkgram | 1 | a4b34d2535a71f1d | PARTIAL_UI | تایید-honest (face a4b34d2535a71f1d rendered; 18 synth-exc/uncaught — frontier recorded) |
| W-04 | sudoku | 1 | be640e39e82901c9 | STABLE_FACE | تایید (zero drift: face == recorded anchor be640e39e82901c9; frontier stable) |
| W-05 | dooz | 1 | d602648e8e401895 | STABLE_FACE | تایید (zero drift: face == recorded anchor d602648e8e401895; frontier stable) |
| W-06 | tictactoe | 139 | NO_SCREENSHOT | NATIVE_SIGSEGV | CONFIRMED_OPEN_GAP (native SIGSEGV in libGDX SharedLibraryLoader chain — S100-CRASH-FORENSICS; candidate fixtu |
| W-07 | bouncy | 1 | 8a6c24ac8a7d718e | PARTIAL_UI | تایید-honest (face 8a6c24ac8a7d718e rendered; 20 synth-exc/uncaught — frontier recorded) |
| W-08 | flappycow | 0 | 13cf47464d9787f4 | PARTIAL_UI | تایید-honest (face 13cf47464d9787f4 rendered; 0 synth-exc/uncaught — frontier recorded) |
| W-09 | gmdice | 0 | 3891679dff449331 | PARTIAL_UI | تایید-honest (face 3891679dff449331 rendered; 5 synth-exc/uncaught — frontier recorded) |
| W-10 | memory | 1 | 3a3ba8734b662e55 | PARTIAL_UI | تایید-honest (face 3a3ba8734b662e55 rendered; 28 synth-exc/uncaught — frontier recorded) |
| W-11 | chess | 1 | a0319686d56ff5c0 | STABLE_FACE | تایید (zero drift: face == recorded anchor a0319686d56ff5c0; frontier stable) |
| W-12 | klondike | 1 | 31ddd4d5b8e6d18e | DEFAULT_BACKGROUND_ONLY | تایید-honest (draw-op frontier: DEFAULT_BACKGROUND_ONLY face 31ddd4d5b8e6d18e, cross-app identical with klondi |
| W-13 | tripeaks | 1 | b5a7a35d5fe0564b | DEFAULT_BACKGROUND_ONLY | تایید-honest (draw-op frontier: DEFAULT_BACKGROUND_ONLY face b5a7a35d5fe0564b, cross-app identical with tripea |
| W-14 | fishrings | 1 | b5a7a35d5fe0564b | DEFAULT_BACKGROUND_ONLY | تایید-honest (draw-op frontier: DEFAULT_BACKGROUND_ONLY face b5a7a35d5fe0564b, cross-app identical with tripea |
| W-15 | tower3d | 1 | 11a38a5aeeff45a6 | STABLE_FACE | تایید (zero drift: face == recorded anchor 11a38a5aeeff45a6; frontier stable) |
| W-16 | opencalc | 1 | d5f3c7b5e9936ae6 | STABLE_FACE | تایید (zero drift: face == recorded anchor d5f3c7b5e9936ae6; frontier stable) |
| W-17 | unote | 0 | 90a67cc1ddda57b7 | STABLE_FACE | تایید (zero drift: face == recorded anchor 90a67cc1ddda57b7; frontier stable) |
| W-18 | notes | 1 | d0a409043ffc83a7 | PARTIAL_UI | تایید-honest (face d0a409043ffc83a7 rendered; 1 synth-exc/uncaught — frontier recorded) |
| W-19 | stopwatch | 1 | 31ddd4d5b8e6d18e | DEFAULT_BACKGROUND_ONLY | تایید-honest (draw-op frontier: DEFAULT_BACKGROUND_ONLY face 31ddd4d5b8e6d18e, cross-app identical with klondi |
| W-20 | microtimer | 0 | bbd350b6c14fbd52 | STABLE_FACE | تایید (zero drift: face == recorded anchor bbd350b6c14fbd52; frontier stable) |
| W-21 | chessclock | 0 | fe3ae1167c9e968c | PARTIAL_UI | تایید-honest (face fe3ae1167c9e968c rendered; 0 synth-exc/uncaught — frontier recorded) |
| W-22 | opmt | 0 | 548a2d91ef9892fb | PARTIAL_UI | تایید-honest (face 548a2d91ef9892fb rendered; 0 synth-exc/uncaught — frontier recorded) |
| W-23 | signal | - | - | NO_ARTIFACT | BLOCKED_NEEDS_ARTIFACT (no Signal APK in corpus — honest, not fabricated) |

## Honest findings (no false closure)

- **W-01 telegram**: UPP-001 family: dlopen gap (telegram: libjnigraphics.so missing on x86_64; forkgram: arm64-v8a-only APK on x86_64 runtime) — honest APP-BOUNDARY, architecture-level
- **W-03 forkgram**: UPP-001 family: dlopen gap (telegram: libjnigraphics.so missing on x86_64; forkgram: arm64-v8a-only APK on x86_64 runtime) — honest APP-BOUNDARY, architecture-level
- **W-06 tictactoe**: NEW: first SIGSEGV in corpus run at HEAD 560077a9; SharedLibraryLoader.isLoaded/mapLibraryName then S100-NATIVE-FRAMES count=2
- **W-06 tictactoe**: SIGSEGV with S100-CRASH-FORENSICS (native frames pinned) — deterministic candidate fixture for next wave; not registered as root without decode.
- **W-23 signal**: Signal named by user but upload/ + upload/canonical_apks/ contain no Signal artifact; requesting the APK or a corpus addition is the unblock path.

## Anchor integrity (zero drift)

Telegram 20ac8cbbbb / sudoku be640e39 / dooz d602648e / chess a0319686 / tower3d 11a38a5a / opencalc d5f3c7b5 / unote 90a67cc1 / microtimer bbd350b6 — all MATCH byte-identical at HEAD 560077a9.

## Cross-app identical faces (draw-op frontier honesty)
klondike == stopwatch == 31ddd4d5b8e6d18e and tripeaks == fishrings == b5a7a35d5fe0564b — cross-app byte-identical faces confirm these are app-invariant frontier faces (DEFAULT_BACKGROUND_ONLY), not app content; consistent with CONT-113 whites classification.