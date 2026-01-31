"""
Review and confirm S3-to-local matches.
Identify books that need manual review or are missing.
"""
import csv
from collections import defaultdict

def load_matches():
    """Load the matching results."""
    matches = []
    
    with open('s3_local_matches.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches.append(row)
    
    return matches

def categorize_matches(matches):
    """Categorize matches by quality."""
    categories = {
        'PERFECT': [],
        'EXCELLENT': [],
        'GOOD': [],
        'PARTIAL': [],
        'POOR': [],
        'NO MATCH': []
    }
    
    for match in matches:
        quality = match['match_quality']
        categories[quality].append(match)
    
    return categories

def main():
    print("Match Review and Confirmation")
    print("="*80)
    
    matches = load_matches()
    categories = categorize_matches(matches)
    
    # Summary
    print("\nMATCH QUALITY SUMMARY:")
    print("-"*80)
    for quality, items in categories.items():
        print(f"{quality:15} {len(items):4} books")
    
    # Review EXCELLENT matches (need confirmation)
    print("\n" + "="*80)
    print("EXCELLENT MATCHES (95%+) - NEED CONFIRMATION")
    print("="*80)
    print("These are very close matches but not 100%. Please review:")
    print()
    
    for match in categories['EXCELLENT']:
        print(f"\nLocal:  {match['local_artist']}/{match['local_book']}")
        print(f"        ({match['local_song_count']} songs)")
        print(f"S3:     {match['s3_artist']}/{match['s3_book']}")
        print(f"        ({match['s3_song_count']} songs)")
        print(f"Match:  {float(match['match_pct'])*100:.1f}% ({match['matches']} matches)")
        if int(match['local_only']) > 0:
            print(f"        {match['local_only']} songs only in local")
        if int(match['s3_only']) > 0:
            print(f"        {match['s3_only']} songs only in S3")
    
    # Review GOOD matches (need confirmation)
    print("\n" + "="*80)
    print("GOOD MATCHES (80-95%) - NEED CONFIRMATION")
    print("="*80)
    print("These match well but have some differences. Please review:")
    print()
    
    for match in categories['GOOD'][:20]:  # Show first 20
        print(f"\nLocal:  {match['local_artist']}/{match['local_book']}")
        print(f"        ({match['local_song_count']} songs)")
        print(f"S3:     {match['s3_artist']}/{match['s3_book']}")
        print(f"        ({match['s3_song_count']} songs)")
        print(f"Match:  {float(match['match_pct'])*100:.1f}% ({match['matches']} matches)")
        if int(match['local_only']) > 0:
            print(f"        {match['local_only']} songs only in local")
        if int(match['s3_only']) > 0:
            print(f"        {match['s3_only']} songs only in S3")
    
    if len(categories['GOOD']) > 20:
        print(f"\n... and {len(categories['GOOD']) - 20} more GOOD matches")
    
    # Review PARTIAL matches (likely wrong)
    print("\n" + "="*80)
    print("PARTIAL MATCHES (50-80%) - LIKELY WRONG")
    print("="*80)
    print("These are weak matches. May need manual investigation:")
    print()
    
    for match in categories['PARTIAL'][:10]:  # Show first 10
        print(f"\nLocal:  {match['local_artist']}/{match['local_book']}")
        print(f"        ({match['local_song_count']} songs)")
        print(f"S3:     {match['s3_artist']}/{match['s3_book']}")
        print(f"        ({match['s3_song_count']} songs)")
        print(f"Match:  {float(match['match_pct'])*100:.1f}% ({match['matches']} matches)")
    
    if len(categories['PARTIAL']) > 10:
        print(f"\n... and {len(categories['PARTIAL']) - 10} more PARTIAL matches")
    
    # Review POOR matches (definitely wrong)
    print("\n" + "="*80)
    print("POOR MATCHES (<50%) - DEFINITELY WRONG")
    print("="*80)
    print("These are bad matches. Need to find correct S3 folder:")
    print()
    
    for match in categories['POOR'][:10]:  # Show first 10
        print(f"\nLocal:  {match['local_artist']}/{match['local_book']}")
        print(f"        ({match['local_song_count']} songs)")
        print(f"S3:     {match['s3_artist']}/{match['s3_book']}")
        print(f"        ({match['s3_song_count']} songs)")
        print(f"Match:  {float(match['match_pct'])*100:.1f}% ({match['matches']} matches)")
    
    if len(categories['POOR']) > 10:
        print(f"\n... and {len(categories['POOR']) - 10} more POOR matches")
    
    # Review NO MATCH (missing from S3)
    print("\n" + "="*80)
    print("NO MATCH - MISSING FROM S3")
    print("="*80)
    print("These local books have no matching S3 folder:")
    print()
    
    for match in categories['NO MATCH']:
        print(f"\nLocal:  {match['local_artist']}/{match['local_book']}")
        print(f"        ({match['local_song_count']} songs)")
        print(f"        ** NO S3 FOLDER FOUND **")
    
    # Save review files
    print("\n" + "="*80)
    print("SAVING REVIEW FILES")
    print("="*80)
    
    # Save books needing review
    needs_review = categories['EXCELLENT'] + categories['GOOD'] + categories['PARTIAL'] + categories['POOR'] + categories['NO MATCH']
    
    with open('matches_need_review.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'local_artist', 'local_book', 'local_song_count',
            's3_artist', 's3_book', 's3_song_count',
            'match_pct', 'match_quality', 'matches', 'local_only', 's3_only',
            'status', 'notes'
        ])
        writer.writeheader()
        
        for match in needs_review:
            # Create a clean dict with only the fields we want
            clean_match = {
                'local_artist': match['local_artist'],
                'local_book': match['local_book'],
                'local_song_count': match['local_song_count'],
                's3_artist': match['s3_artist'],
                's3_book': match['s3_book'],
                's3_song_count': match['s3_song_count'],
                'match_pct': match['match_pct'],
                'match_quality': match['match_quality'],
                'matches': match['matches'],
                'local_only': match['local_only'],
                's3_only': match['s3_only'],
                'status': 'NEEDS_REVIEW',
                'notes': ''
            }
            writer.writerow(clean_match)
    
    print(f"\nSaved {len(needs_review)} books needing review to: matches_need_review.csv")
    print("\nPlease review this file and:")
    print("1. Confirm EXCELLENT and GOOD matches are correct")
    print("2. Find correct S3 folders for PARTIAL, POOR, and NO MATCH")
    print("3. Update 'status' column to 'CONFIRMED' when verified")
    print("4. Update 's3_artist' and 's3_book' if you find better matches")
    
    # Save confirmed matches (PERFECT only)
    with open('matches_confirmed.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'local_artist', 'local_book', 'local_song_count',
            's3_artist', 's3_book', 's3_song_count',
            'match_pct', 'match_quality'
        ])
        writer.writeheader()
        
        for match in categories['PERFECT']:
            clean_match = {
                'local_artist': match['local_artist'],
                'local_book': match['local_book'],
                'local_song_count': match['local_song_count'],
                's3_artist': match['s3_artist'],
                's3_book': match['s3_book'],
                's3_song_count': match['s3_song_count'],
                'match_pct': match['match_pct'],
                'match_quality': match['match_quality']
            }
            writer.writerow(clean_match)
    
    print(f"\nSaved {len(categories['PERFECT'])} confirmed PERFECT matches to: matches_confirmed.csv")
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Review 'matches_need_review.csv' (133 books)")
    print("2. Confirm or correct each match")
    print("3. Mark as 'CONFIRMED' when verified")
    print("4. Run 'merge_confirmed_matches.py' to combine all confirmed matches")
    print("5. Then we can proceed with cleanup")

if __name__ == '__main__':
    main()
