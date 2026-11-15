def parse(text):
    return [w.strip() for w in text.split(",") if w.strip()]


def dedupe(words):
    seen = {}
    for w in words:
        seen[w.lower()] = w
    return list(seen.values())


def render(text):
    return " | ".join(dedupe(parse(text)))


def first_word(text):
    return dedupe(parse(text))[0]
