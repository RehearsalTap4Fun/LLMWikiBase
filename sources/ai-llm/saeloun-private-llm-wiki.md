> **原文存档** | 标题：Building a Private Karpathy-Style LLM Wiki With gbrain and gstack
> 来源：https://blog.saeloun.com/2026/04/28/private-karpathy-llm-wiki-gbrain-gstack-rails-ai-workflow/
> 获取日期：2026-06-12
> 说明：由网页 HTML 转换为 markdown,已去除站点导航与页脚营销内容,正文保持原文。

---

# Building a Private Karpathy-Style LLM Wiki With gbrain and gstack

Apr 28, 2026 

•  [Vipul A M](/authors/vipulnsward/)

Vipul A M

I am an active member of Ruby community. I have been consistently contributing to Ruby on Rails for a number of years and now am one of the top 30 contributors to Ruby on Rails. I also help as co-editor for the This week in Rails newsletter. Besides Ruby on Rails I have also contributed to many other notable open source projects including Sinatra, Devise and Rake. I am a seasoned speaker an have spoken at many conferences around the world including Gogaruco in San Francisco, RedDotRubyConf in Singapore, RubyConfIndia in Goa, India MadisonPlusRuby in Madison, Wisconsin, RubyConfBrazil in Suo Paulo, Brazil, and RubyConf Philippines in Manilla, Philippines. I am organizer of Deccan Ruby Conference and used to run RubyIndia Podcast. During my early days of open source as part of "Google summer of code" I contributed to the krypt-project project. Later I helped mentor in the JRuby and currently mentor in the Ruby on Rails organization for Google summer of code. When not working on Ruby, I am mostly working on Reactjs. I have authored the book Building Modern Web Applications with React.js which is published by PACKT. I have produced a number of screencasts on the topic of Learn React.js.

18 minute read 

I built a private local AI brain so assistants start with my defaults, not a blank prompt.

Generic assistants help, but they do not know how I review Rails, what I call risky, or why I choose boring over clever.

It has three parts:

  * a Karpathy-style LLM Wiki for durable knowledge
  * `gbrain` for my trained and distilled work signals
  * `gstack` for using that memory inside day-to-day coding workflows



The important part: the private corpus stays private. I distill repeated patterns from my own data signals. I am not retraining a public model on private work. The raw work history, private comments, internal repo names, client names, server paths, credentials, and customer details are not public blog material.

The useful public idea is the architecture.

## The Shape

_Local-first AI brain architecture: private signals are redacted, distilled into gbrain, compiled into llmwiki, and used by gstack with review gates before shipping._

Karpathy’s LLM Wiki pattern is simple: raw sources go in, the LLM maintains a structured Markdown wiki, and future agents read that wiki instead of rediscovering the same context every time.

My version adds a personal signal layer.
    
    
    private work signals
      -> redaction and source tagging
      -> gbrain knowledge + persona traits
      -> Karpathy-style LLM Wiki pages
      -> gstack skills and coding workflows
      -> better reviews, writing, and Rails decisions

I do not want a giant prompt. I want better defaults.

## What Goes Into gbrain

Only ingest signals that reveal repeated decisions.

For me, that means:

  * GitHub PRs, issues, and review comments
  * technical blog posts
  * sent emails
  * work chat messages
  * project tickets and notes
  * internal project learnings
  * code review discussions
  * deploy history
  * incident notes
  * calendar context
  * meeting notes and design docs



Each signal needs metadata:

  * tag the source type
  * record the timestamp
  * attach the project slug
  * store confidence
  * keep enough context for retrieval
  * keep private raw text local-only when needed
  * distill traits only after repeated evidence



The useful part is not just storage. It is the shape of each signal.
    
    
    source: github_review
    project: miru
    visibility: private
    recorded_at: 2026-04-28T09:00:00+05:30
    subject: "export endpoint review"
    summary: "Check tenant scope, authorization, signed URL lifetime, and audit event."
    evidence:
      - kind: pull_request
        id_hash: "sha256:..."
      - kind: review_comment
        id_hash: "sha256:..."
    privacy:
      raw_text: local_only
      public_summary: redacted

