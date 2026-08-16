# Week 3  Agentic Architectures

## What I built
1. **ReAct research agent** (raw while-loop) - Claude autonomously calls a `web_search` tool (Tavily) multiple times to research a topic, then writes a report.
2. **Reflection loop** - a second agent critiques the report for accuracy/citation issues; if not approved, a revise step regenerates it. Looped up to a max round count.
3. **Citation grounding** - instructed the model to only state claims traceable to search results, with inline `[1]`, `[2]` markers and a numbered Sources section at the end.
4. **Same system rebuilt in LangGraph** - modeled as a state machine: `AgentState` (typed dict), nodes (`research`, `reflect`, `revise`), and a conditional edge (`should_continue`) replacing the manual `for` loop + `if/break` logic.
5. **Multi-agent router (A2A pattern)** - a `manager` node classifies each incoming request (research / creative / comparison) and routes it via conditional edges to a specialist node, each with its own system prompt and behavior.

## Key concepts

### What makes something "agentic"
Not the presence of tools alone - a chatbot with one tool call is still request→response. An agent has a loop it manages itself: it observes results and decides what to do next, potentially across many steps, until it decides it's done.

### ReAct (Reason + Act)
The foundational agent pattern: Thought → Action (tool call) → Observation → repeat until enough information is gathered, then final answer. This emerged naturally from the same function-calling while-loop built in Week 1 - no special framework needed to get this behavior.

### Reflection
A second pass where a (often separate) call critiques the first output against explicit criteria, and the agent revises based on that critique. Cheap, high-leverage - caught real issues in testing (missing sources, unverifiable claims) across multiple rounds.

### LangGraph - state machine framing
- **State**: a typed shared data structure (`AgentState`) that flows through every node.
- **Nodes**: functions that read state and return updates to it.
- **Edges**: define what runs next; **conditional edges** route dynamically based on state (e.g. "APPROVED" vs. "needs revision", or "research" vs. "creative" vs. "comparison").
- Doesn't add intelligence - it's the same control-flow logic as a hand-written loop, just expressed as a declarative graph instead of imperative `for`/`if`/`break`. The benefit shows up as complexity grows (more branches, more steps) - for a 3-node pipeline the benefit is mostly readability, not new capability.

### MCP (Model Context Protocol) - concept only, not implemented this week
Standardizes how an AI application (MCP client) discovers and calls external tools/data (MCP server) - "USB-C for AI tools." The Week 1 `tools.py` + `tool_functions.py` pattern is what MCP formalizes into a portable, cross-application standard.

### A2A (Agent-to-Agent) - implemented this week
Multiple specialized agents collaborating rather than one agent doing everything.
- **Sequential pipeline** (research → reflect → revise) - output of one feeds the next, fixed order.
- **Manager/delegator** (built this week) - one agent classifies the task and dynamically routes to a specialist agent, each with a distinct system prompt/behavior. This is the more realistic pattern for real-world systems (e.g. customer support routing to billing/technical/returns agents).

## Bugs hit & fixed (the most valuable part of this week)

1. **Fabricated citations** - first research agent run invented plausible-sounding but likely-fake named critics, scholars, and quotes despite using real web search. Grounding via search tools reduces hallucination but does not eliminate it at the generation step. **Fix**: explicit system prompt instruction - "only include facts/names/quotes that appear in search results; do not invent specific details even if plausible."

2. **Lost context between LangGraph nodes** - after adding citation requirements, the `revise_node` was asked to add a Sources section but had no real URLs available - only the report text and critique text were passed through state. The actual search results lived in a local variable inside `research_node` and were discarded when that function returned. **Fix**: added `sources: list` to `AgentState` and had `research_node` collect and persist real URLs/titles into state, so every downstream node has access to grounding data, not just derived text.

3. **`max_tokens` truncation** - sources list was cutting off mid-URL, citations in the report body going up to [40] while the printed Sources section stopped at [4]-[8]. Confirmed via `response.stop_reason == "max_tokens"` (not `end_turn`). Report body + full source list exceeded the token cap. **Fix**: raised `max_tokens` on the revise call (2048 → 4096, tuned up further as needed) and reduced the number of sources being written out via dedup.

4. **Duplicate sources inflating citation counts** - running 6-8 searches per topic meant common sources (e.g. Wikipedia) appeared across multiple search calls and got appended to `collected_sources` multiple times under different numbers. **Fix**: dedup by URL before appending - `if not any(s["url"] == r["url"] for s in collected_sources)`.

5. **Low source quality** - even after dedup and fixing truncation, some cited sources were Instagram reels and Facebook group posts, pulled in because Tavily search doesn't rank by source authority. Noted as a real issue (search-grounded ≠ well-sourced) - optional fix is a domain blocklist filter (`instagram.com`, `facebook.com`, etc.) applied before appending to `collected_sources`.

6. **`AuthenticationError: invalid x-api-key`** and **missing-key errors** - recurred multiple times across the week, always the same root cause: `ANTHROPIC_API_KEY` not present in the environment for that specific script/session. Fixes: confirm `load_dotenv()` is called in every new script file (easy to forget when copying code into a new file), confirm `.env` is in the working directory, and confirm the key itself hasn't been revoked/mistyped.

## Takeaway
The biggest lesson this week wasn't any single framework or pattern - it was that **agent reliability problems compound across steps**: a hallucination risk at generation, a data-loss risk at the state-passing boundary between nodes, and a silent truncation risk from token limits can all look like "the output is wrong" from the outside, but each needs a completely different fix. Diagnosing *which* failure mode you're looking at (check `stop_reason`, check what's actually in state, check the system prompt's constraints) is the actual skill - this is exactly why Week 5 (Evals & Observability) exists as its own topic, not an afterthought.
