"""
Find S3 folders for books that had NO MATCH or POOR matches.
Search more broadly across all S3 folders.
"""
import csv
from collections import defaultdict

def load_matches():
    """Load matching results."""
    matches = []
    
    with open('s3_local_matches.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches.append(row)
    
    return matches

def load_s3_structure():
    """Load S3 structure from analysis."""
    s3_books = []
    
    with open('s3_output_structure_analysis.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            s3_books.append({
                'artist': row['Artist'],
                'book': row['Book'],
                'song_count': int(row['SongCount'])
            })
    
    return s3_books

def normalize_for_search(text):
    """Normalize text for fuzzy searching."""
    text = text.lower()
    # Remove common variations
    text = text.replace('_', ' ')
    text = text.replace('[', '(').replace(']', ')')
    text = text.replace('  ', ' ')
    text = text.strip()
    return text

def find_candidates(local_book, s3_books):
    """Find potential S3 candidates for a local book."""
    local_artist = local_book['local_artist']
    local_book_name = local_book['local_book']
    local_count = int(local_book['local_song_count'])
    
    # Normalize for searching
    local_artist_norm = normalize_for_search(local_artist)
    local_book_norm = normalize_for_search(local_book_name)
    
    candidates = []
    
    for s3_book in s3_books:
        s3_artist_norm = normalize_for_search(s3_book['artist'])
        s3_book_norm = normalize_for_search(s3_book['book'])
        
        # Check if artists match (loosely)
        artist_match = False
        if local_artist_norm in s3_artist_norm or s3_artist_norm in local_artist_norm:
            artist_match = True
        elif local_artist_norm.replace(' ', '') == s3_artist_norm.replace(' ', ''):
            artist_match = True
        
        if not artist_match:
            continue
        
        # Check if book names have any overlap
        local_words = set(local_book_norm.split())
        s3_words = set(s3_book_norm.split())
        
        common_words = local_words & s3_words
        
        if len(common_words) >= 2:  # At least 2 words in common
            # Calculate similarity score
            word_overlap = len(common_words) / max(len(local_words), len(s3_words))
            
            # Check song count similarity
            if local_count > 0:
                count_diff = abs(s3_book['song_count'] - local_count) / local_count
            else:
                count_diff = 1.0
            
            # Combined score
            score = word_overlap * 0.7 + (1 - min(count_diff, 1.0)) * 0.3
            
            candidates.append({
                's3_artist': s3_book['artist'],
                's3_book': s3_book['book'],
                's3_count': s3_book['song_count'],
                'score': score,
                'common_words': len(common_words),
                'word_overlap': word_overlap,
                'count_diff': count_diff
            })
    
    # Sort by score
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    return candidates[:5]  # Top 5 candidates

def main():
    print("Finding Missing Books in S3")
    print("="*80)
    
    # Load data
    matches = load_matches()
    s3_books = load_s3_structure()
    
    print(f"Loaded {len(matches)} local books")
    print(f"Loaded {len(s3_books)} S3 book folders")
    
    # Find books that need better matches
    needs_search = []
    
    for match in matches:
        quality = match['match_quality']
        if quality in ['NO MATCH', 'POOR', 'PARTIAL']:
            needs_search.append(match)
    
    print(f"\nSearching for {len(needs_search)} books with poor/no matches")
    
    # Search for each one
    results = []
    
    for local_book in needs_search:
        candidates = find_candidates(local_book, s3_books)
        
        results.append({
            'local_artist': local_book['local_artist'],
            'local_book': local_book['local_book'],
            'local_count': local_book['local_song_count'],
            'current_match': f"{local_book['s3_artist']}/{local_book['s3_book']}" if local_book['s3_artist'] else 'NONE',
            'current_quality': local_book['match_quality'],
            'candidates': candidates
        })
    
    # Print results
    print("\n" + "="*80)
    print("SEARCH RESULTS")
    print("="*80)
    
    for result in results:
        print(f"\nLocal: {result['local_artist']}/{result['local_book']}")
        print(f"       ({result['local_count']} songs)")
        print(f"Current: {result['current_match']} ({result['current_quality']})")
        
        if result['candidates']:
            print(f"\nPotential S3 matches:")
            for i, cand in enumerate(result['candidates'], 1):
                print(f"  {i}. {cand['s3_artist']}/{cand['s3_book']}")
                print(f"     Score: {cand['score']:.2f}, Songs: {cand['s3_count']}, Common words: {cand['common_words']}")
        else:
            print("  ** NO CANDIDATES FOUND **")
    
    # Save to CSV for review
    with open('missing_books_candidates.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'local_artist', 'local_book', 'local_count',
            'current_match', 'current_quality',
            'candidate_1', 'score_1', 'count_1',
            'candidate_2', 'score_2', 'count_2',
            'candidate_3', 'score_3', 'count_3',
            'selected_match', 'notes'
        ])
        
        for result in results:
            row = [
                result['local_artist'],
                result['local_book'],
                result['local_count'],
                result['current_match'],
                result['current_quality']
            ]
            
            # Add up to 3 candidates
            for i in range(3):
                if i < len(result['candidates']):
                    cand = result['candidates'][i]
                    row.extend([
                        f"{cand['s3_artist']}/{cand['s3_book']}",
                        f"{cand['score']:.2f}",
                        cand['s3_count']
                    ])
                else:
                    row.extend(['', '', ''])
            
            row.extend(['', ''])  # selected_match, notes
            writer.writerow(row)
    
    print("\n" + "="*80)
    print(f"Saved search results to: missing_books_candidates.csv")
    print("="*80)
    print("\nPlease review this file and:")
    print("1. Check the candidate matches")
    print("2. Select the correct match in 'selected_match' column")
    print("3. Add notes if needed")
    print("4. Save the file")

if __name__ == '__main__':
    main()
