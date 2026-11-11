"""zettelgate 回归测试（标准库 unittest，零第三方依赖）。

每个用例都在临时 vault 上跑，绝不触碰真实笔记库。
覆盖前几轮靠手工验证的结论：G1-G8、违规拦截、add/register 幂等、
audit 恒 0、骨架字段、路径优先级。

运行：python3 -m unittest discover -s tests -v
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from zettelgate import paths  # noqa: E402

CARD = """type:: 原子笔记
folgezettel::
created:: 2026-11-11
origin:: 回归自检
tags::
claim_type::
verified::

# 测试卡

## 单一想法

一个用于回归测试的主张，用自己的话写。

## 支撑材料

- 机制：自检
- 示例：自检
- 反例 / 边界条件 ⚠️：自检

## 出处与引文

- 现场来源：回归自检

## 链接

（暂无已存在的链目标）

## 待建链接

（候选写平文）

## 使用记录

由反链自动形成，不手填。

## 拆分候选

（暂无）
"""

INDEX_HEAD = """# Index
Total pages: 1
Last updated: 2026-11-11

## 原子笔记
- [[测试卡]] — 回归测试用
"""


class VaultTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.v = Path(self.tmp.name) / "vault"
        (self.v / "pages/原子笔记").mkdir(parents=True)
        (self.v / "raw").mkdir()
        (self.v / "index.md").write_text(INDEX_HEAD, encoding="utf-8")
        (self.v / "log.md").write_text("# Log\n", encoding="utf-8")
        (self.v / "vault.yaml").write_text("schema_version: 1\n", encoding="utf-8")
        self.write_card(CARD)

    def tearDown(self):
        self.tmp.cleanup()

    def write_card(self, body, name="测试卡"):
        (self.v / "pages/原子笔记" / f"{name}.md").write_text(body, encoding="utf-8")

    def run_os(self, *args, env_extra=None, vault=True):
        env = os.environ.copy()
        env.pop("ZETTELGATE_VAULT", None)
        env.pop("ZETTELGATE_ADAPTERS", None)
        env["PYTHONPATH"] = str(SRC)
        if env_extra:
            env.update(env_extra)
        cmd = [sys.executable, "-m", "zettelgate"]
        if vault:
            cmd += ["--vault", str(self.v)]
        cmd += list(args)
        return subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(ROOT))

    def assert_ok(self, r, contains=None):
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout}\nstderr={r.stderr}")
        if contains:
            self.assertIn(contains, r.stdout)


class TestHardGate(VaultTestCase):
    def test_01_clean_vault_passes(self):
        self.assert_ok(self.run_os("lint"), "✅ 硬 gate 全部通过")

    def test_02_invalid_folgezettel_blocked(self):
        self.write_card(CARD.replace("folgezettel::\n", "folgezettel:: BAD-ID\n"))
        r = self.run_os("lint")
        self.assertEqual(r.returncode, 1)
        self.assertIn("G3", r.stdout)

    def test_03_empty_folgezettel_is_legal(self):
        """用户裁决：ID 留空是正常状态，不得做成 FAIL。"""
        self.assert_ok(self.run_os("lint"), "留空豁免")

    def test_04_broken_link_blocked(self):
        self.write_card(CARD.replace("（暂无已存在的链目标）", "[[根本不存在的页]] —— 为什么链：自检"))
        r = self.run_os("lint")
        self.assertEqual(r.returncode, 1)
        self.assertIn("G1", r.stdout)

    def test_05_link_dump_blocked(self):
        self.write_card(CARD.replace("（暂无已存在的链目标）", "[[甲]] [[乙]] [[丙]]"))
        r = self.run_os("lint")
        self.assertEqual(r.returncode, 1)
        self.assertIn("G2", r.stdout)

    def test_06_unknown_type_blocked(self):
        self.write_card(CARD.replace("type:: 原子笔记", "type:: 瞎编的类型"))
        r = self.run_os("lint")
        self.assertEqual(r.returncode, 1)
        self.assertIn("G6", r.stdout)

    def test_07_index_gap_blocked(self):
        self.write_card(CARD, name="未登记卡")
        r = self.run_os("lint")
        self.assertEqual(r.returncode, 1)
        self.assertIn("G7", r.stdout)


class TestIdempotency(VaultTestCase):
    def test_08_add_twice_writes_one_entry(self):
        draft = Path(self.tmp.name) / "draft.md"
        draft.write_text(CARD.replace("# 测试卡", "# 新卡"), encoding="utf-8")
        for _ in range(2):
            self.assert_ok(self.run_os("add", str(draft), "--name", "新卡",
                                       "--summary", "幂等自检", "--no-lint"))
        idx = (self.v / "index.md").read_text(encoding="utf-8")
        log = (self.v / "log.md").read_text(encoding="utf-8")
        self.assertEqual(idx.count("[[新卡]]"), 1)
        self.assertEqual(log.count("原子笔记《新卡》"), 1)
        self.assertTrue((self.v / "pages/原子笔记/新卡.md").is_file())

    def test_09_register_twice_writes_one_entry(self):
        d = self.v / "pages/结构笔记"
        d.mkdir(parents=True, exist_ok=True)
        page = d / "自检结构笔记.md"
        page.write_text("type:: 结构笔记\ncreated:: 2026-11-11\n\n# 自检结构笔记\n\n## 核心论点\n\n自检。\n",
                        encoding="utf-8")
        for _ in range(2):
            self.assert_ok(self.run_os("register", str(page), "--summary", "自检", "--no-lint"))
        idx = (self.v / "index.md").read_text(encoding="utf-8")
        log = (self.v / "log.md").read_text(encoding="utf-8")
        self.assertEqual(idx.count("[[自检结构笔记]]"), 1)
        self.assertEqual(log.count("结构笔记《自检结构笔记》"), 1)

    def test_10_add_rejects_incomplete_card(self):
        draft = Path(self.tmp.name) / "bad.md"
        draft.write_text("# 只有标题\n\n没有 type，也没有段落。\n", encoding="utf-8")
        r = self.run_os("add", str(draft), "--name", "坏卡", "--no-lint")
        self.assertEqual(r.returncode, 1)
        self.assertIn("不符合 ZETTEL.md", r.stdout)


class TestAuditAndSkeleton(VaultTestCase):
    def test_11_audit_is_readonly_and_always_zero(self):
        before = {p.name: p.read_bytes() for p in self.v.rglob("*.md")}
        self.assert_ok(self.run_os("audit"), "D16")
        after = {p.name: p.read_bytes() for p in self.v.rglob("*.md")}
        self.assertEqual(before, after, "audit 不得改动任何文件")

    def test_12_new_skeleton_has_optional_fields(self):
        self.assert_ok(self.run_os("new", "自检骨架"), "骨架已生成")
        body = (self.v / "pages/原子笔记/自检骨架.md").read_text(encoding="utf-8")
        for token in ["claim_type::", "verified::", "判断立场", "反链自动形成"]:
            self.assertIn(token, body)
        self.assertNotIn("[[", body, "骨架不得制造断链")

    def test_13_init_only_writes_vault_yaml(self):
        target = Path(self.tmp.name) / "fresh"
        r = self.run_os("init", str(target), vault=False)
        self.assert_ok(r, "vault.yaml")
        self.assertTrue((target / "vault.yaml").is_file())
        self.assertFalse((target / "pages").exists(), "init 不得预建笔记目录")


class TestPaths(unittest.TestCase):
    def setUp(self):
        self._saved_argv = sys.argv
        self._saved_env = os.environ.get("ZETTELGATE_VAULT")
        self._saved_cwd = Path.cwd()
        paths._VAULT_OVERRIDE = None
        self.tmp = tempfile.TemporaryDirectory()
        self.v = Path(self.tmp.name)

    def tearDown(self):
        sys.argv = self._saved_argv
        if self._saved_env is None:
            os.environ.pop("ZETTELGATE_VAULT", None)
        else:
            os.environ["ZETTELGATE_VAULT"] = self._saved_env
        os.chdir(self._saved_cwd)
        self.tmp.cleanup()

    def test_14_explicit_wins(self):
        paths.set_vault("/tmp/never-used")
        try:
            sys.argv = ["zettelgate", "lint"]
            os.environ["ZETTELGATE_VAULT"] = str(Path(self.tmp.name) / "env")
            self.assertEqual(paths.vault_root(str(self.v)), self.v.resolve())
        finally:
            paths.set_vault("")
            paths._VAULT_OVERRIDE = None

    def test_15_argv_over_env(self):
        sys.argv = ["zettelgate", "--vault", str(self.v), "lint"]
        os.environ["ZETTELGATE_VAULT"] = str(Path(self.tmp.name) / "env")
        self.assertEqual(paths.vault_root(), self.v.resolve())

    def test_16_env_over_vault_yaml(self):
        sys.argv = ["zettelgate", "lint"]
        (self.v / "vault.yaml").write_text("schema_version: 1\n", encoding="utf-8")
        other = Path(self.tmp.name) / "other"
        other.mkdir()
        os.environ["ZETTELGATE_VAULT"] = str(other)
        os.chdir(self.v)
        self.assertEqual(paths.vault_root(), other.resolve())

    def test_17_vault_yaml_discovery(self):
        sys.argv = ["zettelgate", "lint"]
        os.environ.pop("ZETTELGATE_VAULT", None)
        (self.v / "vault.yaml").write_text("schema_version: 1\n", encoding="utf-8")
        (self.v / "pages").mkdir()
        os.chdir(self.v / "pages")
        self.assertEqual(paths.vault_root(), self.v.resolve())

    def test_18_missing_vault_raises(self):
        sys.argv = ["zettelgate", "lint"]
        os.environ.pop("ZETTELGATE_VAULT", None)
        os.chdir(self.tmp.name)
        with self.assertRaises(paths.VaultNotConfigured):
            paths.vault_root()

    def test_19_config_has_twelve_types(self):
        cfg = paths.load_config()
        self.assertEqual(len(cfg["types"]), 12)
        self.assertIn("原子笔记", cfg["types"])
        self.assertEqual(cfg["atomic"]["required_properties"], ["type", "folgezettel", "created"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
