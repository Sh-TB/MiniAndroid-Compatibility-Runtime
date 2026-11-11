# A-R3 — KNOWLEDGE TRANSFER: the post-A-R2 orphan families (roadmap §89 CI · §87 CG · §33 AE · §36 AH · §90 CJ) — first-ever review, 5 findings (R14–R18), exact fix locations, verify commands; plus the forgotten-work ledger (stranded R1–R5 delivery, rejected-hunk residue)

> **Purpose:** Continue the review work that was never done. A-R1 (issue #576) transferred the first review of §30/§32/§37/§39/§44; A-R2 (issue #578) of §15/§27/§40/§88/§91. The tag scan below shows the roadmap still holds **five more technical families with no owning lane and no executed checklist** — §89 (initialization order), §87 (cache/lifetime — the family A-R1 explicitly deferred as "genuinely unowned" and A-R2 did not pick up), §33 (file/stream/buffer APIs), §36 (native/JNI boundary inventory), §90 (version qualifiers). This issue transfers their first actual review, and closes the loop on two forgotten-work items: the **stranded R1–R5 delivery** (committed locally on `bdf777d9`, never pushed — origin/main contained none of it) and the **rejected-hunk residue** (three `.rej` files, 697 lines, committed to the tree since the S188/S196 merge). Audit-first: findings are code-read and line-cited at one frozen HEAD so they can be ACCEPTED/REJECTED without re-derivation; the landable cumulative patch (R1–R5 re-based + the S211 KT interpreter transfer) is in issue #577's comments per K-2.

**Base commit reviewed:** `6619c34a` (current `origin/main`, `git ls-remote`-verified 2026-11-11; the S211 Segment-forensics HEAD — which itself contains NONE of the R1–R5 laws until the #577 cumulative patch lands).

**Method:** (1) roadmap §3–§92 status-tag census on the current issue-#9 body (machine-counted, script in §5) → every family's item state; (2) lane-ownership map from the issue tracker (Coders 2–9 + Coder D + main-coder S-sessions); (3) registry cross-check per family subject; (4) line-cited code review of each orphan family; (5) corpus grep censuses for §33/§36/§90; (6) git-archaeology pass for forgotten-work items (unpushed local commits, `.rej`/`.orig` residue, gate-marker absence).

---

## 1. Why these five families are the never-reviewed set (reasoning, not assertion)

Tag census of the current roadmap body (reproducible script in §5):

| Roadmap family | Checklist state at #9 | Registry / lane cross-coverage | Lane owner | Why it matters |
|---|---|---|---|---|
| §89 CI initialization order | **procedure, zero items — never executed** ("Many 'random' failures are initialization-order failures") | `<clinit>` laws exist per-app (F-NEW-215 honesty, F-NEW-395/470 unwind, S123/R-NEW-421 namespace) — all **demand-driven singles; no family closure** | **none** | every app boot; Application/ContentProvider/Activity ordering |
| §87 CG cache/lifetime | **procedure, zero items** — A-R1 deferred it ("CG (§87)/CH (§88) remain genuinely unowned"); **A-R2 covered CH only** | boxing caches (correct), theme rebind (F-NEW-484), S124 theme-base — scattered, no family audit | **none** | every cache: creation/lookup/invalidation/config-change/lifecycle/identity |
| §33 AE file/stream/buffer | **12 items bare `[ ]`, 2 done** (`UTF-8 [T]`, `MUTF-8 [RV]`) | LOADING-CAMPAIGN + CONT-102/CONT-49 stream laws — per-idiom singles (InputStream.read, BAOS, BufferedReader.readLine, String ctors) | **none** (Coder-9 owns resources/assets/image, not java.io) | every app that reads assets, decodes bytes, or streams |
| §36 AH native/JNI boundary | **7 items bare `[D]`, 1 done** (`SQLite [T]`); the demanded INVENTORY+CLASSIFICATION never produced | W10/W18 (conscrypt natives), S136 (GLES), S185 (SQLite rule), GATE A loadLibrary contract — lanes recorded per-family work, **the AH table itself never written** | **none** (Coder-6 consumes GL; A-R1 covered AI=method semantics, not AH=boundary inventory) | every APK shipping a real `.so` |
| §90 CJ version qualifiers | **procedure, zero items** | per-app install records DO carry minSdk/targetSdk (e.g. `evidence/s207/runs/store_s208_dooz_ng2/.../io.github.yamin8000.dooz/package.json`: `minSdk 24 / targetSdk 37`) — but the engine side was never started | **none** | every behavior that AOSP gates on targetSdk |

Every other technical family has an owning lane, a closure record, or a registered boundary (A-R1 §1 + A-R2 §1 tables; this census adds the five above as the remaining orphans). That is the derivation, and it is checkable with the §5 commands.

---

## 2. Findings

Status vocabulary per K-6. Each finding: **VERIFIED (code-read, line-cited at `6619c34a`)**; fix status **PENDING**; fix location stated exactly; verify command executable per K-4. Numbering continues A-R2's R13.

### R14 — FAMILY CI: `ensure_class_initialized` has NO superclass-first initialization law (P1)

**Where.** `miniandroid/src/dex/dalvik_engine.cpp:6330` — `ensure_class_initialized()` spans ~6330–6700 and handles: F-NEW-215 erroneous-class honesty, the framework-skip namespaces (G12/M3/S123 laws), the static-default bake (EXP-062, F-028f/F-042), the `<clinit>` dispatch via `try_recursive_invoke(class_descriptor, "<clinit>", …)` (`:6595`), and the F-NEW-395/470 unwind-attribution laws. **Across its entire body and all 25 call sites, no call ever initializes the DIRECT SUPERCLASS first.** The engine already builds `class_to_superclass_` (EXP-068, `dalvik_engine.h:2632`; probe-visible "[EXP068] Built class→superclass map: N entries") and walks it for semantic ancestry (`dalvik_engine.cpp:1363`) — the data is present; the **ordering law is not applied at class-init time**.

**Law (Tier 1).** JVMS 5.5 / AOSP `ClassLinker::EnsureInitialized`: initializing class C requires C's direct superclass to be initialized FIRST (recursively); a `<clinit>` that throws leaves the class erroneous (already law, F-NEW-215). Observable divergence at HEAD: a superclass whose `<clinit>` has side effects (registration singletons, `static int[]` tables consumed reflectively, counters) never runs until the subclass *actively references* a superclass member — on ART it runs at subclass-init time. Any app whose superclass `<clinit>` publishes state consumed via reflection/`Class.forName` paths sees a different world than on ART.

**Consequence at HEAD.** The re-entrancy guard (`initialized_classes_.insert` BEFORE `<clinit>`, `:6467`) correctly handles same-thread cycles A→B→A, so the missing superclass walk does not deadlock — it silently reorders. 11 insert sites exist; none walks the chain upward.

**Verify (K-4).**
```
git grep -n "ensure_class_initialized(super" miniandroid/src/ | wc -l        # 0
git grep -n "initialized_classes_.insert" miniandroid/src/dex/dalvik_engine.cpp | wc -l   # 11
# read :6330–6700 — the only recursive init is the class's OWN <clinit> at :6595
```
**Fix location.** One block at the top of `ensure_class_initialized` after the erroneous-class gate: resolve `class_to_superclass_[normalized]`, and if the superclass is in the app DexReport, `ensure_class_initialized(super)` before the static-default bake. Framework-namespace superclasses keep the platform-skip. Corpus relevance: every app whose base classes carry static state (AppCompat chains, libGDX `AndroidApplication`).

### R15 — FAMILY CG: first cache/lifetime audit — one cross-engine identity hazard, one unbounded cache, two verified-good records (P2 / P3)

§87's demand is an audit of every cache over creation/lookup/invalidation/configuration-change/lifecycle/identity. First pass at HEAD:

- **R15a — `st_cache` is a process-global `static` holding heap object ids (P2).** `android_shadows.cpp:8712` — `static std::map<int32_t, uint32_t> st_cache;` inside the `ImageView$ScaleType` getter, guarded only by `heap_->has_object(it->second)`. In any process that constructs **more than one engine/heap** (the megabatch lanes, probe harnesses, the sequential-app pattern the repo itself documents in `resource_runtime.cpp:703` "the sequential-app isolation requirement"), deterministic heap ids from run N pass the `has_object` guard in run N+1 and the getter returns **run N's object** — a cross-run identity leak of the exact "identity/lifecycle" shape §87 asks to hunt. Single-app-per-process harnesses are unaffected (honest boundary).
- **R15b — `asset_bytes_cache_` is unbounded (P3).** `dalvik_engine.h:4037` — every streamed asset is cached for the process lifetime with no size cap or eviction. A large-asset corpus app (audio/video fixtures) grows RSS monotonically. Classification row: intentional-for-determinism is fine, but the row was never recorded.
- **Verified-good records (close two §87 rows):** (1) boxing identity caches are AOSP-correct — `char_box_cache_` bounded `cp <= 127` and `int_box_cache_` bounded `-128..127` (`dalvik_engine.cpp:82649`, `:82667`), so `Integer.valueOf(1000) == Integer.valueOf(1000)` cannot alias; (2) theme invalidation EXISTS — F-NEW-484 setTheme rebind (`dalvik_engine.cpp:63003` region) + S124 rebind law, and `application_theme_resid()` (`resource_runtime.cpp:711`) caches an immutable manifest value. These need only CH/CG-table rows, not code.

**Verify (K-4).**
```
grep -n "static std::map<int32_t, uint32_t> st_cache" miniandroid/src/framework/android_shadows.cpp   # 8712
grep -n "asset_bytes_cache_" miniandroid/src/dex/dalvik_engine.h | head -1                            # 4037
grep -n "bv >= -128 && bv <= 127" miniandroid/src/dex/dalvik_engine.cpp | wc -l                       # 2 (both box caches bounded)
```
**Fix location.** R15a: key the cache by `(heap_generation, ord)` or move it to an engine member (the getter already receives the engine context); R15b: one `MAX_ASSET_CACHE_BYTES` gate with LRU-evict or a recorded "no-eviction, bounded-by-corpus" classification row in the roadmap.

### R16 — FAMILY AE: first stream census — the decode/encode charset asymmetry + the unowned base classes (P2)

Measured at HEAD (whole-engine grep, exact-class strings):

- **R16a — `new String(bytes, charset)` decodes EVERYTHING as UTF-8 (P2).** The decode ctor (`dalvik_engine.cpp:80542` "LOADING-CAMPAIGN: String(byte[]) / String(byte[], String charset) / …", body ~`:80797–80863`) treats the source bytes with the UTF-8 host convention **regardless of the charset argument** — there is no UTF-16/ISO-8859-1/US-ASCII decode branch. Meanwhile the ENCODE side is real: `getBytes` (`:80616`) implements UTF-16/UTF-16BE/UTF-16LE with correct surrogate pairs. **Asymmetry:** `s.getBytes("UTF-16")` → `new String(thoseBytes, "UTF-16")` produces mojibake, silently. A round-trip property test (`new String(s.getBytes(cs), cs).equals(s)`) fails for every charset except UTF-8.
- **R16b — family census table (the §33 deliverable, first pass):**

| AE item | State at HEAD | Evidence |
|---|---|---|
| InputStream `[T]` | PARTIAL (asset-backed real arms) | `:10620` read/available/close with read(b)→read(b,0,len) law `:10676` |
| OutputStream `[T]` | PARTIAL | BAOS family CONT-49 (`:41368`) |
| Reader `[T]` | **0 exact-class hits** | `Ljava/io/Reader;` = 0 |
| Writer `[T]` | **0 exact-class hits** | `Ljava/io/Writer;` = 0 |
| ByteArrayInputStream `[T]` | **0 hits** | census |
| BufferedInputStream `[T]` | **0 hits** | census |
| BufferedReader | real (readLine) | `:10479`/`:6782` |
| StringReader/StringWriter | present | 1 hit each (LOADING-CAMPAIGN) |
| ByteBuffer `[T]` | real arms | `:37162`, `:53194` |
| Charset `[T]` | real forName arm + alias table | `:57049` |
| UTF-8 `[x]` / MUTF-8 `[x]` | done (pre-ticked) | DEX layer |
| UTF-16 `[T]` | **encode real, decode MISSING** | R16a |

- **R16c — stream convenience idioms absent:** `readAllBytes` / `transferTo` → **0 hits**; every caller idiom that uses them falls to the bridge tail's typed default. `java.io` bulk-read APKs (JSON/config loaders) are the consumer class.

**Verify (K-4).**
```
for s in "Ljava/io/Reader;" "Ljava/io/Writer;" "Ljava/io/ByteArrayInputStream;" "Ljava/io/BufferedInputStream;" readAllBytes transferTo; do printf "%-34s %s\n" $s $(git grep -cF "$s" -- miniandroid/src/dex/dalvik_engine.cpp); done   # all 0
# decode-side: read :80797–80863 — no charset branch exists
```
**Fix location.** R16a: one decode branch beside the UTF-8 decode in the F-NEW-358 arm honoring `__charset_name__` (the alias table at `:57058` already canonicalizes); R16b/c: AE-table rows in the roadmap + the two convenience idioms as tiny arms beside `:10676`.

### R17 — FAMILY AH: the demanded native-boundary INVENTORY+CLASSIFICATION, first pass — plus the rejected-hunk residue still sitting in the tree (P1 for the unapplied resolution law, P2 for the table)

**R17a — the AH `[D]` classification table, first pass (documentation deliverable):**

| AH candidate | State at HEAD | Where |
|---|---|---|
| SQLite `[x]` | done (S185 RULE: vend-don't-rework, real sqlite3) | `storage/sqlite_shadow` |
| crypto | real (conscrypt natives registered & marshaled) | W10/W18 laws |
| compression | real (zlib — APK/zip layer) | `apk/` |
| graphics | real software GLES + translation | S136, `gles/pgl_backend` |
| audio | real decode stack (mpg123/sndfile linked; `audio/audio_engine.{cpp,h}`) | S206-era |
| WebView | real DOM/QuickJS engine | `webview/webview_engine` |
| libc-like | real bionic compat | `jni/bionic_compat.c`, `jni/pthread_shadow` |
| library load boundary | GATE A loadLibrary contract + sha16 identity | `dalvik_engine.cpp:83234`, `dlopen_exec.cpp` |

**R17b — the `.rej` residue (P1):** the tree carries **three committed rejected-hunk files** since commit `74d7693a` — `miniandroid/src/dex/dalvik_engine.cpp.rej` (642 lines, 5 hunks), `miniandroid/src/jni/dlopen_exec.cpp.rej` (45 lines, 2 hunks), `miniandroid/src/jni/dlopen_exec.h.rej` (10 lines) — and per-hunk status at HEAD:

| Rejected hunk | Status at `6619c34a` | Evidence |
|---|---|---|
| F-NEW-583 JNI `$`→`_00024` mangle (`dlopen_exec.cpp.rej` hunk 2) | **SUPERSEDED by a better law** — F-NEW-611 general Unicode-escape mangle `_0%04x` (covers `$`=0x24 and all others) | `dlopen_exec.cpp:1431–1452` |
| F-NEW-582 direct-buffer slots 229–231 routing to `f582_*` (hunk 1 + `.h.rej`) | **PARTIALLY superseded** — the engine-side F-NEW-582 mint exists (`dalvik_engine.cpp:776–810`); the JNI-table routing arm is unapplied, impact low | grep `f582_` in `dlopen_exec.cpp` = 0 |
| **F-NEW-584 EXACT-DESCRIPTOR native resolution (`dalvik_engine.cpp.rej`, incl. the +457-line hunk)** | **UNAPPLIED — 0 hits.** The live dispatch is still name-only ("first ACC_NATIVE method with the requested name", `try_recursive_invoke` native_hit block). The rej's own live face stands: `FreeType$Library` declares BOTH `newMemoryFace(JLjava/nio/ByteBuffer;II)J` (native) and `newMemoryFace(Ljava/nio/ByteBuffer;I)LFace;` (wrapper); name-only dispatch can hand the WRAPPER's shape to the native body | `git grep -c "F-NEW-584" miniandroid/src/dex/dalvik_engine.cpp` = 0 |

**Verify (K-4).**
```
git ls-files | grep -E "\.(rej|orig)$" | wc -l                     # 3
git grep -c "F-NEW-584" -- miniandroid/src/dex/dalvik_engine.cpp   # 0
git grep -c "F-NEW-611" -- miniandroid/src/jni/dlopen_exec.cpp     # ≥1 (supersession proof)
```
**Fix location.** (1) Delete the two superseded/partial files after recording their status (hygiene — they have been misleading merge archaeology since S188). (2) Re-apply F-NEW-584 as a fresh law on current HEAD: in the `try_recursive_invoke` native resolution, when the caller passes a descriptor, dispatch the native ONLY when the invoked descriptor IS the native's (the rej text is intact in `dalvik_engine.cpp.rej` hunk 1 and can be `git apply --3way`-ed onto a fresh base); the +457-line hunk needs line-by-line re-review against the post-S195/S196 engine before landing. PENDING; nothing landed in this wave.

### R18 — FAMILY CJ: the record half exists, the gate half was never started (P2)

**Where.** `manifest_target_sdk_`/`manifest_min_sdk_` are parsed and mirrored to `ApplicationInfo` (`dalvik_engine.cpp:71006–71008`) — and that is their ONLY use: **0 behavioral gates** on either value exist anywhere in the engine (`manifest_target_sdk_ >` / `>=` / `<` comparisons = 0 hits). The per-app RECORD half of §90 exists (install `package.json` files carry `minSdk`/`targetSdk` — e.g. dooz `24/37`), so the census substrate is present; what never happened is (a) any behavior keyed on the version qualifiers (AOSP examples: runtime-permission model at 23, background limits at 26, scoped storage at 29+, precise-alarm gates at 31+) and (b) the "behavioral version differences" rows per corpus app.

**Law (Tier 1).** AOSP `AppGlobals.getCurrentTargetSdkVersion()`-gated behaviors; `Build.VERSION_CODES` branching inside platform code. The runtime's honest current boundary is "targetSdk-blind" — which is FINE as a recorded classification, but §90 demands the record, and it does not exist.

**Verify (K-4).**
```
git grep -n "manifest_target_sdk_" -- miniandroid/src/dex/dalvik_engine.cpp | wc -l   # 4 (parse+mirror only)
git grep -cE "manifest_target_sdk_(>|>=|<)" -- miniandroid/src/dex/dalvik_engine.cpp  # 0
```
**Fix location.** One classification row per §90 bullet in the roadmap (record exists / gate absent), and — only when a corpus app demands it — the first explicit gate with the CJ-record residency (`package.json` fields already parsed at install).

---

## 3. Forgotten-work items this transfer closes or re-flags (not duplicated from A-R2 §3)

1. **CLOSED (transfer complete): the stranded R1–R5 delivery.** The S211 A-R1 implementation was committed locally on the `bdf777d9` lineage and NEVER PUSHED — `git ls-remote origin main` was `6619c34a` and `origin/main` contained **0** occurrences of the R1 law marker (`JNI-PENDING`). S212 re-based it onto `6619c34a` (clean → `9f5d6313`), re-gated it (`ar_probe` 15/15 ×2, `make test` 4/4), and transferred the full cumulative diff `6619c34a`→`1986d55a` (sha16 `b7d5372ba5fe8018`, `git apply --check` CLEAN) **in 3 parts on issue #577** per K-2 (this lane's token is Issues:RW; push denied 403 — K-3 respected).
2. **CLOSED (transfer complete): the S211 KT interpreter patch (#577).** Its 300-line diff (sha16 `9f1f7ddef39e1179`) is included byte-identical in the cumulative transfer; gates on the integrated tree: `mwr_opcode_probe` 5/5, `make test` 4/4, `ar_probe` 15/15 ×2.
3. **RE-FLAGGED: A-R2's R6–R13 remain unimplemented on `6619c34a`** (spot-checked: `getOutputStream` 0, `LifecycleRegistry` impl 0 (comments only), `HTTP_MODE`/`HTTP_MOCK` 0, `invalidateSelf` 0). P0 R9 (silent POST-as-GET) is still the top open risk.
4. **RE-FLAGGED: W21 part 17/17 still missing on main** (`F720`/`F-720` markers 0 hits on `origin/main`) — the integration BLOCKED state from #575 stands.
5. **PROGRESS NOTED: #573's ladder laws have landed** (`F-C4-613` = 7 hits on `origin/main`) — that audit-queue item from S209 can be closed by the main coder.
6. **NEW (this issue): the `.rej` residue** — see R17b.

---

## 4. Roadmap reconciliation proposed (issue #9 living doc)

| § | Family | Current tag state | Proposed after this review |
|---|---|---|---|
| 89 | CI initialization order | procedure, never executed | `[~]` — first audit delivered (R14: superclass-first law absent, 11 insert sites audited); fix PENDING |
| 87 | CG cache/lifetime | procedure, never executed | `[~]` — first audit delivered (R15): st_cache identity P2, asset cache P3; boxing + theme invalidation rows CLOSED as verified-good |
| 33 | AE file/stream/buffer | 12×bare `[ ]` | `[~]` — census delivered (R16): Reader/Writer/BAIS/BIS/idioms 0-hit rows; decode/encode asymmetry P2 |
| 36 | AH native boundary | 7×bare `[D]` | `[~]` — classification table delivered (R17a); F-NEW-584 re-apply P1; `.rej` hygiene row |
| 90 | CJ version qualifiers | procedure, never executed | `[R]` — record-half verified present, gate-half = 0; classification rows proposed (R18) |

---

## 5. Family-orphan derivation, reproducible (K-4)

```
# every candidate family's items are bare [ ] (or the section is a never-executed procedure):
python3 - <<'EOF'
import re
body = open('roadmap_issue9.md').read()   # issue #9 body fetched 2026-11-11
for num in [33, 36]:
    m = re.search(rf'(?ms)^# {num}\. FAMILY [A-Z]+ — .+?(?=^# \d+\. |\Z)', body)
    sec = m.group(0)
    print(num, 'bare:', len(re.findall(r'\*\s*\[ \]', sec)), 'done:', len(re.findall(r'\*\s*\[x\]', sec)))
for num in [87, 89, 90]:
    m = re.search(rf'(?ms)^# {num}\. FAMILY [A-Z]+ — .+?(?=^# \d+\. |\Z)', body)
    print(num, 'items:', len(re.findall(r'\*\s*\[', m.group(0))), '(procedure section)')
EOF
# expected: 33 bare:12 done:2 · 36 bare:7 done:1 · 87/89/90 items:0
# lane-ownership cross-check: no "Coder N" issue in the tracker claims §87/§89/§33/§36/§90
#   (coder lanes: 2=corpus, 3=legacy-exec, 4/5=4APP, 6=hardest, 7=components, 8=concurrency, 9=resources/assets/image)
```

---

## 6. K-7 self-check

- [x] base commit stated and real on `origin/main` (`6619c34a`, `ls-remote`-verified 2026-11-11)
- [x] the wave's landable patch is attached — cumulative diff in 3 parts on #577 (K-2: base/tip/lines/sha16 + CLEAN apply-check stated there); this issue adds no new code claims without locations
- [x] verify commands are executable text with expected outputs (K-4); every grep executed at the frozen HEAD before posting
- [x] every finding carries an honest status (K-6): all VERIFIED / fixes PENDING; superseded hunks marked SUPERSEDED, not "missing"
- [x] English only (K-5)
- [x] signed with lane identity below; no duplicate findings — A-R1 (#576) covered §30/§32/§37/§39/§44, A-R2 (#578) §15/§27/§40/§88/§91; the five families here are the remaining orphans; forgotten-work items #3–#5 referenced, not re-audited
- [x] the §33/§36 family tables (the families' own demanded deliverables) are included, not just referenced

**Requested from the main coder:** verdict per finding (ACCEPTED / REJECTED / PARTIAL / NEEDS REPRODUCTION with reasons, per the #382 protocol), then lane assignment. P1: R14 (superclass-first init), R17b (F-NEW-584 re-apply + `.rej` hygiene). P2: R15a, R16a, R18. P3: R15b.

— Review lane (continuing the A-R series: A-R1 #576 → A-R2 #578 → A-R3; user-directed audit; Issues:RW token, no contents written per K-3)
