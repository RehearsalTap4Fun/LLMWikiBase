# 操作日志 (log)

> 追加式、按时间倒序。条目格式可 grep：`## [YYYY-MM-DD] 动作 — 摘要`

## [2026-07-02] ingest — 精简 K1 新服大地图策划案到 v0.6(移除工作量估计)
- 来源:用户要求策划案与速览页均不预估开发时间,留给开发人员拿到落地策划案后自行评估
- 更新 1 页:[[k1-new-server-map-plan]](版本 v0.5 → v0.6 精简稿)
  - 删除第十二章"开发工作量估计"整章(策划/后端/客户端/QA 分项预估、总周期)
  - 后续章节重编号:十三风险→十二、十四遗留清单→十三、十五下一步→十四
  - 风险章节内小节 13.1-13.9 相应改为 12.1-12.9
  - "下一步"第 3 条改为"交付给开发团队进行技术评估与排期",不再由本文档预估
- 更新 1 页:`wiki/gaming/k1-new-server-map-brief.html`
  - 版本号 v0.5 → v0.6(顶栏、audience 引用、footer 引用)
  - FAQ "什么时候能上线"改写:去除"3-4 周策划补齐、后端 1.5-2 个月、4-5 个月完整落地"等预估,改为流程节点描述
- 更新 wiki/index.md:策划案版本号 v0.5 → v0.6

## [2026-07-02] ingest — 更新 K1 新服大地图策划案到 v0.5 + 新增非开发职能速览网页
- 来源:
  - 用户修正:进程节奏对标 KVK 3 周但省 7 天匹配,压缩到 21 天完成
- 更新 1 页:[[k1-new-server-map-plan]](版本 v0.4 → v0.5 节奏对齐稿)
  - §6.2 迷雾开放时间从 D14/D28 改为 D8/D15,新增 D21 首次本服王座开放
  - §13.2 风险描述从 D14/D28 改为 D8/D15/D21
  - §14 遗留清单新增"首次本服王座开放时间(D21 是否维持)"
- 新增 1 页:`wiki/gaming/k1-new-server-map-brief.html`
  - 自包含 HTML 速览页(28KB,内嵌 SVG 示意图,无外部依赖)
  - 板块:一句话说明 / 四大亮点 / 新旧对比 / 地图 SVG / 玩家旅程时间线 / 5 个核心机制 / 6 职能影响 / 10 个 FAQ
  - 目标读者:产品/策划/市场/客服/运营/QA 等非落地开发职能
  - 21 天节奏在亮点、时间线、FAQ 三处对齐 D8/D15/D21
- 更新 wiki/index.md:策划案版本号 v0.4 → v0.5;新增 brief.html 入口

## [2026-07-02] ingest — 更新 K1 新服大地图重构策划案到 v0.4
- 来源:
  - v0.3 二审后对话:5 条规则澄清
- 更新 1 页:[[k1-new-server-map-plan]](版本 v0.3 → v0.4 规则澄清稿)
  - §2.4/§4.5 将"冷启动"改为玩家不可见的系统首战判定:零堡垒联盟只能攻打初始共享堡垒相邻的非免战普通堡垒
  - §4.5 明确免战优先级高于首战攻击资格
  - §5.1 补齐龙巢失效闭环:失效后保留原归属但暂停加成;任一联盟占有相邻堡垒即可发起争夺;原归属联盟重新获得相邻堡垒且未被打下时恢复生效
  - §9.2 明确联盟迁城不是首战前置,不再把迁城链路作为风险
  - §7.4 收敛恶魔守卫描述为普通野生 PVE,不再强调与堡垒占领无关
  - §13/§14 同步风险与遗留决策项为"首战"口径
- 更新 wiki/index.md:k1-new-server-map-plan 摘要版本号 v0.3 → v0.4

## [2026-07-02] ingest — 更新 K1 新服大地图重构策划案到 v0.3
- 来源:
  - v0.2 审核后对话:5 条细化决策
  - 恶魔守卫定位澄清:与龙巢守卫是两个不同设定
