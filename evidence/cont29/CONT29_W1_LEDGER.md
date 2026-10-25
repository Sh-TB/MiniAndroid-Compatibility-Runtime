# CONT-29 W1 — 同步远程（322 提交）+ 寄存器证据 + R-NEW-467 吞吐法则 + F-NEW-520 PriorityQueue

**日期**: 2026-10-25 · **二进制**: e4da5315cfd95e46 · **指令**: «ادامه گیت هاب خیلی جلوتره برری بکن و خودتو به روز بکن» + «دستاورد نکن الکی»

## Phase 0 — 同步与自我更新

- 远程领先 322 提交（本地容器停在 e99c2fbd = CONT-10 W6 时代）。fast-forward 重置到 origin/main 7f8d639c。
- 审查远程线：CONT-11 W7-W9 → CONT-12/13/14-B4 → CONT-28 W1（registry 566→837，dooz 851cc176 REAL_APP_CONTENT@300s，telegram 1671f5a3）。
- dooz 基线 ×3 字节一致复现（851cc1761a1dfcdf）。

## F-NEW-521 寄存器证据（诚实精化，不假装修复）

- 基准真值解码：`scripts/w8_hexdump_method.py`（字节空间、格式完备；确认 w7_disasm 的 pc = 代码单元 ×2）。
- 增长决策：eu 0x84 iget threshold → 0x88 if-nez →（非零）0x9e 放置路径；fall-through → 0x8a-0x9c DELETED 检查 → 0xaa 增长区；insert tail（eu 0x277）按新槽递减 threshold。
- **PC-WATCH 194 行**：threshold 在分支处完美往返（6→5→4），但每个 map 只被 put 2-3 次即被废弃（o2418→o2452→o3188→o3211→o4372，各自从 6 重启）；增长区 0 命中。**无分支 bug、无别名 bug —— 根因是当前头部没有任何 map 达到阈值**（W7 的满表自旋是 CONT-10 时代二进制的面孔）。
- 当前头部的 183 次墙钟停顿烧在 draw window（HALT-HISTO：39× dispatchDraw、宽游走 visits=1、零紧循环）= **F-NEW-381 吞吐墙**。
- F-NEW-521 保持 CLASSIFIED（P0 潜伏）；探针如实 PENDING（合成触发需要 dooz 自身 DEX 类，无法源码构建）。

## R-NEW-467 字段解析记忆化（60% 核心杠杆）

- PERF-OPS 剖析：iget-object 229 万次调用 = #1 燃烧（~1.9μs/次）；sget-object ~3.5μs/次。每次访问重走原始 DEX 解析 + 类链遍历 + 字符串拼接。
- 修复：resolve_field 内部 memo 快路径 + FieldMemo 库（res + s134 decl/fkey）；四个热点（iget/iget_object/iput/iput_object）走 resolved_field_memo 常引用；epoch = dex_index ^ super表 ^ class_info表（任何运行期增长都失效一次）。
- **语义陷阱（A/B 抓住并修复）**：首次 A/B dooz 锚坍缩 851cc176→d602648e —— res-only 入库条目（s134_valid=false、空 fkey）被命中条件放行 → 所有字段读用空键。修复：命中要求 resolved AND s134_valid。
- 提速：iget-object **-30.6%**、iget **-30.5%**、iget-wide -26.9%、iput-object -22.2%（top-12 燃烧 -10.5%）。
- snakeneon 归因（A/B 双臂同面貌 2617c81c det×3）：与 memo 无关 —— 本容器重建面貌；真实内容不变，如实记录。

## F-NEW-520 PriorityQueue（40% 旧应用杠杆）

- 解码面：wocheneinkauf Ly7;.a —— PriorityQueue.iterator() 回答 NULL（无 shadow 认领）→ hasNext NPE，BreakIterator 断行工作列表从未运行。
- 修复：CollectionShadow 认领 + add/offer（kind 保真）、peek/poll 最小元素法则（int 键含自动装箱 Integer kind-5 从堆 `value` 字段解箱；全 STRING 字典序最小；混合/app 对象 FIFO 头 —— **近似如实记录**）、size/isEmpty/clear/contains（contains 解箱装箱参数）；iterator 走通用 Iterable 法则 = 数组序（OpenJDK：迭代"无特定顺序" —— 忠实）。
- 探针：fixtures/fnew520_probe（真实 aapt2/ECJ/D8）**6/6 PASS**。

## Census batch-20（20 列火车指令的推进计数）

- **5/20 内容行（4→5）：wocheneinkauf 穿越 0 → 1356 色 / 8,579 px 真实 UI**。
- 零漂移：bouncy 72622 / fossify_math 13071 / calendar 12336 EXACT sha；netguard 27,059 内容保留（小增量，如实）。
- 14 个空白面如实命名于 census json（各自首潜待做）。

## 回归墙（全绿）

dooz 851cc176×3 字节一致 · 6 锚钉定面 · negatives 19/19（商店重建后；9/19 = CONT-158 同款过期商店伪象）· selftest 13/13 · goldens 4/4 · games 6/7 EXACT + snakeneon A/B 中性。

## 诚实局限

F-NEW-521 增长路由 = 潜伏未闭 · R-NEW-467 只回收 top-12 燃烧的 ~10.5%（堆字符串键字段映射是下一个结构杠杆）· PQ app 对象排序 = FIFO 近似 · S102/14 空白面 = 未宣称修复。
