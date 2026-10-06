#!/usr/bin/env python3
"""cont7w3_registry_update.py — CONT-7 WAVE 3 session registry update.

1. F-NEW-253: refresh evidence pointer (evidence/cont7/w3/ artifacts were
   lost in the container reset and never committed) -> the fresh directive-
   faithful artifacts produced by re-proving the chain live.
2. Register F-NEW-257 (Bundle parcel-family content fidelity — directive §4
   contract face A/D) ROOT_CAUSED_FIXED.
3. Register F-NEW-258 (STRING_REF instance-of law — discovered by the §4
   probe's B-07 row) ROOT_CAUSED_FIXED.
4. F-NEW-256: note live re-verification (stays CLASSIFIED — the ONE next
   root per §15 discipline).
5. Recount totals + status counts.

Semantic clustering justification (registry discipline):
- F-NEW-253 = platform CLASS HIERARCHY metadata for reflection walks
  (isInstance/assignable over shadowed platform classes).
- F-NEW-257 = Bundle CONTENT STORAGE semantics (put/get reference law) —
  a different layer (framework data-plane API) than 253's type metadata.
- F-NEW-258 = BYTECODE instance-of classification of STRING_REF registers —
  a different dispatch surface (interpreter opcode path) than 253's
  reflection path, though same domain (runtime type classification).
No duplicates created; no roots merged; each has its own synthetic proof.
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)

roots = reg["roots"]
by_id = {r.get("id"): r for r in roots}

# ── 1. F-NEW-253 evidence pointer repair ─────────────────────────────
r253 = by_id["F-NEW-253"]
r253["evidence"] = (
    "evidence/cont7/{fnew253_baseline.json, fnew253_bundle_probe.json, "
    "fnew253_class_probe.json, fnew253_saveable_probe.json, fnew253_final.json} "
    "(2026-10-06 re-proof session: the previously referenced evidence/cont7/w3/ "
    "was never committed and is absent from the container — the full chain was "
    "re-proven live at binary c0fa65ccc7f284e7: decisive rows "
    "Serializable.isInstance(Bundle)->FALSE then Parcelable.isInstance(Bundle)->TRUE "
    "at caller=Le72;.k on the final binary with anchor-identical screenshot). "
    "Fix completeness added: AOSP Bundle extends BaseBundle edge registered in "
    "framework_superclass_of (probed via getGenericSuperclass S-07 — forName "
    "cannot name shadow framework classes, honest recorded limitation)."
)
r253["verified_current"] = "2026-10-06 binary c0fa65ccc7f284e7 — saveable IAE 0, composition clean, anchor d602648e8e401895 byte-identical x3"

# ── 2. F-NEW-257 ──────────────────────────────────────────────────────
if "F-NEW-257" not in by_id:
    roots.append({
        "id": "F-NEW-257",
        "title": "Bundle parcel-family content fidelity: putParcelable silently dropped values and getParcelable/get(String) answered null (directive §4 synthetic contract face A/D; dooz-independent)",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework/bundle-content-storage",
        "root_cause": "PROVEN BY THE DIRECTIVE-REQUIRED SYNTHETIC PROBE (fixtures/fnew253_probe, real aapt2/ECJ/D8 toolchain): the EXP-093 Bundle op block implemented only putString/putInt/putBoolean/putLong/getString/getInt/getBoolean/containsKey — putParcelable fell to the generic stub law (value dropped: containsKey=false after put), getParcelable/get(String) returned null (pre-fix probe 14/20 with every §4 identity row failing: B-01..B-04, B-07, B-08). ART law: a Bundle is an in-memory key->value map; put* stores the object reference, get* returns the SAME reference (no marshalling before writeToParcel).",
        "fix": "ONE generic point in the EXP-093 Bundle op block (dalvik_engine.cpp): AOSP BaseBundle reference-storage law — putParcelable/putSerializable store the value under the same 'bundle:<key>' field law as putString; getParcelable/getSerializable/get(key) return that reference; missing key -> null; Bundle.get(key,def) 2-arg form; typed-getter mismatch law (getParcelable on a String-typed entry -> null via the AOSP CCE-inside-getter path; getSerializable on a String lawful — OpenJDK String implements Serializable). No app conditions, no class-name hacks.",
        "synthetic_probe": "fixtures/fnew253_probe B-01..B-08 all PASS post-fix (probe v1.0 20/20; v1.1 21/21 incl. S-07 BaseBundle completeness). Pre-fix run preserved: evidence/cont7/fnew253_bundle_probe_prefix_run_view_tree.json (14/20).",
        "evidence": "evidence/cont7/fnew253_bundle_probe.json + fnew253_final.json; dooz's own navigation-state Bundles exercise the storage law live ([EXP093-BUNDLE] bundle_id=5045/5065 nav-entry-state keys).",
        "not_claimed": "putParcelableArrayList/getSparseParcelableArray and Parcel marshalling round-trips are NOT implemented/tested (honest untested scope); the fix does NOT affect dooz's draw frontier (F-NEW-256) — dooz composition never reaches putParcelable before canBeSaved."
    })

# ── 3. F-NEW-258 ──────────────────────────────────────────────────────
if "F-NEW-258" not in by_id:
    roots.append({
        "id": "F-NEW-258",
        "title": "instance-of bytecode on a STRING_REF register answered FALSE (String-value runtime-type law; discovered by directive §4 probe row B-07)",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "runtime/instance-of-classification",
        "root_cause": "PROVEN BY PROBE ROW B-07 (pre-fix): a String retrieved from Bundle.get() answered getClass().getName()='java.lang.String' (getClass handles STRING_REF) while `raw instanceof String` answered FALSE — the reflection path (F-103 isInstance law) classifies STRING_REF probes as Ljava/lang/String; but execute_instance_of handled only CLASS_REF/OBJECT_REF branches and fell through every branch for STRING_REF registers, leaving is_instance=false. OpenJDK/ART law: any non-null string value IS a java.lang.String instance; instance-of and Class.isInstance must agree.",
        "fix": "ONE branch in execute_instance_of: STRING_REF values classify as Ljava/lang/String; through the SAME is_subclass_of walk — which composes the framework closure so the full ART truth holds (String is-a CharSequence/Serializable/Comparable). No name matching, no special classes.",
        "synthetic_probe": "B-07 PASS post-fix (raw=java.lang.String, Parcelable.isInstance(raw)=false — String stays String with BOTH conditions lawful); M-01..M-06 isInstance matrix unchanged 6/6 (no regression).",
        "evidence": "evidence/cont7/fnew253_class_probe.json (F-NEW-258 section) + fnew253_bundle_probe.json (B-07 pre/post)."
    })

# ── 4. F-NEW-256 live re-verification note ───────────────────────────
r256 = by_id.get("F-NEW-256")
if r256:
    r256["reverified"] = "2026-10-06 binary c0fa65ccc7f284e7: app_draw_ops=0 / draw_walk_ran=true / nodes_visited=2 / first_missing_stage=APP_DRAW_OPS in every dooz run (x3 byte-identical d602648e8e401895) — classification stands as the ONE next root; NOT fixed this wave per §15 scope discipline."

# ── 5. totals ─────────────────────────────────────────────────────────
reg["total"] = len(roots)
reg["count"] = len(roots)
counts = {}
for r in roots:
    counts[r.get("status", "UNKNOWN")] = counts.get(r.get("status", "UNKNOWN"), 0) + 1
reg["status_counts"] = counts
reg["meta"]["last_update"] = "CONT-7 WAVE 3 re-proof session 2026-10-06: F-NEW-253 evidence repaired + verified_current; F-NEW-257/258 registered ROOT-CAUSED-FIXED; F-NEW-256 re-verified live"

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)

print(f"roots now: {reg['total']}")
print("status counts:", json.dumps(counts, sort_keys=True))
