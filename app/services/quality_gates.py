"""
Quality Gate Enforcement Module

This module implements quality gates that validate processing results at multiple
checkpoints in the pipeline. Quality gates ensure that only high-quality outputs
are produced and route low-quality results to manual review.

Quality Gates:
1. TOC Quality Gate: Verify ≥10 entries extracted
2. Verification Quality Gate: Verify ≥95% song start verification success
3. Output Quality Gate: Verify ≥90% songs extracted successfully
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QualityGateResult:
    """Result of a quality gate check"""
    passed: bool
    status: str  # "success", "failed", or "manual_review"
    metric_value: float
    threshold: float
    message: str
    details: Dict[str, Any]


def check_toc_quality_gate(
    toc_entry_count: int,
    min_entries: int = 10,
    allow_short_books: bool = False
) -> QualityGateResult:
    """
    Check if TOC extraction meets quality threshold.
    
    Args:
        toc_entry_count: Number of TOC entries extracted
        min_entries: Minimum required entries (default 10)
        allow_short_books: If True, bypass check for books marked as short
        
    Returns:
        QualityGateResult with pass/fail status
        
    Quality Gate Rule:
        - PASS: toc_entry_count >= min_entries
        - MANUAL_REVIEW: toc_entry_count < min_entries (unless allow_short_books=True)
    """
    passed = toc_entry_count >= min_entries or allow_short_books
    
    if passed:
        status = "success"
        message = f"TOC quality gate passed: {toc_entry_count} entries extracted (threshold: {min_entries})"
    else:
        status = "manual_review"
        message = f"TOC quality gate failed: {toc_entry_count} entries extracted (threshold: {min_entries})"
    
    logger.info(message)
    
    return QualityGateResult(
        passed=passed,
        status=status,
        metric_value=float(toc_entry_count),
        threshold=float(min_entries),
        message=message,
        details={
            "toc_entry_count": toc_entry_count,
            "min_entries": min_entries,
            "allow_short_books": allow_short_books
        }
    )


def check_verification_quality_gate(
    songs_verified: int,
    total_songs: int,
    min_success_rate: float = 0.95
) -> QualityGateResult:
    """
    Check if song start verification meets quality threshold.
    
    Args:
        songs_verified: Number of songs successfully verified
        total_songs: Total number of songs to verify
        min_success_rate: Minimum required success rate (default 0.95 = 95%)
        
    Returns:
        QualityGateResult with pass/fail status
        
    Quality Gate Rule:
        - PASS: verification_rate >= min_success_rate
        - MANUAL_REVIEW: verification_rate < min_success_rate
    """
    if total_songs == 0:
        # Edge case: no songs to verify
        logger.warning("Verification quality gate: no songs to verify")
        return QualityGateResult(
            passed=False,
            status="manual_review",
            metric_value=0.0,
            threshold=min_success_rate,
            message="No songs to verify",
            details={
                "songs_verified": 0,
                "total_songs": 0,
                "verification_rate": 0.0
            }
        )
    
    verification_rate = songs_verified / total_songs
    passed = verification_rate >= min_success_rate
    
    if passed:
        status = "success"
        message = f"Verification quality gate passed: {verification_rate:.1%} success rate (threshold: {min_success_rate:.1%})"
    else:
        status = "manual_review"
        message = f"Verification quality gate failed: {verification_rate:.1%} success rate (threshold: {min_success_rate:.1%})"
    
    logger.info(message)
    
    return QualityGateResult(
        passed=passed,
        status=status,
        metric_value=verification_rate,
        threshold=min_success_rate,
        message=message,
        details={
            "songs_verified": songs_verified,
            "total_songs": total_songs,
            "verification_rate": verification_rate,
            "songs_failed": total_songs - songs_verified
        }
    )


def check_output_quality_gate(
    songs_extracted: int,
    total_songs: int,
    min_success_rate: float = 0.90,
    allow_partial_output: bool = False
) -> QualityGateResult:
    """
    Check if PDF splitting/output meets quality threshold.
    
    Args:
        songs_extracted: Number of songs successfully extracted to PDFs
        total_songs: Total number of songs to extract
        min_success_rate: Minimum required success rate (default 0.90 = 90%)
        allow_partial_output: If True, allow partial outputs even if gate fails
        
    Returns:
        QualityGateResult with pass/fail status
        
    Quality Gate Rule:
        - PASS: extraction_rate >= min_success_rate
        - MANUAL_REVIEW: extraction_rate < min_success_rate
        - If allow_partial_output=True, partial results are saved even on failure
    """
    if total_songs == 0:
        # Edge case: no songs to extract
        logger.warning("Output quality gate: no songs to extract")
        return QualityGateResult(
            passed=False,
            status="manual_review",
            metric_value=0.0,
            threshold=min_success_rate,
            message="No songs to extract",
            details={
                "songs_extracted": 0,
                "total_songs": 0,
                "extraction_rate": 0.0
            }
        )
    
    extraction_rate = songs_extracted / total_songs
    passed = extraction_rate >= min_success_rate
    
    if passed:
        status = "success"
        message = f"Output quality gate passed: {extraction_rate:.1%} success rate (threshold: {min_success_rate:.1%})"
    else:
        status = "manual_review"
        message = f"Output quality gate failed: {extraction_rate:.1%} success rate (threshold: {min_success_rate:.1%})"
        if allow_partial_output:
            message += " (partial outputs saved)"
    
    logger.info(message)
    
    return QualityGateResult(
        passed=passed,
        status=status,
        metric_value=extraction_rate,
        threshold=min_success_rate,
        message=message,
        details={
            "songs_extracted": songs_extracted,
            "total_songs": total_songs,
            "extraction_rate": extraction_rate,
            "songs_failed": total_songs - songs_extracted,
            "allow_partial_output": allow_partial_output
        }
    )


def aggregate_quality_gates(
    gate_results: List[QualityGateResult]
) -> Dict[str, Any]:
    """
    Aggregate multiple quality gate results into overall status.
    
    Args:
        gate_results: List of QualityGateResult objects
        
    Returns:
        Dict with overall status and details
        
    Aggregation Rule:
        - If any gate has status="manual_review", overall status is "manual_review"
        - If any gate has status="failed", overall status is "failed"
        - Otherwise, overall status is "success"
    """
    all_passed = all(result.passed for result in gate_results)
    
    # Determine overall status
    if any(result.status == "manual_review" for result in gate_results):
        overall_status = "manual_review"
    elif any(result.status == "failed" for result in gate_results):
        overall_status = "failed"
    else:
        overall_status = "success"
    
    # Collect failed gates
    failed_gates = [
        result.message for result in gate_results if not result.passed
    ]
    
    logger.info(f"Quality gate aggregation: overall_status={overall_status}, all_passed={all_passed}")
    
    return {
        "overall_status": overall_status,
        "all_passed": all_passed,
        "gates_checked": len(gate_results),
        "gates_passed": sum(1 for r in gate_results if r.passed),
        "gates_failed": sum(1 for r in gate_results if not r.passed),
        "failed_gates": failed_gates,
        "gate_results": [
            {
                "passed": r.passed,
                "status": r.status,
                "metric_value": r.metric_value,
                "threshold": r.threshold,
                "message": r.message
            }
            for r in gate_results
        ]
    }
