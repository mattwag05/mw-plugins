import json

MAX_TOKENS = 1024


def build_request(prompt):
    body = {
        "model": "nimbus-flash",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        # Nimbus's documented switch to turn reasoning off.
        "reasoning": {"hide": True},
    }
    return json.dumps(body)
