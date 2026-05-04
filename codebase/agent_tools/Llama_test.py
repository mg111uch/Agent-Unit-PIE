from llama_cpp import Llama

llm = Llama(
      model_path="google_functiongemma-270m-it-Q6_K_L.gguf",
      chat_format="gemma",
      ctx_size=2048,
      temperature=0.8,
      # top_p=0.9,
      max_tokens=128,
      stop=["\n", "Q:"],
      echo=False,
      verbose=False,
      # seed=1234,
      # model_kwargs={"use_fp16": True},
      # generate_kwargs={"temperature": 0.7, "top_k": 50}
)

input_text = "What is the capital of India?"

output = llm(input_text) 

response = output['choices'][0]['text']
print(response)

