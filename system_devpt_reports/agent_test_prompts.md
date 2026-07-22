# Agent Tool Test Prompts

These prompts exercise the new capabilities implemented in the agent harness.
Target file: `codebase/rag_pipeline/dummy/fabo/fibonacci.py`

---

# Prompt 1 
Give short details of functions get_counter_argument and index_graph

---

## 1. Orientation (get_workspace_info + list_files + read_file)

```
Start by figuring out where you are. What files exist under rag_pipeline/dummy? Read fibonacci.py and tell me what it does.
Read fibonacci.py under rag_pipeline/dummy and tell me what it does.
```

**Tests:** `get_workspace_info` → `list_files("rag_pipeline/dummy")` → `read_file("rag_pipeline/dummy/fabo/fibonacci.py")`

---

## 2. Basic edit_file with unique old_string

```
In rag_pipeline/dummy/fabo/fibonacci.py, rename the function fibonacci_iterative to fib.
```

**Tests:** `read_file` → `edit_file` with unique old_string. The edit tool must reject 0 or >1 matches and the model must succeed on the first try since `fibonacci_iterative` is unique.

---

## 3. Edit with surrounding context (uniqueness)

```
In rag_pipeline/dummy/fabo/fibonacci.py, change the docstring to say "Returns the first n Fibonacci numbers." instead of "Generates".
```

**Tests:** `edit_file` with enough surrounding context — `old_string` should include `"""Generates the first n Fibonacci numbers."""` to ensure uniqueness (just `Generates` would match in other contexts if they existed).

---

## 4. write_to_file create mode

```
Create a new file rag_pipeline/dummy/fabo/test_fibonacci.py with a simple pytest test for the fibonacci function. Then verify it exists by reading it.
```

**Tests:** `write_to_file` (mode=create) → `read_file` to confirm. Tests that `write_to_file` now resolves paths correctly and that `read_file` returns line-numbered output.

---

## 5. write_to_file overwrite mode (full rewrite)

```
I have changed file name fibonacci.py to fabonacci.py. Now the fabonacci.py file has a typo in its directory name (fabo should be fibo) and the function name doesn't match the filename. Rewrite the entire file to fix both: rename the file's content to use proper naming. Make the fibonacci function work for the edge case n=0 correctly (currently it does, but add a clarifying comment). Overwrite the file with the improved version.
```

**Tests:** `read_file` → `write_to_file` (mode=overwrite) → optionally `read_file` to verify. Tests full-file replacement.

---

## 6. Multi-step workflow with plan

```
In rag_pipeline/dummy/fabo/fibonacci.py:
1. Add a new function fibonacci_recursive(n) that returns the nth Fibonacci number recursively
2. Add a docstring to the new function
3. Update the example usage to call both functions
4. Verify the file looks correct by reading it
```

**Tests:** Full multi-step workflow using `read_file` → `edit_file` (multiple edits) → `read_file`. The model should plan before acting.

---

## 7. Error recovery (bad path)

```
Read the file rag_pipeline/dummy/fibo/fibonacci.py and tell me if it exists.
```

**Tests:** The failure breaker and actionable error messages. The path `fibo/fibonacci.py` doesn't exist — `read_file` should return an error listing nearby files in the `fabo/` directory so the model can self-correct in one step.
