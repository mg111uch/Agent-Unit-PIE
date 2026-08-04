# PROBLEM STATEMENT — Interactive Question Modal Never Appears (Loop Stuck)

## 1. Summary

When a user asks the agent to ask them questions (e.g. `"ask me 3 questions on
indian history"`), the real model (openrouter `inclusionai/ling-3.0-flash:free`)
DOES now correctly call the `ask_user_question` tool (we added system-prompt
guidance + a stronger tool description/schema to make this happen). The server
log shows the tool call is forwarded to the frontend:

```
[LLM call #1] openrouter/inclusionai/ling-3.0-flash:free
[WS-DIAG] forwarding tool_call: tool=ask_user_question step=1 call_id='call_2c288314ee2c4c1b97b1bb78'
```

After that: **the question modal never appears on the frontend**, the assistant
bubble stays on "Thinking…", and the loop blocks with **no further LLM calls**
and **no error** in the terminal or browser.

Expected: the backend emits a `question` WebSocket message, the Vue app renders
the QuestionPanel (inline card), the user clicks options → answers →
`question_answer` WS message → backend unblocks → loop continues → final answer.

## 2. Facts established so far

- **Backend plumbing is PROVEN working** for the `question` flow via
  `/tmp/opencode/smoke_ws_question.py` (real uvicorn 0.35.0 + starlette +
  websockets client, fake orchestrator): client receives
  `['status','llm_call','llm_call','tool_call','question']`, answering via
  `question_answer` yields a `final`, and `cancel` also works. This used
  **simple string options** (`["3","4","5"]`).
- **The real run's payload is richer**: each question is an object with
  `question`, `header`, `options` as **objects** `{label, description}`, plus an
  extra `multi_select: false` key. The ws handler forwards `questions` verbatim,
  and the frontend QuestionPanel renders `optLabel`/`optDescription`, so this
  should be supported — but it has **not** been verified in a real browser.
- **The full frontend stack has NOT been verified in a browser yet.** A headless
  Chrome test (`/tmp/opencode/browser_question_test.py`) was written to do this
  but **hangs with no output** (see §6). This hang itself is a clue/blocker.
- The frontend wiring *by inspection* looks correct: `store.js` `case 'question'`
  sets `AgentStore.pendingQuestions = msg.questions`; `index.html:113` renders
  `<question-panel v-if="store.pendingQuestions">`; `AgentChat.js` exposes
  `onQuestionSubmit` → `store.submitQuestionAnswer` → sends `question_answer`.
- The assistant bubble keeps showing "Thinking" because `isThinking` is only
  cleared by `stream_chunk`/`final`/`error` — NOT by `question` or `tool_call`.
- The scroll watch in `AgentChat.js` only observes `messages.length` and
  `currentToolCall` (not `pendingQuestions`), so the panel is never scrolled
  into view when it appears.

## 3. What needs to be solved

1. **Root-cause why the modal does not render in a real browser** (or why the
   browser test harness hangs). Determine empirically, not by inspection, which
   link is broken: (a) `question` WS message not reaching the page, (b) store
   handler failing, (c) Vue render error in QuestionPanel with the object-option
   payload, (d) panel rendered but invisible/off-screen (no auto-scroll).
2. Fix the loop-block: backend `wait_for_questions` blocks up to 300 s and the
   ws `question` branch blocks in `while True: await websocket.receive_json()`
   — if the frontend never renders/submits, the turn appears dead with no error.
3. (Recommended) Clear "Thinking" when a `question`/`tool_call` arrives, and
   auto-scroll the QuestionPanel into view (add `pendingQuestions` to the watch).

## 4. Reproduction (real model)

1. `cd codebase && conda run -n myenv python server.py` (uses real model, default
   port 8001).
2. Open `http://localhost:8001/`, hard-refresh.
3. Send: `ask me 3 questions on indian history`
4. Observe: `[WS-DIAG] forwarding tool_call ... ask_user_question` in terminal,
   then nothing. No modal, no more LLM calls, no error.
5. Check `codebase/tui_output.txt` — the run is captured there (debug dump).

Evidence transcripts:
- `codebase/condensed.txt` — the stuck run (tool_call present, no final). The
  exact `ask_user_question` tool-call payload (object options + `header` +
  `multi_select`) is in this file under "Tool Calls Raw".
