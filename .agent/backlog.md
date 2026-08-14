# Backlog — EXP-038 Telegram Compatibility

## P0 — Critical (blocking Telegram execution)

### BLOCKER-023: APK Parser Caching
- [ ] Implement central directory cache in ApkParser
- [ ] Parse ZIP entries ONCE, store in map<string, ZipEntry>
- [ ] extract_entry_from_memory uses cache lookup, not re-parse
- **Expected result**: Telegram APK loads in <1 second instead of hanging

### BLOCKER-024: MultiDex Support
- [ ] Load all classes*.dex files from APK
- [ ] Parse each DEX separately
- [ ] Merge DexReports (combine classes, methods, fields, strings, types)
- [ ] Verify class count: 12,521 → 41,078
- **Expected result**: All Telegram classes available to runtime

## P1 — After P0 unblocks

### P1-001: DEX Execution of LaunchActivity.onCreate()
- [ ] Run Telegram after P0 fixes
- [ ] Capture first DEX execution blocker
- [ ] Fix opcode/API issues as they appear

### P1-002: Recursive DEX Method Invocation
- [ ] invoke-* should resolve method in DEX
- [ ] If bytecode exists, create new frame and execute recursively
- [ ] Return result to caller

## P2 — Android Framework APIs

### P2-001: Activity API
- [ ] onCreate (stub exists, needs real implementation)
- [ ] getIntent
- [ ] finish
- [ ] startActivity

### P2-002: Intent API
- [ ] getAction
- [ ] getStringExtra
- [ ] putExtra

### P2-003: Context API
- [ ] getSystemService
- [ ] getApplicationContext

## P3 — Object Model
- [ ] Class instance fields (read/write)
- [ ] Inheritance lookup (walk superclass chain)
- [ ] Virtual dispatch (proper VTable)
- [ ] Monitor/thread basics

## P4 — Native/JNI
- [ ] Detect native methods (is_native flag)
- [ ] Report libtmessages.49.so as required
- [ ] Document JNI boundary (do NOT fake)
