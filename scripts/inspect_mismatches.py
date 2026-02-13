"""Quick script to render flagged mismatch pages for visual inspection."""
import sys
from pathlib import Path
from PIL import Image
import fitz
import imagehash

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
CACHE_DIR = Path('S:/SlowImageCache/pdf_verification_v3')
INSPECT_DIR = PROJECT_ROOT / 'data' / 'v3_verification' / 'inspect'
INSPECT_DIR.mkdir(parents=True, exist_ok=True)

CASES = [
    # (artist, book, song_pdf_name_fragment, song_page_idx, source_page_num, label)
    ("John Lennon", "Greatest Hits", "Love", 1, 48, "lennon_love_p1_vs_48"),
    ("John Lennon", "Greatest Hits", "Love", 5, 52, "lennon_love_p5_vs_52"),
    ("John Lennon", "Greatest Hits", "Imagine", 0, 24, "lennon_imagine_p0_vs_24"),
    ("Crowded House", "Together Alone", "Kare Kare", 4, 10, "crowded_karekare_p4_vs_10"),
    ("Crowded House", "Together Alone", "Fingers Of Love", 5, 36, "crowded_fingers_p5_vs_36"),
    ("Fleetwood Mac", "Deluxe Anthology", "World Turning", 0, 14, "fleetwood_worldturning_p0_vs_14"),
    ("Fleetwood Mac", "Deluxe Anthology", "Blue Letter", 0, 46, "fleetwood_blueletter_p0_vs_46"),
    ("Billy Joel", "Complete Vol 1", "Half A Mile Away", 7, 257, "billyjoel_halfmile_p7_vs_257"),
    ("Monkees", "Greatest Hits", "Listen To The Band", 3, 29, "monkees_listen_p3_vs_29"),
    ("Bruce Springsteen", "Born To Run", "Thunder Road", 9, 12, "bruce_thunder_p9_vs_12"),
]


def find_song_pdf(output_dir, fragment):
    """Find a song PDF by partial name match."""
    book_dir = output_dir
    if not book_dir.exists():
        return None
    for f in book_dir.iterdir():
        if f.suffix.lower() == '.pdf' and fragment.lower() in f.name.lower():
            return f
    return None


def render_page(doc, page_num, dpi=150):
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    page = doc[page_num]
    pix = page.get_pixmap(matrix=mat)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


for artist, book, song_frag, song_page, source_page, label in CASES:
    print(f"\n--- {label} ---")

    # Find and render song page
    song_pdf = find_song_pdf(OUTPUT_DIR / artist / book, song_frag)
    if not song_pdf:
        print(f"  Song PDF not found for '{song_frag}' in {artist}/{book}")
        continue

    print(f"  Song PDF: {song_pdf.name}")
    doc = fitz.open(song_pdf)
    if song_page >= len(doc):
        print(f"  Song page {song_page} out of range (has {len(doc)} pages)")
        doc.close()
        continue

    song_img = render_page(doc, song_page, dpi=150)
    doc.close()

    # Load source cache image
    cache_path = CACHE_DIR / artist / book / f"page_{source_page:04d}.jpg"
    if not cache_path.exists():
        print(f"  Cache image not found: {cache_path}")
        continue

    source_img = Image.open(cache_path).convert('RGB')

    # Compute hashes at multiple sizes for comparison
    for hs in [8, 12, 16]:
        d_song = imagehash.dhash(song_img, hash_size=hs)
        d_source = imagehash.dhash(source_img, hash_size=hs)
        dist = d_song - d_source
        print(f"  dHash({hs}): distance={dist}")

    p_song = imagehash.phash(song_img, hash_size=16)
    p_source = imagehash.phash(source_img, hash_size=16)
    print(f"  pHash(16): distance={p_song - p_source}")

    # Save both for visual inspection
    song_out = INSPECT_DIR / f"{label}_song.jpg"
    source_out = INSPECT_DIR / f"{label}_source.jpg"
    song_img.save(str(song_out), quality=95)
    source_img.save(str(source_out), quality=95)
    print(f"  Saved: {song_out.name}, {source_out.name}")

print(f"\nInspection images saved to: {INSPECT_DIR}")
