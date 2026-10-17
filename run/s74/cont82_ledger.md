# CONT-82 — #364 继续：DexSQL 受控实验 + 三个共享定律修复 + veldsoft 语料重分类

**Wave:** CONT-82 · **Date:** 2026-10-17 · **HEAD at start:** `b7f6f116` (origin/main, CONT-81 closeout) · **Binary:** `c2b649586357a84e` → `9a3d89f7995a5505` · **Registry:** 689→692 (id-unique, canonical mirrored)

---

## 0. 新请求盘点（本波读取 #364 全部 39 条评论）

在 CONT-74 RESULT（6229994936）之后的 8 条新请求全部识别并归档：

| # | comment | 标题 | 本波处置 |
|---|---------|------|---------|
| 1 | 6234354571 | CONT-75 RESULT — F-NEW-277 lever decoded | 已交付（历史波） |
| 2 | 6234924269 | CONT-76 — #364 Closure Wave | 已交付（历史波） |
| 3 | 6236208258 | CONT-77 — closure re-verified + F-NEW-380 | 已交付（历史波） |
| 4 | 6237528258 | CONT-78 DIRECTIVE — corpus expansion | 已交付（历史波） |
| 5 | 6237592508 | CONT-78 AUDIT ADDENDUM — harness contract | 已交付（历史波） |
| 6 | 6237660877 | CONT-79 — White/blank ROOT FIX batch | P1-D/P1-E 本波推进（见 §4） |
| 7 | 6237721198 | CONT-80 — Five NEW roots | T4 本波关闭（见 §3） |
| 8 | 6238136459 | **CONT-81 — DexSQL controlled value test** | **本波执行（唯一零痕迹指令）** §1 |

## 1. DexSQL 受控实验（CONT-81 指令全文执行）

**受控安装**：v0.1.0 linux-amd64（`tools/dexsql/dexsql-linux-amd64`，sha256 `f9e795e1…ef00c`）。诚实记录：release 未发布 checksum 文件（GitHub API 核实 assets 仅 4 二进制 + LICENSE）——本下载的 sha256 被固定并记录；LICENSE（Binary License 1.0）已读：闭源二进制、允许任意使用；LICENSE-AUXILIARY 不存在于 release assets（记录）。二进制不入库；APK 内容不出本地。

**Cookbook**（`scripts/cont82_dexsql_cookbook.py`，14 查询，manifest sha16 `3d0824a694c75f1b`）：12/12 可表达查询全部通过，单查询 0.02–0.04s；**类别 1（manifest）+ 12（resources）诚实 UNSUPPORTED**（DEX-only schema，`dexsql tables` 核实无 manifest/resource 表——基线 aapt2 覆盖）。

**配对实验**（同一调查者双臂，相同起始证据 = engine stderr 行；污染已声明——双臂度量的是 DEX 事实定位速度与精度，不是盲发现）：

| 问题 | Arm A（基线 androguard+zipfile+rg） | Arm B（DexSQL） | 结论 |
|---|---|---|---|
| Q1 veldsoft 启动链 | ~5 次脚本迭代、~6–7 分钟（banner.html 缺失核实 + SplashActivity$1 TimerTask 解码） | 同一结论 0.03s/查询，字节精确描述符 | 双臂同根；B 约 10x 快 |
| Q2 chess NPE 链 | engine 行（REC-MISS/F175/F383-CSL）承载运行时真值 | 秒级定位 Lq/b、Lf2/p.a、Ln0/k1 + Lf2/p.a 精确字节码 | 两条引擎定律由此落地 |

**决定：LIMITED ADOPT** —— DEX 事实定位（caller 链/callsite/字符串/decode）实测 ~10x 且零精度回归；不用于 manifest/resources（不支持）；查询结果不作为证据（必须运行时行核验）。

**修复循环（§5 交付）**：Q1 链 → deferred-drain 预算法（§2）；Q2 链 → F-NEW-383 + F-NEW-384（§3）。DexSQL 辅助解码直接喂出的共享根修复 ≥2：满足。

## 2. veldsoft 语料重分类（3 行 DEFAULT_BACKGROUND_ONLY → REAL_APP_CONTENT）

根因：CONT-81 预算 5 帧 × 300ms 虚拟时钟 = **1500ms < 5000ms** splash `Timer.schedule`（F-115 引擎定律正确触发 `[F115-TIMER] schedule … delay=5000ms` 并入队 `earliest_ready_at=5000ms`）。**分歧在 harness 虚拟时钟预算法，不在引擎。**

deferred-drain 重跑（`--frames 24` = 7200ms 虚拟 > 5000ms）：

| 包 | 旧 face | 新 face | 真实启动证明 | 应用像素 |
|---|---|---|---|---|
| eu.veldsoft.fish.rings | 默认背景 | `a341e3ad9092f640` | `startActivity → GameActivity` 真实 onCreate/setContentView | 105,061 非主色 px / 6,673 色 |
| eu.veldsoft.tri.peaks | 默认背景 | `e2a290ab98762eea` | `startActivity → LobbyActivity` | 559,878 非主色 px |
| eu.veldsoft.free.klondike | 默认背景 | `a77038da303ed1b4` | `startActivity → MenuActivity` | 501,984 非主色 px |

可重复性 6/6（每 app ×2 附加运行字节一致）+ 3/3 在最终二进制复验。诚实注记：这三行的引擎 census 行（trace_summary）未在 drain 重跑中重写——重分类证据 = 真实启动链 + 像素普查，runner 集成（--frames 预算法升级）记录为 next_action。

## 3. 三个引擎定律修复（全链路：pre-fix 行 → decode → fix → post-fix → 回归）

