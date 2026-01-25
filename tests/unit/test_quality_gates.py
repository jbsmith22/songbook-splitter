"""
Unit tests for quality gate enforcement module.
"""

import pytest
from app.services.quality_gates import (
    check_toc_quality_gate,
    check_verification_quality_gate,
    check_output_quality_gate,
    aggregate_quality_gates,
    QualityGateResult
)


class TestTOCQualityGate:
    """Tests for TOC quality gate."""
    
    def test_passes_with_sufficient_entries(self):
        """Test that gate passes with >= 10 entries."""
        result = check_toc_quality_gate(toc_entry_count=15, min_entries=10)
        assert result.passed is True
        assert result.status == "success"
        assert result.metric_value == 15.0
        assert result.threshold == 10.0
    
    def test_passes_at_threshold(self):
        """Test that gate passes at exactly the threshold."""
        result = check_toc_quality_gate(toc_entry_count=10, min_entries=10)
        assert result.passed is True
        assert result.status == "success"
    
    def test_fails_below_threshold(self):
        """Test that gate fails with < 10 entries."""
        result = check_toc_quality_gate(toc_entry_count=5, min_entries=10)
        assert result.passed is False
        assert result.status == "manual_review"
        assert result.metric_value == 5.0
    
    def test_allows_short_books(self):
        """Test that short books bypass the check."""
        result = check_toc_quality_gate(
            toc_entry_count=5,
            min_entries=10,
            allow_short_books=True
        )
        assert result.passed is True
        assert result.status == "success"
    
    def test_custom_threshold(self):
        """Test with custom minimum entries."""
        result = check_toc_quality_gate(toc_entry_count=8, min_entries=5)
        assert result.passed is True
        assert result.status == "success"


class TestVerificationQualityGate:
    """Tests for verification quality gate."""
    
    def test_passes_with_high_success_rate(self):
        """Test that gate passes with >= 95% success rate."""
        result = check_verification_quality_gate(
            songs_verified=48,
            total_songs=50,
            min_success_rate=0.95
        )
        assert result.passed is True
        assert result.status == "success"
        assert result.metric_value == 0.96
    
    def test_passes_at_threshold(self):
        """Test that gate passes at exactly 95%."""
        result = check_verification_quality_gate(
            songs_verified=95,
            total_songs=100,
            min_success_rate=0.95
        )
        assert result.passed is True
        assert result.status == "success"
    
    def test_fails_below_threshold(self):
        """Test that gate fails with < 95% success rate."""
        result = check_verification_quality_gate(
            songs_verified=90,
            total_songs=100,
            min_success_rate=0.95
        )
        assert result.passed is False
        assert result.status == "manual_review"
        assert result.metric_value == 0.90
    
    def test_handles_zero_songs(self):
        """Test edge case with no songs to verify."""
        result = check_verification_quality_gate(
            songs_verified=0,
            total_songs=0,
            min_success_rate=0.95
        )
        assert result.passed is False
        assert result.status == "manual_review"
    
    def test_perfect_verification(self):
        """Test 100% verification rate."""
        result = check_verification_quality_gate(
            songs_verified=50,
            total_songs=50,
            min_success_rate=0.95
        )
        assert result.passed is True
        assert result.metric_value == 1.0
    
    def test_custom_threshold(self):
        """Test with custom success rate threshold."""
        result = check_verification_quality_gate(
            songs_verified=85,
            total_songs=100,
            min_success_rate=0.80
        )
        assert result.passed is True
        assert result.status == "success"


class TestOutputQualityGate:
    """Tests for output quality gate."""
    
    def test_passes_with_high_success_rate(self):
        """Test that gate passes with >= 90% success rate."""
        result = check_output_quality_gate(
            songs_extracted=46,
            total_songs=50,
            min_success_rate=0.90
        )
        assert result.passed is True
        assert result.status == "success"
        assert result.metric_value == 0.92
    
    def test_passes_at_threshold(self):
        """Test that gate passes at exactly 90%."""
        result = check_output_quality_gate(
            songs_extracted=90,
            total_songs=100,
            min_success_rate=0.90
        )
        assert result.passed is True
        assert result.status == "success"
    
    def test_fails_below_threshold(self):
        """Test that gate fails with < 90% success rate."""
        result = check_output_quality_gate(
            songs_extracted=85,
            total_songs=100,
            min_success_rate=0.90
        )
        assert result.passed is False
        assert result.status == "manual_review"
        assert result.metric_value == 0.85
    
    def test_handles_zero_songs(self):
        """Test edge case with no songs to extract."""
        result = check_output_quality_gate(
            songs_extracted=0,
            total_songs=0,
            min_success_rate=0.90
        )
        assert result.passed is False
        assert result.status == "manual_review"
    
    def test_allows_partial_output(self):
        """Test that partial outputs can be saved even on failure."""
        result = check_output_quality_gate(
            songs_extracted=80,
            total_songs=100,
            min_success_rate=0.90,
            allow_partial_output=True
        )
        assert result.passed is False
        assert result.status == "manual_review"
        assert "partial outputs saved" in result.message
    
    def test_perfect_extraction(self):
        """Test 100% extraction rate."""
        result = check_output_quality_gate(
            songs_extracted=50,
            total_songs=50,
            min_success_rate=0.90
        )
        assert result.passed is True
        assert result.metric_value == 1.0


