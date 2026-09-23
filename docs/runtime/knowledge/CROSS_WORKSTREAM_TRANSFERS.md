# CROSS-WORKSTREAM TRANSFERS — cross-stream transfer records (§10)

Each record: SOURCE / FINDING ID / EXPECTED / ACTUAL / EVIDENCE / RELEVANT WS / RECOMMENDATION

---

### X-001 — from UC2-001a (campaign) to WS-C3/PRIMARY
- **SOURCE:** Telegram 12.10.1 execution — RES-INTERCEPT trace
- **FINDING ID:** X-001 (per-version resource map)
- **EXPECTED:** on-screen texts = real localised strings
- **ACTUAL:** R field names (SMSWordTitle/WrongCode/…) rendered as the text
- **EVIDENCE:** stderr `[EXP091-SETTEXT] … text="SMSWordTitle"` + v12 screenshot
- **RELEVANT:** WS-C3 (resources/ARSC), Primary
- **RECOMMENDATION:** auto-generate the string/raw map from resources.arsc at load time; record SFS-010

### X-002 — from WS-C4 to WS-C2
- **FINDING ID:** C4TOC2-001..003 (full text: `WS-C4_TO_C2_C3.md`)
- **Summary:** FriBidi/HarfBuzz/FreeType ready and proven; ThorVG a future rlottie successor; APNG adapt-on-libpng
- **RECOMMENDATION:** FontBackend adapter (T1)

### X-003 — from WS-C4 to WS-C3
- **FINDING ID:** C4TOC3-001..003
- **Summary:** SQLite amalgamation (D1), libdeflate benchmark, dexlib2 cross-check
- **RECOMMENDATION:** in order D1 → benchmark → CI difftest

### X-004 — from WS-C5 to WS-C3/PRIMARY
- **SOURCE:** Robolectric/VirtualApp/Evoke/Redroid research
- **FINDING ID:** X-004 (interception map + environment)
- **EXPECTED:** — (architecture)
- **ACTUAL:** the real intercept surface is small and enumerable (system services + natives + libcore-delta)
- **EVIDENCE:** Robolectric's 607 shadow clusters; VirtualApp proxies/; redroid kernel-deps
- **RELEVANT:** WS-C3, Primary
- **RECOMMENDATION:** `SERVICE_INTERCEPTION_MAP.md` + Environment simulation (P1/P2 in WS-C5_PRIMARY_TRANSFER)

### X-005 — from WS-C3 to WS-C2
- **SOURCE:** src audit + v12 execution
- **FINDING ID:** X-005 (text overlap v12)
- **EXPECTED:** titles render separately
- **ACTUAL:** vertical overlap (custom view without full measure/layout)
- **EVIDENCE:** `run/uc_v12_top.png`
- **RELEVANT:** WS-C2
- **RECOMMENDATION:** after T1/T4, re-trace EXP095-LAYOUT for v12

### X-006 — from UC-CM-001 to everyone
- **FINDING ID:** UC-CM-001 (86bd646)
- **EXPECTED:** F012 false-success silently closed without regression
- **ACTUAL:** merged; 3/3 SHA identical to baseline; equal trace count
- **EVIDENCE:** `SOURCE_CHANGES.md` + runs
- **RELEVANT:** everyone (semantic VM)
- **RECOMMENDATION:** merge on main + close F015 (superclass retry) afterwards

# CROSS_CODER_RECONCILIATION — the Coder2/Coder3/Coder4/Primary/UC bridge table (§6 second part of the charter)

| CODER | FINDING | SOURCE SHA/reference | Previous STATUS | Current STATUS on `86bd646` | Evidence | Decision |
|---|---|---|---|---|---|---|
| C2 | C2-F31 (OX board render) | Coder2 branch | NOT INTEGRATED | NOT INTEGRATED (outside this campaign's scope) | CODER2_KNOWLEDGE | open — needs a branch merge by Primary |
| C2 | C2-F01/F06/F07/F12/F22 | EXP-061/089/093 | INTEGRATED | INTEGRATED — re-confirmed on v12 (lambda dispatch worked) | v12 run | closed |
| C3 | F002 | PRIMARY_CODER_TRANSFER_REPORT | PROVEN/KEEP | KEEP — sandbox healthy | code | make no change |
| C3 | F004 SystemClock | CODER3 | PARTIAL | **OPEN** (grep=0) | UC3-001 | T3-WS-C3 |
| C3 | F005 Application lifecycle | b7dc97b | FIXED | FIXED — Application load also happened on v12 | execution | closed |
| C3 | F007 | CODER3 | PARTIAL | PARTIAL (honest null) | code | after the interception map |
| C3 | F010 components | CODER3 | OPEN | OPEN | grep | T4-WS-C3 |
| C3 | F011 PackageManager | CODER3 | NOT REPRODUCIBLE | re-confirmed — not a hardcode | grep | closed |
| C3 | **F012 catch-all void** | CODER3 | OPEN | **FIXED (UC-CM-001, 86bd646)** | 3/3 SHA + trace | merge it |
| C3 | F015 | CODER3 | OPEN | OPEN | code | T5-WS-C3 (after CM-001) |
| C3 | F016 proto resolver | CODER3 | IMPLEMENTED | IMPLEMENTED + now a UC-CM-001 consumer | code | closed |
| C3 | F017/N9 Makefile deps | CODER3 | OPEN | **ALREADY FIXED** (Makefile: -MMD -MP) | Makefile line 5 | closed |
| C4 | SQLite 11/11+ | CODER4 transfers | PROVEN (POC) | NOT INTEGRATED in main | matrix D1 | D1 adoption |
| C4 | OkHttp 5/5, libcurl 6/6 | CODER4 | PROVEN (POC) | NOT INTEGRATED | matrix D5 | D5 |
| C4 | stb_image/giflib/rlottie/FreeType/HarfBuzz | CODER4 | PROVEN | rlottie/FreeType IN (build), the rest oracle | build | — |
| C4 | FFmpeg/audio/video oracles | CODER4 | PROVEN (oracle) | NOT INTEGRATED | matrix D4 | D4 |
| Primary | CM-001..CM-027 | CODER_MAIN_KNOWLEDGE | PROVEN | all on HEAD; no regression in v12 (except the resource map) | v12 run | — |
| UC | UC2-002 typography POC | this campaign | PROVEN (POC) | outside the runtime | evidence B | T1-WS-C2 |
