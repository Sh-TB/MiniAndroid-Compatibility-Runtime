# MiniAndroid Backlog

Ordered by execution priority (lowest blocking layer first).

## Active (EXP-043 cycle)

| ID | Priority | Description | Status |
|----|---------:|-------------|---------|
| EXP-043-P1 | P0 | Intrinsics/Kotlin compatibility — fix createParameterIsNullExceptionMessage loop, document STUB_DEBT | in_progress |
| EXP-043-P2 | P0 | JNI Early Reach Analysis — scan DEX for native methods + System.loadLibrary, build JNI_DISTANCE.md | pending |
| EXP-043-P3 | P0 | Android Framework Priority Layer — Context/Resources/System/Log APIs proven by traces | pending |
| EXP-043-P4 | P1 | Persistent Telegram Sandbox — wire SharedPreferences + File I/O, run twice to validate | pending |
| EXP-043-P5 | P1 | Loop Detector Validation — finite/infinite/nested/exception tests | pending |
| EXP-043-P6 | P2 | Telegram source-driven compatibility (ApplicationLoader, SharedConfig, UserConfig) | pending |
| EXP-043-P7 | P2 | Diagnostics improvement — execution report fields | pending |

## Deferred (waiting on lower layers)

| ID | Priority | Description |
|----|---------:|-------------|
| FUTURE | P1 | JNI bridge implementation — 462 native methods to dispatch |
| FUTURE | P1 | libtmessages.49.so loading (10 DT_NEEDED, 376 Java_* exports) |
| FUTURE | P2 | SQLite storage layer (23 methods, used by Telegram messages) |
| FUTURE | P2 | RLottie animations (6 methods, used for stickers) |
| FUTURE | P2 | TgNet network protocol (38 methods, used for messaging) |
| FUTURE | P3 | UI rendering — Surface, Canvas, View inflation |
| FUTURE | P3 | VoIP / WebRTC (~70 methods) |
| FUTURE | P3 | ExoPlayer decoders (ffmpeg, flac, opus) |

## Completed (most recent)

| ID | Date | Description |
|----|------|-------------|
| EXP-042-P7 | 2026-08-16 | Automated Telegram test loop |
| EXP-042-P6 | 2026-08-16 | Native library analysis (ELF metadata) |
| EXP-042-P5 | 2026-08-16 | JNI inventory (462 native methods) |
| EXP-042-P4 | 2026-08-16 | Android framework minimal runtime (16 P0/P1 APIs) |
| EXP-042-P3 | 2026-08-16 | Telegram source compatibility map |
| EXP-042-P2 | 2026-08-16 | Execution path tracing (5 blockers A-E) |
| EXP-042-P1 | 2026-08-16 | Memory architecture fix (438-440 MB flat) |
