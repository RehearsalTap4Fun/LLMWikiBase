---
title: Windows 下 Python hook 输出中文须用 ASCII 转义（素材摘要）
type: source-summary
domain: ai-llm
source: sources/ai-llm/windows-python-hook-stdout-ascii.md
date: 2026-07-08
confidence: high
tags: [claude-code, hook, windows, 编码, python, 个人经验]
links: ["[[hook-usage-log-pipeline]]", "[[ai-claude-workflow-lessons]]", "[[windows-python3-store-stub-trap]]"]
---

# Windows 下 Python hook 输出中文须用 ASCII 转义（素材摘要）

个人经验笔记:在 Windows + git-bash 写 Claude Code hook 时踩到的编码坑。**任何**通过 stdout 输出中文的 hook 都适用。相关实现见 [[hook-usage-log-pipeline]],后续在 [[ai-claude-workflow-lessons]] 中也扩展到中文 xlsx / xmind 解析流程。

## 现象

Stop hook(Python 脚本)经 stdout 返回含中文 JSON:

```python
print(json.dumps({"decision": "block", "reason": "在继续之前,请做一次回顾…"}, ensure_ascii=False))
```

在 Claude Code 里渲染成乱码(形如 `�Զ����� ��…`)。

## 原因

Windows 下 Python 的 stdout 默认编码是 **GBK / cp936**。`ensure_ascii=False` 会把中文按 GBK 编码写出字节流,而 **Claude Code 按 UTF-8 读取 stdout** → 字节错位 → 乱码。

## 解法

用 `json.dumps(obj)`(`ensure_ascii` 默认即 `True`),输出纯 ASCII 的 `\uXXXX` 转义:

```python
print(json.dumps({"decision": "block", "reason": "在继续之前,请做一次回顾…"}))
```

`\uXXXX` 是纯 ASCII,在任何编码下解码一致,从根本上规避问题。Claude Code 按 UTF-8 解析 `\uXXXX` 还原出正确中文。

## 验证时的陷阱

别只在 git-bash 里做 round-trip 测试(`脚本 | python -c "json.load"`)—— 两端同为 GBK 会**互相抵消、掩盖 bug**,看起来正常实则有问题。正确做法:

1. 确认脚本 stdout 是**纯 ASCII 字节**(无高位字节);
2. 再单独用 UTF-8 解码,看中文是否正确。

## 适用范围

不限 Stop hook —— **任何**会通过 stdout 输出中文的 hook(及类似的 Windows + Python 管道场景)都适用。

## 扩展：控制台 print 中文"看起来乱码"未必是数据错误

同一根因(GBK vs UTF-8 编码不一致)在更广泛的场景里也会出现,且容易被误判成"数据本身错了"。已反复出现在:Python `print()` 中文到 git-bash 终端、PowerShell `Write-Output` 中文、脚本调试时直接打印中文变量做验证。

**排查顺序**:看到终端输出中文变成 `�` 或类似乱码字符时,**先怀疑是控制台显示层编码问题**,不要直接断定数据本身错误或急着重新提取/重新解析。验证方法:把同样内容写入文件(显式指定 `encoding='utf-8'`),再用文件查看工具(如 Read 工具)读取比对 —— 若文件里的内容正确,就证明数据链路没问题,纯粹是终端渲染问题。

反例(踩坑写法):

```python
print(some_chinese_text)  # 终端显示乱码,若直接据此判断"提取失败/数据损坏"就会误判
```

正确验证写法：

```python
with open('debug_check.txt', 'w', encoding='utf-8') as f:
    f.write(some_chinese_text)
# 再用文件查看工具打开 debug_check.txt 确认
```

2026-07-08 同一次任务里，这个坑连续以三种不同形态出现（[[windows-python3-store-stub-trap]] 排查阶段的 debug print、PDF CMap 手动解析验证、身高体重表格数据整理），每次都需要重新反应过来"这是显示问题不是数据问题"——说明这条规律要主动联想到，不能只在遇到"pip 装包路径不对"这类具体场景时才想起。
