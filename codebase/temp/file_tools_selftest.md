Run a sequential self-test of your basic file tools. Do all of it inside a dedicated temporary directory `codebase/temp/tooltest/` so nothing touches real project files. Use the tools in the order below, adapting your choices to whatever each tool actually returns.

1. `execute_command` — create the test directory `codebase/temp/tooltest`. Confirm the command's actual result.
2. `write_to_file` — create `codebase/temp/tooltest/fibonacci.py` with a small valid Python file implementing a recursive `fib(n)` function and printing `fib(10)`.
3. `write_to_file` — modify `codebase/temp/tooltest/fibonacci.py` to instead print `fib(20)` (use the appropriate mode).
4. `write_to_file` — create a second file `codebase/temp/tooltest/notes.md` with a few lines of notes that include the word `fibonacci`.
5. `read_file` — read `codebase/temp/tooltest/fibonacci.py` and check whether the content is what you expect.
6. `edit_file` — update `codebase/temp/tooltest/fibonacci.py` so it prints `fib(20)` via an exact single replacement (`old_string`/`new_string`).
7. `edit_file` — use the `edits` array in one call on `codebase/temp/tooltest/notes.md` to apply two changes: fix a typo and append a line.
8. `read_file` — re-read `codebase/temp/tooltest/fibonacci.py` and confirm whether your edit took effect.
9. `list_files` — list `codebase/temp/tooltest/` flat, and again recursively. Check what it returns.
10. `glob_search` — find files matching `codebase/temp/tooltest/**/*.py`. Note what matches.
11. `grep_search` — search inside `codebase/temp/tooltest` for a term present in `fibonacci.py` (e.g. `fib`), and note what files match.
12. `execute_command` — run `codebase/temp/tooltest/fibonacci.py` and note the printed value.
13. `todo` — record a short plan titled `file tool self-test` describing what you are testing.
14. `execute_command` — attempt clean up of `codebase/temp/tooltest`.

For each step, report the tool's actual result. If any tool returns an error or is blocked, say which step failed and what was returned, then decide the most sensible way to continue on your own. At the end give a concise per-tool pass/fail summary based purely on what the tools actually returned.