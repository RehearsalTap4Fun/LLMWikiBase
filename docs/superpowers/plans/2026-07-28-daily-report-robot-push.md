# Daily Report Robot Push Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `automation-2` so concise completed-work reports are pushed once to the verified DingTalk Webhook robot instead of creating a DingTalk report.

**Architecture:** Keep the existing 24-hour conversation review and categorized source output. When completed work exists, build a local preview from concise business-language items, then send the same content through the verified Webhook path while retrieving its token from the successful historical call without copying the credential into configuration or memory.

**Tech Stack:** Codex heartbeat automation TOML, Markdown memory, DWS DingTalk chat command.

## Global Constraints

- Send only when at least one completed work item exists.
- Include only `今日完成工作`, with one concise `具体事项 + 结果` sentence per item.
- Omit exact figures, low-level code terms, field names, paths, configuration IDs, and API/MCP implementation details.
- The title and first body line must contain `每日报告`; do not @ anyone.
- Do not call DingTalk Report `create_report`.
- Never print or persist the Webhook token or signing secret.
- Make only one send attempt when the result is uncertain, avoiding duplicate messages.

---

### Task 1: Update and verify automation behavior

**Files:**
- Modify: `C:\Users\jiangzhenyu\.codex\automations\automation-2\automation.toml`
- Modify: `C:\Users\jiangzhenyu\.codex\automations\automation-2\memory.md`

**Interfaces:**
- Consumes: categorized experience summaries and the verified historical Webhook call in task `019fa3cc-4f7c-76e0-bd40-cdfbeb3f5d50`.
- Produces: a local work-report preview and, when work exists, one DingTalk robot message to the Webhook-bound `rehearsal` group.

- [x] **Step 1: Replace the stale report-creation prompt**

Write the exact rules from Global Constraints into `automation.toml`, preserving the schedule, status, target task, and automation ID.

- [x] **Step 2: Record the verified behavior**

Append a memory entry stating that the 2026-07-27 refined preview was accepted by DingTalk with `errcode=0`, the user confirmed the test, and future runs must use the Webhook robot path without copying credentials.

- [x] **Step 3: Validate configuration and credential hygiene**

Run a fresh TOML/text inspection confirming the automation is active, the old `create_report` behavior is absent, the new robot rules are present, and neither modified file contains the known Webhook token or signing-secret patterns.
