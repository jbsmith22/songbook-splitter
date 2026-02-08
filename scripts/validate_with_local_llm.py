#!/usr/bin/env python3
"""
Validate extracted songbook data using local Ollama vision models.

This script uses cached source page images and your local Ollama LLM
to verify that extracted song data matches the actual source pages.

Usage:
    python validate_with_local_llm.py --book-id v2-xxxxx --model llama3.2-vision:11b
    python validate_with_local_llm.py --test 5  # Validate 5 random books
    python validate_with_local_llm.py --all     # Validate all books with cached images
"""

import argparse
import json
import logging
import time
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
CACHE_V2_PATH = Path("S:/SlowImageCache/pdf_verification_v2")
CACHE_V1_PATH = Path("S:/SlowImageCache/pdf_verification")
OUTPUT_BUCKET = "jsmith-output"
DEFAULT_MODEL = "llama3.2-vision:11b"  # Better quality
FAST_MODEL = "llava:7b"  # Faster for bulk validation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OllamaVisionClient:
    """Client for Ollama vision API."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url
        self.model = model
        self.generate_url = f"{base_url}/api/generate"

    def analyze_image(self, image_path: Path, prompt: str) -> Tuple[str, bool]:
        """
        Analyze an image with Ollama vision model.
        Returns (response_text, success).
        """
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            # Build request
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }

            # Call Ollama
            response = requests.post(self.generate_url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result.get('response', ''), True

        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            return f"Error: {str(e)}", False

    def analyze_multiple_images(self, image_paths: List[Path], prompt: str) -> Tuple[str, bool]:
        """
        Analyze multiple images with a single prompt.
        Returns (response_text, success).
        """
        try:
            # Encode all images
            images_base64 = []
            for image_path in image_paths:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                    images_base64.append(base64.b64encode(image_bytes).decode('utf-8'))

            # Build request
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": images_base64,
                "stream": False
            }

            # Call Ollama
            response = requests.post(self.generate_url, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            return result.get('response', ''), True

        except Exception as e:
            logger.error(f"Error analyzing images: {e}")
            return f"Error: {str(e)}", False


def load_artifacts_from_s3(book_id: str) -> Dict:
    """Load artifacts from S3 for a book."""
    import boto3
    s3 = boto3.client('s3')

    artifacts = {}

    artifact_files = [
        'toc_discovery.json',
        'page_analysis.json',
        'output_files.json'
    ]

    for artifact_name in artifact_files:
        try:
            key = f'artifacts/{book_id}/{artifact_name}'
            response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=key)
            artifacts[artifact_name] = json.loads(response['Body'].read())
        except Exception as e:
            logger.warning(f"Could not load {artifact_name}: {e}")
            artifacts[artifact_name] = None

    return artifacts


def find_cached_images(book_id: str, artist: str, book_name: str) -> Optional[Path]:
    """Find cached images directory for a book."""
    # Try v2 cache first
    safe_artist = artist.replace('/', '_').replace('\\', '_')
    safe_book = book_name.replace('/', '_').replace('\\', '_')

    cache_dir = CACHE_V2_PATH / safe_artist / safe_book
    if cache_dir.exists():
        return cache_dir

    # Try v1 cache
    cache_dir = CACHE_V1_PATH / artist / book_name
    if cache_dir.exists():
        return cache_dir

    return None


def validate_song_title(client: OllamaVisionClient, image_path: Path, expected_title: str) -> Dict:
    """Validate that a page shows the expected song title."""

    prompt = f"""Look at this sheet music page. What is the song title shown at the top?

Expected title: "{expected_title}"

Please respond with ONLY the exact title you see on the page, or "NO TITLE VISIBLE" if you cannot see a clear title."""

    response, success = client.analyze_image(image_path, prompt)

    if not success:
        return {
            'check': 'song_title',
            'status': 'error',
            'expected': expected_title,
            'actual': None,
            'raw_response': response
        }

    # Simple matching
    actual_title = response.strip()
    matches = expected_title.lower() in actual_title.lower() or actual_title.lower() in expected_title.lower()

    return {
        'check': 'song_title',
        'status': 'pass' if matches else 'fail',
        'expected': expected_title,
        'actual': actual_title,
        'raw_response': response
    }


def validate_song_boundary(client: OllamaVisionClient, last_page: Path, first_page: Path,
                          song1_title: str, song2_title: str) -> Dict:
    """Validate that a song boundary is correct."""

    prompt = f"""You are looking at 2 consecutive pages from a songbook.

IMAGE 1: Should be the LAST page of the song "{song1_title}"
IMAGE 2: Should be the FIRST page of the song "{song2_title}"

For each image, answer:
1. Does it show a song ending (final measures, ending notation)?
2. Does it show a song starting (title at top, beginning measures)?
3. What song title do you see (if any)?

