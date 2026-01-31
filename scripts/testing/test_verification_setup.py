#!/usr/bin/env python3
"""
Test script to verify the PDF verification setup is working correctly.
Tests Ollama connection, PDF rendering, and basic functionality.
"""

import sys
from pathlib import Path
import requests

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from verify_pdf_splits import (
    OllamaVisionClient,
    PDFRenderer,
    PROCESSED_SONGS_PATH,
    CACHE_PATH,
    OLLAMA_MODEL
)

def test_ollama_connection():
    """Test Ollama is running and model is available."""
    print("=" * 80)
    print("TEST 1: Ollama Connection")
    print("=" * 80)
    
    client = OllamaVisionClient()
    
    # Check if Ollama is running
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        print("✓ Ollama is running")
    except Exception as e:
        print(f"✗ Ollama is NOT running: {e}")
        return False
    
    # Check if model is available
    if client.check_availability():
        print(f"✓ Model '{OLLAMA_MODEL}' is available")
        return True
    else:
        print(f"✗ Model '{OLLAMA_MODEL}' is NOT available")
        return False


def test_pdf_access():
    """Test access to ProcessedSongs directory."""
    print("\n" + "=" * 80)
    print("TEST 2: PDF Access")
    print("=" * 80)
    
    if not PROCESSED_SONGS_PATH.exists():
        print(f"✗ ProcessedSongs path does not exist: {PROCESSED_SONGS_PATH}")
        return False
    
    print(f"✓ ProcessedSongs path exists: {PROCESSED_SONGS_PATH}")
    
    # Find a sample PDF
    pdfs = list(PROCESSED_SONGS_PATH.rglob("*.pdf"))
    if not pdfs:
        print("✗ No PDFs found in ProcessedSongs")
        return False
    
    print(f"✓ Found {len(pdfs)} PDFs")
    print(f"  Sample: {pdfs[0].relative_to(PROCESSED_SONGS_PATH)}")
    
    return True, pdfs[0]


def test_cache_access():
    """Test access to cache directory."""
    print("\n" + "=" * 80)
    print("TEST 3: Cache Directory")
    print("=" * 80)
    
    try:
        CACHE_PATH.mkdir(parents=True, exist_ok=True)
        print(f"✓ Cache directory accessible: {CACHE_PATH}")
        
        # Check disk space
        import shutil
        stats = shutil.disk_usage(CACHE_PATH)
        free_gb = stats.free / (1024**3)
        print(f"✓ Free space: {free_gb:.2f} GB")
        
        if free_gb < 5:
            print(f"⚠ Warning: Less than 5 GB free space")
        
        return True
    except Exception as e:
        print(f"✗ Cannot access cache directory: {e}")
        return False


def test_pdf_rendering(sample_pdf: Path):
    """Test PDF rendering."""
    print("\n" + "=" * 80)
    print("TEST 4: PDF Rendering")
    print("=" * 80)
    
    try:
        renderer = PDFRenderer()
        
        print(f"Rendering first page of: {sample_pdf.name}")
        image_path = renderer.render_page(sample_pdf, 0)
        
        if image_path and image_path.exists():
            size_kb = image_path.stat().st_size / 1024
            print(f"✓ Page rendered successfully")
            print(f"  Cached at: {image_path}")
            print(f"  Size: {size_kb:.2f} KB")
            return True, image_path
        else:
            print("✗ Failed to render page")
            return False, None
            
    except Exception as e:
        print(f"✗ Error rendering PDF: {e}")
        return False, None


def test_ollama_vision(image_path: Path):
    """Test Ollama vision analysis."""
    print("\n" + "=" * 80)
    print("TEST 5: Ollama Vision Analysis")
    print("=" * 80)
    
    try:
        client = OllamaVisionClient()
        
        prompt = "Look at this image. Is this a sheet music page? Answer YES or NO."
        
        print("Sending image to Ollama for analysis...")
        print("(This may take a few seconds with GPU acceleration)")
        
        import time
        start = time.time()
        response = client.analyze_image(image_path, prompt, timeout=30)
        elapsed = time.time() - start
        
        if 'error' in response:
            print(f"✗ Error from Ollama: {response['error']}")
            return False
        
        answer = response.get('response', '').strip()
        print(f"✓ Ollama responded in {elapsed:.2f} seconds")
        print(f"  Response: {answer[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error calling Ollama: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PDF VERIFICATION SETUP TEST")
    print("=" * 80 + "\n")
    
    # Test 1: Ollama connection
    if not test_ollama_connection():
        print("\n❌ FAILED: Ollama is not available")
        print("Please start Ollama and ensure llama3.2-vision:11b is installed")
        sys.exit(1)
    
    # Test 2: PDF access
    result = test_pdf_access()
    if isinstance(result, tuple):
        success, sample_pdf = result
        if not success:
            print("\n❌ FAILED: Cannot access PDFs")
            sys.exit(1)
    else:
        print("\n❌ FAILED: Cannot access PDFs")
        sys.exit(1)
    
    # Test 3: Cache access
    if not test_cache_access():
        print("\n❌ FAILED: Cannot access cache directory")
        sys.exit(1)
    
    # Test 4: PDF rendering
    result = test_pdf_rendering(sample_pdf)
    if isinstance(result, tuple):
        success, image_path = result
        if not success:
            print("\n❌ FAILED: Cannot render PDFs")
            sys.exit(1)
    else:
        print("\n❌ FAILED: Cannot render PDFs")
        sys.exit(1)
    
    # Test 5: Ollama vision
    if not test_ollama_vision(image_path):
        print("\n❌ FAILED: Ollama vision not working")
        sys.exit(1)
    
    # All tests passed
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)
    print("\nYou're ready to run the verification!")
    print("\nNext steps:")
    print("  1. Run pilot: py verify_pdf_splits.py --pilot")
    print("  2. Review results in verification_results/")
    print("  3. Run full verification: py verify_pdf_splits.py --full")
    print()


if __name__ == "__main__":
    main()
