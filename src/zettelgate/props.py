#!/usr/bin/env python3
"""zettelgate 属性解析 —— 兼容两种笔记格式的 property 读取。

支持：
  - Tolaria / YAML frontmatter:  文件开头 `---` 块内的 `key: value`
  - Logseq 内联属性:             行首 `key:: value`

类型与参数真源见 config.json；本模块只负责从文本抽出 property 值，
让 lint / audit / CLI 对两种存储后端（Logseq、Tolaria）一视同仁。
"""
import re
from typing import Optional

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def _strip_yaml_scalar(v: str) -> str:
    """剥离 YAML 标量的引号包裹（'...' 或 \"...\"）。"""
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    return v


def extract_property(text: str, key: str) -> Optional[str]:
    """取属性值，兼容 YAML frontmatter 与 Logseq 内联。

    优先 frontmatter（YAML），其次内联 `key::`。返回首个匹配的去尾空白值；
    无匹配返回 None。值若被 YAML 引号包裹会被剥离。
    """
    fm = _FRONTMATTER_RE.match(text)
    if fm:
        for line in fm.group(1).splitlines():
            m = re.match(rf"^{re.escape(key)}:\s*(.*)$", line)
            if m:
                return _strip_yaml_scalar(m.group(1).strip())
    m = re.search(rf"^{re.escape(key)}::[ \t]*(.*)$", text, re.M)
    if m:
        return m.group(1).strip()
    return None


def page_type(text: str) -> Optional[str]:
    """取 type 属性；无则返回 None（调用方决定默认值）。"""
    return extract_property(text, "type")
