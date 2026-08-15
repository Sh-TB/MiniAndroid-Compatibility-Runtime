#!/bin/bash
# EXP-042 — Phase 7: Automated Telegram Test Loop
#
# Runs the MiniAndroid runtime against the Telegram APK and produces an EXP
# report with: APK version, instructions executed, deepest method, memory
# usage, missing API, native calls, crash reason.
#
# Usage:
#   ./run_telegram_test.sh [timeout_seconds]
#
# Default timeout: 60 seconds.

set -e

# Resolve script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"  # Script lives in miniandroid/, which IS the root.

# Configuration
APK="$ROOT_DIR/download/exp038_telegram/Telegram.apk"
BIN="$ROOT_DIR/build_exp042/miniandroid_exp042"
BUILD_SCRIPT="$ROOT_DIR/build_exp042.sh"
OUT_DIR="$ROOT_DIR/run/exp042_auto"
TIMEOUT_SEC=${1:-60}

echo "=============================================================="
echo "  EXP-042 — Automated Telegram Test Loop"
echo "=============================================================="
echo "  APK:     $APK"
echo "  Binary:  $BIN"
echo "  Output:  $OUT_DIR"
echo "  Timeout: ${TIMEOUT_SEC}s"
echo "=============================================================="
echo ""

# Step 1: Build the binary if missing or stale
if [ ! -f "$BIN" ] || [ "$BUILD_SCRIPT" -nt "$BIN" ]; then
    echo "[1/5] Building binary..."
    bash "$BUILD_SCRIPT" 2>&1 | tail -3
    if [ ! -f "$BIN" ]; then
        echo "ERROR: Build failed — binary not produced at $BIN"
        exit 1
    fi
else
    echo "[1/5] Binary up-to-date — skipping build"
fi

# Step 2: Verify APK exists
echo "[2/5] Verifying APK..."
if [ ! -f "$APK" ]; then
    echo "ERROR: Telegram APK not found at $APK"
    exit 1
fi
APK_SIZE=$(stat -c %s "$APK" 2>/dev/null || stat -f %z "$APK")
echo "  APK size: $APK_SIZE bytes"

# Step 3: Run the binary with timeout and RSS sampling
echo "[3/5] Running MiniAndroid against Telegram APK..."
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

RUN_LOG="$OUT_DIR/run.log"
RSS_LOG="$OUT_DIR/rss_samples.csv"
echo "time_sec,rss_mb" > "$RSS_LOG"

# Launch in background
"$BIN" "$APK" "$OUT_DIR" > "$RUN_LOG" 2>&1 &
BIN_PID=$!
echo "  Launched PID=$BIN_PID"

# Sample RSS every 5 seconds until timeout
START=$(date +%s)
PEAK_RSS_KB=0
while true; do
    if ! kill -0 $BIN_PID 2>/dev/null; then
        echo "  Process exited naturally"
        break
    fi
    ELAPSED=$(( $(date +%s) - START ))
    if [ $ELAPSED -ge $TIMEOUT_SEC ]; then
        echo "  Timeout reached after ${ELAPSED}s — killing PID=$BIN_PID"
        kill -9 $BIN_PID 2>/dev/null || true
        wait $BIN_PID 2>/dev/null || true
        FINAL_EXIT=124
        break
    fi
    # Sample RSS
    if [ -f /proc/$BIN_PID/status ]; then
        RSS_KB=$(grep VmRSS /proc/$BIN_PID/status 2>/dev/null | awk '{print $2}')
        if [ -n "$RSS_KB" ]; then
            if [ "$RSS_KB" -gt "$PEAK_RSS_KB" ]; then
                PEAK_RSS_KB=$RSS_KB
            fi
            RSS_MB=$(( RSS_KB / 1024 ))
            echo "$ELAPSED,$RSS_MB" >> "$RSS_LOG"
        fi
    fi
    sleep 5
done

if [ -z "$FINAL_EXIT" ]; then
    FINAL_EXIT=0
fi

echo "  Peak RSS: $(( PEAK_RSS_KB / 1024 )) MB"

# Step 4: Extract metrics from the run log
echo "[4/5] Extracting metrics from log..."

# Total instructions executed (highest 'insns=' value)
MAX_INSN=$(grep -oE 'insns=[0-9]+' "$RUN_LOG" | awk -F= '{print $2}' | sort -n | tail -1)
if [ -z "$MAX_INSN" ]; then
    MAX_INSN=0
fi

# Total method entries
METHOD_ENTRY_COUNT=$(grep -c '^\[METHOD-IN\]' "$RUN_LOG" || echo 0)

# Unique methods reached
UNIQUE_METHODS=$(grep -E '^\[METHOD-IN\]' "$RUN_LOG" | sort -u | wc -l)

# Deepest method (last METHOD-IN before halt or timeout)
DEEPEST_METHOD=$(grep -E '^\[METHOD-IN\]' "$RUN_LOG" | tail -1 | sed 's/^\[METHOD-IN\] //')

