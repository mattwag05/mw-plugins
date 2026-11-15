def monthly_total(entries):
    """entries: list of (day, amount). Returns the sum of amounts."""
    return sum(amount for _, amount in entries)
