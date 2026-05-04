from google.adk.agents import LlmAgent, LoopAgent, Agent
from google.adk.tools import CodeExecTool 

from readWriteMD import read_and_update_md

# --- 2. Orchestrator Agent ---

# 2a. Define the Tools
# The CodeExecTool allows the agent to generate and run code in a sandbox (essential for dev)
code_tool = CodeExecTool(name="code_executor") 
# Wrap the custom function as an ADK tool
plan_tool = Agent.function_as_tool(read_and_update_md) 

# 2b. Define the Core Development LLM Agent
development_agent = LlmAgent(
    name="GameDeveloperAgent",
    model="gemini-2.5-flash", # Use a powerful model for complex reasoning
    instruction="""
    You are a professional game developer. Your task is to implement the next feature from the provided MD file.
    1. Read the feature using the 'read_and_update_md' tool.
    2. Generate the necessary game code files and corresponding unit tests.
    3. Use the 'code_executor' tool to run the tests and implement the feature.
    4. If the code_executor output indicates success (exit code 0), call 'read_and_update_md' with status="done".
    5. If the code_executor output indicates failure, call 'read_and_update_md' with status="failed" and include the error log in the log_message. Then, reformulate your code and try again (up to 3 times).
    6. Your final output must be the result of the tool call.
    """,
    tools=[code_tool, plan_tool]
)

# 2c. Define the Master Iterative Loop Agent
def loop_condition_function(state) -> bool:
    """Checks the MD file for any remaining undone features."""
    result = read_and_update_md(file_path="development_plan.md", status="read_next")
    # Loop continues as long as a feature is found (i.e., it's not the "ERROR" or "None found" message)
    return "FEATURE:" in result

master_loop_agent = LoopAgent(
    name="IterativeDevOrchestrator",
    instruction="Continuously implement features from development_plan.md until all are complete.",
    initial_state={}, # Initial state can be empty
    loop_agent=development_agent, # The agent to run in the loop
    loop_condition=loop_condition_function # The condition to stop the loop
)

# --- 3. Execution (The "Master File" Run) ---
if __name__ == "__main__":
    # Assuming the 'development_plan.md' is in the current directory
    # In a real ADK setup, you would use a Runner to execute the agent.
    
    print("--- Starting Agentic Development Loop ---")
    
    # This is the simplified execution flow:
    final_output = master_loop_agent.run_with_tools(
        input_message="Start the iterative game development process.",
        context={
            "file_path": "development_plan.md",
            "max_retries": 3 # Custom context variable for the LLM to respect
        }
    )
    
    print("--- Agent Development Complete ---")
    print(final_output)
