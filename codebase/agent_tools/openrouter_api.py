import requests
import json
import os
import sys
from openai import OpenAI

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent_core", "server"))
from encrypt_env import _try_unlock_env

ENCRYPTED_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.enc")

_try_unlock_env(ENCRYPTED_ENV_FILE)

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.environ['OPENROUTER_API_KEY'],
)

completion = client.chat.completions.create(
  model="deepseek/deepseek-v4-flash",
  messages=[
    {
      "role": "user",
      "content": "Ask a question on world history with 4 options and right answer given"
    }
  ]
)

print(completion.choices[0].message.content)