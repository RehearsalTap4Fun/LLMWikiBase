---
title: 钉钉文档与本地 markdown 的转义差异
type: concept
domain: ai-llm
source: ~/.kiro/projects/C--Project-MindToDoc/memory/dingtalk-md-escape-diff.md
date: 2026-06-17
confidence: high
tags: [钉钉, markdown, 双向同步, 转义, GFM, MCP, 工具集成]
links: ["[[hook-usage-log-pipeline]]"]
---

# 钉钉文档与本地 markdown 的转义差异

个人经验笔记：通过 MCP 工具(`get_document_content` / `update_document` / `insert_document_block`)在钉钉在线文档(adoc)与本地 markdown 之间双向同步内容时，**两边的 markdown 转义风格不同**。直接把一边的内容复制到另一边会产生显著差异，必须做一次清洗。

## 钉钉 → 本地：钉钉返回的是 GFM 严格转义

`get_document_content` 返回的 markdown 走 GFM 严格转义路径，常见转义如下：

| 钉钉返回里的写法 | 实际语义 | 本地干净 markdown 应写为 |
|---|---|---|
| `\+` | 字面加号 | `+` |
| `\*\*x\*\*` | 加粗 | `**x**` |
| `\*` | 字面星号(罕见) | `*` |
| `\{` / `\}` | 字面花括号 | `{` / `}` |
| `\[` / `\]` | 字面方括号 | `[` / `]` |
| `\\` | 字面反斜杠 | `\` |
| `&#91;` / `&#93;` | 已 HTML 实体化的方括号 | `[` / `]` |
| `\\\\` | 表格单元里的字面 `\` 折行 | 通常保留为 `\\` 或换行 |

直接保存这些字符到本地 md 会让本地渲染器把反斜杠当字面输出，正文里出现一串 `\+` `\*\*`。

## 本地 → 钉钉：直接喂干净 markdown，不要"未雨绸缪"

本地干净 markdown 直接喂给钉钉一般可用，但要注意：

- `markdown` 参数里的换行**必须是真实换行符 `\n`(U+000A)**，不能是字面字符串 `\n`(反斜杠+字母 n);否则全部并到一行，标题/段落/表格全部错乱。
- 形如 `**\{x\}**` 这种"内容里要带字面花括号"的情况，本地写干净的 `**{x}**` 即可，钉钉会自动转义回 `\{x\}`。
- 反过来**不要**手工加 `\\+` `\\*\\*`，本地 markdown 渲染会把这些反斜杠当字面输出。

## 实操做法：钉钉拉回本地的反转义脚本

**顺序敏感**：先处理 2 字符序列，再处理单字符，最后处理 `\\\\`。

```python
unescaped = raw
unescaped = unescaped.replace('\\+', '+')
unescaped = unescaped.replace('\\*\\*', '**')
unescaped = unescaped.replace('\\*', '*')
unescaped = unescaped.replace('\\{', '{').replace('\\}', '}')
unescaped = unescaped.replace('\\[', '[').replace('\\]', ']')
unescaped = unescaped.replace('\\\\', '\\')              # 必须在最后
unescaped = unescaped.replace('&#91;', '[').replace('&#93;', ']')
```

`\\\\` 必须最后处理，否则会把前面替换掉的转义字符再次破坏。

## 校验：清洗完不应残留这些 token

正常本地 md 不应出现以下 token，扫描任一非零都说明清洗没做完：

```
\+    \**    \{    \}    \[    \]    &#91;    &#93;
```

## 适用场景

- 任何通过钉钉文档 MCP 双向同步内容的工作流(如把策划主案在本地编辑后同步到钉钉给研发评审)。
- 不限于钉钉文档 — 其他遵循 GFM 严格转义的平台(Notion 部分场景、GitLab 部分版本)也可能有类似问题，做双向同步时建议先做一次"小段落 round-trip"测试。

## 相关

- [[hook-usage-log-pipeline]] — 同样涉及"工具集成踩坑"的工程类经验
