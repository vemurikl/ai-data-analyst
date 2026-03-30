import pandas as pd


def format_number(n: int | float) -> str:
    """Format large numbers with commas for display."""
    return f"{n:,}"


def get_memory_usage(df: pd.DataFrame) -> str:
    """Return human-readable memory usage of a DataFrame."""
    bytes_used = df.memory_usage(deep=True).sum()
    if bytes_used < 1024:
        return f"{bytes_used} B"
    elif bytes_used < 1024 ** 2:
        return f"{bytes_used / 1024:.1f} KB"
    else:
        return f"{bytes_used / 1024 ** 2:.1f} MB"