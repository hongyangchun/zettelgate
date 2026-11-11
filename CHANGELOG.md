# Changelog

本项目使用语义化版本。每次变更遵循：先改 `specs/PRINCIPLES.md` 判据 → 再改
`src/zettelgate/config.json` → 再改实现 → 跑 `python3 -m unittest discover -s tests -v` → 升版本并记本文件。

## 0.1.0 — 2026-11-11

首个可分享的独立版本（P0）。从既有实例库抽出「系统」部分，笔记数据一行未搬。

- **新增** `src/zettelgate/paths.py`：统一解析 `--vault` / `ZETTELGATE_VAULT` / `vault.yaml`，
  去掉三个脚本里 `V = Path(__file__).resolve().parent.parent` 的库位置推断，
  以及 `ADAPTERS` 里硬编码的两个宿主目录。
- **新增** `init` 子命令：只在库根写 `vault.yaml`，不预建目录、不碰笔记正文。
- **新增** `pyproject.toml` / `__main__.py` / `zettelgate` wrapper：零安装可用，也可 `pip install -e .`。
- **新增** `tests/test_zettelgate.py`：19 项标准库 unittest 回归测试，在临时 vault 上覆盖
  G1–G8 拦截、ID 留空豁免、add/register 幂等、audit 只读、骨架字段、路径优先级。
- **新增** `specs/` 7 份契约规范（路径参数化为 `$VAULT`）、`adapters/SKILL.md`、
  `references/doto/` 9 份只读快照 + `SOURCE.md`、`example-vault/` 空库模板。
- **新增** `README` / `LICENSE` / `MIGRATION.md` / `VERSION` / `.gitignore`。
- **验证**：新 CLI 对既有 195 页实例库的 `lint` 输出与原 CLI **逐字一致**（退出码 0）；
  `audit` 恒 0、`index` 195/195 覆盖；实例库 git 状态未新增任何改动。

### 兼容性
- `vault.yaml` 的 `schema_version: 1` 表示库配置的格式版本，与 `config.json` 的 `schema_version: 2` 不是同一件事。
- 本版不提供 `upgrade`，也不自动迁移既有库数据。
