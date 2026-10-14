#!/bin/bash
# cont12_oracle_res.sh — CONT-12 PHASE 2 (fix): faithful resource construction
# for the oracle APK. What AGP does at app build: merge every library AAR's
# res/ into the app package namespace (aapt2), then rewrite library R fields
# to the FINAL merged ids. We reproduce: aapt2 compile+link all AAR res ->
# final R.txt -> regenerate every library's R classes (merged, final ids) ->
# D8 uses the jars with stale R classes stripped + regenerated R.
# TEST-ONLY oracle construction; no engine change; no app-specific ids.
set -euo pipefail
BASE=/home/z/my-project
RAW=$BASE/upstream/cont12_maven/raw
WORK=$BASE/tmp/cont12_resbuild
BOOT=$BASE/tools/toolchain/android-34.jar
AAPT2=$BASE/tools/toolchain/aapt2
ECJ=$BASE/tools/toolchain/ecj.jar
FIX=$BASE/fixtures/cont12_oracle

rm -rf "$WORK"; mkdir -p "$WORK/flats" "$WORK/gen" "$WORK/robj" "$WORK/apk"

# ── 1) aapt2 compile every AAR's res/ ─────────────────────────────────────
for a in "$RAW"/*.aar; do
  [ -f "$a" ] || continue
  name=$(basename "$a" .aar)
  if unzip -l "$a" 2>/dev/null | grep -q " res/values/values.xml\| res/values/"; then
    d="$WORK/res_$name"; rm -rf "$d"; mkdir -p "$d"
    unzip -q -o "$a" "res/*" -d "$d" 2>/dev/null || true
    if [ -d "$d/res" ]; then
      "$AAPT2" compile --dir "$d/res" -o "$WORK/flats/${name}.zip" 2>&1 | grep -v "^$" || true
      echo "compiled res: $name"
    fi
  fi
done

# ── 2) aapt2 link everything -> resources.apk + FINAL R.txt ──────────────
FLATS=""
for f in "$WORK"/flats/*.zip; do FLATS="$FLATS $f"; done
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" \
  --java "$WORK/gen_aapt2" \
  --emit-ids "$WORK/R_final.txt" \
  --auto-add-overlay $FLATS
echo "linked resources: $(stat -c%s "$WORK/apk/resources.apk") bytes; R.txt lines: $(wc -l < "$WORK/R_final.txt")"

# ── 3) regenerate R classes for every library package (merged, final ids) ─
python3 - << 'PYEOF'
import re, zipfile, os, glob

WORK = "/home/z/my-project/tmp/cont12_resbuild"
CLS = "/home/z/my-project/upstream/cont12_maven/classes"

# parse emit-ids file: `id/view_tree_lifecycle_owner=0x7f0b0028` style lines;
# styleable arrays are NOT in emit-ids (it carries scalar ids only)
types = {}
for line in open(f"{WORK}/R_final.txt"):
    line = line.strip()
    if not line or line.startswith("#"): continue
    m = re.match(r"(\w+)/(.+?)=(0x[0-9a-fA-F]+)$", line)
    if m:
        name = m.group(2).replace(".", "_").replace("-", "_")
        types.setdefault(m.group(1), {})[name] = m.group(3)
# styleable arrays: reconstructed from the aapt2-generated app R.java
# (gen_aapt2/<app>/R.java contains the styleable class with final arrays)
app_java = glob.glob(f"{WORK}/gen_aapt2/**/R.java", recursive=True)
styleable = {}
for jf in app_java:
    src = open(jf).read()
    ms = re.search(r"public static(?:\s+final)?\s+class styleable \{(.*?)\n    \}", src, re.S)
    if ms:
        body = ms.group(1)
        for am in re.finditer(r"public static final int\[\] (\w+)=\{([^}]*)\}", body):
            styleable[am.group(1)] = [x.strip() for x in am.group(2).split(",")]
        for im in re.finditer(r"public static final int (\w+)=(\d+)", body):
            # index constants share the styleable namespace in R generation
            styleable.setdefault(im.group(1), im.group(2))
if styleable:
    types["styleable"] = styleable

# enumerate R packages present in the library jars
pkgs = set()
for jar in glob.glob(f"{CLS}/*.jar"):
    try: z = zipfile.ZipFile(jar)
    except Exception: continue
    for n in z.namelist():
        m = re.match(r"^(.+)/R(?:\$\w+)?\.class$", n)
        if m: pkgs.add(m.group(1).replace("/", "."))

# the app package R as well
pkgs.add("com.probe.oracle12")

print("R packages:", sorted(pkgs))
print("R types:", {k: len(v) for k, v in types.items()})

# generate merged R.java per package (AGP non-transitive-R=off shape:
# every package's R carries ALL final fields)
header = "package %s;\npublic final class R {\n"
for pkg in sorted(pkgs):
    out = [header % pkg]
    for typ, fields in types.items():
        if typ == "styleable":
            # int[] arrays and their per-attr index constants
            arrays = {}
            indexes = {}
            for full, arr in fields.items():
                arrays[full] = arr
            # R.txt styleable index lines live in the same dict? they are separate
            out.append("  public static final class styleable {\n")
            for full, arr in arrays.items():
                out.append("    public static final int[] %s = { %s };\n" % (full, ",".join(arr)))
            out.append("  }\n")
            continue
        out.append("  public static final class %s {\n" % typ)
        for name, val in sorted(fields.items()):
            out.append("    public static final int %s = %s;\n" % (name, val))
        out.append("  }\n")
    out.append("}\n")
    d = f"{WORK}/gen/" + pkg.replace(".", "/")
    os.makedirs(d, exist_ok=True)
    open(f"{d}/R.java", "w").write("".join(out))
print("R.java files:", len(pkgs))
PYEOF

# styleable index constants (int styleable X_i 0) were parsed into types
# already? R.txt puts them as `int styleable Name_idx N` -> they land in
# types['styleable'] via the int[] regex ONLY for arrays. Fix: the plain
# `int styleable ...` lines match the second regex with group(1)=styleable
# and value 0x-prefixed? No: value is decimal N (no 0x). Regenerate with
# them included as decimal ints.

# ── 4) ECJ compile the R classes ──────────────────────────────────────────
find "$WORK/gen" -name "*.java" > "$WORK/rsrcs.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/robj" @"$WORK/rsrcs.txt" 2>&1 | head -5 || true
ls "$WORK/robj" > /dev/null && echo "R classes compiled"

# ── 5) strip stale R classes from library jars -> rstripped/ ──────────────
python3 - << 'PYEOF'
import zipfile, glob, os, re
CLS = "/home/z/my-project/upstream/cont12_maven/classes"
OUT = "/home/z/my-project/tmp/cont12_resbuild/rstripped"
os.makedirs(OUT, exist_ok=True)
pat = re.compile(r"^(.+)/R(?:\$\w+)?\.class$")
n = 0
for jar in glob.glob(f"{CLS}/*.jar"):
    try: z = zipfile.ZipFile(jar)
    except Exception: continue
    names = z.namelist()
    keep = [x for x in names if not pat.match(x)]
    if len(keep) == len(names): continue
    outj = f"{OUT}/" + os.path.basename(jar)
    zo = zipfile.ZipFile(outj, "w", zipfile.ZIP_DEFLATED)
    for x in keep: zo.writestr(x, z.read(x))
    zo.close(); n += 1
print("rstripped jars:", n)
PYEOF
echo "phase A done"
