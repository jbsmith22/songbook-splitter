#!/usr/bin/env python3
"""
Re-render oversized images at lower DPI to meet Bedrock limits.
"""

from pathlib import Path
from PIL import Image

CACHE_PATH = Path("S:/SlowImageCache/pdf_verification")
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_DIMENSION = 8000  # pixels

def check_and_fix_images():
    """Find and fix oversized images."""
    
    print("Scanning for oversized images...")
    
    all_images = list(CACHE_PATH.glob("**/*.jpg"))
    print(f"Found {len(all_images)} total images")
    
    oversized = []
    oversized_dims = []
    
    for img_path in all_images:
        # Check file size
        size = img_path.stat().st_size
        if size > MAX_IMAGE_SIZE:
            oversized.append((img_path, size))
            continue
        
        # Check dimensions
        try:
            img = Image.open(img_path)
            if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
                oversized_dims.append((img_path, img.width, img.height))
        except Exception as e:
            print(f"Error checking {img_path}: {e}")
    
    print(f"\nFound {len(oversized)} images over 5MB")
    print(f"Found {len(oversized_dims)} images over {MAX_DIMENSION}px")
    
    if not oversized and not oversized_dims:
        print("✓ All images are within limits")
        return
    
    # Fix oversized files
    for img_path, size in oversized:
        print(f"\nFixing {img_path.name} ({size / 1024 / 1024:.1f}MB)")
        try:
            img = Image.open(img_path)
            
            # Reduce quality until under limit
            for quality in [80, 75, 70, 65, 60]:
                img.save(img_path, "JPEG", quality=quality, optimize=True)
                new_size = img_path.stat().st_size
                if new_size < MAX_IMAGE_SIZE:
                    print(f"  ✓ Reduced to {new_size / 1024 / 1024:.1f}MB at quality {quality}")
                    break
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Fix oversized dimensions
    for img_path, width, height in oversized_dims:
        print(f"\nFixing {img_path.name} ({width}x{height}px)")
        try:
            img = Image.open(img_path)
            
            # Calculate new size
            scale = MAX_DIMENSION / max(width, height)
            new_width = int(width * scale * 0.95)  # 95% to be safe
            new_height = int(height * scale * 0.95)
            
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img_resized.save(img_path, "JPEG", quality=85, optimize=True)
            
            new_size = img_path.stat().st_size
            print(f"  ✓ Resized to {new_width}x{new_height}px ({new_size / 1024 / 1024:.1f}MB)")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✓ Done fixing images")


if __name__ == "__main__":
    check_and_fix_images()
