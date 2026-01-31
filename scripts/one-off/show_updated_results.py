"""Show updated results after downloading partial files."""
import pandas as pd

df = pd.read_csv('s3_local_exact_matches_v2.csv')

print('UPDATED RESULTS AFTER DOWNLOADING PARTIAL FILES:')
print('='*80)
print(f'PERFECT:   {len(df[df["quality"]=="PERFECT"])} (was 473, +14)')
print(f'EXCELLENT: {len(df[df["quality"]=="EXCELLENT"])}')
print(f'GOOD:      {len(df[df["quality"]=="GOOD"])}')
print(f'PARTIAL:   {len(df[df["quality"]=="PARTIAL"])} (was 15, -14)')
print(f'POOR:      {len(df[df["quality"]=="POOR"])}')
print(f'NO_MATCH:  {len(df[df["quality"]=="NO_MATCH"])}')
print()
print(f'CONFIRMED (PERFECT+EXCELLENT+GOOD): {len(df[df["quality"].isin(["PERFECT","EXCELLENT","GOOD"])])}')
print()
print('Remaining PARTIAL match:')
partial = df[df['quality']=='PARTIAL']
for idx, row in partial.iterrows():
    print(f'  {row["local_artist"]} / {row["local_book"]} ({row["local_count"]}) -> {row["s3_book"]} ({row["s3_count"]})')
    print(f'    Match: {row["match_pct"]}, Common: {row["common_songs"]}, Local only: {row["local_only"]}, S3 only: {row["s3_only"]}')
