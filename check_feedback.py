import json
f = open('review_feedback_2026-01-29.json')
d = json.load(f)
print(f'Reviews: {len(d.get("reviews", {}))}')
print(f'Split instructions: {len(d.get("splitInstructions", {}))}')
print(f'Correct types: {len(d.get("correctTypes", {}))}')
print(f'\nFirst few split instructions:')
for k, v in list(d.get("splitInstructions", {}).items())[:3]:
    print(f'  {k}: {len(v)} splits')