That small schema matters. Without source, time, and confidence, memory becomes vibes.

## Useful Signal Sources

The best sources are the ones that already show how work actually happens.

I care about these:

  * GitHub PRs: what I block on, what I let pass, how I phrase review feedback
  * GitHub issues: product intent, bug shape, edge cases, repeated customer pain
  * Gmail: founder communication style, hiring patterns, client-safe summaries
  * Slack: operational decisions, rollout notes, debugging threads, handoffs
  * Jira or Linear: status changes, scope cuts, estimates, blockers
  * calendar: what work repeatedly needs meetings, what can move async
  * docs: architecture decisions, product notes, onboarding material
  * deploys: shipped date, linked PRs, rollback signal, incident signal
  * incidents: timelines, impact, root cause, action items
  * blog posts: public technical voice, SEO topics, Rails explanation patterns



I would not ingest everything equally.

For public posts, full text is fine. For private mail, chat, and customer work, the safer default is metadata, hashes, short redacted summaries, and local-only raw text.

That gives the assistant enough signal to learn patterns without turning a private archive into a liability.

The raw data stays local. The trained layer stores distilled patterns.

Examples:

  * direct and pragmatic communication
  * concise Rails explanations
  * preference for minimal dependencies
  * strong verification discipline
  * risk-aware delivery
  * boring, maintainable code
  * practical Rails and API design judgment



This matters because one random comment should not become a rule. Repeated evidence becomes a trait.

## Redact First

Before anything becomes public, private information is censored.

I do not publish:

  * private company names
  * repo names
  * reviewer names
  * raw private comments
  * internal paths
  * hostnames
  * credentials
  * customer names
  * production architecture details



A small redaction step catches obvious leaks before a source enters a public-safe wiki.
    
    
    # script/redact_ai_source.rb
    PRIVATE_PATTERNS = {
      /gh(?:p|o|u|s|r)_[A-Za-z0-9_]+/ => "[REDACTED_GITHUB_TOKEN]",
      /sk-[A-Za-z0-9_-]+/ => "[REDACTED_API_KEY]",
      %r{/Users/[^/\s]+/[^)\s]+} => "[REDACTED_LOCAL_PATH]",
      %r{/home/[^/\s]+/[^)\s]+} => "[REDACTED_LOCAL_PATH]",
      %r{[A-Z]:[\\/]+Users[\\/]+[^\\/\s]+[\\/]+[^)\s]+}i => "[REDACTED_LOCAL_PATH]",
      %r{\\\\[^\\\s]+\\[^\\\s]+\\[^)\s]+} => "[REDACTED_LOCAL_PATH]",
      /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i => "[REDACTED_EMAIL]",
      # This intentionally over-matches. For redaction, false positives are safer
      # than leaking a real internal IP. Use IPAddr if strict validation matters.
      /\b\d{1,3}(\.\d{1,3}){3}\b/ => "[REDACTED_IP]"
    }
    
    input = File.read(ARGV.fetch(0))
    
    redacted = PRIVATE_PATTERNS.reduce(input) do |text, (pattern, replacement)|
      text.gsub(pattern, replacement)
    end
    
    puts redacted
    rescue IndexError
      warn "usage: ruby script/redact_ai_source.rb INPUT_FILE"
      exit 1
    rescue Errno::ENOENT
      warn "file not found: #{ARGV[0]}"
      exit 1

This is not the only guard. It is the first guard. Human review still matters.

## gbrain First

`gbrain` is the private memory layer.

I can inspect what it knows:
    
    
    bun run ~/.gbrain/src/cli.ts stats

On this machine, that reports a local knowledge base with thousands of entries and distilled traits. The point is not the number. The point is that the assistant can now answer from prior work signals instead of guessing.

