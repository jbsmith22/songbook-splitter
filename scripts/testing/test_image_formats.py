#!/usr/bin/env python3
"""
Test PNG vs JPG for rendering and Ollama performance.
"""

import time
import base64
from pathlib import Path
import fitz
import requests

# Test with a sample PDF
PROCESSED_SONGS_PATH = Path("C:/Work/AWSMusic/ProcessedSongs")
CACHE_PATH = Path("D:/ImageCache/format_test")
CACHE_PATH.mkdir(parents=True, exist_ok=True)

# Find a sample PDF
pdfs = list(PROCESSED_SONGS_PATH.rglob("*.pdf"))
sample_pdf = pdfs[0]

print(f"Testing with: {sample_pdf.name}")
print("=" * 80)

# Test PNG rendering
print("\n1. PNG Rendering...")
start = time.time()
doc = fitz.open(sample_pdf)
page = doc[0]
zoom = 300 / 72
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)
png_path = CACHE_PATH / "test_page.png"
pix.save(str(png_path))
doc.close()
png_render_time = time.time() - start
png_size = png_path.stat().st_size

print(f"   Time: {png_render_time:.3f}s")
print(f"   Size: {png_size / 1024:.1f} KB")

# Test JPG rendering
print("\n2. JPG Rendering (quality=90)...")
start = time.time()
doc = fitz.open(sample_pdf)
page = doc[0]
zoom = 300 / 72
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)
jpg_path = CACHE_PATH / "test_page.jpg"
pix.save(str(jpg_path), "jpeg", jpg_quality=90)
doc.close()
jpg_render_time = time.time() - start
jpg_size = jpg_path.stat().st_size

print(f"   Time: {jpg_render_time:.3f}s")
print(f"   Size: {jpg_size / 1024:.1f} KB")
print(f"   Size reduction: {(1 - jpg_size/png_size)*100:.1f}%")

# Test base64 encoding time
print("\n3. Base64 Encoding...")
start = time.time()
with open(png_path, 'rb') as f:
    png_b64 = base64.b64encode(f.read()).decode('utf-8')
png_encode_time = time.time() - start

start = time.time()
with open(jpg_path, 'rb') as f:
    jpg_b64 = base64.b64encode(f.read()).decode('utf-8')
jpg_encode_time = time.time() - start

print(f"   PNG: {png_encode_time:.3f}s ({len(png_b64)} chars)")
print(f"   JPG: {jpg_encode_time:.3f}s ({len(jpg_b64)} chars)")

# Test Ollama inference time
print("\n4. Ollama Inference Time...")
prompt = "Look at this sheet music. Is there a song title visible? Answer YES or NO."

print("   Testing PNG...")
start = time.time()
response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'llava:7b',
        'prompt': prompt,
        'images': [png_b64],
        'stream': False
    },
    timeout=30
)
png_inference_time = time.time() - start
print(f"   PNG inference: {png_inference_time:.3f}s")

print("   Testing JPG...")
start = time.time()
response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'llava:7b',
        'prompt': prompt,
        'images': [jpg_b64],
        'stream': False
    },
    timeout=30
)
jpg_inference_time = time.time() - start
print(f"   JPG inference: {jpg_inference_time:.3f}s")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"PNG Total: {png_render_time + png_encode_time + png_inference_time:.3f}s")
print(f"JPG Total: {jpg_render_time + jpg_encode_time + jpg_inference_time:.3f}s")
print(f"Speedup: {((png_render_time + png_encode_time + png_inference_time) / (jpg_render_time + jpg_encode_time + jpg_inference_time)):.2f}x")
print(f"\nFor 42,000 pages:")
print(f"  PNG: {(png_render_time + png_encode_time + png_inference_time) * 42000 / 3600:.1f} hours")
print(f"  JPG: {(jpg_render_time + jpg_encode_time + jpg_inference_time) * 42000 / 3600:.1f} hours")
