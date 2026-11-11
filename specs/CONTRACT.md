# Vault Contract（写给所有 Agent 的唯一入口）

> 任何 Agent（Hermes / WorkBuddy / 其他）在读写 `$VAULT/` 之前先读本文件。
> 规范正文只在本库内维护，两端 `SKILL.md` 只是指针。建立于 2026-11-11，同日纳入 Doto 方法论契约。

## 1. 唯一真源
- `$VAULT/` 是**唯一真源**。Capacities 双写已于 2026-11-11 停用：不要再跑 `sync_to_capacities.py`，不要做 cap_audit / cap_repair 对账，也不要在 Capacities 侧建对象或属性。
- 跨平台由 **Logseq 官方同步**承担；本地 git 只作版本史，不替代同步。
- **本库的方法论来自 Bob Doto《A System for Writing》(2024)**，经 `hongyangchun/MySkills/doto-skills` 提炼。
  只读快照在 `references/doto/`（见其 `SOURCE.md`），**不得修改**；落地映射在本库根文件里。
  AI 时代的分档依据修订见 `PRINCIPLES.md` 第 5 节 —— **方法论真源不变，只换「为什么保留这项」的理由**。

### 规范清单（按读的顺序）

| 文件 | 管什么 |
|---|---|
| `CONTRACT.md` | 本文件：真源、写入路径、命令、并发 |
| `references/doto/` | **方法论真源（只读）**：全书摘要、清单、模板、术语、四个子技能 |
| `PRINCIPLES.md` | **书的原则 → 可校验项 → 硬 gate / 诊断** 的分档依据；改门禁前先改这里。第 5 节是「AI 时代的分档修订」，**只换依据、不动档位** |
| `SCHEMA.md` | llm-wiki 三层结构：文献笔记 / 视频笔记 / 实体页 / 金句 / MOC（外部来源驱动） |
| `ZETTEL.md` | Doto 主笔记（原子笔记）：一手六要素的 Logseq 落地映射 |
| `WRITING.md` | Part III：Structure / Hub / CLOG / 渐进发布 |
| `INGEST.md` | 外部材料（视频转写等）→ 批注 → 参考笔记 → 主笔记 的转化契约 |
| `platforms/logseq.md` | 10 个平台操作映射 —— 任何 Agent 对得上就能用同一套工作流 |
| `src/zettelgate/config.json` | 类型表与门禁参数唯一真源；新增 `type::` 只改这里 |

## 2. 开工仪式（任何 Agent 必做）
1. 读 `CONTRACT.md` → 按任务类型读对应规范（见上表）
2. **改动门禁或判断「合不合格」前，读 `PRINCIPLES.md`** —— 别把语义判断做成硬 gate
3. 读 `index.md` 查重，读 `log.md` 末 20 行
4. 新主题动手前全库查重（搜概念词，不搜标题词）
5. 写完跑 `zettelgate lint`；**0 断链才算完成**。`zettelgate audit` 是主动体检，不阻断

## 3. 写入路径（统一入口，按类型分流）

| 内容 | 命令 | 落点 | 检查 |
|---|---|---|---|
| 自己的想法 / Doto 主笔记 | `zettelgate new` → 填写 → **`zettelgate add`** | `pages/原子笔记/` | 检 ZETTEL.md 骨架（G5） |
| Structure / Hub / CLOG / 参考笔记 / 视频笔记 | 先按模板落盘 → **`zettelgate register`** | `pages/` 对应目录 | 不检骨架，只检 type/链接/index |
| 既有 scholar-inbox-ingest 进料 | 按 `SCHEMA.md` 原流程落参考笔记，**建议改用 `register` 登记** | `pages/笔记/` | 同上 |

- 两个命令都负责**幂等维护 `index.md` / `log.md`** + 本机文件锁 + 写后硬 gate。
- ⚠️ 禁止直接手改 `index.md` / `log.md`；禁止绕过 CLI 往 `pages/` 落新页（既有 B 路径脚本除外，但应逐步迁移到 `register`，以消除并发写冲突）。
- `.inbox/` 只收 `*.url`（cron 队列），**不要往里投 `.md` 草稿**。
- 本机多进程并发由 `.vault.lock`（flock）保护；跨设备合并由 Logseq 官方同步负责，两端别同时改同一页。

