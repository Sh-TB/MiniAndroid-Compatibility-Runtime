#!/usr/bin/env python3
"""Post the F-NEW-197 wave-2 + campaign-registration progress comment."""
import json, subprocess, sys

def gh_token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None

BODY = """## F-NEW-197 WAVE 2 (SUCCESS-PATH methodology) + campaign registration

**Scope:** three new user mandates registered in the worklist
(SUCCESS-PATH FIRST, SUCCESS-FIRST COMPATIBILITY, SECONDARY DEEP AUDIT)
+ F-NEW-197 attacked. Registry **492 → 509** (F-NEW-198..214). Worklist 728
items (open 284). Commit: this commit.

### NEW WORKLIST ENTRIES (user mandates, generic only)

| ID | ITEM | STATUS |
|---|---|---|
| F-NEW-198 | DEEP-AUDIT P0-1 ApplicationRuntime legacy path (site-level probe list) | PENDING (V8 partial) |
| F-NEW-199 | DEEP-AUDIT P0-2 ArchTaskExecutor background execution (Runnable must execute) | PENDING **P0** |
| F-NEW-200 | DEEP-AUDIT P0-3 STUBBED+true truth contract (EXECUTED_WITH_STUB) | PENDING (partial) |
| F-NEW-201 | DEEP-AUDIT P0-4 canonical window identity extended proofs (ComposeView/subDecor) | PENDING (F-NEW-183 base) |
| F-NEW-202..207 | DEEP-AUDIT P1-5..P1-10 (settle split, thread-identity, bounded logging, ViewTree owner, AOSP second-pass, final visual gate + 45px regression) | PENDING |
| F-NEW-208..214 | SUCCESS-PATH corpus/signature/clusters/authority-accounting/upstream-source/high-fan-out ranking/protection regression + logs-as-data | PENDING |

### F-NEW-197 — SIX GENERIC LAWS IMPLEMENTED+TESTED

Target: opencalculator vc53 (first F-NEW-197 face). Full methodology chain
per law (source-first DEX disassembly → runtime trace → generic law →
3-run regression). No package/class/title-specific branches.

| # | LAW | FACE CLOSED | EVIDENCE |
|---|---|---|---|
| 1 | **TypedArray stale-presence**: recycled-singleton TypedArray; presence written UNCONDITIONALLY per slot (AOSP TypedArray.obtain rewrites every slot) | presence leak across obtainStyledAttributes calls → getInt answered 0 | `[F175-READ]` present=1 stored=0 (stale) → present=0 honest |
| 2 | **XML-AttributeSet precedence**: obtainStyledAttributes resolves XML AttributeSet → style → theme → caller default (AOSP AttributeResolution order); inflater passes parsed AXML attrs via the ctor hook | `SlidingUpPanelLayout.setGravity` ISE "gravity must be set to either top or bottom" | `[F175-READ] getInt idx=0 stored=48 present=1 answered=48` (Gravity.TOP from XML; absent slots honor defaults) |
| 3 | **Config-context**: `createConfigurationContext` never null (AOSP ContextImpl), fresh object per call, dual-view dispatch, base-context recorded | AppCompatActivity attach chain NPE (`pc=180 createConfigurationContext → pc=184 .getResources()` — f141 family) | attach chain completes; NPE gone |
| 4 | **New-theme**: `Resources.newTheme()` non-null | ContextThemeWrapper.getTheme `mTheme.setTo()` NPE | Ll/c;.b pc=26 gone |
| 5 | **Class-token getClass**: `Object.getClass` on CLASS_REF answers `Ljava/lang/Class;` (never null) | Gson `type.getClass().getName()` probe NPE | `[F088]` miss → 0 |
| 6 | **Class-token instanceof**: CLASS_REF (ref_id==0) = the Class token; desc-only OBJECT_REF classifies by descriptor | token misclassification family | law text in registry |

**Honesty:** opencalc uncaught-in-flight exceptions **3 → 1**. Remaining
faces (registered inside F-NEW-197, machine-readable): (A) generic-type
reflection family — `getGenericSuperclass` / `getActualTypeArguments` /
`getRawType` UNBRIDGED → Gson TypeToken IAE in onResume (INSTANCEOF-DIAG
proved the argument register arrives degenerate); (B) tree-build gap —
frame still the shared empty-shell SHA `b5a7a35d5fe0564b`
(DEFAULT_BACKGROUND_ONLY).

### GATES (zero regressions)

- laws130 **51/51**
- goldens ×3 **BYTE-IDENTICAL**, exact SHAs: dooz `d602648e8e401895` · ssw
  `10446aaf0cd642cc` · headingcalc `be1cea9cf994b26a` · microtimer
  `da73010a37dd0189` · whatsapp `31ddd4d5b8e6d18e`
- opencalc ×3 deterministic `b5a7a35d5fe0564b`

### DONE / REMAINING

- **Done this batch:** 17 campaign entries registered; 6 generic laws
  implemented+tested; 3 kill-chain faces closed; registry 509; worklist 728;
  all gates green.
- **Remaining:** F-NEW-197-A type-reflection family (next probe), 197-B
  tree-build gap; F-NEW-199 (P0) ArchTaskExecutor background execution;
  F-NEW-198/200..207 deep-audit items; SUCCESS-PATH corpus F-NEW-208..214;
  main-campaign PHASE 4–20 + item 22 + Wave C continuation per mandates.
"""

def main():
    token = gh_token()
    if not token:
        print("NO TOKEN"); sys.exit(1)
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/354/comments",
        "-H", f"Authorization: token {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"body": BODY}),
    ], capture_output=True, text=True)
    try:
        resp = r.json()
        print("posted:", resp.get("id"), resp.get("html_url"))
    except Exception:
        print("FAIL", r.stdout[:300])

if __name__ == "__main__":
    main()
