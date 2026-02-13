def fibonacci(n):
    """
    Calculates the nth Fibonacci number.

    Args:
        n (int): The position in the Fibonacci sequence (non-negative integer).

    Returns:
        int: The nth Fibonacci number.
             Returns 0 if n is 0, 1 if n is 1 or 2.
             Returns -1 for invalid input (negative n).
    """
    if n < 0:
        return -1  # Invalid input
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

def fibonacci_recursive(n):
    """
    Calculates the nth Fibonacci number using recursion.
    Note: This can be inefficient for large n due to repeated calculations.

    Args:
        n (int): The position in the Fibonacci sequence (non-negative integer).

    Returns:
        int: The nth Fibonacci number.
             Returns 0 if n is 0, 1 if n is 1 or 2.
             Returns -1 for invalid input (negative n).
    """
    if n < 0:
        return -1
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

if __name__ == "__main__":
    print("Fibonacci sequence (iterative):")
    for i in range(15):
        print(f"fibonacci({i}) = {fibonacci(i)}")

    print("\nFibonacci sequence (recursive - for smaller numbers):")
    for i in range(10):
        print(f"fibonacci_recursive({i}) = {fibonacci_recursive(i)}")

    print("\nTesting with specific values:")
    print(f"fibonacci(0) = {fibonacci(0)}")
    print(f"fibonacci(1) = {fibonacci(1)}")
    print(f"fibonacci(2) = {fibonacci(2)}")
    print(f"fibonacci(10) = {fibonacci(10)}")
    print(f"fibonacci(20) = {fibonacci(20)}")
    print(f"fibonacci(-5) = {fibonacci(-5)}") # Invalid input