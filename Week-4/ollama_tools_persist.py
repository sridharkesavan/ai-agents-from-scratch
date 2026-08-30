import ollama
import requests

def get_weather(city: str) -> str:
    geo_resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1}
    )
    geo_data = geo_resp.json()
    if "results" not in geo_data or len(geo_data["results"]) == 0:
        return f"Could not find location: {city}"

    location = geo_data["results"][0]
    lat, lon = location["latitude"], location["longitude"]

    weather_resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current": "temperature_2m"}
    )
    temp = weather_resp.json()["current"]["temperature_2m"]
    return f"{location['name']}: {temp}°C"

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a given city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. 'Tokyo'."}
                },
                "required": ["city"]
            }
        }
    }
]

tool_functions = {"get_weather": get_weather}

# --- Now takes and returns the FULL conversation list, not just one string ---
def run_agent(messages: list):
    print(f"[DEBUG] messages so far: {len(messages)}")
    response = ollama.chat(model="llama3.2", messages=messages, tools=tools)
    messages.append(response["message"])

    if response["message"].get("tool_calls"):
        for call in response["message"]["tool_calls"]:
            fn_name = call["function"]["name"]
            fn_args = call["function"]["arguments"]
            print(f"  [calling: {fn_name}({fn_args})]")
            result = tool_functions[fn_name](**fn_args)
            messages.append({"role": "tool", "content": result})

        final = ollama.chat(model="llama3.2", messages=messages)
        messages.append(final["message"])
        return final["message"]["content"], messages
    else:
        return response["message"]["content"], messages

if __name__ == "__main__":
    conversation = []  # created ONCE, outside the loop

    while True:
        q = input("\nAsk something (or 'quit'): ")
        if q.lower() == "quit":
            break
        conversation.append({"role": "user", "content": q})
        answer, conversation = run_agent(conversation)  # reassign, don't discard
        print(answer)