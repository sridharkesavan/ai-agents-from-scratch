# Week 6 — AI Security & Safety

## What I built
- **Indirect prompt injection tests** (`test_injection.py`, `test_injection_v4.py`) — simulated poisoned search results at increasing levels of realism: a single always-identical poisoned result, then three injection framings (system-override, fake-citation-instruction, fake-user-update) each tested standalone, then a hardened version with 5 varied legitimate sources and the injection hidden in only one of them (the realistic scenario).
- **Output guardrail** (`output_guardrail.py`) — a deterministic, code-level check independent of model behavior: flags suspicious text patterns and citations pointing to domains outside an explicit allow-list. Wired directly into the agent's output path so every report is checked before delivery, not just tested after the fact.
- **Direct prompt injection tests** (`test_direct_injection.py`) — four user-facing social-engineering attempts (ignore citation rules, "unrestricted mode," fake "administrator" override, fake identity change) run directly against the agent, no tool manipulation involved.

## Key concepts

### The AI threat surface is different from traditional app security
Traditional security assumes attackers exploit code paths. LLM systems mix trusted instructions and untrusted retrieved content in the same channel (plain text) — the model has no built-in way to tell "an instruction I should follow" apart from "content I'm supposed to summarize, that happens to contain text shaped like an instruction."

### Prompt injection — two categories, both tested this week
- **Indirect** — malicious instructions hidden inside content the agent retrieves and treats as data (a poisoned search result, in this week's tests; a poisoned RAG document, in principle, connecting back to Week 2). Generally considered the more dangerous category for agentic systems, since more tools/data sources means more surface area.
- **Direct** — a user directly instructing the agent to break its own rules, often via social-engineering framing (fake system messages, fake "unrestricted mode," fake identity changes).

### Hallucination reframed as a safety problem, not just a quality problem
A hallucinated fact in a report (Weeks 3-5) is embarrassing. A hallucinated fact that drives a real downstream action (sending an email, making a purchase, modifying a system) has a much higher cost — same underlying model behavior, different consequence depending on what the agent is actually able to *do*.

### Guardrails as a deterministic backstop, not a replacement for good prompting
Model resistance to an attack is probabilistic — it can hold today and fail tomorrow with a different model version or a cleverer attack. A code-level guardrail (regex pattern matching, domain allow-lists) doesn't rely on the model's judgment at all; it mechanically blocks known-bad signals regardless of why they occurred. The two layers are complementary, not redundant — same "scorecard + trace" pairing lesson from Week 5, applied to safety instead of quality.

### PII handling — covered conceptually, not tested hands-on
The Week 3 research agent doesn't structurally process real user/personal data (it takes a public research topic and searches public web content), so a hands-on PII test wasn't a meaningful fit for this system. Noted as a concept to apply if this agent, or the eventual capstone, ever handles real user data: what flows to third-party APIs (Tavily, Anthropic) per call, and what gets retained in observability traces (Langfuse, from Week 5).

## Bugs hit & fixed
1. **`KeyError: 'web_search'`** — when swapping in a new poisoned-search function, the `tool_functions` dictionary key didn't match the tool schema's declared name. Same root-cause pattern as Week 1's `import tools` mix-up: a name mismatch between two places that must agree exactly.
2. **Weak first version of the injection test** — the original poisoned-search function returned identical content on every call, meaning the model may have been reacting to "suspiciously repetitive results" rather than genuinely resisting the injected instruction. Fixed by building a varied set of legitimate-looking snippets, randomly selected per call, with the injection embedded in only one call among several clean ones — isolating genuine injection resistance from an incidental confound.
3. **Guardrail false positive from a domain-list mismatch** — the output guardrail's `ALLOWED_DOMAINS` list was written for one test file's fake sources but run against a different, older test file using a different fake domain, causing a legitimate citation to be blocked as "unrecognized." Same "which file is the right one" confusion pattern as Week 5 — resolved by aligning the guardrail's config to the actual file being run.
4. **Verdict-scoring blind spot in the direct injection test** — the original pass/fail check only looked for "citations present," which meant an agent correctly *refusing to proceed* without a clear topic looked identical to "the attack succeeded and no citations were produced." Fixed by adding a third verdict category (asked for clarification) — though even the fixed version had one false trigger (a resistant, cited response got mislabeled as a refusal due to a coincidental keyword match), underscoring that keyword-based test harnesses need their own scrutiny, not just the system under test.

## Red-team findings (evidence-backed, not assumed)
- **Indirect injection**: resisted across 3 distinct framings (system-override, fake-citation-instruction, fake-user-update) and multiple runs, including the hardened realistic version with the injection hidden among 5 varied legitimate sources.
- **Direct injection**: resisted across 4 distinct social-engineering framings — 2 proceeded with the legitimate research task while keeping citation rules intact, 2 declined to engage with the fake-authority/fake-identity framing entirely and asked for clarification instead.
- **Output guardrail**: correctly blocks known-bad patterns and unrecognized-domain citations; correctly passes clean output; demonstrated one real false-positive failure mode (stale/mismatched allow-list) worth remembering as an operational risk, not just a testing inconvenience.

## Production-readiness checklist (for this agent, based on what was actually tested this week)
- [x] Tested resistance to indirect prompt injection (poisoned retrieved content)
- [x] Tested resistance to direct prompt injection (user social engineering)
- [x] Deterministic output guardrail in place, independent of model behavior
- [x] Citation/grounding requirements enforced via system prompt (Week 3) and verified under adversarial conditions (this week)
- [ ] PII handling — not applicable to current scope; revisit if the agent is extended to handle real user data (e.g. the capstone)
- [ ] Guardrail allow-list actively maintained — currently hardcoded for test domains; would need a real maintenance process before any production use
- [ ] Rate limiting / cost controls — not addressed this week, worth adding before giving an agent unsupervised, repeated real-world access
- [ ] Human review step for high-stakes or ambiguous outputs — not built; worth considering before connecting an agent to systems that take real action (directly relevant to the ServiceNow/Jira/Outlook-style capstone idea)

## Takeaway
This week's tests didn't just confirm the agent resists prompt injection — they repeatedly revealed that the *test harnesses themselves* were the weaker link: a same-content confound in the first injection test, a stale domain list in the guardrail, a keyword-based blind spot in the verdict logic. That's a fitting way to end a 6-week course built almost entirely on real, hands-on debugging: the system under test held up consistently; the tooling used to verify it needed just as much scrutiny as the thing being tested. Security work, like evals, isn't a single pass/fail check — it's an ongoing discipline of questioning your own test's assumptions, not just the system's behavior.
