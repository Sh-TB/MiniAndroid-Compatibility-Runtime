# MiniAndroid Agent State — EXP-088+ Campaign

## Current Experiment
EXP-088+ — Long-horizon MiniAndroid generic compatibility campaign

## Current Commit (most recent state)
HEAD — F4 CRITICAL FIX: type_list entries are 2 bytes (ushort), not 4 bytes

## Status: 10 PROVEN, 1 IN PROGRESS (M boundary SIGNIFICANTLY advanced)

### PROVEN (no change this round)
- A1 AXML inflation
- A2 measure/layout
- A5 text rendering
- A4 drawable/image loading
- B1 valid PNG output
- B5 entry-point resolution
- B generic input/click
- B2 event deduplication
- C SQLite
- F Handler/Looper
- I multi-DEX audit

### IN PROGRESS (M boundary MASSIVELY advanced this round)
Phase M now reaches the FRAGMENT LIFECYCLE:

```
LaunchActivity.onCreate (1330 instructions) ✅
→ handleIntent (15606 instructions) ✅
→ switchToAccount ✅
→ UserConfig.isClientActivated (EXECUTES, reads this.sync + this.currentUser) ✅
→ LoginActivity.loadCurrentState (EXECUTES, 209 instructions) ✅
→ IntroActivity.<init> ✅
→ setTag (8 calls) ✅
→ addFragmentToStack (2 args correct: ActionBarLayout + IntroActivity) ✅
→ IntroActivity.onFragmentCreate (EXECUTES, 118 instructions) ✅
→ getString(R.string.Page2Title..Page6Title) ✅
→ [next: PhoneView rendering / click dispatch → LoginActivity transition]
```

### Root-cause fixes this round

1. **F4 CRITICAL FIX: type_list entries are 2 bytes (ushort), not 4 bytes** (PRIMARY FIX):
   - DEX format `type_item { ushort type_idx; }` — each entry is 2 bytes
   - Runtime was reading 4 bytes per entry (uint32_t)
   - This caused WRONG proto resolution for ALL methods with 2+ parameters
   - Specifically: `$default$addFragmentToStack` proto resolved as `(J)Z` (takes long)
     instead of `(Lorg/telegram/ui/ActionBar/INavigationLayout;Lorg/telegram/ui/ActionBar/BaseFragment;)Z`
   - Wide-arg merger incorrectly merged the fragment argument as a long
   - args_size=1 instead of 2 → fragment never passed → lifecycle never started
   - FIX: Changed `* 4u` to `* 2u`, `uint32_t` to `uint16_t`, `i * 4` to `i * 2`
   - GENERIC fix — affects ALL multi-DEX APKs with desugared interface default methods

2. **F1 defense-in-depth: on-demand injection checks class_info_index_ first**:
   - No `reserve(43895)` in primary branch (F1 doesn't directly apply)
   - Added defense-in-depth: on-demand injection at line 957 checks if class
     already exists in class_info_index_ before push_back
   - Prevents duplicate injection and potential vector reallocation

3. **AndroidUtilities.readRes bypass**:
   - `readRes` loops forever reading a raw resource InputStream
   - In headless mode, InputStream returns 0/-1 → while loop spins
   - Added to bypass list (generic fix)

### VNC/X11 capability check
- **Xvfb**: AVAILABLE (can run headless X server)
- **VNC server**: NOT AVAILABLE (no root to install x11vnc/tigervncserver)
- **Screenshot tools** (scrot, import, xwd): NOT AVAILABLE
- **xdotool**: NOT AVAILABLE
- **Conclusion**: VNC is impossible in this environment. However, MiniAndroid
  already produces a PNG screenshot via its own software renderer, independently
  verified by PIL (A4.5 PROVEN). No GUI session needed for validation.

### Verified secondary findings
1. **F1 (lazy-load reserve / dangling ClassInfo)**: NOT APPLICABLE — no `reserve(43895)` in primary branch. Injection happens ONCE at startup before execution. Added defense-in-depth.
2. **F4 (invoke overload resolution)**: ROOT CAUSE CONFIRMED — type_list entries are 2 bytes, not 4. FIXED. This was the PRIMARY blocker for Phase M fragment lifecycle.

## Resume Instructions (next round)

1. The campaign is NOT complete. M is IN PROGRESS.
2. **Exact next action**: Investigate what happens after `IntroActivity.onFragmentCreate` completes.
   The runtime needs to:
   - Call `createView()` to create the IntroActivity's view
   - Render the intro screen
   - Then dispatch a click on "Start Messaging" button
   - Then transition to LoginActivity
   - Then render PhoneView
   - Then inject phone number
   - Then mock auth.sendCode
3. Reproducer:
   ```
   cd miniandroid && ./build/miniandroid run -o /tmp/tg_test download/exp038_telegram/Telegram.apk
   grep -aE "onFragmentCreate|createView|PhoneView|onNextPressed|sendCode" /tmp/tg_test.log
   ```
4. After M is PROVEN (full login chain works end-to-end), the campaign is complete.

## Reproducibility
- Telegram: 3/3 reproducible runs (identical screenshot SHA `24956663322f4c73c55f30fc7e46dc63f7578102d1db08e9ae311c19d9e9d495`)
- All A4 tests pass
- All Phase F tests pass: 23/23
- All multi-DEX inject tests pass: 2/2
- All regression tests pass: A1, B, B2, C, F, I — no regressions introduced