- 更新 1 页:[[k1-new-server-map-plan]](版本 v0.2 → v0.3 规则细化稿)
  - §2.4 冷启动圈明确"公共属性长期有效,免战由攻击方触发不区分防守方"
  - §2.3 免战截止时间明确为堡垒属性,配置可调
  - §4.3 归属衰减处补"龙巢有失效状态,详见 §5.1"
  - §4.6 KVK 期间原服堡垒占领时间改为固定倍率延长(全服生效,不按联盟参战比例)
  - §5.1 龙巢失去相邻堡垒进入失效状态(复用现有龙巢已有失效机制)
  - §7.4 恶魔守卫重写:与泰坦/野怪同层的野生 PVE,无归属,按周期刷新,不影响堡垒占领资格
  - §7.5 新增龙巢守卫章节:龙巢内部数据不显示在地图,攻击龙巢时的固有战斗对手
  - §14 遗留清单从 17 项降到 16 项(移除已决策 3 项,新增 1 项守卫刷新周期)
- 更新 wiki/index.md:k1-new-server-map-plan 摘要版本号 v0.2 → v0.3

## [2026-07-02] ingest — 更新 K1 新服大地图重构策划案到 v0.2
- 来源:
  - `wiki/gaming/k1-new-server-map-plan.md` 初稿
  - 对话确认的 5 条规则修正:活动/任务/排行重配、龙巢放在 4 堡垒交叉区、保留公共冷启动锚点且首占免战、KVK 期间原服堡垒占领时间延长、王座战完全复用现有规则
- 更新 1 页:[[k1-new-server-map-plan]]
  - 补齐 frontmatter,版本从 v0.1 初稿调整为 v0.2 规则收敛稿
  - 将"活动/任务/排行完全不变"改为"商业化主结构保留,地图相关活动/任务/成就/排行计数重配"
  - 重写龙巢规则:龙巢位于 4 个相邻堡垒交叉区域,不属于单个堡垒方格
  - 重写新联盟冷启动:公共锚点第一圈可攻击中立或既有堡垒,首占后进入免战时间
  - 补 KVK 期间保护:原服普通堡垒不冻结,但占领所需时间大幅延长
  - 明确王座战斗、占领、重置和奖励坚持复用现有规则
- 更新 wiki/index.md:gaming 分区新增「项目/方案」入口

## [2026-07-02] ingest — 整理 Confluence K1 游戏知识第一批
- 来源:
  - Confluence `K1 游戏知识` 根页 `https://wiki.tap4fun.com/pages/viewpage.action?pageId=61901480`
  - 递归盘点 842 个子页面;直接主干包括 `K1活动`、`K1 常见问题`、`K1付费活动/累计充值活动`、`需删除`、`K1 联盟对决`
- 新建 5 页:
  - [[k1-project-knowledge-map]]:页面树盘点与清洗规则,默认排除 `需删除`、旧/过期/废弃页
  - [[k1-live-activity-patterns-2026h1]]:从沙漠盛典、启明神焰、乐园狂欢、荒野狩猎、机械边境等近期活动提炼复用活动骨架
  - [[k1-cs-faq-current]]:整理守卫币、领主装备、联盟跨服召集、新玩家保护等客服答复边界
  - [[k1-kvk-burning-expedition]]:整理燃烧的远征/KVK、女神系统、安全区、联盟规则与客服口径
  - [[k1-paid-products-current]]:整理守卫币、精英卡、成长基金、商会补给、首充等付费产品当前口径
- 更新 5 页反链/补充:
  - [[k1-monthly-overview]],[[k1-activity-monetization-2026h1]],[[k1-payment-structure]],[[k1-wilderness-hunting-return-analysis]],[[work-dingtalk-logs-2026-h1]]
- 更新 wiki/index.md:work 分区新增「项目组 wiki 口径」入口
- 边界:Confluence 页面部分可能过期,本批页面置信度统一偏保守;奖励表、道具 ID、服务器范围等易变数据不沉淀为长期事实

## [2026-07-01] ingest — 写入 2026H1 数据分析批次
- 来源:
  - `sources/work/k1-data-analysis-2026-06/【K1】2026年H1满意度报告 - 0610 - final.pdf`
  - `sources/work/k1-data-analysis-2026-06/2026H1付费体验下降归因.html`
  - `sources/work/k1-data-analysis-2026-06/【K1】荒野狩猎活动回归.html`
  - `sources/work/k1-data-analysis-2026-06/月度流水构成分析-后续不做节日活动分析.html`
