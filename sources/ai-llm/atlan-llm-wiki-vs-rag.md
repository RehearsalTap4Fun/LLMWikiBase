> **原文存档** | 标题：LLM Wiki vs RAG Knowledge Base
> 来源：https://atlan.com/know/llm-wiki-vs-rag-knowledge-base/
> 获取日期：2026-06-12
> 说明：由网页 HTML 转换为 markdown,已去除站点导航与页脚营销内容,正文保持原文。

---

# LLM Wiki vs RAG Knowledge Base: The Karpathy Approach Explained

  1. [Home](https://atlan.com/)
  2. ›[Context Layer](https://atlan.com/context-layer/)
  3. ›LLM Wiki vs RAG Knowledge Base: The Karpathy Approach Explai...


  1. [Home](https://atlan.com/)
  2. ›[Context Layer](https://atlan.com/context-layer/)
  3. ›LLM Wiki vs RAG Knowledge Base: The Karpathy Approach Explai...



[Context Layer](https://atlan.com/context-layer/)

[Emily Winks](https://www.linkedin.com/in/emily-winks/)

Data Governance Expert

Data Governance Specialist

18+ years in information architecture, data governance, and enterprise data management

Masters, Library and Information Science, Queens College; Certificate in Archives, Records Management and Preservation; BA English, St. Joseph's College

Atlan Product EssentialsComputer Science Principles: Programming (LinkedIn)

[View LinkedIn Profile](https://www.linkedin.com/in/emily-winks/)

Emily WinksData Governance ExpertData Governance Specialist18+ years in information architecture, data governance, and enterprise data managementMasters, Library and Information Science, Queens College; Certificate in Archives, Records Management and Preservation; BA English, St. Joseph's CollegeAtlan Product EssentialsComputer Science Principles: Programming (LinkedIn)[LinkedIn Profile](https://www.linkedin.com/in/emily-winks/)

Updated:04/07/2026

|

Published:04/07/2026

21 min read

[See the Context Lakehouse](https://atlan.com/context-layer-demo/)[Get the Context Layer Ebook](https://atlan.com/resources/wtf-is-the-context-layer-ebook/)

## Key takeaways

  * LLM wikis win on token efficiency below 50,000-100,000 tokens; RAG wins at enterprise scale.
  * The real enterprise question is not wiki vs RAG: it is whether source data is trustworthy enough for either.
  * Karpathy's wiki is a personal data catalog. The enterprise already has one, governed and always-fresh.
  * Access control, freshness, and concurrency are governance problems, not retrieval architecture problems.



In this article

LLM wiki vs RAG knowledge base: what’s the difference? What is an LLM wiki? What is a RAG knowledge base? LLM wiki vs RAG knowledge base: head-to-head comparison How LLM wikis and RAG knowledge bases work together How Atlan approaches the enterprise knowledge base Real stories from real customers: governed context in enterprise AI The bottom line: scale decides the architecture, governance decides the outcome FAQs about LLM wiki vs RAG knowledge base

Reading progress 0%

## LLM wiki vs RAG knowledge base: what is the difference?

Copy summary

An LLM wiki loads a structured markdown index directly into context so the LLM reads relevant articles upfront without a vector database. A RAG knowledge base retrieves semantically relevant chunks from a vector store at query time. The key distinction is compile-time versus query-time knowledge assembly. LLM wikis win on token efficiency and simplicity at personal scale; RAG wins when knowledge exceeds context window limits and requires multi-user, dynamic access.

### Key differences at a glance

  * Architecture: LLM wiki loads a structured index into context; RAG retrieves chunks dynamically from a vector store at query time
  * Scale threshold: LLM wiki works reliably below 50,000-100,000 tokens; RAG handles millions of documents with no context ceiling
  * Infrastructure: LLM wiki requires zero infrastructure; RAG requires a vector database, embedding pipeline, and retrieval layer
  * Governance: neither approach solves enterprise data governance - that requires a separate layer such as a governed data catalog



Is your data LLM-ready?

[Assess Context Maturity](https://tools.atlan.com/tools/context-maturity-assessment/)

* * *

On April 3, 2026, Andrej Karpathy published a [GitHub Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) describing a personal knowledge system he calls an LLM wiki - a three-folder markdown setup that lets an LLM compile, maintain, and query knowledge without a vector database. The [VentureBeat headline](https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an) declared it “bypasses RAG.” The AI/ML community went from zero to hotly contested in days. Atlan implements the enterprise equivalent: Context Agents act as the organizational librarians Karpathy describes, continuously compiling metadata, query patterns, and institutional knowledge into a governed, LLM-readable context repository rather than requiring a documentation project no one finishes. Atlan’s Context Agents solve the enterprise version of this problem directly: they continuously crawl 75+ data systems, compile governed metadata, query patterns, and lineage into a structured LLM-readable wiki, and keep it current without a human documentation project.

The debate matters. But not quite in the way most coverage frames it. The LLM wiki and [retrieval-augmented generation](https://atlan.com/know/what-is-retrieval-augmented-generation/) are answers to different versions of the same question. Both address “how do I give an LLM access to knowledge?” One answers it for a solo researcher with 100 curated articles. The other answers it for an enterprise team with millions of records, dozens of systems, and regulatory access requirements. At personal scale, the wiki approach can [cut token usage by up to 95% compared to loading all source documents into context at once](https://www.mindstudio.ai/blog/llm-wiki-vs-rag-markdown-knowledge-base-comparison), an advantage that narrows against optimized RAG pipelines and disappears entirely beyond one context window. At enterprise scale, the index overflows context before you finish the import.

This guide explains how each approach works, when each wins, and why neither fully resolves the underlying enterprise knowledge problem, which is not a retrieval architecture question at all.

**Quick comparison at a glance:**

Dimension | LLM Wiki | RAG Knowledge Base  
---|---|---  
What it is | Curated markdown folder system compiled into LLM context | Embedding + retrieval pipeline over a vector-indexed corpus  
How it works | LLM reads a structured index and pulls pre-summarized articles | LLM queries a vector store and retrieves semantically relevant chunks  
Who owns it | Individual researcher or small team | Data/ML engineering team  
Key strength | Zero infrastructure, high token efficiency at small scale | Scales to millions of documents; handles dynamic, multi-domain data  
Best for | Personal knowledge bases, solo researchers, stable corpora up to ~100 articles | Enterprise knowledge systems, frequently updated content, multi-team access  
Questions it answers | “What do I know about X?” (curated, stable knowledge) | “What’s relevant to X right now?” (real-time, large-scale retrieval)  
Infrastructure cost | Near-zero - no vector DB, no embedding pipeline | Medium-high - vector database, embedding model, retrieval layer  
Governance model | None by default | Partial - depends on upstream data quality and access controls  
  
Below, we explore: the core architectural difference, what an LLM wiki is, what a RAG knowledge base is, how they compare head-to-head, how they can work together, and how Atlan approaches the enterprise knowledge layer.

* * *

* * *

## LLM wiki vs RAG knowledge base: what’s the difference?

Permalink to “LLM wiki vs RAG knowledge base: what’s the difference?” #

The architectural distinction is simpler than the debate suggests. An LLM wiki loads a structured index directly into context - the LLM reads everything relevant upfront. A RAG knowledge base retrieves chunks dynamically from a vector store at query time. The distinction is compile-time versus query-time knowledge assembly, not intelligence.

Karpathy’s [original Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) describes a three-folder system: `raw/` for source material, `wiki/` for LLM-compiled summary articles, and an `index.md` that maps all articles and fits in a single context window. The LLM reads `index.md` first, then pulls specific articles as needed - no embedding step, no vector search, no retrieval pipeline. On [X on April 3, 2026](https://x.com/karpathy/status/2039805659525644595), Karpathy noted that “a large fraction of my recent token throughput is going less into manipulating code, and more into manipulating knowledge.” That is a practitioner signal that knowledge management is becoming the dominant AI workflow cost center.

* * *

* * *

The VentureBeat coverage framed the approach as one that “bypasses RAG,” which accelerated an either/or framing across communities. But the confusion persists because both approaches answer the same surface-level question with different underlying assumptions about scale.

The LLM wiki assumes knowledge is bounded and stable - a personal research corpus of ~100 curated articles that fits comfortably in context. RAG assumes knowledge is large, dynamic, and multi-domain - too sprawling for any single index file. The [50,000-100,000 token threshold](https://www.mindstudio.ai/blog/llm-wiki-vs-rag-markdown-knowledge-base-comparison) is where the wiki approach stops working reliably: beyond that, the index cannot fit in context, and [LLM context window limitations](https://atlan.com/know/llm-context-window-limitations/) force a retrieval layer regardless of the storage format. Scale is not a minor caveat. It is the entire frame.

* * *

## What is an LLM wiki?

Permalink to “What is an LLM wiki?” #

An LLM wiki is a structured, markdown-based personal knowledge base designed to be loaded directly into LLM context. Karpathy introduced the approach in April 2026 via [GitHub Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). The key insight is using the LLM not just to query knowledge but to compile and maintain it.

The three-folder architecture works as follows. `raw/` stores unstructured source material - PDFs, notes, web clips, raw research. `wiki/` holds LLM-compiled summary articles, one per concept or topic. `index.md` is a master map of all articles, sized to fit within the model’s context window. At query time, the LLM reads `index.md` first, identifies which articles are relevant, and loads only those - no embedding, no vector search.

At roughly 100 articles and ~400,000 words of source material, the index fits easily in a modern context window. The [MindStudio analysis](https://www.mindstudio.ai/blog/llm-wiki-vs-rag-markdown-knowledge-base-comparison) found that this approach can reduce token consumption by up to 95% compared to naive full-document loading, which is the primary practical appeal for researchers watching API costs. LLM health check prompts add a self-healing mechanism: periodic passes scan wiki articles for outdated, incomplete, or contradictory entries and flag them for update.

The [DAIR.AI Academy](https://academy.dair.ai/blog/llm-knowledge-bases-karpathy) articulates the LLM’s role as “compiler”: not just retrieving text but synthesizing raw knowledge into structured articles. This makes the wiki actively maintained rather than static, which is a meaningful distinction from a traditional documentation site. Backlinks between articles function as lightweight knowledge graph edges, adding navigability without a graph database.

### Core components of an LLM wiki

Permalink to “Core components of an LLM wiki” #  


  * **`raw/`** : Unstructured source material - PDFs, notes, web clips, raw research inputs
  * **`wiki/`** : LLM-compiled summary articles, one per concept or topic
  * **`index.md`** : Master map of all articles; fits in context window; the LLM’s entry point
  * **Health check prompts** : Periodic LLM passes that identify stale, incomplete, or contradictory entries
  * **Backlinks** : Cross-references between wiki articles that function like lightweight knowledge graph edges



* * *

## What is a RAG knowledge base?

Permalink to “What is a RAG knowledge base?” #

A [RAG knowledge base](https://atlan.com/know/what-is-an-llm-knowledge-base/) combines a vector-indexed document store with a retrieval layer that surfaces semantically relevant chunks at query time. The LLM never loads the full corpus - it grounds its response in retrieved context only. This makes RAG the architecture of choice when knowledge is too large, too dynamic, or too multi-domain for a single index file.

[Retrieval-augmented generation](https://atlan.com/know/what-is-retrieval-augmented-generation/) works in three stages. Documents are chunked into retrievable segments, each chunk is converted into a vector embedding by an embedding model, and those embeddings are indexed in a [vector database](https://atlan.com/know/what-is-a-vector-database/) such as Pinecone, Weaviate, or pgvector. At query time, the system converts the user’s query into a vector, retrieves the top-K most semantically similar chunks, and passes them as context to the LLM. The LLM synthesizes a response from retrieved evidence rather than from a preloaded index.

Enterprise adoption reflects where the hard problems live. The majority of RAG deployments occur in enterprise environments where regulatory compliance and data sensitivity are paramount - meaning governance is not an edge case, it is the default operating condition. Enterprise data is not 100 curated articles. It is millions of records, documents, and assets distributed across dozens of systems, updated continuously, and subject to access controls that a markdown folder cannot enforce.

RAG’s limitations are real and worth stating plainly. Output quality depends entirely on upstream data quality. If the source documents are stale, contradictory, or ungoverned, RAG retrieves and amplifies those problems. Access control, freshness, and lineage are not built into RAG pipelines by default. Chunking and embedding strategies significantly affect retrieval quality, adding meaningful engineering overhead to every deployment.

### Core components of a RAG knowledge base

Permalink to “Core components of a RAG knowledge base” #  


  * **Document store** : Raw source content - databases, PDFs, wikis, CMS, data warehouses
  * **Chunking layer** : Splitting documents into retrievable segments; strategy directly affects retrieval quality
  * **Embedding model** : Converts text chunks into vector representations for semantic indexing
  * **Vector database** : Stores and indexes embeddings for fast similarity search (Pinecone, Weaviate, pgvector)
  * **Retrieval layer** : At query time, fetches the top-K most semantically relevant chunks
  * **LLM grounding** : The LLM synthesizes a response using retrieved chunks as context



* * *

* * *

## LLM wiki vs RAG knowledge base: head-to-head comparison

Permalink to “LLM wiki vs RAG knowledge base: head-to-head comparison” #

The sharpest differences appear at three axes: scale, infrastructure, and governance. LLM wikis win on simplicity and token efficiency below the [50,000-100,000 token threshold](https://www.mindstudio.ai/blog/llm-wiki-vs-rag-markdown-knowledge-base-comparison). RAG wins on scale, dynamism, and multi-user access. Neither wins on enterprise data governance - that requires a separate layer entirely.

Dimension | LLM Wiki | RAG Knowledge Base  
---|---|---  
Knowledge scale | Up to ~100-200 articles (index must fit in context) | Millions of documents - no context ceiling  
Infrastructure required | Zero - markdown files, no vector DB | Vector database, embedding pipeline, retrieval layer  
Token efficiency | Up to 95% reduction vs. naive loading (small scale) | Higher per-query cost; scales more efficiently at large N  
Freshness mechanism | Manual + LLM health checks; no automatic propagation | Pipeline-triggered re-indexing; can be near-real-time  
Access control | None - file system permissions only | Partial - depends on upstream system and retrieval layer design  
Multi-user support | Race conditions, write conflicts without transactional DB | Designed for concurrent read access; write governance varies  
Setup time | Hours - markdown files and LLM prompts | Days to weeks - embedding pipeline, vector DB, chunking strategy  
Best knowledge type | Stable, curated, personal-scale research | Dynamic, large-scale, multi-domain enterprise content  
Failure mode | Context overflow, stale content at scale, no access control | Poor chunking, embedding drift, ungoverned upstream data  
Governance model | None built in | Partial - depends on implementation choices  
LLM Wiki raw/ Source material wiki/ Compiled articles index.md Master map - fits in context LLM context window Reads index - no retrieval RAG Knowledge Base Document store Any format, any size Chunking + embed Vectors indexed Vector database Pinecone, Weaviate, pgvector LLM + retrieved chunks Top-K relevant at query time

The [Epsilla analysis](https://www.epsilla.com/blogs/karpathy-agentic-wiki-beyond-rag-enterprise-memory) captures the enterprise concurrency problem precisely: multiple simultaneous agents updating a markdown wiki create race conditions, write conflicts, and potential for data corruption without transactional database support. Karpathy himself scoped the approach explicitly to individual researchers - the “bypasses RAG” framing misrepresents his stated intent.

**A concrete scenario:** A data engineer at a mid-size fintech has ~80 internal research notes on regulatory requirements. For personal reference, the LLM wiki works - the index fits in context, and their LLM assistant answers accurately without a vector database. When the same company needs a compliance assistant for 200 analysts querying across 50,000 documents in five systems with role-based access, the LLM wiki breaks down immediately: index overflow, no access control layer, and write conflicts across simultaneous users. RAG with a governed retrieval layer is the only workable path. Neither approach, however, solves the upstream problem: if the source documents are stale or uncertified, both fail.

* * *

## How LLM wikis and RAG knowledge bases work together

Permalink to “How LLM wikis and RAG knowledge bases work together” #

LLM wikis and RAG pipelines are not mutually exclusive. In hybrid architectures, the wiki provides curated, high-confidence context that anchors RAG retrieval - reducing noise, improving grounding, and making LLM responses more consistent across queries.

### Wiki as curated context layer over RAG

Permalink to “Wiki as curated context layer over RAG” #  


The wiki’s structured, summarized articles serve as high-quality “seed” context passed to the LLM before RAG retrieval begins. Rather than sending the LLM into a raw corpus cold, the wiki gives it a reliable interpretive frame: key concepts, stable definitions, known relationships. RAG then retrieves supporting evidence for specific queries. Combined outcome: higher response consistency and fewer hallucinations than RAG alone, because the LLM is grounding against curated knowledge before it reaches into dynamic retrieval.

### Wiki for knowledge curation, RAG for knowledge retrieval

Permalink to “Wiki for knowledge curation, RAG for knowledge retrieval” #  


A two-tier architecture lets each layer do what it does best. The LLM wiki handles the “what we know for sure” layer - certified concepts, stable definitions, internal frameworks that change slowly. RAG handles the “what’s in the corpus right now” layer - real-time document search, evidence retrieval, broad coverage across large and dynamic datasets. This separation avoids contaminating the curated knowledge layer with the noise and variance of broad retrieval.

### When the wiki layer is the governed metadata layer

Permalink to “When the wiki layer is the governed metadata layer” #  


The most powerful hybrid arises when the “wiki” is not a markdown folder but a governed [data catalog](https://atlan.com/know/data-catalog-for-ai/) \- curated, certified, access-controlled metadata about every data asset in the enterprise. The catalog answers “what do we know about our data”; RAG retrieves from the data itself. An LLM agent that knows the shape, certification status, and lineage of a dataset before it queries it is a fundamentally more reliable agent than one that retrieves blindly.

When to start with each approach:

  * **Start with LLM wiki** : personal research workflows, stable knowledge corpora under 150 pages, solo practitioners, zero-infrastructure constraints
  * **Start with RAG** : enterprise scale, dynamic content, multi-user access, regulatory environments, corpora exceeding context window limits
  * **Invest in both simultaneously** : when building enterprise AI agents that need curated knowledge anchors and broad document retrieval - and when source data is already governed



* * *

## How Atlan approaches the enterprise knowledge base

Permalink to “How Atlan approaches the enterprise knowledge base” #

When executives read the Karpathy post and ask their data teams to “build an LLM wiki for the company,” the data team faces an immediate problem: enterprise data is not a tidy collection of markdown articles. It is distributed across dozens of systems, maintained by hundreds of people, ungoverned by default, and subject to access controls that a markdown folder cannot enforce.

The [Epsilla analysis](https://www.epsilla.com/blogs/karpathy-agentic-wiki-beyond-rag-enterprise-memory) is precise on this point: “The jump from personal research wiki to enterprise operations is where it gets brutal. Thousands of employees, millions of records, tribal knowledge that contradicts itself across teams.” That is a data governance problem, not a retrieval architecture problem. Building a shadow wiki or a raw RAG pipeline on top of ungoverned data does not solve it. It reorganizes the problem into a new format.

Atlan’s data catalog is structurally the enterprise version of what Karpathy built for himself. It has curated asset summaries (documentation), cross-references (lineage), concept definitions (business glossary), certification status (quality scores), and a freshness mechanism via [active metadata propagation](https://atlan.com/active-metadata-management/) \- not manual health checks but automatic propagation as pipelines run. Where the markdown folder has no access control, the catalog enforces policy-level RBAC: a FinanceAgent cannot reach HR data. Where the wiki index breaks at scale, the catalog’s structured query layer handles millions of assets without context overflow.

The practical outcome: enterprise teams using Atlan as their AI knowledge substrate connect a governed, certified, always-fresh metadata layer to their LLMs via MCP and API - rather than building a shadow knowledge layer on top of ungoverned source data. The [enterprise LLM knowledge base](https://atlan.com/know/enterprise-llm-knowledge-base/) the organization needs already exists in most cases. The connection is the missing piece, not the construction. For the broader comparison between these approaches, see [LLM knowledge base vs RAG](https://atlan.com/know/llm-knowledge-base-vs-rag/).

* * *

## Real stories from real customers: governed context in enterprise AI

Permalink to “Real stories from real customers: governed context in enterprise AI” #

"We're excited to build the future of AI governance with Atlan. All of the work that we did to get to a shared language at Workday can be leveraged by AI via Atlan's MCP server...as part of Atlan's AI Labs, we're co-building the semantic layer that AI needs with new constructs, like context products."

Joe DosSantos, VP of Enterprise Data & Analytics, Workday

[Watch Now](https://atlan.com/regovern-watch-center/workday-context-as-culture/)

"Atlan is much more than a catalog of catalogs. It's more of a context operating system...Atlan enabled us to easily activate metadata for everything from discovery in the marketplace to AI governance to data quality to an MCP server delivering context to AI models."

Sridher Arumugham, Chief Data & Analytics Officer, DigiKey

[Watch Now](https://atlan.com/regovern-watch-center/digikey-context-readiness/)

Both Workday and DigiKey illustrate the same pattern: the path to reliable enterprise AI is not a better retrieval architecture - it is a governed, certified, always-fresh [context layer](/context-layer/) that any LLM or agent can access through a standard interface. The data catalog is that layer. The MCP server is the connection.

* * *

## The bottom line: scale decides the architecture, governance decides the outcome

Permalink to “The bottom line: scale decides the architecture, governance decides the outcome” #

The LLM wiki vs RAG debate is a question of scale, not superiority. Karpathy’s approach is genuinely elegant for what it is: a personal knowledge system for a solo researcher with a stable, bounded corpus. At that scale, it outperforms RAG on simplicity, token efficiency, and zero infrastructure. At enterprise scale, it breaks on access control, concurrency, and index overflow - not because the idea is wrong, but because the problem is different.

The more important insight is that the enterprise already has a governed version of what Karpathy built. The data catalog provides curated summaries, lineage, certification, access controls, and freshness - the same architecture, at enterprise scale, with governance built in. As agentic AI systems multiply across enterprise data estates, the upstream data quality and governance problem grows more acute. Organizations that solve it at the substrate level will outperform those treating it as a retrieval architecture question.

* * *

## FAQs about LLM wiki vs RAG knowledge base

Permalink to “FAQs about LLM wiki vs RAG knowledge base” #

### 1\. What is the Karpathy LLM wiki approach?

Permalink to “1. What is the Karpathy LLM wiki approach?” #  


Andrej Karpathy proposed a personal knowledge base using three markdown folders: `raw/` for source material, `wiki/` for LLM-compiled summary articles, and `index.md` as a master map sized to fit within the model’s context window. An LLM compiles raw notes into structured wiki articles and maintains the index. At query time, the LLM reads the index and pulls relevant articles without a vector database or retrieval pipeline. Karpathy explicitly scoped the approach to individual researchers with stable, bounded knowledge corpora.

### 2\. Is an LLM wiki better than RAG for knowledge bases?

Permalink to “2. Is an LLM wiki better than RAG for knowledge bases?” #  


Neither is universally better. LLM wikis outperform RAG on token efficiency and simplicity for small, stable, personal-scale knowledge bases below roughly 100-200 articles and 50,000-100,000 tokens. RAG outperforms on large, dynamic, multi-user corpora where the knowledge base exceeds context window limits. The right choice depends on the scale, dynamism, and governance requirements of the knowledge - not on a universal ranking of one architecture over the other.

### 3\. What are the limitations of the Karpathy LLM wiki approach?

Permalink to “3. What are the limitations of the Karpathy LLM wiki approach?” #  


Three core limitations constrain the approach at enterprise scale. First, scale: the index must fit in context, capping practical knowledge at 50,000-100,000 tokens. Second, access control: markdown folders have no native role-based permissions, meaning any agent with file access can read any content. Third, concurrency: multiple simultaneous users or agents create write conflicts without transactional database support. Karpathy explicitly scoped the approach to individual researchers - the limitations are not bugs, they are consequences of the design assumptions.

### 4\. Can the Karpathy LLM wiki approach work for enterprise teams?

Permalink to “4. Can the Karpathy LLM wiki approach work for enterprise teams?” #  


Karpathy scoped this approach explicitly to individual researchers - it was not designed as an enterprise architecture. For teams with enterprise-scale requirements - millions of assets, concurrent access, regulatory permissions, and continuous data change - the markdown folder architecture needs significant additions: a transactional write layer, role-based access control, automated freshness propagation, and scale beyond a single context window. Those additions describe a RAG pipeline or a governed data catalog. The approach is not wrong; it is solving a different problem than enterprise knowledge management.

### 5\. How does an LLM wiki handle data freshness?

Permalink to “5. How does an LLM wiki handle data freshness?” #  


Through periodic LLM health check prompts that scan wiki articles for outdated, incomplete, or contradictory entries and flag them for update. This works when knowledge is stable and the curator actively runs health checks on a regular schedule. It does not propagate changes automatically from upstream sources - making it unsuitable for data that changes without human intervention. Enterprise data catalogs solve this differently: active metadata propagation pushes changes automatically as pipelines run, without requiring a manual trigger.

### 6\. When should you use a vector database vs. an LLM wiki?

Permalink to “6. When should you use a vector database vs. an LLM wiki?” #  


Use a vector database when your knowledge corpus exceeds roughly 50,000-100,000 tokens, when content updates frequently, or when multiple users need concurrent access. Use an LLM wiki when your corpus is small and stable, you are working alone, and token efficiency is the primary constraint. Most enterprise use cases require a vector database. Personal research workflows with bounded, stable corpora are the strongest fit for the wiki approach.

### 7\. Is a data catalog the same as an enterprise LLM knowledge base?

Permalink to “7. Is a data catalog the same as an enterprise LLM knowledge base?” #  


Not by default, but a governed data catalog is structurally the closest enterprise equivalent. A data catalog provides curated asset summaries, lineage, business glossary definitions, certification status, and access controls - the same functions an LLM wiki provides at personal scale, with enterprise governance built in. Connecting a catalog to an LLM stack via MCP or API produces a governed knowledge layer without building a shadow wiki from scratch on top of ungoverned data.

### 8\. What is the difference between a knowledge base and RAG?

Permalink to “8. What is the difference between a knowledge base and RAG?” #  


A knowledge base is the organized repository of information an LLM draws from. RAG is one retrieval architecture for connecting an LLM to that repository dynamically at query time. RAG is not the only method: loading structured indexes directly into context (the LLM wiki approach) is another, and using structured query APIs over governed metadata stores is a third. The knowledge base is the substrate; RAG is one connection method.


## Sources

  1. [1]

[llm-wiki GitHub Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — Andrej Karpathy, GitHub, 2026

  2. [2]

[LLM Knowledge Bases thread](https://x.com/karpathy/status/2039805659525644595) — Andrej Karpathy, X, 2026

  3. [3]

[Karpathy shares LLM Knowledge Base architecture that bypasses RAG](https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an) — VentureBeat Staff, VentureBeat, 2026

  4. [4]

[LLM Wiki vs RAG - Markdown Knowledge Base Comparison](https://www.mindstudio.ai/blog/llm-wiki-vs-rag-markdown-knowledge-base-comparison) — MindStudio, MindStudio Blog, 2026

  5. [5]

[LLM Knowledge Bases: Karpathy](https://academy.dair.ai/blog/llm-knowledge-bases-karpathy) — DAIR.AI Academy, DAIR.AI Academy, 2026

  6. [6]

[Karpathy Agentic Wiki: Beyond RAG Enterprise Memory](https://www.epsilla.com/blogs/karpathy-agentic-wiki-beyond-rag-enterprise-memory) — Epsilla, Epsilla Blog, 2026

  7. [7]

[Andrej Karpathy Moves Beyond RAG, Builds LLM-Powered Personal Knowledge Bases](https://analyticsindiamag.com/ai-news/andrej-karpathy-moves-beyond-rag-builds-llm-powered-personal-knowledge-bases) — Analytics India Mag Staff, Analytics India Mag, 2026
