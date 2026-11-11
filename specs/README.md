# specs/ — 契约规范

这 7 份文档是系统的**方法论真源落地物**，按读的顺序排列：

| 文件 | 管什么 |
|---|---|
| `CONTRACT.md` | 唯一入口：真源、写入路径、命令、并发、硬规约 |
| `PRINCIPLES.md` | 书的原则 → 可校验项 → 硬 gate / 诊断 的分档依据；第 5 节是 AI 时代依据修订 |
| `SCHEMA.md` | llm-wiki 三层结构：文献笔记 / 视频笔记 / 实体页 / 金句 / MOC |
| `ZETTEL.md` | Doto 主笔记（原子笔记）：一手六要素的 Logseq 落地映射 |
| `WRITING.md` | Part III：Structure / Hub / CLOG / 渐进发布 |
| `INGEST.md` | 外部材料（视频转写等）→ 批注 → 参考笔记 → 主笔记 的转化契约 |
| `platforms/logseq.md` | 10 个平台操作映射 —— 任何 Agent 对得上就能用同一套工作流 |

## 与实例库的差异

本目录从产生这套系统的实例库复制而来，做了**路径参数化**（不改语义）：

- `~/LogseqVault/` → `$VAULT/`（笔记库根目录，由 `--vault` / `ZETTELGATE_VAULT` / `vault.yaml` 解析）
- `python3 ~/LogseqVault/scripts/vault.py ...` → `zettelgate ...`
- `scripts/vault-config.json` → `src/zettelgate/config.json`
- `.hermes` / `.workbuddy` 的绝对路径 → `<宿主 skills 目录>` / `adapters` 软链目标

`references/doto/` 在系统仓内保持同名路径，`SOURCE.md` 锁上游版本，**禁止修改**。

## 通用规约 vs 实例约定

| 类型 | 例子 | 换环境时 |
|---|---|---|
| 通用（书里的方法论） | 一卡一想法、用自己的话、带上下文的链接、只诊断不动手、可持续性第一 | 不动 |
| 通用（本项目库规约） | G1–G8 硬 gate、D1–D16 诊断、判断痕迹不可覆盖、`claim_type::` / `verified::` | 不动，改动走 CHANGELOG |
| 实例约定 | 「跨平台由 Logseq 官方同步承担」、`pages/笔记/` 这类目录名、cron 队列 `.inbox/*.url` | 按你的存储与调度方式改写，但要在自己的 CONTRACT 里写清楚 |

⚠️ 换句话说：**这份 specs 是可以直接拿去用的默认配置，不是不可修改的教条**。
改门禁分档前先读 `PRINCIPLES.md`，改完记得同步 `config.json` 与测试。

## 上游与版权

方法论来自 **Bob Doto, _A System for Writing_ (2024)**，经 `hongyangchun/MySkills/doto-skills`
提炼成 `references/doto/` 的只读快照。那是二手提炼与章节引用，**不是原书全文**；
书的版权归原作者及出版方，本项目不分发原文。
