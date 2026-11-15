import sys

def main(argv):
    if argv[1:2] == ["add"]:
        with open("todos.txt", "a") as f:
            f.write(" ".join(argv[2:]) + "\n")
    elif argv[1:2] == ["list"]:
        try:
            print(open("todos.txt").read(), end="")
        except FileNotFoundError:
            pass

if __name__ == "__main__":
    main(sys.argv)
