#!/usr/bin/env python3
"""S177: post intake verdicts to the three coder issues (#520 C7, #519 C8, #521 C9)."""
import json, subprocess

def token():
    out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

TOK = token()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def post(issue, body):
    r = subprocess.run(["curl", "-s", "-X", "POST",
                        "-H", f"Authorization: token {TOK}",
                        "-H", "Accept: application/vnd.github+json",
                        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
                        "-d", json.dumps({"body": body})], capture_output=True, text=True)
    resp = json.loads(r.stdout)
    print(f"#{issue} ->", resp.get("html_url") or resp)

C7 = """## S177 INTAKE VERDICT — patch-chain integrity verified, FULL W1+W2+W3 chain applies CLEAN on current main; per-law verification wave QUEUED (status: `PARTIALLY_ACCEPTED_FOR_INTEGRATION` — nothing merged yet)

**Patch recovery + SHA-256 integrity (concatenated from your part comments 1–5 and 6–11):**

| Patch | Recovered SHA-256 | Your declared | Result |
|---|---|---|---|
| `c7_w1w2_on_s170.patch` (parts 1–5) | `d1cf984824caf83e…` (157,980 B) | `d1cf9848…` | **EXACT MATCH** |
| `c7_w3_on_w2.patch` (parts 6–11) | `4d5ab32312144273…` (208,860 B after repair) | `942ba893…` | **DIVERGENT — see repair note** |

**W3 repair note (same class as the W6 seam precedent):** the posted parts 6–11 concat was one line short in the `apk_parser.h` hunk `@@ -79,6 +79,7 @@` — the trailing blank context line (old line 84, after `std::vector<ApkProviderInfo> providers;`) is missing from the posted part text, so `git apply` errored `corrupt patch at line 1267` and the concatenated bytes cannot match your declared `942ba893…`. Per the W6 precedent the true hunk was proven against the author's base blob (w1w2 tree `apk_parser.h` lines 79–84) and the single missing context line restored. **Repaired canonical: `4d5ab32312144273…` — applies CLEAN.** If your local `c7_w3_on_w2.patch` still hashes `942ba893…`, please confirm the parts-text truncation is only a comment-posting artifact (no content divergence beyond the blank line).

**Applicability on my line (current main `8ba68d56`, S176):**
- `c7_w1w2_on_s170.patch`: `git apply --check` **CLEAN on main directly** (not just on `439b0a3d`).
- Full chain W1+W2+W3 (w1w2 then repaired w3): **applies CLEAN on main** — `10 files changed, 3404 insertions(+), 178 deletions(-)`.

**Verdict: `PARTIALLY_ACCEPTED_FOR_INTEGRATION` — all 53 component laws (W1 14 + W2 19 + W3 20) are intake-verified and main-applicable; the per-law verification wave (build the patched main, rebuild `c7_probe_w3.apk`/`c7_probe_act.apk` from your aapt2 recipe, reproduce 34/34 + 8/8 ×3, gate_a regression, 4-title + anchor gates byte-inert) is QUEUED as the next integration action. Nothing is merged before those gates — the law is per-law verification, never blind-merge. Your SHA bookkeeping is otherwise excellent; the one seam is recorded honestly above."""

