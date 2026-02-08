#!/usr/bin/env python3
"""
Comprehensive Songbook Quality Validation Demonstration

This script shows EXACTLY what will be validated for each songbook:
1. TOC accuracy vs actual pages
2. Song title accuracy
3. Page range correctness
4. Song boundary detection
5. Output file completeness
6. Metadata consistency
"""
import json
from pathlib import Path

def validate_songbook_comprehensive(book_id, artist, book_name):
    """
    Perform comprehensive validation showing detailed checks.
    """
    print(f"\n{'='*100}")
    print(f"COMPREHENSIVE VALIDATION: {artist} - {book_name}")
    print(f"Book ID: {book_id}")
    print(f"{'='*100}\n")

    # Load artifacts
    toc_data = json.load(open('temp_cream_toc.json'))
    page_analysis = json.load(open('temp_cream_page_analysis.json'))
    output_files = json.load(open('temp_cream_output.json'))

    toc_entries = toc_data.get('entries', [])
    songs = page_analysis.get('songs', [])
    outputs = output_files.get('output_files', [])

    print(f" DATA SUMMARY")
    print(f"   TOC Entries Found: {len(toc_entries)}")
    print(f"   Songs Analyzed: {len(songs)}")
    print(f"   Output Files Created: {len(outputs)}")
    print()

    # ========== VALIDATION CHECK 1: TOC vs Extracted Songs ==========
    print(f" CHECK 1: TOC ACCURACY")
    print(f"   Purpose: Verify that TOC entries match the songs we extracted")
    print(f"   Method: Compare TOC count vs songs count, check for missing/extra songs")
    print()

    if len(toc_entries) == len(songs):
        print(f"    PASS: TOC count ({len(toc_entries)}) matches songs extracted ({len(songs)})")
    else:
        print(f"    WARNING: TOC has {len(toc_entries)} entries but extracted {len(songs)} songs")
        print(f"   Action needed: Visual inspection to determine if discrepancy is valid")

    # Sample TOC entries
    print(f"\n   Sample TOC Entries (first 3):")
    for i, entry in enumerate(toc_entries[:3], 1):
        title = entry.get('song_title', 'N/A')
        page = entry.get('page_number', 'N/A')
        print(f"      {i}. \"{title}\"  Page {page}")

    # ========== VALIDATION CHECK 2: Song Title Accuracy ==========
    print(f"\n CHECK 2: SONG TITLE ACCURACY")
    print(f"   Purpose: Verify extracted song titles match what's on the actual pages")
    print(f"   Method: For each song, would examine first page image to confirm title")
    print()

    for i, song in enumerate(songs[:3], 1):
        title = song.get('title', 'N/A')
        pages = song.get('pages', [])
        page_range = f"{pages[0]}-{pages[-1]}" if pages else "N/A"

        print(f"   Song {i}: \"{title}\"")
        print(f"      Pages: {page_range}")
        print(f"      What I would check:")
        print(f"          Load page {pages[0] if pages else 'N/A'} image from PDF")
        print(f"          Use vision to read the song title at top of page")
        print(f"          Compare with extracted title: \"{title}\"")
        print(f"          Verify title is not truncated or misread")
        print()

    # ========== VALIDATION CHECK 3: Page Range Accuracy ==========
    print(f" CHECK 3: PAGE RANGE ACCURACY")
    print(f"   Purpose: Verify songs are assigned correct page ranges")
    print(f"   Method: Check that page ranges don't overlap and cover expected pages")
    print()

    # Check for overlaps
    all_pages_used = []
    overlaps_found = False

    for i, song in enumerate(songs):
        pages = song.get('pages', [])
        title = song.get('title', 'Unknown')

        for page in pages:
            if page in all_pages_used:
                overlaps_found = True
                print(f"    WARNING: Page {page} is assigned to multiple songs")
                print(f"      Including: \"{title}\"")

        all_pages_used.extend(pages)

    if not overlaps_found:
        print(f"    PASS: No page overlaps detected")

    # Check for gaps
    if all_pages_used:
        all_pages_used_sorted = sorted(set(all_pages_used))
        gaps = []
        for i in range(len(all_pages_used_sorted) - 1):
            if all_pages_used_sorted[i+1] - all_pages_used_sorted[i] > 1:
                gap_start = all_pages_used_sorted[i] + 1
                gap_end = all_pages_used_sorted[i+1] - 1
                gaps.append((gap_start, gap_end))

        if gaps:
            print(f"\n    Page gaps found (likely TOC/intro pages):")
            for gap_start, gap_end in gaps:
                print(f"      Pages {gap_start}-{gap_end}: Not assigned to any song")
        else:
            print(f"\n    PASS: No unexpected page gaps")

    # ========== VALIDATION CHECK 4: Song Boundaries ==========
    print(f"\n CHECK 4: SONG BOUNDARY DETECTION")
    print(f"   Purpose: Verify songs aren't cut mid-song or merged incorrectly")
    print(f"   Method: Check last page of each song and first page of next song")
    print()

    for i in range(min(2, len(songs) - 1)):
        current_song = songs[i]
        next_song = songs[i + 1]

        current_title = current_song.get('title', 'Unknown')
        next_title = next_song.get('title', 'Unknown')
        current_last_page = current_song.get('pages', [])[-1] if current_song.get('pages') else None
        next_first_page = next_song.get('pages', [])[0] if next_song.get('pages') else None

        if current_last_page and next_first_page:
            print(f"   Boundary Check {i+1}:")
            print(f"      Current song: \"{current_title}\" ends on page {current_last_page}")
            print(f"      Next song: \"{next_title}\" starts on page {next_first_page}")

            if next_first_page - current_last_page == 1:
                print(f"       Sequential pages - boundary looks correct")
            elif next_first_page == current_last_page + 1:
                print(f"       Consecutive pages")
            else:
                print(f"       Gap of {next_first_page - current_last_page - 1} pages")

            print(f"      What I would check with vision:")
            print(f"          View page {current_last_page}: Verify it shows end of song (final measures, ending)")
            print(f"          View page {next_first_page}: Verify it shows start of new song (title, intro)")
            print()

    # ========== VALIDATION CHECK 5: Output File Completeness ==========
    print(f" CHECK 5: OUTPUT FILE COMPLETENESS")
    print(f"   Purpose: Verify every song has a corresponding output PDF file")
    print(f"   Method: Check that output_files.json entries match songs")
    print()

    if len(outputs) == len(songs):
        print(f"    PASS: All {len(songs)} songs have output files")
    else:
        print(f"    WARNING: {len(songs)} songs but {len(outputs)} output files")

    # Check that each output has required fields
    missing_fields = []
    for output in outputs:
        if not output.get('song_title'):
            missing_fields.append("Missing song_title")
        if not output.get('output_uri'):
            missing_fields.append("Missing output_uri")

    if missing_fields:
        print(f"    Some outputs have missing fields: {set(missing_fields)}")
    else:
        print(f"    All output files have required metadata")

    # ========== VALIDATION CHECK 6: Metadata Consistency ==========
    print(f"\n CHECK 6: METADATA CONSISTENCY")
    print(f"   Purpose: Verify metadata is consistent across all artifacts")
    print(f"   Method: Check artist/book name consistency, file naming conventions")
    print()

    # Check output file naming
    inconsistent_naming = []
    for output in outputs[:3]:
        uri = output.get('output_uri', '')
        song_title = output.get('song_title', '')

        # Output URIs should contain artist name
        if artist.replace(' ', '') not in uri.replace(' ', ''):
            inconsistent_naming.append(f"URI doesn't contain artist: {uri}")

    if inconsistent_naming:
        print(f"    Naming inconsistencies found:")
        for issue in inconsistent_naming:
            print(f"      {issue}")
    else:
        print(f"    Output file naming is consistent")

    # ========== FINAL SUMMARY ==========
    print(f"\n{'='*100}")
    print(f"VALIDATION SUMMARY FOR: {artist} - {book_name}")
    print(f"{'='*100}")

    checks_passed = 0
    total_checks = 6

    # Simplified pass/fail logic for demo
    if len(toc_entries) == len(songs):
        checks_passed += 1
    if not overlaps_found:
        checks_passed += 1
    if len(outputs) == len(songs):
        checks_passed += 1
    if not inconsistent_naming:
        checks_passed += 1

    # Always count title and boundary checks as needing visual verification
    print(f"\n Automated Checks Passed: {checks_passed}/4")
    print(f" Visual Verification Needed: 2/6 (Song titles, Song boundaries)")
    print(f"\n NEXT STEPS FOR FULL VALIDATION:")
    print(f"   1. Extract page images from source PDF: s3://jsmith-input/{artist}/{book_name}.pdf")
    print(f"   2. Use vision to validate first page of each song matches extracted title")
    print(f"   3. Use vision to validate song boundaries (check ending/starting pages)")
    print(f"   4. Use vision to spot-check random pages within songs for content accuracy")
    print(f"   5. Generate validation report with screenshots of any issues found")

if __name__ == '__main__':
    # Demo validation for Cream
    validate_songbook_comprehensive(
        'v2-04f34885c435fac6-2',
        'Cream',
        'Cream Complete'
    )
