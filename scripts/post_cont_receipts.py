#!/usr/bin/env python3
"""Post continuation-wave receipts (#608 chess parse chain, #611 Notepad diagnosis)."""
import json, subprocess, urllib.request

CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project/miniandroid").stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]
H = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json",
     "User-Agent": "layout-audit"}
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"

R608 = """## GAME-185 CONTINUATION — the parse-layer frontier chain: THREE more root causes root-caused + fixed (commit 125f5690), chesslib Board load now REACHED

Picking up from the S83 receipt (rc=0 SUCCESS, 9002 CSV lines read): the frame still showed the empty-state text, so the parse layer was chased one layer deeper. Three independent defects, each proven by a real-APK run on the SHA-pinned APK:

1. **ROOT-1b — the inline static-invoke packer never retyped C/Z/B/S.** The ROOT-1 fix (this issue's §4) lives in the shared `build_invoke_args`; `execute_invoke_static`'s own inline packer handled ONLY the 'F' float-bits case. Kotlin's `split(delimiter: Char)` lowers to `invoke-static String.valueOf(char)` — register word 44 (',') arrived INT32 and `valueOf` answered the string "44": `indexOf` matched nothing, every row collapsed to ONE column, `cols.size() < 5` dropped all 9,000 rows, and chesslib `Board` never initialized. Law: the proto's param char is the only authority for an untyped DEX register word. Evidence after: chesslib class inits **0 → 22** (Board/PieceList walk begins).
2. **ROOT-2b — `Character.isDigit` had NO handler** (the §4 ROOT-2 fix was likewise absent from this tree): the silent stub answered false, so the FEN parser treated the empty-square count digit as a PIECE — `IllegalArgumentException "Unknown piece '8'"` on the first FEN, 20 throws. Law added: isDigit = Unicode Nd (ASCII + Arabic-Indic/Devanagari/Fullwidth), getNumericValue = digit value / 10..35 for letters / -1. Evidence: "Unknown piece" **20 → 0**.
3. **ROOT-2c — framework-boundary hashCode recursed forever.** chesslib's PieceList (Lw1/f;, a LinkedList descendant) inherits AbstractList.hashCode: the element walk re-entered the SAME DEX hashCode → 2048-deep recursion → frame drops at the limit → a spurious NPE at the unwind killed onCreate. Law: a framework-boundary hashCode consult (java/lang/Object or java/util/*) answers the IDENTITY hash (the Fibonacci mix ×2654435761, same as System.identityHashCode) and never re-dispatches into the receiver's own DEX hashCode.

Gates after all three: s246 layout-closure ✓, s247 grid+RTL ✓, **test-all 42/42 PASSED (RC=0)**.

**Remaining frontier (measured):** the LinkedList-shadow node model — the DEX hashCode of a shadow-materialized w1/f node reads an UNSET String field → 20× `NPE "String.hashCode on a null object reference" at Lw1/f;.hashCode pc=10`. The engine's list shadow must initialize the DEX-side fields a real node constructor writes (the same one-model-two-faces family as F-057). After that lands, the 9,000-puzzle repository fills and the Compose board state gate (§6 Canvas frontier) becomes the next surface."""

R611 = """## Notepad CONTINUATION — full root-cause: the launch chain is CLEAN; the stall is the coroutine worker dispatch boundary (measured)

Re-ran F-Droid 3.0.6 (vc 122) on commit 125f5690 and chased the white screen to the end of the chain:

**What is NOT the problem (all verified clean):**
- No uncaught exception anywhere in the run.
- The 4 deferred `ClassNotFoundException`s (`kotlin.reflect.jvm.internal.ReflectionFactoryImpl`, 2× `androidx.datastore.preferences.protobuf.*`) are reflection PROBES with fallbacks — identical behavior on real Android with R8; non-fatal by design.
- `libcore.io.Memory` is okio's zero-fill probe — fallback path exists upstream.
- The absent `files/datastore/settings.preferences_pb` FNFE is the honest first-run state; `throw_deferred` DID find and redirect to the app's IOException catch (`deferred handler` path taken).
- The time-driven capture (`--frames 60`) advanced the virtual clock past the deferred 5873 ms item — the queued Runnable FIRED (`dequeue ... now=5880ms`) and the worker threads ran real DEX.

**The measured stall:** after the file-miss continuation completes, the engine's coroutine worker parks — `[PARK-YIELD] parked worker frame suspended (depth=1, quiescence) at Lz3/a;.run` — the next hop of the DataStore flow (the default-preferences emit back onto Main → `NotepadActivity`'s collect → `setContentView`) is never re-posted to a runnable queue. `NotepadActivity` therefore never calls setContentView at all (`U007-INFLATE` count = 0 across both the plain and the time-driven runs).

**Next wave (single law):** the parked-worker dispatch boundary — when a worker's suspension completes, the engine must re-post the resumed continuation to the target dispatcher's queue (Main/IO handoff), the same family as the compose-pump F-277 poll-timeout law. Once that lands, the collect lambda runs and the note-list workflow the issue scopes starts from an already-dispatched launcher activity."""

for n, body in [(608, R608), (611, R611)]:
    req = urllib.request.Request(BASE + f"/issues/{n}/comments",
        data=json.dumps({"body": body}).encode(), headers=H, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        print(n, "receipt:", json.loads(r.read().decode())["id"])
