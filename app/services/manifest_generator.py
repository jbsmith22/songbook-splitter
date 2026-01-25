"""
Manifest Generator Service - Creates audit manifests with metadata and results.

This module provides functions for:
- Generating comprehensive manifests from pipeline execution data
- Aggregating data from all pipeline stages
- Calculating success metrics and quality scores
- Writing manifests to S3 or local filesystem
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from app.models import Manifest, TOCDiscoveryResult, TOCParseResult, PageMapping, OutputFile
from app.utils.s3_utils import S3Utils

logger = logging.getLogger(__name__)


class ManifestGeneratorService:
    """Service for generating and persisting manifests."""
    
    def __init__(self, local_mode: bool = False, local_output_path: Optional[str] = None):
        """
        Initialize manifest generator service.
        
        Args:
            local_mode: If True, write to local filesystem
            local_output_path: Base path for local output
        """
        self.local_mode = local_mode
        self.s3_utils = S3Utils(local_mode=local_mode, local_base_path=local_output_path)
        logger.info(f"ManifestGeneratorService initialized (local_mode={local_mode})")
    
    def generate_manifest(self, book_id: str, source_pdf: str, artist: str, book_name: str,
                         toc_discovery: Optional[TOCDiscoveryResult] = None,
                         toc_parse: Optional[TOCParseResult] = None,
                         page_mapping: Optional[PageMapping] = None,
                         verification_results: Optional[Dict] = None,
                         output_files: Optional[List[OutputFile]] = None,
                         processing_start: Optional[datetime] = None,
                         processing_end: Optional[datetime] = None,
                         warnings: Optional[List[str]] = None,
                         errors: Optional[List[str]] = None) -> Manifest:
        """
        Create manifest from Step Functions execution data.
        
        Args:
            book_id: Unique book identifier
            source_pdf: S3 URI or path to source PDF
            artist: Artist name
            book_name: Book name
            toc_discovery: TOC discovery results
            toc_parse: TOC parsing results
            page_mapping: Page mapping results
            verification_results: Song verification results
            output_files: List of output files
            processing_start: Processing start time
            processing_end: Processing end time
            warnings: List of warning messages
            errors: List of error messages
        
        Returns:
            Manifest object
        """
        logger.info(f"Generating manifest for book {book_id}")
        
        # Calculate processing duration
        processing_duration = None
        if processing_start and processing_end:
            processing_duration = (processing_end - processing_start).total_seconds()
        
        # Build TOC discovery metadata
        toc_discovery_meta = {}
        if toc_discovery:
            toc_discovery_meta = {
                'toc_pages': toc_discovery.toc_pages,
                'extraction_method': 'textract',
                'entry_count': len(toc_discovery.toc_pages),
                'confidence': sum(toc_discovery.confidence_scores.values()) / len(toc_discovery.confidence_scores) if toc_discovery.confidence_scores else 0.0
            }
        
        # Build TOC parsing metadata
        if toc_parse:
            toc_discovery_meta['extraction_method'] = toc_parse.extraction_method
            toc_discovery_meta['entry_count'] = len(toc_parse.entries)
            toc_discovery_meta['confidence'] = toc_parse.confidence
        
        # Build page mapping metadata
        page_mapping_meta = {}
        if page_mapping:
            page_mapping_meta = {
                'offset': page_mapping.offset,
                'confidence': page_mapping.confidence,
                'samples_verified': page_mapping.samples_verified
            }
        
        # Build verification metadata
        verification_meta = {}
        if verification_results:
            total_songs = verification_results.get('total_songs', 0)
            verified_songs = verification_results.get('verified_songs', 0)
            adjusted_songs = verification_results.get('adjusted_songs', 0)
            failed_songs = verification_results.get('failed_songs', 0)
            
            verification_meta = {
                'songs_verified': verified_songs,
                'songs_adjusted': adjusted_songs,
                'songs_failed': failed_songs,
                'success_rate': verified_songs / total_songs if total_songs > 0 else 0.0
            }
        
        # Build output metadata
        output_meta = {}
        if output_files:
            total_size = sum(f.file_size_bytes for f in output_files)
            output_meta = {
                'songs_extracted': len(output_files),
                'output_directory': self._get_output_directory(output_files),
                'total_size_bytes': total_size,
                'files': [
                    {
                        'song_title': f.song_title,
                        'artist': f.artist,
                        'page_range': list(f.page_range),
                        'output_file': f.output_uri,
                        'file_size_bytes': f.file_size_bytes
                    }
                    for f in output_files
                ]
            }
        
        # Calculate cost estimate (placeholder - would use actual AWS costs)
        cost_estimate = self._estimate_costs(toc_discovery, toc_parse, output_files)
        
        # Create manifest
        manifest = Manifest(
            book_id=book_id,
            source_pdf=source_pdf,
            artist=artist,
            book_name=book_name,
            processing_timestamp=processing_end.isoformat() if processing_end else datetime.utcnow().isoformat(),
            processing_duration_seconds=processing_duration,
            toc_discovery=toc_discovery_meta,
            page_mapping=page_mapping_meta,
            verification=verification_meta,
            output=output_meta,
            warnings=warnings or [],
            errors=errors or [],
            cost_estimate=cost_estimate
        )
        
        logger.info(f"Generated manifest with {len(output_files or [])} output files")
        return manifest
    
    def _get_output_directory(self, output_files: List[OutputFile]) -> str:
        """Extract common output directory from output files."""
        if not output_files:
            return ""
        
        # Get first file's directory
        first_uri = output_files[0].output_uri
        if '/' in first_uri:
            parts = first_uri.rsplit('/', 1)
            return parts[0] + '/'
        
        return ""
    
    def _estimate_costs(self, toc_discovery: Optional[TOCDiscoveryResult],
                       toc_parse: Optional[TOCParseResult],
                       output_files: Optional[List[OutputFile]]) -> Dict[str, Any]:
        """
        Estimate AWS costs for processing.
        
        This is a placeholder - real implementation would track actual costs.
        """
        cost_estimate = {
            'textract_pages': len(toc_discovery.toc_pages) if toc_discovery else 0,
            'bedrock_tokens': 0,  # Would track actual token usage
            'estimated_cost_usd': 0.0
        }
        
        # Rough estimates (as of 2024):
        # Textract: $0.0015 per page
        # Bedrock Claude: $0.008 per 1K input tokens, $0.024 per 1K output tokens
        
        if toc_discovery:
            cost_estimate['estimated_cost_usd'] += len(toc_discovery.toc_pages) * 0.0015
        
        if toc_parse and toc_parse.extraction_method == 'bedrock':
            # Estimate ~2000 tokens for TOC parsing
            cost_estimate['bedrock_tokens'] = 2000
            cost_estimate['estimated_cost_usd'] += (2000 / 1000) * 0.008
        
        return cost_estimate
    
    def write_manifest_to_s3(self, manifest: Manifest, output_bucket: str,
                            output_key: str) -> str:
        """
        Write manifest.json to S3 or local filesystem.
        
        Args:
            manifest: Manifest object
            output_bucket: S3 bucket name
            output_key: S3 key or relative path
        
        Returns:
            S3 URI or local path
        """
        try:
            # Convert manifest to JSON
            manifest_json = json.dumps(manifest.to_dict(), indent=2)
            manifest_bytes = manifest_json.encode('utf-8')
            
            # Write using S3Utils
            output_uri = self.s3_utils.write_bytes(
                data=manifest_bytes,
                bucket=output_bucket,
                key=output_key
            )
            
            logger.info(f"Wrote manifest to {output_uri}")
            return output_uri
            
        except Exception as e:
            logger.error(f"Error writing manifest: {e}")
            raise