- 新建 4 页素材摘要:
  - [[k1-satisfaction-2026-h1]]:满意度 60.11、忠诚度 59.66,付费体验最低,礼包性价比/付费活动为最低三级指标
  - [[k1-payment-experience-decline-2026-h1]]:付费体验下降归因,记录新玩家第一印象、俄语区、边付边骂、巨蛇争议等线索
  - [[k1-wilderness-hunting-return-analysis]]:荒野狩猎两期回归分析,活动拉 PVE/在线但不明显拉付费率或 ARPPU
  - [[k1-no-holiday-event-revenue-forecast]]:不做节日活动流水推算,未来 6 个月净少赚约 $5.22M,并补 open_udid 设备口径 DAC 风险
- 新建 1 页综合:[[k1-activity-monetization-2026h1]]
  - 综合判断:节日活动仍有真增量,但继续堆活动密度不能解决付费价值感、L1/L2 DAC 下滑和新玩家单价下降
- 更新 5 页反链/补充:
  - [[k1-monthly-overview]],[[k1-payment-structure]],[[k1-revenue-arpc]],[[k1-dac]],[[k1-new-player-retention-roi]]
- 更新 wiki/index.md:work 分区新增 2026H1 数据分析批次入口

## [2026-06-30] ingest — 综合页扩充 06-27 之后的 4 条工作流经验
- 来源:`sources/ai-llm/hook-fires-2026-06.md`(06-29 新增 5 段总结:Agent Reach 安装 1 段 + slice-editor 反导 4 段;06-26 两条 test prompt 空 stub 忽略)
- 更新 1 页:[[ai-claude-workflow-lessons]](synthesis,date 刷新至 2026-06-30)
  - 新增章节「2026-06-27 之后的补充」,追加 §13-16 四条原则:外部 installer 先跑 dry-run/safe、报告成功前三件套(exit code + git status + 抽样读)、反向同步函数默认最小覆盖、配置工具必问「真相源是哪个文件」
  - §14 与 §8 同族(绿灯 ≠ 已通过,本月第二次翻车)、§15 与 §16 呼应本轮 slice-editor 反导用了 5 版才对
  - frontmatter tags 增补:反向同步 / 真相源 / 报告成功前自检 / 外部installer / 最小覆盖
- 未新建页面,未改动 index.md(仅摘要级刷新按需后续,本轮暂免)
- 未处理:未跟踪的 wiki/ai-llm/{karpathy,rag,gbrain,...}.md 属旧遗留,不属本次 ingest,另行分开处理

## [2026-06-29] ingest — 更新钉钉日志增量到 06-26
- 来源:
  - `sources/work/dingtalk-logs-2026/dingtalk-logs-2026.md`(2026-01-01 至 2026-06-26,116 条钉钉日报)
- 更新 1 页:[[work-dingtalk-logs-2026-h1]](source-summary,date 刷新至 2026-06-29)
  - 覆盖范围从 113 条扩到 116 条;补充 06-24/06-25/06-26 世界杯主题活动关卡正式配置、朝向与人球重叠处理、坐标系等比缩小、初始占位、足球飞行手感、关卡难度适配和球员 AI 行为调整
  - 继续只总结日报工作事项,不外推经营表现或功能收益
- 更新 wiki/index.md:work H1 日志条数改为 116,摘要补充手感调优
- 未写入 `sources/ai-llm/hook-fires-2026-06.md` 的 06-26 test prompt/TODO 占位;`sources/work/历史报告综述_2025-01至2026-04.md` 仍待单独裁决

## [2026-06-26] ingest — 执行每日巡检建议,更新钉钉日志与 hook 工作流经验
- 来源:
  - `sources/work/dingtalk-logs-2026/dingtalk-logs-2026.md`(2026-01-01 至 2026-06-23,113 条钉钉日报)
  - `sources/ai-llm/hook-fires-2026-06.md`(06-23 至 06-25 的新增自动总结)
