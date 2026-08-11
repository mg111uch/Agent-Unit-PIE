import requests

# Start ollama server: `ollama serve`

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "funcGemma",
        "messages": [
            {"role": "user", "content": "say hello!"}
        ],
        "stream": False
    }
)

data = response.json()
print(data["message"]["content"])

# Stop ollama server:
# Command: `pgrep -af ollama` (returns ollama server pid)
# Command: `kill <pid>`

# Modelfile content:
# FROM ./google_functiongemma-270m-it-Q6_K_L.gguf
# renderer functiongemma
# parser functiongemma
# PARAMETER top_k 64
# PARAMETER top_p 0.95
# PARAMETER temperature 0.1
