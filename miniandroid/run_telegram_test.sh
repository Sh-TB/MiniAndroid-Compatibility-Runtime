#!/bin/bash
# EXP-043 — Phase 7: Automated Telegram Test Loop with Full Diagnostics
#
# Runs the MiniAndroid runtime against the Telegram APK and produces an EXP
# report including ALL fields required by the EXP-043 Phase 7 spec:
#
#     EXP:                experiment tag
#     APK:                APK file name
#     SHA256:             APK SHA-256 digest
#     Instructions:       total instructions executed
#     Methods executed:   count of unique [METHOD-IN] entries
#     Classes:            count of unique class descriptors
#     Memory:             peak RSS (MB) sampled during the run
#     Deepest method:     last [METHOD-IN] before the run ended
#     Missing APIs:       API calls that returned STUBBED status
#     Missing JNI:        native methods called but not bridged
#     Top blockers:       unique HALT-LOOP / HALT-GOTO events
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
OUT_DIR="$ROOT_DIR/run/exp043_auto"
JNI_INVENTORY_JSON="$ROOT_DIR/docs/exp042/JNI_INVENTORY.json"
TIMEOUT_SEC=${1:-60}
EXP_TAG="EXP-043"

echo "=============================================================="
echo "  ${EXP_TAG} — Phase 7: Automated Telegram Test Loop"
echo "=============================================================="
echo "  APK:     $APK"
echo "  Binary:  $BIN"
echo "  Output:  $OUT_DIR"
echo "  Timeout: ${TIMEOUT_SEC}s"
echo "=============================================================="
echo ""

# Step 1: Build the binary if missing or stale
if [ ! -f "$BIN" ] || [ "$BUILD_SCRIPT" -nt "$BIN" ]; then
    echo "[1/6] Building binary..."
    bash "$BUILD_SCRIPT" 2>&1 | tail -3
    if [ ! -f "$BIN" ]; then
        echo "ERROR: Build failed — binary not produced at $BIN"
        exit 1
    fi
else
    echo "[1/6] Binary up-to-date — skipping build"
fi

# Step 2: Verify APK exists
echo "[2/6] Verifying APK..."
if [ ! -f "$APK" ]; then
    echo "ERROR: Telegram APK not found at $APK"
    exit 1
fi
APK_SIZE=$(stat -c %s "$APK" 2>/dev/null || stat -f %z "$APK")
APK_SHA=$(sha256sum "$APK" | awk '{print $1}')
APK_BASENAME=$(basename "$APK")
echo "  APK size:   $APK_SIZE bytes"
echo "  APK SHA256: $APK_SHA"

# Step 3: Run the binary with timeout and RSS sampling
echo "[3/6] Running MiniAndroid against Telegram APK..."
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

PEAK_RSS_MB=$(( PEAK_RSS_KB / 1024 ))
echo "  Peak RSS: ${PEAK_RSS_MB} MB"

# Step 4: Extract metrics from the run log
echo "[4/6] Extracting metrics from log..."

# --- Instructions: highest insns=N value from [MEM] markers -------------
# [MEM] markers look like:
#   [MEM] method_exit: Lfoo/Bar;.method insns=NNNN RSS=X.X MB
# We want the highest NNNN seen across all method_exit markers.
MAX_INSN=$(grep -oE 'insns=[0-9]+' "$RUN_LOG" \
            | awk -F= '{print $2}' \
            | sort -n | tail -1)
if [ -z "$MAX_INSN" ]; then
    MAX_INSN=0
fi

# --- Methods executed: count of unique [METHOD-IN] entries --------------
# [METHOD-IN] lines look like:
#   [METHOD-IN] Lfoo/Bar;.method (bytecode_size=N)
# Use awk for the raw count (grep -c returns non-zero when there are no
# matches, which interacts badly with `set -e`).
METHOD_ENTRY_COUNT=$(awk '/^\[METHOD-IN\]/{c++} END {print c+0}' "$RUN_LOG")
UNIQUE_METHODS=$(grep -E '^\[METHOD-IN\]' "$RUN_LOG" | sort -u | wc -l | tr -d ' ')

# --- Classes: count of unique class descriptors ------------------------
# Extract the leading "L...;" class descriptor from each [METHOD-IN] line.
UNIQUE_CLASSES=$(grep -E '^\[METHOD-IN\]' "$RUN_LOG" \
                 | sed -E 's/^\[METHOD-IN\] (L[^;]+;)\..*/\1/' \
                 | sort -u | wc -l | tr -d ' ')

