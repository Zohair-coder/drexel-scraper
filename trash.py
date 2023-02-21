import json

with open("data.json") as f:
    data = json.load(f)

m = 0
for key, value in data.items():
    m = max(m, len(value["course_title"]))

print(m)
