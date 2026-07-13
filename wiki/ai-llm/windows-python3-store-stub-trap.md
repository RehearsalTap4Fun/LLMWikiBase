---
title: Windows 环境 python3 命令指向 Store 空壳，需用完整路径调用真实 Python
type: concept
domain: ai-llm
source: 对话
date: 2026-07-08
confidence: high
tags: [windows, python, 环境陷阱, pip, 个人经验]
links: ["[[windows-python-hook-stdout-ascii]]", "[[ai-claude-workflow-lessons]]"]
---

# Windows 环境 python3 命令指向 Store 空壳，需用完整路径调用真实 Python

个人经验笔记：这台 Windows 机器上 `python3` 命令和 `pip`/`pip3` 实际指向两个不同的 Python 安装，导致"pip 装完包却在 python3 里 import 不到"的假象。已独立触发两次（一次是给 `claude-video`/`watch` skill 装依赖时，一次是给知识库处理 PDF 装 PyMuPDF 时）。

## 现象

```bash
pip install pymupdf --quiet   # 显示成功，无报错
python3 -c "import fitz"      # ModuleNotFoundError: No module named 'fitz'
```

看起来像是 pip 装到了别处，但报错信息本身不会直接告诉你原因。

## 原因

```bash
which python3
# /c/Users/jiangzhenyu/AppData/Local/Microsoft/WindowsApps/python3
```

`python3` 命令解析到的是 **Microsoft Store 版 Python 的空壳可执行文件**（Windows 10/11 默认会在 PATH 里放一个占位 `python3.exe`，用于引导用户去 Store 安装，本身不是真实运行时）。而 `pip` 命令却解析到了系统里真正装的 Python（此机器是 `C:\Users\jiangzhenyu\AppData\Local\Programs\Python\Python310`），两者不是同一个环境，装的包自然互相看不到。

## 排查方法

```bash
pip show <package>   # 能看到已安装 → 说明 pip 本身没问题
where python3         # 或 which python3，看实际解析路径
```

若 `pip show` 显示已安装、但 `python3 -m pip show` 或 `python3 -c "import X"` 报错，基本可判定是这个陷阱，不必再怀疑 pip 安装本身出了问题。

## 解法

直接用完整路径调用真实 Python，跳过 PATH 解析：

```bash
PYTHON="C:/Users/jiangzhenyu/AppData/Local/Programs/Python/Python310/python.exe"
"$PYTHON" -c "import fitz; print(fitz.version)"
```

## 适用范围

这台机器上任何需要调用 Python 的场景（脚本执行、pip 装包后验证）都适用。遇到 `python3 -c "import X"` 报 `ModuleNotFoundError` 但 `pip show X` 又显示已安装时，第一时间换成完整路径重试，不必重新排查 PATH 或重装。

注意与 [[windows-python-hook-stdout-ascii]] 区分：那是**编码显示问题**（控制台按 GBK 显示中文导致误判乱码），本页是**PATH 解析问题**（命令指向了错误的可执行文件）。两者都是本机 Windows + Python 环境的常见陷阱，但根因和解法都不同，遇到问题时先判断是哪一类再对应排查。
