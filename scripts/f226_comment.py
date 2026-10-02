#!/usr/bin/env python3
"""F-NEW-222..227 wave — post the §A-§P compact table to issue #354."""
import subprocess


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

BODY = """## F-NEW-222..227 wave — §A–§P audit table + honest white-screen answer

Sandbox commit `bac49b5` is NOT on the repository and the sandbox is gone from the workspace — the 8 sandbox faults were re-derived from live evidence and re-implemented generically (this wave). Nothing was accepted on SHA-change alone: every law carries the full chain (BEFORE → ROOT → FIX → AFTER → 3-RUN → REGRESSION).

### Compact root table

| ROOT ID | FILE | FUNCTION | SYMPTOM | FIRST DIVERGENCE | ROOT CAUSE | GENERIC FIX | TEST | 3-RUN RESULT | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| F-NEW-221 leg | dex/dalvik_engine.cpp | LA/h;.z / c1/d.<init> | Map.get NPE, onCreate dies (R8 merged host) | FIELD-TRACE `b=<unset>` obj#1232 | unbridged `Collections.emptyMap()` → unset register → R8 synthetic ctor stored it | (see F-NEW-222) | 3-run opencalc | superseded by 222 | SUPERSEDED |
| F-NEW-222 | dex/dalvik_engine.cpp | bridge_to_api (Collections) | NPE Map.get on null | c1/d.<init> pc=0x52 move-result | emptyMap/emptySet unbridged → fallback UNSET | route to R-NEW-397 shared singletons (identity sget+method) | opencalc ×3 | rc=0 sha 2291d74de0b6bac5 ×3 | IMPLEMENTED |
| F-NEW-223 | dex/dalvik_engine.cpp | bridge_to_api + File laws | /storage/emulated/0 "does not exist"; onCreate death | Environment REC-MISS; exists()=false | Environment had ZERO handlers; mkdir family was a pretend-true stub creating nothing | virtual volume mount (data_root-backed) + honest creation laws + Environment statics + MEDIA_* seeds | storage probes + goldens | deterministic; goldens byte-identical | IMPLEMENTED |
| F-NEW-224 | framework/view_ancestry.h + dalvik_engine.cpp | normalize_class_desc + ingestion | dotted superclass names broke resolution | hierarchy walk miss | normalizer only handled one spelling | ONE canonical form (4 spellings, idempotent); canonical ingestion at both hierarchy sites | laws130 + goldens | byte-identical ×3 | IMPLEMENTED |
| F-NEW-225a | dex/dalvik_engine.cpp | Field.getGenericType | Gson IAE "<null> is of type null" | e1/d.g ← j1/a.<init> ← f1/m.b pc=0x132 | getGenericType unbridged → null TypeToken | erased-fallback law (never null; = getType() without signature) | opencalc ×3 | rc=0 ×3 | IMPLEMENTED |
| F-NEW-225b | dex/dalvik_engine.cpp | getDeclaredConstructor | NoSuchMethodException for real JDK ctors | LA/h;.z pc=0x94 | framework classes have no DEX body | public no-arg framework ctor minting | opencalc ×3 | rc=0 ×3 | IMPLEMENTED |
| F-NEW-225c | dex/dalvik_engine.cpp + view_ancestry.h | Class.getGenericSuperclass | TypeToken(null) IAE | f1/m.b pc=0x406 | unbridged + JDK collection hierarchy absent | erased law (null only for Object/interfaces) + collection hierarchy edges | opencalc ×3 | rc=0 ×3 | IMPLEMENTED |
| F-NEW-225d | dex/dalvik_engine.cpp | if-eq/if-ne macro | `cls == X.class` never true; loop guard never exits | Gson bound-fields climb past Object | CLASS_REF compared mint ref_ids (fresh per token) | ART one-Class-per-class: compare canonical descriptors | ssw A/B bisect + opencalc | deterministic | IMPLEMENTED |
| F-NEW-226 | dex/dalvik_engine.cpp | TextView.getPaint | TextPaint.measureText NPE (reachable only after 225d) | MyChrono.setFractionView pc=23 | unbridged; old golden SHA encoded a token-identity-masked wrong-branch relaunch | per-view TextPaint identity law | ssw ×3 | rc=0 f48ae6d467d1e746 ×3 REAL UI | IMPLEMENTED |
| F-NEW-227 | dex/dalvik_engine.cpp | Paint.measureText | text metrics unbridged | ssw setFractionView | no handler any overload | 0.5em/char deterministic positive law (paint-size state) | ssw ×3 | deterministic ×3 | IMPLEMENTED |
| §A inherited lifecycle | dex/dalvik_engine.cpp | try_recursive_invoke(+_on_super), invoke-super | — (verification, user §A) | — | local→ancestor walk ≤16 hops; super starts at declaring class (no child recursion) | verified + F-NEW-224 canonical chain; F-NEW-191 attachBaseContext already banked | ssw ShowTime extends StopWatch live chain + goldens | ×3 | TESTED |
| §C/J/K window authority | runtime/execution_engine.cpp | stage_render_frame | — (audit) | — | SmsView/PhoneView/last_setParams render-root heuristics already removed (b0eab647); placeholders = census regions only (diag_owned_pixels=0) | verified, no regression | opencalc census | diag px 0; verdict REAL_APP_CONTENT | TESTED |
| secuso notes grey face | — | — | 97% #303030 dark-theme window + 2.7% blue, no list content | run PARTIAL | not yet root-caused | §I provenance attack next | ×3 | eb5ebd559cad1028 deterministic | PENDING |

### Honest answer to "did any app actually pass white screen" (current HEAD, 3-run proven)

- **opencalc**: rc=0, ZERO uncaught for the first time; frame `2291d74de0b6bac5` = REAL_APP_CONTENT ×3 (digits/text render) — but still **partial**: 91% window-background blue, rows 7-8-9-× and .-0-= missing, layout distribution wrong (§I next frontier, census captured: nodes 48, app_draw_ops 34, app pixels 180772).
- **ssw (simplestopwatch)**: advanced to the ART-correct launcher flow; REAL UI ×3 (`f48ae6d467d1e746`): Start/Delay buttons, gear, hamburger. Old golden `10446aaf` was A/B-proven to encode a wrong-branch relaunch loop masked by broken token identity.
- **uNote**: REAL content ×3 (`4f1a9e4e8f64fae8`): Add note/Search/Quit bar + toolbar.
- **forkgram**: holds REAL_APP_CONTENT; dooz/headingcalc/microtimer/whatsapp byte-identical (zero drift).
- **Why some apps run and these did not (pattern, extended)**: the running family shares SIX laws now — honest clinit bookkeeping (215), real constant identity (216), class-token identity (218+225d), resolve-or-throw reflection (219+225a/b), canonical content parent (220), and this wave's additions: empty-collection factories (222), storage volume honesty (223), descriptor canonicalization (224), generic-supertype family (225a-c), view-paint identity (226).

### Gates
laws130 51/51; opencalc/unote/secuso/ssw ×3 deterministic rc=0; dooz MATCH-GOLDEN; headingcalc/microtimer/whatsapp byte-identical; registry 516→522; commit `e6c522e4` pushed to main.

### Remaining frontier (next batch)
secuso grey-face §I provenance; opencalc missing button rows (7-8-9-×, .-0-=) + layout distribution; F-NEW-225 Signature/ParameterizedType parsing leg; F-NEW-227 shaper-integrated metrics; F-NEW-204..207 P1 batch; F-NEW-217 kotlinx resume; F-NEW-221 R8 merge-model deep leg; §L multi-activity capture authority verification.
"""


def main():
    tok = token()
    import json
    payload = json.dumps({"body": BODY})
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "-H", f"Authorization: token {tok}",
        "-H", "Accept: application/vnd.github+json",
        "-d", payload,
        f"https://api.github.com/repos/{REPO}/issues/354/comments",
    ], capture_output=True, text=True)
    import json as j
    try:
        resp = j.loads(r.stdout)
        print("comment id:", resp.get("id"), "url:", resp.get("html_url"))
    except Exception:
        print("RAW:", r.stdout[:500])


if __name__ == "__main__":
    main()
