def shipping_cost(weight_kg, zone):
    if zone == "local":
        if weight_kg <= 1:
            return 5.0
        elif weight_kg <= 5:
            return 5.0 + (weight_kg - 1) * 2.0
        else:
            return 5.0 + 4 * 2.0 + (weight_kg - 5) * 1.5
    elif zone == "national":
        if weight_kg <= 1:
            return 8.0
        elif weight_kg <= 5:
            return 8.0 + (weight_kg - 1) * 3.0
        else:
            return 8.0 + 4 * 3.0 + (weight_kg - 5) * 2.5
    elif zone == "intl":
        if weight_kg <= 1:
            return 20.0
        elif weight_kg <= 5:
            return 20.0 + (weight_kg - 1) * 6.0
        else:
            return 20.0 + 4 * 6.0 + (weight_kg - 5) * 5.0
    else:
        raise ValueError("unknown zone: " + zone)
