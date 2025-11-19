import re


def factorial(n: int) -> int:
    """Calculate factorial of a non-negative integer using recursion."""
    if not isinstance(n, int) or n < 0:
        raise ValueError("Input must be a non-negative integer")
    return 1 if n <= 1 else n * factorial(n - 1)


def fibonacci(n: int) -> list[int]:
    """Generate Fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence[:n]


def count_vowels(s: str) -> int:
    """Count number of vowels (a,e,i,o,u) in a string (case-insensitive)."""
    vowels = "aeiou"
    return sum(1 for char in s.lower() if char in vowels)


def count_words(text: str) -> int:
    """Count the number of words in a string."""
    if not text.strip():
        return 0
    return len(text.split())


def validate_email(email: str) -> bool:
    """Validate if a string is a properly formatted email address."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
