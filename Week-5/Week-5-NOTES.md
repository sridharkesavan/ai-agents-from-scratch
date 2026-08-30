# Week 5 — Evals, Observability & Monitoring

## What I built
1. **Golden dataset** (`golden_dataset.py`) — 5 test cases against the Week 3 research agent, each with explicit, checkable criteria targeting known failure modes (citation presence, complete sources, no fabrication, balanced comparison coverage, scope discipline).
2. **LLM-as-a-judge** (`eval_judge.py`) — a Claude call that grades a report against a topic's criteria, returning structured JSON (pass/fail + reason per criterion). Validated standalone against a deliberately bad fake report before trusting it against real output.
3. **Automated batch eval** (`run_eval.py`) — runs the full golden dataset through the real agent (`agent_langgraphV1.py`), scores every result via the judge, prints a scorecard, and saves results to `eval_results.json` for future regression comparison.
4. **Langfuse observability** — instrumented the agent with `@observe()` on graph nodes and a wrapped `call_claude()` function for per-generation tracing (tokens, latency, full prompt/response), plus `propagate_attributes()` to tag each eval run by test case ID.

## Key concepts

### Why normal software testing doesn't work for LLMs
No fixed `assert output == expected` — outputs vary even at low temperature, and many valid answers can exist for one prompt. Evals need explicit, checkable criteria per case, not exact-match assertions.

### Golden datasets
A curated set of realistic inputs with explicit pass/fail criteria — the ground truth to test against. Deliberately included an edge case with no real answer (`no_good_sources`, a fictional/nonexistent person) to test refusal behavior, not just accuracy on answerable questions.

### Failure analysis
Score alone isn't actionable — need to know *how* something failed, not just that it did. The judge's structured per-criterion reasons (not just pass/fail) are what make a failure something you can actually act on.

### LLM-as-a-judge
Using a second model call to grade output against explicit criteria, returning structured (JSON) results so they can be tallied programmatically. Same mechanism as Week 3's `reflect_node`, applied as a standalone evaluation tool instead of a mid-pipeline revision trigger.

### Observability (Langfuse)
Automatic, structured logging of every step in a multi-call system — prompts, responses, token counts, latency — replacing manual `print()`/terminal-scrollback debugging with searchable, inspectable traces per run.

## Bugs hit & fixed

1. **Wrong file targeted for the eval, three times** — attempted to import `app` from `agent_grounding_fix.py`, then `agent_langgraphV1.py` pasted content that turned out to be the plain-function version, before finally using `grep -l "StateGraph"` and `grep -l "sources"` across all Week 3 files to definitively identify which file actually had both the LangGraph structure AND the source-persistence fix. Lesson: when several similarly-named files exist, verify with a direct search (`grep`) rather than trusting filenames or memory of what was built when.

2. **Langfuse SDK version mismatches, three in a row**:
   - `ModuleNotFoundError: No module named 'langfuse.decorators'` — fixed by switching to `from langfuse import observe, get_client` (v2→v3 API change).
   - `AttributeError: 'Langfuse' object has no attribute 'update_current_trace'` — fixed by switching to the `propagate_attributes()` context manager (v3→v4 API change).
   - `TypeError: update_current_generation() got an unexpected keyword argument 'usage'` — fixed by using `usage_details` instead of `usage`.
   - Lesson: for fast-moving libraries, verify against current docs/search rather than trusting remembered syntax — this happened three times in one integration, and each error message itself pointed toward the fix.

## Real findings surfaced by the eval + observability together

1. **`simple_fact` failed on "excessive padding"** — the agent ran a full multi-search research process and produced a long report for a one-fact question ("what year was the Eiffel Tower completed"). Caught by the judge, not by manual testing — revealed the system prompt has no instruction to scale effort/length to question complexity.

2. **Token truncation (`max_tokens` stop reason) resurfaced** — on `comparison_topic` and `ambiguous_scope`, despite being "fixed" in Week 3, under different conditions (more citations, longer content). The reflection loop caught and corrected it within its round limit, but the underlying ceiling can still be hit — worth a dedicated stress-test golden case later.

3. **Eval passed (3/3) but the trace revealed a real factual inconsistency the criteria didn't check for** — reading the raw Langfuse trace for `ambiguous_scope` surfaced the judge's own critique flagging a likely-wrong Tanizaki Prize award year, which never affected the pass/fail score because "cited" and "correct" are different bars the golden dataset didn't distinguish.

4. **Malformed source URLs slipping through** — some entries in the sources list are opaque encoded strings (e.g. `CAESZQHrOzAV...`) instead of real `https://` URLs, visible only in the raw trace data, not in the terminal summary or the eval score. Noted as a gap: no current criterion checks that source URLs are actually well-formed/resolvable — a good candidate for a new golden dataset criterion in a future session.

## Takeaway
This week's real lesson wasn't the eval framework itself — it was that **a passing score and a correct system are not the same thing.** The golden dataset checks for citation *presence*; the raw trace revealed citation *correctness* is a separate, uncovered bar. Evals catch what you explicitly test for; observability lets you catch what you didn't think to test for, by making the actual content inspectable rather than trusting an aggregate score. Neither tool replaces the other — this week showed why both are needed together, not as a redundant pair but as genuinely complementary checks.
