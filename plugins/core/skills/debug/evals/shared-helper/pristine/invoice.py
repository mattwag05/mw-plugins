from shared import to_cents


def total_cents(lines):
    """lines: list of (price_string, quantity). Returns the invoice total in cents."""
    return sum(to_cents(price) * qty for price, qty in lines)
