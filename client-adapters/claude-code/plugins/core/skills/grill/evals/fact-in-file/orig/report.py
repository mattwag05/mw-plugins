import csv

def total(path):
    return sum(int(r["amount"]) for r in csv.DictReader(open(path)))
