#!/bin/bash
# cont12_oracle_res2.sh — CONT-12 PHASE 2 (faithful artifact construction, v2).
# What AGP does at app build that raw AAR dexing lacks:
#   (a) merge every library AAR's res/ into the app package namespace (aapt2);
#   (b) generate R classes (per library package) with the FINAL merged ids.
# AAR classes.jar files carry NO R classes, so library code's
# `sget androidx/lifecycle/runtime/R$id.view_tree_lifecycle_owner` needs
# generated R classes, else the engine resolves a nonexistent field.
# Output: $WORK/rclasses.jar (generated R classes) + full resources.apk.
set -uo pipefail
BASE=/home/z/my-project
RAW=$BASE/upstream/cont12_maven/raw
WORK=$BASE/tmp/cont12_resbuild
BOOT=$BASE/tools/toolchain/android-34.jar
AAPT2=$BASE/tools/toolchain/aapt2
ECJ=$BASE/tools/toolchain/ecj.jar
FIX=$BASE/fixtures/cont12_oracle

rm -rf "$WORK"; mkdir -p "$WORK/flats" "$WORK/gen" "$WORK/gen_aapt2" "$WORK/robj" "$WORK/apk"

# ── 1) aapt2 compile EVERY AAR res dir (match anywhere in listing) ────────
for a in "$RAW"/*.aar; do
  [ -f "$a" ] || continue
  name=$(basename "$a" .aar)
  listing=$(unzip -l "$a" 2>/dev/null)
  if echo "$listing" | grep -q "res/values/"; then
    d="$WORK/res_$name"; rm -rf "$d"; mkdir -p "$d"
    unzip -q -o "$a" "res/*" -d "$d" 2>/dev/null || true
    if [ -d "$d/res" ]; then
      if "$AAPT2" compile --dir "$d/res" -o "$WORK/flats/${name}.zip" > "$WORK/flats/${name}.log" 2>&1; then
        echo "compiled res: $name"
      else
        echo "COMPILE-FAIL: $name (see log)"
      fi
    fi
  fi
done

# ── 2) aapt2 link everything -> resources.apk + emit-ids + app R.java ─────
FLATS=""
for f in "$WORK"/flats/*.zip; do FLATS="$FLATS $f"; done
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" \
  --java "$WORK/gen_aapt2" \
  --emit-ids "$WORK/R_final.txt" \
  --auto-add-overlay $FLATS 2>&1 | tail -3
echo "linked resources: $(stat -c%s "$WORK/apk/resources.apk") bytes; ids emitted: $(grep -c . "$WORK/R_final.txt")"

# ── 3) generate merged R classes for every R package the dex references ───
python3 - << 'PYEOF'
import re, zipfile, os, glob

WORK = "/home/z/my-project/tmp/cont12_resbuild"
DEX1 = "/home/z/my-project/run/w8/oracle12.apk"

# collect the R packages actually referenced in the oracle dexes
rpkgs = set()
z = zipfile.ZipFile(DEX1)
for dex in [n for n in z.namelist() if n.endswith(".dex")]:
    d = z.read(dex)
    for m in re.finditer(rb"L([a-zA-Z0-9_/]+/R)(\$\w+)?;", d):
        pkg_with_r = m.group(1).decode()          # e.g. androidx/lifecycle/runtime/R
        pkg = pkg_with_r[:-2].replace("/", ".")   # strip trailing /R
        if not pkg.endswith(".R"):                # "*.R" packages are never legit
            rpkgs.add(pkg)
rpkgs.add("com.probe.oracle12")
print("R packages referenced:", len(rpkgs), sorted(rpkgs)[:12], "...")

# scalar ids from emit-ids
types = {}
for line in open(f"{WORK}/R_final.txt"):
    line = line.strip()
    if not line or line.startswith("#"): continue
    m = re.match(r"([\w.]+):(\w+)/(.+?) = (0x[0-9a-fA-F]+)$", line)
    if m:
        types.setdefault(m.group(2), {})[m.group(3).replace(".", "_").replace("-", "_")] = m.group(4)
        continue
    m = re.match(r"([\w.]+)/(.+?)=(0x[0-9a-fA-F]+)$", line)
    if m:
        name = m.group(2).replace(".", "_").replace("-", "_")
        types.setdefault(m.group(1), {})[name] = m.group(3)

# styleables from the aapt2-generated app R.java
styleable = {}
for jf in glob.glob(f"{WORK}/gen_aapt2/**/R.java", recursive=True):
    src = open(jf).read()
    ms = re.search(r"public static final class styleable \{(.*?)\n    \}", src, re.S)
    if ms:
        body = ms.group(1)
        for am in re.finditer(r"public static final int\[\] (\w+)=\{([^}]*)\}", body):
            styleable[am.group(1)] = [x.strip() for x in am.group(2).split(",")]
        for im in re.finditer(r"public static final int (\w+)=(\d+)", body):
            styleable.setdefault(im.group(1), im.group(2))
if styleable:
    types["styleable"] = styleable
print("types:", {k: len(v) for k, v in sorted(types.items())})

# javac field-name sanitizer (R names are already sanitized by aapt2's
# --java output, so apply the same transform defensively)
def jname(n): return n.replace(".", "_").replace("-", "_")

for pkg in sorted(rpkgs):
    out = ["package %s;\npublic final class R {\n" % pkg]
    for typ in sorted(types):
        out.append("  public static final class %s {\n" % typ)
        for name in sorted(types[typ]):
            val = types[typ][name]
            if isinstance(val, list):
                out.append("    public static final int[] %s = { %s };\n" % (jname(name), ",".join(val)))
            else:
                out.append("    public static final int %s = %s;\n" % (jname(name), val))
        out.append("  }\n")
    out.append("}\n")
    d = f"{WORK}/gen/" + pkg.replace(".", "/")
    os.makedirs(d, exist_ok=True)
    open(f"{d}/R.java", "w").write("".join(out))
print("R.java files written:", len(rpkgs))
PYEOF

# ── 4) ECJ compile the generated R classes ────────────────────────────────
find "$WORK/gen" -name "*.java" > "$WORK/rsrcs.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/robj" @"$WORK/rsrcs.txt" 2>&1 | grep -vE "^$|^\d+\. " | head -5
RCOUNT=$(find "$WORK/robj" -name "*.class" | wc -l)
echo "R classes compiled: $RCOUNT"
cd "$WORK/robj" && zip -q -r "$WORK/rclasses.jar" . && cd "$BASE"
echo "rclasses.jar: $(sha256sum "$WORK/rclasses.jar" | cut -c1-16) ($(stat -c%s "$WORK/rclasses.jar") bytes)"
# sanity: the id that gates composition must be present with a REAL value
python3 - << 'PYEOF'
ids = open("/home/z/my-project/tmp/cont12_resbuild/R_final.txt").read()
for probe in ["view_tree_lifecycle_owner", "view_tree_view_model_store_owner",
              "view_tree_saved_state_registry_owner"]:
    hit = [l for l in ids.splitlines() if probe in l]
    print(("OK  " if hit else "MISS"), probe, hit[0] if hit else "")
PYEOF
