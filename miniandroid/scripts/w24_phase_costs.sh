#!/usr/bin/env bash
# w24_phase_costs.sh — COMPILER_PHASE_COSTS.csv via gcc -ftime-report on the
# EXACT command lines from the -j1 FASTPROFILE log (perfect flag parity).
# Top-12 heavy TUs + 4 representative small TUs. -ftime-report inflates wall
# ~10-15%: use for phase STRUCTURE (shares), not absolute wall.
set -x
cd /home/z/my-project/miniandroid
EV=evidence/w24
LOG=$EV/RAW_LOGS/w24_fastprofile_j1.log
OUTCSV=$EV/COMPILER_PHASE_COSTS.csv
mkdir -p $EV/RAW_LOGS/ftime

# TUs to profile: top-12 + representative small ones
TUS=$(python3 - <<'EOF'
import csv
rows=[r for r in csv.reader(open('evidence/w24/TU_COST_RANKING.csv')) if r and r[0].isdigit()]
heavy=[r[1] for r in rows[:12]]
small=[r[1] for r in rows if 2.0<=float(r[2])<=5.0][:4]
print("\n".join(heavy+small))
EOF
)

echo "tu,phase_or_pass,user_s,sys_s,wall_s,mem" > $OUTCSV
for src in $TUS; do
  tag=$(basename $src .cpp)
  # exact original command line for this TU from the log
  line=$(grep -m1 " -c -o .*$src" $LOG | sed 's/^ *[0-9.]* //')
  # append -ftime-report right after 'g++' (note: BRE 'g\+\+ ' never matches)
  cmd=$(echo "$line" | sed 's/^g[+][+] /g++ -ftime-report /')
  out=$EV/RAW_LOGS/ftime/ft_$tag.txt
  $cmd > /tmp/w24ft_obj.o 2> $out
  rc=$?
  echo "== $tag rc=$rc" >> $out
  # extract phases + top passes into CSV (GCC timevar cols: user, sys, wall, mem)
  python3 - "$tag" "$out" "$OUTCSV" <<'PYEOF'
import re, sys
tag, path, outcsv = sys.argv[1], sys.argv[2], sys.argv[3]
want_phase = ("phase parsing", "phase lang. deferred", "phase opt and generate",
              "phase last asm")
want_pass = ("template instantiation", "symout", "integration", "garbage collection",
             "callgraph functions expansion", "callgraph ipa passes",
             "var-tracking dataflow", "var-tracking emit", "variable tracking",
             "tree PTA", "integrated RA")
f = open(outcsv, "a")
pct = re.compile(r"\s*(\S.*?)\s*:\s*([0-9.]+) \(\s*\d+%\)\s+([0-9.]+) \(\s*\d+%\)\s+([0-9.]+) \(\s*\d+%\)\s+([0-9.]+[kMG]?)\s*\(")
tot = re.compile(r"\s*TOTAL\s*:\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+[kMG]?)")
for line in open(path, errors="replace"):
    m = pct.match(line)
    if m:
        name = m.group(1)
        if name in want_phase or name in want_pass:
            f.write(f"{tag},{name},{m.group(2)},{m.group(3)},{m.group(4)},{m.group(5)}\n")
        continue
    m = tot.match(line)
    if m:
        f.write(f"{tag},TOTAL,{m.group(1)},{m.group(2)},{m.group(3)},{m.group(4)}\n")
f.close()
PYEOF
done
echo PHASE_COSTS_DONE
