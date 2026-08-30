#This is a research agent that uses LangGraph to orchestrate a multi-step process: research, reflection, and revision. It uses the Tavily API for web search and the Anthropic API for LLM responses. The agent collects sources during research and ensures that the final report is accurate and well-cited.
#This uses langfuse for observability and monitoring
#A file carried over from Week-3, with some edits to add langfuse observability and to ensure that the research node collects sources and passes them to the revise node. 
import os
from dotenv import load_dotenv
from typing import TypedDict
import anthropic
from tavily import TavilyClient
from langgraph.graph import StateGraph, END
from langfuse import observe, get_client

load_dotenv()
langfuse = get_client()

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
    sources: list       # <-- NEW: real URLs collected during research
    round: int
    max_rounds: int

# --- Node 1: Research (contains its own internal ReAct tool loop) ---
@observe()
def research_node(state: AgentState) -> dict:
    print(f"\n[Researching: {state['topic']}]")

    system = (
        "You are a research assistant. Use the web_search tool as many times as needed. "
        "CRITICAL — Accuracy: only include facts from your search results, nothing invented. "
        "CRITICAL — Citations: every claim needs an inline marker like [1], [2]. "
        "When done, write the final report directly."
    )
    messages = [{"role": "user", "content": f"Research and write a report on: {state['topic']}"}]
    collected_sources = []  # track every URL actually returned by search

    while True:
        response = call_claude(system=system, tools=tools, messages=messages)
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [searching: {block.input['query']}]")
                    result = tool_functions[block.name](**block.input)
                    
                    #NEW: parse and store URLs/titles as we go
                    raw_results = tavily.search(query=block.input["query"], max_results=5)
                    
                    #NEW: filter out low-quality domains (social media, etc.) and avoid duplicates
                    LOW_QUALITY_DOMAINS = ["instagram.com", "facebook.com", "tiktok.com", "pinterest.com"]

                    for r in raw_results["results"]:
                        domain = r["url"].split("/")[2] if "//" in r["url"] else ""
                        if any(bad in domain for bad in LOW_QUALITY_DOMAINS):
                            continue  # skip social media links as sources
                        if not any(s["url"] == r["url"] for s in collected_sources):
                            collected_sources.append({"url": r["url"], "title": r["title"]})
                    
                    tool_results.append({
                        "type": "tool_result", "tool_use_id": block.id, "content": result
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            report = "".join(b.text for b in response.content if b.type == "text")
            return {"report": report, "sources": collected_sources}  # <-- now saved in state}  # only return the state keys this node updates

@observe(as_type="generation")
def call_claude(system, tools, messages, max_tokens=2048):
    response = llm.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=max_tokens,
        system=system,
        tools=tools,
        messages=messages
    )
    langfuse.update_current_generation(
        model="claude-sonnet-4-5",
        usage_details={"input": response.usage.input_tokens, "output": response.usage.output_tokens}
    )
    return response

# --- Node 2: Reflect ---
@observe()
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
@observe()
def revise_node(state: AgentState) -> dict:
    print("  -> Revising...")

    sources_list = "\n".join(
        f"[{i+1}] {s['title']} — {s['url']}" for i, s in enumerate(state["sources"])
    )

    revise_prompt = f"""Revise this report based on the critique.

Report: {state['report']}

Critique: {state['critique']}

Here are the ACTUAL sources available from research — use only these URLs, 
renumber citations to match this list, and include this exact list as your Sources section:
{sources_list}

Write the improved report."""

    response = llm.messages.create(
        model="claude-sonnet-4-5", max_tokens=4096,
        messages=[{"role": "user", "content": revise_prompt}]
    )
    print(f"Stop reason: {response.stop_reason}")  # add this temporarily
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
        "topic": topic, "report": "", "critique": "", 
        "sources": [], "round": 0, "max_rounds": 2   # <-- add sources: [] 
    })
    print("\n" + "="*50)
    print("FINAL REPORT")
    print("="*50)
    print(result["report"])