Example queries:
    
    
    bun run ~/.gbrain/src/cli.ts query \
      "What patterns should I check before shipping a Rails migration?" \
      --synth true
    
    bun run ~/.gbrain/src/cli.ts query \
      "How do I usually explain Rails upgrade work?" \
      --synth true
    
    bun run ~/.gbrain/src/cli.ts persona voice --for blog

For private workflows, the model path is local LLM backed by default. The sensitive corpus stays on my machine. If I choose to use a cloud model for a public-safe summary, that is an explicit boundary, not the default for private raw data.

## Adding an LLM Wiki

The LLM Wiki is the compiled knowledge layer. It turns source files into interlinked Markdown pages that can be read by agents, searched by humans, and versioned like code.

I tested the local setup with `llm-wiki-compiler`, which provides a `llmwiki` CLI.
    
    
    mkdir -p ~/ai-brain/llmwiki
    cd ~/ai-brain/llmwiki
    
    npm exec --yes --package llm-wiki-compiler -- llmwiki schema init

Then I created a public-safe source file from the gbrain summary layer:
    
    
    ---
    title: Building a Private Local AI Brain
    source: public-safe-demo
    ---
    
    I built a local-first AI brain from my own work signals.
    
    Private data stays local. Public summaries must not expose private company names,
    repository names, reviewer names, raw comments, internal paths, hostnames,
    credentials, customer names, or production details.
    
    For Rails work, the brain helps an assistant check correctness, tenant boundaries,
    risky migrations, small changes, minimal dependencies, focused verification,
    and clear PR descriptions.

Then ingest it:
    
    
    npm exec --yes --package llm-wiki-compiler -- \
      llmwiki ingest my-local-ai-brain-public-source.md

The local test saved the file into `sources/`.

Then lint:
    
    
    npm exec --yes --package llm-wiki-compiler -- llmwiki lint

The local test returned:
    
    
    0 error(s), 0 warning(s), 0 info

For agent integration, `llmwiki` also starts an MCP server:
    
    
    npm exec --yes --package llm-wiki-compiler -- \
      llmwiki serve --root ~/ai-brain/llmwiki

That gives agents read/write tools for wiki status, source ingest, page reads, linting, and compilation.

The bridge from `gbrain` to `llmwiki` can stay boring.
    
    
    # script/gbrain_to_llmwiki_source.rb
    require "fileutils"
    require "open3"
    require "shellwords"
    require "time"
    
    question = ARGV.join(" ")
    abort "usage: ruby script/gbrain_to_llmwiki_source.rb QUESTION" if question.empty?
    
    slug = question.downcase.gsub(/[^a-z0-9]+/, "-").gsub(/\A-|-+\z/, "")
    path = File.expand_path("~/ai-brain/llmwiki/#{slug}.public.md")
    
    answer, error, status = Open3.capture3(
      "bun",
      "run",
      File.expand_path("~/.gbrain/src/cli.ts"),
      "query",
      question,
      "--synth",
      "true"
    )
    
    abort "gbrain query failed: #{error}" unless status.success?
    
    body = <<~MARKDOWN
      ---
      title: #{question}
      source: gbrain
      generated_at: #{Time.now.iso8601}
      visibility: public-safe-summary
      ---
    
      #{answer}
    MARKDOWN
    
    FileUtils.mkdir_p(File.dirname(path))
    File.write(path, body)
    puts path

Then:
    
    
    ruby script/gbrain_to_llmwiki_source.rb \
      "Rails review rules for exports, reports, and billing changes"
    
    ruby script/redact_ai_source.rb \
      ~/ai-brain/llmwiki/rails-review-rules-for-exports-reports-and-billing-changes.public.md \
      > /tmp/rails-review-rules.redacted.md
    
    npm exec --yes --package llm-wiki-compiler -- \
      llmwiki ingest /tmp/rails-review-rules.redacted.md
    npm exec --yes --package llm-wiki-compiler -- \
      llmwiki compile --review

The script is intentionally small. The policy lives in the review step, not in clever glue code.

## Importing gbrain Into llmwiki

I also set up a real local `llmwiki` project at `~/.gbrain/llmwiki`.

