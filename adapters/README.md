# adapters/ — 让任意 Agent 接上同一个库

`SKILL.md` 是**唯一一份**薄指针：只说「读哪份规范、调哪个命令」，不复制规范正文。
各 Agent 宿主通过符号链接指向 `adapters/`，这样改规范只改系统仓一处，不会漂移。

## 配置软链目标

`zettelgate` **不硬编码任何宿主目录**。二选一：

```bash
# 方式 A：环境变量（多路径用 : 分隔）
export ZETTELGATE_ADAPTERS="$HOME/.hermes/skills/productivity/zettelgate:$HOME/.workbuddy/skills/zettelgate"

# 方式 B：配置文件 ~/.config/zettelgate/adapters.json
# {"adapters": ["~/.hermes/skills/productivity/zettelgate", "~/.workbuddy/skills/zettelgate"]}

zettelgate link
```

`link` 会创建缺失的软链、修复指向错误目标的软链，**跳过已存在的真实目录**（不覆盖）。

未配置时 `link` 会打印上面的提示并返回 1，不会往 home 里乱写东西。

## frontmatter 兼容性

两端宿主的 `SKILL.md` frontmatter 核心字段是 `name` / `description` / `version`，
本文件只用这些共有字段（外加 `license` / `tags`），因此同一份文件可直接被两端索引。
若宿主另有专属字段（如 `metadata.*`、`display_name_*`），放在各自的配置里，别写进这份共享指针。

## 换一个 Agent

1. 把它的 skills 目录加进 `ZETTELGATE_ADAPTERS`，跑 `zettelgate link`。
2. 让它读 `specs/CONTRACT.md`，再按任务读对应规范。
3. 对照 `specs/platforms/logseq.md` 的 10 个操作，把 `search` / `read` / `create` / `append` / … 映射到它自己的工具。

接第三个 Agent 不需要改 `src/zettelgate/` 里的代码。
