---
title: AI 使用日志自动化管线（素材摘要）
type: source-summary
domain: ai-llm
source: sources/ai-llm/hook-usage-log-pipeline.md
date: 2026-06-16
confidence: high
tags: [claude-code, hook, 工作流, 自动化, 个人经验, 知识库]
links: ["[[windows-python-hook-stdout-ascii]]", "[[llm-wiki-pattern]]", "[[ai-claude-workflow-lessons]]"]
---

# AI 使用日志自动化管线（素材摘要）

个人经验笔记:用 Claude Code 的 **Stop hook** 在「对话上下文增长到一定规模」时自动记一笔(时间、上下文 token 数、本轮主题),并唤醒主模型做一次总结 + 工作流优化建议。日志积累后,知识库周期总结能扫到,提炼出「我这段时间怎么用 AI、哪类对话容易膨胀、暴露了哪些工作流摩擦」。这是 [[llm-wiki-pattern]] 里「LLM 当簿记员」思路在**个人元数据**上的一次应用——把使用过程本身也沉淀为素材。

## 为什么以「上下文超阈值」而非「每轮」触发

小对话(随手一问)不该被打断、也没有总结价值;只有对话长到一定程度,回顾与经验沉淀才有意义。

## 组成

| 文件 | 作用 |
|------|------|
| `~/.claude/hooks/summarize-gate.py` | Stop hook 脚本,每轮对话结束触发,内含门禁逻辑 |
| `~/.claude/settings.json` 的 `hooks.Stop` | 注册脚本:`python ~/.claude/hooks/summarize-gate.py` |
| `~/.claude/hooks/fire.log` | 纯数据日志(时间⇥token⇥session),用于调阈值 |
| `~/.claude/hooks/state/<session>.last` | 每会话状态文件,记上次触发时的 token 数,防循环 |
| `sources/ai-llm/hook-fires-YYYY-MM.md` | **本库内**按月日志(Markdown 表格、纳入 git),作经验素材 |

## 门禁逻辑(怎么决定触发)

1. 从 transcript 最后一个 `usage` 块读真实上下文 token = `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`。
2. 低于 `THRESHOLD_TOKENS`(默认 60k)→ 静默退出,零模型成本。
3. 较上次触发增长不足 `GROWTH_TOKENS`(默认 40k)→ 静默退出。这条 + 状态文件共同防「总结那一轮又触发总结」的死循环(总结轮新增 token 很少,够不到增量门槛)。
4. 全部通过 → 写日志、输出 `{"decision":"block","reason":...}` 唤醒主模型做总结 + 优化建议 + 反问。

## 「本轮主题」怎么提取

取 transcript 里**首条真实人类 prompt**:`type:"user"` 且 `message.content` 是字符串(content 为 list 的是 tool_result,跳过);并跳过以 `Stop hook feedback` 开头的 hook 回灌。单行化后截 80 字。

注意:Claude Code 自动生成的 `slug` 字段(如 `serialized-hopping-flurry`)是随机英文词、**不是内容摘要**,不能当主题。

## 维护要点

- **调触发频率**:改 `summarize-gate.py` 顶部 `THRESHOLD_TOKENS` / `GROWTH_TOKENS`。提示太晚就调低 THRESHOLD,太频繁就调高 GROWTH。
- **transcript 路径**:`~/.claude/projects/<项目路径哈希>/<session>.jsonl`。
- **中文输出必须 ASCII 转义**:脚本输出含中文的 JSON 必须用 `json.dumps(obj)`(默认 `ensure_ascii=True`),否则 Windows 下乱码。详见 [[windows-python-hook-stdout-ascii]]。
- **hook 中途加入**需 `/hooks` 重载或重启才生效。
- 日志路径选在 `sources/ai-llm`(知识库内、git 跟踪)而非 `~/.claude`,就是为了让它进入知识库总结范围。
