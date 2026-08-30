# Week 4 — Fine-tuning & Local Models

## What I built
1. **Ollama local setup** — installed Ollama, ran Llama 3.2 (3B) fully offline, both interactively (`ollama run`) and via the Python client.
2. **Local function-calling agent** — reused the Week 1 Open-Meteo weather tool, wired to a local model instead of Claude's API, using the same request → execute → respond loop pattern.
3. **QLoRA fine-tuning attempt on Colab** — loaded `Qwen2.5-0.5B-Instruct` in 4-bit, trained a LoRA adapter on a small custom dataset (context/question/answer triples) targeting one specific behavior: answer only from given context, say "I don't know" otherwise.

## Key concepts

### When fine-tuning is (and isn't) the right tool
Fine-tuning changes the model's actual weights — permanent, expensive to iterate on, hard to reverse. Prompting/RAG shape behavior at inference time — cheap, instant, reversible.
- **Knowledge problem** ("model doesn't know X") → RAG, not fine-tuning.
- **Behavior/style problem** that prompting genuinely can't fix, or a cost/latency need to shrink a large model's capability into a small one for one narrow task → legitimate fine-tuning territory.
- Checklist before fine-tuning: try better prompting first → confirm it's not a knowledge/RAG problem → confirm enough high-quality labeled examples exist → confirm the ongoing cost (retrain on every behavior change) is worth it.

### LoRA / QLoRA mechanism
- Full fine-tuning updates all of a model's weights — expensive in memory (optimizer state alone can be 2-3x model size) and compute.
- LoRA freezes the original weights and represents the *update* to a weight matrix as the product of two much smaller matrices (rank `r`, e.g. 8) instead of one full-size matrix — often training under 1% of total parameters. Confirmed directly via `model.print_trainable_parameters()`.
- QLoRA adds 4-bit quantization on top — the frozen base model loads at ~4x less memory, while the small trained LoRA matrices stay in higher precision. This combination is what makes fine-tuning feasible on a free Colab GPU.
- LoRA adapters are small, separate files that can be merged into or detached from the frozen base model — swappable, like different "adapters" for different tasks on the same base.

### Local models vs. API models — real hands-on comparison
- Local (Ollama, Llama 3.2 3B): free, private, offline, no per-token cost. Noticeably weaker at broad factual knowledge (failed on "who is Vasco da Gama") and multi-step reasoning across tool results.
- Frontier API (Claude): far more reliable at grounding answers in tool results and reasoning across multiple retrieved facts — the gap was very visible testing the same weather-comparison task on both.
- Function calling works on Ollama too (OpenAI-style tool schema), confirming the agent *pattern* from Week 1 isn't Claude-specific — it's how tool-using LLM systems work in general.

## Bugs hit & fixed (the real content of this week)

1. **Two terminals confusion** — tried running `ollama pull` in the same terminal already running `ollama serve` (a foreground process that occupies the terminal). Fix: `ollama serve` in one terminal, all other commands in a second terminal/tab.

2. **Local agent gave inconsistent answers across turns** — root cause was `run_agent()` building a fresh one-item `messages` list on every call instead of persisting conversation history, so each turn had zero memory of previous turns. This produced hallucinated follow-up answers (e.g. randomly checking "London" or "Sydney" instead of the city actually being discussed). Same "no memory between calls" principle from Week 1, just missed in a new script. Fix: pass and reassign the full `messages` list across turns instead of rebuilding it each call. Confirmed fixed via a `[DEBUG] messages so far: N` print showing the count growing correctly turn over turn.

3. **Model ignored real tool results in favor of generic trained "knowledge"** — even after the persistence fix, the local 3B model would call the weather tool correctly, receive a real temperature, and then answer with fabricated generic climate trivia instead of using the actual returned value. Diagnosed as a genuine small-model capability limit (weak grounding in tool output), not a code bug — a plausible real candidate for fine-tuning if this exact behavior needed to be reliable.

4. **LoRA training produced gibberish output (repeated garbage tokens)** — multi-step debugging process:
   - First suspected overfitting on too few examples (4-5) at too high a learning rate — added more data and lowered the learning rate, gibberish persisted.
   - Checked training loss logs directly — loss was decreasing normally (3.06 → 2.92), ruling out gradient explosion/NaN divergence.
   - Isolated the base model (full precision, no quantization) with proper generation settings (`do_sample=False`, `repetition_penalty=1.3`) — worked fine, produced coherent text.
   - Tested the fine-tuned (quantized + LoRA) model with the same generation settings — still gibberish.
   - Disabled the LoRA adapter (`model.disable_adapter()`) and tested the quantized base model alone — still gibberish, isolating the bug to the 4-bit quantized model's generation itself, unrelated to LoRA or training at all.
   - Root cause: a KV-cache/dtype interaction bug under 4-bit quantization (a known category of issue with certain `bitsandbytes`/`transformers` version combinations on Colab). Fix: `use_cache=False` during generation.

5. **Fine-tuning didn't actually change the target behavior** — once generation was fixed, the fine-tuned model still confidently guessed answers instead of saying "I don't know" for out-of-context questions, same as the base model (just guessed a different wrong answer). Root cause: 27 training examples over 14 total steps was nowhere near enough signal to durably shift a base model's strong tendency toward always giving a confident-sounding answer.

## Takeaway
This week made the "fine-tuning is finicky and expensive to get right" lesson from the opening theory session real rather than abstract. Every step of the LoRA exercise surfaced a genuinely different class of problem — an environment/library quirk (KV-cache dtype bug), a classic ML pitfall (small data + aggressive LR causing model collapse), and an honest insufficient-signal result (correct mechanism, too little data to actually move behavior). None of these were solved by "write better code" the way most of Weeks 1-3's bugs were — which is itself the point: fine-tuning is a different kind of engineering problem, with a different, higher bar for what "enough data" and "correct setup" actually mean. This is exactly why the Week 4 opening checklist (try prompting/RAG first, confirm real need, confirm real data) matters — it's not overly cautious advice, it's a reflection of how much more there is to get right once you actually commit to fine-tuning.
