def to_cents(amount):
    """Convert a decimal price string like '12.34' to integer cents."""
    return int(float(amount) * 100)
