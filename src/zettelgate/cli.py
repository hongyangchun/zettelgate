#!/usr/bin/env python3
"""zettelgate CLI — 跨 Agent 的唯一写入口与门禁。

规范真源: CONTRACT.md(入口) / SCHEMA.md(文献) / ZETTEL.md(主笔记)
          WRITING.md(Part III) / INGEST.md(外部材料转化) / PRINCIPLES.md(原则→门禁)
方法论只读快照: references/doto/（见其 SOURCE.md）
类型与参数唯一真源: 包内 config.json
所有 Agent 都用本脚本登记页面，由脚本幂等维护 index.md / log.md 并跑硬 gate。
"""
import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

try:
    from zettelgate import paths, lint, doto_audit, upgrade
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from zettelgate import paths, lint, doto_audit, upgrade

try:
    V = paths.vault_root()
except paths.VaultNotConfigured as _e:
    V = None
    _VAULT_ERR = str(_e)
S = paths.PKG_ROOT
CFG = paths.load_config()
PAGES = V / "pages" if V else None
ATOMIC_DIR = V / CFG["atomic"]["dir"] if V else None
INDEX = V / "index.md" if V else None
LOG = V / "log.md" if V else None
LOCK = V / ".vault.lock" if V else None
SKILL_SRC = paths.PROJECT_ROOT / "adapters"
SECTIONS = CFG["index_sections"]


def acquire_lock(timeout=30):
    """跨平台互斥锁（POSIX + Windows 通用）。

    用 O_CREAT|O_EXCL 创建锁文件，成功即获得锁，失败（FileExistsError）即未获得；
    循环重试直到超时。附带 stale 锁清理：锁文件 mtime 超过 STALE 秒视为残留，
    强制删除后重试，避免进程崩溃导致永久死锁。
    返回文件描述符（int），调用方须用 release_lock(fd) 释放。
    """
    STALE = 300  # 5 分钟视为残留
    deadline = time.time() + timeout
    while True:
        if LOCK.exists():
            try:
                if time.time() - LOCK.stat().st_mtime > STALE:
                    LOCK.unlink()
            except OSError:
                pass
        try:
            return os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except FileExistsError:
            if time.time() >= deadline:
                raise RuntimeError(
                    f"无法获取 {LOCK} 上的锁：可能被另一进程占用，或存在残留锁文件"
                )
            time.sleep(0.2)


def release_lock(fd):
    try:
        os.close(fd)
    finally:
        try:
            LOCK.unlink()
        except OSError:
            pass


def slugify(title):
    return re.sub(r"[\s\[\]#|/\\:*?\"<>,，。、「」『』（）()【】]", "", title.strip())


def page_type(text):
    m = re.search(r"^type::[ \t]*(.+)$", text, re.M)
    return m.group(1).strip() if m else "(无 type::)"


def check_card(text):
    """主笔记骨架（库规约 G5，非书里六要素原文）。"""
    errs = []
    if page_type(text) != "原子笔记":
        errs.append("缺 `type:: 原子笔记`")
    for prop in CFG["atomic"]["required_properties"]:
        if not re.search(rf"^{re.escape(prop)}::", text, re.M):
            errs.append(f"缺 property `{prop}::`")
    for sec in CFG["atomic"]["required_sections"]:
        if not re.search(rf"^##\s*.*{re.escape(sec)}", text, re.M):
            errs.append(f"缺段 `## {sec}`")
    if not re.search(r"^#\s+\S", text, re.M):
        errs.append("缺 H1 声明式标题")
    return errs


def refresh_index_header():
    """顺带修 index.md 头部的滞后计数（只在值变化时写）。"""
    text = INDEX.read_text(encoding="utf-8")
    total = len(list(PAGES.rglob("*.md")))
    today = date.today().isoformat()
    new = re.sub(r"Total pages:\s*\d+", f"Total pages: {total}", text)
    new = re.sub(r"Last updated:\s*\d{4}-\d{2}-\d{2}", f"Last updated: {today}", new)
    if new != text:
        INDEX.write_text(new, encoding="utf-8")
        return True
    return False


