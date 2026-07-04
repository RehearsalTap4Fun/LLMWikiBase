> **个人经验** | 标题:2026-07-03 AI 使用复盘（证据优先的跨客户端回顾与发布前验证）
> 创建日期:2026-07-04
> 来源覆盖:Codex `~/.codex/sessions/2026/07/03/*.jsonl`；Cursor `~/.cursor/ai-tracking/ai-code-tracking.db` 与 `~/.cursor/projects/**/agent-transcripts/**/*.jsonl`；Claude Code `~/.claude/history.jsonl` 与 `~/.claude/projects/*/*.jsonl`
> 说明:只记录本机可验证的 2026-07-03（Asia/Shanghai）活跃会话。当天有可恢复内容的来源是 Codex；未发现 Cursor 或 Claude Code 在当天的可恢复活跃会话。

---

# 2026-07-03 AI 使用复盘（证据优先的跨客户端回顾与发布前验证）

## 覆盖到的有效会话

### Codex

- `每日 AI 使用经验沉淀` 自动化线程：回顾 2026-07-02 本机 AI 使用情况，先确认各客户端的本地日志落点，再决定是否落库、提交和推送。
- `TDGame` 发布整理线程：在 `/Users/tap4fun/Documents/TDGame` 中配置远端、检查当前分支状态、验证 `npm test` 与 `npm run build`，然后提交并推送 `codex/dungeon-defense-web-prototype`。

### Cursor

- `ai-code-tracking.db` 的 `conversation_summaries` 仍为空。
- `agent-transcripts` 没有文件修改时间落在 2026-07-03 的样本。
- 结论是“未发现当天可恢复活跃会话”，不是“当天一定没用过 Cursor”。

### Claude Code

- `~/.claude/history.jsonl` 未发现 2026-07-03 prompt。
- `~/.claude/projects/*/*.jsonl` 也未发现时间戳落在 2026-07-03 的会话。
- 因此当天经验总结不纳入 Claude Code 样本。

## 关键经验

### 1. 跨客户端复盘要先定“证据层级”，不要直接按文件名或主观记忆下结论

这次最稳的做法是先把证据源分层：

- Codex 用 session `jsonl` 的内嵌时间戳和工具调用记录。
- Claude Code 用项目 `jsonl` 与 `history.jsonl` 的内嵌时间戳。
- Cursor 先看 `ai-tracking` 数据库，没有摘要时再退回 `agent-transcripts` 和文件修改时间。

这样做的价值在于：可以明确区分“当天没有可恢复日志”和“当天没有使用”。对长期自动化复盘，这是必要的边界感。

### 2. 自动化总结任务，先做日志发现，再做经验抽象，比直接写总结更可靠

当天 Codex 自动化线程没有一开始就写“昨天学到了什么”，而是先做三步：

- 读自动化记忆，避免重复沉淀同一天内容。
- 枚举 Codex、Cursor、Claude Code 的本地存储位置。
- 按日历日时间窗筛出真正活跃的会话，再从里面抽经验。

这个顺序值得固定下来。否则很容易把旧样本、缓存文件或者空数据库误当成当天证据。

### 3. 对发布/推送任务，把“边界”说清楚，Agent 就不容易擅自扩 scope

`TDGame` 线程里比较有效的一点，是先把任务边界收紧成：

- 配置远端。
- 提交当前项目状态。
- 运行可用检查。
- 推送当前分支。

并且显式说明“这次不是开 PR”。这类约束很有用，因为很多 AI 在遇到 git 任务时会默认补做 PR、标签、说明文档等额外动作。

### 4. Git 发布前先查最小事实集合，可以减少无效往返

这次推送前先读的是：

- `git status --short --branch`
- `git remote -v`
- `git branch --show-current`
- `git diff --stat`
- `git log --oneline -5`
- `package.json`

这是一个很实用的最小检查集。它能快速回答四个问题：当前改了什么、要往哪推、所在分支是什么、项目有没有现成的验证命令。

### 5. “能 push” 不等于“值得 push”，发布前验证仍然要落到命令

当天的发布线程在提交和推送前明确跑了：

- `npm test`
- `npm run build`

然后才报告分支、提交号和 upstream。这个顺序比“先推上去再看 CI”更稳，尤其适合个人项目和快速原型仓库。

## 暴露出的限制与失败模式

### 1. 多客户端本地日志的可恢复性非常不对称

Codex 的 session `jsonl` 足以还原 commentary、工具调用和最终答复；Cursor 和 Claude Code 当天则没有可恢复样本。做跨客户端复盘时，不能假装三者覆盖度相同。

### 2. 空数据库或空摘要表不能直接解释为“没发生会话”

Cursor 这次就是典型例子。`conversation_summaries` 为空，只能说明当前数据库里没有当天摘要，不能直接推出“用户当天没在 Cursor 用 AI”。

## 可复用做法

### 跨客户端 AI 使用复盘

> 先列出每个客户端的本地日志路径与可用字段，再按明确的本地时间窗筛会话。若没有可恢复内容，请写“无可恢复证据”，不要写成“无使用”。

### Git 发布任务

> 先确认 `git status`、`remote -v`、当前分支、最近提交和项目验证命令，再决定提交、推送还是先补检查。不要默认扩展到 PR 或额外发布动作。

### 发布前验证

> 在报告“已推送/可交付”前，运行项目内真实可用的测试或构建命令，并把通过的是哪几个命令说清楚。

## 后续动作

- 以后做“全设备 AI 使用复盘”时，默认把“证据来源”和“缺失来源”并列写清楚。
- 以后遇到 git 发布请求，优先复用这套最小事实检查集和发布前验证顺序。
