"""Summarize the matching results by quality."""
import pandas as pd

print('S3 MATCHING RESULTS BY QUALITY')
print('='*80)

for quality in ['PERFECT', 'EXCELLENT', 'GOOD', 'PARTIAL', 'POOR', 'NO_MATCH']:
    filename = f's3_matches_{quality.lower()}.csv'
    df = pd.read_csv(filename)
    
    print(f'\n{quality} ({len(df)} matches) - {filename}')
    print('-'*80)
    
    if quality == 'PERFECT':
        print('All local songs found in S3 with exact title match')
        print('\nSample entries (first 5):')
        for idx, row in df.head(5).iterrows():
            print(f'  {row["local_artist"]} / {row["local_book"]} ({row["local_count"]}) -> {row["s3_book"]} ({row["s3_count"]})')
    
    elif quality == 'EXCELLENT':
        print('95%+ songs match, counts within 5%')
        print('\nAll entries:')
        for idx, row in df.iterrows():
            print(f'  {row["local_artist"]} / {row["local_book"]} ({row["local_count"]}) -> {row["s3_book"]} ({row["s3_count"]}) - {row["match_pct"]} match')
    
    elif quality == 'GOOD':
        print('90%+ songs match, counts within 10%')
        print('\nAll entries:')
        for idx, row in df.iterrows():
            print(f'  {row["local_artist"]} / {row["local_book"]} ({row["local_count"]}) -> {row["s3_book"]} ({row["s3_count"]}) - {row["match_pct"]} match')
    
    elif quality == 'PARTIAL':
        print('80%+ songs match')
        print('\nAll entries:')
        for idx, row in df.iterrows():
            print(f'  {row["local_artist"]} / {row["local_book"]} ({row["local_count"]}) -> {row["s3_book"]} ({row["s3_count"]}) - {row["match_pct"]} match, {row["local_only"]} missing')
    
    elif quality == 'POOR':
        print('<80% songs match - likely wrong match or different book')
        print(f'\nShowing first 10 of {len(df)}:')
        for idx, row in df.head(10).iterrows():
            print(f'  {row["local_artist"]} / {row["local_book"]} ({row["local_count"]}) -> {row["s3_book"]} ({row["s3_count"]}) - {row["common_songs"]} common')
    
    elif quality == 'NO_MATCH':
        print('No S3 folder found - may need reprocessing')
        print('\nAll entries:')
        for idx, row in df.iterrows():
            print(f'  {row["local_artist"]} / {row["local_book"]} ({row["local_count"]} songs)')

print('\n' + '='*80)
print('CSV FILES CREATED:')
print('='*80)
print('  s3_matches_perfect.csv    - 473 matches (84.0%)')
print('  s3_matches_excellent.csv  -   8 matches (1.4%)')
print('  s3_matches_good.csv       -   4 matches (0.7%)')
print('  s3_matches_partial.csv    -  15 matches (2.7%)')
print('  s3_matches_poor.csv       -  52 matches (9.2%)')
print('  s3_matches_no_match.csv   -  11 matches (2.0%)')
print('\nTotal: 563 local books')
