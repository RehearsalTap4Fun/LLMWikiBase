---
title: Claude Code 工作流经验沉淀(2026-06)
type: synthesis
domain: ai-llm
source: sources/ai-llm/hook-fires-2026-06.md
date: 2026-06-30
confidence: medium
tags: [claude-code, 工作流, hook, 个人经验, brainstorming, plan, subagent, 自动化, ingest, lint, 协议, 配置工程, 设计意图, xlsx, xmind, 编码, 反向同步, 真相源, 报告成功前自检, 外部installer, 最小覆盖]
links: ["[[hook-usage-log-pipeline]]", "[[windows-python-hook-stdout-ascii]]", "[[llm-wiki-pattern]]"]
---

# Claude Code 工作流经验沉淀(2026-06)

> 综合自 [[hook-usage-log-pipeline]] 在 2026-06 月的 15 段自动总结(世界杯主题活动配置工具、坐标协议、配置审核、中文策划素材解析与 xlsx 同步会话)。这是「LLM 当簿记员」思路在**个人元工作流**上的落地——hook 自动产出流水日志,人(+ LLM)做阶段性提炼。confidence 标 medium 是因为主要来自同一项目簇,还未跨多个项目复现。

## 三条最稳的原则

把 6 条原始建议归并、按跨项目复用价值排序,留下 3 条:

### 1. brainstorming 累计 ≥6 轮强制汇总

**痛点**:连问 9 轮才进入方案对比,中段(tag 表位置 / 必须 vs 可选 / 路径)信息量小,token 与等待都被拖长。

**做法**:在项目 CLAUDE.md / `superpowers:brainstorming` 调用约定里加一条「累计提问 ≥6 轮停下来汇总剩余疑点一次性问完」,允许打包多选。

**为什么**:小粒度问询的边际信息量随轮数衰减,在 brainstorming 阶段一次问 3-4 个比拆 6-8 轮单选更高效,也降低用户的回复成本。

### 2. 长产物(>300 行 plan/spec)一次性 Write,不分段 Bash 追加

**痛点**:1887 行 plan 走 8 次 `Write + cat + rm`,heredoc 含单引号会爆,临时 fragment 文件污染目录;省的单次 token 被错误重试反吃回去。

**做法**:在项目 CLAUDE.md 约束「>300 行 plan/spec 一次性 Write」;若必须增量,在 `scripts/` 加 `append_to.py`(stdin → 原子追加),不再用 heredoc。

**为什么**:Bash heredoc 对引号/反斜杠/`$` 的转义不稳定,越长越容易出错;一次性 Write 在编辑器里整体校对也更直观。乘以错误重试,小批量追加并不省。

### 3. subagent reviewer 必须先读 spec/plan 再评判

**痛点**:Task 3 reviewer 没看 plan §4.4 就要求加 n<2 防御,controller 反复挡下才避免无谓改动 —— 因为 reviewer 用小模型(haiku)时凭通用规范推断,本项目设计常违反通用直觉。

**做法**:reviewer dispatch prompt 模板加强制项 ——「评判前必须 grep spec/plan 文件,引用章节;凡引用不到原文支撑的建议降级为 Nit 或不报」。已在项目 `references/reviewer-spec-grounding.md` 落地(见 06-18 13:08 hook 总结)。

**为什么**:reviewer 不读 spec 就误判,会逼 controller 写 fix commit 解释设计意图,反而增加噪音 commit。强制 ground 在 spec 上,把错的建议挡在生成前。

## 已落地的较小项(不复述)

下面两条跨项目复用价值中等,但已在 06-18 commit `d308f33` 落地,作为本项目稳态工具:

- **`templates/config-tool-spec.md`** —「配置生成器/工具类」需求的固定问询模板(输入形态 → 词表 → 落点 → 冲突 → 输出),首次澄清直接据此跳过通用项。
- **`scripts/check_plan_signatures.py`** — plan §11 自检脚本稳定版,接受 `--plan <path>`,做语法检查 + 关键符号交叉引用扫描,作为 plan 落盘后的 `make check` 步骤。

## 新增的工程化护栏

06-18 13:10 至 06-22 11:20 的 4 段总结没有推翻上面的三条原则,但把问题从"个人协作习惯"推进到"长文档/长配置工程的防漂移机制"。

### 4. rolling source 先判类型,再选 ingest 路径

**痛点**:hook-fires、月报、巡检日志这类持续增量素材不是一次性参考资料。若每次都当新 source-summary 建页,会把流水账堆进 wiki;若完全不沉淀,又会丢掉跨轮复现的经验。

