# Week 1 Gen AI Building Blocks

## What I built
A CLI agent using Claude's function-calling API with two tools: a calculator and a weather lookup (later upgraded from mocked data to a real Open-Meteo API integration, chained across a geocoding call + a forecast call).

## Key concepts
- **Tokens & context windows** - pricing and model limits are token-based, not word-based; ~4 chars per token as a rule of thumb.
- **Function calling loop** - the model never executes anything itself. It returns a structured request ("call X with Y"), your code runs it, and you send the result back. This request → execute → resume loop is the seed pattern for every agent built afterward.
- **`stop_reason`** - always check this (`tool_use` vs `end_turn`) rather than assuming any response is final.
- Claude can chain multiple tool calls autonomously in one turn (tested with a "compare weather in two cities" prompt. It called `get_weather` twice without being told to).

## Bugs hit & fixes
1. **`TypeError: Object of type module is not JSON serializable`** - caused by `import tools` instead of `from tools import tools`. The variable name shadowed the module name. Lesson: be careful naming a variable the same as its file/module.
2. **`BadRequestError: credit balance too low`** - not a code bug, just needed to add billing credit in the Anthropic console.

## Stretch: real weather API (Open-Meteo)
Swapped the mocked `get_weather` for a real 2-step API call (geocode city → lat/lon, then fetch forecast for those coordinates). No API key required. Confirmed the agent handled a "not found" city gracefully once the tool returned an explicit error string instead of crashing.

## Takeaway
An "agent" starts as nothing more than a while-loop around a single API call. Everything more advanced (Week 3) is this same pattern with more tools, more turns, and better planning layered on top.
