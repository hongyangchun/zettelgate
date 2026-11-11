#!/usr/bin/env python3
"""LogseqVault 硬 gate（PRINCIPLES.md 第 2 节 G1-G8）。

只做「可客观判定 / 判错代价低 / 书里明确必须或禁止」的检查；
语义类判断一律交给 doto_audit.py 出诊断报告（不阻断、不改文件）。
用法: zettelgate lint   —— 任一 FAIL 退出码 1
类型与参数唯一真源: 包内 config.json

本模块可独立运行，也可被 cli 进程内调用：main() 返回退出码，不自行 sys.exit，
由调用方统一决定进程退出码。
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    from zettelgate import paths
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from zettelgate import paths


def main():
    V = paths.vault_root()
    PAGES = V / "pages"
    CFG = paths.load_config()
    D = CFG["doto"]
    TAGS_TYPE = set(CFG["types"])
    ATOMIC_DIR = V / CFG["atomic"]["dir"]
    SOURCES = D["gate_sources"]

    pages, texts = {}, {}
    for p in PAGES.rglob("*.md"):
        pages[p.stem] = p
        texts[p.stem] = p.read_text(encoding="utf-8")
    raw_names = {p.stem for p in (V / "raw").rglob("*.md")}

    LINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
    issues = defaultdict(list)
    all_links = []

    for name, text in texts.items():
        clean = re.sub(r"`[^`]*`", "", text)  # 行内代码里的 [[示例]] 不算链接
        for m in LINK_RE.finditer(clean):
            all_links.append((name, m.group(1).strip()))

    print(f"页面总数: {len(pages)}  出链总数: {len(all_links)}  type 表: {len(TAGS_TYPE)} 种")
    print("硬 gate 依据: PRINCIPLES.md（语义诊断请用 zettelgate audit）\n")

    # ---- G1 断链 ----------------------------------------------------------
    for s, t in all_links:
        if t not in pages and t not in raw_names:
            issues["G1"].append(f"{s} → [[{t}]]")

    # ---- G6 type 越界 -----------------------------------------------------
    for name, text in texts.items():
        m = re.search(r"^type::[ \t]*(.+)$", text, re.M)
        if m and m.group(1).strip() not in TAGS_TYPE:
            issues["G6"].append(f"{name}: type:: {m.group(1).strip()}")

    # ---- 原子笔记专属（G2/G3/G4/G5）---------------------------------------
    atomic_names = set()
    for name, p in pages.items():
        text = texts[name]
        m = re.search(r"^type::[ \t]*(.+)$", text, re.M)
        if not m or m.group(1).strip() != "原子笔记":
            continue
        atomic_names.add(name)

        # G4 落点
        if ATOMIC_DIR not in p.parents:
            issues["G4"].append(f"{name}: 不在 {CFG['atomic']['dir']}/")

        # G5 骨架（库规约，不是书里六要素原文）
        for sec in CFG["atomic"]["required_sections"]:
            if not re.search(rf"^##\s*.*{re.escape(sec)}", text, re.M):
                issues["G5"].append(f"{name}: 缺段「{sec}」")
        for prop in CFG["atomic"]["required_properties"]:
            if not re.search(rf"^{re.escape(prop)}::", text, re.M):
                issues["G5"].append(f"{name}: 缺 property {prop}::")
        if not re.search(r"^#\s+\S", text, re.M):
            issues["G5"].append(f"{name}: 缺 H1 声明式标题")

        # G2 禁止链接堆砌（Ch.4）：连续裸链接行 / 单行多个裸链接
        clean = re.sub(r"`[^`]*`", "", text)
        bare_run, threshold = 0, D["link_dump_threshold"]
        for line in clean.splitlines():
            links = LINK_RE.findall(line)
            residue = LINK_RE.sub("", line).strip(" \t-*>—:：,，、")
            if links and len(residue) < 4:
                bare_run += 1
                if len(links) >= threshold or bare_run >= threshold:
                    issues["G2"].append(f"{name}: 连续裸链接 ≥{threshold}（{line.strip()[:60]}）")
                    break
            else:
                bare_run = 0

        # G3 ID 格式：留空合法（用户裁决），填了才校验
        fm = re.search(r"^folgezettel::[ \t]*(.*)$", text, re.M)
        if fm:
            val = fm.group(1).strip()
            if val and not re.match(D["folgezettel_pattern"], val):
                issues["G3"].append(f"{name}: folgezettel:: {val} 格式不合法")

    # ---- G7 / G8 index ----------------------------------------------------
    idx = (V / "index.md").read_text(encoding="utf-8")
    # 目录条目 = 以 "- [[" 开头的行；小标题里的 [[X|MOC]] 是导航引用，不算条目
    idx_entry_links = [m.strip() for line in idx.splitlines()
                       if line.lstrip().startswith("- [[")
                       for m in LINK_RE.findall(line)]
    idx_all_links = [m.strip() for m in LINK_RE.findall(idx)]
    for n in sorted(pages):
        if f"[[{n}]]" not in idx:
            issues["G7"].append(n)
    for link, cnt in sorted((k, v) for k, v in Counter(idx_entry_links).items() if v > 1):
        issues["G8"].append(f"重复目录条目 [[{link}]] ×{cnt}")
    for link in sorted(set(idx_all_links)):
        if link not in pages and link not in raw_names:
            issues["G8"].append(f"悬空条目 [[{link}]]")

    # ---- 输出 -------------------------------------------------------------
    for gid in [f"G{i}" for i in range(1, 9)]:
        label = {
            "G1": "断链 = 0", "G2": "禁止链接堆砌", "G3": "Folgezettel 格式（留空豁免）",
            "G4": "原子笔记落点", "G5": "原子笔记骨架", "G6": "type 合法",
            "G7": "index 覆盖所有页", "G8": "index 无悬空/重复",
        }[gid]
        if issues[gid]:
            print(f"[FAIL] {gid} {label} — {len(issues[gid])} 项  «{SOURCES[gid]}»")
            for x in issues[gid][:12]:
                print(f"       {x}")
            if len(issues[gid]) > 12:
                print(f"       … 另有 {len(issues[gid]) - 12} 项")
        else:
            print(f"[PASS] {gid} {label}  «{SOURCES[gid]}»")

    # ---- 观察名单（不阻断）-------------------------------------------------
    linked = {t for _, t in all_links if t in pages}
    excluded = atomic_names if CFG["atomic"]["exclude_from_orphans"] else set()
    orphans = sorted(set(pages) - linked - excluded)
    print(f"\n[观察] 孤儿页（零入链，非门禁）: {len(orphans)}")
    for o in orphans[:10]:
        print(f"       {o}")
    pending = sorted(atomic_names - linked)
    print(f"[观察] 主笔记暂无入链: {len(pending)} —— 书里明确说这是正常的，不要为了连接而连接")
    for a in pending[:10]:
        print(f"       {a}")

    fails = sum(len(v) for v in issues.values())
    print(f"\n{'❌ 硬 gate 未通过' if fails else '✅ 硬 gate 全部通过'}（{fails} 项）"
          f"  主笔记 {len(atomic_names)} 张")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