- 更新 1 页:[[work-dingtalk-logs-2026-h1]](source-summary,date 刷新至 2026-06-26)
  - 覆盖范围从 111 条扩到 113 条;补充 06-22/06-23 世界杯主题活动正式配置、静态参数、场景/球员/足球比例、引导配置和分组讨论
  - 继续只总结日报工作事项,不外推经营表现或功能收益
- 更新 2 页:[[ai-claude-workflow-lessons]] 与 [[windows-python-hook-stdout-ascii]]
  - 补充 lint 反向注入测试、硬范围/软分布/设计意图三层审核、全局参数语义迁移、xlsx 写前脏检测、extractor/drift 检查和 xmind 解析 helper
  - 为 Windows 中文编码经验补上到工作流综合页的反链
- 更新 wiki/index.md:work H1 日志条数改为 113;ai-llm 综合页摘要刷新

## [2026-06-23] ingest — 采纳钉钉日志归档入库
- 来源:
  - `sources/work/dingtalk-logs-2026/dingtalk-logs-2026.md`(2026-01-01 至 2026-06-22,111 条钉钉日报)
  - `sources/work/dingtalk-logs-2026/dingtalk-logs-2026-raw.json`(结构化备查)
- 新建 1 页:[[work-dingtalk-logs-2026-h1]](source-summary,confidence: high)
  - 提炼 2026H1 工作主线:联盟对决/SVS/KVK → 巨龙培育与 KVK 新赛季 → 世界杯主题活动与 AI 协作文档/配置流
  - 保留边界:只总结日报工作事项,不外推经营表现或版本收益
- 更新 2 页 backlink:
  - [[work-weekly-2026-06-08]] 与 H1 钉钉日志摘要双向链接
  - [[k1-monthly-overview]] 增加工作日志入口;不批量硬链所有 K1 指标页
- 更新 wiki/index.md:work「素材摘要」新增 H1 钉钉日志归档

## [2026-06-22] ingest — 采纳每日巡检建议,写入 1 篇周报并扩充 hook 工作流经验
- 来源:
  - `sources/work/周报-2026-06-08.md`
  - `sources/ai-llm/hook-fires-2026-06.md`(06-18 13:10 至 06-22 11:20 的新增 4 段详细总结)
- 新建 1 页:[[work-weekly-2026-06-08]](source-summary,confidence: high)
  - 提炼 2026-06-08 至 06-14 的 17 条 worklog:世界杯主题活动、巨龙培育、周年庆验收、KVK 后续目标、AI skill 效率工作
  - 与 [[k1-monthly-overview]] 做双向链接;不硬链其它 K1 指标页
- 更新 1 页:[[ai-claude-workflow-lessons]](synthesis,confidence: medium,date 刷新至 2026-06-22)
  - 在原三条原则外补充 rolling source ingest 类型判定、协议/配置 lint 防漂移、references TBD 状态机、分批写 plan 禁止同消息 Write+Bash
- 更新 wiki/index.md:work 增加「素材摘要」分区;ai-llm 综合页摘要刷新

## [2026-06-18] ingest — 从 hook 自动产出的 6 月日志提炼工作流经验
- 来源:`sources/ai-llm/hook-fires-2026-06.md`(hook-usage-log-pipeline 在 6 月的 4 段自动总结)
- 新建 1 页:[[ai-claude-workflow-lessons]](synthesis,confidence: medium)
  - 把 6 条原始建议归并为 3 条最稳的原则:brainstorming ≥6 轮汇总 / >300 行一次性 Write / subagent reviewer 必须读 spec
  - 互链 [[hook-usage-log-pipeline]](反向加 link)、[[windows-python-hook-stdout-ascii]]、[[llm-wiki-pattern]]
- 更新 wiki/index.md:ai-llm「综合」分区从 1 条增至 2 条
- 选 A 方案而非 C(只记 log)的依据:#1/#2/#3 三条跨项目复用价值高,留在 sources 会被新月份日志稀释
- 排除入页的 2 条建议(`templates/config-tool-spec.md` / `scripts/check_plan_signatures.py`)只在新页「已落地的较小项」一节点名,不另开页 —— 它们是项目内部工具,跨项目复用性中等

