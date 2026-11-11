# 平台驱动：LogseqVault

> 按 `references/doto/.../PLATFORM_TEMPLATE.md`（上游模板见 `references/doto/SOURCE.md`）的 10 个操作填出本库映射。
> **不管接什么 Agent（WorkBuddy / Hermes / 其他），只要对得上这 10 个操作，就能用同一套 Doto 工作流。**
> 模板原本在上游仓库 `platforms/` 目录，本库不复制 obsidian / capacities 两份驱动；这份是 Logseq 专属。

---

## 初始化（3 步）

1. 读 `$VAULT/CONTRACT.md`（唯一入口）→ 按任务读 `ZETTEL.md` / `WRITING.md` / `INGEST.md` / `SCHEMA.md`
2. 确认 `zettelgate`、`vault-config.json`、`lint.py`、`doto_audit.py` 存在；缺则按 `CONTRACT.md:48-54` 从主设备拷一次
3. 跑 `zettelgate link` 修两端 skill 软链，`zettelgate lint` 确认 0 断链

---

## 操作映射（10 项）

| 操作 | 用途 | 本库工具 | 具体写法 |
|---|---|---|---|
| **search** | 查重 / 找候选连接 | Grep / Glob | `rg -n "<概念词>" $VAULT/pages $VAULT/raw`；先搜 `index.md`，再搜正文。**搜概念词，不搜标题词**（`doto-connect_SKILL.md:42-46`） |
| **read** | 读完整页 | Read | `$VAULT/pages/**/<页名>.md`；引用前必读全文，别只看摘要 |
| **create** | 建主笔记 | `zettelgate new` → 填写 → `zettelgate add` | `zettelgate new "声明式标题"`，骨架落 `pages/原子笔记/`；写完 `zettelgate add <文件> --summary "一句话"` 才登记 index/log + lint |
| **create**（其他页） | Structure / Hub / CLOG / 参考笔记 | 写文件 → `zettelgate register` | 按 `WRITING.md` / `INGEST.md` 模板写好 `.md`，再 `zettelgate register <文件> --summary "一句话"` |
| **append** | 追加连接 / 批注 | Edit 已有页 | 追加到 `## 链接` 或 `## 批注` 段末尾；每条 `[[ ]]` 必带「为什么链」；改完跑 `zettelgate lint` |
| **update** | 改元数据 | Edit 页首 properties | `key:: value` 格式（`folgezettel::` 由用户手工填，agent 不写）；改 `type::` 前先改 `vault-config.json` |
| **quickCapture** | 临时想法 | 纯文本收件箱 | `$VAULT/fleeting.md`，格式 `💡 {一句话}` + 日期；**不在 `pages/` 内、不进 lint、不预建**，第一次用时创建。⚠️ 别投 `.inbox/`（那里只收 cron 的 `*.url`） |
| **linkSyntax** | 互链格式 | Logseq wikilink | `[[页名]] — 为什么链`；目标**逐字等于已存在的文件名**；候选写平文 |
| **idProperty** | ID 存哪 | 页首 property | `folgezettel::`（**留空，用户手工填**）；格式若填须为 `数字.数字 + 字母数字延伸`，如 `3.2a1b`（G3） |
| **notesDir** | 主笔记落点 | 目录 | `$VAULT/pages/原子笔记/`；参考笔记 `pages/笔记/`；Structure/Hub/CLOG 见 `WRITING.md` |
| **getAllIds** | 取已有 ID 分配新号 | Grep + 报告 | `rg -n '^folgezettel::' pages/原子笔记/`；`zettelgate audit` 报告 ID 空缺与建议主题号。**只出建议、不自动回写**（`SOURCE.md` 本地差异 4） |

---

## 笔记模板（主笔记 / Zettel）

```
type:: 原子笔记
folgezettel::
created:: YYYY-MM-DD
origin:: <现场来源：与谁、何时、由什么引出>
tags::
claim_type:: <事实 | 推理 | 类比 | 判断 | 决策>   # 可选，不进硬 gate
verified:: <true | false | 推理 | 类比 | 待查>   # 可选，复用 SCHEMA.md:37 的语义

# <标题：一句完整的话概括这个想法>

## 单一想法
<用自己的话写的原子主张，完整句子>

## 支撑材料
- 机制：
- 示例：
- 反例 / 边界条件 ⚠️：

## 出处与引文
- 现场来源：
- 文献来源：

## 链接
- [[已有页名]] — 为什么链（连接类型）

## 待建链接
（候选方向写平文）

## 使用记录
（由 Logseq 反链自动形成，不手填）

## 拆分候选
（可独立成卡的想法）
```

> 段的性质与出处见 `ZETTEL.md:4`；「支撑材料 / 待建链接 / 拆分候选」是本库扩展，不计入 Doto 六要素。

---

## 链接示例

```markdown
✅ 带上下文：[[分辨先于处置]] — 对比：本卡讲「什么时候动手」，那张讲「动手前先要能分辨」
❌ 裸链接堆砌：[[A]] [[B]] [[C]]          ← 硬 gate G2 直接 FAIL
✅ 暂时无连接：正常，不要为了连接而连接（`doto-connect_SKILL.md:160`）
```

---

## 门禁（两档）

| 命令 | 档位 | 退出码 |
|---|---|---|
| `zettelgate lint` | 硬 gate（G1–G8） | 失败 = 1，可被 cron / CI 用 |
| `zettelgate audit` | 诊断报告（D1–D16） | 恒为 0，只出报告、不改文件 |

依据与逐项出处见 `PRINCIPLES.md`（第 5 节是 AI 时代的依据修订，**只换理由、不动档位**）。`zettelgate add` 写后自动跑 lint，不跑 audit。

---

## 边界

- 不复制 Capacities / Obsidian 驱动进本库；也不接 Capacities API（双写已于 2026-11-11 停用）
- 下载 / 抓流 / ASR 由 Hermes `link-to-transcript` 负责，本驱动只管「交出来的东西怎么入库」，见 `INGEST.md`
- 不预建空目录、不预设主题分区（受控混乱，Ch.6）
- **不得依据 audit 报告自动重写既有主笔记**（`PRINCIPLES.md` 第 5.3 节库规约）：诊断只贴标签，任何改动须用户逐条确认；矛盾按 `SCHEMA.md`「不覆盖」处理
