Implement the feature from `next_feature.yaml` by editing only the files listed as paths in `context.txt`. Apply changes atomically, update metadata headers, then re-ingest to DB.

**Steps (use tools where needed):**

1. For each path in paths :
   - Parse feature: '{spec['feature']}', deps: {spec['deps']}. 
   - Plan: Semantic edits (add/enhance methods, imports). Preserve style (indentation, existing logic).
   - Apply: Modify content.
   - Update metadata: Regenerate YAML header using internal CoD for summary (add salient entities like new method), dependencies (parse imports), tags (e.g., add "movement"), hierarchy_mapping (add method to class), graph_methods (update edges/CFG). Prepend as docstring: `"""\nmetadata:\n  summary: "..."\n  ...\n"""` + cleaned original content (remove old header/docstrings/comments/blank lines per sqlrag.py logic).
2. After all edits: Re-ingest modified files to DB.
   - Code: `import subprocess; subprocess.run(['python', 'sqlrag.py', 'ingest', '--dir', '/python/Popula', '--db', 'rag.db'])`
3. Log changes: Append to `development_log.md`: "## Changes for {spec['feature']} - {datetime.now()}\n- Files edited: {paths}\n- Summary: Added fertility bias to farmer movement."

**Constraints:** Only edit listed paths. Import numpy if absent. Limit to minimal 1-2 changes per file. 

============================================================

- Make changes in the code. (Generation step). Append all the changes made in the project during the code generation phase in the devpt_log.md file.

- Reflect on the project and agent performance by reading those files and reflect on how the execution loop of project+agent pipeline could be made faster. Also the codebase of project development and agent evolution process should move to higher level and layers of planning. Find strategies and algorithms to make the process flow smoother and easier for human understanding.For this execute this command. <Command>cd python/rag_pipeline/ai_agent && python reflection.py</Command> 

- File metadata structure is given in metaFileStr.md file. The strategies which have already been tried are appended in metadata report file. Find new strategies on how this metadata structure above each file should be modified to make the retrieval process from a sqlite database more accurate.

- Find plans on how this loop could be parallelised by delegating the tasks in the loop to sub agents. After finishing the subagent task the result from each subagent should be complied and then reasoned for the next loop iteration.

- Analyse the performance of subagents and find the bottleneck subagent. Then find and implement the strategy on how the execution of this subagent could be made faster.Log the changes made on subagent in the agentReadme.md file.  

- Find the files in which the changes need to be done by executing this command. <Command>cd python/rag_pipeline/ai_agent && python retrieve.py</Command> 

- For testing the front end changes run the following command to record front end video.<Command>cd python/rag_pipeline/ai_agent && eval "$(conda shell.bash hook)" && conda activate myenv python record_browser.py</Command>. 

- Then get the testing result of recorded frontend video in a text file by running this command.<Command>cd python/rag_pipeline/ai_agent && eval "$(conda shell.bash hook)" && conda activate myenv python reason_video.py</Command>

## 6. META-REFLECTION & SELF-EVOLUTION
- **Performance Analysis:** Read `agent_state.db` logs.
  - Identify Bottleneck (Metric: Execution Time).
  - Suggest 1-2 fixes as YAML: {{improvements: [{{target: 'file path', change: 'Changes to be made in the file.'}}]}}.
  - Log reflection to `devpt_log.md`: refl_entry = f"### Reflection {iteration_num} - {datetime.now()}\n{json.dumps(reflection, indent=2)}\n"
- **Self-Improvement:**
  - Log all the performance metrics of the agent in the agent report file.
  - If the loop execution could be made faster by making a tool, then write a python script for that tool and save the tool in /tools directory for later use.
- **Self-Optimization:**
  - *Scenario:* If `sub_agents.py` is too slow:
    - Agent writes optimized code to `updates/sub_agents_v2.py`.
    - Agent writes `orchestrator_prompt_v2.txt`.
  - *Verification:* Run "Agent Test Suite" on new code.
  - *Deployment:* Signal `Launcher.py` -> `UPDATE_PENDING`.
  - `Launcher` stops current process, replaces files in `Agent_Logic/`, and restarts.

- Create as many agents for the tasks in the loop as possible.

- Use different models for different tasks.

- Invoke gemini cli directly from the kilocode.
 