class TestAggregateQualityGates:
    """Tests for quality gate aggregation."""
    
    def test_all_gates_pass(self):
        """Test aggregation when all gates pass."""
        gate1 = QualityGateResult(
            passed=True,
            status="success",
            metric_value=15.0,
            threshold=10.0,
            message="TOC gate passed",
            details={}
        )
        gate2 = QualityGateResult(
            passed=True,
            status="success",
            metric_value=0.96,
            threshold=0.95,
            message="Verification gate passed",
            details={}
        )
        gate3 = QualityGateResult(
            passed=True,
            status="success",
            metric_value=0.92,
            threshold=0.90,
            message="Output gate passed",
            details={}
        )
        
        result = aggregate_quality_gates([gate1, gate2, gate3])
        
        assert result["overall_status"] == "success"
        assert result["all_passed"] is True
        assert result["gates_checked"] == 3
        assert result["gates_passed"] == 3
        assert result["gates_failed"] == 0
        assert len(result["failed_gates"]) == 0
    
    def test_one_gate_fails(self):
        """Test aggregation when one gate fails."""
        gate1 = QualityGateResult(
            passed=True,
            status="success",
            metric_value=15.0,
            threshold=10.0,
            message="TOC gate passed",
            details={}
        )
        gate2 = QualityGateResult(
            passed=False,
            status="manual_review",
            metric_value=0.90,
            threshold=0.95,
            message="Verification gate failed",
            details={}
        )
        gate3 = QualityGateResult(
            passed=True,
            status="success",
            metric_value=0.92,
            threshold=0.90,
            message="Output gate passed",
            details={}
        )
        
        result = aggregate_quality_gates([gate1, gate2, gate3])
        
        assert result["overall_status"] == "manual_review"
        assert result["all_passed"] is False
        assert result["gates_checked"] == 3
        assert result["gates_passed"] == 2
        assert result["gates_failed"] == 1
        assert len(result["failed_gates"]) == 1
        assert "Verification gate failed" in result["failed_gates"][0]
    
    def test_multiple_gates_fail(self):
        """Test aggregation when multiple gates fail."""
        gate1 = QualityGateResult(
            passed=False,
            status="manual_review",
            metric_value=5.0,
            threshold=10.0,
            message="TOC gate failed",
            details={}
        )
        gate2 = QualityGateResult(
            passed=False,
            status="manual_review",
            metric_value=0.90,
            threshold=0.95,
            message="Verification gate failed",
            details={}
        )
        gate3 = QualityGateResult(
            passed=True,
            status="success",
            metric_value=0.92,
            threshold=0.90,
            message="Output gate passed",
            details={}
        )
        
        result = aggregate_quality_gates([gate1, gate2, gate3])
        
        assert result["overall_status"] == "manual_review"
        assert result["all_passed"] is False
        assert result["gates_checked"] == 3
        assert result["gates_passed"] == 1
        assert result["gates_failed"] == 2
        assert len(result["failed_gates"]) == 2
    
    def test_empty_gate_list(self):
        """Test aggregation with no gates."""
        result = aggregate_quality_gates([])
        
        assert result["overall_status"] == "success"
        assert result["all_passed"] is True
        assert result["gates_checked"] == 0
        assert result["gates_passed"] == 0
        assert result["gates_failed"] == 0
    
    def test_gate_results_included(self):
        """Test that individual gate results are included in output."""
        gate1 = QualityGateResult(
            passed=True,
            status="success",
            metric_value=15.0,
            threshold=10.0,
            message="TOC gate passed",
            details={}
        )
        
        result = aggregate_quality_gates([gate1])
        
        assert "gate_results" in result
        assert len(result["gate_results"]) == 1
        assert result["gate_results"][0]["passed"] is True
        assert result["gate_results"][0]["metric_value"] == 15.0


class TestQualityGateResult:
    """Tests for QualityGateResult dataclass."""
    
    def test_quality_gate_result_creation(self):
        """Test creating a QualityGateResult."""
        result = QualityGateResult(
            passed=True,
            status="success",
            metric_value=0.95,
            threshold=0.90,
            message="Test passed",
            details={"key": "value"}
        )
        
        assert result.passed is True
        assert result.status == "success"
        assert result.metric_value == 0.95
        assert result.threshold == 0.90
        assert result.message == "Test passed"
        assert result.details == {"key": "value"}
