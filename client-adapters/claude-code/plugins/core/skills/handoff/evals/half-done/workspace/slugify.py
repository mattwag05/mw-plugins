import re

def slugify(text):
    text = text.lower().strip()
    return text.replace(" ", "-")