## 4. 两档门禁（用户 2026-11-11 裁决）

| 档 | 命令 | 内容 | 退出码 |
|---|---|---|---|
| **硬 gate** | `zettelgate lint` | G1–G8：断链、链接堆砌、ID 格式（留空豁免）、落点、骨架、type、index 覆盖/悬空 | 失败 = **1**，可被 cron / CI 用 |
| **诊断报告** | `zettelgate audit` | D1–D16：原子性、原创性、标题、连接理由、来源、ID 空缺、链接密度、孤岛、Hub/写作触发、使用记录反链、批注覆盖、CLOG、论证缺口、**证据/判断分层** | **恒为 0**，只读不改文件 |

语义类判断一律不进硬 gate —— 依据是书的第一原则「可持续性」与 `doto-audit`「只诊断不动手 / 不批量重构 / 15 分钟时间盒」。
`PRINCIPLES.md` 第 5 节把分档依据修订到 AI 时代（第一读者是 Agent、稀缺变成 context 预算与可追溯的判断），**档位与退出码一个都没变**。
`add` / `register` 写后自动跑 **lint**，不跑 audit（避免诊断噪音塞进每次写入）。

## 5. 命令速查
```
zettelgate new "声明式标题"       # 主笔记骨架
zettelgate add <草稿.md> --summary "…"   # 主笔记入库
zettelgate register <pages/内的.md> --summary "…"  # 其他页登记
zettelgate lint                  # 硬 gate（阻断）
zettelgate audit                 # Doto 诊断（只读）
zettelgate index [--fix]         # 覆盖率 / 类型分布 [--fix 刷头部]
zettelgate link                  # 修复两端 skill 软链
```
`add` / `register` 都**不自动 git commit**；工作区有其它未提交改动时由人决定提交范围。
**任何 Agent / 定时任务（含 cron）都不得 `git add -A` 或自动 `git commit`** —— 2026-11-11 已同步清理 cron 与两端 skill 中的自动提交指令；提交范围一律由人决定。

## 6. 硬规约
- 元数据用 Logseq properties（页首 `key:: value`），不用 YAML frontmatter
- `[[链接]]` 目标必须逐字等于**已存在**的文件名；候选链接一律写平文，否则 lint 报断链
- 每条链接写明「为什么链」；**禁止连着三个裸链接**（Ch.4，G2）
- **Folgezettel ID 留空由用户手工填写**，agent 不自动编号；填了才校验格式（G3）。编号已是检索基础设施的遗迹，退为可选的人类策展痕迹
- 使用记录靠 Logseq 反链自动形成，**不手填字段**
- `claim_type::` / `verified::` 是**可选的人类判断留痕**（AI 时代新增），不进硬 gate、不校验取值、不逼填；`verified::` 复用 `SCHEMA.md:37` 的同名 property，`true|false` 语义不变。判断立场写在 `## 单一想法` 正文，不建 `stance::` 字段
- **判断痕迹不可覆盖**：`audit` 只读、无 `--fix`；**Agent 不得依据诊断报告自动重写既有主笔记**，任何改动须用户逐条确认（`PRINCIPLES.md` 5.3）。矛盾不覆盖：双方并列 + 日期 + 来源
- 改规范只改本库内文件；两端 `SKILL.md` 是软链/薄指针，**禁止在副本里写规范正文**
- `references/doto/` 只读；上游更新按 `SOURCE.md` 的复核流程走

## 7. 新设备检查（Logseq 官方同步范围待确认）
官方同步若只覆盖 graph 页面，另一台设备可能没有门禁文件。落地后检查：
- [ ] 根目录规范：`CONTRACT.md` / `PRINCIPLES.md` / `SCHEMA.md` / `ZETTEL.md` / `WRITING.md` / `INGEST.md`
- [ ] `references/doto/`（含 `SOURCE.md`）、`platforms/logseq.md`
- [ ] `zettelgate` / `doto_audit.py` / `lint.py` / `vault-config.json`
- [ ] `skills/note-vault/SKILL.md` 存在；两端软链可解析（`zettelgate link` 一键修）
- [ ] `index.md` / `log.md` 为最新
缺失时从主设备拷贝一次（一次性动作），**不要建第二个库、不要在副本里重写规范**。
