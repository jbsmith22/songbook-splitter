#!/usr/bin/env python3
"""Test the new parsing logic."""

# Simulate Ollama response
raw_text = """1. Yes
2. A Matter Of Trust
3. No
4. No"""

print("Raw response:")
print(raw_text)
print("\n" + "=" * 80)

# Parse it
lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
answers = []
for line in lines:
    answer = line.split('.', 1)[-1].strip() if '.' in line else line.strip()
    answers.append(answer)

while len(answers) < 4:
    answers.append("UNKNOWN")

has_title = answers[0].upper() in ['YES', 'Y', 'TRUE']
title_text = answers[1] if answers[1].upper() not in ['NO', 'N', 'NONE', 'FALSE', 'UNKNOWN'] else None
is_first = answers[2].upper() in ['YES', 'Y', 'TRUE']
is_continuation = answers[3].upper() in ['YES', 'Y', 'TRUE']

print("Parsed results:")
print(f"  has_title: {has_title}")
print(f"  title_text: {title_text}")
print(f"  is_first_page: {is_first}")
print(f"  is_continuation: {is_continuation}")
print("\nExpected:")
print("  has_title: True")
print("  title_text: A Matter Of Trust")
print("  is_first_page: False")
print("  is_continuation: False")
