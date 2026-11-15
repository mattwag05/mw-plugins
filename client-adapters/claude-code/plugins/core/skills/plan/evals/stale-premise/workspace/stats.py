import argparse
import collections
import json


def count_words(path):
    with open(path, encoding="utf-8") as f:
        return collections.Counter(f.read().split())


def main(argv=None):
    ap = argparse.ArgumentParser(description="Word counts for a text file.")
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true", help="print counts as JSON")
    args = ap.parse_args(argv)
    counts = count_words(args.path)
    if args.json:
        print(json.dumps(dict(counts), sort_keys=True))
    else:
        for word, n in sorted(counts.items()):
            print(f"{word}\t{n}")


if __name__ == "__main__":
    main()
