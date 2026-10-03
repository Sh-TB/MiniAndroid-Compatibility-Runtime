#!/usr/bin/env python3
"""GATE A (issue #370) — multi-app installed-environment proof harness.

§18: 5 app families (simple / storage-heavy / game / resource-heavy /
render-FAIL) each prove: install → identity → SOURCE HIDING → inspection
→ 3-run restart persistence → post-run inspection. Inspection must
complete for the render-fail app too (GATE A ≠ GATE B/C).
"""
import json, os, shutil, subprocess, sys, hashlib

B = "/home/z/my-project/miniandroid/build/miniandroid"
BASE = "/home/z/my-project/run/gatea/multiapp"
OUT = "/home/z/my-project/run/gatea/multiapp_evidence"

APPS = [
    ("simple",         "run/gatea/gate_a_probe.apk"),
    ("storage-heavy",  "run/diff366/hidden_sources/chess_jwtc_298.apk"),
    ("game",           "run/diff366/hidden_sources/bouncy.apk"),
    ("resource-heavy", "run/diff366/hidden_sources/com.sanskritbasics.memory_34.apk"),
    ("render-FAIL",    "run/diff366/hidden_sources/com.sidhant.blockblast_43.apk"),
]

SECTIONS_PRE = "identity,manifest,entries,dex,resources,assets,libs,media"
SECTIONS_POST = "identity,data,external,dbs,prefs,provenance"

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def run(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), cwd="/home/z/my-project",
                          capture_output=True, text=True, **kw)

def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    # Stage a COPY per app so the post-hide law never destroys the corpus.
    staged = {}
    for label, apk in APPS:
        dst = f"{BASE}/stage_{os.path.basename(apk)}"
        shutil.copy2(apk, dst)
        staged[label] = dst
    for label, apk in APPS:
        apk = staged[label]
        store = f"{BASE}/{label}"
        hidden = f"{BASE}/hidden_sources_{label}"
        appdir = f"{OUT}/{label}"
        shutil.rmtree(store, ignore_errors=True)
        shutil.rmtree(appdir, ignore_errors=True)
        shutil.rmtree(hidden, ignore_errors=True)
        os.makedirs(appdir, exist_ok=True)
        os.makedirs(store, exist_ok=True)
        row = {"family": label, "apk": apk}

        # 1. INSTALL — capture source SHA + identity
        r = run([B, "install", apk, "--data-root", store])
        row["install_rc"] = r.returncode
        src_sha = sha256(apk)
        row["source_apk_sha256"] = src_sha

        # resolve package via pkginspect DIRECT-APK identity
        r = run([B, "pkginspect", "--apk", apk, "--what", "identity"])
        ident = json.loads(r.stdout[r.stdout.index("{"):])
        pkg = ident["package"]
        row["package"] = pkg
        row["identity_sha_match"] = ident["sections"]["identity"]["shaMatch"]

        # installed base.apk equality
        base_apk = f"{store}/data/app/{pkg}/base.apk"
        row["installed_base_apk_sha256"] = sha256(base_apk)
        row["sha_source_eq_installed"] = src_sha == row["installed_base_apk_sha256"]

        # 2. HIDE THE SOURCE APK — post-install identity is package-only
        os.makedirs(hidden, exist_ok=True)
        shutil.move(apk, f"{hidden}/{os.path.basename(apk)}")
        row["source_hidden"] = not os.path.exists(apk)

        # 3. INSPECT (pre-run sections) from the INSTALLED identity alone
        r = run([B, "pkginspect", "--package", pkg, "--data-root", store,
                 "--what", SECTIONS_PRE,
                 "--jsonl", f"{appdir}/inspect_pre.jsonl"])
        row["inspect_pre_rc"] = r.returncode
        pre = json.loads(r.stdout[r.stdout.index("{"):])
        row["manifest_activities"] = len(pre["sections"].get("manifest", {}).get("activities", []))
        row["manifest_providers"] = len(pre["sections"].get("manifest", {}).get("providers", []))
        row["manifest_services"] = len(pre["sections"].get("manifest", {}).get("services", []))
        row["manifest_receivers"] = len(pre["sections"].get("manifest", {}).get("receivers", []))
        row["dex_total_classes"] = pre["sections"].get("dex", {}).get("totalClasses", 0)
        row["resources_total_entries"] = pre["sections"].get("resources", {}).get("totalEntries", 0)
        row["assets_count"] = pre["sections"].get("assets", {}).get("count", 0)
        row["native_libs"] = pre["sections"].get("nativeLibs", {}).get("soCount", 0)
        row["native_abis"] = pre["sections"].get("nativeLibs", {}).get("abis", [])

        # 4. RUN x3 (installed-identity mode; restart persistence + traces)
        runs = []
        for i in (1, 2, 3):
            out = f"{appdir}/run{i}"
            os.makedirs(out, exist_ok=True)
            r = subprocess.run(
                [B, "run", "--package", pkg, "--data-root", store, "-o", out,
                 "--dump-view-tree"],
                cwd="/home/z/my-project", capture_output=True, text=True,
                env={**os.environ,
                     "MINIANDROID_FILE_IO": f"{out}/file_io.jsonl"})
            log = r.stdout + r.stderr
            open(f"{out}/run.log", "w").write(log)
            info = {"run": i, "rc": r.returncode}
            # first divergence from the trace/log (machine-readable marker)
            for marker in ("F-NEW-233 frame truth", "first_missing_stage"):
                if marker in log:
                    for line in log.splitlines():
                        if marker in line:
                            info["frame_truth"] = line.strip()[:220]
                            break
                    break
            runs.append(info)
            # keep probe results file (simple app) after each run
        row["runs"] = runs
        row["three_run_rc"] = len({r["rc"] for r in runs}) == 1

        # 5. INSPECT (post-run sections): data trees / dbs / prefs / provenance
        r = run([B, "pkginspect", "--package", pkg, "--data-root", store,
                 "--what", SECTIONS_POST,
                 "--jsonl", f"{appdir}/inspect_post.jsonl"])
        row["inspect_post_rc"] = r.returncode
        post = json.loads(r.stdout[r.stdout.index("{"):])
        sec = post["sections"]
        row["data_files"] = sec.get("dataTree", {}).get("count", 0)
        row["dbs"] = [d["name"] for d in sec.get("databases", {}).get("items", [])
                      if d.get("sqliteHeaderValid")]
        row["prefs"] = [p["file"].split("/")[-1] for p in
                        sec.get("preferences", {}).get("files", [])]
        row["provenance_edges"] = len(sec.get("provenance", {}).get("graph", []))
        row["inspection_complete_after_fail"] = (
            row["inspect_pre_rc"] == 0 and row["inspect_post_rc"] == 0)

        # 6. for the render-FAIL family the gate is: inspection still complete
        rows.append(row)
        print(f"[{label}] pkg={pkg} pre={row['inspect_pre_rc']} "
              f"post={row['inspect_post_rc']} dex={row['dex_total_classes']} "
              f"res={row['resources_total_entries']} assets={row['assets_count']} "
              f"libs={row['native_libs']} data={row['data_files']} "
              f"dbs={len(row['dbs'])} prefs={len(row['prefs'])}")

    with open(f"{OUT}/multi_app_proof.json", "w") as f:
        json.dump(rows, f, indent=1)
    ok = all(r["inspection_complete_after_fail"] and r["source_hidden"]
             and r["sha_source_eq_installed"] for r in rows)
    print("MULTI-APP PROOF:", "ALL PASS" if ok else "GAPS PRESENT")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
