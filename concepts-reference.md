# AI Agents — Concepts Reference Guide

A condensed study reference covering core concepts, without the debugging detours. Pairs with the code and NOTES.md files in the [ai-agents-from-scratch] repo.

---

## Week 1 — Gen AI Building Blocks

### Tokens & Context Windows
- Models process **tokens**, not characters or words — roughly 4 characters / 0.75 words per token in English.
- API pricing is per-token; output tokens typically cost 3-5x more than input tokens.
- **Context window** = total tokens the model can see at once (system prompt + conversation history + output combined).
- Bigger context ≠ better retrieval — models attend less reliably to information buried in the middle of a large context (the "lost in the middle" effect). This is the core reason RAG exists instead of just pasting everything into the prompt.

### How Generation Works
- Models generate **one token at a time**, autoregressively — each new token depends on everything generated before it.
- **Temperature** controls randomness in token selection: near-0 for deterministic/structured tasks, higher for creative/varied output.
- No "undo" — once a token is generated, it's locked in. This is why chain-of-thought prompting improves accuracy: it gives the model "working memory" written directly into the context before it commits to an answer.
- The model has **no memory between API calls** — every call is stateless. "Conversation" is just resending the full history each time.

### Prompting Techniques
- **System prompt** — sets persistent role/behavior, sent once per conversation.
- **Few-shot prompting** — showing 2-3 example input→output pairs often improves reliability more than a longer instruction, especially for structured tasks.
- **Chain-of-thought** — "think step by step" — improves multi-step logical accuracy.

### Function Calling (Tool Use)
The mechanism underlying every agent:
1. You send the model a list of tool definitions (name, description, JSON schema).
2. The model doesn't execute anything — it returns a structured request: "call `X` with `{params}`."
3. **Your code** executes the actual function.
4. You send the result back to the model in a follow-up call.
5. The model uses that result to continue — answer the user, or call another tool.

This request → pause → execute → resume loop is the entire foundation every agent is built on. It's literally a `while True` loop checking `stop_reason` on each response (`tool_use` = keep looping, `end_turn` = done).

### Structured Outputs
Prefer constraining the model to return valid JSON matching a schema (via JSON mode or a forced tool call) over parsing free text with regex — far more reliable for anything feeding into other code.

---

## Week 2 — RAG & Context Engineering

### Why RAG Exists
Pasting entire documents into every prompt doesn't scale:
- **Cost** — paying for every token on every call, even irrelevant parts.
- **Context window limits** — large knowledge bases won't fit regardless.
- **Lost in the middle** — retrieval accuracy degrades with context size; better to send only what's relevant.

RAG's answer: **retrieve only relevant chunks**, then send just those alongside the question.

### Embeddings
- An embedding model converts text into a vector (list of floats) that captures **meaning**, not literal words.
- Semantically similar texts produce vectors that are close together (measured by **cosine similarity**, range -1 to 1).
- This is why RAG works even when the user's phrasing doesn't match the document's wording — "cancel my subscription" and "terminate your plan" land close together despite sharing no words.
- **Critical rule**: documents and queries must be embedded with the *same* model — mixing models produces incompatible, meaningless similarity scores.
- Local option: `sentence-transformers` (e.g. `all-MiniLM-L6-v2`) — free, runs on CPU, no API key. Hosted alternative: OpenAI/Voyage/Cohere embedding APIs — higher quality, small per-token cost. Anthropic does not offer an embeddings endpoint.

### The RAG Pipeline — Two Phases

**Indexing (done once, or when documents change):**
1. Load documents
2. Split into chunks
3. Embed each chunk
4. Store (chunk text + vector + metadata) in a vector database

**Querying (done per user question):**
1. Embed the user's question with the same embedding model
2. Search the vector DB for the closest stored vectors (top-k)
3. Insert those chunks into the prompt as context
4. Instruct the model to answer **using only that context** — critical for preventing hallucination, since retrieval always returns *something*, even a bad match. Only an explicit instruction ("say so if the answer isn't in the context") makes the model admit uncertainty.

### Chunking Strategy
- **Fixed-size** — split every N characters/tokens. Simple but can cut ideas mid-sentence.
- **Recursive** — split on paragraph → sentence → word boundaries, preserving semantic units. Sane default.
- **Semantic chunking** — use embeddings to detect topic shifts. More expensive, marginal gains for most use cases.
- **Overlap** — chunks typically overlap 10-20% so ideas split across a boundary aren't lost.
- Starting default: ~500-1000 characters per chunk, ~100-150 character overlap.

### Retrieval Beyond Naive Top-K
- **Hybrid search** — combines vector similarity with keyword search (typically **BM25**), merged via a method like Reciprocal Rank Fusion. Needed when exact terms — product codes, names, acronyms — matter and pure semantic similarity might miss them.
- **Re-ranking** — retrieve a larger candidate set cheaply (e.g. top 20), then re-score with a **cross-encoder** (scores query + document jointly, not independently — slower but more accurate) before sending the final top 3-5 to the LLM.
- Both are "measure first" additions — only worth implementing once evals (Week 5) show retrieval quality is actually a problem, not a default to reach for upfront.

### Real-World Data Quality (the part tutorials skip)
- **Scanned/image-based PDFs** — no real embedded text, only pixels. Text extraction libraries return empty. Requires OCR (`pytesseract` + `pdf2image`) to recover text at all.
- **Broken font encoding** — some PDFs embed custom/subsetted fonts with no `ToUnicode` character map. Extraction returns private-use Unicode codepoints (`\uf0XX` range) instead of real letters — looks fine visually in a PDF reader, but structurally unreadable to any text extractor. Confirmed by testing two different libraries (`pypdf`, `pymupdf`) — if both fail identically, the problem is the file's font encoding, not the tool, and only OCR can recover it.
- **Practical lesson**: always validate chunk counts and spot-check extracted text before trusting an ingestion pipeline — a "successful" run can still produce garbage chunks if extraction silently failed.

---

## Quick-Reference Glossary

| Term | Definition |
|---|---|
| Token | Sub-word unit of text the model processes; ~4 characters in English |
| Context window | Total tokens a model can attend to in one call |
| Temperature | Controls randomness in token selection during generation |
| Function/tool calling | Model requests a function call; your code executes it and returns the result |
| Embedding | A vector representation of text capturing semantic meaning |
| Cosine similarity | Metric (-1 to 1) measuring how close two vectors are in meaning |
| Chunking | Splitting documents into smaller pieces for embedding/retrieval |
| Vector database | Storage optimized for similarity search over embeddings (e.g. Chroma, Pinecone) |
| RAG | Retrieval-Augmented Generation — retrieve relevant context, then generate an answer grounded in it |
| BM25 | Statistical keyword-ranking algorithm used in traditional/hybrid search |
| Cross-encoder | Model that scores a query and document jointly (used in re-ranking); more accurate but slower than embeddings |
| Hallucination | Model generating plausible-sounding but false/unsupported information |
