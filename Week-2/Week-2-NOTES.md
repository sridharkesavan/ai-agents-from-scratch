# Week 2  RAG & Context Engineering

## What I built
A local RAG pipeline: ingest PDFs/markdown → chunk → embed (local `sentence-transformers` model) → store in ChromaDB → retrieve top-k relevant chunks per question → generate an answer grounded only in retrieved context, with source citations.

## Key concepts
- **Why RAG over "just paste everything in the prompt"** - cost, context window limits, and the "lost in the middle" effect where models attend less reliably to info buried in a huge context.
- **Embeddings** - verified hands-on: "cancel my subscription" vs "terminate your plan" scored ~0.48 cosine similarity despite sharing no words, vs ~-0.09 against an unrelated "weather" sentence. This is the entire mechanism semantic search depends on.
- **Indexing vs. querying are separate phases** - index once (or when docs change), query many times, both must use the *same* embedding model or the vector spaces are incompatible.
- **Chunking** - used recursive fixed-size chunking (800 chars, 150 overlap) as a sane starting default.
- Grounded prompting matters: explicitly instructing "answer using ONLY the context, say so if it's not there" is what prevents hallucination when retrieval comes up empty/irrelevant,  retrieval always returns *something*, even a bad match, so the LLM has to be told when to admit it doesn't know.

## Bugs hit & fixes (the most valuable part of this week, honestly)
1. **Scanned PDF (`norwegian-wood.pdf`)** - `pypdf` extracted zero text because the pages were images of text, not real embedded text. No library fix; would require OCR (`pytesseract` + `pdf2image`). Skipped the file for now, added defensive `if not chunks: continue` handling in `ingest.py` so one bad file doesn't crash the whole ingestion run.
2. **Broken font encoding (`sputnik-sweetheart.pdf`)** - extracted "text" was garbage: private-use Unicode codepoints (`\uf0XX` range) instead of real characters. Tried both `pypdf` and `pymupdf` - same result on both, confirming the PDF's embedded font has no usable character-to-Unicode mapping at all. Not fixable without OCR. Lesson: try a second extraction library before assuming OCR is needed, but if two libraries agree, the problem is the file, not the tool.

## Stretch (conceptual only): hybrid search & re-ranking
- **Hybrid search** = vector search + keyword search (BM25) combined via something like Reciprocal Rank Fusion. Needed when exact terms/codes/names matter, which pure embedding similarity can miss.
- **Re-ranking** = retrieve a larger candidate set cheaply, then re-score with a more expensive cross-encoder (scores query+doc jointly, not independently) before sending the final top few to the LLM.
- Didn't implement - noted as a "measure first, then decide" (Week 5 eval territory) rather than a default to reach for.

## Takeaway
RAG's hard part isn't the pipeline code - that's straightforward. It's real-world data quality. Two different PDF failure modes in one afternoon was a good reminder that "garbage in, garbage out" applies just as much to retrieval as to any other data pipeline.