**做法**:对 rolling source 默认给三档路径:A 建轻量 synthesis 页 / B 补母页章节 / C 只记 log。素材自身最好带 `kind: rolling-log` 之类标记,让 ingest 阶段先看类型再决定默认策略。

**为什么**:持续素材的价值在"多次触发后的稳定模式",不在单条记录。先判类型可以减少误建页面,也让"暂不写 wiki"成为明确选择。

### 5. 协议/配置双源必须靠 lint 防漂移

**痛点**:坐标协议确认后,主生成器里仍可能残留旧常量、旧单位或旧 preset。手写 WARN 注释只能提醒,不能阻止后续继续漂移。

**做法**:把"读现有代码反推现状"固化成 lint,例如 `check_protocol_drift.py` 对比协议常量与代码常量,`check_preset_consistency.py` 校验 18 个 preset 的方向、单位和关键区间。

**为什么**:配置工程里最危险的是文档已确认、代码未迁移但表面仍能跑通。lint 把软约束变成硬失败,比靠人工巡检便宜。

### 6. references 类文档需要 TBD 状态机

**痛点**:协议草稿很容易累计大量 TBD 与派生改动清单。若没有状态机,文档会停在"已记录问题"而不是驱动代码同步。

**做法**:用 `scripts/list_tbd.py` 统计 references 的 TBD 数;在协议派生改动清单里约定状态推进,例如 v1 → v1.1(P0 全完成)→ v2(P1 完成),并把重跑测试/刷新 TBD 作为升级条件。

**为什么**:TBD 和 P0/P1 不是备注,而是工程状态。状态机能把"问题列表"转成"可关闭的任务队列"。

### 7. 分批写长 plan 时禁止同消息 Write+Bash

**痛点**:分批落 plan 时,如果同一轮里先 Write 临时片段、再 Bash `cat` 追加,工具调度一旦不是严格顺序,就可能 append 空内容或漏掉中段 task。

**做法**:若必须分批,每批先等 Write 返回,再单独执行 Bash 追加;更理想是用一次性 Write 或原子 append helper。

**为什么**:长 plan 中任一批丢失都会让后续 subagent 执行缺关键代码块。多一轮等待比排查残缺 plan 便宜得多。

## 2026-06-23 之后的补充

后续几段日志继续围绕世界杯主题活动配置工程,把"lint 防漂移"进一步推进到"审核标准、语义迁移、派生产物保护"。

### 8. 新 lint 要做反向注入测试

**痛点**:第一版 keeper z lint 跑通后报告 50 个 preset 全部合规,但把一处 helper 临时改回旧值做反向测试才发现正则抓错参数,相当于给了虚假安全感。

**做法**:新增 lint 规则时配一个反向 fixture 或临时 patch 验证:故意制造一处违规,确认 lint exit code 非 0,再还原。规则本身跑绿不够,必须证明它能抓到目标坏例子。

**为什么**:lint 的危险不只是漏报,而是让人误以为已经有机器护栏。反向注入测试是最便宜的"护栏本身也受检"。

### 9. 配置审核分三层:硬范围 / 软分布 / 设计意图

**痛点**:坐标范围 lint 全过,并不代表玩法语义保住。z 半场缩短后,如果只看 `[-60, 0]` 合法区间,会漏掉"主要发生在敌方半场"、门将-球距离、球员朝向等软约束。

**做法**:配置/坐标审核类任务先列三档断言:硬范围(是否越界)、软分布(是否落在合理区间/比例)、设计意图(这条数据代表什么场景)。只有三档都通过,才报告合规。

**为什么**:硬范围是最便宜也最弱的一层。全局参数变动时,设计意图往往藏在数据分布里,不能用"lint 过了"替代语义审核。

### 10. 全局参数变更默认按语义迁移处理

**痛点**:协议把场地 z 半场从 120 缩到 60 后,只同步常量会让旧 preset 仍然"数值合法",但门-球真实距离、远射阈值、球员站位语义已经漂移。

**做法**:场地深度、单位、坐标原点这类根值变化时,默认列出所有派生数据(preset / instance / xlsx),给出"等比缩放 / 重设计 / 不动"三档建议和距离对照,再落数据。

**为什么**:全局参数不是局部常量。若不显式呈现影响面,LLM 很容易走最近路:改字面量、跑全绿、收工,把语义债留给后续。

### 11. 生成器写派生产物前先保护人工编辑

