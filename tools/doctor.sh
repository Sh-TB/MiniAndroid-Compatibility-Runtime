#!/usr/bin/env bash
# doctor.sh — Tool Health Check (brief §31). Text + machine-readable (--json).
# Layout-adaptive: works when committed INSIDE the repo (ROOT=repo) and when
# sitting beside it in the bootstrap tools dir (ROOT=project root).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$ROOT/root_registry.json" ]; then
  PROJ="$ROOT"                                    # committed in-repo layout
else
  PROJ="$ROOT/MiniAndroid-Compatibility-Runtime"   # external bootstrap layout
fi
# find_tool RELPATH — resolve a toolchain file across layouts:
#   ${MINITOOLS}/REL → ${ROOT}/tools/REL → ${ROOT}/REL → $(dirname ROOT)/tools/REL
find_tool() {
  local rel="$1" c
  if [ -n "${MINITOOLS:-}" ] && [ -e "$MINITOOLS/$rel" ]; then echo "$MINITOOLS/$rel"; return 0; fi
  for c in "$ROOT/tools/$rel" "$ROOT/$rel" "$(dirname "$ROOT")/tools/$rel"; do
    if [ -e "$c" ]; then echo "$c"; return 0; fi
  done
  return 1
}
AAPT2_BIN="${MINIAAPT2:-}"
if [ -z "$AAPT2_BIN" ] || [ ! -x "$AAPT2_BIN" ]; then
  AAPT2_BIN="$(find_tool aapt2/aapt2 || true)"
fi
if [ -z "$AAPT2_BIN" ]; then AAPT2_BIN="$(command -v aapt2 2>/dev/null || true)"; fi
JSON=""
[ "${1:-}" = "--json" ] && JSON=1
check() { # name path_or_cmd test_args
  local name="$1"; shift
  if command -v "$1" >/dev/null 2>&1; then
    echo "OK      $name $( "$@" --version 2>/dev/null | head -1 || true)"
    return 0
  fi
  echo "ABSENT  $name"
  return 1
}
items=()
add() { items+=("$1"); }
ver() { "$@" --version 2>/dev/null | head -1 || "$@" -version 2>&1 | head -1 || echo "?"; }

gpp_v=$(g++ --version | head -1)
gcc_ok=$?
java_v=$(java -version 2>&1 | head -1)
py_v=$(python3 --version)
git_v=$(git --version)
if [ -n "$AAPT2_BIN" ] && [ -x "$AAPT2_BIN" ]; then
  aapt2_v=$("$AAPT2_BIN" version 2>&1 | head -1); aapt2_st=OK
else
  aapt2_v=""; aapt2_st=ABSENT
fi
r8_p=$(find_tool d8/r8.jar || true);     r8_ok=$([ -n "$r8_p" ] && echo OK || echo ABSENT)
ecj_p=$(find_tool ecj/ecj.jar || true);  ecj_ok=$([ -n "$ecj_p" ] && echo OK || echo ABSENT)
stubs_p=$(find_tool android-34.jar || true); stubs_ok=$([ -n "$stubs_p" ] && echo OK || echo ABSENT)
make_v=$(make --version | head -1)
zip_ok=$(command -v zip >/dev/null && echo OK || echo ABSENT)
unzip_ok=$(command -v unzip >/dev/null && echo OK || echo ABSENT)
objdump_ok=$(command -v objdump >/dev/null && echo OK || echo ABSENT)
readelf_ok=$(command -v readelf >/dev/null && echo OK || echo ABSENT)
pil_ok=$(python3 -c "import PIL; print('OK', PIL.__version__)" 2>/dev/null || echo ABSENT)
bin_ok=$([ -x "$PROJ/miniandroid/build/miniandroid" ] && echo OK || echo ABSENT)
sqlite_ok=$(python3 -c "import sqlite3; print('OK')" 2>/dev/null || echo ABSENT)
reg_ok=$([ -f "$PROJ/root_registry.json" ] && echo OK || echo ABSENT)
java_ok=$(command -v java >/dev/null 2>&1 && echo OK || echo ABSENT)
py_ok=$(command -v python3 >/dev/null 2>&1 && echo OK || echo ABSENT)
make_ok=$(command -v make >/dev/null 2>&1 && echo OK || echo ABSENT)
git_ok=$(command -v git >/dev/null 2>&1 && echo OK || echo ABSENT)

out=$(cat <<EOF
compiler:g++:$( [ "$gcc_ok" = 0 ] && echo OK || echo ABSENT ):$gpp_v
java::${java_ok}:${java_v}
python::${py_ok}:${py_v}
make::${make_ok}:${make_v}
git_cli::${git_ok}:${git_v}
apk_tools:aapt2:${aapt2_st}:${aapt2_v}
dex_tools:r8.jar:${r8_ok}:
resource_tools:android-34.jar:${stubs_ok}:
java_compiler:ecj.jar:${ecj_ok}:
screenshot_pipeline:PIL:${pil_ok%% *}:
runtime_binary:build/miniandroid:${bin_ok}:
git::OK:${git_v}
zip::${zip_ok}:
unzip::${unzip_ok}:
objdump::${objdump_ok}:
readelf::${readelf_ok}:
sqlite3::${sqlite_ok}:
root_registry:root_registry.json:${reg_ok}:
EOF
)
if [ -n "$JSON" ]; then
  python3 - "$out" <<'PY'
import json, sys
rows = [l.split(":", 3) for l in sys.argv[1].splitlines() if l.strip()]
print(json.dumps({"doctor": [{"component": r[0], "tool": r[1] if len(r)>1 else "",
                             "status": r[2] if len(r)>2 else "?",
                             "version": r[3] if len(r)>3 else ""} for r in rows]}, indent=1))
PY
else
  echo "$out" | awk -F: '{printf "%-22s %-18s %-8s %s\n", $1, $2, $3, $4}'
fi