The export path is intentionally local-only:
    
    
    ~/.gbrain/bin/export-gbrain-to-llmwiki
    ~/.gbrain/bin/gbrain-llmwiki-refresh
    ~/.gbrain/bin/gbrain-llmwiki-query \
      "How should I review this Rails export change?"

The exporter reads the local `~/.gbrain/brain.db` SQLite database and writes chunked Markdown files into `~/.gbrain/llmwiki/sources/`.

For the current gbrain, that produced:
    
    
    persona_signals: 14955 (75 files)
    persona_traits: 3485 (18 files)
    knowledge: 2245 (12 files)
    projects: 4 (1 files)
    manifest: sources/gbrain-export-manifest.md

The files are marked `visibility: local-only`. They are not meant to be published. They are meant to make the private memory readable to agents through the same LLM Wiki path.

Then I lint the wiki:
    
    
    cd ~/.gbrain/llmwiki
    npm exec --yes --package llm-wiki-compiler -- llmwiki lint

That local lint run returned:
    
    
    0 error(s), 0 warning(s), 0 info

This gives me two retrieval paths:

  * `gbrain` for direct signal search and persona synthesis
  * `llmwiki` for compiled, durable, reviewable Markdown memory



The local setup is now useful alongside gbrain, not separate from it.

## What I Tested Locally

For this post, I tested the non-cloud path that does not require sending private data to any hosted model:
    
    
    node --version
    # v24.14.1
    
    bun run ~/.gbrain/src/cli.ts stats
    
    npm exec --yes --package llm-wiki-compiler -- llmwiki schema init
    npm exec --yes --package llm-wiki-compiler -- \
      llmwiki ingest my-local-ai-brain-public-source.md
    npm exec --yes --package llm-wiki-compiler -- llmwiki lint
    
    ~/.gbrain/bin/export-gbrain-to-llmwiki
    cd ~/.gbrain/llmwiki
    npm exec --yes --package llm-wiki-compiler -- llmwiki lint

The local `llmwiki lint` run returned 0 errors and 0 warnings. The full gbrain export produced 107 local-only source chunks plus a manifest, and the exported wiki lint also returned 0 errors and 0 warnings. I also started the `llmwiki serve` MCP process locally and stopped it after confirming startup. I verified a smaller Ollama-backed `compile --review` run with three seed sources: 3 compiled, 0 skipped, 0 deleted.

Full compile over the complete exported gbrain corpus is heavier. I run that locally with Ollama in review mode, then approve pages instead of letting the model silently rewrite memory. For private work, that provider should be a local LLM or an internal OpenAI-compatible endpoint.

## Local LLM Setup

For private corpora, I want local inference.

One setup uses Ollama through an OpenAI-compatible endpoint:
    
    
    ollama pull qwen2.5-coder:32b
    ollama pull nomic-embed-text
    
    export LLMWIKI_PROVIDER=ollama
    export LLMWIKI_MODEL=qwen2.5-coder:32b
    export LLMWIKI_EMBEDDING_MODEL=nomic-embed-text
    export OLLAMA_HOST=http://localhost:11434/v1
    
    npm exec --yes --package llm-wiki-compiler -- llmwiki compile --review
    npm exec --yes --package llm-wiki-compiler -- llmwiki review list

I prefer `--review` for private knowledge systems. The LLM can propose wiki pages, but I still approve what lands.

That keeps the wiki useful without letting a model silently rewrite memory.

## How gbrain and llmwiki Work Together

`gbrain` is good at finding signals. `llmwiki` is good at making durable pages.

So the loop looks like this:
    
    
    # 1. Ask gbrain for patterns from private history
    bun run ~/.gbrain/src/cli.ts query \
      "Rails code review patterns I care about" \
      --synth true > /tmp/rails-review-patterns.md
    
    # 2. Redact before moving anything into a shareable wiki
    ruby script/redact_ai_source.rb /tmp/rails-review-patterns.md \
      > ~/ai-brain/llmwiki/rails-review-patterns.public.md
    
    # 3. Ingest into the LLM Wiki
    cd ~/ai-brain/llmwiki
    npm exec --yes --package llm-wiki-compiler -- \
      llmwiki ingest rails-review-patterns.public.md
    
    # 4. Compile candidates for review
    npm exec --yes --package llm-wiki-compiler -- llmwiki compile --review
    npm exec --yes --package llm-wiki-compiler -- llmwiki review list

