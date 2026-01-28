"""
Bedrock Integration Module - LLM-based fallback TOC parser.

This module provides:
- Bedrock Claude API integration for TOC parsing
- Token limiting (4000 input, 2000 output)
- JSON response parsing
- Mock Bedrock for local testing
"""

import json
from typing import List, Optional, Dict
import logging
import boto3
from botocore.exceptions import ClientError
from app.models import TOCEntry, TOCParseResult

logger = logging.getLogger(__name__)


class MockBedrock:
    """Mock Bedrock implementation for local mode."""
    
    def __init__(self):
        logger.info("MockBedrock initialized")
    
    def invoke_model(self, modelId: str, body: str) -> dict:
        """
        Mock Bedrock model invocation.
        
        Returns a realistic mock response for TOC parsing.
        """
        # Parse the request to understand what's being asked
        request_body = json.loads(body)
        
        # Return a mock TOC parsing response
        mock_entries = [
            {"song_title": "Amazing Grace", "page_number": 5},
            {"song_title": "Ave Maria", "page_number": 12},
            {"song_title": "Canon in D", "page_number": 18},
            {"song_title": "Danny Boy", "page_number": 24},
            {"song_title": "Edelweiss", "page_number": 30},
            {"song_title": "Greensleeves", "page_number": 36},
            {"song_title": "Hallelujah", "page_number": 42},
            {"song_title": "Imagine", "page_number": 48},
            {"song_title": "Let It Be", "page_number": 54},
            {"song_title": "Yesterday", "page_number": 60}
        ]
        
        response_text = json.dumps(mock_entries)
        
        # Mimic Bedrock response structure
        return {
            'body': {
                'content': [
                    {
                        'text': response_text
                    }
                ],
                'usage': {
                    'input_tokens': 500,
                    'output_tokens': 200
                }
            }
        }