- `codebase/tui_output.txt` — currently holds a LATER plain-text run (the model
  is nondeterministic: second attempt returned inline text, no tool call, and
  completed with a `final`). The stuck tool-call run is in condensed.txt.

## 5. Reproduction harness status (headless browser)

`/tmp/opencode/browser_question_test.py` — runs the REAL `agent_core.server`
(uvicorn, fake orchestrator returning the EXACT transcript tool-call payload)
and drives the real frontend in headless system Chrome (`/usr/bin/google-chrome`,
playwright sync API). **Current symptom: the script hangs with zero output** even
with `python -u`. It was run via `conda run -n myenv python -u ...` (conda buffers
output). Not yet clear whether the hang is at `browser.launch`, `page.goto`, or
CDN script load. Internet is available (CDNs return 302). Playwright's own
chromium is NOT installed; system Chrome is used via `executable_path`.
This harness must be made to run — it is the fastest path to a definitive answer.

## 6. Context files needed to solve the issue

### Backend (all under `codebase/`)
- `agent_core/server/ws_handler.py` — WS loop; question branch (~L317–340):
  sends `question`, blocks on `question_answer`/`cancel`; tool_call forward
  (~L348–356); main cancel/drain loop (~L252–298); worker thread (~L218–248).
- `agent_core/loop/stepper.py` — single-tool path (~L261–289) and multi-tool
  path (~L163–196): yields `tool_call` then `question` BEFORE blocking.
- `agent_core/loop/_helpers.py` — `_prepare_interactive_tool` (~L73–109);
  `_QUESTION_TOOLS` (~L39).
- `agent_core/tools/question_ops.py` — `register_questions` / `wait_for_questions`
  (300 s timeout) / `resolve_all_questions` / `cancel_questions`.
- `agent_core/loop/engine.py` — generator event loop (~L194–314).
- `agent_core/tools/__init__.py` — `ask_user_question` registration (~L181–187):
  description + schema (options = string OR `{label, description}`; optional
  `header`).
- `agent_core/server/__init__.py` — serves `codebase/frontend` at `/` via
  `NoCacheStaticFiles` (~L163–173); `SYSTEM_PROMPT`, `iter_agent_events`,
  `get_or_create_session`.

### Frontend (all under `codebase/frontend/`)
- `store.js` — state + `handleMessage`; `case 'question'` (~L113–115); `isBusy`.
- `websocket.js` — `sendCancel`, `submitQuestionAnswer`.
- `index.html` — panel mount (~L113); QuestionPanel template (~L153–182); scripts
  (~L230–237, Vue/marked/DOMPurify from CDN).
- `app.js` — dynamic component loading + app mount.
- `components/AgentChat.js` — scroll watch (~L75–77), `onQuestionSubmit` (~L81).
- `components/QuestionPanel.js` — option-object rendering, multi-question paging.

### Prompt (affects whether the model calls the tool)
- `prompt_fragments/response_contract.md` — INTERACTIVE QUESTIONS section (forces
  `ask_user_question` for Q&A; reads every turn, mtime-cached).

### Test harnesses (referenced above; already in the repo `/tmp/opencode/`)
- `/tmp/opencode/smoke_ws_question.py` — PASSING backend smoke (simple options).
- `/tmp/opencode/browser_question_test.py` — full-stack headless-browser test,
  currently HANGING (must be fixed first for empirical diagnosis).

## 7. Open hypotheses (ranked)

1. **Frontend receives `question` but the panel render fails or is invisible.**
   A JS error in QuestionPanel/tool-call-card with the object-option payload, or
   the panel renders below the fold with no auto-scroll.
2. **The `question` WS message never reaches the page** (backend race or a
   message silently dropped between the tool_call forward and the question send).
3. **Browser-test harness bug** (not the app): conda-run buffering + chrome
   launch/goto hang masked everything. Fix harness first, then re-test the app.

## 8. Minimal acceptance criteria

- Headless-browser test (`/tmp/opencode/browser_question_test.py`) completes:
  panel renders (header `Maurya Empire`, `Question 1 of 3`, option labels),
  answering all 3 questions drives the flow to a final answer.
- Real-model reproduction: modal appears, answers work, loop continues, final
  answer arrives; no deadlock; terminal log shows a resumed `[LLM call #2]`.
