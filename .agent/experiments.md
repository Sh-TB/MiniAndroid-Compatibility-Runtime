# EXP-048 Experiment Log

## EXP-048.1 — SharedPreferences Persistence

**OBJECTIVE:** Implement persistent SharedPreferences that survives process restart.

**BASELINE:** 189 methods, 5 JNI calls, 0 HALT, SUCCESS.

**OBSERVATION:** 
- `getSharedPreferences` is called 5 times (confirmed via verbose API BRIDGE log)
- `SharedPrefsHelper.init` calls `Context.getSharedPreferences("InviteMessagePremiumBlockedMany_other", 0)` 
- `SharedConfig.loadConfig` calls `Context.getSharedPreferences("background_activity", 0)` and `Context.getSharedPreferences("userconfing", 0)`
- But SharedPreferences interface methods (getBoolean, getString, edit, commit) do NOT appear in API BRIDGE log

**EVIDENCE:**
- Verbose log shows 1219 API BRIDGE calls total, 5 are getSharedPreferences
- 0 calls to getBoolean, getString, edit, commit, apply, putString, etc.
- SharedPreferences interface methods ARE in the DEX (classes.dex, classes3.dex, etc.)
- They are abstract (no bytecode), so try_recursive_invoke should return false
- bridge_to_api should then handle them

**HYPOTHESIS:** 
The invoke-interface handler may not be correctly routing SharedPreferences
interface calls to bridge_to_api. The interface methods are abstract in the DEX,
so try_recursive_invoke should skip them (bytecode.empty()), but the fallback
to bridge_to_api might not be triggered correctly for invoke-interface.

**EXPERIMENT:** Add diagnostic logging to invoke-interface handler to confirm
whether SharedPreferences methods reach bridge_to_api.

**STATUS:** OPEN

---

## EXP-048.2 — Native Method Dispatch

**OBJECTIVE:** Execute multiple native method calls beyond native_getCurrentTime.

**BASELINE:** 5 JNI calls to native_getCurrentTime via HOST_COMPATIBILITY_STUB.

**OBSERVATION:**
- ConnectionsManager.native_getCurrentTime dispatched 5 times
- No other native methods dispatched
- 12 P0 native stubs registered in JNI bridge
- ConnectionsManager.getInstance reaches the native call
- Other native methods (native_init, native_setJava, etc.) not yet called

**HYPOTHESIS:** 
The execution path only reaches getCurrentTime because postInitApplication
calls it for logging. Other native methods require deeper execution
(e.g., UserConfig.loadConfig might call native methods, or
MessagesController might call native_init).

**STATUS:** OPEN

---

## EXP-048.3 — const/4 Fix Impact (EXP-047, verified)

**OBJECTIVE:** Verify const/4 fix enables deeper execution.

**BASELINE (before fix):** 184 methods, 0 JNI calls.

**OBSERVATION (after fix):** 189 methods, 5 JNI calls.

**ROOT CAUSE:** const/4 (opcode 0x12, format 11n B|A|op) extracted register
and literal from wrong nibbles. Old code: dest_reg=(instr>>8)&0xFF,
literal=(instr&0xF). Correct: dest_reg=(instr>>8)&0xF,
literal=(instr>>12)&0xF.

**RESULT:** +5 methods, +5 JNI calls. ConnectionsManager.getInstance,
getCurrentTime, MessagesController.getInstance, UserConfig.loadConfig,
SendMessagesHelper.getInstance all reached for the first time.

**STATUS:** CONFIRMED