def add_index_entry(name, summary, section="原子笔记"):
    text = INDEX.read_text(encoding="utf-8")
    link = f"[[{name}]]"
    if link in text:
        return False
    lines = text.splitlines()
    header = f"## {section}"
    try:
        start = lines.index(header)
    except ValueError:
        lines += ["", header]
        start = len(lines) - 1
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    lines.insert(end, f"- {link} — {summary}")
    INDEX.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return True


def add_log_entry(name, src_name, added, kind):
    text = LOG.read_text(encoding="utf-8")
    key = f"{kind}《{name}》"
    if key in text:
        return False
    note = ("- Folgezettel ID 留空待手工填写\n" if "原子笔记" in kind
            else "- 由 vault.py register 登记（非主笔记，不检六要素骨架）\n")
    entry = (
        f"\n\n## [{date.today().isoformat()}] {key}\n"
        f"- 由 vault.py 登记：{src_name}\n"
        f"{note}"
        f"- index 条目：{'新增' if added else '已存在，跳过'}\n"
    )
    LOG.write_text(text.rstrip() + entry, encoding="utf-8")
    return True


def cmd_new(args):
    title = args.title.strip()
    name = slugify(title)
    if not name:
        print("[ERR] 标题清洗后为空")
        return 1
    ATOMIC_DIR.mkdir(parents=True, exist_ok=True)
    target = ATOMIC_DIR / f"{name}.md"
    if target.exists():
        print(f"[ERR] 已存在，未覆盖：{target}")
        return 1
    body = f"""type:: 原子笔记
folgezettel::
created:: {date.today().isoformat()}
origin::
tags::
claim_type::
verified::

# {title}

## 单一想法

<用自己的话写一个主张，完整句子，一卡一想法；写明判断立场：同意什么 / 反对什么 / 据此做什么>

## 支撑材料

- 机制：
- 示例：
- 反例 / 边界条件 ⚠️：

## 出处与引文

- 现场来源：
- 文献来源：
- ⚠️ 未核实内容：
- 可选字段取值（留空正常，不进硬 gate）：claim_type 为 事实/推理/类比/判断/决策；verified 为 true/false/推理/类比/待查

## 链接

（只有已存在的页才能写成 wikilink；每条写明「为什么链」与连接类型：延伸/对比/因果/举例/质疑/跨域）

## 待建链接

（候选方向写平文，注明「候选，建卡后再改 wikilink」）

## 使用记录

由 Logseq 反链自动形成：Structure Note 或草稿引用本卡即产生使用记录，不手填字段。

## 拆分候选

（待填：本卡偏大时可独立成卡的想法）
"""
    target.write_text(body, encoding="utf-8")
    print(f"骨架已生成：{target.relative_to(V)}")
    print("按 ZETTEL.md 六要素填完，再跑：zettelgate add <该文件> --summary \"一句话摘要\"")
    return 0


def cmd_add(args):
    """主笔记（原子笔记）专用入库：检骨架 + 落盘 + 登记 + 硬 gate。"""
    src = Path(args.file).expanduser().resolve()
    if not src.exists():
        print(f"[ERR] 文件不存在：{src}")
        return 1
    text = src.read_text(encoding="utf-8")
    errs = check_card(text)
    if errs:
        print("[ERR] 卡片不符合 ZETTEL.md，未入库：")
        for e in errs:
            print("  -", e)
        return 1
    name = slugify(args.name) if args.name else slugify(src.stem)
    if not name:
        print("[ERR] 页名为空，请用 --name 指定")
        return 1
    ATOMIC_DIR.mkdir(parents=True, exist_ok=True)
    target = ATOMIC_DIR / f"{name}.md"
    m = re.search(r"^#\s+(.+)$", text, re.M)
    summary = args.summary.strip() if args.summary else (m.group(1).strip()[:60] if m else name)

    fd = acquire_lock()
    try:
        same_file = target.resolve() == src
        if not same_file and target.exists():
            if target.read_text(encoding="utf-8") == text:
                print(f"卡片已在库内且内容一致，跳过复制：{target.relative_to(V)}")
            elif args.force:
                target.write_text(text, encoding="utf-8")
                print(f"已按 --force 覆盖：{target.relative_to(V)}")
            else:
                print(f"[ERR] 目标已存在且内容不同，未覆盖：{target}（确认替换请加 --force）")
                return 1
        elif not same_file:
            target.write_text(text, encoding="utf-8")
            print(f"卡片落盘：{target.relative_to(V)}")
        else:
            print(f"卡片已在库内：{target.relative_to(V)}")
        idx_added = add_index_entry(name, summary, SECTIONS.get("原子笔记", "原子笔记"))
        log_added = add_log_entry(name, src.name, idx_added, "create | 原子笔记")
        refresh_index_header()
        print(f"index 条目：{'新增' if idx_added else '已存在，跳过'}"
              f"　log 条目：{'追加' if log_added else '已存在，跳过'}")
    finally:
        release_lock(fd)

    if args.no_lint:
        print("（已跳过 lint）")
        return 0
    print("\n--- 硬 gate lint ---")
    return lint.main()


