# 构建私有 Karpathy 式 LLM Wiki（gbrain + gstack + Rails AI 工作流）

> **来源**：https://blog.saeloun.com/2026/04/28/private-karpathy-llm-wiki-gbrain-gstack-rails-ai-workflow/
> **作者**：Vipul A M（Saeloun）
> **获取日期**：2026-06-12
> **说明**：本文为 AI 转写的结构化摘要，非逐字原文。以原链接为准。

## 核心思路

从私有工作信号中提炼可复现的模式，让 AI 助手理解作者如何 review Rails、如何判断风险、如何 ship 代码——给助手"更好的默认值"，而非空白提示。原始语料留在本地；只公开架构，不公开私有数据、仓库名、客户名、凭据、客户细节。

## 三部分架构

- **Karpathy 式 LLM Wiki** —— 持久知识层，原始素材进去，LLM 维护结构化、互链的 markdown 页面，未来 agent 读它而非重新发现上下文。
- **gbrain** —— 私有记忆层，存放训练/提炼的工作信号 + persona 特质，由本地 SQLite（`brain.db`）支撑。
- **gstack** —— 把记忆应用到日常编码工作流：review、ship、debug、写作。

## 隐私优先流水线

私有信号 → 脱敏与来源标注 → gbrain 知识与 persona 特质 → LLM Wiki 页面 → gstack 工作流 → 更好的 review/写作/Rails 决策。目标是"更好的默认值"，不是巨型提示。

## 元数据 schema（关键借鉴）

每条信号带结构化元数据，使记忆有据可循。作者名言：没有 source、time、confidence，"记忆就只是感觉（vibes）"。字段包括：
- `source`（类型，如 `github_review`）
- `project` slug
- `visibility`（可见性）
- `recorded_at`（时间戳）
- `subject` 与 `summary`
- `evidence`（PR/评论的哈希 ID）
- `privacy`（原文本地、公开摘要脱敏）
- 存储的 confidence

特质只在重复证据后才提炼，"一条孤立评论永远不会变成规则"。

## 脱敏步骤

公开前先打码。不公开公司名、仓库名、reviewer 名、原始评论、内部路径、主机名、凭据、客户名、生产架构细节。

一个 Ruby 脚本（`redact_ai_source.rb`）用正则掩码 GitHub token、API key、本地路径、邮箱、IP。它刻意过度匹配，因为"误报比泄露一个真实内网 IP 更安全"。这是第一道防线，不是唯一一道——人工审核仍然重要。

## --review 人工闸门（关键借鉴）

对私有知识系统，作者偏好 `--review`：LLM 可以**提议** wiki 页面，但由人批准哪些落地。这让 wiki 保持有用，"而不让模型偷偷改写记忆"。完整编译在本地用 Ollama 以 review 模式运行，页面经批准而非自动写入。

执行循环：脱敏源 → 用 gbrain 提炼 → 编译候选页 → 人工批准 → 发布或用于 gstack。原则："无产物，不下论断（no artifact, no claim）。"

## 工具

- **gbrain CLI**（经 bun 运行）：`stats`、`query --synth true`、`persona voice`。私有工作流默认本地 LLM 支撑。
- **llm-wiki-compiler**（`llmwiki` CLI）：`schema init`、`ingest`、`lint`、`compile --review`、`review list`，以及 `serve` MCP server。
- **Ollama**：本地推理，OpenAI 兼容端点，模型如 `qwen2.5-coder:32b`、`nomic-embed-text`。

## gstack / Rails 工作流

gstack 把记忆变成可执行检查而非偶尔翻开的文档。Rails PR 上运行 `gstack review`、`gstack cso --diff`、`gstack ship`：
- `/review` —— 范围匹配、租户/账户边界、迁移安全、聚焦测试、避免多余依赖
- `/cso --diff` —— 密钥泄露、不安全的认证/授权、有风险的 CI/CD 或部署改动
- `/ship` —— 合并前构建与测试、更新博客日期/文件名、绝不声称未运行的验证

### 强制合并闸门

- GitHub 检查必须通过
- 读并修复 CodeRabbit 的可执行评论
- 把 Copilot review 当作另一位 reviewer，而非噪音
- 本地验证必须与 PR 声明一致
- 用户可见改动须检查部署/预览链接

## 作者拒绝的反模式（铁律借鉴）

- 没有产物（CI 链接、测试输出、lint 结果、命令输出）就不声称"已验证"
- 公开页面不含私有标识符
- 不把风格偏好伪装成正确性
- 不让过期 wiki 冒充当前——必须有 source、timestamp、review 状态

结语：记忆应改善默认值，但不取代判断。
