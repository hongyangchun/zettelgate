#!/usr/bin/env python3
"""Doto 诊断报告（PRINCIPLES.md 第 3 节 D1-D16；D16 为 AI 时代库规约，见第 5 节）。

只读：不修改任何笔记，不提供 --fix，退出码恒为 0。
依据 doto-audit 模式 A：AI 只诊断不动手 / 不批量重构旧笔记 / 一次最多 15 分钟。
库规约（PRINCIPLES.md 5.3）：Agent 不得依据本报告自动重写既有主笔记。
用法: zettelgate audit   （通常由 zettelgate audit 调用，也可被 cli 进程内调用）

本模块可独立运行，也可被 cli 进程内调用：main() 返回退出码，不自行 sys.exit。
"""
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

try:
    from zettelgate import paths
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from zettelgate import paths


def main():
    V = paths.vault_root()
    CFG = paths.load_config()
    D = CFG["doto"]
    MAX = D["audit_max_items"]
    LINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")

    pages, texts, meta = {}, {}, {}
    for p in (V / "pages").rglob("*.md"):
        pages[p.stem] = p
        texts[p.stem] = p.read_text(encoding="utf-8")
        m = re.search(r"^type::[ \t]*(.+)$", texts[p.stem], re.M)
        meta[p.stem] = m.group(1).strip() if m else "(无 type::)"

    atomic = sorted(n for n, t in meta.items() if t == "原子笔记")
    backlinks = Counter()
    for _name, _text in texts.items():
        for _m in LINK_RE.findall(re.sub(r"`[^`]*`", "", _text)):
            backlinks[_m.strip()] += 1
    out_links = {}
    for n in atomic:
        out_links[n] = [m.strip() for m in LINK_RE.findall(re.sub(r"`[^`]*`", "", texts[n]))]

    def section(text, name):
        """取 ## 段正文；先严格匹配段名，避免「## 链接」被「## 待建链接」抢走。"""
        m = re.search(rf"^##\s+{re.escape(name)}\s*$", text, re.M)
        if not m:
            m = re.search(rf"^##\s*[^\n]*{re.escape(name)}[^\n]*$", text, re.M)
        if not m:
            return ""
        start = m.end()
        nxt = re.search(r"^##\s+", text[start:], re.M)
        return text[start:start + nxt.start()] if nxt else text[start:]

    def diagnose_card(name):
        """返回 (findings, category)；findings 为 (D编号, 说明) 列表。"""
        text = texts[name]
        f = []
        h1 = re.search(r"^#\s+(.+)$", text, re.M)
        title = h1.group(1).strip() if h1 else name
        single = section(text, "单一想法")
        links_sec = section(text, "链接")

        # D1 原子性（只在「单一想法」段内看，减少误报）
        hits = [w for w in D["atomicity_markers"] if w in single]
        if hits:
            f.append(("D1", f"单一想法段出现 {hits}，可能含多个主张"))

        # D2 原创性（引用块占比）
        body_lines = [l for l in text.splitlines() if l.strip() and not l.startswith(("type::", "#"))]
        quotes = [l for l in body_lines if l.lstrip().startswith(">")]
        ratio = len(quotes) / max(len(body_lines), 1)
        if ratio > D["quote_ratio_warning"]:
            f.append(("D2", f"引用块占比 {ratio:.0%}，可能偏摘抄而非自己的话"))

        # D3 标题命题句
        if any(title.startswith(p) for p in D["title_topic_prefixes"]) or \
           any(title.endswith(s) for s in D["title_topic_suffixes"]):
            f.append(("D3", f"标题「{title}」像话题标签，建议改成命题句"))

        # D4 连接理由
        link_lines = [l for l in links_sec.splitlines() if LINK_RE.search(l)]
        no_ctx = [l for l in link_lines
                  if not any(k in l for k in D["context_markers"])]
        if link_lines and no_ctx:
            f.append(("D4", f"{len(no_ctx)}/{len(link_lines)} 条链接缺「为什么链」说明"))

        # D5 来源
        om = re.search(r"^origin::[ \t]*(.*)$", text, re.M)
        origin = om.group(1).strip() if om else ""
        source_sec = section(text, "出处与引文")
        if not origin or (source_sec and ("<" in source_sec or "待填" in source_sec)):
            f.append(("D5", "origin:: 或出处段仍为空/占位符"))

        # D6 ID（只提示，不影响分类）
        fm = re.search(r"^folgezettel::[ \t]*(.*)$", text, re.M)
        id_val = fm.group(1).strip() if fm else ""
        if not id_val:
            f.append(("D6", "Folgezettel ID 留空（用户裁决：待手工填写，不算不合格）"))

        # D7 链接密度 / 完全图
        n = len(out_links[name])
        if n > D["high_link_density"]:
            f.append(("D7", f"{n} 条出链偏高；书里连接质量 > 数量"))

        # D16 证据 / 判断分层（AI 时代库规约，PRINCIPLES.md 第 5 节）
        vm = re.search(r"^verified::[ \t]*(.*)$", text, re.M)
        v_val = vm.group(1).strip() if vm else ""
        if not v_val:
            support = section(text, "支撑材料")
            claim_hits = [w for w in D["claim_signals"] if w in support]
            unit_hits = [u for u in D["claim_number_units"]
                         if re.search(r"\d+\s*" + re.escape(u), support)]
            if claim_hits or unit_hits:
                sample = "、".join((claim_hits + unit_hits)[:3])
                if D["honest_marker"] in text:
                    f.append(("D16", f"含机制/数值断言（{sample}），正文已有 ⚠️ 留痕；"
                                     "可升级为可机读 verified:: / claim_type::（不算不合格）"))
                else:
                    f.append(("D16", f"含机制/数值断言（{sample}）但未标 verified:: "
                                     "—— 请区分核实过的事实与推理类比"))

        # D12 使用记录 = 反链
        f.append(("D12", f"反链 {backlinks[name]} 条（使用记录由反链自动形成，无需手填）"))

        minor = {"D3", "D4", "D5"}
        ids = {x[0] for x in f}
        if "D2" in ids:
            cat = "📦 降级为参考笔记"
        elif "D1" in ids:
            cat = "✂️ 建议拆分"
        elif ids & minor:
            cat = "🔧 小修"
        else:
            cat = "✅ 保持"
        return f, cat

    # ---------- 完全图检测（D7 补充）----------
    aset = set(atomic)
    fully = False
    if len(atomic) >= 3:
        fully = all(aset - {n} <= set(out_links[n]) | {n} for n in atomic)

    results = {n: diagnose_card(n) for n in atomic}
    cats = Counter(cat for _, cat in results.values())

    print(f"📊 Doto 诊断报告 — {date.today().isoformat()}")
    print("=" * 62)
    print("只诊断，不动手修改。一次最多 15 分钟，不批量重构旧笔记。")
    print("依据：references/doto/methods/doto-audit_SKILL.md 模式 A / PRINCIPLES.md（第 5 节：AI 时代依据修订）")
    print("=" * 62)

    print(f"\n━━ 总览 ━━")
    print(f"全库 {len(pages)} 页 | 主笔记 {len(atomic)} 张 | 参考/视频笔记 "
          f"{sum(1 for t in meta.values() if t in CFG['reference_types'])} 页")
    print(f"分类：✅ 保持 {cats['✅ 保持']} · 🔧 小修 {cats['🔧 小修']} · "
          f"✂️ 建议拆分 {cats['✂️ 建议拆分']} · 📦 降级 {cats['📦 降级为参考笔记']}")
    print("（🗑️ 删除不在自动建议范围内 —— 由人决定，`doto-audit_SKILL.md:162-163`）")

    print(f"\n━━ 逐卡诊断（最多列 {MAX} 张）━━")
    for n in atomic[:MAX]:
        f, cat = results[n]
        print(f"\n{cat}  {n}  (反链 {backlinks[n]} / 出链 {len(out_links[n])})")
        for did, msg in f:
            print(f"    · {did} {msg}")
    if len(atomic) > MAX:
        print(f"\n… 另有 {len(atomic) - MAX} 张未展开（时间盒）")

    # ---------- 系统健康检查 ----------
    print("\n━━ 系统健康检查 ━━")
    islands = [n for n in atomic if backlinks[n] == 0]
    ratio = len(islands) / max(len(atomic), 1)
    print(f"D8  主笔记零入链 {len(islands)}/{len(atomic)} ({ratio:.0%}) "
          f"{'⚠️ 超过 50%，关注' if ratio > D['orphan_ratio_warning'] else '· 正常范围'}")
    print("D9  暂时没有连接是正常的，不要为了连接而连接（doto-connect_SKILL.md:160）")
    if fully:
        print(f"D7  ⚠️ {len(atomic)} 张主笔记构成完全图（两两互链）—— 密度偏高，"
              f"建议精简到每卡 2-3 条强链，弱关系降回平文")

    topic_count = Counter()
    for n in atomic:
        tm = re.search(r"^tags::[ \t]*(.*)$", texts[n], re.M)
        if tm:
            for t in CFG["topics"]:
                if t in tm.group(1):
                    topic_count[t] += 1
    mature = [(t, c) for t, c in topic_count.items() if c >= D["hub_threshold"]]
    print(f"D10 Hub Note 触发（同主题 ≥{D['hub_threshold']} 条）："
          f"{'、'.join(f'{t}({c})' for t, c in mature) if mature else '暂无'}"
          f"  | 主题分布：{dict(topic_count) or '未标注'}")

    structs = [n for n, t in meta.items() if t in CFG["structure_types"]]
    print(f"D11 Structure/Hub/CLOG 页 {len(structs)} 张；主笔记集群 {len(atomic)} 条 "
          f"{'（≥3，具备起步写作条件）' if len(atomic) >= D['cluster_threshold'] else ''}")

    refs = [n for n, t in meta.items() if t in CFG["reference_types"]]
    ann = D["annotation_section"]
    missing_ann = [n for n in refs if not re.search(rf"^##\s*[^\n]*{re.escape(ann)}", texts[n], re.M)]
    thin_ann = [n for n in refs if n not in missing_ann and
                sum(1 for k in D["annotation_required"] if k not in section(texts[n], ann)) > 0]
    print(f"D13 批注覆盖（Ch.2 Marginalia 前置）：{len(refs) - len(missing_ann)}/{len(refs)} 页有「## 批注」"
          f"  ⚠️ 缺 {len(missing_ann)} 页、缺必答项 {len(thin_ann)} 页")
    if missing_ann:
        print(f"     示例：{'、'.join(missing_ann[:4])} …（见 INGEST.md；不批量回填历史页）")

    clogs = [n for n, t in meta.items() if t == "CLOG"]
    pending = sum(len([l for l in section(texts[n], "待处理").splitlines()
                       if l.strip().startswith(("-", "*"))]) for n in clogs)
    print(f"D14 CLOG {len(clogs)} 张，待处理 {pending} 项 "
          f"{'⚠️ 超过阈值，建议清理' if pending > D['clog_pending_warning'] else '· 正常'}")

    gaps = [n for n, t in meta.items() if t == "结构笔记"
            and [l for l in section(texts[n], "论证缺口").splitlines() if l.strip().startswith(("-", "*"))]]
    print(f"D15 含「论证缺口」的结构笔记 {len(gaps)} 张 —— 每个缺口都是下一次建卡方向")

    d16 = [n for n in atomic if any(x[0] == "D16" for x in results[n][0])]
    print(f"D16 证据/判断分层：{len(d16)}/{len(atomic)} 张主笔记含未标 verified:: 的机制/数值断言"
          f"  （只提示区分事实与推理，不影响分类、不批量回填）")
    if d16:
        print(f"     示例：{'、'.join(d16[:4])} …（可选字段，见 ZETTEL.md 第 3 节）")

    print("\n" + "=" * 62)
    print(f"⏱  时间盒 {D['audit_timebox_minutes']} 分钟：先从「小修」入手，别一上来就拆笔记；")
    print("   余下的放回队列，三个月后回头看。任何修改都需你逐条确认后由 Agent 执行。")
    print("   本报告为启发式诊断，允许误报；它不改动文件，也不影响 lint 硬 gate。")
    print("   库规约：Agent 不得据此自动重写既有主笔记（PRINCIPLES.md 5.3）；矛盾不覆盖，改动须逐条确认。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
