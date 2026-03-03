#!/usr/bin/env python3
"""
Standalone GIF Preprocessing Script for MWAHAHA Pipeline
=========================================================

This script processes GIFs from task-b1.tsv and task-b2.tsv files:
1. Downloads each GIF from URL
2. Converts GIF to MP4 (required for vision models)
3. Sends to OpenRouter (Gemini 2.5 Flash) for detailed text description
4. Saves results to TSV files with resume capability

Usage:
    python preprocess_gifs.py --task b1          # Process task-b1.tsv
    python preprocess_gifs.py --task b2          # Process task-b2.tsv
    python preprocess_gifs.py --task all         # Process both tasks
    python preprocess_gifs.py --task b1 --resume # Resume from where left off
    python preprocess_gifs.py --task b1 -v       # Verbose mode with debug logs

Requirements:
    - requests
    - ffmpeg (system binary)

Environment Variables:
    - OPENROUTER_API_KEY: Your OpenRouter API key
"""

import os
import csv
import sys
import time
import base64
import logging
import argparse
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

import requests

# =============================================================================
# Logging Configuration
# =============================================================================

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and symbols for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    SYMBOLS = {
        'DEBUG': '🔍',
        'INFO': '✓',
        'WARNING': '⚠',
        'ERROR': '✗',
        'CRITICAL': '💀',
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        symbol = self.SYMBOLS.get(record.levelname, '')
        reset = self.RESET
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Build formatted message
        formatted = f"{color}{symbol} [{timestamp}] {record.getMessage()}{reset}"
        
        return formatted


def setup_logging(verbose: bool = False):
    """Configure logging with colored output."""
    logger = logging.getLogger('gif_preprocessor')
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
log = setup_logging()

# =============================================================================
# Configuration
# =============================================================================

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "your-openrouter-api-key-here")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"  # Vision-capable model

# HTTP Status Code Descriptions
HTTP_STATUS_NAMES = {
    200: "OK",
    400: "Bad Request",
    401: "Unauthorized", 
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    408: "Request Timeout",
    429: "Too Many Requests (Rate Limited)",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}

# Timeout Configuration
API_TIMEOUT = 120  # seconds for OpenRouter request

# Timeout Configuration
API_TIMEOUT = 120  # seconds for OpenRouter request
GIF_DOWNLOAD_TIMEOUT = 15  # seconds
GIF_CONVERSION_TIMEOUT = 60  # seconds

# Directory Configuration
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / "Input"
OUTPUT_DIR = SCRIPT_DIR / "preprocessed"

# =============================================================================
# Utility Functions
# =============================================================================

def sanitize_text_for_tsv(text: str) -> str:
    """Sanitize text for TSV format by replacing newlines with spaces."""
    if not text:
        return text
    # Replace newlines and tabs with spaces, collapse multiple spaces
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # Collapse multiple spaces into single space
    while '  ' in text:
        text = text.replace('  ', ' ')
    return text.strip()


