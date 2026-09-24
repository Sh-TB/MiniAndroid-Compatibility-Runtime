#!/usr/bin/env python3
"""S94 Phase A: verify identity of every candidate repository via git ls-remote.

No GitHub API (quota exhausted). `git ls-remote --symref URL HEAD` returns the
default branch name + HEAD commit SHA without authentication. This is genuine
identity evidence: a repo that does not exist fails here.

Output:
  run/s94/source_mining/repositories.json   - full verified records
  run/s94/source_mining/phase_a_log.txt     - human-readable log
"""
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from s94_repo_list import REPOS

OUT = Path("/home/z/my-project/run/s94/source_mining")
TIMEOUT = 30
ATTEMPTS = 2


def ls_remote(repo: str):
    """Return (default_branch, head_sha) or raise."""
    url = f"https://github.com/{repo}.git"
    for attempt in range(1, ATTEMPTS + 1):
        try:
            r = subprocess.run(
                ["git", "ls-remote", "--symref", url, "HEAD"],
                capture_output=True, text=True, timeout=TIMEOUT,
            )
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip().splitlines()[-1][:160] if r.stderr.strip() else f"rc={r.returncode}")
            branch, sha = None, None
            for line in r.stdout.splitlines():
                if line.startswith("ref:") and line.rstrip().endswith("HEAD"):
                    branch = line[len("ref:"):].split("\t")[0].strip()
                elif "\tHEAD" in line:
                    sha = line.split("\t")[0].strip()
            if not sha:
                raise RuntimeError("no HEAD sha in output")
            return branch or "unknown", sha
        except Exception as e:
            if attempt == ATTEMPTS:
                raise
            time.sleep(1.5 * attempt)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    t0 = time.time()

    def work(item):
        idx, (repo, families, priority, rel, seed, note) = item
        rec = {
            "id": f"GFX-SRC-{idx+1:03d}",
            "repository": repo,
            "url": f"https://github.com/{repo}",
            "families": families.split(","),
            "priority": priority,
            "relationship": rel,
            "seed_entry": seed,
            "directive_note": note,
        }
        try:
            branch, sha = ls_remote(repo)
            rec.update({
                "status": "VERIFIED",
                "default_branch": branch,
                "head_sha": sha,
                "verified_via": "git ls-remote --symref",
            })
        except Exception as e:
            rec.update({"status": "NOT_VERIFIED", "error": str(e)[:200]})
        rec["last_verified"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return rec

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(work, it): it for it in enumerate(REPOS)}
        for fut in as_completed(futs):
            records.append(fut.result())
            if len(records) % 20 == 0:
                print(f"  ... {len(records)}/{len(REPOS)}", flush=True)

    records.sort(key=lambda r: r["id"])
    ok = [r for r in records if r["status"] == "VERIFIED"]
    bad = [r for r in records if r["status"] != "VERIFIED"]

    doc = {
        "campaign": "S94 GRAPHICS SOURCE LIBRARY",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verification_method": "git ls-remote --symref https://github.com/<owner>/<repo>.git HEAD (no GitHub API used)",
        "candidates": len(REPOS),
        "verified": len(ok),
        "not_verified": len(bad),
        "distinct_verified_repositories": len(ok),
        "repositories": records,
    }
    (OUT / "repositories.json").write_text(json.dumps(doc, indent=1))
    log = []
    for r in records:
        if r["status"] == "VERIFIED":
            log.append(f"{r['id']} {r['repository']:52s} {r['default_branch']:8s} {r['head_sha'][:12]} [{r['relationship'][:48]}]")
        else:
            log.append(f"{r['id']} {r['repository']:52s} !! {r['error']}")
    (OUT / "phase_a_log.txt").write_text("\n".join(log) + "\n")
    print(f"verified {len(ok)}/{len(REPOS)} in {time.time()-t0:.0f}s")
    for r in bad:
        print("  NOT_VERIFIED:", r["repository"], "->", r["error"])
    return 0 if len(ok) >= 100 else 1


if __name__ == "__main__":
    sys.exit(main())