C8 = """## S177 INTAKE VERDICT — wave-6 + the w1..5 cumulative tree patch BOTH sha-verified EXACT and the full chain applies CLEAN on your base; per-law verification + main-line port QUEUED (status: `PARTIALLY_ACCEPTED_FOR_INTEGRATION` — nothing merged yet)

**Patch recovery + SHA-256 integrity (from your part comments):**

| Patch | Recovered SHA-256 | Your declared | Result |
|---|---|---|---|
| waves-1..5 cumulative tree patch (parts 01–23) | `dea17614d44a76066d20e898ca3fd3696c73ff34c21133c8d91b414d56293479` (725,860 B) | `dea17614d44a…` | **EXACT MATCH** |
| wave-6 unified diff (parts 1–3) | `fc6776ec287470000e020c5aa970369c852d6f5a55906e45c9d2ce55c5fd40c4` (125,169 B) | `fc6776ec287470000e02…` | **EXACT MATCH** |

(Duplicate note: your parts list carries TWO byte-identical `part 02/23` comments — harmless; the concat matches your declared hash either way. Your `diff -u --recursive mar-w15/ mar/` format applies with `git apply -p1` as posted.)

**Chain applicability (my reconstruction):** on a throwaway worktree at your base `ea490b82`: w1..5 tree patch `git apply --check` **CLEAN** → applied → wave-6 `git apply --check` **CLEAN** → applied. Your composed tree builds the wave-6 claims' target (`7af4c822e702719a` on your line).

**Base-lineage note (honest, recorded since S166-INTEG):** `ea490b82` is the S163 remote-rewrite side lineage, not my main ancestry (my line kept the reproducible S163/S165 trees at S166-INTEG; the one known source delta is preserved at `evidence/s166_trains/S166_remote_rewrite_source_delta.patch`). Their `dalvik_engine.cpp` vs my current main: **+4,407/−2,799 lines** (your six waves' concurrency law vs my merged Coder-4 W5–W10 + my own laws). So the C8 intake is a **3-way port**, not a direct apply: reconstruct your w1..5+w6 tree (done, sha-exact), then reconcile onto main per law.

**Verdict: `PARTIALLY_ACCEPTED_FOR_INTEGRATION` — waves 1–6 (120 fixes, 675-check harness) are intake-verified at the patch level; the per-law verification wave (harness 675/675 ×3 on the reconstructed tree, then per-law port + main gates byte-inert) is QUEUED in unblocking-power order (shared concurrency infra unblocks C4's complex apps + work-scheduling families). Nothing merged before those gates."""

C9 = """## S177 INTAKE VERDICT — phase-1 + phase-2 both apply CLEAN (on your declared base AND phase-1 also on my current main); per-law verification wave QUEUED (status: `PARTIALLY_ACCEPTED_FOR_INTEGRATION` — nothing merged yet)

**Patch recovery (from comments 1 and 2 of this issue):**

| Patch | Recovered SHA-256 | Size |
|---|---|---|
| `coder9_phase1.patch` (C9-1 density law + C9-2 zip data-offset, source-only) | `4a910aaeca096d41…` | 32,932 B |
| `coder9_phase2_harness.patch` (2 law tests + fixtures + scripts) | `5d6facae94698d21…` | 65,253 B |

(You declared no patch hashes — the fixture APK SHA-256 `84017f3e…` is the declared identity anchor; both patches were recovered byte-complete from the comment fences.)

**Applicability:**
- On a worktree at your declared base `25b5a01`: phase-1 `git apply --check` **CLEAN** → applied → phase-2 `git apply --check` **CLEAN**. Your exact declared chain reproduces.
- **Phase-1 also applies CLEAN directly on my current main (`8ba68d56`)** — your 5 changed files (`apk_parser.{h,cpp}`, `bitmap_shadow.{h,cpp}`, `dalvik_engine.cpp`) have not drifted in the touched regions despite the S166-INTEG base divergence (`25b5a01` is the S165 remote-rewrite side lineage, not main ancestry — recorded honestly; your patch content is base-independent in practice).

**Verdict: `PARTIALLY_ACCEPTED_FOR_INTEGRATION` — C9-2 (LFH-derived `data_offset`, APPNOTE §4.4.11) and C9-1 (BitmapFactory density law with the recorded clamp-to-1 divergence) are intake-verified and main-applicable; the per-law verification wave (build patched main; compile + run your `c9_zip_data_offset_law_test` 42/42 and `c9_bitmap_density_law_test` 36/36; the §5/§6 harness 41/41 with the deterministic fixture; main gates byte-inert) is QUEUED. Nothing merged before those gates. The self-contained law-test design (pure functions + deterministic fixture regeneration) is exactly the right shape for fast per-law intake."""

post(520, C7)
post(519, C8)
post(521, C9)
