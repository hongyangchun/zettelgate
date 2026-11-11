# Doto 方法论真源（只读快照）

> **本目录只读。** 任何 Agent 不得在此修改、追加或"顺手优化"文件内容。
> 方法论正文在这里；本库怎么写，看库根的落地文件。

## 上游

| 项 | 值 |
|---|---|
| 仓库 | `hongyangchun/MySkills`（public） |
| 子目录 | `doto-skills/` |
| 快照 commit | `b4d6e88` |
| 该 commit 日期 | 2026-08-17 12:38:33 +0800 |
| 纳入本库日期 | 2026-11-11 |
| 原书 | Bob Doto, *A System for Writing* (2024) |

仓库里是**方法论提炼，不是全书全文**。本快照只收方法论相关的 9 份 Markdown，
未收 `tools/capacities-batch/`（Capacities 专用脚本，本库已停用 Capacities）、
`platforms/capacities.md`、`platforms/obsidian.md`（别平台驱动）。

## 目录

```
references/doto/
├── SOURCE.md                     ← 本文件（本地维护，非上游原文）
├── book-summary.md               全书结构 / 六要素 / Folgezettel / 关键引语
├── checklists.md                 四套检查清单 + 周/月健康检查
├── note-templates.md             主/参考/枢纽/结构笔记/CLOG 模板
├── glossary.md                   术语中英对照
└── methods/                      四个子技能 + 主入口（工作流正文）
    ├── MAIN_SKILL.md             最高原则与意图路由
    ├── doto-create_SKILL.md      捕捉 → 参考 → 主笔记，ID 分配规则
    ├── doto-connect_SKILL.md     6 种连接类型、禁链接堆砌、Hub/Structure 决策
    ├── doto-write_SKILL.md       Part III：渐进发布、8 步起草、CLOG
    └── doto-audit_SKILL.md       双模式（体检 A / 质检 B），只诊断不动手
```

## 本库如何用它（分层，别混）

| 层 | 文件 | 职责 |
|---|---|---|
| ① 方法论真源 | **本目录** | 书里怎么说。只读，改这里等于改上游口径 |
| ② 可校验原则映射 | `PRINCIPLES.md` | 哪些原则能机判、落在硬 gate 还是诊断、对应代码位置 |
| ③ Logseq 落地 | `ZETTEL.md` / `WRITING.md` / `INGEST.md` / `SCHEMA.md` | 在这个库里具体怎么写、放哪、用哪个命令 |
| ④ 执行 | `scripts/lint.py`（硬 gate）/ `scripts/doto_audit.py`（诊断）/ `scripts/vault.py`（CLI） | 机器强制与报告 |
| ⑤ 两端指针 | `skills/note-vault/SKILL.md` | 只指路，不复制规范正文 |

**为什么不在 `ZETTEL.md` 里复述书**：两边都写正文必然漂移，上次 Capacities 双写就是这么来的。
`ZETTEL.md` 只写「一手六要素 → 本库字段/段落的映射」与「本库与书的差异」。

## 已知的本地差异（用户裁决，优先于书）

1. **Folgezettel ID 留空**，由用户手工填写；agent 不自动编号。
   书里要求必填 → 本库**不设硬 gate**，`doto_audit` 只作诊断提示。
2. **使用记录不手填**：靠 Structure Note / 草稿双链形成的 Logseq 反链自动产生。
   `ZETTEL.md` 的 `## 使用记录` 段是说明位，不是待填字段。
3. **本地扩展段**（书里没有）：`## 支撑材料`、`## 拆分候选`、`## 待建链接`。
   保留是因为用户偏好写足推理/机制/示例；不计入六要素，不得拿来评分。
4. **ID 建议不回写**：`tools/capacities-batch/` 的 `suggest_ids.py` 思路可参考，
   但本库只出建议、不自动写回 property。

## 更新上游

仓库有新 commit 时：整体替换本目录的 9 份文件 → 更新上方 commit/日期 →
**必须复核 `PRINCIPLES.md` 和 `lint.py` 的原则出处是否仍对得上**，
再跑 `vault.py lint` 与 `vault.py audit` 确认没有把新的诊断项误做成硬 gate。