def cmd_register(args):
    """通用登记：Structure / Hub / CLOG / 参考笔记等已在库内的页面。

    不复制文件、不检主笔记骨架，只幂等维护 index/log 并跑硬 gate。
    这样路径 B（既有进料管线）也能逐步收敛到 CLI 单一入口，避开 index/log 并发写。
    """
    src = Path(args.file).expanduser().resolve()
    if not src.exists():
        print(f"[ERR] 文件不存在：{src}")
        return 1
    if PAGES not in src.parents:
        print(f"[ERR] 页面须先落盘到 {PAGES}/ 内，register 不负责复制文件：{src}")
        return 1
    text = src.read_text(encoding="utf-8")
    ptype = page_type(text)
    if ptype == "原子笔记":
        print("[ERR] 主笔记请走 zettelgate add（需检 ZETTEL.md 骨架）")
        return 1
    if ptype not in CFG["types"]:
        print(f"[ERR] type:: {ptype} 不在 vault-config.json 的 types 中")
        return 1
    name = src.stem
    m = re.search(r"^#\s+(.+)$", text, re.M)
    summary = args.summary.strip() if args.summary else (m.group(1).strip()[:60] if m else name)
    section = args.section or SECTIONS.get(ptype, ptype)

    fd = acquire_lock()
    try:
        idx_added = add_index_entry(name, summary, section)
        log_added = add_log_entry(name, src.name, idx_added, f"register | {ptype}")
        refresh_index_header()
        print(f"登记 {ptype}《{name}》→ index 段「{section}」：{'新增' if idx_added else '已存在，跳过'}"
              f"　log：{'追加' if log_added else '已存在，跳过'}")
    finally:
        release_lock(fd)

    if args.no_lint:
        print("（已跳过 lint）")
        return 0
    print("\n--- 硬 gate lint ---")
    return lint.main()


def cmd_lint(args):
    return lint.main()


def cmd_audit(args):
    return doto_audit.main()


def cmd_index(args):
    pages = {p.stem: p for p in PAGES.rglob("*.md")}
    idx = INDEX.read_text(encoding="utf-8")
    missing = sorted(n for n in pages if f"[[{n}]]" not in idx)
    types = Counter(page_type(p.read_text(encoding="utf-8")) for p in pages.values())
    print(f"页面总数: {len(pages)}　index 覆盖: {len(pages) - len(missing)}/{len(pages)}")
    print("类型分布: " + ", ".join(f"{k} {v}" for k, v in types.most_common()))
    if args.fix:
        changed = refresh_index_header()
        print(f"index 头部：{'已刷新（页数/日期）' if changed else '已是最新'}")
    if missing:
        print(f"\n[FAIL] index 缺条目 {len(missing)} 条:")
        for n in missing:
            print("  -", n)
        return 1
    print("[PASS] index 完整")
    return 0


