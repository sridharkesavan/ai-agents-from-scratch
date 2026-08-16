import os
from dotenv import load_dotenv
import anthropic
from tavily import TavilyClient

load_dotenv()

llm = anthropic.Anthropic()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# --- Tool definition ---
tools = [
    {
        "name": "web_search",
        "description": "Search the web for current information on a topic. Returns a list of results with titles, URLs, and content snippets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."}
            },
            "required": ["query"]
        }
    }
]

def web_search(query: str) -> str:
    results = tavily.search(query=query, max_results=5)
    formatted = []
    for r in results["results"]:
        formatted.append(f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}\n")
    return "\n---\n".join(formatted)

tool_functions = {"web_search": web_search}

# --- Stage A: ReAct research loop ---
def research(topic: str) -> str:
    system = (
        "You are a research assistant. Use the web_search tool as many times as needed "
        "to gather enough information to write a well-supported report on the given topic. "
        "Search for multiple angles/sub-questions before writing your final report. "
        "When you have enough information, write the final report directly (no more tool calls)."
    )
    messages = [{"role": "user", "content": f"Research this topic and write a short report: {topic}"}]

    while True:
        response = llm.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            system=system,
            tools=tools,
            messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [searching: {block.input['query']}]")
                    result = tool_functions[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            return "".join(b.text for b in response.content if b.type == "text")

# --- Stage B: Reflection ---
def reflect(topic: str, report: str) -> str:
    critique_prompt = f"""You are a critical editor reviewing a research report.

Topic: {topic}

Report:
{report}

Critique this report. Check for:
- Factual claims that seem unsupported or vague
- Missing important angles on the topic
- Poor structure or unclear writing

If the report is genuinely solid, respond with exactly: APPROVED
Otherwise, list specific, actionable issues to fix."""

    response = llm.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": critique_prompt}]
    )
    return response.content[0].text

def revise(topic: str, report: str, critique: str) -> str:
    revise_prompt = f"""Revise this research report based on the critique below.

Topic: {topic}

Original report:
{report}

Critique:
{critique}

Write the improved report."""

    response = llm.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": revise_prompt}]
    )
    return response.content[0].text

# --- Orchestration: research -> reflect -> revise loop ---
def run_research_agent(topic: str, max_reflection_rounds: int = 2):
    print(f"\n[Researching: {topic}]")
    report = research(topic)

    for round_num in range(max_reflection_rounds):
        print(f"\n[Reflection round {round_num + 1}]")
        critique = reflect(topic, report)

        if critique.strip() == "APPROVED":
            print("  -> Approved, no changes needed")
            break

        print(f"  -> Critique: {critique[:200]}...")
        print("  -> Revising...")
        report = revise(topic, report, critique)

    return report

if __name__ == "__main__":
    topic = input("What topic should I research? ")
    final_report = run_research_agent(topic)
    print("\n" + "="*50)
    print("FINAL REPORT")
    print("="*50)
    print(final_report)