5. Get the text for the image plot generated after running the simulation using the following command.<Command>cd python/rag_pipeline/ai_agent && eval "$(conda shell.bash hook)" && conda activate myenv && python reason_Img.py</Command> 

6. Compare the expected_changes and the actual_changes. 
  - If the expected_changes and the actual_changes are not matching, then go back to step 2 and make the necessary changes. 
  - If the expected_changes and the actual_changes are matching, then Update `TODO.md` (Mark current task done) and proceed to the next step.

7. Update `Insight.md` with the insights from the simulation results.

8. **Interactive Query:**
  - "Task Complete. Current State: [Summary]. Proceed to deduce next logical step, or await new Prompt?"
  - *Action:* Wait for User Input.

===========================================================

# AGENT ORCHESTRATION PROTOCOL (PHOENIX V1)

- **Read Access:** Files allowed to be read in `python/rag_pipeline/ai_agent` are `Orchestrator.md` and `config.yaml`.

## SYSTEM INITIALIZATION
- Directly start implementing the instructions without making any orchestrator script.
- Read `config.yaml` for project parameters.
- Initialize a counter for the loop: LOOP_ITERATION = 1
- Open the log_file in append mode.
- Working directory is the project_root given in config . 
- All files other than above mentioned files are in project_root.
- You are not allowed to read, write or edit any file outside of project_root. 
- Read target project's `README.md`.
- Run the loop given below. Do the tasks inside loop in order.
- Before each code execution, remember to activate the conda environment using command given in `config.yaml`.
- All dependencies are already installed in the environment.No need to check for them.
- Git is already initialised in the project_root. No need to do it.

<LOOP – Run until all features in `development_plan.md` are marked done >

# Phase 1: TDD Planning and Test Generation
1.  **[TIME START]** Record the current system timestamp: **LOOP_START_TIME**
2. Read the next undone feature from `development_plan.md` in the project_root directory. 
3. **Analyze Feature:** Check feature dependencies and clarity against `README.md` in the project_root. If unclear, prompt user for clarification.
5. **[START TIME LOG: Test Gen]** Record system timestamp.
4. **Action:** Generate ALL necessary unit test files in project_root for the feature based on its requirements. 
6. **[END TIME LOG: Test Gen]** Record and log time for test generation.

# Phase 2: Feature Implementation and Testing
4. **[START TIME LOG: Implement]** Record system timestamp.
5. Implement the feature and generate necessary code files in the project_root that will make the tests pass.
6. **[END TIME LOG: Implement]** Record and log time for implementation/generation.
7. Before execution, activate the conda environment using command in `config.yaml`.
8. **[START TIME LOG: Execute]** Record system timestamp.
9. Execute the game code files and tests.
10. **[END TIME LOG: Execute]** Record and log time for execution.

# Phase 3: Validation and Version Control
11. If code execution output indicates SUCCESS:
    a. **Git Commit:** Execute the command: git add . && git commit -m "feat(phoenix): Implemented feature <FEATURE_NAME>"
    b. Mark the feature done in `development_plan.md`.
    c. **Update README.md:** Append a section to `README.md` detailing the current project state (including the new feature and current version/commit hash).
    d. **Logging:** Log the success, total loop time, and current commit ID to log_file.
12. If code execution output indicates FAILURE:
    a. **Git Checkout:** Execute the command: git checkout -- . (Revert changes to the last committed state).
    b. **Generate Root Cause Analysis (RCA):** Summarize the failure and identify the fix strategy.
    c. **Retry:** Try to fix the error or reformulate the code using the RCA.Increment the retry counter. Try again up to 3 times (loop back to Task 7).
    d. **Escalation:** If the Retry Counter reaches 3 attempts, log the failure/RCA and ESCALATE to the user for manual intervention.

## Finalization
13.  **[TIME END & LOG]**
    a. Record the current system timestamp: **LOOP_END_TIME**
    b. Calculate the duration: **EXECUTION_TIME = LOOP_END_TIME - LOOP_START_TIME**
    c. **Log the result:** Append the following line to log_file:
       `[TIMESTAMP] Loop <LOOP_ITERATION> completed in: <EXECUTION_TIME> seconds. Status: <SUCCESS/FAILURE>`
    d. Ask the user to proceed to the next loop iteration.
    e. Increment the loop counter: **LOOP_ITERATION = LOOP_ITERATION + 1**

</LOOP>

=================================================

- Add token usage in each loop.
- Add on feature changes needed after each loop.