def cmd_link(args):
    if not SKILL_SRC.exists():
        print(f"[ERR] 技能源目录不存在：{SKILL_SRC}")
        return 1
    dry = getattr(args, "dry_run", False)
    print(f"技能源：{SKILL_SRC}")
    targets = paths.adapters()
    if not targets:
        print("未配置 adapters。设置 ZETTELGATE_ADAPTERS（多路径用 : 分隔），")
        print('或写 ~/.config/zettelgate/adapters.json：{"adapters": ["<软链目标>"]}')
        return 1
    if dry:
        print("[DRY-RUN] 以下为将执行的软链操作（不实际创建/修改）：")
    for t in targets:
        t.parent.mkdir(parents=True, exist_ok=True)
        if t.is_symlink():
            if t.resolve() == SKILL_SRC.resolve():
                line = f"  [OK]     {t}"
            else:
                line = f"  [修复]   {t}  ->  {SKILL_SRC}（先删旧链再建）"
        elif t.exists():
            line = f"  [跳过]   {t} 已是真实目录，未覆盖"
        else:
            line = f"  [新建]   {t}  ->  {SKILL_SRC}"
        print(("[DRY-RUN] " if dry else "") + line)
        if dry:
            continue
        if t.is_symlink():
            if t.resolve() == SKILL_SRC.resolve():
                continue
            t.unlink()
            t.symlink_to(SKILL_SRC, target_is_directory=True)
        elif t.exists():
            continue
        else:
            t.symlink_to(SKILL_SRC, target_is_directory=True)
    return 0

def cmd_init(args):
    """只在目标库根写一份 vault.yaml，绝不改动笔记正文或 index/log。"""
    target = Path(args.path).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    conf = target / "vault.yaml"
    if conf.exists():
        print(f"配置已存在，未覆盖：{conf}")
    else:
        conf.write_text(f"schema_version: {CFG['schema_version']}\n", encoding="utf-8")
        print(f"已写入 {conf}")
        print("zettelgate 不改动笔记正文；用 --vault 或 ZETTELGATE_VAULT 指向本库即可。")
    return 0


def cmd_upgrade(args):
    """按 vault.yaml 的 schema_version 提示/引导升级（不自动迁移数据）。"""
    return upgrade.main(args.apply)


def main():
    ap = argparse.ArgumentParser(prog="zettelgate", description="zettelgate — Doto 式笔记库唯一写入口与两档门禁")
    ap.add_argument("--vault", help="笔记库路径（也可放在子命令后，或设 ZETTELGATE_VAULT）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="生成主笔记骨架")
    p.add_argument("title", help="声明式标题")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("add", help="主笔记入库（检骨架 + index/log + 硬 gate）")
    p.add_argument("file", help="草稿或已写好的卡片 .md")
    p.add_argument("--name", help="页名（默认取文件名）")
    p.add_argument("--summary", help="index 里的一句话摘要")
    p.add_argument("--force", action="store_true", help="允许覆盖同名卡片")
    p.add_argument("--no-lint", action="store_true", help="跳过写后硬 gate")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("register", help="通用登记：Structure/Hub/CLOG/参考笔记等非主笔记页")
    p.add_argument("file", help="已在 pages/ 内的 .md")
    p.add_argument("--summary", help="index 里的一句话摘要")
    p.add_argument("--section", help="覆盖默认 index 分节")
    p.add_argument("--no-lint", action="store_true", help="跳过写后硬 gate")
    p.set_defaults(func=cmd_register)

    p = sub.add_parser("lint", help="硬 gate G1-G8（失败退出码 1）")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("audit", help="Doto 诊断报告（只读，恒为 0）")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("index", help="index 覆盖率与类型分布")
    p.add_argument("--fix", action="store_true", help="刷新头部页数/日期")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("link", help="创建/修复各 Agent 的 skill 软链")
    p.add_argument("--dry-run", action="store_true", help="只打印将执行的软链操作，不实际创建")
    p.set_defaults(func=cmd_link)

    p = sub.add_parser("init", help="在笔记库根生成 vault.yaml（不改动笔记正文）")
    p.add_argument("path", help="笔记库目录")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("upgrade", help="按 schema_version 提示/引导升级（不自动迁移数据）")
    p.add_argument("--apply", action="store_true", help="仅更新 vault.yaml 版本标记，不改动笔记数据")
    p.set_defaults(func=cmd_upgrade)

    for sp in sub.choices.values():
        sp.add_argument("--vault", dest="vault_in_sub",
                        help="笔记库路径（也可放在子命令前，或用 ZETTELGATE_VAULT）")

    args = ap.parse_args()
    vault_arg = args.vault or getattr(args, "vault_in_sub", None)
    if vault_arg:
        paths.set_vault(vault_arg)
    if args.cmd not in ("init", "link") and V is None:
        print("[ERR] " + _VAULT_ERR)
        sys.exit(2)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
