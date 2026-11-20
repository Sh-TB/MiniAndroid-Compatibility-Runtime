# NEXT INTEGRATION PLAN — dependency-ordered, evidence-based

Order follows verified evidence (not issue-count targets). Each step names
its ledger ID and the test that proves it.

1. **BUG-7 dedupe (AUD-49)** — two differing shadow_registry.h copies; repoint
   consumers to the authoritative src/framework copy; proof = battery 49/49 +
   header-cascade probe (dalvik_engine_types edit → 0 TU rebuild).
2. **#633 MG-011 ok-fix (AUD-40)** — one-line `out->ok` correction in vector
   decode; proof = direct-vs-referenced PathData pixel parity + battery.
3. **CMake WEBP parity (AUD-07)** — add -DMINIANDROID_HAVE_WEBP to CMakeLists;
   proof = cmake configure + binary section compare vs Make build (needs
   cmake restored — AUD-06 blocker).
4. **#626 PR rebase (PRESERVED manifest)** — rebase wave-10 dev-so profiles on
   current HEAD; proof = dev-so cycle timings + 5-APK gate on dev path.
5. **RC-12 ScaleType oracle recovery (AUD-26)** — obtain the 4 commits; add
   verifier/scaletype_oracle.py + apps/probe_scaletype; proof = mutation
   battery 8/8 + three-run determinism.
6. **#630/#631 layout apps (AUD-43)** — recover the ten test apps; label
   diagnostic vs compatibility; proof = each app runs under the gate.
7. **#632 §H/§K laws (AUD-30/32)** — GridLayout solver, nine-patch npTc;
   proof = focused law tests in the battery.
8. **UBSAN=1 profile (AUD-47)** — optional sanitizer profile; proof = the
   reported 7/7 rerun.
9. **-Werror/CI (AUD-45)** — only after the warning backlog is triaged, per
   #632 §R (R1-R4 dead-code removal precedes -Werror).

Standing rules carried forward: ABBA order for any timing claim (BUG-5
lesson); evidence logs force-added per the BUG-3 law; Production and Dev-So
results reported separately; no semantic weakening of runtime behavior for
build speed.
