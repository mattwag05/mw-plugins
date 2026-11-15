import sys

def items():
    return open("todos.txt").read().splitlines()

if __name__ == "__main__":
    if sys.argv[1:2] == ["list"]:
        print("\n".join(items()))
