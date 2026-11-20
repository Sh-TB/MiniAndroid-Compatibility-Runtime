#!/usr/bin/env python3
"""S15-c: update ledger — AUD-57 census correction, AUD-53 re-verification,
new AUD-58 row (#626 wave10 superseded-in-full classification), re-validate,
sync to download/audit_v2/."""
import csv, subprocess, shutil, os

AUD = "/home/z/my-project/miniandroid/evidence/audit/ACHIEVEMENT_LEDGER.csv"
DL = "/home/z/my-project/download/audit_v2"

rows = list(csv.DictReader(open(AUD, newline="", encoding="utf-8")))
hit57 = hit53 = hit58 = 0
for r in rows:
    if r["ID"] == "AUD-57":
        hit57 += 1
        r["Evidence"] = ("branch census 2026-11-20 + S15 ls-remote re-run (same day): merged s241-law-waves/s237/s238/s239/s240; "
                         "S15 CORRECTION — wave10/dalvik-accel (= refs/pull/626/head), audit/s236, audit/m16-litehtml, "
                         "cont24/skeleton-light-experiment are NOW PRESENT on the remote and fetched into the audit clone; "
                         "wave9/dev-so-clean confirmed MERGED (PR #625 merged=True, base=main, 1e5c8fb9 in main ancestry); "
                         "layout-geometry-001 still ABSENT (RC-12/AUD-53 unrecoverability re-confirmed)")
        r["Next action"] = "census corrected; per-line dispositions in AUD-58"
    elif r["ID"] == "AUD-53":
        hit53 += 1
        r["Next action"] = (r["Next action"] + " | S15 re-verification 2026-11-20: layout-geometry-001 absent from "
                            "git ls-remote --heads — unrecoverability re-confirmed from the remote side")
    elif r["ID"] == "AUD-58":
        hit58 += 1  # already present (rerun) — overwrite below

upd58 = {
 "ID": "AUD-58",
 "Issue/Coder": "#626 PR / S15",
 "Exact claim": "PR #626 (wave10/dalvik-accel, 15 commits stacked on merged wave9/PR #625) carries dev-so speed profiles and W11-W20 laws/fixes not yet in main",
 "Source inspected": "git ls-remote + fetch of all four formerly-absent lines; PR API states (#625 merged=True base=main, #626 OPEN base=wave9/dev-so-clean head=671d2577); 3-dot delta 153 files +73824/-54783; per-piece content checks logged in evidence/audit/RAW_LOGS/s15_branch_classification_2026-11-20.md",
 "Test executed": "F-NEW id matrix over main src (ALL 13 ids 709-723b present: 709x3 710x6 711 712x2 713x4 714 717 718 719x2 721 722 723 723b); F-NEW-710 by-value signature verbatim at dalvik_engine_invoke.cpp:187-191; 3/3 W20 P2 fixes in main (cstdint in adapter_scrap_bin.h; 0 android_shadows.h refs in dalvik_engine_tail.cpp 599L; -include DEV_SO .d block Makefile:817-820); zero-missing-file check: EVERY branch src/tests path exists in main (git cat-file -e loop, 0 MISSING-IN-MAIN); s236_port_laws_test present in main + registered Makefile TEST_LAW:531; P0-split domain TUs + docs/dev-so-architecture.md (93L) in main",
 "Runtime verified": "n/a — content classification; no tree change (the in-main equivalents already carry the 49/49 battery gates)",
 "Verdict": "SUPERSEDED",
 "Evidence level": "SOURCE-INSPECTED",
 "Evidence": "evidence/audit/RAW_LOGS/s15_branch_classification_2026-11-20.md",
 "Integration status": "INTEGRATED",
 "Next action": "NO rebase, NO cherry-pick — every code/law/fix piece is in main via the W22-W24 direct landings; rebasing would resurrect duplicate implementations against main's further-evolved P0/header-split architecture; recommend closing PR #626 with the classification comment (owner decision); audit/s236 remainder = raw evidence only; m16-litehtml + cont24 stay branch-only, now reachable",
}

hit = 0
for r in rows:
    if r["ID"] == "AUD-58":
        for k, v in upd58.items():
            r[k] = v
        hit += 1
if hit == 0:
    rows.append(upd58)
elif hit > 1:
    raise SystemExit("duplicate AUD-58 rows before write")

fields = list(rows[0].keys())
with open(AUD, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(f"ledger updated: AUD-57 corrected ({hit57}), AUD-53 re-verified ({hit53}), AUD-58 {'overwritten' if hit58 else 'appended'}; total rows {len(rows)}")

r = subprocess.run(["python3", "/home/z/my-project/scripts/validate_ledger.py"], capture_output=True, text=True)
print("\n".join(r.stdout.splitlines()[-4:]))
if "OVERALL: PASS" not in r.stdout:
    raise SystemExit("validator FAILED")

os.makedirs(DL, exist_ok=True)
shutil.copy(AUD, f"{DL}/ACHIEVEMENT_LEDGER.csv")
shutil.copy("/home/z/my-project/miniandroid/evidence/audit/LEDGER_VALIDATION_REPORT.md", f"{DL}/LEDGER_VALIDATION_REPORT.md")
print("synced to download/audit_v2/")
