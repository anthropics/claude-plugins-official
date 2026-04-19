---
name: rag-architect
description: >
  Designs production-grade RAG pipelines with chunking optimization, retrieval
  evaluation, and pipeline architecture. Use when building a RAG system,
  selecting a chunking strategy, choosing a vector database, optimizing
  retrieval quality, designing embedding pipelines, or evaluating RAG
  performance with RAGAS metrics.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: engineering
  domain: ai-ml
  tier: POWERFUL
  updated: 2026-03-31
---
# RAG Architect

The agent designs, implements, and optimizes production-grade Retrieval-Augmented Generation pipelines, covering the full lifecycle from document chunking through evaluation.

## Workflow

1. **Analyse corpus** -- Profile the document collection: count, average length, format mix (PDF, HTML, Markdown), language(s), and domain. Validate that sample documents are accessible before proceeding.
2. **Select chunking strategy** -- Choose from the Chunking Strategy Matrix based on corpus characteristics. Set chunk size, overlap, and boundary rules. Run a test split on 100 sample documents.
3. **Choose embedding model** -- Select an embedding model from the Embedding Model table based on domain, latency budget, and cost constraints. Verify dimension compatibility with the target vector database.
4. **Select vector database** -- Pick a vector store from the Vector Database Comparison based on scale, query patterns, and operational requirements.
5. **Design retrieval pipeline** -- Configure retrieval strategy (dense, sparse, or hybrid). Add reranking if precision requirements exceed 0.85. Set the top-K parameter and similarity threshold.
6. **Implement query transformations** -- If query-document style mismatch exists, enable HyDE. If queries are ambiguous, enable multi-query generation. Validate each transformation improves retrieval metrics on a held-out set.
7. **Configure guardrails** -- Enable PII detection, toxicity filtering, hallucination detection, and source attribution. Set confidence score thresholds.
8. **Evaluate end-to-end** -- Run the RAGAS evaluation framework. Verify faithfulness > 0.90, context relevance > 0.80, answer relevance > 0.85. Iterate on weak components.

## Chunking Strategy Matrix

| Strategy | Best For | Chunk Size | Overlap | Pros | Cons |
|----------|----------|-----------|---------|------|------|
| Fixed-size (token) | Uniform docs, consistent sizing | 512-2048 tokens | 10-20% | Predictable, simple | Breaks semantic units |
| Sentence-based | Narrative text, articles | 3-8 sentences | 1 sentence | Preserves language boundaries | Variable sizes |
| Paragraph-based | Structured docs, technical manuals | 1-3 paragraphs | 0-1 paragraph | Preserves topic coherence | Highly variable sizes |
| Semantic | Long-form, research papers | Dynamic | Topic-shift detection | Best coherence | Computationally expensive |
| Recursive | Mixed content types | Dynamic, multi-level | Per-level | Optimal utilization | Complex implementation |
| Document-aware | Multi-format collections | Format-specific | Section-level | Preserves metadata | Format-specific code required |

## Embedding Model Comparison

| Model | Dimensions | Speed | Quality | Cost | Best For |
|-------|-----------|-------|---------|------|----------|
| all-MiniLM-L6-v2 | 384 | ~14K tok/s | Good | Free (local) | Prototyping, low-latency |
| all-mpnet-base-v2 | 768 | ~2.8K tok/s | Better | Free (local) | Balanced production use |
| text-embedding-3-small | 1536 | API | High | $0.02/1M tokens | Cost-effective production |
| text-embedding-3-large | 3072 | API | Highest | $0.13/1M tokens | Maximum quality |
| Domain fine-tuned | Varies | Varies | Domain-best | Training cost | Specialized domains (legal, medical) |

## Vector Database Comparison

| Database | Type | Scaling | Key Feature | Best For |
|----------|------|---------|-------------|----------|
| Pinecone | Managed | Auto-scaling | Metadata filtering, hybrid search | Production, managed preference |
| Weaviate | Open source | Horizontal | GraphQL API, multi-modal | Complex data types |
| Qdrant | Open source | Distributed | High perf, low memory (Rust) | Performance-critical |
| Chroma | Embedded | Limited | Simple API, SQLite-backed | Prototyping, small-scale |
| pgvector | PostgreSQL ext | PostgreSQL scaling | ACID, SQL joins | Existing PostgreSQL infra |

## Retrieval Strategies

