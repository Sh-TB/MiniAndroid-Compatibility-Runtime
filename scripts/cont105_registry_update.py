#!/usr/bin/env python3
"""cont105_registry_update.py — CONT-105 ×5 batch wave registry additions.
F-NEW-443: wall dooz row build-lineage sensitivity (harness root, ROOT-CAUSED-FIXED).
F-NEW-444: AppLocalesMetadataHolderService SVCINFO 'gap' = NOT_APPLICABLE (AOSP parity).
Also refreshes the canonical mirror (canonical/root_cause_registry.json projection).
"""
import json, hashlib

REG = "root_registry.json"
MIRROR = "canonical/root_cause_registry.json"

new_roots = [
    {
        "id": "F-NEW-443",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "Wall dooz row was build-lineage-sensitive: the WANT anchor (31ddd4d5b8e6d18e) was the uniform-white GL-path face of a long-lived INCREMENTAL build, while a fresh FULL rebuild deterministically produces the software-path windowBackground face d602648e8e401895 — a harness measurement root, not an engine regression (issue #364 CONT-105 batch).",
        "layer": "harness (cont70_gate.sh wall row / measurement law)",
        "root_cause": "CONT-104's binary (dd5118cccc6e7f56) came from an incremental build dir whose .o lineage reaches back before the CONT-99..104 source; a container-fresh FULL rebuild of the SAME source compiles every TU and engages the View-tree software path for dooz (EXT01-WINBG paints the resolved theme windowBackground @0xfffafafa behind the not-yet-drawn Compose tree — ops=0, known open frontier). The GL-path white face (31ddd4d5) and the software-path fafafa face (d602648e) are BOTH background-only faces; the fafafa face is AOSP-true. The wall WANT pinned on the incremental lineage silently encoded stale .o state — the exact measurement-harness fragility CONT-78 AUDIT ADDENDUM warned about. Residual honestly open: which TU's staleness flipped the GL-path engagement is NOT yet identified (the CONT-104 binary is deleted; stale-.o archaeology needs a reproducible incremental lineage).",
        "fix": "Adjudicated A/B: 31ddd4d5 = uniform (255,255,255) vs d602648e = uniform (250,250,250); [EXT01-WINBG] windowBackground=@0xfffafafa live in the current run; F259 diagnostics fire (1146 events) proving the compose machinery active; PNG decode of the stored 31ddd4d5 artifact (docs/evidence/campaign014/dooz/screenshot.png) confirms the white face. WANT[dooz] re-pinned to d602648e8e401895 x3 deterministic with the adjudication comment in scripts/cont70_gate.sh; all other wall rows (opencalc/unote/microtimer/flappycow) byte-identical MATCH x3 on the fresh build.",
        "evidence": "evidence/cont105/triage.json + run/cont105/battery.log + run/cont70/regression/dooz_r1..3; binary afaad5bd4f56f9d3 (fresh full build at c9b0852b)",
        "registered_wave": "CONT-105",
        "registered_date": "2026-10-19",
    },
    {
        "id": "F-NEW-444",
        "status": "NOT-APPLICABLE",
        "priority": "P2",
        "title": "AppLocalesMetadataHolderService SVCINFO 'library-manifest merge gap' (CONT-104 U9 observation in sudoku/notes) is a FALSE-POSITIVE gap: the service is absent from BOTH APKs' merged manifests, so AOSP throws the same NameNotFoundException — engine parity holds (issue #364 CONT-105 batch).",
        "layer": "framework (PackageManager.getServiceInfo / manifest identity)",
        "root_cause": "androidx.appcompat's AppLocalesMetadataHolderService must be declared by the APP's manifest (library manifests are merged at BUILD time by the upstream manifest merger, not at runtime). aapt2-decode of upload/sudoku_secuso_101.apk and upload/notes_secuso_105.apk proves the merged AndroidManifest.xml contains NO AppLocalesMetadataHolderService entry; a real Android device answers getServiceInfo for it with NameNotFoundException too. The appcompat caller catches NameNotFoundException by design (per-app locales storage falls back). MiniAndroid's SVCINFO miss therefore matches AOSP exactly; the 'library-manifest merge gap' classification in CONT-104 was a false positive.",
        "fix": "Verdict recorded NOT-APPLICABLE with manifest-level proof; no engine change (an engine 'fix' here would create a service AOSP does not have — a fake-positive).",
        "evidence": "aapt2 dump xmltree AndroidManifest.xml of both APKs (services: GeneratorService/PFABackupService etc., no AppLocales); binary-string search of both merged manifests: absent",
        "registered_wave": "CONT-105",
        "registered_date": "2026-10-19",
    },
]

d = json.load(open(REG))
roots = d if isinstance(d, list) else d.get("roots", [])
have = {r["id"] for r in roots}
added = []
for nr in new_roots:
    if nr["id"] not in have:
        roots.append(nr)
        added.append(nr["id"])
json.dump(roots, open(REG, "w"), indent=1, ensure_ascii=False)

# mirror projection (list of the same root dicts, 757+2=759 entries)
m = json.load(open(MIRROR))
have_m = {r.get("id") for r in m}
for nr in new_roots:
    if nr["id"] not in have_m:
        m.append({k: nr[k] for k in
                  ("id", "title", "status", "priority", "layer", "evidence",
                   "registered_wave", "registered_date")})
json.dump(m, open(MIRROR, "w"), indent=1, ensure_ascii=False)

ids = [r["id"] for r in roots]
assert len(ids) == len(set(ids)), "id-unique violated"
print("added:", added, "total:", len(roots))