The public wiki gets distilled patterns. The private database keeps the raw signals.

That is the point.

## How gstack Uses It

`gstack` is where this becomes daily work.

The memory is not a document I sometimes open. It is context the coding agent can use while reviewing, shipping, debugging, and writing.

For a Rails PR, I want checks like:
    
    
    /review
      - Does this match the requested scope?
      - Are tenant/account boundaries preserved?
      - Is the migration safe to deploy?
      - Are tests focused on the changed behavior?
      - Did we avoid a dependency we do not need?
    
    /cso --diff
      - Any secret leakage?
      - Any unsafe auth or authorization path?
      - Any risky CI/CD or deploy change?
    
    /ship
      - Build and test before merge.
      - Update dates and filenames for blog posts.
      - Do not claim verification unless it actually ran.

Those are not generic agent preferences. They are trained from my work signals and repeatedly reinforced through gbrain.

The use cases compound:

  * reviewing Miru PRs for Rails correctness and product scope
  * checking migrations before they become deploy risk
  * turning review comments into reusable project learnings
  * writing Saeloun blog drafts in my voice
  * picking the next SEO post from the content queue
  * updating dates and filenames before blog merges
  * checking whether a PR has enough verification to ship
  * building short CTO briefings from private notes
  * preparing upgrade plans for Rails and dependencies
  * turning incident learnings into review checklists
  * keeping agents aligned with “small change, verified change”



This is where the setup becomes useful. Not because it writes more text. Because it remembers the review loop.

## Mandatory Review Gates

The assistant should adapt to my preferences. It should not bypass review.

For this workflow, these gates are mandatory before merge:

  * GitHub checks must pass
  * CodeRabbit review must be read and actionable comments fixed
  * GitHub Copilot review should be treated as another reviewer, not ignored as AI noise
  * local verification must match the claim in the PR
  * deploy or preview link must be checked when the change is user-facing



This is how the AI setup learns without becoming loose.

`gbrain` stores the repeated preference: small changes, clear scope, real verification, no fake test claims, no private data leaks.

`gstack` turns that into a merge policy:
    
    
    before merge
      -> run local checks
      -> push PR
      -> wait for GitHub checks
      -> read CodeRabbit and Copilot feedback
      -> fix actionable review
      -> verify preview or production
      -> merge only with artifacts

That is the adaptation I want. The agent does not just remember my writing style. It remembers how I ship.

## Miru Review and Shipping Example

Miru is a good example because it has normal product pressure: ship improvements, keep the Rails app clean, and avoid breaking core workflows.

The old way:
    
    
    Open the PR.
    Read the diff.
    Search old context manually.
    Remember the tenant rules.
    Find related issues.
    Check if tests ran.
    Write the same review comments again.

The gbrain and gstack way:
    
    
    bun run ~/.gbrain/src/cli.ts query \
      "Miru review checklist for invoices, reports, exports, and customer data" \
      --synth true
    
    gstack review --persona vipul --project miru --diff
    gstack cso --diff
    gstack ship

The assistant starts from my known checks:

  * Is this scoped to the current company or account?
  * Did the change preserve invoice and payment invariants?
  * Are background jobs idempotent?
  * Are reports and exports authorized?
  * Is customer data filtered from logs?
  * Are date and timezone boundaries explicit?
  * Does the API name match the product language?
  * Is the test focused enough to catch the regression?
  * Did the PR description say what changed and how it was verified?



That saves time without weakening review. The agent can draft the first pass, but the merge decision still needs evidence.

