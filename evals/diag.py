import json

print("--- Résultats du run ---")
r = json.load(open("report.json", encoding="utf-8"))["results"]
for x in r:
    refused = "ne trouve pas cette information" in x["answer"].lower()
    print(x["id"], "| cat=", x["category"], "| refused=", refused, "| answer=", x["answer"][:80])

print("\n--- expected_source dans le dataset ---")
for l in open("golden_dataset.jsonl", encoding="utf-8"):
    d = json.loads(l)
    print(d["id"], "|", repr(d["expected_source"]))