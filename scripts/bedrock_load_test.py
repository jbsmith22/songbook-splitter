"""
Bedrock Vision API Load Test

Tests concurrent Bedrock Claude vision calls to find the practical throughput
ceiling and optimal parallelism settings for the songbook pipeline.

Known quotas (us-east-1 cross-region):
  - 100 requests/minute (RPM) for Claude 3.5 Sonnet V2
  - 800,000 tokens/minute (TPM)

Usage:
    python scripts/bedrock_load_test.py --concurrency 4
    python scripts/bedrock_load_test.py --ramp          # Test 1,2,4,8,12,16,20
"""

import argparse
import base64
import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import boto3
import fitz  # PyMuPDF

PROJECT_ROOT = Path(__file__).parent.parent
VISION_MODEL_ID = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'

# Minimal prompt matching our actual pipeline usage
TEST_PROMPT = """Analyze this sheet music page and respond with JSON only.

Songs in this book include: Test Song 1, Test Song 2, Test Song 3

Identify:
1. printed_page: The printed page number visible on this page (integer, or null)
2. content_type: One of "song_start", "song_continuation", "toc", "index", "cover", "blank", "other"
3. song_title: If this is a song_start page, the song title (string or null)
4. has_music: Whether this page contains music notation (boolean)

Respond with ONLY valid JSON:
{"printed_page": <int|null>, "content_type": "<string>", "song_title": <string|null>, "has_music": <bool>}"""


def get_test_image() -> str:
    """Render a single page from a known PDF as base64 PNG."""
    # Use 52nd Street as test - smallest book
    test_pdf = PROJECT_ROOT / 'SheetMusic_Input' / 'Billy Joel' / 'Billy Joel - 52nd Street.pdf'
    if not test_pdf.exists():
        # Fallback to any available PDF
        for pdf in (PROJECT_ROOT / 'SheetMusic_Input').rglob('*.pdf'):
            test_pdf = pdf
            break

    doc = fitz.open(str(test_pdf))
    page = doc[5]  # Pick a mid-book page (likely has music)
    pix = page.get_pixmap(dpi=72)
    img_bytes = pix.tobytes("png")
    doc.close()

    print(f"Test image: {test_pdf.name} page 5 ({len(img_bytes):,} bytes)")
    return base64.b64encode(img_bytes).decode('utf-8')


def make_vision_call(client, image_b64: str, call_id: int) -> dict:
    """Make a single Bedrock vision API call. Returns timing and status."""
    start = time.time()
    try:
        response = client.invoke_model(
            modelId=VISION_MODEL_ID,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 256,
                'messages': [{
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image',
                            'source': {
                                'type': 'base64',
                                'media_type': 'image/png',
                                'data': image_b64
                            }
                        },
                        {
                            'type': 'text',
                            'text': TEST_PROMPT
                        }
                    ]
                }]
            })
        )
        elapsed = time.time() - start
        body = json.loads(response['body'].read())

        # Extract token usage
        usage = body.get('usage', {})
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)

        return {
            'call_id': call_id,
            'status': 'success',
            'elapsed_sec': round(elapsed, 3),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
        }
    except client.exceptions.ThrottlingException as e:
        elapsed = time.time() - start
        return {
            'call_id': call_id,
            'status': 'throttled',
            'elapsed_sec': round(elapsed, 3),
            'error': str(e),
        }
    except Exception as e:
        elapsed = time.time() - start
        error_type = type(e).__name__
        return {
            'call_id': call_id,
            'status': 'error',
            'elapsed_sec': round(elapsed, 3),
            'error': f'{error_type}: {e}',
        }


def run_burst(client, image_b64: str, concurrency: int, num_calls: int) -> dict:
    """
    Fire num_calls concurrent vision requests with given concurrency.
    Returns aggregate stats.
    """
    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {}
        for i in range(num_calls):
            future = executor.submit(make_vision_call, client, image_b64, i)
            futures[future] = i

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    total_elapsed = time.time() - start_time

    # Aggregate
    successes = [r for r in results if r['status'] == 'success']
    throttled = [r for r in results if r['status'] == 'throttled']
    errors = [r for r in results if r['status'] == 'error']

    latencies = [r['elapsed_sec'] for r in successes]
    total_input_tokens = sum(r.get('input_tokens', 0) for r in successes)
    total_output_tokens = sum(r.get('output_tokens', 0) for r in successes)

    stats = {
        'concurrency': concurrency,
        'num_calls': num_calls,
        'total_elapsed_sec': round(total_elapsed, 2),
        'successes': len(successes),
        'throttled': len(throttled),
        'errors': len(errors),
        'throughput_rpm': round(len(successes) / total_elapsed * 60, 1) if total_elapsed > 0 else 0,
        'effective_rps': round(len(successes) / total_elapsed, 2) if total_elapsed > 0 else 0,
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'tokens_per_call': round(total_input_tokens / len(successes)) if successes else 0,
    }

    if latencies:
        stats['latency_p50'] = round(statistics.median(latencies), 2)
        stats['latency_p90'] = round(sorted(latencies)[int(len(latencies) * 0.9)], 2)
        stats['latency_min'] = round(min(latencies), 2)
        stats['latency_max'] = round(max(latencies), 2)

    return stats


