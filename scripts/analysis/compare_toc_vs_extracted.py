"""
Compare TOC entries vs Extracted songs for all COMPLETE books.

This identifies books where:
- TOC parsing found significantly more songs than extracted (extraction missed songs)
- TOC parsing found significantly fewer songs than extracted (TOC parsing issue)

Usage:
    py scripts/analysis/compare_toc_vs_extracted.py
"""
import json
from pathlib import Path

PROVENANCE_FILE = Path('data/analysis/v2_provenance_database.json')


def main():
    if not PROVENANCE_FILE.exists():
        print(f"ERROR: {PROVENANCE_FILE} not found")
        return

    with open(PROVENANCE_FILE) as f:
        data = json.load(f)

    # Filter to COMPLETE books
    complete = [b for b in data['songbooks'] if b['verification']['status'] == 'COMPLETE']

    print("=" * 90)
    print("TOC vs EXTRACTED SONG COMPARISON")
    print("=" * 90)
    print(f"\nTotal complete books: {len(complete)}\n")

    # Build comparison table
    rows = []
    mismatches = []

    for book in complete:
        source = book['source_pdf']['path']
        toc = book['verification'].get('toc_songs', 0)
        extracted = book['verification'].get('actual_songs', 0)
        detected = book['verification'].get('detected_songs', 0)
        matched = book['verification'].get('matched_songs', 0)

        if max(toc, extracted) > 0:
            diff = toc - extracted
            diff_pct = abs(diff) / max(toc, extracted) * 100
        else:
            diff = 0
            diff_pct = 0

        # Determine status
        if toc == 0:
            status = "NO TOC"
        elif diff_pct <= 10:
            status = "OK"
        elif diff > 0:
            status = "EXTRACT MISSED"  # TOC has more than extracted
        else:
            status = "TOC INCOMPLETE"  # Extracted has more than TOC

        rows.append([
            source[:50] + "..." if len(source) > 50 else source,
            toc,
            detected,
            matched,
            extracted,
            diff,
            f"{diff_pct:.0f}%",
            status
        ])

        if diff_pct > 10 and toc > 0:
            mismatches.append({
                'source': source,
                'toc': toc,
                'extracted': extracted,
                'diff': diff,
                'diff_pct': diff_pct,
                'status': status
            })

    # Sort by diff_pct descending
    rows.sort(key=lambda r: -float(r[6].rstrip('%')))

    # Print table header
    print(f"{'Source PDF':<55} {'TOC':>5} {'Det':>5} {'Mat':>5} {'Ext':>5} {'Diff':>5} {'%':>5} {'Status'}")
    print("-" * 95)
    for row in rows:
        print(f"{row[0]:<55} {row[1]:>5} {row[2]:>5} {row[3]:>5} {row[4]:>5} {row[5]:>5} {row[6]:>5} {row[7]}")

    # Summary
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)

    ok_count = sum(1 for r in rows if r[7] == "OK")
    no_toc_count = sum(1 for r in rows if r[7] == "NO TOC")
    extract_missed = sum(1 for r in rows if r[7] == "EXTRACT MISSED")
    toc_incomplete = sum(1 for r in rows if r[7] == "TOC INCOMPLETE")

    print(f"OK (within 10%):       {ok_count}")
    print(f"No TOC parsed:         {no_toc_count}")
    print(f"Extraction missed:     {extract_missed} (TOC > Extracted)")
    print(f"TOC incomplete:        {toc_incomplete} (Extracted > TOC)")

    if mismatches:
        print("\n" + "=" * 90)
        print("BOOKS NEEDING ATTENTION")
        print("=" * 90)

        for m in sorted(mismatches, key=lambda x: -x['diff_pct']):
            print(f"\n{m['source']}")
            print(f"  TOC: {m['toc']}, Extracted: {m['extracted']}")
            print(f"  Status: {m['status']} ({m['diff_pct']:.0f}% difference)")

            if m['status'] == "EXTRACT MISSED":
                print(f"  Action: May need full reprocessing - extraction missed ~{m['diff']} songs")
            else:
                print(f"  Action: Check TOC parsing - may have missed entries or parsed wrong pages")


if __name__ == '__main__':
    main()
