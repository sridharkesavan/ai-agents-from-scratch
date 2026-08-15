tools = [
    {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression, e.g. '12 * (4 + 3)'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "A math expression to evaluate."}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "get_weather",
        "description": "Get the current weather for a given city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Tokyo'."}
            },
            "required": ["city"]
        }
    },
    {
    "name": "get_live_weather",
    "description": "Get the current real-time weather for a given city, anywhere in the world.",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name, e.g. 'Tokyo'."}
        },
        "required": ["city"]
        }
    }
]