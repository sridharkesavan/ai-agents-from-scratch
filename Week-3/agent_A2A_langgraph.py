from typing import TypedDict, Literal
import anthropic
from dotenv import load_dotenv
load_dotenv()
from langgraph.graph import StateGraph, END

llm = anthropic.Anthropic()

class AgentState(TypedDict):
    request: str
    task_type: str
    output: str

# --- Manager: classifies the request, doesn't do the work itself ---
def manager_node(state: AgentState) -> dict:
    print(f"\n[Manager reviewing: {state['request']}]")
    classify_prompt = f"""Classify this request into exactly one category:
- "research" — needs factual information, current events, or verifiable facts
- "creative" — needs opinion, brainstorming, or creative writing
- "comparison" — needs a structured comparison between two or more things

Request: {state['request']}

Respond with ONLY the category word, nothing else."""

    response = llm.messages.create(
        model="claude-sonnet-4-5", max_tokens=20,
        messages=[{"role": "user", "content": classify_prompt}]
    )
    task_type = response.content[0].text.strip().lower()
    print(f"  -> Routing to: {task_type}")
    return {"task_type": task_type}

# --- Specialist 1: Research (reuses your Week 3 pattern, simplified here) ---
def research_specialist(state: AgentState) -> dict:
    print("  [Research specialist working...]")
    response = llm.messages.create(
        model="claude-sonnet-4-5", max_tokens=1024,
        system="You are a factual research specialist. Be precise and cite general knowledge carefully; flag anything uncertain.",
        messages=[{"role": "user", "content": state["request"]}]
    )
    return {"output": response.content[0].text}

# --- Specialist 2: Creative ---
def creative_specialist(state: AgentState) -> dict:
    print("  [Creative specialist working...]")
    response = llm.messages.create(
        model="claude-sonnet-4-5", max_tokens=1024,
        system="You are a creative writing specialist. Prioritize originality, voice, and engaging language over strict factual precision.",
        messages=[{"role": "user", "content": state["request"]}]
    )
    return {"output": response.content[0].text}

# --- Specialist 3: Comparison ---
def comparison_specialist(state: AgentState) -> dict:
    print("  [Comparison specialist working...]")
    response = llm.messages.create(
        model="claude-sonnet-4-5", max_tokens=1024,
        system="You are a comparison specialist. Always structure your answer as a clear side-by-side breakdown across relevant dimensions.",
        messages=[{"role": "user", "content": state["request"]}]
    )
    return {"output": response.content[0].text}

# --- Routing function: reads manager's classification, picks the next node ---
def route_task(state: AgentState) -> str:
    return state["task_type"] if state["task_type"] in ["research", "creative", "comparison"] else "research"

# --- Build the graph ---
graph = StateGraph(AgentState)
graph.add_node("manager", manager_node)
graph.add_node("research", research_specialist)
graph.add_node("creative", creative_specialist)
graph.add_node("comparison", comparison_specialist)

graph.set_entry_point("manager")
graph.add_conditional_edges("manager", route_task, {
    "research": "research",
    "creative": "creative",
    "comparison": "comparison"
})
graph.add_edge("research", END)
graph.add_edge("creative", END)
graph.add_edge("comparison", END)

app = graph.compile()

if __name__ == "__main__":
    while True:
        request = input("\nWhat do you need? (or 'quit'): ")
        if request.lower() == "quit":
            break
        result = app.invoke({"request": request, "task_type": "", "output": ""})
        print(f"\n{result['output']}")