| Strategy | When to Use | Implementation |
|----------|-------------|---------------|
| Dense (vector similarity) | Default for semantic search | Cosine similarity with k-NN/ANN |
| Sparse (BM25/TF-IDF) | Exact keyword matching needed | Elasticsearch or inverted index |
| Hybrid (dense + sparse) | Best of both needed | Reciprocal Rank Fusion (RRF) with tuned weights |
| + Reranking | Precision must exceed 0.85 | Cross-encoder reranker after initial retrieval |

## Query Transformation Techniques

| Technique | When to Use | How It Works |
|-----------|-------------|-------------|
| HyDE | Query/document style mismatch | LLM generates hypothetical answer; embed that instead of query |
| Multi-query | Ambiguous queries | Generate 3-5 query variations; retrieve for each; deduplicate |
| Step-back | Specific questions needing general context | Transform to broader query; retrieve general + specific |

## Context Window Optimization

- **Relevance ordering**: Most relevant chunks first in the context window
- **Diversity**: Deduplicate semantically similar chunks
- **Token budget**: Fit within model context limit; reserve tokens for system prompt and answer
- **Hierarchical inclusion**: Include section summary before detailed chunks when available
- **Compression**: Summarize low-relevance chunks; extract key facts from verbose passages

## Evaluation Metrics (RAGAS Framework)

| Metric | Target | What It Measures |
|--------|--------|-----------------|
| Faithfulness | > 0.90 | Answers grounded in retrieved context |
| Context Relevance | > 0.80 | Retrieved chunks relevant to query |
| Answer Relevance | > 0.85 | Answer addresses the original question |
| Precision@K | > 0.70 | % of top-K results that are relevant |
| Recall@K | > 0.80 | % of relevant docs found in top-K |
| MRR | > 0.75 | Reciprocal rank of first relevant result |

## Guardrails

- **PII detection**: Scan retrieved chunks and generated responses for PII; redact or block
- **Hallucination detection**: Compare generated claims against source documents via NLI
- **Source attribution**: Every factual claim must cite a retrieved chunk
- **Confidence scoring**: Return confidence level; if below threshold, return "I don't have enough information"
- **Injection prevention**: Sanitize user queries; reject prompt injection attempts

## Example: Internal Knowledge Base RAG Pipeline

```yaml
corpus:
  documents: 12,000 Confluence pages + 3,000 PDFs
  avg_length: 2,400 tokens
  languages: [English]
  domain: internal engineering docs

pipeline:
  chunking:
    strategy: recursive
    max_tokens: 512
    overlap: 50 tokens
    boundary: paragraph
  embedding:
    model: text-embedding-3-small
    dimensions: 1536
    batch_size: 100
  vector_db:
    engine: pgvector
    index: HNSW (ef_construction=128, m=16)
    reason: "Existing PostgreSQL infra; ACID compliance for audit"
  retrieval:
    strategy: hybrid
    dense_weight: 0.7
    sparse_weight: 0.3
    top_k: 10
    reranker: cross-encoder/ms-marco-MiniLM-L-12-v2
    final_k: 5

evaluation_results:
  faithfulness: 0.93
  context_relevance: 0.84
  answer_relevance: 0.88
  precision_at_5: 0.76
  recall_at_10: 0.85
```

## Production Patterns

- **Caching**: Query-level (exact match), semantic (similar queries via embedding distance < 0.05), chunk-level (embedding cache)
- **Streaming**: Stream generation tokens while retrieval completes; show sources after generation
- **Fallbacks**: If primary vector DB is unavailable, serve from read-replica; if retrieval returns no results above threshold, say so explicitly
- **Document refresh**: Incremental re-embedding on change detection; full re-index weekly
- **Cost control**: Batch embeddings, cache aggressively, route simple queries to BM25 only

## Common Pitfalls

| Problem | Solution |
|---------|----------|
| Chunks break mid-sentence | Use boundary-aware chunking with sentence/paragraph overlap |
| Low retrieval precision | Add cross-encoder reranker; tune similarity threshold |
| High latency (> 2s) | Cache embeddings; use faster model; reduce top-K |
| Inconsistent quality | Implement RAGAS evaluation in CI; add quality scoring |
| Scalability bottleneck | Shard vector DB; implement auto-scaling; add caching layer |

## Scripts

### Chunking Optimizer
Analyses corpus and recommends optimal chunking strategy with parameters.

### Retrieval Evaluator
Runs evaluation suite (precision, recall, MRR, NDCG) against a test query set.

