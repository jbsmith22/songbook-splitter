"""Show weak matches that need manual review."""
import pandas as pd

df = pd.read_csv('s3_matches_by_name_similarity.csv')

print('NAME SIMILARITY MATCHING RESULTS')
print('='*80)
print(f'Total: {len(df)}')
print(f'  EXCELLENT (90%+): {len(df[df["quality"]=="EXCELLENT"])}')
print(f'  GOOD (80-90%): {len(df[df["quality"]=="GOOD"])}')
print(f'  FAIR (70-80%): {len(df[df["quality"]=="FAIR"])}')
print(f'  WEAK (<70%): {len(df[df["quality"]=="WEAK"])}')
print()
print('WEAK MATCHES (need manual review):')
print('-'*80)
weak = df[df['quality']=='WEAK']
for idx, row in weak.iterrows():
    print(f'{row["local_artist"]} / {row["local_book"]} ({row["local_count"]} songs)')
    print(f'  -> {row["s3_artist"]} / {row["s3_book"]}')
    print(f'  Similarity: {row["similarity_pct"]}')
    print()

print('FAIR MATCH (review recommended):')
print('-'*80)
fair = df[df['quality']=='FAIR']
for idx, row in fair.iterrows():
    print(f'{row["local_artist"]} / {row["local_book"]} ({row["local_count"]} songs)')
    print(f'  -> {row["s3_artist"]} / {row["s3_book"]}')
    print(f'  Similarity: {row["similarity_pct"]}')
    print()

print('='*80)
print(f'TOTAL GOOD MATCHES: {len(df[df["quality"].isin(["EXCELLENT","GOOD"])])} / {len(df)}')
print('='*80)