**痛点**:`ActivitySoccer_preview.xlsx` 被策划手工调整后,直接跑主生成器会覆盖人工稿,再从 git 里捞回原稿和 diff,时间全花在补救。

**做法**:生成器写出 xlsx 前先检查目标文件是否相对 HEAD 或 source-data 变脏;若变脏且没有 `--force`,先备份或中止。配套补齐 `extract_*.py`,把策划在 xlsx 中编排好的真值抽回 JSON,再用 CI 做 drift 检查。

**为什么**:配置表 round-trip 的危险点在"脚本认为自己是真相源,但用户刚在表里改了真值"。写前脏检测能防止无声覆盖,extractor 让人工编辑也进入可审计链路。

### 12. 中文策划素材解析要工具化

**痛点**:总结联动活动方案时,Windows 下 Python 读中文 xlsx 的 sheet name 首次输出乱码;xmind 也需要 unzip `content.json` 再手写递归 walker。

**做法**:Windows 跑 Python 处理中文文件时默认设 UTF-8 stdout;把 xmind 解析固化成 `xmind_to_outline.py <xmind>` 这类 helper,输出缩进 outline 供后续总结。

**为什么**:中文 xlsx / xmind 是策划常见交付形态。把编码和解析步骤做成工具,能减少重复试错,也和 [[windows-python-hook-stdout-ascii]] 的编码经验形成反链。

## 关键提醒

这些原则不是普适教条:

- 「≥6 轮汇总」是**针对 brainstorming 阶段**,debugging / TDD 这类需要细粒度反馈的场景仍按 skill 自身节奏。
- 「>300 行一次性 Write」是**针对一次成型的 plan/spec**,实施期 commit 历史里的渐进编辑该多次就多次。
- 「reviewer 必须读 spec」假设有 spec/plan 可读;无 spec 的临时改动,reviewer 只能凭通用规范评判,这是另一类问题。
- 「协议 lint / TBD 状态机 / 三层审核 / 派生产物保护」适合长期维护的配置工程;一次性小脚本不一定值得建设完整治理层。
- 「全局参数变更默认语义迁移」不等于每次都要重做全部数据,而是要求先把影响面摆出来,再决定缩放、重设计或保留。

## 与本知识库其他页的关系

- 元方法论源头 → [[hook-usage-log-pipeline]](让对话过程本身沉淀为素材的管线)、[[llm-wiki-pattern]](LLM 当簿记员)。
- 同域技术 recipe → [[windows-python-hook-stdout-ascii]](hook 输出中文转义;中文 xlsx/xmind 解析也复用同一类 Windows 编码经验)。
- 后续若新月份日志暴露新摩擦或推翻上述某条,直接更新本页并刷新 date;只有出现独立主题簇时再另开 synthesis 页。

## 2026-06-27 之后的补充

06-29 一天连爆 5 段总结(Agent Reach 安装 + slice-editor 反导 4 段),暴露 4 条新原则,继续挂在本页而非另开:

### 13. 外部 installer 执行前先跑 dry-run/safe

**痛点**:安装 Agent Reach 时直接 `agent-reach install --env=auto` 一气呵成,没先用文档自己写出来的 `--safe`(仅检查)或 `--dry-run`(预览)。结果 Exa MCP 注册被 auto-mode 拦截才发现——那步是"修改 agent 自己的 MCP 配置"敏感操作,提前 dry-run 就能在执行前跟用户对齐授权。

**做法**:项目/全局 CLAUDE.md 加一条「执行外部 install.md / setup script 前,如其本身提供 `--dry-run` / `--safe` / `--check` 模式,默认先跑一遍列动作清单,再决定是否原命令执行;尤其当该 installer 会注册 MCP / 写 `~/.claude/skills` / 改 PATH 时」。

**为什么**:外部 installer 的"自动模式"含义不透明。本轮 agent-reach 一次写了三处 skills 目录(`~/.agents/skills`、`~/.openclaw/skills`、`~/.claude/skills`),若其中一处写错或污染,撤销代价远大于多花 1 分钟 dry-run。

### 14. 报告"跑成功"前必做三件套

**痛点**:主生成器跑完看到 stdout 有 `Wrote ...ActivitySoccer_preview.xlsx` 就报"重生成成功",实际后续 `apply_slice_preset_editor_patch` 抛了 `ValueError`,xlsx 根本没被改写。用户提"没按 patch 重写"才查出。**这是本月第二次翻车**(上次是 06-23 lint 全绿但实际没抓 keeper z,即 §8 反向注入测试的场景)。

