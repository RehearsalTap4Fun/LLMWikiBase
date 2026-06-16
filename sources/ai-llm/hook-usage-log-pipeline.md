> **个人经验** | 标题:AI 使用日志自动化管线
> 创建日期:2026-06-16
> 说明:用 Claude Code 的 Stop hook 把"对话变大"事件自动记进知识库,供周期总结成个人 AI 使用经验。本文是该工作流的设计与维护笔记。

---

# AI 使用日志自动化管线

## 目标

把个人 AI/LLM 使用过程沉淀成知识库里的经验:**每当一次对话的上下文增长到一定规模,就自动记录一笔(时间、上下文 token 数、本轮主题),并唤醒模型做一次总结 + 工作流优化建议。** 这些记录积累起来,知识库周期总结时就能扫到,提炼出"我这段时间怎么用 AI、哪类对话容易膨胀、暴露了哪些工作流摩擦"。

为什么用"上下文超阈值"而不是"每轮对话"做触发:小对话(随手一问)不该被打断、也没有总结价值;只有对话长到一定程度,回顾和经验沉淀才有意义。

## 组成

| 文件 | 作用 |
|------|------|
| `~/.claude/hooks/summarize-gate.py` | Stop hook 脚本,每轮对话结束时触发,内含门禁逻辑 |
| `~/.claude/settings.json` 的 `hooks.Stop` | 注册该脚本:`python ~/.claude/hooks/summarize-gate.py` |
| `~/.claude/hooks/fire.log` | 纯数据日志(时间⇥token⇥session),用于调阈值 |
| `~/.claude/hooks/state/<session>.last` | 每会话状态文件,记录上次触发时的 token 数,用于防循环 |
| `C:\Project\KnowledgeBase\sources\ai-llm\hook-fires-YYYY-MM.md` | **本知识库内**的按月日志,Markdown 表格,纳入 git,作为经验素材 |

## 门禁逻辑(怎么决定触发)

1. 从 transcript 最后一个 `usage` 块读真实上下文 token 数 = `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`。
2. 低于 `THRESHOLD_TOKENS`(默认 60k)→ 静默退出,零模型成本。
3. 较上次触发增长不足 `GROWTH_TOKENS`(默认 40k)→ 静默退出。这条 + 状态文件共同防止"总结那一轮又触发总结"的死循环(总结轮新增 token 很少,够不到增量门槛)。
4. 全部通过 → 写日志、输出 `{"decision":"block","reason":...}` 唤醒主模型做总结 + 优化建议 + 反问。

## "本轮主题"怎么提取

取 transcript 里**首条真实人类 prompt**:`type:"user"` 且 `message.content` 是字符串(content 为 list 的是 tool_result,跳过);并跳过以 `Stop hook feedback` 开头的 hook 回灌。单行化后截 80 字。

注意:Claude Code 自动生成的 `slug` 字段(如 `serialized-hopping-flurry`)是随机英文词、**不是内容摘要**,不能拿来当主题。

## 维护要点

- **调触发频率**:改 `summarize-gate.py` 顶部 `THRESHOLD_TOKENS` / `GROWTH_TOKENS` 两个常量。觉得提示太晚就调低 THRESHOLD,太频繁就调高 GROWTH。
- **transcript 路径**:`~/.claude/projects/<项目路径哈希>/<session>.jsonl`。
- **中文输出必须 ASCII 转义**:脚本输出含中文的 JSON 必须用 `json.dumps(obj)`(默认 `ensure_ascii=True`),不能用 `ensure_ascii=False`,否则 Windows 下 GBK/UTF-8 错位导致乱码。详见 [[windows-python-hook-stdout-ascii]]。
- **hook 中途加入**需 `/hooks` 重载或重启才生效。
- 日志路径选在 `sources/ai-llm`(知识库内、git 跟踪),而非 `~/.claude`,就是为了让它进入知识库总结范围。
