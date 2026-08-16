import os
from dotenv import load_dotenv
from typing import TypedDict
import anthropic
from tavily import TavilyClient
from langgraph.graph import StateGraph, END

load_dotenv()

llm = anthropic.Anthropic()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# --- Tool (same as before) ---
tools = [
    {
        "name": "web_search",
        "description": "Search the web for current information on a topic. Returns titles, URLs, and content snippets.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query."}},
            "required": ["query"]
        }
    }
]

def web_search(query: str) -> str:
    results = tavily.search(query=query, max_results=5)
    formatted = []
    for r in results["results"]:
        formatted.append(f"URL: {r['url']}\nTitle: {r['title']}\nContent: {r['content']}\n")
    return "\n---\n".join(formatted)

tool_functions = {"web_search": web_search}

# --- State: the shared data every node reads/writes ---
class AgentState(TypedDict):
    topic: str
    report: str
    critique: str
    round: int
    max_rounds: int

# --- Node 1: Research (contains its own internal ReAct tool loop) ---
def research_node(state: AgentState) -> dict:
    print(f"\n[Researching: {state['topic']}]")

    system = (
        "You are a research assistant. Use the web_search tool as many times as needed "
        "to gather enough information to write a well-supported report.\n\n"
        "CRITICAL — Accuracy: Only include facts, names, quotes, dates from your search "
        "results. Do not invent specific details even if plausible.\n\n"
        "CRITICAL — Citations: Every factual claim needs an inline marker like [1], [2]. "
        "End with a numbered 'Sources' section listing URLs.\n\n"
        "When you have enough information, write the final report directly."
    )
    messages = [{"role": "user", "content": f"Research and write a report on: {state['topic']}"}]

    while True:
        response = llm.messages.create(
            model="claude-sonnet-4-5", max_tokens=2048,
            system=system, tools=tools, messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [searching: {block.input['query']}]")
                    result = tool_functions[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result", "tool_use_id": block.id, "content": result
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            report = "".join(b.text for b in response.content if b.type == "text")
            return {"report": report}  # only return the state keys this node updates

# --- Node 2: Reflect ---
def reflect_node(state: AgentState) -> dict:
    print(f"\n[Reflection round {state['round'] + 1}]")
    critique_prompt = f"""Review this research report for accuracy and sourcing.

Topic: {state['topic']}
Report: {state['report']}

Check for: invented names/quotes, uncited claims, missing Sources section.
If genuinely solid, respond with exactly: APPROVED
Otherwise, list specific issues to fix."""

    response = llm.messages.create(
        model="claude-sonnet-4-5", max_tokens=1024,
        messages=[{"role": "user", "content": critique_prompt}]
    )
    critique = response.content[0].text
    print(f"  -> {critique[:150]}...")
    return {"critique": critique, "round": state["round"] + 1}

# --- Node 3: Revise ---
def revise_node(state: AgentState) -> dict:
    print("  -> Revising...")
    revise_prompt = f"""Revise this report based on the critique.

Report: {state['report']}
Critique: {state['critique']}

Write the improved report."""

    response = llm.messages.create(
        model="claude-sonnet-4-5", max_tokens=2048,
        messages=[{"role": "user", "content": revise_prompt}]
    )
    return {"report": response.content[0].text}

# --- Conditional edge: decide what happens after reflection ---
def should_continue(state: AgentState) -> str:
    if state["critique"].strip() == "APPROVED":
        return "end"
    if state["round"] >= state["max_rounds"]:
        print("  -> Max rounds reached, stopping.")
        return "end"
    return "revise"

# --- Build the graph ---Tell me about Haruki Murakami, why he is famous? what makes him different than other authors? 
graph = StateGraph(AgentState)
graph.add_node("research", research_node)
graph.add_node("reflect", reflect_node)
graph.add_node("revise", revise_node)

graph.set_entry_point("research")
graph.add_edge("research", "reflect")
graph.add_conditional_edges("reflect", should_continue, {"revise": "revise", "end": END})
graph.add_edge("revise", "reflect")  # loop back after revising

app = graph.compile()

if __name__ == "__main__":
    topic = input("What topic should I research? ")
    result = app.invoke({
        "topic": topic, "report": "", "critique": "", "round": 0, "max_rounds": 2
    })
    print("\n" + "="*50)
    print("FINAL REPORT")
    print("="*50)
    print(result["report"])