# zettelgate

把 Bob Doto《A System for Writing》的方法论变成一套**可分享、可版本化、可迭代**的笔记库操作系统：
规范写在系统仓里，强制力落在 CLI 与门禁里，任何 Agent 接上同一份适配层就产出同一种笔记。

> 版本 0.1.0（P0）· 纯 Python 标准库，无第三方依赖 · Python ≥ 3.9

## 是什么 / 不是什么

| | |
|---|---|
| ✅ 是 | 规范包 + 命令行工具 + 两档门禁 + 跨 Agent 适配层 + 回归测试 |
| ❌ 不是 | 笔记应用、云同步服务、MCP server、向量数据库，也不是第二个笔记库 |

**系统和数据分开**：`zettelgate/` 里只有规范、代码、测试与只读方法论快照；
笔记正文（`pages/`、`raw/`、`index.md`、`log.md`）永远留在你自己的 `$VAULT`，不进这个仓库。

## 5 分钟上手

```bash
cd zettelgate
./zettelgate init ~/my-vault                 # 只在库根写一份 vault.yaml，不碰笔记正文
./zettelgate --vault ~/my-vault lint        # 硬 gate：0 断链才算健康
./zettelgate --vault ~/my-vault audit       # 诊断报告：只读，看缺口
python3 -m unittest discover -s tests -v # 19 项回归测试
```

零安装即可用（`./zettelgate` 是 wrapper）；也可以 `pip install -e .` 后用全局 `zettelgate` 命令。
库路径三种给法，优先级从高到低：

```
zettelgate --vault <path> lint      # 显式，子命令前后都行
export ZETTELGATE_VAULT=<path>      # 环境变量
cd <vault> && zettelgate lint       # 库根有 vault.yaml 时自动发现
```

## 两档门禁（用户裁决，档位不可混）

| 档 | 命令 | 内容 | 退出码 |
|---|---|---|---|
| **硬 gate** | `zettelgate lint` | G1–G8：断链、链接堆砌、ID 格式（留空豁免）、落点、骨架、type、index 覆盖/悬空 | 失败 = **1**，可被 cron / CI 用 |
| **诊断报告** | `zettelgate audit` | D1–D16：原子性、原创性、标题、连接理由、来源、ID 空缺、链接密度、批注覆盖、证据/判断分层 | **恒为 0**，只读、无 `--fix` |

语义判断一律不进硬 gate。依据是书里「可持续性第一」与 `doto-audit`「只诊断不动手 / 不批量重构 / 15 分钟时间盒」。
`add` / `register` 写后自动跑 lint，不跑 audit。

## 命令

| 命令 | 作用 |
|---|---|
| `new <标题>` | 生成主笔记骨架（Folgezettel 留空、可选 `claim_type::` / `verified::`） |
| `add <草稿.md>` | 主笔记入库：检骨架 + 落盘到 `pages/原子笔记/` + 幂等维护 index/log + 硬 gate |
| `register <pages 内的 .md>` | 其它类型页登记（不检骨架，只维护 index/log + 硬 gate） |
| `lint` | 硬 gate G1–G8；失败退出码 1（`add`/`register` 写后自动跑） |
| `audit` | Doto 诊断 D1–D16；只读、恒为 0（不改文件） |
| `index [--fix]` | 覆盖率、类型分布；默认只读，`--fix` 才刷新头部计数（缺条目返回 1） |
| `init <库目录>` | 生成 `vault.yaml`（只写配置，绝不碰笔记正文） |
| `link [--dry-run]` | 按 `adapters` 配置创建/修复各 Agent 的 skill 软链（`--dry-run` 只预览不创建） |
| `upgrade [--apply]` | 按 vault.yaml 的 `schema_version` 提示/引导升级（只改版本标记，不自动迁移数据） |

所有写入都由 `.vault.lock`（跨平台互斥锁，POSIX + Windows 通用）保护，重复执行不会产生第二条 index/log 条目。

## 目录

```
zettelgate/
├── specs/               # 7 份契约规范（路径已参数化为 $VAULT）
├── src/zettelgate/         # CLI、lint、doto_audit、paths、config.json
├── references/doto/     # 方法论只读快照（见 SOURCE.md，禁止修改）
├── adapters/            # 通用 SKILL.md 指针 + 软链配置说明
├── tests/               # 19 项标准库 unittest 回归测试
├── example-vault/       # 最小可用空库模板
└── MIGRATION.md         # 从既有实例库接入的三步
```

规范与实现的对应：`specs/PRINCIPLES.md`（人读判据）→ `src/zettelgate/config.json`（机读参数）→
`lint.py` / `doto_audit.py`（实现）。**改规则的顺序**：先改 PRINCIPLES → 再改 config → 再改实现 → 跑 tests → 升版本并写 CHANGELOG。

## 可迭代的地基

- 语义化版本 + `CHANGELOG.md`；`vault.yaml` 记 `schema_version`，不兼容时只提示、不自动迁移数据。
- `tests/` 用临时库回归，把「违规页退出码 1」「重复 add 不产生第二条记录」「ID 留空合法」「audit 不改文件」等结论固化。
- `references/doto/` 是**只读快照**，上游更新按 `SOURCE.md` 的复核流程走，不自动拉取。

## 与 Bob Doto 那本书的关系（重要）

本项目的规范来自 **Bob Doto, _A System for Writing_ (2024)** 的方法论提炼，经
`hongyangchun/MySkills/doto-skills` 整理后纳入 `references/doto/`。
那是对书的**二手提炼与章节引用，不是原文**，书的版权归原作者及出版方。

MIT LICENSE 仅覆盖本仓库自己的代码与文字；`references/doto/` 请在遵守原书版权的前提下使用，
本项目不分发原书全文。规范里 G4–G8 与 D16 是本项目新增的库规约，不是书里的条款，已在 `specs/PRINCIPLES.md` 逐条标注。

## 明确不做

- MCP server（本机文件用不着能力通道，规范仍要另放）
- 向量索引 / 语义检索（先用 `index.md` 摘要做两阶段检索）
- 自动拆卡、自动编号、自动重写旧笔记（判断痕迹不可覆盖）
- 自动 `git add -A` / `git commit`（提交范围由人决定）

## 路线图

- **P0（本版）**：独立仓库、路径参数化、19 项测试、文档与示例库；已发布至 GitHub 公开仓库，既有实例库零改动。
- **P1**：两端软链切到 `adapters/`、实例库规范标注为「由系统仓生成」、`upgrade` 命令。
- **P2**：只读索引快照；MCP 薄壳仅在需要远端访问时考虑。
- **CI（可选）**：如需自动跨平台验证（ubuntu + windows，Python 3.9–3.12），新增 `.github/workflows/ci.yml` 跑 `python -m unittest discover -s tests` 即可；需 gh `workflow` scope，按需开启。
