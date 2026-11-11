# Wiki Schema（宪法）

## 领域
哲学、健身营养、技术、经济学、通识科普。范围外内容不建页，顺带一提不建页。

## 三层结构（Karpathy llm-wiki 模式）
- **`raw/` 原始层（不可变）**：来源原文。agent 只读不写，永不修改。转写稿进 `raw/transcripts/`，网页文章进 `raw/articles/`。每个 raw 文件头部必须有元信息块（`source_url:` / `ingested:` / `sha256:`）。
- **`pages/` Wiki 层（agent 所有）**：笔记页、实体页、金句页、MOC 页——由 agent 创建、更新、互链。
- **`SCHEMA.md` + `index.md` + `log.md`**：宪法、目录、日志。任何写操作后必须更新后两者。

## 命名与格式
- 文件名：简体中文可读名，无空格无特殊符号（实体页如 `看不见的手.md`）
- 元数据用 Logseq properties（页首 `key:: value`），**不用 YAML frontmatter**
- 页面内链接用 `[[wikilink]]`，实体首次出现处才加链，全篇 5-15 个
- **每次写入后**：更新 `index.md` 对应条目 + `log.md` 追加一行（由 `zettelgate add` / `register` 幂等代劳）；**CLI 不自动 git commit**，提交范围由人决定

## 标签分类法（type:: 取值）
`视频笔记` `文献笔记` `人物` `概念` `著作` `金句` `MOC` `工具卡`（工具/软件/服务的使用卡：地址、原理、本机用法与踩坑） `原子笔记`（自己的想法，Doto 主笔记；规范见 `ZETTEL.md`） `结构笔记` `枢纽笔记` `CLOG`（Doto Part III 写作产出；规范见 `WRITING.md`，有内容时才用，**不预建空目录**）
主题 tags（多选）：`哲学` `健身` `营养` `技术` `经济学` `心理学` `历史` `科学`
新 tag 先加进本分类法再用。**取值唯一真源是 `src/zettelgate/config.json`**（`lint.py` 与 `zettelgate` 都从那里读）；新增或改名 type 时先改配置，再同步本文件与 `ZETTEL.md`。

## Properties 规范
笔记页：
```
type:: 视频笔记 | 文献笔记
source:: <url>
author:: <作者/频道>
collection:: <合集名（视频类）>
episode:: <集数>
date:: <发布日期 YYYY-MM-DD>
duration:: <分钟>
```
实体页：
```
type:: 人物 | 概念 | 著作
aliases:: 别名1, 别名2
verified:: true | false
contradicted:: <冲突页名（有矛盾时）>
```
- `verified:: true` = 有视频/文献实据；`verified:: false` = AI 生成，待人工核
- **2026-11-11 值域扩展**：主笔记（`pages/原子笔记/`）复用**同一个** `verified::`，可填 `推理` / `类比` / `待查` 等更细的证据状态；`true` / `false` 的原有含义不变。配套的 `claim_type::`（事实/推理/类比/判断/决策）标断言类型，两者都**可选、不进硬 gate**，见 `ZETTEL.md` 第 3 节与 `PRINCIPLES.md` 第 5 节。⚠️ 不要另起同义字段，避免跨 Agent 读到两套口径
- 实体页的「定义」由 agent 重写，**不抄 ASR 原句**（隔离同音字错误）

## 建页阈值
- 实体出现于 2+ 篇笔记，或单篇核心 → 建页
- 顺带一提、脚注级提及 → 不建页，正文平文
- 页面超 200 行 → 拆分加互链
- 内容被完全取代 → 移入 `_archive/`，从 index 摘除，原链接改平文+「(已归档)」

## 链接纪律
- 每篇笔记 5-15 个出链；宁缺勿滥（缺链可由「未链接引用」事后补）
- 通用动词名词不链；停用表由 lint 沉淀到本文件
- 金句：`pages/金句/<俗语>.md`，正文原句用 `>` 块引用后链金句页
- 不手写反向链接——Logseq/Tine 自动计算

## 矛盾处理
新信息与既有页面冲突时：不覆盖。双方并列+日期+来源，双方页面互加 `contradicted::`，log 标记，lint 报告置顶。

## 每会话开工仪式（agent 必读）
1. 读 `CONTRACT.md`（跨 Agent 统一入口，2026-11-11 起）
2. 按任务读规范：本文件（文献/实体）/ `INGEST.md`（外部材料转化）/ `ZETTEL.md`（自己的想法）/ `WRITING.md`（写作产出）
3. 涉及「合不合格」或改门禁时读 `PRINCIPLES.md`（书的原则 → 硬 gate / 诊断分档）
4. 读 `index.md`——已有页面与一句话摘要
5. 读 `log.md` 最近 20 行
6. 新主题动手前先搜**概念词**全库查重
跳过会导致重复建页、漏链、违反约定。

## 两套范式与统一写入口（2026-11-11）
本宪法管的是「外部来源驱动」的 llm-wiki 三层结构（raw → 笔记页 → 实体页）。用户自己的想法另走 `ZETTEL.md` 的 Doto 原子笔记范式，落在 `pages/原子笔记/`；两者**同 graph、不同目录**，以便 reference → main 之间可以互链。

原子笔记本规范中**豁免**以下铁律：建页阈值（2+ 篇才建页）、每篇 5-15 出链、笔记页 properties 里的 `source::` / `author::` 等外部来源字段。仍须遵守：Logseq properties 格式、`[[ ]]` 逐字等于文件名、每次写入更新 index/log、lint 0 断链。

所有 Agent（Hermes / WorkBuddy / 其他）读写本库前**先读 `CONTRACT.md`**：
主笔记走 `zettelgate add`，**其它所有类型（含本宪法管的视频笔记 / 文献笔记 / 实体页）走 `zettelgate register`**，
由脚本幂等维护 `index.md` / `log.md` 并跑硬 gate。既有 scholar-inbox-ingest 进料管线按本宪法原流程落盘，
但登记环节建议迁到 `register`，以消除两端并发追加 `index.md` / `log.md` 的冲突。Capacities 双写已停用，不再执行。

## Doto 方法论纳管（2026-11-11）
本宪法管「外部来源驱动」的 wiki 层，但**外部材料如何变成想法**不在这里，见 `INGEST.md`：
`raw/` 全文（不可变）→ **批注前置（Marginalia，当前 92 页参考/视频笔记的主要缺口）** → 参考笔记
→ 判断有没有值得独立的原创想法 → 主笔记（`ZETTEL.md` 范式）。
⚠️ 不要批量回填历史页的批注；`zettelgate audit` 的 D13 只列缺口，遇到哪一页再顺手补。

方法论只读快照在 `references/doto/`（**不得修改**）；原则如何变成两档门禁见 `PRINCIPLES.md`。
`lint`（硬 gate G1–G8，失败退出码 1）与 `audit`（诊断 D1–D16，只读、恒为 0）分工不可混：
原子性、原创性、标题好坏、连接理由是否成立，**一律不进硬 gate** —— 依据是书的第一原则「可持续性」。