def format_bytes(num_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def get_status_description(status_code: int) -> str:
    """Get human-readable description for HTTP status code."""
    return HTTP_STATUS_NAMES.get(status_code, "Unknown Status")


# Retry Configuration (in seconds)
RETRY_INTERVALS = [2, 5, 10, 30, 60, 120]
MAX_RETRIES = len(RETRY_INTERVALS)


# =============================================================================
# Analysis Prompts
# =============================================================================

PROMPT_B1_GIF_ANALYSIS = """Analyze this GIF/video in comprehensive detail for humor generation purposes.

**Your Task:**
Provide a thorough, objective description that captures EVERYTHING visible and happening in this GIF. This description will be used by a humor generation system, so include details that could inspire creative comedy.

**Required Analysis:**

1. **Visual Content:**
   - Describe all subjects (people, animals, objects) with specific details (appearance, expressions, clothing, colors)
   - Note the setting/environment (location type, lighting, atmosphere)
   - Identify any text, logos, or graphics visible

2. **Action & Motion:**
   - Describe the complete sequence of events from start to finish
   - Note timing, speed, and rhythm of movements
   - Identify the key moment or climax of the action
   - Describe body language and facial expressions throughout

3. **Context Clues:**
   - What situation or scenario does this appear to be?
   - Any cultural references, memes, or recognizable formats?
   - What expectations are set up, and are they subverted?

4. **Comedic Elements (if present):**
   - Physical comedy (falls, reactions, timing)
   - Unexpected elements or surprises
   - Relatable situations or universal experiences
   - Exaggeration or absurdity

5. **Emotional Tone:**
   - What emotions are conveyed by subjects in the GIF?
   - What emotional response might viewers have?

**Output Format:**
Provide your analysis as flowing prose (300-500 words), organized logically. Be specific and vivid - a reader should be able to visualize the GIF clearly from your description alone."""

PROMPT_B2_GIF_ANALYSIS = """Analyze this GIF/video in the context of the provided humor prompt.

**The Humor Prompt:**
"{prompt}"

**Your Task:**
Provide a detailed description of this GIF that specifically highlights elements relevant to completing the humor prompt above. Focus on what makes this GIF suitable for this particular comedic context.

**Required Analysis:**

1. **Visual Content Summary:**
   - Key subjects and their appearance
   - Setting and atmosphere
   - Notable visual elements

2. **Action Description:**
   - What happens in the GIF (sequence of events)
   - Key moments and timing
   - Expressions and reactions shown

3. **Prompt Relevance:**
   - How does the GIF content relate to the prompt scenario?
   - What emotions/reactions shown could complete the blank?
   - What situational comedy does this GIF suggest?

4. **Comedic Potential:**
   - What makes this GIF funny or relatable?
   - What universal experiences does it capture?
   - What unexpected or exaggerated elements are present?

**Output Format:**
Provide a focused analysis (200-400 words) that emphasizes elements most useful for generating a funny completion to the prompt. Be specific about expressions, actions, and reactions that suggest particular punchlines."""

# =============================================================================
# GIF Processing Functions  
# =============================================================================

def download_gif(url: str, record_id: str, timeout: int = GIF_DOWNLOAD_TIMEOUT) -> bytes:
    """
    Download a GIF from URL and return its bytes.
    
    Args:
        url: URL of the GIF to download
        record_id: ID for logging purposes
        timeout: Request timeout in seconds
        
    Returns:
        GIF content as bytes
        
    Raises:
        requests.RequestException: If download fails
    """
    log.debug(f"  📥 DOWNLOAD: Starting download from {url[:60]}...")
    
    start_time = time.time()
    
    try:
        response = requests.get(url, timeout=timeout)
        elapsed = time.time() - start_time
        
        status_desc = get_status_description(response.status_code)
        
        if response.status_code != 200:
            log.error(f"  📥 DOWNLOAD FAILED: HTTP {response.status_code} ({status_desc})")
            response.raise_for_status()
        
        content_length = len(response.content)
        log.info(f"  📥 DOWNLOAD: Complete - {format_bytes(content_length)} in {elapsed:.2f}s (HTTP 200 OK)")
        
        return response.content
        
    except requests.Timeout:
        log.error(f"  📥 DOWNLOAD TIMEOUT: Request timed out after {timeout}s")
        raise
        
    except requests.ConnectionError as e:
        log.error(f"  📥 DOWNLOAD CONNECTION ERROR: {e}")
        raise
        
    except requests.HTTPError as e:
        log.error(f"  📥 DOWNLOAD HTTP ERROR: {e}")
        raise


def convert_gif_to_mp4(gif_bytes: bytes, record_id: str, timeout: int = GIF_CONVERSION_TIMEOUT) -> bytes:
    """
    Convert GIF bytes to MP4 format using ffmpeg.
    
    Args:
        gif_bytes: GIF content as bytes
        record_id: ID for logging purposes
        timeout: Conversion timeout in seconds
        
    Returns:
        MP4 content as bytes
        
    Raises:
        subprocess.CalledProcessError: If ffmpeg conversion fails
        subprocess.TimeoutExpired: If conversion times out
    """
    log.debug(f"  🔄 CONVERT: Starting GIF→MP4 conversion ({format_bytes(len(gif_bytes))} input)...")
    
    with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as gif_file:
        gif_file.write(gif_bytes)
        gif_path = gif_file.name
    
    mp4_path = gif_path.replace('.gif', '.mp4')
    
    try:
        start_time = time.time()
        
        # ffmpeg command to convert GIF to MP4 with proper pixel format
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-i', gif_path,   # Input GIF
            '-movflags', 'faststart',  # Enable streaming
            '-pix_fmt', 'yuv420p',     # Standard pixel format
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',  # Ensure even dimensions
            '-loglevel', 'error',  # Suppress verbose output
            mp4_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            check=False  # Don't raise immediately, we want to log the error
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='replace')
            log.error(f"  🔄 CONVERT FAILED: ffmpeg exit code {result.returncode}")
            log.error(f"  🔄 CONVERT ERROR: {stderr[:200]}")
            result.check_returncode()  # Raise the exception
        
        with open(mp4_path, 'rb') as f:
            mp4_bytes = f.read()
        
        log.info(f"  🔄 CONVERT: Complete - {format_bytes(len(mp4_bytes))} output in {elapsed:.2f}s (ffmpeg exit 0)")
        
        return mp4_bytes
            
    except subprocess.TimeoutExpired:
        log.error(f"  🔄 CONVERT TIMEOUT: ffmpeg timed out after {timeout}s")
        raise
        
    finally:
        # Cleanup temp files
        if os.path.exists(gif_path):
            os.remove(gif_path)
        if os.path.exists(mp4_path):
            os.remove(mp4_path)


