# Mastering AI Agents — Learning Log

A self-paced 6-week journey into building AI agents from first principles: LLM fundamentals, RAG, agentic architectures, fine-tuning, evals, and AI security.

## Progress

| Week | Topic | Status | Notes |
|---|---|---|---|
| 1 | Gen AI Building Blocks (tokens, prompting, function calling) | ✅ Done | [Notes](https://github.com/sridharkesavan/ai-agents-from-scratch/blob/b2d8d4704c35ca85445418b3c4434089ed53fc1c/Week-1/Week-1-NOTES.md) |
| 2 | RAG & Context Engineering | ✅ Done | [Notes](https://github.com/sridharkesavan/ai-agents-from-scratch/blob/b2d8d4704c35ca85445418b3c4434089ed53fc1c/Week-2/Week-2-NOTES.md) |
| 3 | Agentic Architectures (ReAct, Reflection, LangGraph, MCP) | ✅ Done  | [Notes](https://github.com/sridharkesavan/ai-agents-from-scratch/blob/b2d8d4704c35ca85445418b3c4434089ed53fc1c/Week-3/Week-3-NOTES.md) |
| 4 | Fine-tuning & Local Models | ✅ Done  | [Notes](https://github.com/sridharkesavan/ai-agents-from-scratch/blob/b2d8d4704c35ca85445418b3c4434089ed53fc1c/Week-4/Week-4-NOTES.md) |
| 5 | Evals & Observability | ✅ Done  | [Notes](https://github.com/sridharkesavan/ai-agents-from-scratch/blob/b2d8d4704c35ca85445418b3c4434089ed53fc1c/Week-5/Week-5-NOTES.md)
| 6 | AI Security & Safety | ✅ Done | [Notes](https://github.com/sridharkesavan/ai-agents-from-scratch/blob/b2d8d4704c35ca85445418b3c4434089ed53fc1c/Week-6/Week-6-NOTES.md)  |

## Stack

- Python 3.12
- Claude API (Anthropic) — Sonnet 4.5
- ChromaDB — local vector store (Week 2)
- sentence-transformers — local embeddings, `all-MiniLM-L6-v2` (Week 2)
- Tavily — web search for agents (Week 3, Week 6)
- LangGraph — agent orchestration and state machines (Week 3)
- Ollama — local model inference, Llama 3.2 (Week 4)
- Hugging Face `transformers` / `peft` / `bitsandbytes` / `trl` — QLoRA fine-tuning, Colab only (Week 4)
- Langfuse — observability and tracing (Week 5)

## Setup

**1. Clone and install dependencies**
\`\`\`bash
git clone https://github.com/sridharkesavan/ai-agents-from-scratch.git
cd ai-agents-from-scratch
pip install -r requirements.txt
\`\`\`

**2. Environment variables**

Create a `.env` file in the repo root:
\`\`\`
ANTHROPIC_API_KEY=your-key-here
TAVILY_API_KEY=your-key-here
LANGFUSE_PUBLIC_KEY=your-key-here
LANGFUSE_SECRET_KEY=your-key-here
LANGFUSE_HOST=https://cloud.langfuse.com
\`\`\`
(`.env` is gitignored — never commit real keys.)

**3. Ollama (Week 4 only)**

Not a pip package — install separately:
\`\`\`bash
brew install ollama        # macOS
ollama serve                # run in its own terminal, leave running
ollama pull llama3.2        # in a second terminal
\`\`\`

**4. Local documents (Week 2 only)**

`Week-2/documents/` is intentionally empty in this repo — drop your own PDFs or text files there to run the RAG pipeline locally.

**5. Colab fine-tuning (Week 4 stretch exercise)**

The QLoRA fine-tuning notebook runs on Google Colab (free tier, T4 GPU), not locally. Install its dependencies inside the notebook itself:
\`\`\`python
!pip install -q transformers peft bitsandbytes accelerate datasets trl
\`\`\`

## Requirements

# Core — used across most weeks
anthropic
python-dotenv
requests
 
# Week 2 — RAG pipeline
chromadb
pypdf
pymupdf
sentence-transformers
 
# Week 3 — Agentic architectures
tavily-python
langgraph
 
# Week 4 — Local models
ollama
 
# Week 5 — Observability
langfuse
 
# ---
# Colab-only (Week 4 fine-tuning stretch exercise — not needed for local/CPU use)
# Install these only inside the Colab notebook, not on your local machine:
#   transformers
#   peft
#   bitsandbytes
#   accelerate
#   datasets
#   trl
