from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/manigupt/Hello/python/Agentic_Unit_PIE/codebase") 

my_api_key = os.getenv("HUGGING_FACE_API_KEY")

client = InferenceClient(
    # provider="hf-inference",
    provider="cerebras",
    api_key=my_api_key,
)

completion = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ],
    stream=False,
    max_tokens=1024,
)

print(completion.choices[0].message)