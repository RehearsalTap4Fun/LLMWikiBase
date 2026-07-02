> **个人经验** | 标题:2026-07-01 AI 使用复盘（Codex 审查子线程驱动实现收敛）
> 创建日期:2026-07-02
> 来源覆盖:Codex `~/.codex/session_index.jsonl` 与 `~/.codex/sessions/2026/07/01/*.jsonl`，重点包括 `整理游戏框架与配置物料` 主线程派生的 Task 1/Task 2 实施与审查子线程；Cursor `~/.cursor/ai-tracking/ai-code-tracking.db` 与 `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`；Claude Code `~/.claude/history.jsonl` 与 `~/.claude/projects/*.jsonl`
> 说明:只记录本机可验证的 2026-07-01（Asia/Shanghai）活跃会话。当天可恢复的高价值内容主要来自 Codex。Cursor 未发现 2026-07-01 的 Composer 会话记录；Claude Code 未发现 2026-07-01 的新历史或项目会话。

---

# 2026-07-01 AI 使用复盘（Codex 审查子线程驱动实现收敛）

## 覆盖到的有效会话

### Codex

- `Scaffold Vite React app`：Task 1 实施子线程。价值点不在“脚手架本身”，而在环境排障和验证路径修正。
- `Review Task 1 spec compliance` / `Review Task 1 scaffold` / `Re-review Task 1 after fix`：围绕同一任务拆成“规格符合性”和“代码质量”两类审查，再做定向复审。
- `Define domain types and MVP content`：Task 2 实施子线程。暴露了“计划文本互相冲突”时如何落回可验证不变量。
- `Review Task 2 compliance` / `Review Task 2 spec compliance` / `Review Task 2 changes` / `Re-review Task 2 code quality`：连续发现模板冲突、不可达路径、未跟踪素材依赖、测试缺口，最后靠一轮轮最小修复收敛。

### Cursor

- `ai-code-tracking.db` 的 `conversation_summaries` 未发现 2026-07-01 记录。
- `state.vscdb` 的 `composer.composerHeaders` 最新可恢复会话停在 2026-06-16。
- 可见 Cursor 当天没有可恢复的本地 AI 对话样本，至少当前数据库里拿不到。

### Claude Code

- `~/.claude/history.jsonl` 未发现 2026-07-01 prompt。
- `~/.claude/projects/*.jsonl` 也未发现 2026-07-01 项目会话。

## 高价值做法

### 1. 主线程做实现，子线程做窄目标审查，比“一个线程全包”更稳

这批会话最有价值的不是单次 prompt，而是分工方式：

- 一个实施线程只负责把当前任务做完并跑验证。
- 多个审查线程分别只看 `spec compliance`、`code quality`、`re-review after fix`。
- 每个审查线程都要求 `Do not edit files`，并限定检查范围与输出格式。

这样做的结果是，审查线程真的在挑错，而不是边审边修把问题掩掉。Task 2 最后能抓出“英雄槽位可达性”和“clean checkout 下素材缺失”这种问题，靠的就是这个拆法。

### 2. 审查 prompt 要把“检查维度”写成不同批次，不要一锅端

这次有效的审查 prompt 不是笼统地说“review this code”，而是拆成：

- 规格符合性：文件、导出、计数、不变量是否满足任务说明。
- 代码质量：可维护性、引用完整性、clean checkout 可用性、后续任务阻塞点。
- 定向复审：只验证上一次 findings 是否真的修掉。

这种写法能让同一个任务连续产生不同种类的发现，而不是每轮都重复讲同样的问题。

### 3. 一旦发现不变量，就立刻写进测试，不要只留在评审文字里

7 月 1 日几轮修复里，最持久的收益不是某个具体房间配置，而是把约束变成了测试：

- battle room 数量和 hero placement 数量一致。
- 每个模板房间 ID 都能解析到内容表。
- hero `subSkillIds` 都能解析到奖励表。
- 每个 hero placement 都能从 spawn 到达。
- 内容里的素材路径必须指向 `public/assets/wiki/...` 里的已跟踪子集。

这个模式很值得复用。评审文字只能发现一次，测试能防止同类问题再回来。

### 4. 当计划文本彼此冲突时，先显式挑出冲突，再选择“可验证的不变量”

