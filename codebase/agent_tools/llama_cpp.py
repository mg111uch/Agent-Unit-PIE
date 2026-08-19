# Start Server first:
# cd ~/Hello/llama.cpp
# ./build/bin/llama-server -m /home/manigupt/.ollama/models/blobs/sha256-3d7c6c90dd98717a203adb22d5eacd2581850e40aa5327e144b97766cae5f7e3 -t 2 -tb 4 -c 512 -b 64 --port 8080

# Test server from another terminal client:
# curl http://127.0.0.1:8080/health

import requests

url = "http://127.0.0.1:8080/v1/chat/completions"

payload = {
    "model": "Bonsai",
    "messages": [
        {
            "role": "user",
            "content": """You are a tool classifier.
Output ONLY one tool name.

Tools:
CREATE_DIRECTORY
READ_FILE
WRITE_FILE
DELETE_FILE
LIST_FILES
EXECUTE_COMMAND

User: Create a directory called tests

Tool:"""
        }
    ],
    "temperature": 0,
    "max_tokens": 10
}

r = requests.post(url, json=payload)
r.raise_for_status()

print(r.json()["choices"][0]["message"]["content"])