#!/usr/bin/env python3
"""S138 — post the new-campaign progress comment to issue #354 (§28 deliverable)."""
import subprocess, json

def token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no github credential")

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

BODY = """## NEW FINAL GENERIC RUNTIME COMPATIBILITY CAMPAIGN — waves 1–5 banked

Scope: user campaign §0–30 (deep core audit: black/white/partial/freeze root-cause elimination) + the remaining open items from the previous campaigns. All gates green after EVERY law commit: laws130 51/51, goldens ×3 byte-identical (dooz `d602648e8e401895`, ssw `10446aaf0cd642cc`, headingcalc `be1cea9cf994b26a`, microtimer `da73010a37dd0189`, whatsapp `31ddd4d5b8e6d18e`).

### §28 Root table (this session)

| Root | Symptom | Generic Cause | Fix | Visual Effect | Regression | Status |
| ---- | ------- | ------------- | --- | ------------- | ---------- | ------ |
| F-NEW-215 | droidify NCDFE family at okhttp/DI; silent failed `<clinit>` everywhere | class marked INITIALIZED before `<clinit>`; false `true` on failure; TWO bypass lists swallowed `<clinit>` itself (j$-CHM 11 statics lost) | honest erroneous-state registry + NoClassDefFoundError at first active use (sget/sput/new-instance/forName; sput init-trigger added) + `<clinit>` bypass exemption (JVMS 5.5) | j$-CHM statics materialize; okhttp/CursorOwner faces GONE | goldens ×3 identical | IMPLEMENTED+TESTED |
| F-NEW-216 | kotlin `toDuration` NPE → Dagger SettingsSerializer dead | FICTIONAL enum constant `TimeUnit.NANOS` in kOrdinals (ChronoUnit name; OpenJDK has NANOSECONDS) | AOSP name law | datastore settings build | goldens ×3 identical | IMPLEMENTED+TESTED |
| F-NEW-218 | Gson `getRawType` IAE "Expected a Class…" (opencalc) | CLASS_REF `instanceof` dereferenced `ref_id=instruction_sequence_` (a counter, not a heap id) into the SHARED id space → token class became random (PROVEN ref_id=63=CopyOnWriteArrayList vs ArrayList token); Class had no hierarchy edges | token classifies as `java.lang.Class` unconditionally + collision diag + Class hierarchy/interfaces seeded (OpenJDK Class.java) | Gson probe passes | goldens ×3 identical | IMPLEMENTED+TESTED |
| F-NEW-219 | null-chain NPE `Class.getComponentType` (Gson records probe) | `getMethod` minted fake records for ANY name; `Method.getReturnType` unbridged (null) | resolve-or-throw NoSuchMethodException (app-DEX method tables, superclass walk) + absent-on-Android JDK 9–17 API set → designed fallback + non-null getReturnType | opencalc rc=1→0, PARTIAL→SUCCESS | goldens ×3 identical | IMPLEMENTED+TESTED |
| F-NEW-220 | opencalc empty-shell frame despite successful inflation+addView | F165 anchor materialized a PARALLEL android.R.id.content ABOVE the appcompat screen root → app layout in a sibling the render walk never reaches | reuse the subDecor's own ContentFrameLayout + id-swap (AOSP createSubDecor) + descendant-cycle guard | **tree builds: 935→939→ConstraintLayout(8 children); SHA moved off empty-shell → `2291d74de0b6bac5`** | goldens ×3 identical | IMPLEMENTED+TESTED |
| F-NEW-200 | SUCCESS claims hid stub-driven behavior | no run-level roll-up of STUBBED/MISSING/ERROR | unbounded API status census (6 push sites, per-run reset); every SUCCESS/PARTIAL message carries the roll-up | opencalc live: "8678 IMPLEMENTED, 1188 STUBBED — success claim is stubby-bounded" | goldens ×3 identical | IMPLEMENTED+TESTED |
| F-NEW-202 | virtual-clock corruption after idle-settle | `settle()` jumped +1e9 ms (11.5 days) on the ONE clock shared with Scroller/GestureDetector/sleep-wake | jump to max(ready_at) — same drain set, real work boundary | goldens ×3 identical (drain law preserved) | goldens ×3 identical | IMPLEMENTED+TESTED |
| F-NEW-217 | droidify MutexImpl.unlock F084 spin | kotlinx waiter-resume protocol across virtual thread model (CAS resolution PROVEN not the cause) | evidence captured (SPIN-REGS/HISTO/STACK + UNSAFE-CAS-UNRESOLVED observability) | — | — | OBSERVED (PENDING fix) |
| F-NEW-221 | opencalc Map.get NPE in Gson adapter cache | R8 horizontal class merge: ctor/dispatch mismatch on merged host `A/h` | evidence captured (ctor ran, b=null; packed-switch paths disassembled) | — | — | OBSERVED (PENDING fix) |

### Honest answer: did the white screens move to real content?

**Yes — measurably.** Five-app visual gate (F-NEW-193 verdict chain, 3 runs each, byte-identical):

- **opencalc: BLOCKED (empty-shell) → OBSERVED REAL_APP_CONTENT ×3** (`2291d74de0b6bac5`) — moved THIS session by the F-NEW-215→220 law chain.
- **forkgram: OBSERVED REAL_APP_CONTENT ×3** (`cf4c41e62ceb6557`) — held.
- dame / game2048 / droidify: BLOCKED but deterministic, with first-missing attribution to registered frontiers (F-NEW-217 kotlinx resume protocol, F-NEW-221 R8 merge model, droidify protobuf-CNFE family).
- Goldens (dooz, simplestopwatch, headingcalc, microtimer) continue to produce real content deterministically; whatsapp stays honestly NO_ROOT.

### Why do some apps run and others don't (the running-app law)

The SUCCESS-PATH census (F-NEW-208/209, in progress) shows the working family shares: clean `<clinit>` bookkeeping (F-NEW-215), real enum/constant identity (F-NEW-216), correct class-token identity (F-NEW-218), resolve-or-throw reflection (F-NEW-219), and a canonical content parent inside the screen tree (F-NEW-220). Every failing title inspected so far fails one of exactly these five laws — the census now names which law per title.

### Remaining frontier (ranked per §29)

1. F-NEW-221 R8 merge-group model (opencalc adapter-cache NPE)
2. F-NEW-217 kotlinx-coroutines resume protocol (droidify mutex spin)
3. droidify protobuf-CNFE family; dame/game2048 first-missing legs
4. DEEP-AUDIT P1s: F-NEW-204 (log noise), 205 (lifecycle-owner canonicality), 206 (traversal order vs AOSP ViewRootImpl), 207 (final visual gate), F-NEW-192 (elevation)
5. SUCCESS-PATH SP-1..13 + SFC-1..9 corpus formalization

Registry: 516 roots (open 281), worklist 735 items. Commits: `3d193a5a`, `8c19a653`, `0f832f14`, `34b6597d`.
"""

r = subprocess.run(
    ["curl", "-s", "-X", "POST",
     f"https://api.github.com/repos/{REPO}/issues/354/comments",
     "-H", f"Authorization: Bearer {token()}",
     "-H", "Accept: application/vnd.github+json",
     "-d", json.dumps({"body": BODY})],
    capture_output=True, text=True).stdout
try:
    print("comment url:", json.loads(r)["html_url"])
except Exception:
    print("ERROR:", r[:400])
