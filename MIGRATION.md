# 从既有实例库接入 zettelgate

本文件说明如何把「规范长在笔记库里」的旧形态，平滑切到「系统是独立仓库、数据留在原库」。
**P0 只做第 0 步，原库零改动。**

## 现状（切换前）

```text
~/LogseqVault/
├── CONTRACT.md / PRINCIPLES.md / SCHEMA.md / ZETTEL.md / WRITING.md / INGEST.md
├── scripts/vault.py / lint.py / doto_audit.py / vault-config.json
├── references/doto/ · platforms/ · skills/note-vault/
├── pages/ (195 页) · raw/ (109 份) · index.md · log.md
└── 两端软链指向 skills/note-vault/SKILL.md
```

规范与数据同仓；脚本靠 `V = Path(__file__).parent.parent` 推断库位置；
换设备要靠 Logseq 官方同步把根目录规范也带过去。

## 第 0 步 —— P0（本版已完成，原库不动）

新建独立仓库 `zettelgate`，复制系统文件并参数化路径。两个系统并存：

```bash
cd zettelgate
./zettelgate --vault ~/LogseqVault lint      # 与原 CLI 输出逐字一致
./zettelgate --vault ~/LogseqVault audit
python3 -m unittest discover -s tests -v
```

此时原库的规范、脚本、软链全部照旧工作，随时可退。**不做自动提交，不删任何文件。**

## 第 1 步 —— P1（待用户确认）

1. 给两端宿主配置 adapter 软链目标（见 `adapters/README.md`），跑 `zettelgate link`。
2. 把原库里 `CONTRACT.md` 等规范标注为「由 zettelgate 系统仓生成，勿在此修改」。
3. 定时任务与 agent 配置里的 `python3 ~/LogseqVault/scripts/vault.py ...`
   改为 `zettelgate --vault ~/LogseqVault ...`。
4. 观察一到两周，确认两端产出一致。

> ⚠️ `adapters/SKILL.md` 的 `name` 是 `zettelgate`；若旧软链目录叫 `note-vault`，P1 切换时把目录名一并改成 `zettelgate` 即可，避免宿主索引时目录名与 frontmatter 不一致。

## 第 2 步 —— P2（确认后再做）

- 删除原库内的规范副本与 `scripts/` 里 13 个已停用的双写时代脚本（先归档，不直接删）。
- 原库只保留 `pages/`、`raw/`、`index.md`、`log.md`、`vault.yaml`。
- 推 GitHub、加 CI。

## 回滚

P0 阶段：什么都不用做，原库一直在跑旧 CLI。
P1 之后：删掉新建的 adapter 软链、把配置里的命令改回旧路径即可；
笔记正文从未被本系统改写，不需要数据回滚。

## 一个额外收益

独立之后，新设备只需装一次 `zettelgate` 系统包 + `zettelgate init <库目录>` 就有全套规范与门禁，
**不再依赖 Logseq 官方同步是否覆盖根目录的 `CONTRACT.md` / `scripts/` / `references/`**。
