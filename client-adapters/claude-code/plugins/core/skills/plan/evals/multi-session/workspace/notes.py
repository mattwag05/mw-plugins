import json, sys

def load():
    return json.load(open("notes.json"))

if __name__ == "__main__":
    print(load())
