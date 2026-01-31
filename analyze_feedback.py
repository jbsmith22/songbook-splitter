#!/usr/bin/env python3
"""
Analyze review feedback to identify patterns and suggest improvements.
"""

import json
from pathlib import Path
from collections import Counter

def analyze_feedback(feedback_file: Path):
    """Analyze exported feedback."""
    
    with open(feedback_file, 'r') as f:
        data = json.load(f)
    
    summary = data['summary']
    reviews = data['reviews']
    feedback = data.get('feedback', {})
    correct_types = data.get('correctTypes', {})
    
    print("=" * 80)
    print("FEEDBACK ANALYSIS")
    print("=" * 80)
    
    # Overall stats
    print("\n📊 OVERALL STATISTICS")
    print(f"  Total PDFs reviewed: {summary['reviewed']}/{summary['total']}")
    print(f"  Correct detections: {summary['correct']} ({summary['correct']/summary['reviewed']*100:.1f}%)")
    print(f"  False positives: {summary['incorrect']} ({summary['false_positive_rate']})")
    print(f"  Skipped: {summary['skipped']}")
    
    # Analyze error types for correct detections
    if correct_types:
        print("\n🎯 ERROR TYPE BREAKDOWN (Correct Detections)")
        
        type_counts = Counter()
        for idx, ct in correct_types.items():
            if reviews.get(idx) == 'correct' and ct.get('type'):
                type_counts[ct['type']] += 1
        
        if type_counts:
            print("\n  Error types found:")
            type_labels = {
                'starts-mid-song-correct': '⚠️  Starts mid-song (SAME song, wrong start)',
                'wrong-song-entirely': '❌ Wrong song entirely (DIFFERENT song)',
                'missed-split': '🔀 Missed split (multiple songs)',
                'extra-pages': '📄 Extra pages (continues into next song)'
            }
            for error_type, count in type_counts.most_common():
                label = type_labels.get(error_type, error_type)
                print(f"    • {label}: {count}")
        
        # Show detailed notes for correct detections
        print("\n📝 ERROR DETAILS")
        for idx, ct in correct_types.items():
            if reviews.get(idx) == 'correct' and ct.get('notes'):
                error_type = ct.get('type', 'unknown')
                label = type_labels.get(error_type, error_type)
                print(f"\n  PDF #{idx} ({label}):")
                print(f"    {ct['notes']}")
    
    # Analyze false positive patterns
    if feedback:
        print("\n🔍 FALSE POSITIVE PATTERNS")
        
        all_reasons = []
        for idx, fb in feedback.items():
            if reviews.get(idx) == 'incorrect' and 'reasons' in fb:
                all_reasons.extend(fb['reasons'])
        
        if all_reasons:
            reason_counts = Counter(all_reasons)
            print("\n  Most common reasons:")
            for reason, count in reason_counts.most_common():
                reason_label = reason.replace('-', ' ').title()
                print(f"    • {reason_label}: {count} times")
        
        # Show notes
        print("\n📝 DETAILED NOTES")
        for idx, fb in feedback.items():
            if reviews.get(idx) == 'incorrect' and fb.get('notes'):
                print(f"\n  PDF #{idx}:")
                print(f"    Reasons: {', '.join(fb.get('reasons', []))}")
                print(f"    Notes: {fb['notes']}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    fp_rate = summary['incorrect'] / summary['reviewed'] * 100
    
    if fp_rate < 10:
        print("\n✅ EXCELLENT: False positive rate is very low (<10%)")
        print("   → Ready to proceed with full 11,976 PDF verification")
        print("   → Expected flagged PDFs: ~1,200-2,400")
        print("   → Manual review effort: Manageable")
    elif fp_rate < 20:
        print("\n✓ GOOD: False positive rate is acceptable (10-20%)")
        print("   → Can proceed with full verification")
        print("   → Expected flagged PDFs: ~2,400-4,800")
        print("   → Consider prompt tuning to reduce false positives")
    elif fp_rate < 40:
        print("\n⚠️ MODERATE: False positive rate is high (20-40%)")
        print("   → Recommend prompt tuning before full run")
        print("   → Expected flagged PDFs: ~4,800-9,600")
        print("   → Manual review effort: Significant")
    else:
        print("\n❌ HIGH: False positive rate is too high (>40%)")
        print("   → Must tune prompts before proceeding")
        print("   → Current approach would flag majority of PDFs")
        print("   → Review feedback patterns and adjust detection logic")
    
    # Specific prompt suggestions
    if feedback:
        print("\n🔧 PROMPT TUNING SUGGESTIONS")
        
        reason_counts = Counter()
        for idx, fb in feedback.items():
            if reviews.get(idx) == 'incorrect' and 'reasons' in fb:
                reason_counts.update(fb['reasons'])
        
        if reason_counts.get('song-starts-midpage', 0) > 2:
            print("\n  • Add to prompt: 'Songs CAN start mid-page if previous song ends there'")
        
        if reason_counts.get('guitar-tabs', 0) > 2:
            print("\n  • Add to prompt: 'Guitar tabs above sheet music are NORMAL in guitar books'")
        
        if reason_counts.get('text-tabs', 0) > 2:
            print("\n  • Add to prompt: 'Text-only guitar tabs (no staff lines) are valid song formats'")
        
        if reason_counts.get('extra-content', 0) > 2:
            print("\n  • Add to prompt: 'Photos, discography, or text at end are ACCEPTABLE'")
        
        if reason_counts.get('section-marker', 0) > 2:
            print("\n  • Strengthen prompt: 'Section markers (Verse, Chorus, Bridge) are NOT new songs'")
        
        if reason_counts.get('tempo-change', 0) > 2:
            print("\n  • Strengthen prompt: 'Tempo/key changes within a song are NOT new songs'")
        
        if reason_counts.get('title-midpage', 0) > 2:
            print("\n  • Add to prompt: 'Title mid-page is OK if previous song ends there'")
        
        if reason_counts.get('continuation', 0) > 2:
            print("\n  • Strengthen prompt: 'Only flag if ABSOLUTELY CERTAIN a NEW song starts'")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: py analyze_feedback.py <feedback_json_file>")
        print("\nExample:")
        print("  py analyze_feedback.py review_feedback_2026-01-28.json")
        sys.exit(1)
    
    feedback_file = Path(sys.argv[1])
    if not feedback_file.exists():
        print(f"Error: {feedback_file} not found")
        sys.exit(1)
    
    analyze_feedback(feedback_file)