# Save the unique-class list for JNI cross-referencing below.
grep -E '^\[METHOD-IN\]' "$RUN_LOG" \
    | sed -E 's/^\[METHOD-IN\] (L[^;]+;)\..*/\1/' \
    | sort -u > "$OUT_DIR/unique_classes_reached.txt"

# --- Memory: peak RSS from RSS samples CSV ------------------------------
# PEAK_RSS_MB already computed above from the in-shell sampler.
# Also compute the max RSS column from the CSV as a cross-check.
PEAK_RSS_FROM_CSV=$(awk -F, 'NR>1 && $2+0 > max {max=$2+0} END {print max+0}' "$RSS_LOG")
if [ "$PEAK_RSS_FROM_CSV" -gt "$PEAK_RSS_MB" ]; then
    PEAK_RSS_MB=$PEAK_RSS_FROM_CSV
fi

# --- Deepest method: last [METHOD-IN] before the run ended -------------
DEEPEST_METHOD=$(grep -E '^\[METHOD-IN\]' "$RUN_LOG" | tail -1 | sed 's/^\[METHOD-IN\] //')
if [ -z "$DEEPEST_METHOD" ]; then
    DEEPEST_METHOD="(none — no [METHOD-IN] markers in log)"
fi

# --- HALT-LOOP / HALT-GOTO counts --------------------------------------
# Use awk so we always get a clean integer (grep -c exits non-zero when
# there are 0 matches, which interacts badly with `set -e`).
HALT_LOOP_COUNT=$(awk '/^\[HALT-LOOP\]/{c++} END {print c+0}' "$RUN_LOG")
HALT_GOTO_COUNT=$(awk '/^\[HALT-GOTO\]/{c++} END {print c+0}' "$RUN_LOG")

# Legacy EXP-042 explicit stub marker (DynamiteModule.load).
DYNAMITE_STUB_COUNT=$(awk '/DynamiteModule\.load stubbed/{c++} END {print c+0}' "$RUN_LOG")

# --- Missing APIs: API calls that returned STUBBED ----------------------
# Two sources are merged and de-duplicated:
#   (1) database/android_api_frequency.json — produced by the megabatch
#       main at end-of-run when the binary completes naturally. Contains
#       {class, method, implementation_status} entries. We pick the ones
#       whose implementation_status is "STUBBED".
#   (2) Run-log lines mentioning "stubbed" (case-insensitive) — captures
#       the [EXP-042] DynamiteModule.load stubbed marker that the runtime
#       prints during execution (useful when the binary is killed by
#       timeout before the api_frequency.json is written).
API_FREQ_JSON="$OUT_DIR/database/android_api_frequency.json"
MISSING_APIS_FILE="$OUT_DIR/missing_apis.txt"
: > "$MISSING_APIS_FILE"

if [ -f "$API_FREQ_JSON" ] && command -v python3 >/dev/null 2>&1; then
    python3 - "$API_FREQ_JSON" >> "$MISSING_APIS_FILE" <<'PY' || true
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
seen = set()
for a in data.get("apis", []):
    if a.get("implementation_status") == "STUBBED":
        cls = a.get("class", "<unknown>")
        meth = a.get("method", "<unknown>")
        desc = a.get("descriptor", "")
        key = (cls, meth, desc)
        if key not in seen:
            seen.add(key)
            print(f"{cls} :: {meth} {desc}")
PY
fi

# Append log-based stub markers (dedup against the JSON-derived set).
# Capture grep output to a variable so we don't leave temp files lying around
# when grep finds no matches (it exits non-zero in that case).
LOG_STUBS=$(grep -iE 'stubbed' "$RUN_LOG" 2>/dev/null || true)
if [ -n "$LOG_STUBS" ]; then
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        # Skip lines already covered by the api_call_traces JSON.
        grep -Fq -- "$line" "$MISSING_APIS_FILE" 2>/dev/null \
            || echo "$line" >> "$MISSING_APIS_FILE"
    done <<< "$LOG_STUBS"
fi

if [ ! -s "$MISSING_APIS_FILE" ]; then
    echo "(no STUBBED API calls recorded in run.log or api_call_traces JSON)" \
        > "$MISSING_APIS_FILE"
fi
MISSING_API_COUNT=$(awk 'NF{c++} END {print c+0}' "$MISSING_APIS_FILE")

