# example-vault

最小可用的空库模板：一张合规的原子笔记 + `index.md` / `log.md` / `vault.yaml`。
用来验证装好之后系统是否正常工作，也可以复制成自己的新库起点。

```bash
cd zettelgate
./zettelgate --vault ./example-vault lint     # 预期：G1–G8 全绿，退出码 0
./zettelgate --vault ./example-vault audit    # 预期：恒为 0，列出诊断缺口
./zettelgate --vault ./example-vault index    # 预期：1/1 覆盖
./zettelgate --vault ./example-vault new "我的第一条想法"
```

`vault.yaml` 只有一行 `schema_version: 1`；库根有它时，也可以在库目录里直接跑 `zettelgate lint`。

⚠️ 系统仓不会自动往这里写笔记：`add` / `register` 只在你显式指定 `--vault` 的库里落盘。
