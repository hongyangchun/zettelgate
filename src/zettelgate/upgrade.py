#!/usr/bin/env python3
"""zettelgate 升级向导：按 vault.yaml 的 schema_version 提示/引导升级。

原则（与 PRINCIPLES.md 一致）：不自动迁移数据，只提示变更与更新版本标记。
vault.yaml 里的 schema_version 仅是「规范/配置版本」标记，升级只动这个标记，
绝不触碰笔记正文、index.md、log.md。
"""
import re
import sys
from pathlib import Path

try:
    from zettelgate import paths
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from zettelgate import paths

CFG = paths.load_config()
PKG_SCHEMA = int(CFG.get("schema_version", 1))

# 每个目标版本的迁移说明；缺失时回退到 CHANGELOG 提示。
MIGRATIONS = {
    2: (
        "v1 → v2：配置与规范版本标记对齐，无破坏性数据迁移。"
        "升级后请通读 specs/ 确认门禁（G1-G8）与类型定义（config.json）无变化；"
        "笔记正文与 index.md / log.md 均不被触碰。"
    ),
}


def read_version(vault_yaml):
    m = re.search(r"schema_version:\s*(\d+)", vault_yaml.read_text(encoding="utf-8"))
    return int(m.group(1)) if m else 1


def write_version(vault_yaml, version):
    text = vault_yaml.read_text(encoding="utf-8")
    if re.search(r"schema_version:\s*\d+", text):
        text = re.sub(r"schema_version:\s*\d+", f"schema_version: {version}", text)
    else:
        text = text.rstrip() + f"\nschema_version: {version}\n"
    vault_yaml.write_text(text, encoding="utf-8")


def main(apply=False):
    try:
        V = paths.vault_root()
    except paths.VaultNotConfigured as _e:
        print("[ERR] " + str(_e))
        return 2
    if V is None:
        print("[ERR] 未配置笔记库（--vault / ZETTELGATE_VAULT / vault.yaml）")
        return 2
    vault_yaml = V / "vault.yaml"
    if not vault_yaml.exists():
        print(f"[ERR] 未找到 {vault_yaml}，请先 `zettelgate init {V}`")
        return 1

    current = read_version(vault_yaml)
    if current >= PKG_SCHEMA:
        print(f"[PASS] 已是最新 schema_version={current}")
        return 0

    print(f"当前库 schema_version={current}，系统仓要求 {PKG_SCHEMA}。")
    for v in range(current + 1, PKG_SCHEMA + 1):
        note = MIGRATIONS.get(v, f"schema_version 升级到 {v}：见 CHANGELOG.md 与 specs/")
        print(f"  - {note}")
    print()
    if apply:
        write_version(vault_yaml, PKG_SCHEMA)
        print(f"[OK] 已将 {vault_yaml} 的 schema_version 更新为 {PKG_SCHEMA}"
              f"（仅标记，未触碰笔记数据）")
        return 0
    print("确认无数据迁移风险后，运行：")
    print(f"  zettelgate --vault {V} upgrade --apply")
    print("该命令仅更新 vault.yaml 的版本标记，不会改动任何笔记正文。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
