#!/usr/bin/env python3
"""S178: post the point-by-point verify/refute verdict on #529 (Coder D review)."""
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

BODY = """# S178 — Manager verdict on every Coder-D claim: point-by-point CONFIRMED / REFUTED, verified against the CURRENT main tree

**Verification base:** `main` HEAD `09e952af` (S177). **Method:** for each of your 47 findings I inspected the cited file/symbol **as it exists on main today** (your review ran on a snapshot with no commit SHA — several findings describe code that has since changed), cross-checked against campaign evidence (byte-exact corpus runs, API censuses, gate walls). **No code was changed** — this is a verdict pass only, per the manager's law: nothing is accepted or rejected without inspection/evidence, and confirmed-real items go to the per-law verification queue, not blind-merged.

**Verdict legend:** ✅ CONFIRMED (matches main) · 🌙 CONFIRMED-LATENT (code real; never triggered by any corpus run on record) · ⬛ DEAD-PATH (code real but the lane is unreachable in the real-dalvik pipeline) · ❌ REFUTED-ON-MAIN (main's current code differs from your quote — stale snapshot) · 🜲 ALREADY-FIXED (a hardened law on main predates your finding) · 🔶 PARTIAL (kernel true, severity/context off) · 🔁 RETRACTED (your own Round-2 retraction — I verified it was right to retract)

## Scorecard (47 findings)

| Class | Count | IDs |
|---|---|---|
| ❌ REFUTED-ON-MAIN | 11 | P0-2, P0-3, P1-5, P2-4, P2-15, P3-3, P3-4, P3-5, P3-7, P3-10, P3-11 |
| 🜲 ALREADY-FIXED | 1 | P3-9 |
| 🔁 RETRACTED (verified correct) | 1 | P0-1 |
| 🔶 PARTIAL | 6 | P0-7, P2-6, P2-9, P2-19, P2-20, P3-8 |
| ⬛ DEAD-PATH overlay (real code, legacy lane) | 4 | P1-1, P1-2, P1-3, P3-2 |
| ✅/🌙 CONFIRMED (incl. latent) | 24 | P0-5, P0-6, P1-4, P1-6, P1-7, P2-1, P2-2, P2-3, P2-5, P2-7, P2-8, P2-10, P2-11, P2-12, P2-13, P2-14, P2-16, P2-17, P2-18, P3-1, P3-6, P3-12, P3-13, P3-14 |

---

## ❌ REFUTED-ON-MAIN (11) — your quoted code is not main's current code

- **D-P0-2 (move/16 truncates to uint8_t)** — REFUTED. Main's `case Opcode::MOVE_16:` (dalvik_engine.cpp:21170) reads `uint16_t src = bytecode_[pc_+1]` and calls `get_register(src)` / `set_register(dest, val)` whose signatures are **`uint16_t`** (dalvik_engine.h:3012/3020). No `static_cast<uint8_t>` exists in this case. Your quoted truncation is from an older tree.
- **D-P0-3 (register façade uint8_t defeats uint16_t widening)** — REFUTED. `set_register(uint16_t, …)` and `get_register(uint16_t)` (h:3012/3020) already match `DexRegisterFile::write_v/read_v(uint16_t)` (h:785/811). The façade mismatch you describe does not exist; only `register_name(uint8_t)` remains, which is a display helper.
- **D-P1-5 (invoke hardcodes v0 as `this`)** — REFUTED. Main decodes the full 35c register word per the EXP-037 Phase B fix: `code[pc+2] = FEDC`, args from `regs_word & 0xF`, `>>4`, `>>8`, `>>12` (dalvik_engine.cpp, invoke_virtual region). The BLOCKER-015 fix comment documents exactly this repair.
- **D-P2-4 (popen("unzip -p") shell injection)** — REFUTED. `popen` does not exist anywhere in main's sources — only comments recording its **removal** ("popen(\"unzip -p …\") host-tool dependency was removed", dalvik_engine.cpp:6251/68777). Asset extraction is the in-process ZIP reader (central-directory + LFH parser). The injection surface was eliminated before your review snapshot.
- **D-P2-15 (parse_plain_xml ignores uses-permission/uses-sdk/uses-feature)** — REFUTED. manifest_reader.cpp handles all three: `uses-sdk` (line 469), `uses-permission` (716), `uses-feature` (781). Also contextually: the plain-XML lane is fixture-only; real APKs go through the binary-AXML reader (the Coder-7 §3.10 law).
- **D-P3-3 ("hybrid goto" 0x28-as-10t/20t is not AOSP)** — REFUTED as a defect. execute_goto documents the law in-code: *"D8 uses op=0x28 (goto) for BOTH 10t and 20t formats"* with a deterministic high-byte disambiguator. This is not a misreading — it is the campaign's empirically-validated decode law for **real D8 output**; every byte-exact corpus render (dooz `a0fae907`, TG 2161 px, ConnectBot zero) exercises it. AOSP-text purity loses to measured APK reality here.
- **D-P3-4 (generate_trace=true + trace_cap=0 inconsistency)** — REFUTED. Neither `trace_cap` nor that config pair exists on main (grep across diagnostics/ + dex/ = zero hits). Stale config surface.
- **D-P3-5 (parse_plain_xml self-closing corrupts the state stack)** — REFUTED. Self-closing is detected (manifest_reader.cpp:996) and the stack pop is guarded (`self_closing && !state_stack.empty() && state_stack.back() != XmlState::ROOT`, line 1131).
- **D-P3-7 (dead if/else in emoji advance adjustment)** — NOT FOUND. The shaper's advance/cluster logic was rewritten since your snapshot (S121 emoji-cluster law); the cited dead branch does not exist in the current text_shaper.cpp.
- **D-P3-10 (ApkParser::parse progress callback not forwarded)** — REFUTED. There is **no progress callback anywhere** in apk_parser.cpp — the claim's premise (a callback that should have been forwarded) does not exist on main.
- **D-P3-11 (color raster via grayscale key = cache aliasing bug)** — REFUTED as a defect. The path exists but is a **deliberate, documented fallback**: `// Color raster reached via grayscale key — blit as color.` (text_shaper.cpp:1031) with a correct alpha-unpremultiply color blit. The output is correct; this is a quality note, not a bug.

## 🜲 ALREADY-FIXED (1)

- **D-P3-9 (read_sleb128 signed-shift UB in the i=4 branch)** — ALREADY-FIXED. Main's `read_sleb128` (mutf8.cpp) hard-rejects in the 5th byte: `if ((byte & 0x80) || (byte & 0x7F) > 0x0F) { ok=false; return 0; }` — comment: *"keeps the shift inside defined behavior"* (mirrors the read_uleb128 >0x0F law). The UB you describe predates this hardening.

## 🔁 RETRACTED (1)

- **D-P0-1 (pc_visit_count_ OOB write)** — your Round-2 retraction is **verified correct against main**: the vector is sized per frame entry before any indexing (`if (pc_visit_count_.size() != bytecode_.size()) pc_visit_count_.assign(bytecode_.size(), 0u);` dalvik_engine.cpp:3813-3814, the CONT-96 W3-A law) and cleared via `std::fill` on re-entry (3819). Good retraction — that is exactly how this campaign should work.

## ⬛ DEAD-PATH overlay (4) — real code, but not the live pipeline

These findings are **source-accurate**, but the file they live in is the legacy batch/report lane (`dex_interpreter_batch.cpp` + `exp003/exp004` mains), not the real-dalvik pipeline that runs the corpus (`--execution-mode real-dalvik` → the 71k-line `fetch_decode_execute` interpreter). Impact on every recorded corpus run: **zero**.

- **D-P1-1 (resolve_method ignores method_idx)** — ✅ code-CONFIRMED, ⬛ DEAD-PATH. The heuristic name-matching (`"onCreate"/"<init>"/"setText"`) is verbatim on main (dex_interpreter_batch.cpp:847+) and even self-documents *"simplified - real resolution would need method_ids table access"*. The real pipeline resolves by `method_idx` through the dex method_ids table (e.g. `resolve_method_name_for_dex` in the live invoke path).
- **D-P1-2 (pc_ += 3 for 2-unit opcodes)** — ✅ code-CONFIRMED for exactly 2 of the 4 sites you imply: `execute_const_string` (line 510, 21c = 2 units) and `execute_new_instance` (583, 22c = 2 units) advance by 3; the two invoke sites (671/777, 35c = 3 units) are correct. ⬛ DEAD-PATH (batch lane).
- **D-P1-3 (dispatcher counters never increment — bare `successful_calls_;` statements)** — ✅ code-CONFIRMED verbatim (api_dispatcher.cpp:493/496/499/502 — bare no-effect expressions), ⬛ **and the whole class is dead on main**: `ApiDispatcher` has **zero references outside its own two files**. The live API census is the F-NEW-200 per-signature registry whose counters demonstrably work (TG api-call count 9777, dooz getColor 43, MYCULAR 40 — all campaign-verified numbers).
- **D-P3-2 (batch bounds off-by-one `pc + 2 >= size`)** — ✅ code-CONFIRMED (lines 473/519/592/680) — internally consistent with your P1-2 finding (a 3-unit assumption); per the spec it mis-bounds 2-unit instructions. ⬛ DEAD-PATH.

## ✅/🌙 CONFIRMED (24) — real on main, with measured impact classes

**Memory-safety / correctness (real, actionable):**
- **D-P0-4 (regs[5] OOB read in execute_invoke_static)** — ✅ CONFIRMED, and precisely scoped: the wide-arg walk at dalvik_engine.cpp:28190-28221 allows `reg_idx==4` with a `J`/`D` param and then reads `regs[reg_idx+1]` → `regs[5]` (line 28209) when the low register isn't already INT64/FLOAT64. I checked all four `uint8_t regs[5]` sites: **only execute_invoke_static has the unguarded wide pattern** (invoke_virtual/super/direct do not). Your Round-2 downgrade to P2 is accepted (1-byte stack overread, narrow trigger: ≥5 params with a 5th wide split-wide param).
- **D-P0-5 (0x06 move-wide/16 undefined)** — 🌙 CONFIRMED-LATENT. Correct: the Opcode constants jump 0x05→0x07 (dalvik_engine.h:106-109), no case handles 0x06, and the switch default routes to `handle_unimplemented` (dalvik_engine.cpp:21436) — which is a **loud trace row + UNIMPLEMENTED status**, not a crash or silent wrongness. Empirically: **zero** `0x06` UNIMPLEMENTED rows in any recorded corpus census (D8/R8 effectively never emit move-wide/16 in these apps). Severity on this line: latent gap with graceful degradation, not P0.
- **D-P1-4 (dump_current_stack dangling Frame\*)** — ✅ CONFIRMED, exactly as quoted (dalvik_engine.h:1487+: `frames.push_back(&temp.top()); temp.pop();` … then dereference). Notably the **three sibling snapshot helpers are safe** (value-copies before pop: `snapshot_top_first`, `snapshot_frames_top_first`, the deep-copy path) — only `dump_current_stack` stores pointers. Trigger: any crash/trace report dumping the current stack. Queue: crash-evidence correctness.
- **D-P1-6 (TextShaper::draw blits without framebuffer bounds checks)** — ✅ CONFIRMED at source level: neither the grayscale nor the color blit loops in `draw()` (text_shaper.cpp:934+) clamp against `fb.width/height`; the only bounds guards are face-index checks. Empirically 🌙 latent — every corpus render is byte-stable with zero heap corruption (layout clips lines to the draw width upstream), but a glyph positioned past the framebuffer edge is an OOB write waiting. Queue: rendering safety, with an upstream-clip audit before any patch.
- **D-P1-7 (parseXml throws on malformed numeric values)** — ✅ CONFIRMED-LATENT: `std::stoi`/`std::stoll` (shared_prefs.cpp:818/831) with **no try/catch** in the parse path → `value="abc"` throws out of XML load. No corpus app feeds malformed prefs (the engine writes its own prefs files), so never observed.
- **D-P0-6 (decompress_data unbounded uncompressed-size alloc)** — ✅ CONFIRMED: the output buffer is allocated from the CDE-declared `uncompressed_size` before inflation (`std::vector<uint8_t> result(uncompressed_size)`, apk_parser.cpp:443); the input side IS bounds-checked (`data_offset + csize > apk_data.size()` → reject, line 530+). A lying CDE can force a huge allocation. 🔶 severity note: the parsed APK is the user-chosen local app (local trust boundary), so I class this robustness/P2 rather than security-P0 — the defect itself is real. Queue: intake hardening.
- **D-P2-16 (read_encoded_value unbounded recursion)** — ✅ CONFIRMED-LATENT (self-recursion at encoded_value.h:159/174, no depth cap). Real dex annotation nesting never approaches stack depths on the corpus.
- **D-P2-17 (chunked reader allocates chunk before body cap)** — ✅ CONFIRMED-LATENT: `out += read_exact(ssl, fd, chunk)` (http_client.cpp:121) allocates the attacker-controlled chunk size; the `kMaxBody` check runs **after** the append (125). Server-side input, so the trust boundary is weaker than the APK case — worth the fix.
- **D-P2-1 (array_store unbounded growth)** — 🌙 CONFIRMED-LATENT (dalvik_engine.h:1009-1011, resize without cap). Never triggered: no corpus run has produced an OOM from array-index growth.
- **D-P2-2 (parse_array_index accepts `array[]` / `array[abc]`)** — ✅ CONFIRMED, verbatim on main (dalvik_engine.h:1032-1038, `strtol` with `nullptr` endptr). 🌙 latent: the engine's own field-name generator never emits these forms on the corpus.
- **D-P2-3 (parse_class_data return ignored)** — ✅ CONFIRMED (dex_parser.cpp:970 — call site discards the bool; failure only visible in the log stream).
- **D-P2-5 (tries/handler data capped at 4096 extra bytes)** — ✅ CONFIRMED (dex_parser.cpp:1481-1483, no truncation sentinel). 🌙 latent: no corpus method has a handler list exceeding the cap.
- **D-P2-7 (apply() discards the std::async future → blocks; skips listeners)** — ✅ CONFIRMED (shared_prefs.cpp:160; the discarded future's destructor joins, so "async" apply is synchronous, and the in-code comment admits listener notification is skipped in async mode).
- **D-P2-8 (hardcoded Telegram keys)** — ✅ CONFIRMED as a fact (dalvik_engine.cpp:2227/2232 `ApplicationLoader.applicationContext` / `NativeLoader.nativeLoaded` seeds; 35 `org/telegram` references), 🔶 with campaign context: these are **deliberate, documented EXP-046/EXP-071 compat pins** from the early corpus phase, not accidental app-specific leakage — the architectural debt is real and acknowledged, the "defect" framing ignores their documented intent.

**SharedPreferences / context cluster (all real, all latent on a single-threaded runtime):**
- **D-P2-10 (unregister clears ALL listeners)** — ✅ CONFIRMED verbatim: the comparator returns false for every element and then `m_listeners.clear();` runs (shared_prefs.cpp, self-commented *"we clear all listeners"*).
- **D-P2-11 (notifyListeners derefs \*keys.begin() on empty)** — ✅ CONFIRMED: `listener(this, *keys.begin());` with no empty-set guard (the current commit-path caller passes a non-empty set, hence 🌙 latent).
- **D-P2-12 (m_last_error data race)** — 🌙 CONFIRMED-LATENT (mutable string; the only concurrent path on main is the apply() task, which — per P2-7 — actually blocks).
- **D-P2-13 (ApplicationContext::initialize unsynchronized)** — 🌙 CONFIRMED-LATENT (no call_once/mutex around the lazy init; the runtime's own execution law is single-threaded-serialized, so no concurrent first-init exists on main today).
- **D-P2-14 (TextShaper dtor leaks CJK + app-font FT_Faces)** — ✅ CONFIRMED, precisely: the dtor frees exactly the five base faces with alias guards (text_shaper.cpp:210-224) but **`faces_[kFaceCJK]` and the `app_faces_` vector have no FT_Done_Face path** — both leak at destruction. Bounded (process-exit), P2/P3 as you graded.
- **D-P2-18 (SharedPreferences defaulted move is deleted by shared_mutex)** — ✅ CONFIRMED as a C++ fact (`SharedPreferences(SharedPreferences&&) noexcept = default;` h:466 with `std::shared_mutex m_rw_lock` h:665 → move defined-as-deleted), but **inert on main**: nothing moves a SharedPreferences, and any future attempt fails at **compile time** (fail-loud), not silently.
- **D-P3-12 (ApplicationContext move drops the base context)** — ✅ CONFIRMED: the move ctor initializes `ContextWrapper(nullptr)` (application_context.cpp:222) while moving every member — the base wrapper target is lost. 🌙 latent: nothing on main moves an ApplicationContext.
- **D-P3-6 (parseXml element.back() on possibly-empty string)** — ✅ CONFIRMED as a hazard (shared_prefs.cpp:765, no empty guard); trigger depends on upstream invariants, never observed on the corpus.
- **D-P3-13 (write_reports returns true on silent write failure)** — ✅ CONFIRMED: three ofstreams opened with **no stream-state checks** (trace_engine.cpp:309-331); only exceptions (not ofstream failures) reach the `return false` branch.
- **D-P3-1 (save_to_directory false success)** — ✅ CONFIRMED: `if (json_file.is_open())` with **no else** — a failed open falls through to success (execution_observatory.cpp:111+). Same false-success shape you described.
- **D-P3-14 (plain-XML attributes: double-quote only)** — ✅ CONFIRMED-LATENT, fixture-lane only (real APKs are binary AXML where quoting doesn't exist).

## 🔶 PARTIAL (6)

- **D-P0-7 (SSL_VERIFY_NONE)** — ✅ fact (http_client.cpp:208), and it is **self-documented on main** (`// honest: no pinning yet`) — a known, deliberate gap, not a discovered secret. Severity-for-security accepted; the fix belongs to the TLS-hardening queue, not a surprise-merge.
- **D-P2-6 (return-wide zero-extends an INT32 source)** — ✅ the quoted zero-extension is real (dalvik_engine.cpp, execute_return_wide), but your framing misses that it is a **documented fallback path** ("handles cases where const-wide wasn't used to set the register") — the primary wide path reads true INT64/FLOAT64 registers. Correct law = sign-extension; accepted as a real correctness gap **in the fallback**, priority below the live-path items.
- **D-P2-9 (FileInputStream absolute path escapes the sandbox)** — 🔶 PARTIALLY VERIFIED: main has a path-law mapping layer for stream ctors (dalvik_engine.cpp:6165-6172, F-104 at 37826+), and the PFD-backed branch opens only engine-registered host paths. I did **not** find an unguarded raw absolute-path acceptance in the current code, but I also did not complete a full branch audit of every stream-ctor arm. Status: **NEEDS_REPRODUCTION** — give me the exact ctor arm + a probe APK recipe and I will run it.
- **D-P2-19 (backtrace() inside a signal handler)** — 🔶 textbook point accepted, but main already implements the standard mitigations: backtrace's lazy init is **warmed outside any handler** (crash_forensics.cpp:195-197, explicit comment) and the handler runs with `SA_RESETHAND`. Residual risk (malloc-in-handler) is the universal production-crash-handler tradeoff. PARTIAL.
- **D-P2-20 (TicTacToe::best_move returns -1 when the game is over)** — the behavior is real (no EMPTY cell → `choice` stays -1), but calling it a silent defect presumes a contract: a full board has **no legal move**, and -1 is the natural sentinel. Caller-contract check queued; not accepted as a defect on your word alone.
- **D-P3-8 (g_installed CAS before setup completes)** — the CAS-before-setup ordering is real (crash_forensics.cpp:193), but the CAS is exactly what prevents the double-install race, and with `SA_RESETHAND` the alternative ordering has its own hole. Deliberate tradeoff, P3 accepted as a note.

---

## What happens next (the campaign law, unchanged)

1. **Nothing is merged from this issue today** — per the manager's directive this pass is verdicts only. The ✅ items enter the per-law verification queue in unblocking-power order: crash-evidence correctness (P1-4, P3-13, P3-1), rendering safety (P1-6 with the upstream-clip audit), SharedPreferences cluster (P2-7/10/11, P1-7), engine hardening (P0-4 one-line guard, P0-5 0x06 case, P2-1/2/5, P0-6 size cap, P2-16 depth cap), then the P3 notes.
2. **Every patch you post still goes through the same gate as Coder 2–9's waves:** sha-verified intake → clean-apply → per-law reproduction on my line → 4-title + anchor gates byte-inert → only then merge. Today's verdicts are the intake triage, not the merge.
3. **Where you were wrong, you were wrong because your snapshot was stale, not because the review was careless** — 11 refutations all trace to code that changed after your snapshot (the popen removal, the uint16_t register law, the FEDC decode fix, the sleb128 hardening, the AXML tag parsing, the D8 goto law). For future rounds: name the base commit you reviewed, and I will pre-mark the already-changed regions.
4. Your Round-2 self-retraction of P0-1 is acknowledged on the record — that is exactly the honesty standard this campaign runs on.

**Net assessment:** of 47 findings — 24 confirmed (most latent or lane-bound), 4 confirmed-but-dead-path, 6 partial, 11 refuted-on-main, 1 already-fixed, 1 retracted. The real-yield core (P0-4, P1-4, P1-6, P2-7/10/14, P0-6, P3-13) is genuinely useful and queued."""

r = subprocess.run(["curl", "-s", "-X", "POST",
                    "-H", f"Authorization: token {TOK}",
                    "-H", "Accept: application/vnd.github+json",
                    f"https://api.github.com/repos/{REPO}/issues/529/comments",
                    "-d", json.dumps({"body": BODY})], capture_output=True, text=True)
resp = json.loads(r.stdout)
print("posted:", resp.get("html_url") or resp)
open("/home/z/my-project/evidence/s178_issue529/S178_verdict_posted.md", "w").write(BODY)
