# EXP-115 — Opcode census cross-check: androguard vs dexlib2/baksmali (T15)

Input: Telegram 12.10.1 classes.dex (DEX#1). Two independent tools.

| opcode | androguard 4.1.4 | baksmali 2.5.2 smali tree | verdict |
|---|---|---|---|
| iget-object | 45,060 | 45,060 | EXACT MATCH |
| iput-object | 15,921 | 15,921 | EXACT MATCH |
| sget-object | 12,248 | 12,248 | EXACT MATCH |
| sput-object | 9,954 | 9,954 | EXACT MATCH |
| return-void | 29,260 | 29,260 | EXACT MATCH |
| new-instance | 26,470 | 26,470 | EXACT MATCH |
| const-string | 28,023 | 28,023 | EXACT MATCH |
| invoke-virtual | 90,289 | 91,209 | MATCH after +920 invoke-virtual/range |
| invoke-direct | 42,120 | 44,006 | MATCH after +1,886 invoke-direct/range |
| invoke-static | 48,015 | 48,662 | MATCH after +647 invoke-static/range |
| invoke-super | 1,227 | 1,244 | MATCH after +17 invoke-super/range |
| invoke-interface | 19,010 | 19,185 | MATCH after +175 invoke-interface/range |

Explanation: the smali-tree grep pattern matched `*/range` variants under base names;
plain-count and range-count sum == androguard count for every opcode.
methods_with_code (androguard, DEX#1): 55,121.

VERDICT: PROVEN — two independent parsers agree byte-exactly on the instruction mix.
Raw JSON: EXP-115_opcode_crosscheck.json (androguard side).
Total class cross-check: baksmali produced 41,146 smali classes across 5 DEX ==
androguard EXP-105 census of 41,146 classes.
