---
title: Saeloun 私有 LLM Wiki（素材摘要）
type: source-summary
domain: ai-llm
source: https://blog.saeloun.com/2026/04/28/private-karpathy-llm-wiki-gbrain-gstack-rails-ai-workflow/
date: 2026-06-12
confidence: medium
tags: [llm-wiki, 知识库, 隐私, 元数据, 人工审核, 工作流]
links: ["[[llm-wiki-pattern]]", "[[karpathy-llm-wiki]]", "[[gbrain]]"]
---

# Saeloun 私有 LLM Wiki（素材摘要）

Vipul A M(Saeloun)的实践文章,把 [[llm-wiki-pattern]]落地到**私有工作信号**上(gbrain + gstack + Rails AI 工作流)。本库的几条铁律直接借鉴自此文。

## 核心思路

从私有工作信号中提炼可复现的模式,给 AI 助手"更好的默认值"而非空白提示。原始语料留在本地;只公开架构,不公开私有数据、仓库名、客户名、凭据。

三部分:Karpathy 式 LLM Wiki(持久知识层) + [[gbrain]](私有记忆层,本地 SQLite) + gstack(把记忆应用到 review/ship/debug/写作)。

## 元数据 schema(关键借鉴)

作者名言:没有 source、time、confidence,"**记忆就只是感觉(vibes)**"。每条信号带 source / project / visibility / recorded_at / subject / summary / evidence / privacy / confidence。

特质只在重复证据后才提炼,"**一条孤立评论永远不会变成规则**"——对应本库铁律:单条信息支撑的结论标 `low`。

## --review 人工闸门(关键借鉴)

对私有知识系统,作者偏好 `--review`:LLM 可以**提议** wiki 页面,但由人批准哪些落地,以免"模型偷偷改写记忆"。执行循环:脱敏源 → gbrain 提炼 → 编译候选页 → 人工批准 → 发布。原则:"**无产物,不下论断(no artifact, no claim)**。"

→ 对应本库 Ingest 工作流的"提议清单 + 用户确认后才写入"。

## 脱敏

公开前用正则脚本掩码 token/key/路径/邮箱/IP,刻意过度匹配("误报比泄露一个真实内网 IP 更安全")——是第一道防线,人工审核仍重要。

## 拒绝的反模式(铁律借鉴)

- 没有产物(CI 链接、测试输出、命令输出)就不声称"已验证"。
- 公开页面不含私有标识符。
- 不把风格偏好伪装成正确性。
- 不让过期 wiki 冒充当前——必须有 source、timestamp、review 状态。

结语:"记忆应改善默认值,但不取代判断。"

## 在本库中的角色

提供**落地流水线**与**纪律约束**。本库 AGENTS.md 的"三条铁律"(无证据不标 high / 不偷偷改写记忆 / 回答带引用)和"提议-确认"Ingest 流程,主要源于本文。