Task 2 里出现了典型问题：

- 一处“精确模板块”要求 6 个 battle room。
- 另一处测试/设计约束要求 5 个 battle room 和 5 个 hero placement。

好的处理不是闷头“照抄更具体的那段”，而是先把冲突指出来，然后选择一个后续能稳定验证的约束作为准绳。这里最后选择的是“五战斗房间 + 五英雄位 + 所有引用有效 + 路径可达”。

对 AI 协作来说，这个经验很关键：当规范互相打架时，prompt 里要允许 Agent 报告冲突并解释取舍，否则它很容易表面完成、实际埋雷。

### 5. 环境问题不要立刻切换工具链，先确认“缺的是命令，还是缺的是运行时”

Task 1 的一个很实用教训是：

- `npm` 不在 PATH，不等于不能跑 npm。
- Codex 运行时里有 bundled `node` / `npm`，只是默认 shell 环境不对。
- 与其直接切到 `pnpm`，不如先补对 PATH，用目标项目原本要求的命令完成验证。

后面又遇到 macOS signed node 与 Rollup native binary 的问题，最后也是通过切换到运行时 Node 解决，而不是直接改项目依赖。这个排障顺序更稳：

1. 先确认命令是否真的不存在。
2. 再确认本地/runtime 里是否有可用二进制。
3. 最后才考虑换包管理器或改项目。

### 6. “本地参考素材存在”不等于“仓库可交付素材存在”

Task 2 中最容易漏掉的问题是：

- 根目录下有一个本地未跟踪的 `assets/wiki` 参考树。
- 代码引用 `/assets/wiki/...` 时，本机开发环境看起来没问题。
- 但 clean checkout 或部署后，真实需要的是 `public/assets/wiki/...` 里的已跟踪子集。

这类问题很适合专门写一条审查 prompt 去问：`Check for asset availability in clean checkout`。这是一个很实用的审查关键词，值得复用到所有带图片/静态资源的原型项目里。

## 暴露出的失败模式

### 1. 审查不分层时，容易漏掉“规格问题”和“交付问题”是两类不同错误

如果只让一个线程泛泛 review，通常只能抓到显眼 bug。像这次这样分开看，才能分别抓到：

- `strict` 配置缺失
- `.gitignore` 与依赖分类错误
- 模板与计数冲突
- 不可达 hero slot
- 未跟踪 public 资产缺口

### 2. 直接依赖本地文件系统校验，容易在构建时踩类型/运行时边界

这次一度用 Node `fs` 检查素材存在，Vitest 能跑，但构建配置缺 Node 类型。后来改成更贴近项目运行方式的 `import.meta.glob` / Vite 资产图，才和项目本身一致。教训是：

- 测试校验最好尽量贴近应用真实加载路径。
- 不要为了“验证方便”引入项目本身并不使用的运行时假设。

## 可复用的 prompt 写法

### 实施 + 审查并行收敛

> 主线程负责实现和提交。另开只读审查线程分别做 spec compliance、code quality、re-review。审查线程不得改文件，必须给出带文件/行号的 findings，并明确 residual risks。

### 规格冲突澄清

> 如果任务说明内部存在冲突，不要自行糊过去。先列出冲突项，再说明你将以哪个可验证不变量为准继续实现，并把该不变量编码进测试。

### clean checkout 资产检查

> 不要只检查本机文件是否存在。请验证代码引用的静态资源是否都来自仓库已跟踪、构建可访问的 public 子集，并给出任何 clean checkout 会丢失的路径。

### 环境命令排障

> 如果 `npm`/`node`/`pnpm` 运行失败，先区分是 PATH 问题、runtime 问题还是项目配置问题。不要直接切换包管理器；先定位本机或运行时内是否已有可用二进制。

## 后续动作

- 以后做多步开发任务时，默认把“实现”和“审查”拆成不同会话，不要指望一个线程同时高质量写代码又高质量挑错。
- 评审发现一旦上升为不变量，尽快补测试，而不是只修当前数据。
- 对含静态资源的前端原型，固定加一轮 `clean checkout` 视角检查。
- 当本地工具链异常时，优先修验证路径，再决定是否要改项目本身。
