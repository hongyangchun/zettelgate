#!/usr/bin/env python3
"""zettelgate 路径解析 —— 唯一负责回答「笔记库在哪 / 配置在哪 / 适配器在哪」。

优先级（高 → 低）：
  1. set_vault() / vault_root(explicit=...)     显式传入
  2. 命令行 --vault <path>                      脚本独立运行时（参数位置不限）
  3. 环境变量 ZETTELGATE_VAULT
  4. 从当前工作目录向上找 vault.yaml（最多 5 层）
  5. VaultNotConfigured —— 提示先跑 zettelgate init

系统仓与笔记库彼此独立：规范 / CLI / 门禁在本包，笔记数据只在 $VAULT。
本模块不得引用任何用户绝对路径或宿主（Hermes / WorkBuddy）专用目录。
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

PKG_ROOT = Path(__file__).resolve().parent          # src/zettelgate
PROJECT_ROOT = PKG_ROOT.parents[1]                  # zettelgate/
CONFIG_FILE = PKG_ROOT / "config.json"

_VAULT_OVERRIDE: Optional[Path] = None


class VaultNotConfigured(RuntimeError):
    """找不到笔记库时抛出，交调用方决定如何提示。"""


def set_vault(path) -> None:
    global _VAULT_OVERRIDE
    _VAULT_OVERRIDE = Path(path).expanduser().resolve()


def _from_argv():
    argv = sys.argv[1:]
    for flag in ("--vault", "-v"):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 < len(argv):
                return argv[i + 1]
    for a in argv:
        if a.startswith("--vault="):
            return a.split("=", 1)[1]
    return None


def _find_vault_yaml(start: Path):
    cur = start.resolve()
    for _ in range(5):
        f = cur / "vault.yaml"
        if f.is_file() and "schema_version" in f.read_text(encoding="utf-8", errors="ignore"):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def vault_root(explicit=None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    if _VAULT_OVERRIDE:
        return _VAULT_OVERRIDE
    a = _from_argv()
    if a:
        return Path(a).expanduser().resolve()
    e = os.environ.get("ZETTELGATE_VAULT")
    if e:
        return Path(e).expanduser().resolve()
    found = _find_vault_yaml(Path.cwd())
    if found:
        return found
    raise VaultNotConfigured(
        "未指定笔记库。任选其一：\n"
        "  zettelgate --vault <path> lint\n"
        "  export ZETTELGATE_VAULT=<path>\n"
        "  在笔记库根放一份 vault.yaml（schema_version: 1）后在该目录运行\n"
        "  zettelgate init <path>  可生成配置"
    )


def load_config(path=None) -> dict:
    """类型表与门禁参数的唯一真源；默认读系统包内的 config.json。"""
    p = Path(path) if path else CONFIG_FILE
    return json.loads(p.read_text(encoding="utf-8"))


def adapters() -> list:
    """返回各 Agent 的 skill 软链目标；不硬编码任何宿主路径。

    来源二选一：环境变量 ZETTELGATE_ADAPTERS（os.pathsep 分隔），
    或 ~/.config/zettelgate/adapters.json 里的 {"adapters": [...]}。
    两者都没有时返回空列表，由调用方提示如何配置。
    """
    env = os.environ.get("ZETTELGATE_ADAPTERS", "")
    items = [x for x in env.split(os.pathsep) if x] if env else []
    cfg = Path.home() / ".config/zettelgate/adapters.json"
    if not items and cfg.is_file():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            items = data.get("adapters", []) if isinstance(data, dict) else list(data)
        except (json.JSONDecodeError, OSError, TypeError):
            items = []
    return [Path(x).expanduser() for x in items]


_PAGES_DIR_RE = re.compile(r"^pages_dir:\s*(.+?)\s*$", re.M)


def vault_conf(vault=None) -> dict:
    """读笔记库根的 vault.yaml，返回笔记目录等配置（缺省给默认）。

    当前支持 pages_dir（默认 "pages"）——Tolaria 等后端若把笔记放在其他
    目录（例如库根扁平存放），在 vault.yaml 里写 `pages_dir: .` 即可。
    无 vault.yaml 或未配置时回退默认，不抛异常。
    """
    try:
        v = vault or vault_root()
    except VaultNotConfigured:
        v = None
    data = {"pages_dir": "pages"}
    if v is not None:
        f = v / "vault.yaml"
        if f.is_file():
            m = _PAGES_DIR_RE.search(f.read_text(encoding="utf-8", errors="ignore"))
            if m:
                data["pages_dir"] = m.group(1).strip()
    return data
