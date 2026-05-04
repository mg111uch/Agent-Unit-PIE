from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from t5_hybrid_retrieval import hybrid_code_retriever

# Initialize Ollama LLM
# Make sure Ollama is running and 'codellama' model is pulled
llm = Ollama(model="codellama") # Or "llama3" or "mistral"

# Define a prompt template for RAG
# This template instructs the LLM how to use the provided context.
RAG_PROMPT_TEMPLATE = """
You are an AI assistant specialized in understanding codebases.
Use the following pieces of Python code context and code relationships to answer the user's question.
If the answer is not available in the provided context, state that you don't know, and do not make up an answer.

Code Context:
{context}

Question: {question}

Detailed Answer:
"""
rag_prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

# Create an LLM chain
rag_chain = LLMChain(llm=llm, prompt=rag_prompt)

if __name__ == "__main__":
    print("\n--- Starting LLM Integration ---")
    # Make sure AuraDB connector is initialized
    # Make sure `code_collection` (ChromaDB) is initialized
    
    # Example Query
    user_query = "Explain the authentication process in this project. Which functions are involved?"
    
    # Step 1: Retrieve context using our hybrid retriever
    context = hybrid_code_retriever(user_query, top_k_vector=5, top_k_graph=5)

    # Step 2: Pass context and query to the LLM
    print(f"\n--- Sending to LLM with context ---")
    llm_response = rag_chain.invoke({"context": context, "question": user_query})

    print("\n--- LLM Response ---")
    print(llm_response['text'])

    # Close AuraDB connection when done
    if auradb_connector:
        auradb_connector.close()