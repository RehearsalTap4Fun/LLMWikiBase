# Automation Git Commit Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add same-day K1 client, server, and configuration Git commits authored by the user to the concise work report, with Merge exclusion and semantic deduplication against conversation-derived items.

**Architecture:** Extend the existing heartbeat prompt rather than introducing a new script. Each run reads all local refs in the three repositories for the Shanghai calendar day, filters exact author email and non-Merge commits, summarizes evidence in business language, then deduplicates hashes, related commits, cross-repository work, and conversation-derived report items before the existing preview and robot-send stages.

**Tech Stack:** Codex heartbeat automation TOML, Git CLI read-only queries, Markdown automation memory.

## Global Constraints

- Repositories: `C:\Project\K1Client\k1_client`, `C:\Project\K1Game\game`, and `C:\Project\K1Dataconfig\dataconfig`.
- Author email must exactly equal `jiangzhenyu@nibirutech.com`.
- Time range is the current `Asia/Shanghai` calendar day from `00:00:00` through automation run time.
- Query all local refs and exclude Merge commits.
- Do not run `git fetch`, `pull`, checkout, or any Git write command.
- Deduplicate by full commit hash, then business topic across commits and repositories, then semantically against conversation-derived report items.
- Omit ambiguous commits instead of inventing a business result.
- Do not expose hashes, branches, paths, filenames, author email, fields, configuration IDs, or code terms in the report.
- Preserve the existing concise completed-work-only report and single Webhook send behavior.

---

### Task 1: Extend automation prompt and memory

**Files:**
- Modify: `C:\Users\jiangzhenyu\.codex\automations\automation-2\automation.toml`
- Modify: `C:\Users\jiangzhenyu\.codex\automations\automation-2\memory.md`

**Interfaces:**
- Consumes: local Git commit metadata and necessary read-only diff context from the three repositories, plus the existing 24-hour Codex/Claude conversation review.
- Produces: one deduplicated set of business-language completed-work items for the existing local preview and robot message.

- [x] **Step 1: Add exact Git collection rules to the heartbeat prompt**

Add all Global Constraints to `prompt`. Require candidate enumeration equivalent to `git log --all --no-merges` for the Shanghai-day interval, emit author email with `%ae`, and retain only records whose email exactly equals `jiangzhenyu@nibirutech.com`.

- [x] **Step 2: Add evidence and deduplication rules**

Require title, body, and changed-file overview for each candidate. Permit minimal read-only diff inspection only when needed. Merge related commits across repositories, then merge duplicates with conversation items while retaining the more complete supported outcome.

- [x] **Step 3: Record the policy in automation memory**

Append the three repository roots, exact author identity, Shanghai calendar-day window, Merge exclusion, read-only boundary, semantic deduplication sequence, and failure handling. Do not store any robot credential.

- [x] **Step 4: Run structural and behavior verification**

Parse `automation.toml`; confirm ID, schedule, status, and target task are unchanged. Check every new rule is present and credential scans remain clean. Run a read-only same-day sample across all three repositories: the client commit `调整委派按钮显示效果` must be selected, while the configuration commit authored by `xuefeng@nibirutech.com` must be excluded.