class BedrockParserService:
    """Service for LLM-based TOC parsing using Bedrock."""
    
    def __init__(self, local_mode: bool = False, model_id: str = 'anthropic.claude-3-sonnet-20240229-v1:0'):
        """
        Initialize Bedrock parser service.
        
        Args:
            local_mode: If True, use mock Bedrock
            model_id: Bedrock model ID to use
        """
        self.local_mode = local_mode
        self.model_id = model_id
        self.max_input_tokens = 4000
        self.max_output_tokens = 2000
        
        if local_mode:
            self.bedrock = MockBedrock()
            logger.info("BedrockParserService initialized in local mode")
        else:
            self.bedrock_runtime = boto3.client('bedrock-runtime')
            logger.info(f"BedrockParserService initialized with model {model_id}")
    
    def bedrock_vision_parse(self, toc_images: List, book_metadata: Optional[Dict] = None) -> TOCParseResult:
        """
        Use Claude vision via Bedrock to parse TOC from images.
        
        Args:
            toc_images: List of PIL Image objects of TOC pages
            book_metadata: Optional metadata about the book
        
        Returns:
            TOCParseResult with parsed entries
        """
        import base64
        import io
        from PIL import Image
        
        logger.info(f"Starting Bedrock vision parsing with {len(toc_images)} images")
        
        # Construct prompt
        artist = book_metadata.get('artist', 'Unknown') if book_metadata else 'Unknown'
        book_name = book_metadata.get('book_name', 'Unknown') if book_metadata else 'Unknown'
        
        prompt = f"""Analyze these Table of Contents pages from a music book and extract all songs with their page numbers.

Book information:
- Artist: {artist}
- Book name: {book_name}

Instructions:
1. Look at the visual layout of the TOC - it may have multiple columns, dots connecting titles to page numbers, or other formatting
2. Extract ALL song titles and their corresponding page numbers
3. Pay attention to the spatial relationship between titles and numbers
4. Ignore headers, footers, copyright notices, and non-song entries
5. If artist information is shown per-song, include it

Return a JSON array ONLY (no other text):
[
  {{"song_title": "Song Name", "page_number": 42, "artist": "Artist Name (optional)"}},
  ...
]"""

        # Convert images to base64
        image_content = []
        for i, img in enumerate(toc_images):
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            image_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
            
            image_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_base64
                }
            })
        
        # Add text prompt after images
        image_content.append({
            "type": "text",
            "text": prompt
        })
        
        # Call Bedrock
        try:
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_output_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": image_content
                    }
                ],
                "temperature": 0.0
            }
            
            body_json = json.dumps(request_body)
            
            if self.local_mode:
                # Mock response for local mode
                logger.info("Local mode: Using mock Bedrock vision response")
                mock_entries = [
                    TOCEntry(song_title="Big Shot", page_number=10, confidence=0.85),
                    TOCEntry(song_title="52nd Street", page_number=68, confidence=0.85),
                    TOCEntry(song_title="Half A Mile Away", page_number=52, confidence=0.85),
                    TOCEntry(song_title="Honesty", page_number=19, confidence=0.85),
                    TOCEntry(song_title="My Life", page_number=25, confidence=0.85),
                    TOCEntry(song_title="Rosalinda's Eyes", page_number=46, confidence=0.85),
                    TOCEntry(song_title="Stiletto", page_number=40, confidence=0.85),
                    TOCEntry(song_title="Until The Night", page_number=60, confidence=0.85),
                    TOCEntry(song_title="Zanzibar", page_number=33, confidence=0.85),
                ]
                return TOCParseResult(
                    entries=mock_entries,
                    extraction_method='bedrock_vision',
                    confidence=0.90,
                    artist_overrides={}
                )
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=body_json
            )
            
            response_body = json.loads(response['body'].read())
            response_text = response_body['content'][0]['text']
            
            # Parse JSON response
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                entries_data = json.loads(json_match.group(0))
                
                entries = []
                for entry_data in entries_data:
                    if 'song_title' in entry_data and 'page_number' in entry_data:
                        entry = TOCEntry(
                            song_title=entry_data['song_title'],
                            page_number=int(entry_data['page_number']),
                            artist=entry_data.get('artist'),
                            confidence=0.90
                        )
                        entries.append(entry)
                
                logger.info(f"Bedrock vision parsing succeeded with {len(entries)} entries")
                return TOCParseResult(
                    entries=entries,
                    extraction_method='bedrock_vision',
                    confidence=0.90,
                    artist_overrides=self._extract_artist_overrides(entries)
                )
            else:
                logger.error("Could not find JSON array in Bedrock response")
                return TOCParseResult(entries=[], extraction_method='bedrock_vision', confidence=0.0, artist_overrides={})
                
        except Exception as e:
            logger.error(f"Bedrock vision parsing failed: {e}", exc_info=True)
            return TOCParseResult(entries=[], extraction_method='bedrock_vision', confidence=0.0, artist_overrides={})
    
    def bedrock_fallback_parse(self, toc_text: str, book_metadata: Optional[Dict] = None) -> TOCParseResult:
        """
        Use Claude via Bedrock to parse TOC.
        
        Args:
            toc_text: Extracted text from TOC pages
            book_metadata: Optional metadata about the book
        
        Returns:
            TOCParseResult with parsed entries
        """
        logger.info("Starting Bedrock fallback parsing")
        
        # Limit input text to max tokens
        limited_text = self._limit_input_text(toc_text, self.max_input_tokens)
        
        # Construct prompt
        prompt = self._construct_prompt(limited_text, book_metadata or {})
        
        # Call Bedrock
        try:
            response = self._invoke_bedrock(prompt)
            
            # Parse response
            entries = self._parse_response(response)
            
            if entries and len(entries) >= 10:
                logger.info(f"Bedrock parsing succeeded with {len(entries)} entries")
                return TOCParseResult(
                    entries=entries,
                    extraction_method='bedrock',
                    confidence=0.85,
                    artist_overrides=self._extract_artist_overrides(entries)
                )
            else:
                logger.warning(f"Bedrock parsing produced only {len(entries) if entries else 0} entries")
                return TOCParseResult(
                    entries=entries or [],
                    extraction_method='bedrock',
                    confidence=0.5 if entries else 0.0,
                    artist_overrides={}
                )
                
        except Exception as e:
            logger.error(f"Bedrock parsing failed: {e}")
            return TOCParseResult(
                entries=[],
                extraction_method='bedrock',
                confidence=0.0,
                artist_overrides={}
            )
    
    def _limit_input_text(self, text: str, max_tokens: int) -> str:
        """
        Limit input text to maximum token count.
        
        Uses rough approximation: 1 token ≈ 4 characters.
        
        Args:
            text: Input text
            max_tokens: Maximum number of tokens
        
        Returns:
            Truncated text
        """
        max_chars = max_tokens * 4
        
        if len(text) <= max_chars:
            return text
        
        truncated = text[:max_chars]
        logger.warning(f"Input text truncated from {len(text)} to {len(truncated)} characters")
        
        return truncated
    
    def _construct_prompt(self, toc_text: str, book_metadata: Dict) -> str:
        """
        Construct prompt for Bedrock.
        
        Args:
            toc_text: TOC text to parse
            book_metadata: Book metadata
        
        Returns:
            Formatted prompt
        """
        artist = book_metadata.get('artist', 'Unknown')
        book_name = book_metadata.get('book_name', 'Unknown')
        
        prompt = f"""You are parsing a Table of Contents from a songbook PDF. Extract a structured list of songs with their page numbers.

Input text:
{toc_text}

Book metadata:
- Artist: {artist}
- Book name: {book_name}

Return a JSON array of objects with this structure:
[
  {{"song_title": "Song Name", "page_number": 42, "artist": "Artist Name (optional)"}},
  ...
]

Rules:
- Extract all song entries with page numbers
- Preserve exact song titles
- If artist information is present per-song, include it in the "artist" field
- Ignore headers, footers, and non-song entries
- Page numbers should be integers
- Return ONLY the JSON array, no other text

JSON array:"""
        
        return prompt
    
    def _invoke_bedrock(self, prompt: str) -> dict:
        """
        Invoke Bedrock model.
        
        Args:
            prompt: Prompt to send
        
        Returns:
            Bedrock response
        """
        # Construct request body for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_output_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.0  # Deterministic output
        }
        
        body_json = json.dumps(request_body)
        
        if self.local_mode:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=body_json
            )
        else:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=body_json
            )
            
            # Parse response body
            response_body = json.loads(response['body'].read())
            response = {'body': response_body}
        
        return response
    
    def _parse_response(self, response: dict) -> List[TOCEntry]:
        """
        Parse JSON response from Bedrock into TOCEntry objects.
        
        Args:
            response: Bedrock response
        
        Returns:
            List of TOCEntry objects
        """
        try:
            # Extract text from response
            content = response['body']['content'][0]['text']
            
            # Parse JSON
            entries_data = json.loads(content)
            
            # Convert to TOCEntry objects
            entries = []
            for entry_data in entries_data:
                if 'song_title' in entry_data and 'page_number' in entry_data:
                    entry = TOCEntry(
                        song_title=entry_data['song_title'],
                        page_number=int(entry_data['page_number']),
                        artist=entry_data.get('artist'),
                        confidence=0.85
                    )
                    entries.append(entry)
            
            logger.info(f"Parsed {len(entries)} entries from Bedrock response")
            return entries
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error parsing Bedrock response: {e}")
            return []
    
    def _extract_artist_overrides(self, entries: List[TOCEntry]) -> Dict[str, str]:
        """Extract per-song artist information."""
        artist_overrides = {}
        
        for entry in entries:
            if entry.artist:
                artist_overrides[entry.song_title] = entry.artist
        
        if artist_overrides:
            logger.info(f"Extracted {len(artist_overrides)} artist overrides from Bedrock")
        
        return artist_overrides