def print_stats(stats: dict):
    """Pretty print a stats dict."""
    c = stats['concurrency']
    n = stats['num_calls']
    s = stats['successes']
    t = stats['throttled']
    e = stats['errors']
    rpm = stats['throughput_rpm']
    rps = stats['effective_rps']
    elapsed = stats['total_elapsed_sec']

    throttle_pct = round(t / n * 100, 1) if n > 0 else 0
    status = "OK" if t == 0 else f"THROTTLED ({throttle_pct}%)"

    print(f"  Concurrency {c:2d} | {s}/{n} ok | {t} throttled | "
          f"{rpm:5.1f} RPM | {rps:.2f} RPS | "
          f"p50={stats.get('latency_p50', '?')}s p90={stats.get('latency_p90', '?')}s | "
          f"{elapsed:.1f}s total | {status}")

    if stats.get('tokens_per_call'):
        print(f"               | {stats['tokens_per_call']} tokens/call | "
              f"{stats['total_input_tokens'] + stats['total_output_tokens']} total tokens")


def main():
    parser = argparse.ArgumentParser(description='Bedrock Vision API Load Test')
    parser.add_argument('--concurrency', type=int, default=0,
                        help='Test a specific concurrency level')
    parser.add_argument('--calls', type=int, default=20,
                        help='Number of calls per test (default: 20)')
    parser.add_argument('--ramp', action='store_true',
                        help='Ramp test: 1, 2, 4, 8, 12, 16, 20 concurrent')
    parser.add_argument('--cooldown', type=int, default=15,
                        help='Seconds between ramp levels (default: 15)')
    args = parser.parse_args()

    print(f"Bedrock Vision Load Test")
    print(f"Model: {VISION_MODEL_ID}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Prepare test image
    image_b64 = get_test_image()
    print()

    # Create Bedrock client
    client = boto3.client('bedrock-runtime', region_name='us-east-1')

    if args.ramp:
        levels = [1, 2, 4, 8, 12, 16, 20]
        print(f"Ramp test: {levels}")
        print(f"Calls per level: {args.calls}")
        print(f"Cooldown between levels: {args.cooldown}s")
        print(f"{'='*100}")

        all_stats = []
        for level in levels:
            print(f"\n--- Testing concurrency={level} ({args.calls} calls) ---")
            stats = run_burst(client, image_b64, level, args.calls)
            print_stats(stats)
            all_stats.append(stats)

            # Cooldown to let rate limiter reset
            if level != levels[-1]:
                print(f"  Cooling down {args.cooldown}s...")
                time.sleep(args.cooldown)

        # Summary
        print(f"\n{'='*100}")
        print(f"SUMMARY")
        print(f"{'='*100}")
        print(f"{'Conc':>5} | {'OK':>4} | {'Throt':>5} | {'RPM':>7} | {'RPS':>6} | {'p50':>6} | {'p90':>6} | {'Time':>6}")
        print(f"{'-'*5}-+-{'-'*4}-+-{'-'*5}-+-{'-'*7}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}")
        for s in all_stats:
            t_pct = f"{s['throttled']}" if s['throttled'] > 0 else "-"
            print(f"{s['concurrency']:5d} | {s['successes']:4d} | {t_pct:>5} | "
                  f"{s['throughput_rpm']:7.1f} | {s['effective_rps']:6.2f} | "
                  f"{s.get('latency_p50', '?'):>6} | {s.get('latency_p90', '?'):>6} | "
                  f"{s['total_elapsed_sec']:6.1f}")

        # Find optimal
        best = max(all_stats, key=lambda s: s['effective_rps'] if s['throttled'] == 0 else 0)
        max_clean = best['concurrency'] if best['throttled'] == 0 else 'none'
        print(f"\nMax clean concurrency (0 throttles): {max_clean}")
        if max_clean != 'none':
            print(f"  Throughput at that level: {best['effective_rps']} RPS = {best['throughput_rpm']} RPM")

        # Pipeline planning
        if best.get('tokens_per_call'):
            tpc = best['tokens_per_call']
            print(f"\nPipeline planning (at {tpc} tokens/call):")
            for books in [1, 2, 4, 8]:
                workers = max(1, best['concurrency'] // books) if max_clean != 'none' else 1
                total_conc = books * workers
                print(f"  {books} books x {workers} workers = {total_conc} concurrent calls")

    elif args.concurrency > 0:
        print(f"Single test: concurrency={args.concurrency}, calls={args.calls}")
        print(f"{'='*80}")
        stats = run_burst(client, image_b64, args.concurrency, args.calls)
        print_stats(stats)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
