# AGENT ORCHESTRATION PROTOCOL (PHOENIX V1)
You are tasked with rebuilding a non-functional legacy codebase in `python/dota2/grok4/` into a functional, modular game in `python/dota2/grok_code1/dota2_gym/`.

## DIRECTORY STRUCTURE OF AGENT AND PROJECT
### Tree
python/
├── ai_agent/                # THE BRAIN TOOLS
│   ├── orchestrator.md
│   └── phoenix_helper.py
└── dota2/                   # THE PROJECT SPACE
    ├── grok_code1/          # TARGET (Clean Code)
    │   └── dota2_gym/       # Working Dir (run tests here)
    ├── grok4/               # LEGACY (Reference)
    │   └── dota2_gym/       # legacy Code
    ├── project_manifesto.md
    ├── devpt_state.md
    ├── file_map.md
    ├── legacy_atlas.md
    ├── ecs_mapping.md
    └── devpt_log.md
### End Tree

- **Project Root:** `python/dota2/`
- **Working Directory:** `python/dota2/grok_code1/dota2_gym/` (All `pytest` and game execution occurs here).
- **Environment:** Always use `conda run -n myenv python [file]` for all executions.
- **log_file:** `./../../devpt_log.md`
- **helper_path:** `./../../../ai_agent/phoenix_helper.py`

## 1. CORE DIRECTIVES 
- Directly start implementing the instructions without making any orchestrator script.
- **Read Access:** File allowed to be read in `python/ai_agent` is `Orchestrator.md`.
- All dependencies are already installed in the environment.No need to check for them.
- Git is already initialised in the working directory. No need to do it.
- **Legacy is Reference:** The code in `grok4/` is raw material. Do not fix it; extract its math and logic.
- **View Enforcement:** Every task MUST have a `engine/view/` component. Even for logic-heavy tasks, you must implement a visual debug representation (e.g., text overlays, moving shapes).
- **Hard Gate:** You are forbidden from calling the `success` helper until the user provides the keyword: **"VISUALLY VERIFIED"**.
- **Timing:** Do not guess the duration. You must use system timestamps.

## 2. SYSTEM INITIALIZATION
Before taking any action, you must read and internalize the following files in the project_root:
- `Project_manifesto.md`: Contains the Master Project Specification. This is your "Source of Truth."
- `devpt_state.md`: Contains the development plan(checklist), archive and resume point.
- `file_map.md`: Contains the legacy directory tree. Working directory should follow same structure to organise files. 
- `ecs_mapping.md` and `legacy_atlas.md`: ECS component mapping and code atlas of legacy code.
- Verify your working directory is `python/dota2/grok_code1/dota2_gym/`.
- Initialize a counter for the loop: LOOP_ITERATION = 1

## 3. RESUME PROTOCOL (Session Startup)
Before taking any action in a new session, you MUST:
- **Task to do before resuming:** Task 1 & 2 are "Done" but Task 3 has not been properly implemented, you must RE-IMPLEMENT tests of the already implemented logic for task 3 before starting Task 4. 
- **RESUME CHECK:** Execute existing logic tests (`conda run -n myenv pytest tests/...`) to ensure the environment is functional. 
- **State Intent:** Summarize your "Recovered Mental Context" to the user before starting work.

## 4. OPERATIONAL TDD LOOP
Execute these steps in order for every task in the development plan:

<LOOP – Run until all features in `devpt_state.md` are marked done >

### Step 1: TDD Planning and Test Generation
- **Start Timer:** Execute `python -c "import time; print(int(time.time()))" > .loop_start`.
- Read the next undone feature from `devpt_state.md`.
- **Legacy Lookup:** Search `legacy_atlas.md` and `ecs_mapping.md`. 
- **Extraction:** Read relevant functions from `grok4/dota2_gym/`. Extract math/logic snippets.
- **Test Generation:** 
    - Generate `tests/test_[feature]_logic.py` (Headless).
    - Prepend `os.environ['SDL_VIDEODRIVER'] = 'dummy'` to all test files.
    - **Requirement:** - Include a **State Determinism Test** (Save state -> Action -> Load state -> Verify equality).
- **Mandatory Visual Plan:** Write a brief description of how this feature will be rendered in Pygame (e.g., "The server state will be drawn as blue circles for clients").

### Step 2: Implementation & Verification
- **Model:** Implement NumPy-vectorized ECS logic in `engine/model/`.
- **Test:** Run `conda run -n myenv pytest tests/`. If it fails, you have **3 retries** to generate an **RCA (Root Cause Analysis)** and fix it.
- **View/Controller:** Implement/Update `engine/view/` and `engine/controller/`.

### Step 3: Manual Verification (The Gate)
- **Execution:** Run the game: `conda run -n myenv python main.py`.
- **Interaction:** STOP and tell the user: *"The game is running. Please verify [Specific Feature]. Reply with 'VISUALLY VERIFIED' to proceed or describe changes needed."*
- **Wait:** You must not proceed until the user replies. If changes are requested, refactor and repeat Step 3.

### Step 4: Documentation, Version Control & Logging
- **Calculate Duration:** 
    - Execute `python -c "import time; start=int(open('.loop_start').read()); print(int(time.time()) - start)"` to get `ACTUAL_DURATION`.
- **On Success:**
    - Mark the feature done and move sub-task notes to the `# ARCHIVE` section in `devpt_state.md`. 
    - Update `README.md` of the working directory.
    - From working directory call: `conda run -n myenv python <helper_path> success <log_file> <feature_name> <loop_iter> <ACTUAL_DURATION>`.
- **On 3rd failure:** 
    - Summarize the RCA of 3 retries.
    - From working directory call: `python <helper_path> faliure <log_file> <rca_summary> <loop_iter> <ACTUAL_DURATION>`.
    - Stop and **ESCALATE** to the user.

### Step 4: Finalization
- Increment **LOOP_ITERATION**.
- Ask user: "Proceed to next task?"

</LOOP>

## 5. PAUSE & SAVE PROTOCOL (Session Shutdown):
If the user types **"PAUSE"** or the session ends:
Generate a `RESUME_POINT` at the top of `devpt_state.md` including:
1. **Active Location:** Current file and last edited line.
2. **Test Status:** Current passing/failing tests.
3. **Mental Context:** Detailed summary of logic flow or bugs currently being solved.
4. **Immediate Next Step:** Exactly what the agent should do first upon return.

## 6. SYSTEM CONSTRAINTS & PERFORMANCE
- **Architecture:** Strict Hierarchical MVC + ECS.
- **Performance:** All updates must be vectorized with NumPy.
- **Headless First Priority:** Logic must pass `pytest` in dummy-video mode before you build the Pygame View.The Model must function 100% without Pygame initialized.
- **Network Ready:** When implementing Networking tasks, spin up a local server and client as separate processes for integration.