### Pipeline Benchmarker
Measures end-to-end latency, throughput, and cost per query across configurations.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Chunks contain incomplete sentences or broken code blocks | Fixed-size chunking ignoring semantic boundaries | Switch to sentence-based or semantic (heading-aware) chunking; enable boundary detection in `chunking_optimizer.py` |
| Retrieved context is relevant but answer is wrong | LLM hallucinating beyond retrieved chunks | Enable faithfulness evaluation via RAGAS; add source attribution guardrails; lower confidence threshold to surface "I don't know" responses |
| Precision@K below 0.50 despite relevant documents existing | Embedding model does not capture domain vocabulary | Fine-tune embedding model on domain data or switch to a domain-specific model; add cross-encoder reranking stage |
| Query latency exceeds 2 seconds | Large top-K, no caching, or unoptimized HNSW index | Reduce top-K, enable query-level and semantic caching, tune HNSW parameters (ef_search, m) |
| Recall drops after adding new documents | Stale embeddings or index fragmentation after incremental inserts | Trigger full re-index; verify new documents pass chunking pipeline; check embedding model version consistency |
| Hybrid retrieval returns duplicate chunks | Dense and sparse retrievers returning overlapping results without deduplication | Apply Reciprocal Rank Fusion (RRF) with deduplication before reranking; tune dense/sparse weight ratio |
| Evaluation metrics fluctuate across runs | Non-deterministic embedding batching or insufficient test query set | Fix random seeds, increase evaluation sample size, run evaluations on a frozen ground-truth set |

## Success Criteria

- **Faithfulness > 0.90** -- Generated answers are grounded in retrieved context as measured by the RAGAS faithfulness metric.
- **Context Relevance > 0.80** -- At least 80% of retrieved chunks are relevant to the user query.
- **Precision@5 > 0.70** -- Seven out of ten top-5 result sets contain only relevant documents.
- **End-to-end latency < 500ms** -- P95 query-to-response latency stays under 500 milliseconds for interactive workloads.
- **Recall@10 > 0.85** -- The system retrieves at least 85% of relevant documents within the top 10 results.
- **Chunk boundary quality > 0.80** -- At least 80% of chunks end on clean sentence or paragraph boundaries as reported by `chunking_optimizer.py`.
- **Monthly cost within budget** -- Total embedding, vector DB, and reranking costs stay within the budget ceiling defined in requirements.

## Scope & Limitations

**This skill covers:**
- End-to-end RAG pipeline architecture design: chunking, embedding, vector storage, retrieval, reranking, and evaluation.
- Quantitative chunking analysis across four strategy families (fixed-size, sentence, paragraph, semantic).
- Retrieval quality evaluation using standard IR metrics (Precision@K, Recall@K, MRR, NDCG) with a built-in TF-IDF baseline.
- Automated pipeline design with component selection, cost projection, and Mermaid architecture diagrams.

**This skill does NOT cover:**
- LLM prompt engineering or generation-side optimization -- see `engineering/prompt-engineer-toolkit`.
- Database schema design for metadata stores alongside vector databases -- see `engineering/database-designer`.
- Production observability, alerting, and SLO dashboards for deployed pipelines -- see `engineering/observability-designer`.
- Agent orchestration or multi-step reasoning workflows that sit on top of RAG retrieval -- see `engineering/agent-workflow-designer`.

## Integration Points

| Skill | Integration | Data Flow |
|-------|-------------|-----------|
| `engineering/prompt-engineer-toolkit` | Optimize system prompts and few-shot examples fed alongside retrieved chunks | Pipeline design output --> prompt templates that reference chunk format and metadata |
| `engineering/database-designer` | Design relational metadata stores (tags, access control, source tracking) paired with the vector database | Vector DB recommendation --> metadata schema for hybrid storage |
| `engineering/observability-designer` | Set up latency, throughput, and accuracy monitoring for the deployed RAG pipeline | Evaluation metrics and SLO targets --> dashboards and alerting rules |
| `engineering/agent-workflow-designer` | Embed the RAG retrieval step inside multi-agent reasoning workflows | Retrieval config --> agent tool definition with top-K and threshold parameters |
| `engineering/ci-cd-pipeline-builder` | Automate embedding re-indexing, evaluation regression tests, and deployment on document changes | Evaluation thresholds --> CI gate that blocks deploys when metrics regress |
| `engineering/api-design-reviewer` | Review the query and ingestion API surface exposed by the RAG service | Pipeline config --> OpenAPI spec review for search and ingest endpoints |

## Tool Reference

### chunking_optimizer.py

**Purpose:** Analyzes a document corpus and evaluates multiple chunking strategies (fixed-size, sentence-based, paragraph-based, semantic/heading-aware) to recommend the optimal approach with configuration parameters.