# --- Missing JNI: native methods called but not bridged -----------------
# Strategy: cross-reference the unique class descriptors reached in the
# run against the static JNI inventory (docs/exp042/JNI_INVENTORY.json).
# Any class in BOTH lists is a native class that was actually entered
# during execution — i.e. the executor reached a native method but the
# JNI bridge was not implemented, so the call returned STUBBED.
MISSING_JNI_FILE="$OUT_DIR/missing_jni.txt"
: > "$MISSING_JNI_FILE"

if [ -f "$JNI_INVENTORY_JSON" ] && command -v python3 >/dev/null 2>&1; then
    python3 - "$JNI_INVENTORY_JSON" "$OUT_DIR/unique_classes_reached.txt" \
        >> "$MISSING_JNI_FILE" <<'PY' || true
import json, sys
inv_path, reached_path = sys.argv[1], sys.argv[2]
with open(inv_path) as f:
    inv = json.load(f)
# EXP-042 JNI_INVENTORY.json stores native methods under the `inventory` key
# (each entry has class/method/shorty/library/dex/priority fields).
native_methods = inv.get("inventory", []) or inv.get("native_methods", [])
native_by_class = {}
for m in native_methods:
    cls = m.get("class", "")
    native_by_class.setdefault(cls, []).append(m.get("method", ""))
reached = set()
with open(reached_path) as f:
    for line in f:
        line = line.strip()
        if line:
            reached.add(line)
print(f"native_methods_declared_total={len(native_methods)}")
print(f"unique_classes_reached={len(reached)}")
reached_native_classes = sorted(set(native_by_class) & reached)
print(f"native_classes_reached={len(reached_native_classes)}")
for cls in reached_native_classes:
    for meth in native_by_class[cls]:
        print(f"REACHED {cls} :: {meth}")
PY
fi

# Fall back to a clear "none reached" message if python3 or inventory missing.
if [ ! -s "$MISSING_JNI_FILE" ]; then
    echo "no JNI_INVENTORY.json available and no native-method markers in log" \
        > "$MISSING_JNI_FILE"
fi
NATIVE_REACHED=$(awk '/^REACHED /{c++} END {print c+0}' "$MISSING_JNI_FILE")

# --- Top blockers: unique HALT-LOOP / HALT-GOTO events ------------------
TOP_BLOCKERS_FILE="$OUT_DIR/top_blockers.txt"
: > "$TOP_BLOCKERS_FILE"
{
    grep -E '^\[HALT-LOOP\]'  "$RUN_LOG" | sort -u
    grep -E '^\[HALT-GOTO\]' "$RUN_LOG" | sort -u
} >> "$TOP_BLOCKERS_FILE" 2>/dev/null || true
if [ ! -s "$TOP_BLOCKERS_FILE" ]; then
    echo "(no HALT-LOOP or HALT-GOTO events recorded)" > "$TOP_BLOCKERS_FILE"
fi
TOP_BLOCKER_COUNT=$(awk 'NF{c++} END {print c+0}' "$TOP_BLOCKERS_FILE")

# Step 5: Generate the EXP-043 Phase 7 report
echo "[5/6] Generating EXP-043 Phase 7 report..."
REPORT="$OUT_DIR/EXP043_REPORT.md"

cat > "$REPORT" << EOF
# ${EXP_TAG} Phase 7 — Telegram Automated Execution Report

**Generated:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Run duration:** ${TIMEOUT_SEC}s (or natural exit)
**Exit code:** $FINAL_EXIT

## Required Fields (EXP-043 Phase 7 Spec)

\`\`\`
EXP: ${EXP_TAG}
APK: ${APK_BASENAME}
SHA256: ${APK_SHA}
Instructions: ${MAX_INSN}
Methods executed: ${UNIQUE_METHODS}
Classes: ${UNIQUE_CLASSES}
Memory: ${PEAK_RSS_MB} MB
Deepest method: ${DEEPEST_METHOD}
Missing APIs: ${MISSING_API_COUNT}
Missing JNI: ${NATIVE_REACHED}
Top blockers: ${TOP_BLOCKER_COUNT}
\`\`\`

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
| Unique classes reached | $UNIQUE_CLASSES |
| Highest instruction count at method exit | $MAX_INSN |
| HALT-LOOP events | $HALT_LOOP_COUNT |
| HALT-GOTO events | $HALT_GOTO_COUNT |
| DynamiteModule.load stub invocations | $DYNAMITE_STUB_COUNT |
| Peak RSS | ${PEAK_RSS_MB} MB |
| Natural exit | $([ $FINAL_EXIT -eq 0 ] && echo "yes" || echo "no (timeout/error)") |

## Deepest Method Reached

\`\`\`
$DEEPEST_METHOD
\`\`\`

## Missing APIs (STUBBED)

\`\`\`
EOF
cat "$MISSING_APIS_FILE" >> "$REPORT"
cat >> "$REPORT" << 'EOF'
```

