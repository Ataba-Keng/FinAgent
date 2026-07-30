import json

r = json.load(open("report.json", encoding="utf-8"))["results"]
for x in r:
    print(x["id"], "| cat=", x["category"], "| correct_refusal=", x["correct_refusal"], "| grounded=", x["grounded"])
    print("  answer :", x["answer"])
    print()