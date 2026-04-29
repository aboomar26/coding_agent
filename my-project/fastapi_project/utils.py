def trim_text(s: str) -> str:
    """Remove leading and trailing whitespace."""
    return s.strip()

def uppercase_text(s: str) -> str:
    """Convert string to uppercase."""
    return s.upper()

def char_count(s: str) -> int:
    """Return number of characters in the string."""
    return len(s)

def word_count(s: str) -> int:
    """Return number of words (split by whitespace)."""
    # split on any whitespace, filter empty strings
    return len([w for w in s.split() if w])