For example, a Miru billing or reporting change can create a wiki page like this:
    
    
    ---
    title: Miru Billing and Report Review Rules
    source: gbrain
    project: miru
    visibility: private
    ---
    
    Checks:
    
    - Scope records through the current company/account.
    - Keep money calculations integer-backed.
    - Make timezone boundaries explicit for reports.
    - Avoid N+1 queries in dashboard and export paths.
    - Keep export URLs short-lived.
    - Add regression tests for cross-account access.
    - Include the exact verification command in the PR.

Then future reviews can read that page before looking at the diff. That is the novel part: review memory becomes operational. It is not buried in old PR threads.

## More Workflow Examples

For a Rails migration:
    
    
    bun run ~/.gbrain/src/cli.ts query \
      "How should I review a Rails migration before deploy?" \
      --synth true

The answer should push the agent toward:

  * reversible migrations where possible
  * backfills outside the lock-heavy deploy path
  * indexes created safely
  * column defaults handled with production size in mind
  * deploy and rollback notes in the PR



For a blog merge:
    
    
    bun run ~/.gbrain/src/cli.ts query \
      "Blog publishing checklist for Saeloun Rails posts" \
      --synth true

The answer should remind the agent to:

  * update the post date to the actual publish date
  * rename the file to match the date
  * check title, summary, categories, keywords, and author
  * run Jekyll build
  * run internal link checks
  * verify production after deploy



For CTO transformation work:
    
    
    private signals
      -> source policy
      -> local memory
      -> team-specific wiki
      -> agent workflow
      -> review and delivery metrics

That is the work I find most interesting. Not “add AI”. Change how the engineering system learns.

## Rails Workflow Example

Say I am reviewing a Rails change that adds a new export endpoint.

The generic assistant might check syntax and tests.

The trained workflow asks better questions:
    
    
    class ExportsController < ApplicationController
      def show
        export = Current.account.exports.find(params[:id])
        authorize export
    
        return head :not_found unless export.file.attached?
    
        redirect_to rails_blob_url(export.file, disposition: "attachment"),
          allow_other_host: false
      end
    end

The checks I care about:

  * Is the record scoped through `Current.account`?
  * Is authorization explicit?
  * Does the redirect avoid an open redirect?
  * Is the file URL short-lived?
  * Are access logs filtered?
  * Is there an audit event?
  * Is the background job idempotent?
  * Is there a focused test for cross-account access?



That is the difference between memory and linting.

## Blog Workflow Example

The same setup helps writing.

Bad draft:
    
    
    In today's fast-paced world, developers need a robust AI-powered system
    to streamline their workflow.

Better draft:
    
    
    I wanted an AI assistant that starts from my defaults, not a blank prompt.

Then show the old way. Show the new way. Share the code. State the tradeoff. Link to the source.

That is closer to how I prefer Rails posts to read.

## What I Do Not Want

I do not want an assistant that becomes more confident just because it has more memory.

The rules stay enforceable:

  * No “verified” without an artifact: CI link, test output, lint result, or command output.
  * No private identifiers in public pages: run redaction and do human review.
  * No style preference dressed up as correctness: require evidence on policy pages.
  * No stale wiki pretending to be current: include source, timestamp, and review status.



Enforcement is simple.
    
    
    redact source
      -> distill with gbrain
      -> compile candidate LLM Wiki page
      -> human approve
      -> publish/use in gstack

No artifact, no claim.

Memory should improve defaults. It should not remove judgment.

## Why This Matters

Most AI coding setups still treat context as disposable. Paste a few files. Ask a question. Lose the reasoning. Repeat tomorrow.

A Karpathy-style LLM Wiki changes that. The assistant writes durable knowledge. `gbrain` trains and distills my private work signals. `gstack` applies those signals inside real Rails workflows.

That gives the agent better starting points:

  * how I review Rails code
  * how I think about migrations
  * how I judge dependencies
  * how I write technical posts
  * how I separate blockers from nits
  * how I verify before shipping
  * how Miru work should be reviewed
  * how private source signals should be handled



Not magic. Just memory, evidence, and better defaults.
