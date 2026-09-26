#!/usr/bin/env python3
"""S107 fresh trace — re-verify the 4 canonical titles on current HEAD (3 runs each).
Records status, error count, exception-set hash, screenshot SHA per run."""
import hashlib, json, re, subprocess, sys
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid"
OUT = BASE / "evidence/s107_fresh"

APKS = {
    "dooz": BASE / "upload/canonical_apks/io.github.yamin8000.dooz_23.apk",
    "dooz_toplevel": BASE / "upload/canonical_apks/dooz_23_toplevel.apk",
    "ballbreak": BASE / "upload/s105_apks/de.georgsieber.ballbreak_10.apk",
    "solitaire": BASE / "evidence/s106_fresh/apks/solitaire_vc20260804.apk" if (BASE / "evidence/s106_fresh/apks/solitaire_vc20260804.apk").exists() else None,
    "mykanji": None,
    "unote": BASE / "upload/canonical_apks/app.varlorg.unote_30.apk",
    "bouncy": BASE / "upload/canonical_apks/bouncy.apk",
}

# locate solitaire/mykanji from s106 evidence dir
apk_dir = BASE / "evidence/s106_fresh/apks"
if apk_dir.exists():
    for f in sorted(apk_dir.iterdir()):
        n = f.name.lower()
        if "solitaire" in n and APKS["solitaire"] is None:
            APKS["solitaire"] = f
        if "mykanji" in n and APKS["mykanji"] is None:
            APKS["mykanji"] = f

def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]

results = {}
for name, apk in APKS.items():
    if apk is None or not Path(apk).exists():
        print(f"[SKIP] {name}: APK not found")
        continue
    runs = []
    for i in (1, 2, 3):
        outdir = OUT / f"{name}_run{i}"
        outdir.mkdir(parents=True, exist_ok=True)
        log = outdir / "run.log"
        try:
            with open(log, "w") as f:
                rc = subprocess.run(
                    [str(BIN), "run", str(apk), "-o", str(outdir)],
                    stdout=f, stderr=subprocess.STDOUT, timeout=280,
                ).returncode
        except subprocess.TimeoutExpired:
            rc = -1
            log.write_text("TIMEOUT 280s")
        text = log.read_text(errors="ignore")
        m = re.search(r"Errors[:|]\s*(\d+)", text)
        errors = int(m.group(1)) if m else -1
        m2 = re.search(r"Status[:|]?\s*\**([A-Z ]+)", text)
        status = m2.group(1).strip() if m2 else "?"
        # exception-set hash: sorted unique [SYNTH-EXC] lines
        excs = sorted(set(re.findall(r"\[SYNTH-EXC\][^\n]*", text)))
        exc_hash = sha("\n".join(excs).encode()) if excs else "none"
        shot = outdir / "screenshot.png"
        ssha = sha(shot.read_bytes()) if shot.exists() else "NO-SHOT"
        runs.append({"rc": rc, "status": status, "errors": errors,
                     "exc_hash": exc_hash, "shot_sha": ssha})
        print(f"{name} run{i}: rc={rc} status={status} errors={errors} exc={exc_hash} shot={ssha}")
    results[name] = runs

(OUT / "fresh_trace.json").write_text(json.dumps(results, indent=2))
print("\nSUMMARY:")
for name, runs in results.items():
    e = {r["errors"] for r in runs}
    s = {r["shot_sha"] for r in runs}
    print(f"  {name}: errors={e} shot_deterministic={'YES' if len(s)==1 else 'NO'}")
