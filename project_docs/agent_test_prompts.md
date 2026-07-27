# Agent Tool Test Prompts

# Prompt 1 
Give short details of functions get_counter_argument and index_graph

---

## 1. Orientation (get_workspace_info + list_files + read_file)
```
Check if file temp/dummy/fibo/fibonacci.py exists.
```

## 2. Basic edit_file with unique old_string
```
In fibonacci.py, rename the function fibonacci_iterative to fib.
```

## 3. Edit with surrounding context (uniqueness)
```
In fibonacci.py, change the docstring to say "Returns the first n Fibonacci numbers." instead of "Generates".
```

## 4. write_to_file create mode
```
Create a new file temp/dummy/fibo/test_fibonacci.py with a simple pytest test for the fibonacci function.
```

## 6. Multi-step workflow with plan
```
In temp/dummy/fabo/fibonacci.py:
1. Add a new function fibonacci_recursive(n) that returns the nth Fibonacci number recursively
2. Add a docstring to the new function
3. Update the example usage to call both functions
4. Verify the file looks correct by reading it
```
