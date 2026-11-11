---
name: zettelgate
description: 往笔记库写笔记、起 Doto 主笔记卡片、把视频/文章转成笔记、建结构笔记或 CLOG、查询与体检知识库时使用。统一走 zettelgate CLI：主笔记用 add，其它页用 register，体检用 audit。触发词：写笔记、记一条想法、原子笔记、卡片盒、Zettelkasten、批注、结构笔记、CLOG、知识库入库、lint、audit、查重。
version: 0.1.0
license: MIT
tags: [knowledge-base, logseq, zettelkasten, atomic-note, doto]
---

# zettelgate — 跨 Agent 写笔记统一入口

> **路径约定**：文中 `<zettelgate>` 指 zettelgate 系统仓根目录，默认 `~/zettelgate`
> （本文件经软链部署后，真实位置即该系统仓下的 `adapters/SKILL.md`，故系统仓根 = 本文件所在目录的上两级）。
> 若你的系统仓在他处，请把文中 `<zettelgate>` 统一替换为实际绝对路径。
> `$VAULT` 指笔记库根（如 `~/LogseqVault`），各端按自己的库填。

> 本文件只是**指针**。规范正文在 `<zettelgate>/specs/`，门禁实现在 `<zettelgate>/src/zettelgate/`，
> 方法论只读快照在 `<zettelgate>/references/doto/`（见其 `SOURCE.md`）。
> **禁止在适配层复制或改写规范正文**；笔记数据留在各自的 `$VAULT`，不进系统仓。

## When to use
用户要写一条自己的想法、起原子笔记卡片、把视频/文章转成笔记、建 Structure Note / Hub / CLOG、
把草稿入库、查询或体检知识库时。任何 Agent（Hermes / WorkBuddy / 其他）通用。

## 铁律（五条）
1. **先读 `<zettelgate>/specs/CONTRACT.md`** —— 唯一入口契约；再按任务读对应规范。
2. **判断「合不合格」前先读 `specs/PRINCIPLES.md`** —— 硬 gate 只管客观项，语义判断只出诊断报告。第 5 节是 AI 时代依据修订，**档位不变**。
3. **所有新页走 CLI** —— 主笔记 `zettelgate add`，其它页 `zettelgate register`；由脚本幂等维护 `index.md` / `log.md` 并跑硬 gate。禁止直接手改这两个文件。
4. **写完 `zettelgate lint` 必须 0 断链**；`zettelgate audit` 只读诊断、恒为 0，不要求它「全绿」。
5. **判断痕迹不可覆盖** —— 不得依据 `audit` 报告自动重写既有主笔记；任何改动须用户逐条确认。不自动 `git commit`。

## 规范路由
| 任务 | 读哪份 | 命令 |
|---|---|---|
| 自己的想法 / 一条主张 / Doto 主笔记 | `specs/ZETTEL.md` | `new` → 填六要素 → `add` |
| 视频转写 / 网页文章 → 批注 → 参考笔记 → 主笔记 | `specs/INGEST.md` + `specs/SCHEMA.md` | 参考笔记落盘 → `register`；转出的主笔记 → `add` |
| Structure Note / Hub Note / CLOG / 渐进发布 | `specs/WRITING.md` | 按模板落盘 → `register` |
| 文献笔记 / 实体页 / 金句 / MOC 织网 | `specs/SCHEMA.md` | 落盘 → `register` |
| 门禁依据 / 改检查项 | `specs/PRINCIPLES.md` | `lint` / `audit` |
| 换一个 Agent 接这个库 | `specs/platforms/logseq.md` | 10 个操作映射 |

两套范式同 graph、不同目录；主笔记落 `pages/原子笔记/`，可与文献页互链。
**视频转笔记封装的是转化契约（批注前置），不是下载与 ASR 工具** —— 后者留在链路边缘，由各端自己的工具负责。

## 命令速查
```
zettelgate --vault "$VAULT" new "声明式标题"
zettelgate --vault "$VAULT" add <草稿.md> --name <页名> --summary "一句话摘要"
zettelgate --vault "$VAULT" register <pages/内的.md> --summary "一句话摘要"
zettelgate --vault "$VAULT" lint          # 硬 gate G1-G8，失败退出码 1
zettelgate --vault "$VAULT" audit         # 诊断 D1-D16，只读、恒为 0
zettelgate --vault "$VAULT" index [--fix]
zettelgate init <库目录>                  # 生成 vault.yaml
zettelgate --vault "$VAULT" upgrade [--apply]   # 按 schema_version 提示/引导升级（不自动迁移数据）
```
库路径也可用 `ZETTELGATE_VAULT` 环境变量，或在库根放 `vault.yaml` 后于该目录直接运行。
`zettelgate link` 只处理 `adapters` 配置里显式列出的软链目标，**不硬编码任何宿主目录**。

## 开工仪式
读 CONTRACT → 读 PRINCIPLES（涉及门禁时）→ 读对应规范 → 查 `index.md` / `log.md` 末 20 行
→ 全库查重（搜概念词）→ 写 → `add` / `register` → `lint`。

## 禁止事项
- 禁止在适配层写规范正文；禁止把规范复制到第二个库；禁止修改 `references/doto/` 只读快照
- 禁止 `[[候选页]]` 指向不存在的页；候选方向写平文
- 禁止链接堆砌（连着三个裸链接，G2 会 FAIL）；每条链接写明「为什么链」
- 禁止往 `.inbox/` 投 `.md` 草稿（那里只收定时任务的 `*.url`）
- **Folgezettel ID 留空由用户手工填写**，agent 不自动编号
- **使用记录不手填**，由 Structure Note / 草稿双链形成的反链自动产生
- 未核实的推理类比要标 ⚠️，不要当事实引用；`claim_type::` / `verified::` 是**可选**留痕，别为过门禁编标注
- 不批量重构历史笔记；不得自动重写既有主笔记；不自动 `git add -A` / `git commit`

## 并发与新设备
本机多进程由 `.vault.lock`（跨平台互斥锁，POSIX + Windows 通用）保护；跨设备合并由各自的同步方案负责。
新设备只需装一次 `zettelgate` 系统包，再 `zettelgate init <库目录>` 生成 `vault.yaml` —— 规范与门禁不再依赖笔记同步是否覆盖根目录文件。