## [2026-06-17] ingest — 从 MindToDoc auto-memory 回填 2 条经验
- 来源:`~/.kiro/projects/C--Project-MindToDoc/memory/` 的当日 6 条 memory，按"对未来仍具参考价值"标准筛选
- 新建 2 页:
  - ai-llm 概念 ×1:[[dingtalk-md-escape-diff]](技术 recipe,跨项目复用)
  - gaming 概念 ×1:[[双模式难度故意不对齐]](可泛化游戏设计模式)
- 排除 4 条(留在 auto-memory):user 角色、2 条 feedback 协作偏好、1 条项目内部状态
- 更新 index.md:gaming 新增 1 条、ai-llm 个人经验新增 1 条
- 背景:hook 在 06-17 19:14 触发(321k tokens, 切片操作模式讨论),已修订 `summarize-gate.py` reason 模板,后续 memory 写入会自动判断是否同步 KB

## [2026-06-16] ingest — 新增 3 篇素材(ai-llm hook 经验 ×2 + gaming 兼容自检 ×1)
- 来源:sources/ai-llm/hook-usage-log-pipeline、windows-python-hook-stdout-ascii;sources/gaming/高兼容性风险的修改项自检
- 新建 3 页:
  - ai-llm source-summary ×2:hook-usage-log-pipeline、windows-python-hook-stdout-ascii(两页互链,均个人亲历经验标 high)
  - gaming concept ×1:高兼容性风险修改项自检(K1 开发规范,补全「新旧版本兼容/团队规范沉淀」背景后标 high)
- 更新 index.md:ai-llm 新增「个人经验」小组(2 条)、gaming 分区从「暂无」改为 1 条
- 边界:gaming 页不硬链 work 域机密页,仅正文点明「源自 K1 实践」,避免协作者侧悬空链接
- lint(ai-llm)通过

## [2026-06-12] ingest — K1 月报补全全年趋势(2025-01 至 2026-05)
- 来源:sources/work/ 全 17 期月报
- 将 7 个 work 指标页从"仅最新两月"扩展为全年趋势:
  - revenue-arpc / edau / dac / payment-structure / retention-roi 补 17 月数据表
  - progression-lines 补科研/图鉴满进度长期曲线
  - monthly-overview 改为全年经营快照(全年大势 + 关键转折 + 近月对照)
- 更新 index.md work 分区摘要
- 核心结论:规模一年收缩 61%(EDAU 15.1万→5.9万)、流水千万→600万,靠付费深度(ARPC/超R)撑收入;2026-01 运营控制拉收致流水 -25.6%

## [2026-06-12] ingest — K1 数据月报试点(2026-04, 2026-05)
- 来源:sources/work/ 的 k1-月报-2026-04 / 2026-05(17 份已全部转 md,机密仅本地)
- 新建 7 页(均在 wiki/work/,仅本地不推送):
  - concept ×6:k1-revenue-arpc、k1-payment-structure、k1-edau、k1-dac、k1-new-player-retention-roi、k1-progression-lines
  - synthesis ×1:k1-monthly-overview
- 更新 wiki/index.md 的 work 分区(7 条目)
- 试点范围:仅最新两月;后续可补 2025-01 起的全年趋势
- 置信度 high(来自机密月报原文数字)

## [2026-06-12] ingest — AI/LLM 四篇 LLM Wiki 素材
- 来源:sources/ai-llm/ 的 karpathy / atlan / saeloun / gbrain 四篇
- 新建 8 页(均在 wiki/ai-llm/):
  - source-summary ×4:karpathy-llm-wiki、atlan-llm-wiki-vs-rag、saeloun-private-llm-wiki、gbrain
  - concept ×2:llm-wiki-pattern、rag
  - entity ×1:karpathy
  - synthesis ×1:llm-wiki-vs-rag(规模决定架构,双源支撑标 high)
- 更新 wiki/index.md 的 ai-llm 分区(8 条目)
- 置信度:gbrain/saeloun/karpathy(实体)标 medium(数字未核实或履历未覆盖),其余 high

## [2026-06-11] init — 知识库初始化
- 建立三层结构与 work/gaming/ai-llm 三域分区
- 添加 search.py / lint.py 工具
