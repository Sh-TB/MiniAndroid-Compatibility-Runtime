# Coder Knowledge Index

**Last Updated:** 2026-08-25
**Primary Branch HEAD:** See git log

## Coder Missions

| Coder | Mission | Archive File | GitHub Access |
|-------|---------|-------------|--------------|
| Primary (Super Z) | Authoritative implementation, Git, regression, Telegram login | N/A (owns main) | Yes |
| Coder 2 | OX/libGDX/graphics/GUI/gameplay research | [CODER2_KNOWLEDGE.md](CODER2_KNOWLEDGE.md) | No |
| Coder 3 | Android System Compatibility Laboratory | [CODER3_KNOWLEDGE.md](CODER3_KNOWLEDGE.md) | No |

## Latest Imported Findings

### From Coder 2
| ID | Finding | Status | Integrated? |
|----|---------|--------|-------------|
| C2-F01 | Receiver/this propagation | PROVEN | YES (EXP-061) |
| C2-F06 | D8/R8 lambda resolution | PROVEN | YES (EXP-089) |
| C2-F07 | array-length bugs | PROVEN | YES |
| C2-F08 | ViewShadow over-interception | PROVEN | Game-specific |
| C2-F12 | Wide-value (return-wide/move-wide) | PROVEN | YES (EXP-089) |
| C2-F13 | Lazy-load/reserve lifetime | HYPOTHESIS | Defense-in-depth added |
| C2-F14 | Swallowed C++ exceptions | HYPOTHESIS | Not yet |

### From Coder 3
| ID | Finding | Status | Integrated? |
|----|---------|--------|-------------|
| F002 | openFileOutput path divergence | DIVERGENT | Not yet |
| F004 | SystemClock absent/zero | PROVEN | Related to F5 fix |
| F005 | Application lifecycle not real DEX | CRITICAL | Partially (ApplicationLoader pre-populated) |
| F007 | getSystemService null | DIVERGENT | Not yet |
| F011 | PackageManager hardcoded | DIVERGENT | Not yet |

## Historical Archive Lessons

1. **Multi-DEX string bug:** per-DEX `string_idx` was read from merged table → wrong string. Fixed in primary branch.
2. **Telegram UI corruption:** FIELD_PREFERRED_AUDIO_LANGUAGES leaked from wrong DEX string table.
3. **EditText semantic inheritance:** PhoneView$1/$3 → AnimatedPhoneNumberEditText → EditText → TextView → View. Must use inheritance, not hardcoded IDs.
4. **Renderer warning:** Old screenshots were fallback/synthetic. A screenshot is NOT proof without real runtime ViewTree → renderer → framebuffer → independently decoded PNG.
5. **DEX tooling warning:** Analysis/generator tools can make mistakes in opcode width, 23x packing, register lists, per-DEX tables. Always independently verify.

## Replacement Coder Instructions

A future Coder 2 or Coder 3 must:
1. Read the appropriate knowledge archive file.
2. Check current HEAD and origin/main sync.
3. Read `.agent/state.md` for current campaign state.
4. Read `worklog.md` for recent history.
5. Continue from `exact_next_action` in state file.
6. Never delete historical findings — append new ones.
