import anthropic
from tools import tools
from tool_functions import tool_functions

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

def run_agent(user_message: str):
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        # Add Claude's response to the conversation
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [Claude is calling: {block.name}({block.input})]")
                    fn = tool_functions[block.name]
                    result = fn(**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            # Send tool results back as a user turn
            messages.append({"role": "user", "content": tool_results})
        else:
            # No more tool calls — final answer
            final_text = "".join(b.text for b in response.content if b.type == "text")
            return final_text

if __name__ == "__main__":
    while True:
        q = input("\nAsk something (or 'quit'): ")
        if q.lower() == "quit":
            break
        answer = run_agent(q)
        print(f"\n{answer}")