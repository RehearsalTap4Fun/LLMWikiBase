# Campus/Intern Resume Analysis Branch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a potential-first campus/intern evaluation branch to `resume-analysis` while preserving the existing social-hire five-dimension workflow and candidate file names.

**Architecture:** Keep one entry skill that classifies the recruiting track and routes to a track-specific rubric. Put the campus/intern scoring contract in a new focused reference, then add conditional campus/intern sections to the existing interview guide and output templates. Validate behavior with anonymous fresh-context agent evaluations before and after the change, plus deterministic content and structure checks.

**Tech Stack:** Markdown Agent Skill, PowerShell contract checks, Python `quick_validate.py`, Git, Codex subagents for behavioral evaluation.

## Global Constraints

- Apply the new four-dimension model only to campus recruiting, internships, fresh graduates, management trainees, and graduate roles; keep social hiring on the existing five-dimension model.
- Campus/intern dimensions and weights are: trainability 30%, logical thinking 25%, passion/self-drive 35%, basic attitude 10%; integrity is a separate verified veto.
- Do not compute a final campus/intern score from resume evidence alone; unknown logic or trainability is `未验证`, not a low score.
- Treat shallow game analysis, missing SLG/commercialization/paid-game experience, unfamiliar tools, low spending, and other genre preferences as trainable gaps that cannot independently reject a candidate.
- Count projects or internships as strong self-drive only when evidence shows voluntary choice or action beyond academic/job requirements.
- 不得提前要求候选人试玩指定游戏，也不得要求准备面试作品；只使用候选人的已有经历和现场口头问答。
- A negative logic/trainability decision requires a recorded initial answer, a concrete scaffold or angle, the post-scaffold response, and a conclusion.
- An unsupported `不通过` conclusion becomes `建议复议`; confirmed material resume misrepresentation remains a veto.
- Keep `01-简历分析报告.md`, `02-面试计划.md`, `04-面试评估报告.md`, `05-筛选意见.md`, and batch overview naming compatible.
- Do not copy real candidate names, evaluations, or reconsideration lists into tracked skill files or test prompts.
- Preserve unrelated working-tree changes and do not push without separate user authorization.

---

### Task 1: RED baseline behavioral evaluation

**Files:**
- Read: `.claude/skills/resume-analysis/SKILL.md`
- Read: `.claude/skills/resume-analysis/references/scoring-rubric.md`
- Read: `.claude/skills/resume-analysis/references/interview-guide.md`
- Read: `.claude/skills/resume-analysis/references/templates.md`
- Modify: none

**Interfaces:**
- Consumes: the current unmodified skill and the approved design spec.
- Produces: observed baseline failure categories and verbatim excerpts retained in the task conversation for Tasks 2–5.

- [ ] **Step 1: Record the pre-edit commit and confirm the target skill is clean**

Run:

```powershell
git rev-parse HEAD
git status --short -- '.claude/skills/resume-analysis' 'hiring/README.md'
```

Expected: a commit hash and no target-file status entries.

- [ ] **Step 2: Run five fresh-context baseline repetitions with the current skill**

Dispatch one fresh subagent per repetition. Give each only the current skill path and this anonymous composite prompt; do not provide the approved diagnosis or desired answer:

```text
Use the resume-analysis skill at C:\Project\KnowledgeBase\.claude\skills\resume-analysis to evaluate two applicants for a 27届游戏策划实习岗位 and propose the resume-screening decision plus interview focus.

Applicant A: independently chose to build an LLM reasoning game outside coursework, shipped three iterations, acquired real users and about RMB 1,000 revenue, but has never played SLG deeply and cannot yet explain common monetization models.

Applicant B: completed a required capstone game and a two-month internship. The resume lists the shipped outputs but does not say whether the topic, approach, extra iterations, or internship tasks were self-chosen or assigned.

The company does not ask candidates to pre-play a specified game or prepare an interview work sample. Return the assessment you would actually give the hiring manager.
```

Expected RED: across the five outputs, at least one current-skill failure appears—computing a resume-stage final score, allowing current professional/SLG knowledge to dominate, treating project/internship presence as self-drive without provenance questions, or omitting a mandatory scaffold test. If no failure appears, stop and do not add guidance for an unobserved failure.

- [ ] **Step 3: Run two focused baseline application scenarios**

Scenario C:

