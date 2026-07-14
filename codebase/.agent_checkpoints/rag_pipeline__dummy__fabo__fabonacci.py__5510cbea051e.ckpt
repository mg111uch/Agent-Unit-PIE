def fibonacci_iterative(n):
    """Generates the first n Fibonacci numbers."""
    if n <= 0:
        return []
    if n == 1:
        return [0]
    
    sequence = [0, 1]
    # Start from the 3rd term (index 2) up to n
    while len(sequence) < n:
        next_fib = sequence[-1] + sequence[-2]
        sequence.append(next_fib)
    return sequence

# Example usage:
n_terms = 10
print(f"Fibonacci sequence for the first {n_terms} terms: {fib(n_terms)}") 
# Output: Fibonacci sequence for the first 10 terms: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
