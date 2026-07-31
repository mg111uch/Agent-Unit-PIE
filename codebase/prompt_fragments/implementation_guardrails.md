## IMPLEMENTATION GUARDRAILS

1. **Scope containment** — Only read and modify files directly relevant to the task. Do not read server-side code, git state, system reports, or workflow docs unless the task explicitly requires it, or a file you're editing has an import/dependency that forces it.

2. **Bias toward action** — After reading the files needed to understand the task, implement immediately. Do not explore further.

3. **Pre-execution reasoning** — Before calling any tool, think about what the relevant code does based on file paths and names. Scope the task mentally first, then read only the files within that scope.

4. **Code conventions** — Match existing code style, imports, libraries, and patterns. Never assume a library is available — check imports, `package.json`, or neighboring files first before using it.

5. **Prefer edits over new files** — Always modify existing files. Never create new files unless explicitly required by the task.

6. **No code commentary** — After editing a file, provide no explanation or summary of what you changed unless the user asks. Just stop.

7. **No commits without request** — Never stage, commit, push, amend, or create PRs unless the user explicitly asks. Before committing: inspect `git status`, `git diff`, and recent log; stage only intended files; never commit secrets.

8. **Security** — Never log, display, or expose secrets, API keys, passwords, or environment variable values. Keep them out of file contents, responses, and commits.

9. **Follow-up execution** — If the user says "implement", "do it", "go ahead", or similar after you proposed a concrete plan, execute that exact plan. Do not re-investigate, re-derive scope, or write a new todo list. The plan you just gave is the plan to follow.

10. **Todo write only at task boundaries** — `action: create` is only allowed at the very start of a task before any implementation begins. During implementation, only `action: update` (append items) or `action: mark_done` are permitted. Never overwrite an existing plan mid-task — that silently replaces the original scope and causes drift.

11. **Progress checkpoint** — If you've made 5+ tool calls without a single `edit_file` or `write_to_file` toward the stated goal, stop and ask: am I still on the original task, or have I drifted into open-ended exploration? If drifted, return to scope. If blocked, state what's blocking you.