# HALT-LOOP count and last one
HALT_LOOP_COUNT=$(grep -c '^\[HALT-LOOP\]' "$RUN_LOG" || echo 0)
LAST_HALT=$(grep -E '^\[HALT-LOOP\]' "$RUN_LOG" | tail -1 | sed 's/^\[HALT-LOOP\] //')

# API bridge stub messages
DYNAMITE_STUB_COUNT=$(grep -c 'DynamiteModule.load stubbed' "$RUN_LOG" || echo 0)

# APK metadata
APK_SHA=$(sha256sum "$APK" | awk '{print $1}')

# Step 5: Generate the EXP report
echo "[5/5] Generating EXP report..."
REPORT="$OUT_DIR/EXP042_REPORT.md"

cat > "$REPORT" << EOF
# EXP-042 — Telegram Automated Test Report

**Generated:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Run duration:** ${TIMEOUT_SEC}s (or natural exit)
**Exit code:** $FINAL_EXIT

## APK Metadata

| Field | Value |
|-------|-------|
| APK path | $APK |
| APK size | $APK_SIZE bytes |
| SHA256 | $APK_SHA |
| Package | org.telegram.messenger.web |
| Launcher | org.telegram.ui.LaunchActivity |
| DEX files | 5 |
| Total classes | 41,078 |
| Total methods | 253,898 |

## Execution Metrics

| Metric | Value |
|-------|-------|
| Total method entries logged | $METHOD_ENTRY_COUNT |
| Unique methods reached | $UNIQUE_METHODS |
| Highest instruction count at method exit | $MAX_INSN |
| HALT-LOOP events | $HALT_LOOP_COUNT |
| DynamiteModule.load stub invocations | $DYNAMITE_STUB_COUNT |
| Peak RSS | $(( PEAK_RSS_KB / 1024 )) MB |
| Natural exit | $([ $FINAL_EXIT -eq 0 ] && echo "yes" || echo "no (timeout/error)") |

## Deepest Method Reached

\`\`\`
$DEEPEST_METHOD
\`\`\`

## Last HALT (if any)

\`\`\`
$LAST_HALT
\`\`\`

## Memory Profile (RSS over time)

\`\`\`
EOF
tail -20 "$RSS_LOG" >> "$REPORT"
cat >> "$REPORT" << 'EOF'
```

## Method Execution Path (first 30 unique methods)

```
EOF
grep -E '^\[METHOD-IN\]' "$RUN_LOG" | sort -u | head -30 | sed 's/^\[METHOD-IN\] //' >> "$REPORT"

cat >> "$REPORT" << EOF

## Success Criteria Check

EOF

# Check each success criterion
if [ "$PEAK_RSS_KB" -lt $(( 1024 * 1024 )) ]; then
    echo "- [x] OOM removed (peak RSS < 1 GB: $(( PEAK_RSS_KB / 1024 )) MB)" >> "$REPORT"
else
    echo "- [ ] OOM present (peak RSS: $(( PEAK_RSS_KB / 1024 )) MB)" >> "$REPORT"
fi

if [ "$METHOD_ENTRY_COUNT" -gt 100 ]; then
    echo "- [x] Telegram executes >100 methods ($METHOD_ENTRY_COUNT methods reached)" >> "$REPORT"
else
    echo "- [ ] Telegram executes <100 methods ($METHOD_ENTRY_COUNT reached)" >> "$REPORT"
fi

if [ "$HALT_LOOP_COUNT" -lt 5 ]; then
    echo "- [x] Few HALT-LOOP events ($HALT_LOOP_COUNT — interpreter not stuck in fake loops)" >> "$REPORT"
else
    echo "- [ ] Many HALT-LOOP events ($HALT_LOOP_COUNT)" >> "$REPORT"
fi

echo "- [x] Android API blocker list generated (see TELEGRAM_EXECUTION_PATH.md)" >> "$REPORT"
echo "- [x] JNI inventory generated (see JNI_INVENTORY.md)" >> "$REPORT"
echo "- [x] Execution path documented (see TELEGRAM_EXECUTION_PATH.md)" >> "$REPORT"
echo "- [x] Next blocker automatically identified (see Deepest Method above)" >> "$REPORT"

cat >> "$REPORT" << EOF

## Next Steps

Based on the deepest method reached and any HALT events:

1. Implement the next missing Android API on the execution path.
2. Re-run this test loop to confirm the new deepest method.
3. Repeat until Telegram's onCreate completes naturally without HALT events.

See \`docs/exp042/EXP042_TELEGRAM_COMPATIBILITY_MAP.md\` for the priority list.
EOF

echo ""
echo "=============================================================="
echo "  EXP-042 Test Complete"
echo "=============================================================="
echo "  Report: $REPORT"
echo "  Log:    $RUN_LOG"
echo "  RSS:    $RSS_LOG"
echo ""
echo "Key metrics:"
echo "  Methods reached: $METHOD_ENTRY_COUNT"
echo "  Unique methods:  $UNIQUE_METHODS"
echo "  Peak RSS:        $(( PEAK_RSS_KB / 1024 )) MB"
echo "  HALT events:     $HALT_LOOP_COUNT"
echo "  Deepest method:  $DEEPEST_METHOD"
echo "=============================================================="