def call_openrouter(
    video_bytes: bytes,
    prompt: str,
    record_id: str
) -> Tuple[str, dict]:
    """
    Call OpenRouter API with video content.
    
    Args:
        video_bytes: MP4 video content as bytes
        prompt: Analysis prompt
        record_id: ID for logging purposes
        
    Returns:
        Tuple of (response_text, usage_stats)
        
    Raises:
        requests.RequestException: If API call fails
    """
    log.debug(f"  📤 UPLOAD: Encoding video to base64...")
    
    # Encode video to base64
    video_base64 = base64.b64encode(video_bytes).decode('utf-8')
    encoded_size = len(video_base64)
    
    log.info(f"  📤 UPLOAD: Encoded {format_bytes(len(video_bytes))} → {format_bytes(encoded_size)} base64")
    
    # Prepare request payload
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": f"data:video/mp4;base64,{video_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "max_tokens": 2048,
        "temperature": 0.3
    }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/mwahaha-pipeline",
        "X-Title": "MWAHAHA GIF Preprocessor"
    }
    
    log.debug(f"  🌐 API: Sending request to OpenRouter ({OPENROUTER_MODEL})...")
    
    start_time = time.time()
    
    response = requests.post(
        OPENROUTER_BASE_URL,
        json=payload,
        headers=headers,
        timeout=API_TIMEOUT
    )
    
    elapsed = time.time() - start_time
    status_desc = get_status_description(response.status_code)
    
    # Log response status
    if response.status_code == 200:
        log.info(f"  🌐 API: Response received - HTTP {response.status_code} ({status_desc}) in {elapsed:.2f}s")
    else:
        log.error(f"  🌐 API FAILED: HTTP {response.status_code} ({status_desc}) in {elapsed:.2f}s")
        
        # Try to get error details from response
        try:
            error_data = response.json()
            if 'error' in error_data:
                error_msg = error_data['error'].get('message', str(error_data['error']))
                error_code = error_data['error'].get('code', 'unknown')
                log.error(f"  🌐 API ERROR: [{error_code}] {error_msg}")
        except:
            log.error(f"  🌐 API ERROR: {response.text[:200]}")
        
        response.raise_for_status()
    
    # Parse response
    data = response.json()
    
    # Extract usage stats
    usage = data.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
    
    log.debug(f"  📊 TOKENS: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}")
    
    # Extract response text
    if 'choices' not in data or len(data['choices']) == 0:
        log.error(f"  🌐 API ERROR: No choices in response")
        raise ValueError("No choices in API response")
    
    response_text = data['choices'][0]['message']['content']
    
    log.info(f"  📝 RESPONSE: Received {len(response_text)} chars, {total_tokens} tokens")
    
    return response_text, usage