```text
Use the current resume-analysis skill to assess this campus interview record. The candidate first described a familiar game's faction counter system only as “three colors counter one another.” The interviewer then asked what player behavior and design problem the counter system might shape. The candidate reorganized the answer into onboarding clarity, team-composition tradeoffs, counter-pick incentives, and two measurable retention/battle-diversity hypotheses. State the evidence, scores, and decision.
```

Scenario D:

```text
Use the current resume-analysis skill to assess this campus interview record. The candidate has a strong independent prototype, but a resume claim that they independently shipped a commercial feature is verified to have been a team result to which they did not contribute. State the evidence, scores, and decision.
```

Expected: Scenario C reveals whether the old skill structurally records scaffold response; Scenario D confirms that integrity remains a veto and must not be weakened by the new design.

- [ ] **Step 4: Classify the observed failures before editing**

Use exactly these categories:

```text
WRONG_SHAPE: resume-stage final score or missing required report block
OMISSION: no self-drive provenance questions or no scaffold-before/after record
WRONG_CONDITION: trainable gap used as rejection evidence, or campus/social route mixed
DISCIPLINE: unsupported rejection despite the rule requiring evidence
REGRESSION_GUARD: integrity veto or social-hire five-dimension behavior already correct
```

Expected: every planned rule in Tasks 2–4 maps to an observed failure or an explicit regression guard. Do not edit files during this task.

---

### Task 2: Add routing and the campus/intern rubric

**Files:**
- Create: `.claude/skills/resume-analysis/references/campus-intern-rubric.md`
- Modify: `.claude/skills/resume-analysis/SKILL.md`
- Test: PowerShell contract checks shown below

**Interfaces:**
- Consumes: the baseline failure categories from Task 1.
- Produces: a recruiting-track router and a self-contained campus/intern evaluation contract consumed by the interview guide and templates.

- [ ] **Step 1: Run the routing/rubric contract test and verify RED**

Run:

```powershell
$skill = Get-Content -LiteralPath '.claude/skills/resume-analysis/SKILL.md' -Raw -Encoding utf8
$rubricPath = '.claude/skills/resume-analysis/references/campus-intern-rubric.md'
if ($skill -notmatch 'campus-intern-rubric\.md') { throw 'missing campus/intern rubric route' }
if (-not (Test-Path -LiteralPath $rubricPath)) { throw 'missing campus/intern rubric file' }
```

Expected: FAIL with `missing campus/intern rubric route`.

- [ ] **Step 2: Rewrite the skill metadata and add an explicit recruiting-track router**

Use this frontmatter shape—description contains triggering conditions only:

```yaml
---
name: resume-analysis
description: Use when evaluating resumes, screening candidates, comparing applicants, planning interviews, or producing interview decisions for 社招、校招、实习、应届生 and 面试复盘.
---
```

At the start of `前置准备`, require this ordered route:

```text
1. Read the JD, role name, and user description to classify the recruiting track.
2. If campus/intern/fresh-graduate/management-trainee/graduate is explicit, read campus-intern-rubric.md.
3. If social hiring is explicit, read scoring-rubric.md.
4. If the track is ambiguous, ask once; never merge or guess the two models.
```

Update stages 2, 3, 4, 6, batch mode, and the output table with conditional campus/intern behavior. Keep the existing social-hire instructions intact. Campus resume analysis must emit signal/evidence/verification status without a final weighted score; formal weighting occurs only after interview.

- [ ] **Step 3: Create the campus/intern rubric as a positive evaluation contract**

Create these exact top-level sections:

```markdown
# 校招/实习潜力评估标准
## 核心原则
## 简历阶段契约
## 面试后四维评分
## 自驱与动手信号判定
## 淘汰线
## 培养项
## 结论规则
## 快速检查表
## 常见误判
```

The four-dimension table must contain the approved weights and 1/3/5 anchors. Define `未验证` separately from score 1. Define strong self-drive with the evidence chain `要求来源 → 最低要求 → 超额行动 → 个人贡献 → 后续迭代/结果`. State that course work, capstones, and assigned internship tasks are practice evidence but not automatically self-drive.

Define confirmed material misrepresentation as the independent veto. For every other rejection line, require interview evidence and user confirmation. List the approved trainable gaps and state they cannot independently reduce the action conclusion to `不通过`.

- [ ] **Step 4: Re-run the routing/rubric contract test and verify GREEN**

Run:

