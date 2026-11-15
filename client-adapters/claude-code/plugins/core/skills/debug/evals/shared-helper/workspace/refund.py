from shared import to_cents


def refund_cents(price, qty_returned, restock_fee_cents=0):
    """Refund for returned items, in cents, minus any restock fee."""
    return to_cents(price) * qty_returned - restock_fee_cents