def call_openrouter_with_retry(
    video_bytes: bytes,
    prompt: str,
    record_id: str
) -> str:
    """
    Call OpenRouter API with exponential backoff retry logic.
    
    Args:
        video_bytes: MP4 video content as bytes
        prompt: Analysis prompt
        record_id: ID for logging purposes
        
    Returns:
        Generated text response
        
    Raises:
        Exception: If all retries are exhausted
    """
    last_exception = None
    
    for attempt, wait_time in enumerate(RETRY_INTERVALS):
        try:
            response_text, usage = call_openrouter(video_bytes, prompt, record_id)
            return response_text
            
        except requests.HTTPError as e:
            last_exception = e
            status_code = e.response.status_code if e.response is not None else 0
            
            # Retryable status codes
            if status_code in [429, 500, 502, 503, 504]:
                log.warning(f"  ⏳ RETRY: HTTP {status_code} - attempt {attempt + 1}/{MAX_RETRIES}, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Non-retryable error
                log.error(f"  💀 FATAL: HTTP {status_code} is not retryable")
                raise
                
        except requests.Timeout:
            last_exception = requests.Timeout("API request timed out")
            log.warning(f"  ⏳ RETRY: Timeout - attempt {attempt + 1}/{MAX_RETRIES}, waiting {wait_time}s...")
            time.sleep(wait_time)
            
        except requests.ConnectionError as e:
            last_exception = e
            log.warning(f"  ⏳ RETRY: Connection error - attempt {attempt + 1}/{MAX_RETRIES}, waiting {wait_time}s...")
            time.sleep(wait_time)
            
        except Exception as e:
            last_exception = e
            error_str = str(e).lower()
            
            # Check if it's a rate limit error in the message
            if any(keyword in error_str for keyword in ['rate', 'quota', 'limit', 'resource']):
                log.warning(f"  ⏳ RETRY: Rate limited - attempt {attempt + 1}/{MAX_RETRIES}, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Non-retryable error
                log.error(f"  💀 FATAL: Unexpected error: {e}")
                raise
    
    log.error(f"  💀 EXHAUSTED: All {MAX_RETRIES} retry attempts failed")
    raise last_exception


def analyze_gif_b1(url: str, record_id: str) -> str:
    """
    Analyze a GIF for Task B1 (open-ended analysis).
    
    Args:
        url: URL of the GIF to analyze
        record_id: ID for logging purposes
        
    Returns:
        Detailed text description of the GIF
    """
    log.info(f"  🎬 PIPELINE: Starting B1 analysis for {record_id}")
    
    # Step 1: Download
    gif_bytes = download_gif(url, record_id)
    
    # Step 2: Convert
    mp4_bytes = convert_gif_to_mp4(gif_bytes, record_id)
    
    # Step 3: Analyze
    description = call_openrouter_with_retry(mp4_bytes, PROMPT_B1_GIF_ANALYSIS, record_id)
    
    log.info(f"  🎬 PIPELINE: B1 analysis complete for {record_id}")
    
    return description


def analyze_gif_b2(url: str, prompt: str, record_id: str) -> str:
    """
    Analyze a GIF for Task B2 (prompt-contextualized analysis).
    
    Args:
        url: URL of the GIF to analyze
        prompt: The humor prompt for context
        record_id: ID for logging purposes
        
    Returns:
        Context-aware text description of the GIF
    """
    log.info(f"  🎬 PIPELINE: Starting B2 analysis for {record_id}")
    
    # Step 1: Download
    gif_bytes = download_gif(url, record_id)
    
    # Step 2: Convert
    mp4_bytes = convert_gif_to_mp4(gif_bytes, record_id)
    
    # Step 3: Analyze with contextualized prompt
    analysis_prompt = PROMPT_B2_GIF_ANALYSIS.format(prompt=prompt)
    description = call_openrouter_with_retry(mp4_bytes, analysis_prompt, record_id)
    
    log.info(f"  🎬 PIPELINE: B2 analysis complete for {record_id}")
    
    return description


# =============================================================================
# Data Loading and Saving Functions
# =============================================================================

def load_input_b1(input_path: Path) -> list[dict]:
    """Load task-b1.tsv input file."""
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            records.append({
                'id': row['id'],
                'url': row['url']
            })
    return records


def load_input_b2(input_path: Path) -> list[dict]:
    """Load task-b2.tsv input file."""
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            records.append({
                'id': row['id'],
                'url': row['url'],
                'prompt': row['prompt']
            })
    return records


def load_existing_outputs(output_path: Path) -> set[str]:
    """Load existing output file and return set of processed IDs."""
    processed_ids = set()
    
    if not output_path.exists():
        return processed_ids
    
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row.get('id'):
                processed_ids.add(row['id'])
    
    return processed_ids


def save_result_b1(output_path: Path, record: dict, description: str, append: bool = True):
    """Save a single B1 result to TSV file."""
    file_exists = output_path.exists()
    mode = 'a' if append else 'w'
    
    with open(output_path, mode, encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        
        # Write header if new file
        if not file_exists or not append:
            writer.writerow(['id', 'url', 'description'])
        
        writer.writerow([
            record['id'],
            record['url'],
            sanitize_text_for_tsv(description)
        ])


def save_result_b2(output_path: Path, record: dict, description: str, append: bool = True):
    """Save a single B2 result to TSV file."""
    file_exists = output_path.exists()
    mode = 'a' if append else 'w'
    
    with open(output_path, mode, encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        
        # Write header if new file
        if not file_exists or not append:
            writer.writerow(['id', 'url', 'prompt', 'description'])
        
        writer.writerow([
            record['id'],
            record['url'],
            record['prompt'],
            sanitize_text_for_tsv(description)
        ])


# =============================================================================
# Main Processing Functions
# =============================================================================

def process_task_b1(resume: bool = True, limit: Optional[int] = None, verbose: bool = False):
    """
    Process all GIFs from task-b1.tsv.
    
    Args:
        resume: If True, skip already processed IDs
        limit: If set, only process this many GIFs (for testing)
        verbose: Enable debug logging
    """
    print("=" * 70)
    print("🚀 Processing Task B1 (Open-ended GIF Analysis)")
    print(f"   Model: {OPENROUTER_MODEL}")
    print(f"   API: OpenRouter")
    print("=" * 70)
    
    # Setup paths
    input_path = INPUT_DIR / "task-b1.tsv"
    output_path = OUTPUT_DIR / "task-b1-preprocessed.tsv"
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load input data
    records = load_input_b1(input_path)
    log.info(f"📂 Loaded {len(records)} records from {input_path}")
    
    # Load existing outputs for resume
    processed_ids = set()
    if resume:
        processed_ids = load_existing_outputs(output_path)
        if processed_ids:
            log.info(f"📂 Resuming: {len(processed_ids)} already processed")
    
    # Filter to unprocessed records
    pending = [r for r in records if r['id'] not in processed_ids]
    
    if limit:
        pending = pending[:limit]
        log.info(f"📂 Limit applied: processing only {limit} GIFs")
    
    log.info(f"📋 Processing {len(pending)} GIFs...")
    print()
    
    # Process each GIF
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    for i, record in enumerate(pending, 1):
        record_id = record['id']
        print(f"[{i}/{len(pending)}] 🖼️  {record_id}")
        
        try:
            description = analyze_gif_b1(record['url'], record_id)
            save_result_b1(output_path, record, description)
            success_count += 1
            log.info(f"  💾 SAVED: {record_id} ({len(description)} chars)")
            
        except requests.Timeout:
            error_count += 1
            log.error(f"  ❌ FAILED: {record_id} - Request timeout")
            
        except requests.HTTPError as e:
            error_count += 1
            status = e.response.status_code if e.response is not None else "unknown"
            status_desc = get_status_description(status) if isinstance(status, int) else ""
            log.error(f"  ❌ FAILED: {record_id} - HTTP {status} ({status_desc})")
            
        except subprocess.CalledProcessError as e:
            error_count += 1
            log.error(f"  ❌ FAILED: {record_id} - ffmpeg exit code {e.returncode}")
            
        except Exception as e:
            error_count += 1
            log.error(f"  ❌ FAILED: {record_id} - {type(e).__name__}: {e}")
        
        print()  # Blank line between records
        
        # Small delay between requests to avoid rate limiting
        if i < len(pending):
            time.sleep(1)
    
    elapsed = time.time() - start_time
    
    print("=" * 70)
    print(f"✅ Task B1 Complete")
    print(f"   Success: {success_count}")
    print(f"   Errors:  {error_count}")
    print(f"   Time:    {elapsed:.1f}s ({elapsed/max(len(pending),1):.1f}s/GIF avg)")
    print(f"   Output:  {output_path}")
    print("=" * 70)


def process_task_b2(resume: bool = True, limit: Optional[int] = None, verbose: bool = False):
    """
    Process all GIFs from task-b2.tsv.
    
    Args:
        resume: If True, skip already processed IDs
        limit: If set, only process this many GIFs (for testing)
        verbose: Enable debug logging
    """
    print("=" * 70)
    print("🚀 Processing Task B2 (Prompt-Contextualized GIF Analysis)")
    print(f"   Model: {OPENROUTER_MODEL}")
    print(f"   API: OpenRouter")
    print("=" * 70)
    
    # Setup paths
    input_path = INPUT_DIR / "task-b2.tsv"
    output_path = OUTPUT_DIR / "task-b2-preprocessed.tsv"
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load input data
    records = load_input_b2(input_path)
    log.info(f"📂 Loaded {len(records)} records from {input_path}")
    
    # Load existing outputs for resume
    processed_ids = set()
    if resume:
        processed_ids = load_existing_outputs(output_path)
        if processed_ids:
            log.info(f"📂 Resuming: {len(processed_ids)} already processed")
    
    # Filter to unprocessed records
    pending = [r for r in records if r['id'] not in processed_ids]
    
    if limit:
        pending = pending[:limit]
        log.info(f"📂 Limit applied: processing only {limit} GIFs")
    
    log.info(f"📋 Processing {len(pending)} GIFs...")
    print()
    
    # Process each GIF
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    for i, record in enumerate(pending, 1):
        record_id = record['id']
        print(f"[{i}/{len(pending)}] 🖼️  {record_id}")
        log.info(f"  📝 PROMPT: {record['prompt'][:60]}...")
        
        try:
            description = analyze_gif_b2(record['url'], record['prompt'], record_id)
            save_result_b2(output_path, record, description)
            success_count += 1
            log.info(f"  💾 SAVED: {record_id} ({len(description)} chars)")
            
        except requests.Timeout:
            error_count += 1
            log.error(f"  ❌ FAILED: {record_id} - Request timeout")
            
        except requests.HTTPError as e:
            error_count += 1
            status = e.response.status_code if e.response is not None else "unknown"
            status_desc = get_status_description(status) if isinstance(status, int) else ""
            log.error(f"  ❌ FAILED: {record_id} - HTTP {status} ({status_desc})")
            
        except subprocess.CalledProcessError as e:
            error_count += 1
            log.error(f"  ❌ FAILED: {record_id} - ffmpeg exit code {e.returncode}")
            
        except Exception as e:
            error_count += 1
            log.error(f"  ❌ FAILED: {record_id} - {type(e).__name__}: {e}")
        
        print()  # Blank line between records
        
        # Small delay between requests to avoid rate limiting
        if i < len(pending):
            time.sleep(1)
    
    elapsed = time.time() - start_time
    
    print("=" * 70)
    print(f"✅ Task B2 Complete")
    print(f"   Success: {success_count}")
    print(f"   Errors:  {error_count}")
    print(f"   Time:    {elapsed:.1f}s ({elapsed/max(len(pending),1):.1f}s/GIF avg)")
    print(f"   Output:  {output_path}")
    print("=" * 70)


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Preprocess GIFs for MWAHAHA humor generation pipeline (OpenRouter)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python preprocess_gifs.py --task b1           # Process task B1 GIFs
    python preprocess_gifs.py --task b2           # Process task B2 GIFs
    python preprocess_gifs.py --task all          # Process both tasks
    python preprocess_gifs.py --task b1 --limit 5 # Process only 5 GIFs (for testing)
    python preprocess_gifs.py --task b1 --no-resume  # Start fresh, ignore existing
    python preprocess_gifs.py --task b1 -v        # Verbose mode with debug logs

Output files:
    preprocessed/task-b1-preprocessed.tsv  - B1 results (id, url, description)
    preprocessed/task-b2-preprocessed.tsv  - B2 results (id, url, prompt, description)

Environment:
    OPENROUTER_API_KEY - Your OpenRouter API key (required)
        """
    )
    
    parser.add_argument(
        '--task', '-t',
        choices=['b1', 'b2', 'all'],
        required=True,
        help="Which task to process: b1, b2, or all"
    )
    
    parser.add_argument(
        '--resume/--no-resume',
        dest='resume',
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Resume from where left off (default: True)"
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help="Limit number of GIFs to process (for testing)"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Enable verbose/debug logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging based on verbosity
    global log
    log = setup_logging(verbose=args.verbose)
    
    # Validate environment
    if not OPENROUTER_API_KEY:
        print("❌ ERROR: OPENROUTER_API_KEY environment variable not set!")
        print("   Set it with: export OPENROUTER_API_KEY='your-key-here'")
        return 1
    
    log.info(f"🔑 API Key: {OPENROUTER_API_KEY[:8]}...{OPENROUTER_API_KEY[-4:]}")
    
    # Check ffmpeg is available
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        # Extract version from first line
        version_line = result.stdout.decode().split('\n')[0]
        log.info(f"🎬 ffmpeg: {version_line[:50]}...")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ERROR: ffmpeg not found!")
        print("   Install it with: sudo apt install ffmpeg")
        return 1
    
    # Check input files exist
    if args.task in ['b1', 'all']:
        if not (INPUT_DIR / "task-b1.tsv").exists():
            print(f"❌ ERROR: Input file not found: {INPUT_DIR / 'task-b1.tsv'}")
            return 1
    
    if args.task in ['b2', 'all']:
        if not (INPUT_DIR / "task-b2.tsv").exists():
            print(f"❌ ERROR: Input file not found: {INPUT_DIR / 'task-b2.tsv'}")
            return 1
    
    print()
    
    # Process tasks
    try:
        if args.task in ['b1', 'all']:
            process_task_b1(resume=args.resume, limit=args.limit, verbose=args.verbose)
        
        if args.task == 'all':
            print("\n")
        
        if args.task in ['b2', 'all']:
            process_task_b2(resume=args.resume, limit=args.limit, verbose=args.verbose)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Progress has been saved.")
        return 130
    
    except Exception as e:
        log.critical(f"💀 FATAL ERROR: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
