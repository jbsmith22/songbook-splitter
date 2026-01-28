#!/usr/bin/env python3
"""
PDF Splitter - Reads manifest JSON files and splits PDFs into individual songs.
No API required - just local file operations.

Usage:
    python split_from_manifest.py                    # Process all manifests in current folder
    python split_from_manifest.py manifest.json     # Process single manifest
    python split_from_manifest.py --recursive       # Process all manifests in folder tree
"""

import json
import os
import sys
from pathlib import Path
from pypdf import PdfReader, PdfWriter


def split_pdf_from_manifest(manifest_path: str) -> dict:
    """Split a PDF based on a manifest file."""
    print(f"\n{'='*60}")
    print(f"Processing: {manifest_path}")
    print('='*60)
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    source_pdf = manifest['source_pdf']
    output_dir = manifest['output_dir']
    songs = manifest['songs']
    
    print(f"Source: {source_pdf}")
    print(f"Output: {output_dir}")
    print(f"Songs: {len(songs)}")
    
    if not os.path.exists(source_pdf):
        print(f"ERROR: Source PDF not found: {source_pdf}")
        return {"success": False, "error": f"Source not found: {source_pdf}"}
    
    os.makedirs(output_dir, exist_ok=True)
    
    reader = PdfReader(source_pdf)
    total_pages = len(reader.pages)
    print(f"PDF has {total_pages} pages")
    
    results = []
    
    for song in songs:
        title = song['title']
        start_page = song['start_page']
        end_page = song['end_page']
        filename = song['output_filename']
        
        writer = PdfWriter()
        
        for page_num in range(start_page - 1, end_page):
            if page_num < total_pages:
                writer.add_page(reader.pages[page_num])
            else:
                print(f"  WARNING: Page {page_num + 1} out of range for {title}")
        
        output_path = os.path.join(output_dir, filename)
        
        # Handle duplicates
        if os.path.exists(output_path):
            base, ext = os.path.splitext(output_path)
            counter = 2
            while os.path.exists(f"{base} ({counter}){ext}"):
                counter += 1
            output_path = f"{base} ({counter}){ext}"
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        page_count = end_page - start_page + 1
        results.append({"title": title, "pages": page_count, "output": output_path})
        print(f"  ✓ {filename} ({page_count} pages)")
    
    return {"success": True, "songs_created": len(results), "results": results}


def find_manifests(directory: str, recursive: bool = False) -> list:
    """Find all manifest JSON files."""
    path = Path(directory)
    if recursive:
        return list(path.rglob("*_manifest.json"))
    else:
        return list(path.glob("*_manifest.json"))


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--recursive":
            directory = sys.argv[2] if len(sys.argv) > 2 else "."
            manifests = find_manifests(directory, recursive=True)
        elif sys.argv[1].endswith('.json'):
            manifests = [Path(sys.argv[1])]
        else:
            manifests = find_manifests(sys.argv[1])
    else:
        manifests = find_manifests(".")
    
    if not manifests:
        print("No manifest files found.")
        print("Usage:")
        print("  python split_from_manifest.py                    # Current folder")
        print("  python split_from_manifest.py manifest.json     # Single file")
        print("  python split_from_manifest.py --recursive path  # Recursive search")
        return
    
    print(f"Found {len(manifests)} manifest(s)")
    
    total_songs = 0
    successful = 0
    
    for manifest_path in manifests:
        result = split_pdf_from_manifest(str(manifest_path))
        if result.get("success"):
            successful += 1
            total_songs += result.get("songs_created", 0)
    
    print(f"\n{'='*60}")
    print(f"COMPLETE: {successful}/{len(manifests)} books processed")
    print(f"Total songs created: {total_songs}")
    print('='*60)


if __name__ == "__main__":
    main()
