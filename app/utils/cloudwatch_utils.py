"""
CloudWatch utilities for metrics and structured logging.

This module provides:
- Custom metric emission
- Structured JSON logging with correlation IDs
- Local mode support (logs to console instead of CloudWatch)
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class MockCloudWatch:
    """Mock CloudWatch implementation for local mode."""
    
    def __init__(self):
        logger.info("MockCloudWatch initialized")
    
    def put_metric_data(self, Namespace: str, MetricData: List[Dict]) -> None:
        """Mock metric emission - logs to console."""
        for metric in MetricData:
            logger.info(f"[METRIC] {Namespace}/{metric['MetricName']}: {metric['Value']} {metric.get('Unit', '')}")


class CloudWatchUtils:
    """Utilities for CloudWatch metrics and logging."""
    
    def __init__(self, namespace: str = 'SheetMusicSplitter', local_mode: bool = False):
        """
        Initialize CloudWatch utilities.
        
        Args:
            namespace: CloudWatch namespace for metrics
            local_mode: If True, log to console instead of CloudWatch
        """
        self.namespace = namespace
        self.local_mode = local_mode
        
        if local_mode:
            self.cloudwatch = MockCloudWatch()
            logger.info("CloudWatchUtils initialized in local mode")
        else:
            self.cloudwatch_client = boto3.client('cloudwatch')
            logger.info(f"CloudWatchUtils initialized with namespace {namespace}")
    
    def emit_metric(self, metric_name: str, value: float, unit: str = 'Count',
                   dimensions: Optional[Dict[str, str]] = None) -> None:
        """
        Emit custom metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (Count, Seconds, Bytes, etc.)
            dimensions: Optional dimensions for the metric
        """
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            if self.local_mode:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[metric_data]
                )
            else:
                self.cloudwatch_client.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[metric_data]
                )
            
            logger.debug(f"Emitted metric: {metric_name}={value} {unit}")
            
        except ClientError as e:
            logger.error(f"Error emitting metric {metric_name}: {e}")
    
    def emit_processing_metrics(self, book_id: str, metrics: Dict[str, Any]) -> None:
        """
        Emit batch of processing metrics.
        
        Args:
            book_id: Book identifier
            metrics: Dictionary of metric name -> value
        """
        dimensions = {'BookId': book_id}
        
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                self.emit_metric(metric_name, value, dimensions=dimensions)
    
    def emit_cost_metrics(self, textract_pages: int, bedrock_tokens: int, 
                         estimated_cost_usd: float) -> None:
        """
        Emit cost-related metrics.
        
        Args:
            textract_pages: Number of pages processed by Textract
            bedrock_tokens: Number of tokens used by Bedrock
            estimated_cost_usd: Estimated cost in USD
        """
        self.emit_metric('TextractPages', textract_pages, unit='Count')
        self.emit_metric('BedrockTokens', bedrock_tokens, unit='Count')
        self.emit_metric('EstimatedCost', estimated_cost_usd, unit='None')
    
    def emit_success_metrics(self, books_processed: int, songs_extracted: int,
                            toc_success_rate: float, verification_success_rate: float) -> None:
        """
        Emit success rate metrics.
        
        Args:
            books_processed: Number of books processed
            songs_extracted: Number of songs extracted
            toc_success_rate: TOC extraction success rate (0.0-1.0)
            verification_success_rate: Verification success rate (0.0-1.0)
        """
        self.emit_metric('BooksProcessed', books_processed, unit='Count')
        self.emit_metric('SongsExtracted', songs_extracted, unit='Count')
        self.emit_metric('TOCSuccessRate', toc_success_rate * 100, unit='Percent')
        self.emit_metric('VerificationSuccessRate', verification_success_rate * 100, unit='Percent')
    
    def emit_error_metric(self, error_type: str, stage: str) -> None:
        """
        Emit error metric.
        
        Args:
            error_type: Type of error
            stage: Pipeline stage where error occurred
        """
        dimensions = {
            'ErrorType': error_type,
            'Stage': stage
        }
        self.emit_metric('ProcessingErrors', 1, dimensions=dimensions)


class StructuredLogger:
    """Structured JSON logger with correlation IDs."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        """
        Initialize structured logger.
        
        Args:
            correlation_id: Correlation ID for tracing (e.g., Step Functions execution ARN)
        """
        self.correlation_id = correlation_id or self._generate_correlation_id()
        self.logger = logging.getLogger(__name__)
    
    def _generate_correlation_id(self) -> str:
        """Generate a correlation ID."""
        import uuid
        return str(uuid.uuid4())
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """
        Log structured message.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            **kwargs: Additional fields to include in log
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': self.correlation_id,
            'level': level,
            'message': message,
            **kwargs
        }
        
        log_json = json.dumps(log_entry)
        
        if level == 'ERROR':
            self.logger.error(log_json)
        elif level == 'WARNING':
            self.logger.warning(log_json)
        elif level == 'DEBUG':
            self.logger.debug(log_json)
        else:
            self.logger.info(log_json)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.log('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.log('ERROR', message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.log('DEBUG', message, **kwargs)


def create_structured_logger(execution_arn: Optional[str] = None) -> StructuredLogger:
    """
    Create a structured logger with correlation ID.
    
    Args:
        execution_arn: Step Functions execution ARN (used as correlation ID)
    
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(correlation_id=execution_arn)
