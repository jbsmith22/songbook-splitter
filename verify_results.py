"""
Verify the pipeline results match our expected mapping.
"""
import json

# Load the actual results
with open("page_mapping_result.json", "r") as f:
    results = json.load(f)

# Expected mapping from our analysis
expected = [
    {"song": "Big Shot", "toc_page": 10, "expected_pdf_index": 2},
    {"song": "Honesty", "toc_page": 19, "expected_pdf_index": 10},
    {"song": "My Life", "toc_page": 25, "expected_pdf_index": 15},
    {"song": "Zanzibar", "toc_page": 33, "expected_pdf_index": 22},
    {"song": "Stiletto", "toc_page": 40, "expected_pdf_index": 29},
    {"song": "Rosalinda's Eyes", "toc_page": 46, "expected_pdf_index": 34},
    {"song": "Half A Mile Away", "toc_page": 52, "expected_pdf_index": 40},
    {"song": "Until The Night", "toc_page": 60, "expected_pdf_index": 47},
    {"song": "52nd Street", "toc_page": 68, "expected_pdf_index": 55},
]

print("=" * 80)
print("VERIFICATION: Expected vs Actual Results")
print("=" * 80)
print()
print(f"{'Song':<25} {'TOC Page':>8} {'Expected':>10} {'Actual':>10} {'Status':>10}")
print("-" * 80)

all_correct = True
for exp in expected:
    # Find matching result
    actual = None
    for loc in results["song_locations"]:
        if exp["song"].upper() in loc["song_title"].upper() or loc["song_title"].upper() in exp["song"].upper():
            actual = loc
            break
    
    if actual:
        status = "✓ CORRECT" if actual["pdf_index"] == exp["expected_pdf_index"] else "✗ WRONG"
        if actual["pdf_index"] != exp["expected_pdf_index"]:
            all_correct = False
        print(f"{exp['song']:<25} {exp['toc_page']:>8} {exp['expected_pdf_index']:>10} {actual['pdf_index']:>10} {status:>10}")
    else:
        print(f"{exp['song']:<25} {exp['toc_page']:>8} {exp['expected_pdf_index']:>10} {'NOT FOUND':>10} {'✗ MISSING':>10}")
        all_correct = False

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total songs expected: {len(expected)}")
print(f"Total songs found: {results['samples_verified']}")
print(f"Confidence: {results['confidence']}")
print()

if all_correct:
    print("🎉 SUCCESS! All 9 songs found at the correct PDF indices!")
else:
    print("⚠ Some songs were not found at the expected indices.")