**Usage:**
```bash
python chunking_optimizer.py <directory> [options]
```

**Flags / Parameters:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `directory` | positional, required | -- | Directory containing text/markdown documents to analyze |
| `--output`, `-o` | string | None | Output file path for results in JSON format |
| `--config`, `-c` | string | None | JSON configuration file to customize strategy parameters (fixed_sizes, overlaps, sentence_max_sizes, paragraph_max_sizes, semantic_max_sizes) |
| `--extensions` | string list | `.txt .md .markdown` | File extensions to include when scanning the corpus |
| `--verbose`, `-v` | flag | off | Print all strategy scores in addition to the recommendation |

**Example:**
```bash
python chunking_optimizer.py ./docs --output results.json --extensions .txt .md --verbose
```

**Output Formats:**
- **Console** -- Corpus summary, recommended strategy name, performance score, reasoning text, and two sample chunks. With `--verbose`, all strategy scores are listed.
- **JSON** (`--output`) -- Full results object containing `corpus_info`, `strategy_results` (per-strategy size statistics, boundary quality, semantic coherence, vocabulary statistics, performance score), `recommendation` (best strategy, all scores, reasoning), and `sample_chunks`.

---

### retrieval_evaluator.py

**Purpose:** Evaluates retrieval system performance using a built-in TF-IDF baseline retriever and standard information retrieval metrics: Precision@K, Recall@K, MRR, and NDCG. Includes failure analysis and improvement recommendations.

**Usage:**
```bash
python retrieval_evaluator.py <queries> <corpus> <ground_truth> [options]
```

**Flags / Parameters:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `queries` | positional, required | -- | JSON file containing queries (list of `{"id": ..., "query": ...}` objects, or `{"queries": [...]}`) |
| `corpus` | positional, required | -- | Directory containing the document corpus |
| `ground_truth` | positional, required | -- | JSON file mapping query IDs to lists of relevant document IDs |
| `--output`, `-o` | string | None | Output file path for results in JSON format |
| `--k-values` | int list | `1 3 5 10` | K values used when computing Precision@K, Recall@K, and NDCG@K |
| `--extensions` | string list | `.txt .md .markdown` | File extensions to include from the corpus directory |
| `--verbose`, `-v` | flag | off | Print detailed per-metric values and failure analysis counts |

**Example:**
```bash
python retrieval_evaluator.py queries.json ./corpus ground_truth.json --output eval.json --k-values 1 5 10 --verbose
```

**Output Formats:**
- **Console** -- Evaluation summary table (Precision@1, Precision@5, Recall@5, MRR, NDCG@5) with performance assessment and numbered improvement recommendations. With `--verbose`, all aggregate metrics and failure analysis counts are printed.
- **JSON** (`--output`) -- Full results object containing `aggregate_metrics`, `query_results` (per-query metrics, retrieved docs, relevant docs), `failure_analysis` (poor precision/recall counts, zero-result counts, query length analysis, failure patterns), `evaluation_summary`, and `recommendations`.

---

### rag_pipeline_designer.py

**Purpose:** Accepts a system requirements specification and generates a complete RAG pipeline design including component recommendations (chunking, embedding, vector DB, retrieval, reranking, evaluation), cost projections, a Mermaid architecture diagram, and deployment configuration templates.

**Usage:**
```bash
python rag_pipeline_designer.py <requirements> [options]
```

**Flags / Parameters:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `requirements` | positional, required | -- | JSON file containing system requirements (document_types, document_count, avg_document_size, queries_per_day, query_patterns, latency_requirement, budget_monthly, accuracy_priority, cost_priority, maintenance_complexity) |
| `--output`, `-o` | string | None | Output file path for the pipeline design in JSON format |
| `--verbose`, `-v` | flag | off | Print full configuration templates for each component |

**Example:**
```bash
python rag_pipeline_designer.py requirements.json --output pipeline_design.json --verbose
```

**Output Formats:**
- **Console** -- Design summary with total monthly cost, per-component recommendations (name, rationale, cost), and a Mermaid architecture diagram. With `--verbose`, full JSON configuration templates for each component are printed.
- **JSON** (`--output`) -- Complete pipeline design object containing per-component `ComponentRecommendation` fields (name, type, config, rationale, pros, cons, cost_monthly), `total_cost`, `architecture_diagram` (Mermaid markup), and `config_templates` (per-component configs plus deployment/scaling/monitoring settings).
