import ollama

response = ollama.chat(
    model="llama3.2",
    messages=[{"role": "user", "content": "What's 2+2? Answer in one word."}]
)
print(response["message"]["content"])