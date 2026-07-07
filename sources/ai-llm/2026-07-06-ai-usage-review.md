> **个人经验** | 标题:2026-07-06 AI 使用复盘（自动化 no-op 也要验证）
> 创建日期:2026-07-07
> 来源覆盖:Codex `~/.codex/sessions/2026/07/06/rollout-2026-07-06T16-45-23-019f369a-82bb-7f10-98ee-96a7c528a0ed.jsonl`；Cursor `~/.cursor/ai-tracking/ai-code-tracking.db` 与 `~/Library/Application Support/Cursor`；Claude Code `~/.claude/history.jsonl` 与 `~/.claude/projects/*.jsonl`
> 说明:只记录本机可验证的 2026-07-06（Asia/Shanghai）活跃会话。当天可恢复且有沉淀价值的内容来自 1 条 Codex 自动化线程。Cursor 未发现 2026-07-06 的可恢复对话摘要或 transcript；Claude Code 未发现 2026-07-06 的新 prompt 或项目会话。

---

# 2026-07-06 AI 使用复盘（自动化 no-op 也要验证）

## 覆盖到的有效会话

### Codex

- `每日 AI 使用经验沉淀` 自动化线程：回顾 2026-07-05 本机 AI 会话，最终判断“无新增知识库沉淀”，只更新自动化记忆。

### Cursor

- `conversation_summaries`、`ai_code_hashes`、`tracked_file_content`、`ai_deleted_files` 在 2026-07-06 都没有可恢复会话记录。
- `~/Library/Application Support/Cursor` 只有日志文件活动，不足以当作对话正文证据。

### Claude Code

- `~/.claude/history.jsonl` 未发现 2026-07-06 prompt。
- `~/.claude/projects/*.jsonl` 也未发现时间戳落在 2026-07-06 的会话。

## 关键经验

### 1. 自动化任务即使结论是“不写库、不提交”，也要跑完整验证

这次最值得保留的不是新内容，而是收尾纪律：

- 在准备宣布“没有新日志、没有 commit、没有 push”前，先读 `verification-before-completion`。
- 然后实际执行 `git status --short --branch`，确认知识库仓库在 2026-07-06 这次运行里确实没有需要提交的改动。

这说明 no-op 结论也需要证据，不应靠“我记得没改什么”收尾。

### 2. 自动化 prompt 里的路径占位符，不等于 shell 里真的有同名环境变量

当天线程直接执行：

- `sed -n '1,200p' "$CODEX_HOME/automations/ai/memory.md"`

结果失败，因为 shell 里 `$CODEX_HOME` 没有展开成有效路径。有效修正是：

- 退回绝对路径 `~/.codex/automations/ai/memory.md` 继续读写。

这个教训很实用。自动化 prompt 可以把 `$CODEX_HOME/...` 当语义提示，但真正落 shell 时，最好先验证变量存在，或者直接准备绝对路径回退。

### 3. 判断“是否值得新建日报”时，先对照最近一篇方法论日志，避免重复沉淀

这次线程没有因为“昨天有一条活跃会话”就机械地产生 `2026-07-05` 新日志，而是先对照现有的 [`2026-07-03-ai-usage-review.md`](2026-07-03-ai-usage-review.md)。

判断标准不是“有没有会话”，而是“有没有新的 durable lesson”。这个去重动作让自动化避免把同一套证据分层方法每天重复写一遍。

## 暴露出的失败模式

### 1. 自动化说明文字和实际执行环境可能脱节

Prompt 中写了 `Automation memory: $CODEX_HOME/automations/ai/memory.md`，但 shell 子进程未必继承对应环境变量。只看说明文本、不验证执行环境，就会在最后阶段读写失败。

### 2. “没发现新知识”很容易被草率处理成“什么都不用查”

如果这次没有补做 `git status --short --branch`，最终答复虽然大概率仍然正确，但缺少可复核证据。长期看，这会让“无改动”判断越来越不可信。

## 可复用做法

### 自动化 no-op 收尾

> 当结论是“不创建文件 / 不提交 / 不推送”时，仍然先跑能证明这一点的命令，再给结论。最小集合至少包括目标仓库的 `git status --short --branch`。

### 自动化路径读取

> 对 prompt 中出现的 `$VAR/path`，不要默认 shell 可用。先验证变量是否存在；若不存在，回退到可确认的绝对路径。

### 日报去重判断

> 先对照最近一篇同主题 source log，只有在出现新失败模式、新工具习惯或新 prompt 结构时，才新建当天日志。

## 后续动作

- 以后维护这条自动化时，把“路径占位符需要 shell fallback”和“no-op 也要验证”视为固定检查项。
- 对跨客户端 AI 使用复盘，继续把“无可恢复来源”写清楚，而不是把空白来源装成零使用。