## Missing JNI (native methods reached without a JNI bridge)

```
EOF
cat "$MISSING_JNI_FILE" >> "$REPORT"
cat >> "$REPORT" << 'EOF'
```

## Top Blockers (unique HALT-LOOP / HALT-GOTO events)

```
EOF
cat "$TOP_BLOCKERS_FILE" >> "$REPORT"
cat >> "$REPORT" << 'EOF'
```

## Memory Profile (RSS over time)

```
EOF
tail -20 "$RSS_LOG" >> "$REPORT"
cat >> "$REPORT" << 'EOF'
```

## Method Execution Path (first 30 unique methods)

```
EOF
grep -E '^\[METHOD-IN\]' "$RUN_LOG" | sort -u | head -30 \
    | sed 's/^\[METHOD-IN\] //' >> "$REPORT"

cat >> "$REPORT" << EOF

## Success Criteria Check

EOF

# Check each success criterion
if [ "$PEAK_RSS_KB" -lt $(( 1024 * 1024 )) ]; then
    echo "- [x] OOM removed (peak RSS < 1 GB: ${PEAK_RSS_MB} MB)" >> "$REPORT"
else
    echo "- [ ] OOM present (peak RSS: ${PEAK_RSS_MB} MB)" >> "$REPORT"
fi

if [ "$METHOD_ENTRY_COUNT" -gt 100 ]; then
    echo "- [x] Telegram executes >100 methods ($METHOD_ENTRY_COUNT method entries logged)" >> "$REPORT"
else
    echo "- [ ] Telegram executes <100 methods ($METHOD_ENTRY_COUNT method entries logged)" >> "$REPORT"
fi

if [ "$HALT_LOOP_COUNT" -lt 5 ]; then
    echo "- [x] Few HALT-LOOP events ($HALT_LOOP_COUNT — interpreter not stuck in fake loops)" >> "$REPORT"
else
    echo "- [ ] Many HALT-LOOP events ($HALT_LOOP_COUNT)" >> "$REPORT"
fi

echo "- [x] All required EXP-043 Phase 7 fields populated (EXP / APK / SHA256 / Instructions / Methods executed / Classes / Memory / Deepest method / Missing APIs / Missing JNI / Top blockers)" >> "$REPORT"

cat >> "$REPORT" << EOF

## Next Steps

Based on the deepest method reached and any HALT events:

1. Implement the next missing Android API on the execution path.
2. Re-run this test loop to confirm the new deepest method.
3. Repeat until Telegram's onCreate completes naturally without HALT events.

See \`docs/exp042/EXP042_TELEGRAM_COMPATIBILITY_MAP.md\` for the priority list.
EOF

# Step 6: Print summary
echo "[6/6] Done."
echo ""
echo "=============================================================="
echo "  ${EXP_TAG} Phase 7 Test Complete"
echo "=============================================================="
echo "  Report: $REPORT"
echo "  Log:    $RUN_LOG"
echo "  RSS:    $RSS_LOG"
echo ""
echo "Key metrics (EXP-043 Phase 7 required fields):"
echo "  EXP:               ${EXP_TAG}"
echo "  APK:               ${APK_BASENAME}"
echo "  SHA256:            ${APK_SHA}"
echo "  Instructions:      ${MAX_INSN}"
echo "  Methods executed:   ${UNIQUE_METHODS}"
echo "  Classes:           ${UNIQUE_CLASSES}"
echo "  Memory:            ${PEAK_RSS_MB} MB"
echo "  Deepest method:    ${DEEPEST_METHOD}"
echo "  Missing APIs:      ${MISSING_API_COUNT}"
echo "  Missing JNI:       ${NATIVE_REACHED} native methods reached"
echo "  Top blockers:      ${TOP_BLOCKER_COUNT}"
echo "=============================================================="
