#!/usr/bin/env python3
"""
Diagnose why PDFs can't be renamed - find the conflicting files.
"""

import re
from pathlib import Path

def normalize_name(name):
    """Apply title case normalization."""
    acronyms = ['PVG', 'SATB', 'MTI', 'PC', 'RSC', 'TYA', 'TV', 'DVD', 'CD', 'II', 'III', 'IV', 'V', 'VI']
    words = name.split()
    result = []
    
    for word in words:
        if word.upper() in acronyms:
            result.append(word.upper())
        elif re.match(r'^[IVX]+$', word.upper()) and len(word) <= 4:
            result.append(word.upper())
        elif word.isdigit():
            result.append(word)
        elif '_' in word:
            result.append(word)
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)

def has_lowercase_words(name):
    """Check if name has lowercase words that should be capitalized."""
    lowercase_words = [' and ', ' of ', ' the ', ' in ', ' for ', ' from ', ' with ', ' to ', ' at ', ' by ']
    return any(word in name for word in lowercase_words)

print("=" * 80)
print("DIAGNOSING RENAME CONFLICTS")
print("=" * 80)
print()

# Find PDFs with lowercase words
sheet_music_path = Path("SheetMusic")
conflicts = []

for pdf_file in sheet_music_path.rglob("*.pdf"):
    if pdf_file.name.startswith('.'):
        continue
    
    old_name = pdf_file.stem
    
    if not has_lowercase_words(old_name):
        continue
    
    new_name = normalize_name(old_name)
    
    if old_name == new_name:
        continue
    
    new_path = pdf_file.parent / f"{new_name}.pdf"
    
    # Check if destination exists
    if new_path.exists():
        conflicts.append({
            'old_file': pdf_file,
            'old_name': old_name,
            'new_name': new_name,
            'new_path': new_path,
            'conflict': True
        })
    else:
        conflicts.append({
            'old_file': pdf_file,
            'old_name': old_name,
            'new_name': new_name,
            'new_path': new_path,
            'conflict': False
        })

print(f"Found {len(conflicts)} files to analyze")
print()

# Show conflicts
conflict_count = sum(1 for c in conflicts if c['conflict'])
no_conflict_count = sum(1 for c in conflicts if not c['conflict'])

print(f"Files with conflicts: {conflict_count}")
print(f"Files without conflicts: {no_conflict_count}")
print()

if conflict_count > 0:
    print("=" * 80)
    print("CONFLICTS (destination already exists)")
    print("=" * 80)
    print()
    
    for i, item in enumerate([c for c in conflicts if c['conflict']], 1):
        print(f"{i}. CONFLICT:")
        print(f"   Current file: {item['old_file'].relative_to(sheet_music_path)}")
        print(f"   Wants to rename to: {item['new_name']}.pdf")
        print(f"   But this already exists: {item['new_path'].relative_to(sheet_music_path)}")
        
        # Check if they're the same file (case-only difference)
        if item['old_file'].resolve() == item['new_path'].resolve():
            print(f"   → SAME FILE (case-only difference on case-insensitive filesystem)")
        else:
            print(f"   → DIFFERENT FILES (true conflict)")
        print()

if no_conflict_count > 0:
    print("=" * 80)
    print("NO CONFLICTS (safe to rename)")
    print("=" * 80)
    print()
    
    for i, item in enumerate([c for c in conflicts if not c['conflict']], 1):
        print(f"{i}. {item['old_name']}.pdf → {item['new_name']}.pdf")