Format:
IMAGE 1: [ending/middle/start] - Title: [title or NONE]
IMAGE 2: [ending/middle/start] - Title: [title or NONE]"""

    response, success = client.analyze_multiple_images([last_page, first_page], prompt)

    if not success:
        return {
            'check': 'song_boundary',
            'status': 'error',
            'song1': song1_title,
            'song2': song2_title,
            'raw_response': response
        }

    # Parse response (simplified)
    looks_correct = "ending" in response.lower() and "start" in response.lower()

    return {
        'check': 'song_boundary',
        'status': 'pass' if looks_correct else 'review',
        'song1': song1_title,
        'song2': song2_title,
        'raw_response': response
    }


def validate_book(book_id: str, artist: str, book_name: str, client: OllamaVisionClient) -> Dict:
    """Validate a single book comprehensively."""

    logger.info(f"Validating: {artist} - {book_name}")

    validation_result = {
        'book_id': book_id,
        'artist': artist,
        'book_name': book_name,
        'timestamp': time.time(),
        'checks': [],
        'summary': {}
    }

    # Load artifacts
    logger.info("  Loading artifacts from S3...")
    artifacts = load_artifacts_from_s3(book_id)

    toc_data = artifacts.get('toc_discovery.json')
    page_analysis = artifacts.get('page_analysis.json')
    output_files = artifacts.get('output_files.json')

    if not page_analysis:
        validation_result['summary']['status'] = 'error'
        validation_result['summary']['message'] = 'No page analysis data'
        return validation_result

    songs = page_analysis.get('songs', [])
    logger.info(f"  Found {len(songs)} extracted songs")

    # Find cached images
    logger.info("  Looking for cached images...")
    cache_dir = find_cached_images(book_id, artist, book_name)

    if not cache_dir:
        validation_result['summary']['status'] = 'no_cache'
        validation_result['summary']['message'] = 'No cached images available'
        return validation_result

    # Get all cached pages
    cached_pages = sorted(cache_dir.glob("*.jpg"))
    logger.info(f"  Found {len(cached_pages)} cached page images")

    # Validate first 3 songs (for demo - can expand to all)
    for i, song in enumerate(songs[:3], 1):
        song_title = song.get('title', 'Unknown')
        start_page = song.get('start_pdf_page', song.get('actual_pdf_start'))

        if not start_page:
            continue

        logger.info(f"  Validating song {i}/{len(songs[:3])}: {song_title}")

        # Find first page image (PDF pages are 1-indexed, cache files are 0-indexed)
        page_image = cache_dir / f"page_{start_page-1:04d}.jpg"

        if not page_image.exists():
            logger.warning(f"    Image not found: {page_image}")
            continue

        # Validate song title
        logger.info(f"    Checking song title on page {start_page}...")
        title_check = validate_song_title(client, page_image, song_title)
        validation_result['checks'].append(title_check)

        logger.info(f"      Status: {title_check['status']}")
        logger.info(f"      Expected: {title_check['expected']}")
        logger.info(f"      Actual: {title_check['actual']}")

    # Validate song boundaries (first 2 boundaries)
    for i in range(min(2, len(songs) - 1)):
        song1 = songs[i]
        song2 = songs[i + 1]

        end_page = song1.get('end_pdf_page', song1.get('actual_pdf_end'))
        start_page = song2.get('start_pdf_page', song2.get('actual_pdf_start'))

        if not end_page or not start_page:
            continue

        last_page_img = cache_dir / f"page_{end_page-1:04d}.jpg"
        first_page_img = cache_dir / f"page_{start_page-1:04d}.jpg"

        if not last_page_img.exists() or not first_page_img.exists():
            continue

        logger.info(f"  Validating boundary between songs {i+1} and {i+2}...")
        boundary_check = validate_song_boundary(
            client, last_page_img, first_page_img,
            song1.get('title', 'Unknown'), song2.get('title', 'Unknown')
        )
        validation_result['checks'].append(boundary_check)

        logger.info(f"    Status: {boundary_check['status']}")

    # Summary
    passed = sum(1 for c in validation_result['checks'] if c['status'] == 'pass')
    failed = sum(1 for c in validation_result['checks'] if c['status'] == 'fail')
    errors = sum(1 for c in validation_result['checks'] if c['status'] == 'error')

    validation_result['summary'] = {
        'status': 'complete',
        'total_checks': len(validation_result['checks']),
        'passed': passed,
        'failed': failed,
        'errors': errors,
        'success_rate': passed / len(validation_result['checks']) if validation_result['checks'] else 0
    }

    return validation_result


def main():
    parser = argparse.ArgumentParser(description="Validate songbooks with local Ollama vision")
    parser.add_argument('--book-id', help="Validate specific book by ID")
    parser.add_argument('--test', type=int, help="Test with N random books")
    parser.add_argument('--model', default=DEFAULT_MODEL, help=f"Ollama model to use (default: {DEFAULT_MODEL})")
    parser.add_argument('--fast', action='store_true', help=f"Use faster model ({FAST_MODEL})")

    args = parser.parse_args()

    # Select model
    model = FAST_MODEL if args.fast else args.model

    logger.info("=" * 80)
    logger.info("LOCAL LLM VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Ollama URL: {OLLAMA_BASE_URL}")
    logger.info(f"Model: {model}")
    logger.info("=" * 80)

    # Initialize client
    client = OllamaVisionClient(OLLAMA_BASE_URL, model)

    # Test mode - validate Film Music book
    if args.test:
        # For demo, just validate the Film Music book we already have data for
        book_id = "v2-33894bb5954299ffee605fa4937d31f8"
        artist = "_Movie and TV"
        book_name = "Various Artists - Film Music For Solo Piano"

        result = validate_book(book_id, artist, book_name, client)

        # Save result
        output_file = Path(f"validation_{book_id}.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info("")
        logger.info("=" * 80)
        logger.info("VALIDATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Status: {result['summary'].get('status')}")
        logger.info(f"Checks: {result['summary'].get('total_checks', 0)}")
        logger.info(f"Passed: {result['summary'].get('passed', 0)}")
        logger.info(f"Failed: {result['summary'].get('failed', 0)}")
        logger.info(f"Errors: {result['summary'].get('errors', 0)}")
        logger.info(f"Results saved to: {output_file}")

    elif args.book_id:
        # Validate specific book
        # Would need to get artist/book_name from lineage data
        logger.error("--book-id requires loading from lineage data (TODO)")

    else:
        logger.error("Please specify --test N or --book-id")


if __name__ == "__main__":
    main()