**做法**:在项目/全局 CLAUDE.md 加一条「跑生成器/构建/迁移脚本后,报告成功之前必做三件套」:
- (a) `echo $?` 或检查 exit code;
- (b) `git status --short` 看目标产物 mtime/diff 实际有无变化;
- (c) 抽样读 1 行产物校验关键字段。

**为什么**:配置生成器是「写盘 → 校验 → 报告」三段式,任一段抛异常都会半途崩,但 stdout 已经打了 `Wrote`。LLM 凭乐观 stdout 误报,用户看产物不变又得追问,反复一次比加 3 行护栏贵得多。这条与 §8「新 lint 要做反向注入测试」是同一族——都是"绿灯 ≠ 已通过",必须再证一次。

### 15. 反向同步函数默认最小覆盖,别堆防御性

**痛点**:`apply_slice_preset_editor_patch` 我写了三轮才对——v1 未知 ID 直接 raise(炸生成器)→ v2 加 xlsx 兜底插行 + 补 angle cols + 二次覆盖盖 normalize(80 行)→ v3 用户点破"为啥这么多检测"才精简到 40 行。根源是把"防御性编程"当默认,但反向同步的语义本来就是"用户说了算"——网页编辑器只能改 5 字段、保存前已做吸附,脚本要做的就是按 ID 找行、覆盖 5 字段、结束,任何 normalize/校验都在"对抗用户输入"。

**做法**:在 `templates/config-tool-spec.md` 加一节「反向同步函数设计原则」:
- (a) 输入源是真相,不二次校验/修复;
- (b) 字段集合就是 patch 里有的那几个,不扩;
- (c) 未知 ID 默认"静默忽略 + 计数告知",不 raise;
- (d) 想做硬约束就在用户输入端(网页/前端)做,主生成器是消费者不是质检员。

配套规则:**用户连续 2 次说「为什么需要 X / 为什么这么多 X」= 明确的回退到设计起点重审信号**。下一轮首个动作必须是"重读问题描述 + 列最小可用动作清单",而不是"在现有代码上再剪一刀"。加法防御性代码会自我增殖,减法重写一次可以彻底清账。

**为什么**:配置工程里"程序生成 vs 用户手改"的边界模糊时,LLM 的默认偏见是"多校验保安全",但反向同步这类语义,校验就是对抗用户。本轮前两版多写的代码在用户读完函数就会反问"我编辑只动 5 字段,为啥还要 normalize/raise"——这是设计直觉与领域语义错位。

### 16. 配置工具类需求必问 N+1:真相源是哪个文件?

**痛点**:整个 slice-editor 反导事件用了 5 个 patch 版本才走到正确架构(raise → 兜底 + normalize → 简化 40 行 → 独立脚本 → xlsx overlay),最终结论是「xlsx 才是真相源,Python `specs` 只是首次 bootstrap 种子」。实际只要在最初就问「策划工作流里,xlsx vs Python specs 谁是真相源?」,一个 AskUserQuestion 就能避开所有中间版本。

**做法**:在 `templates/config-tool-spec.md` 的固定问询链路里加必填澄清项 —— **「真相源是哪个文件?其他文件是它的派生/补充?」**。与前置的「输入形态 / 词表 / 落点 / 冲突 / 输出」并列。

延伸模式(可在 `templates/` 加 `data-driven-config-generator.md`):
- (a) 真相源是 xlsx(或类似持久化层);
- (b) 主生成器读 xlsx → overlay specs → 写回 xlsx,保证幂等;
- (c) 反向同步脚本(网页 patch、批改工具)只动几个字段,与主生成器解耦;
- (d) 测试断言基于 xlsx 现状而非 specs 期望。

**为什么**:配置工程的核心矛盾是「程序生成 vs 用户手改」,真相源走向决定整个数据流(覆盖方向 / 兜底逻辑 / 测试断言)。LLM 自己猜大概率猜反——因为代码主流是「程序生成」,但用户实际工作流是「策划在 xlsx 手改是日常,跑生成器是兜底」,方向正好相反。一句话澄清省 5 轮代码重写。

### 与 §4「rolling source」的关系

这 4 条都发生在同一天、同一个项目(MindToDoc 世界杯活动),说明 §4 提到的「rolling source 判类型」思路对 hook-fires 这类流水日志仍适用——本轮把新增部分作为章节挂到已有 synthesis 页(路径 B),而不是每天新建页面。