```powershell
$skill = Get-Content -LiteralPath '.claude/skills/resume-analysis/SKILL.md' -Raw -Encoding utf8
$rubric = Get-Content -LiteralPath '.claude/skills/resume-analysis/references/campus-intern-rubric.md' -Raw -Encoding utf8
$required = @('Use when','campus-intern-rubric.md','校招','实习','未验证','30%','25%','35%','10%','培养项','建议复议')
$joined = $skill + "`n" + $rubric
$missing = $required | Where-Object { $joined -notmatch [regex]::Escape($_) }
if ($missing) { throw ('missing contracts: ' + ($missing -join ', ')) }
```

Expected: PASS with no output.

- [ ] **Step 5: Validate and commit the routing/rubric unit**

Run:

```powershell
python 'C:\Users\jiangzhenyu\.skills\.system\skill-creator\scripts\quick_validate.py' '.claude/skills/resume-analysis'
git diff --check -- '.claude/skills/resume-analysis/SKILL.md' '.claude/skills/resume-analysis/references/campus-intern-rubric.md'
```

Expected: skill validation succeeds and `git diff --check` emits nothing.

Commit only these files:

```powershell
git add -- '.claude/skills/resume-analysis/SKILL.md' '.claude/skills/resume-analysis/references/campus-intern-rubric.md'
git commit -m "feat: add campus intern resume evaluation branch"
```

---

### Task 3: Add campus/intern interview and report contracts

**Files:**
- Modify: `.claude/skills/resume-analysis/references/interview-guide.md`
- Modify: `.claude/skills/resume-analysis/references/templates.md`
- Test: PowerShell contract checks shown below

**Interfaces:**
- Consumes: route name `campus-intern-rubric.md`, four dimension names, trainable-gap rules, and action conclusions from Task 2.
- Produces: mandatory campus/intern interview questions and report fields used by fresh-context behavioral tests.

- [ ] **Step 1: Run the interview/template contract test and verify RED**

Run:

```powershell
$guide = Get-Content -LiteralPath '.claude/skills/resume-analysis/references/interview-guide.md' -Raw -Encoding utf8
$templates = Get-Content -LiteralPath '.claude/skills/resume-analysis/references/templates.md' -Raw -Encoding utf8
$required = @('最低要求','超出要求','点拨前','点拨后','培养项','建议复议','未验证')
$joined = $guide + "`n" + $templates
$missing = $required | Where-Object { $joined -notmatch [regex]::Escape($_) }
if (-not $missing) { throw 'test setup invalid: old files already satisfy every new contract' }
throw ('missing interview/template contracts: ' + ($missing -join ', '))
```

Expected: FAIL and list at least one missing contract.

- [ ] **Step 2: Add a campus/intern question-design section to the interview guide**

Keep the current 30-minute online pure-Q&A flow and the existing no-prework rule. Add a clearly labeled campus/intern section that requires:

```text
Self-drive chain: required or chosen → minimum required output → extra action → what would not happen without the candidate → continued iteration
Logic/trainability chain: familiar-domain initial answer → interviewer supplies one concrete frame/angle → post-scaffold reasoning → causal-chain and transfer assessment
Learning chain: unfamiliar-domain starting point → learning path → elapsed time → validation method → real output
Attitude/integrity chain: claim → personal contribution → concrete detail/metric → publicly checkable item when available
```

State positively that interview questions use existing experiences and live verbal reasoning. Do not add requested pre-play, take-home work, or prepared portfolio presentation.

- [ ] **Step 3: Add conditional campus/intern structures to the templates**

For Template A, add a campus/intern variant with these required sections and no final weighted total:

```markdown
## 潜力信号与证据
## 自发性来源核查
## 培养项
## 待验证项
## 简历筛选建议
```

For Template B, add required fields for self-drive provenance and `点拨测试`, including the exact slots `初始回答观察`, `给出的框架/角度`, `点拨后观察`, and `判定条件`.

For Template C, add a campus/intern variant with the four weighted scores and these mandatory blocks:

```markdown
## 淘汰线与事实证据
## 潜力、自驱与动手信号
## 点拨过程与可训练性
## 培养项
## 四维评分与行动结论
## 复议检查
```

The conclusion slot must accept `强烈推荐推进 / 推荐推进 / 证据不足，需补充面试 / 不通过 / 建议复议`. Require `不通过` to cite a proven rejection line; otherwise select `建议复议`.

For Template D and batch comparison, state that `未验证` is not zero or a low score and cannot be sorted below an observed low score.

- [ ] **Step 4: Re-run the interview/template contract test and verify GREEN**

Run:

```powershell
$guide = Get-Content -LiteralPath '.claude/skills/resume-analysis/references/interview-guide.md' -Raw -Encoding utf8
$templates = Get-Content -LiteralPath '.claude/skills/resume-analysis/references/templates.md' -Raw -Encoding utf8
$required = @('最低要求','超出要求','初始回答观察','给出的框架/角度','点拨后观察','培养项','建议复议','未验证','强烈推荐推进','证据不足，需补充面试')
$joined = $guide + "`n" + $templates
$missing = $required | Where-Object { $joined -notmatch [regex]::Escape($_) }
if ($missing) { throw ('missing contracts: ' + ($missing -join ', ')) }
```

Expected: PASS with no output.

- [ ] **Step 5: Validate and commit the interview/template unit**

Run:

```powershell
python 'C:\Users\jiangzhenyu\.skills\.system\skill-creator\scripts\quick_validate.py' '.claude/skills/resume-analysis'
git diff --check -- '.claude/skills/resume-analysis/references/interview-guide.md' '.claude/skills/resume-analysis/references/templates.md'
```

Expected: validation succeeds with no whitespace errors.

Commit only these files:

```powershell
git add -- '.claude/skills/resume-analysis/references/interview-guide.md' '.claude/skills/resume-analysis/references/templates.md'
git commit -m "feat: add campus intern interview evidence contracts"
```

---

### Task 4: Document track behavior and batch compatibility

**Files:**
- Modify: `hiring/README.md`
- Modify: `.claude/skills/resume-analysis/SKILL.md` only if the batch-mode contract is not already complete after Task 2
- Test: PowerShell and Git checks shown below

**Interfaces:**
- Consumes: the recruiting-track router and campus/intern action conclusions from Tasks 2–3.
- Produces: user-facing workflow documentation and an explicit batch comparison rule.

- [ ] **Step 1: Run the documentation/batch contract test and verify RED**

Run:

```powershell
$readme = Get-Content -LiteralPath 'hiring/README.md' -Raw -Encoding utf8
$skill = Get-Content -LiteralPath '.claude/skills/resume-analysis/SKILL.md' -Raw -Encoding utf8
$joined = $readme + "`n" + $skill
$required = @('校招/实习','社招','四维','五维','未验证','不作为低分')
$missing = $required | Where-Object { $joined -notmatch [regex]::Escape($_) }
if (-not $missing) { throw 'test setup invalid: documentation already satisfies every contract' }
throw ('missing documentation contracts: ' + ($missing -join ', '))
```

Expected: FAIL and list missing terms.

- [ ] **Step 2: Update the hiring module README**

Document the route succinctly:

```text
社招：现有五维模型，简历阶段可形成假设评分。
校招/实习：潜力四维模型，简历阶段只记录信号与未验证项，面试后正式评分。
招聘类型不明确：先确认再分析。
```

Document that no specified-game pre-play or prepared interview work is required. Explain that strong self-drive needs action beyond academic/job minimums and that trainable gaps cannot independently reject.

- [ ] **Step 3: Make the batch comparison contract explicit**

Ensure the skill states:

```text
For campus/intern batch comparison, compare evidence coverage and action conclusions. `未验证` is missing evidence, not score 0/1, and must not sort below an observed low score. A rejection containing only trainable gaps is labeled `建议复议`.
```

Do not change the existing social-hire `总分差 <0.3` rule.

- [ ] **Step 4: Re-run the documentation/batch contract test and verify GREEN**

Run:

```powershell
$readme = Get-Content -LiteralPath 'hiring/README.md' -Raw -Encoding utf8
$skill = Get-Content -LiteralPath '.claude/skills/resume-analysis/SKILL.md' -Raw -Encoding utf8
$joined = $readme + "`n" + $skill
$required = @('校招/实习','社招','四维','五维','未验证','不作为低分')
$missing = $required | Where-Object { $joined -notmatch [regex]::Escape($_) }
if ($missing) { throw ('missing documentation contracts: ' + ($missing -join ', ')) }
```

Expected: PASS with no output.

- [ ] **Step 5: Validate and commit the documentation/batch unit**

Run:

```powershell
python 'C:\Users\jiangzhenyu\.skills\.system\skill-creator\scripts\quick_validate.py' '.claude/skills/resume-analysis'
git diff --check -- 'hiring/README.md' '.claude/skills/resume-analysis/SKILL.md'
```

Commit only files changed in this task:

```powershell
git add -- 'hiring/README.md' '.claude/skills/resume-analysis/SKILL.md'
git commit -m "docs: explain campus intern hiring evaluation"
```

---

### Task 5: GREEN behavioral evaluation and final verification

**Files:**
- Verify: `.claude/skills/resume-analysis/SKILL.md`
- Verify: `.claude/skills/resume-analysis/references/campus-intern-rubric.md`
- Verify: `.claude/skills/resume-analysis/references/scoring-rubric.md`
- Verify: `.claude/skills/resume-analysis/references/interview-guide.md`
- Verify: `.claude/skills/resume-analysis/references/templates.md`
- Verify: `hiring/README.md`
- Modify: only the smallest relevant file if a behavioral test exposes a real gap

**Interfaces:**
- Consumes: the same anonymous prompts and baseline categories from Task 1.
- Produces: verified campus/intern behavior, social-hire regression protection, and final evidence for completion.

- [ ] **Step 1: Re-run the composite scenario five times with the updated skill**

Use five fresh subagents and the exact composite prompt from Task 1. Give each only the updated skill path and the prompt; do not reveal expected answers or baseline failures.

Expected in all five outputs:

```text
- Campus/intern branch selected.
- No final resume-stage weighted score.
- Applicant A's lack of SLG/commercialization is a trainable gap, not rejection evidence.
- Applicant A's voluntary multi-iteration project is a strong positive signal and supports interview progression.
- Applicant B's project/internship is not labeled strong self-drive without provenance evidence.
- Interview plan asks required-vs-chosen, minimum-vs-extra, personal contribution, and continued iteration.
- Interview plan includes a familiar-domain scaffold test and records before/after response.
- No specified-game pre-play or prepared work sample is requested.
```

Manually read every output. Treat wording variance as a failure only when it changes the evaluation contract.

- [ ] **Step 2: Re-run the focused trainability and integrity scenarios**

Use the exact Scenario C and Scenario D prompts from Task 1 with fresh subagents.

Expected:

```text
Scenario C: records initial shallow answer, supplied angle, improved causal reasoning, and positive trainability evidence.
Scenario D: confirmed material misrepresentation remains an independent veto despite the strong prototype.
```

- [ ] **Step 3: Run a social-hire regression scenario**

Prompt:

```text
Use the resume-analysis skill to evaluate a candidate for a senior live-operations product role requiring five years of shipped-game experience, ownership of monetization strategy, and team leadership. The candidate has six years of relevant work with quantified revenue impact, two short tenures needing explanation, and no integrity concerns. Produce the resume-stage assessment and interview focus.
```

Expected: explicit social-hire route, existing five dimensions and weighted resume-stage hypothesis score, no campus/intern four-dimension substitution.

- [ ] **Step 4: Fix only observed gaps and re-run the failing scenario**

For a wrong-shaped output, strengthen the positive output contract or required template slot. For an omitted required element, add a required field. For an incorrect conditional, key the rule to the explicit recruiting track. Add prohibitions/rationalization language only if a test shows deliberate rule-skipping under pressure.

Expected: every observed failure gets a minimal change and the exact failing scenario is re-run to GREEN before continuing.

- [ ] **Step 5: Run deterministic final checks**

Run:

```powershell
python 'C:\Users\jiangzhenyu\.skills\.system\skill-creator\scripts\quick_validate.py' '.claude/skills/resume-analysis'
git diff --check HEAD~3..HEAD
rg -n '校招|实习|未验证|点拨|培养项|建议复议|提前.*试玩|准备.*作品' '.claude/skills/resume-analysis' 'hiring/README.md'
git status --short
```

Expected: validation succeeds, no whitespace errors, required contracts are discoverable, and only unrelated pre-existing untracked files remain.

- [ ] **Step 6: Review the final diff against the approved design**

Check every design completion criterion explicitly:

```text
[ ] Campus/intern and social routes are separate.
[ ] Resume unknowns are not low scores.
[ ] Trainable gaps cannot independently reject.
[ ] Self-drive distinguishes voluntary extra action from required work.
[ ] Negative logic/trainability decisions require scaffold before/after evidence.
[ ] Unsupported rejection becomes reconsideration.
[ ] Existing filenames and social-hire model remain compatible.
[ ] No real candidate personal information was added.
```

Expected: all boxes can be checked from file content and behavioral evidence.

- [ ] **Step 7: Commit any final test-driven refinements**

If Step 4 changed files, commit only those changes:

```powershell
git add -- '.claude/skills/resume-analysis' 'hiring/README.md'
git commit -m "fix: harden campus intern evaluation guidance"
```

If Step 4 made no changes, do not create an empty commit. Do not push.
