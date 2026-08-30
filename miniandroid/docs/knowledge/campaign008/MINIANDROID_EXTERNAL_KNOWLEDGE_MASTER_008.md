# MINIANDROID EXTERNAL KNOWLEDGE MASTER — UNIFIED_008

Campaign type: OPEN SOURCE FIRST / GITHUB DEEP MINING / REAL APK COMPLETION.
Baseline: UNIFIED_007 (00921c9). Solo principal coder, reuse-first discipline.

## 1. The one-paragraph result

This campaign achieved **acceptance jump A** (charter §44): a real F-Droid
APK (GM Dice) now completes a full interactive user journey — real UI built
from its own resources, real touch, real DEX execution through its dice-logic
(class hierarchy, arrays, string parsing, PRNG, formatting), real visible
state change per tap, per-tap screenshots — while Telegram stayed
byte-identical across all five stage captures and gained real ARSC string
values on the SMS screen. Alongside: 119 open-source candidates verified
(114 by commit), four tools adopted (two as runtime-data oracles), SwiftShader
configured (compile blocked by env RAM), and the custom-code surface
documented so every remaining hand-written piece is justified.

## 2. The four root causes behind the "instance-array plumbing" blocker

UNIFIED_007 left gmdice's visible state change FAILED with a vague
"instance-array value integrity" note. The reality — found only by
disassembling the DEX with the adopted androguard oracle and instrumenting
the interpreter — was FOUR stacked defects, none of them where the note
pointed:

1. **array-length register decode**: format-12x source register read
   `bits 4-7` (the OPCODE's high nibble — always `2` for opcode 0x21)
   instead of `bits 12-15`. Every `array-length` in every app read register
   v2. Effect: onCreate's `button_ids` loop exited immediately → the four
   dice buttons never received listeners → the journey could only ever tap
   the "more" button → AlertDialog dead-end.
2. **Same nibble leak** in `add-int/2addr`, `add-int/lit16`, wide-2addr and
   `move-wide` (`src = instr & 0xF` = opcode low nibble!). Dice sums, loop
   counters, and long math were computing against the wrong registers.
3. **Dice-notation parsing chain**: `getDiceSet("1d6+4")` is a real parser —
   `String.split("[d+-]")` (regex class!), `Integer.parseInt`,
   `String.indexOf` — plus `CharSequence.toString()` across an
   invoke-interface, which returned NULL. Every one was missing or broken.
4. **Formatting + PRNG**: `String.format` stripped `%` specs ("3d20"→"d"),
   `Integer.valueOf` returned empty boxes, and `Random.nextInt` was stubbed
   0 — so even after the loop fix, buttons showed wrong labels, lookups
   failed, and every roll rendered identically ("1 ·1 ·1"), pixel-identical.

Plus a **fifth, systemic** one: the per-method execution throttle (10 calls)
silently disabled app methods mid-journey — proof that interactive journeys
need repeat execution, not just startup reachability.

Lesson recorded: state-change failures in a bytecode interpreter are rarely
where the stack trace points; an independent oracle disassembly is the
fastest path to truth.

## 3. Reuse-first results (§2/§45 honored)

- ARSCLib V1.4.0 (Apache-2.0): downloaded, CLI built with downloaded Temurin
  JDK, gmdice table dumped → **cross-validated MiniAndroid's ARSC parser
  exactly** (8 types/73 entries). Decision: AUGMENT (oracle), not replace.
- Apktool 3.0.3: decode ground truth for string values.
- androguard 4.1.4: **production adoption** — ARSCParser generates the
  runtime's resource value cache (11,314 Telegram strings). This converted
  UNIFIED_007's PARTIAL (names instead of values) into PROVEN ("Enter code"
  on the SMS screen).
- SwiftShader: cloned, **cmake configure SUCCEEDED**, compile blocked by
  3GB RAM — precise, tested blocker; build recipe recorded for a 16GB host.
- git ls-remote as the API-free GitHub verification channel (114/119 repos
  commit-verified).
- Rejected with reasons: 22 entries including license-kill (ultralight) and
  wrong-abstraction (Flutter/bgfx/sokol for soft-GLES).

## 4. Dooz — the honest verdict

Dooz is pure Compose: 2,189 methods / 446 classes touching androidx.compose
(runtime/ui/foundation/material3), zero XML layouts. The campaign fixed no
View-system bug that would make it render. The architecture bridge
(Composer/SlotTable/Material3 painters on the software renderer) is
documented with machine-generated facts; dooz_02–05 remain NOT_PROVEN rather
than being faked — the depth-first rule chose the Golden jump.

## 5. Process discoveries

- A scripted refactor once deleted 9.4k lines via a duplicated marker —
  recovered from git in one command; rule added: never splice by
  non-unique markers; verify with `git diff --stat` immediately.
- The corpus regression practice of "rebuild the TRUE baseline in a
  worktree" settled two suspicious deltas (microtimer exit-1, dooz +71%
  runtime) as pre-existing/expected — regressions must be proven against
  the baseline binary, not remembered from notes.
- GitHub's unauthenticated API quota is a trap in shared-IP environments;
  git-protocol ls-remote is the reliable discovery primitive.

## 6. Status snapshot (full: status.json)

golden=PROVEN · telegram=PROVEN · arsc=PROVEN · layout=PROVEN ·
fonts=PROVEN · touch=PROVEN · audio=PROVEN · 3D=PROVEN · browser/API=PROVEN
· dooz=PARTIAL · corpus=PARTIAL · backgrounds=PARTIAL · crash/hang=PARTIAL
· GLES=BLOCKED (env memory; recipe recorded)
