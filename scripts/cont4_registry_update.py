#!/usr/bin/env python3
"""cont4_registry_update.py — CONT-4 wave registry update.

1. F-NEW-235: OBSERVED -> CLOSED-CLASSIFIED (the named remaining face
   Lm2;.b pc=1471 ISE classified RUNTIME ROOT via the CONT-4 diagnostic
   chain; root-caused to F-NEW-239/240/241/242, all fixed; the game runs
   its full pipeline: board -> solver -> artwork -> render, exit=0 x3).
2. Registers F-NEW-239 / F-NEW-240 / F-NEW-241 / F-NEW-242.
3. Recomputes summary counts.
"""
import json

P = "root_registry.json"
r = json.load(open(P))
roots = r["roots"] if isinstance(r, dict) and "roots" in r else r
by_id = {x["id"]: x for x in roots}

by_id["F-NEW-235"]["status"] = "CLOSED-CLASSIFIED"
by_id["F-NEW-235"]["progress_note"] = (
    "CONT-4 PHASE 1 CLASSIFICATION COMPLETE (deterministic diagnostic chain, "
    "env MINIANDROID_CONT4_SOLVER_DIAG): the remaining named face Lm2;.b "
    "pc=1471 ISE 'Even face counts always permit a completion' is a RUNTIME "
    "ROOT, not an app bug. Proof: (a) the solver's face-set is built by "
    "toSet(take(shuffled(tiles, Ls5;-RNG), n)) (Lt;.r=shuffled, Ls;.y=take, "
    "Ls;.D=toSet confirmed from DEX); (b) Kotlin shuffled swaps via "
    "list[i]=list.set(j,list[i]) — ArrayList.set MUST return the previous "
    "element (OpenJDK law); the pre-fix engine returned VOID, so every swap "
    "poisoned a slot with an empty string ([F-NEW-238-SET]/[CONT4-SET-EMPTY] "
    "chain Lt;.r@pc198 <- Lm2;.b@pc138); (c) the poisoned list made "
    "toSet() produce a string-typed set whose contains(Integer) always "
    "missed -> per-face availability counts initialized to 46 units for a "
    "68-tile board; (d) the solver drains exactly 1 unit/outer iteration "
    "(trace-verified) so the game's own parity guard legitimately fired at "
    "iteration 47 with 22 tiles unpaired. Fix set: F-NEW-239 (set returns "
    "previous element) + F-NEW-240/241/242 (the artwork/JSON config chain "
    "the game advances into). Post-fix: exit=0 Status:SUCCESS x3, "
    "byte-identical screenshot 76e097244767d6c3; the game renders its own "
    "full-screen content (2073600/2073600 px painted). One residual named "
    "face downstream (does not affect run completion): Lr5;.g pc=150 "
    "getClass-on-null deferred NPE, caught by the app's own handlers."
)