- **F-NEW-383 ROOT-CAUSED-FIXED P1** — ColorStateList 资源定律族 + Context 族 obtainStyledAttributes producer gate。chess 的 Material drawable 链（Lq/a → TypedArray.getColorStateList → Lq/b.getDefaultColor）与 themed-obtain 惯用法（Lf2/p.a：`new ContextThemeWrapper(ctx, resid).obtainStyledAttributes(attrs)`）此前全部 null → NPE。诚实抓漏：首跑把 attr id `0x10104e2` 当 ARGB 包了——已加 gate → null + 有界行。
- **F-NEW-384 LAW-LANDED-PARTIAL P1** — 根 WindowInsets dispatch（AOSP performTraversals 在 measure 之前）。落地的定律真实且 AOSP 有序：`[F384-ROOTINSETS] root=o421 (ActionBarOverlayLayout) dispatched=true`（骨架树 o232 / last-root o631 两次误选被抓出并修正；root 权威 = ActivityShadow content_view_id）。**诚实残差**：chess 面字节不变（`b270ff040b3601dc` 零漂移）——measure 路径的缓存包装仍在读 PRE-dispatch 填充的字段（k1.b() 平台 insets 链 + d1.l(IIII) builder 族）——第二代 null 源已命名，未关闭。
- **F-NEW-385 ROOT-CAUSED-FIXED P1** — 数组组件类型定律族（CONT-80 T4 验收门）：new-array 零初始化（缺失槽 ≠ null）、aput 变体类型化、fill-array-data 宽度-2 [C/[S 类型化、filled-new-array [Z/[C/[B/[S 类型化。fixture `fixtures/cont82_arrays_fixture`（真实 aapt2/ECJ/D8）pre-fix `[1, null]`/`[120, 121]` → post-fix **8/8 PASS**。

## 4. 逐项 تایید/رد 终局表（本波指令要求的二值结论）

| # | 项目 | 结论 |
|---|------|------|
| 1 | CONT-81 DexSQL value test | ✅ **تایید** — LIMITED ADOPT（实测 A/B + 决定门） |
| 2 | CONT-80 T4 Arrays.toString 矩阵 | ✅ **تایید** — fixture 8/8 + F-NEW-385 三定律 |
| 3 | veldsoft 三白屏（fish.rings/tri.peaks/klondike） | ✅ **تایید** — 3 行翻转为 REAL_APP_CONTENT（字节稳定） |
| 4 | chess ColorStateList/themed-obtain 链 | ✅ **تایید（定律落地）** — F-NEW-383；白面残差属 #5 |
| 5 | chess k1.c insets 族（+ AndStatus2048 候选） | ⚠️ **部分 تایید** — F-NEW-384 dispatch 落地，第二代 null 源已命名未关闭 |
| 6 | CONT-79 P1-D F-NEW-351 one-bit diag | ⏸ **رد（本波不执行，有理由）** — 触 draw 路径需独立波 + 全电池；solitaire APP_PIXELS 行如实保留 |
| 7 | SWIPE tap 词汇 | ⏸ **رد（本波不执行，有理由）** — harness 特性非运行时缺陷；click-test 已覆盖交互证明契约 |
| 8 | DT_NEEDED soname shim | ⏸ **رد（本波不执行，有理由）** — ELF 依赖 shim 定律保持命名前沿，需独立波 |
| 9 | F-NEW-381 register-file | ⛔ **BLOCKED（沿用终局）** — 实测证据不变 |
| 10 | UPP-001 native 执行 | ⛔ **BLOCKED（沿用终局）** — 架构级 |

**本波成功率**：4/10 全 تایید（40%）+ 1 部分落地说（50% 完成度计数）+ 3 有理由 رد（本波范围外）+ 2 沿用 BLOCKED。**#364 全历史累计**：CONT-74 29 评论零未分类 → CONT-76 8 项终局（50% confirmed/37.5% rejected/12.5% blocked）→ CONT-77 复验（5 confirmed 55.6%）→ CONT-81 corpus 73.3% app-content → **本波后语料 25/30 = 83.3% app-content**（22/30 + 3 veldsoft 翻转，5 个非 REAL 面全部有命名根：dooz F-NEW-381 预算、chess F-NEW-384 残差、stopwatch 包工件、solitaire F-NEW-351 域、fishrings/tripeaks/klondike 已翻转）。

## 5. 回归电池（最终二进制 9a3d89f7995a5505，全绿）

wall **12/12** MATCH（cont70 的 g2048/tttdeluxe WANT 已更新为 CONT-81 记录锚 f43face0/db1d633d——旧行是 CONT-77/81 之前的陈旧记录，got 值与记录锚字节一致 = 零漂移）· goldens **4/4** · negatives **19/19** · reinstall 身份 **5/5**（hidden_sources 从 canonical uploads 重建）· MG-310 **7/7** · MG-150 **3/3** · c72priv **12 OK 零 BAD** · F-NEW-376 注入 **70/70** · f382 probe **4/4** · arrays fixture **8/8** · harness selftests **14/14**。

## 6. 诚实的未做/未证明清单

- chess 白面未翻转（F-NEW-384 第二代 null 源已命名）。
- 这三行 veldsoft 的引擎 census 行未在 drain 重跑中重写（重分类证据 = 启动链 + 像素普查）。
- F-NEW-351 one-bit diag、DT_NEEDED shim、SWIPE 词汇、F-NEW-381 表示层——均有记录理由，未声称。
- DexSQL MCP smoke test 未跑（CLI 已满足本波度量；MCP initialize/open/query 冒烟按指令要求记录为未执行）。
