# RESEARCH 500 — FIX CROSSWALK (reverse mapping: fix → tickets)

For every implemented fix: root, commits, and EVERY ticket it resolves
— checked individually, never via the root alone (§6/§19).

## FIX-001

- Root: R-001 ROOT-REFLECTION-FIELD-IDENTITY
- Implementation: one canonical field key (declaring-class,name) across sget/sput/heap/Unsafe/java.lang.reflect.Field; NSFE/NPE/IAE laws; getField superclass walk; boxing/unboxing; real access flags; final-write IAE
- Commits: 0fc8bb69, bca4c001
- Evidence: R1-R12 probe 3/3 byte-identical; battery 105/105; 5 census titles un-killed (getField-NULL family)

Solves:

[x] P005
[x] P006
[x] P056
[x] P057
[x] P058
[x] P059
[x] P060
[x] P061
[x] P062
[x] P063
[x] P064
[x] P065
[x] P066
[x] P067
[x] P068
[x] P069
[x] P070
[x] P071
[x] P072
[x] P077
[x] P090

## FIX-002

- Root: R-002 ROOT-VIEW-FRAME
- Implementation: layout/setFrame through the ONE ViewNode geometry store; default onMeasure law; MeasureSpec constant seeding + makeMeasureSpec in-place OR law; getWidth=mRight-mLeft
- Commits: 0fc8bb69
- Evidence: W1-W5 probe 3/3; battery 105/105

Solves:

[x] P004
[x] P013
[x] P018
[x] P092
[x] P093
[x] P094
[x] P095

## FIX-003

- Root: R-003 ROOT-PFQ-ORDER
- Implementation: postAtFrontOfQueue = AOSP enqueueMessage(queue,msg,0): when=0, always due, front-first tie ordering
- Commits: 0fc8bb69
- Evidence: H6 order=-PF -> -FP 3/3; battery 105/105

Solves:

[x] P003
[x] P017
[x] P119
[x] P120
[x] P121
[x] P122
[x] P123
[x] P124

## FIX-004

- Root: R-001 ROOT-REFLECTION-FIELD-IDENTITY (framework surface)
- Implementation: framework_declared_fields_ registry — Field objects over framework statics (Build.*/Settings.*/MeasureSpec) resolve + answer identity with sget
- Commits: bca4c001
- Evidence: Lk3/a getField(SDK_INT)=34 identity with sget seed; census reflection titles rerun

Solves:

[x] P077
[x] P090

## FIX-005

- Root: R-009 ROOT-SWITCH-KEY-WIDENING
- Implementation: packed/sparse-switch key widening via dalvik_int_value (BYTE/CHAR/SHORT/BOOLEAN widen like AOSP ints) — R8 merged-class classId dispatch now runs the correct branch
- Commits: 4feaaeda
- Evidence: solitaire errors 12 -> 0 (3/3, SHA 59fdbfcd60b86a23); [S104-SW] probe key=0->5; battery 105/105; sgtpuzzles unchanged

Solves:

[x] P082
[x] P084

## Not resolved by any fix yet (high-value roots still open)

- [ ] P001 (Toolbar class identity) — R-004 dual-identity law pending
- [ ] P096/P097/P099 (decor root/sub-decor/findViewById) — R-005 attach model pending
- [ ] P011/P115..P118 (ARSC OFFSET16/COMPACT) — latent, 0/54 corpus exposure
- [ ] GL family P019..P055 slices — corpus-demand gated (see GL_NEED_LEDGER)