new_roots = [
    {
        "id": "F-NEW-239",
        "title": "java.util.ArrayList.set(int,E) must return the PREVIOUS "
                 "element (OpenJDK ArrayList.set law) — the engine returned "
                 "VOID, corrupting every swap idiom",
        "status": "ROOT-CAUSED-FIXED",
        "root_cause": "CollectionShadow set() handler ended with "
                      "handled_void(). Kotlin shuffled(rng) (R8: Lt;.r) "
                      "implements Fisher-Yates as list[i]=list.set(j,"
                      "list[i]) — the return IS the swap temporary; with "
                      "VOID the next set() received an UNSET/\"\" element "
                      "and poisoned one slot per swap (CONT-4 evidence: "
                      "[CONT4-SET-EMPTY] chains Lt;.r@pc198<-Lm2;.b@pc138; "
                      "solver face-set became string-typed). Generic: "
                      "Collections.shuffle, sort internals, any "
                      "swap-via-set idiom. FIX: kind-faithful old-value "
                      "serve (int/string/object/null) before overwrite; "
                      "OOB set() answers null with the divergence "
                      "documented (F-165 precedent).",
        "evidence": "run/cont4/fairy_diag* (stage dumps), "
                    "run/cont4/trace_run1 (full METHOD-TRACE), post-fix "
                    "run/cont4/fairy_clean1-3 exit=0 x3 byte-identical.",
    },
    {
        "id": "F-NEW-240",
        "title": "BitmapFactory.Options law: inJustDecodeBounds=true must "
                 "fill outWidth/outHeight/outMimeType and return null "
                 "without allocating; inSampleSize honored (AOSP "
                 "BitmapFactory.java)",
        "status": "ROOT-CAUSED-FIXED",
        "root_cause": "The decodeStream/decodeFile/decodeResource/"
                      "decodeByteArray handlers ran the FULL decode and "
                      "never wrote the Options out* fields; the game's "
                      "bounds-first validation (Ln5;.b: open -> "
                      "decodeStream(bounds) -> if outWidth<=0 throw 'Invalid "
                      "fairy artwork: <path>') legitimately threw on valid "
                      "assets (1122x1402 PNG). FIX: f240_decode_with_options "
                      "— single decode, out* always set, bounds-only returns "
                      "null unallocated, inSampleSize subsample ((dim+s-1)/s "
                      "nearest).",
        "evidence": "run/cont4/fairy_fixed2 (bounds-only logs res/*.png "
                    "1254x1254), 'Invalid fairy artwork' GONE post-fix.",
    },
    {
        "id": "F-NEW-241",
        "title": "java.io.Reader.read(char[]) real-character law: BufferedReader/"
                 "InputStreamReader.read fills the buffer from the wrapped "
                 "stream and returns -1 at EOF (OpenJDK Reader.java)",
        "status": "ROOT-CAUSED-FIXED",
        "root_cause": "The K-34 real-byte read law matched only "
                      "*InputStream* declaring classes; BufferedReader."
                      "read(char[]) fell to the type-aware stub default "
                      "(0) — and every `while ((n = read(cbuf)) >= 0) "
                      "write(...)` copy loop spun forever (fairymahjong "
                      "Ln5;.b artwork-config JSON read: F084 "
                      "forward-progress halt at pc=0x108, deterministic "
                      "x3). FIX: dedicated read law over the SAME "
                      "resolve_asset_stream wrapper hops readLine uses "
                      "(BufferedReader.in -> InputStreamReader.source -> "
                      "InputStream), char-faithful fills, -1 at EOF, "
                      "single-char + two overloads.",
        "evidence": "F084-HALT-RETURN Ln5;.b pc=0x108 x3 pre-fix; "
                    "halts GONE post-fix.",
    },
    {
        "id": "F-NEW-242",
        "title": "java.io.StringWriter accumulation law: write(int/char[]/"
                 "String) appends to the buffer, toString() returns the "
                 "accumulated chars (never null), getBuffer() exposes them",
        "status": "ROOT-CAUSED-FIXED",
        "root_cause": "Every StringWriter method fell to the generic stub: "
                      "write() stored nothing, toString() answered null -> "
                      "the canonical StringWriter JSON-asset parse chain "
                      "NPE'd at the R8 toString null-check (Ln5;.b pc=278 "
                      "Object.getClass on null). FIX: sb_value heap "
                      "convention (same as StringBuilder), full write/"
                      "toString/getBuffer/flush/close laws in bridge_to_api.",
        "evidence": "Ln5;.b pc=278 deferred NPE pre-fix; gone post-fix; "
                    "the JSON config parse completes (JSONObject.<init> "
                    "reached with real text).",
    },
]
for nr in new_roots:
    if nr["id"] not in by_id:
        roots.append(nr)

if isinstance(r, dict):
    verified = sum(1 for x in roots if x.get("status") in
                   ("ROOT-CAUSED-FIXED", "CLOSED-CLASSIFIED"))
    r["summary"] = {
        **(r.get("summary") or {}),
        "total_roots": len(roots),
        "verified_fixed": verified,
    }
    open(P, "w").write(json.dumps(r, indent=1) + "\n")
else:
    open(P, "w").write(json.dumps(roots, indent=1) + "\n")
print("registry updated: roots =", len(roots))
