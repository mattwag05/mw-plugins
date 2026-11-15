"""Cart pricing."""

DISCOUNT_RATE = 0.10
THRESHOLD = 100.0


def subtotal(prices):
    return sum(prices)


def total(prices):
    s = subtotal(prices)
    if s >= THRESHOLD:
        return round(s * (1 - DISCOUNT_RATE), 2)
    return round(s, 2)
