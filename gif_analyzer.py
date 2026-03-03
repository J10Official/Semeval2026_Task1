"""
GIF Analyzer Module for the MWAHAHA Humor Generation Pipeline.

This module converts GIF visuals into detailed textual descriptions using
Gemini 2.5 Flash Lite's video understanding capabilities.

The output descriptions are designed to capture all subtleties needed for
effective humor generation in Task B1 (GIF only) and Task B2 (GIF + prompt).

Key Features:
- Converts GIFs to MP4 for Gemini video processing
- Two specialized prompts: B1 (open-ended) and B2 (prompt-contextualized)
- Thorough descriptions optimized for downstream caption generation
- Integrated retry logic for rate limit handling
"""

import time
import logging
import tempfile
import os
import subprocess
import shutil
import threading
from pathlib import Path
from typing import Optional
import requests
import google.generativeai as genai

from config import GEMINI_API_KEY, RETRY_INTERVALS, MAX_RETRIES, GIF_DOWNLOAD_TIMEOUT, GIF_CONVERSION_TIMEOUT

# Configure logging
logger = logging.getLogger("mwahaha")


# =========================================================================
# PROMPTS FOR GIF ANALYSIS
# =========================================================================

# Task B1: GIF Only - Open-ended analysis for caption generation
PROMPT_B1_GIF_ANALYSIS = """You are an expert visual analyst specializing in analyzing GIFs for meme caption generation. Your task is to provide an exhaustive, detailed description of this GIF that will be used by a humor generation system to create funny captions.

## YOUR ANALYSIS MUST CAPTURE:

### 1. SUBJECTS & CHARACTERS
- Who/what is in the GIF? (humans, animals, objects, cartoon characters, etc.)
- Physical appearance: age range, gender presentation, clothing, distinctive features
- If animals: species, breed if identifiable, any anthropomorphic qualities
- If objects: what are they, their condition, any unusual aspects

### 2. ACTIONS & MOVEMENTS (CRITICAL - This is a GIF, motion matters!)
- What is happening frame by frame? Describe the SEQUENCE of events
- Speed and intensity of movements (frantic, slow, deliberate, explosive)
- Direction of movement (approaching, retreating, falling, rising)
- Any looping quirks - does the loop create unintentional comedy?
- Repeated motions, gestures, or actions
- Physical comedy elements: falls, collisions, exaggerated movements

### 3. FACIAL EXPRESSIONS & BODY LANGUAGE
- Emotional state conveyed (joy, frustration, confusion, shock, etc.)
- Changes in expression throughout the GIF
- Eye movements, eyebrow positions, mouth shapes
- Posture and what it communicates
- Hand gestures and their meaning
- The "vibe" or energy the subject gives off

### 4. SETTING & CONTEXT
- Location/environment (indoor, outdoor, office, home, public space)
- Time indicators (day, night, season if apparent)
- Background elements that might be relevant
- Any text visible in the GIF (signs, captions, watermarks)
- Production quality (professional, amateur, movie clip, TV show, etc.)

### 5. COMEDIC POTENTIAL OBSERVATIONS
- What makes this GIF funny or shareable on its own?
- Universal experiences this could represent ("we've all been there" moments)
- Relatable situations or emotions depicted
- Absurdity, irony, or incongruity present
- Meme template potential - what kinds of "When you..." scenarios fit?
- The "mood" this GIF captures (Monday energy, Friday energy, etc.)

### 6. TECHNICAL OBSERVATIONS
- GIF quality and clarity
- Duration/length (short punchy vs. longer narrative)
- Color palette and lighting mood
- Any visual effects or editing

### 7. CULTURAL/CONTEXTUAL NOTES
- If from a known source (movie, TV show, viral video), note it
- Any cultural references or in-jokes apparent
- Internet culture relevance

## OUTPUT FORMAT:
Provide a comprehensive paragraph-form description (300-500 words) that flows naturally and captures ALL the above elements. Write it as if describing the GIF to someone who cannot see it but needs to write the perfect funny caption for it.

Focus especially on MOTION, EXPRESSION, and COMEDIC TIMING - these are what make GIF captions land.

DO NOT suggest captions yourself. Just describe what you see in thorough detail."""


# Task B2: GIF + Prompt - Analysis contextualized by the fill-in-the-blank prompt
PROMPT_B2_GIF_ANALYSIS = """You are an expert visual analyst specializing in analyzing GIFs for meme caption generation. Your task is to provide an exhaustive, detailed description of this GIF that will be used to complete a specific fill-in-the-blank prompt.

## THE PROMPT TO BE COMPLETED:
"{prompt}"

Your description must help a humor system understand how this GIF relates to and can complete this prompt.

## YOUR ANALYSIS MUST CAPTURE:

### 1. SUBJECTS & CHARACTERS
- Who/what is in the GIF? (humans, animals, objects, cartoon characters, etc.)
- Physical appearance: age range, gender presentation, clothing, distinctive features
- If animals: species, breed if identifiable, any anthropomorphic qualities
- If objects: what are they, their condition, any unusual aspects

### 2. ACTIONS & MOVEMENTS (CRITICAL - This is a GIF, motion matters!)
- What is happening frame by frame? Describe the SEQUENCE of events
- Speed and intensity of movements (frantic, slow, deliberate, explosive)
- Direction of movement (approaching, retreating, falling, rising)
- Any looping quirks - does the loop create unintentional comedy?
- Repeated motions, gestures, or actions
- Physical comedy elements: falls, collisions, exaggerated movements

### 3. FACIAL EXPRESSIONS & BODY LANGUAGE
- Emotional state conveyed (joy, frustration, confusion, shock, etc.)
- Changes in expression throughout the GIF
- Eye movements, eyebrow positions, mouth shapes
- Posture and what it communicates
- Hand gestures and their meaning
- The "vibe" or energy the subject gives off

### 4. SETTING & CONTEXT
- Location/environment (indoor, outdoor, office, home, public space)
- Time indicators (day, night, season if apparent)
- Background elements that might be relevant
- Any text visible in the GIF (signs, captions, watermarks)
- Production quality (professional, amateur, movie clip, TV show, etc.)

### 5. PROMPT-SPECIFIC ANALYSIS (CRITICAL FOR TASK B2)
- How does this GIF visually represent or relate to the prompt scenario?
- What emotion, reaction, or state does the GIF show that could complete the blank?
- What specific visual element would be the "punchline" when paired with the prompt?
- How might someone describe what they see as a completion to the prompt?
- What unexpected but fitting completions does this visual suggest?

### 6. COMEDIC POTENTIAL FOR THIS PROMPT
- What makes this GIF the perfect visual "answer" to the prompt?
- The gap between what the prompt might expect and what the GIF delivers
- How the visual either confirms, subverts, or exaggerates the prompt's scenario
- The "mood" or "vibe" this GIF adds to the prompt's setup

### 7. TECHNICAL OBSERVATIONS
- GIF quality and clarity
- Duration/length (short punchy vs. longer narrative)
- Color palette and lighting mood
- Any visual effects or editing

## OUTPUT FORMAT:
Provide a comprehensive paragraph-form description (300-500 words) that flows naturally and captures ALL the above elements. 

CRUCIAL: Your description should make it obvious how this GIF serves as the visual punchline to the given prompt. The humor system needs to understand the connection between what's seen and how it could complete the blank.

Focus especially on MOTION, EXPRESSION, and how they relate to the PROMPT SCENARIO.

DO NOT suggest completions yourself. Just describe what you see in thorough detail, with special attention to how it relates to the prompt."""


# =========================================================================
# GIF ANALYZER CLASS
# =========================================================================

class GIFAnalyzer:
    """
    Analyzes GIF content using Gemini 2.5 Flash Lite's video understanding.
    
    Converts visual GIF content into detailed textual descriptions optimized
    for downstream humor generation in Tasks B1 and B2.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the GIF Analyzer.
        
        Args:
            api_key: Gemini API key. If not provided, uses GEMINI_API_KEY from config.
        """
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Set it in .env or pass directly.")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 2.5 Flash Lite for vision tasks (optimized for speed/cost)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Track usage for debugging
        self.calls_made = 0
        self.last_call_time = 0
    
    def _download_gif(self, url: str) -> Optional[bytes]:
        """
        Download a GIF from a URL.
        
        Args:
            url: URL of the GIF to download
            
        Returns:
            GIF content as bytes, or None if download fails
        """
        try:
            logger.debug(f"Downloading GIF from: {url}")
            response = requests.get(url, timeout=GIF_DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Failed to download GIF from {url}: {e}")
            return None
    
    def _convert_gif_to_mp4(self, gif_path: str) -> Optional[str]:
        """
        Convert a GIF to MP4 using ffmpeg for Gemini video processing.
        
        Args:
            gif_path: Path to the GIF file
            
        Returns:
            Path to the MP4 file, or None if conversion fails
        """
        # Check if ffmpeg is available
        if not shutil.which('ffmpeg'):
            logger.error("ffmpeg not found. Please install ffmpeg for GIF processing.")
            return None
        
        mp4_path = gif_path.replace('.gif', '.mp4')
        
        try:
            # Convert GIF to MP4 with ffmpeg
            # -y: overwrite output, -i: input, -movflags: for web playback
            # -pix_fmt yuv420p: compatible pixel format
            # -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2": ensure even dimensions
            result = subprocess.run(
                [
                    'ffmpeg', '-y',
                    '-i', gif_path,
                    '-movflags', 'faststart',
                    '-pix_fmt', 'yuv420p',
                    '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
                    '-an',  # No audio
                    mp4_path
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"ffmpeg conversion failed: {result.stderr[:500]}")
                return None
            
            logger.debug(f"Converted GIF to MP4: {mp4_path}")
            return mp4_path
            
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg conversion timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to convert GIF to MP4: {e}")
            return None
    
    def _upload_gif_to_gemini(self, gif_bytes: bytes) -> Optional[genai.types.File]:
        """
        Convert GIF to MP4 and upload to Gemini's file API for processing.
        
        Gemini doesn't support GIF directly, so we convert to MP4 first.
        
        Args:
            gif_bytes: GIF content as bytes
            
        Returns:
            Gemini File object, or None if upload fails
        """
        gif_path = None
        mp4_path = None
        
        try:
            # Write GIF to temp file
            with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as tmp:
                tmp.write(gif_bytes)
                gif_path = tmp.name
            
            logger.debug(f"GIF saved to temp file (size: {len(gif_bytes)} bytes)")
            
            # Convert GIF to MP4
            mp4_path = self._convert_gif_to_mp4(gif_path)
            if not mp4_path:
                return None
            
            logger.debug(f"Uploading MP4 to Gemini...")
            
            # Upload the MP4 file
            file = genai.upload_file(mp4_path, mime_type='video/mp4')
            
            # Wait for processing
            while file.state.name == "PROCESSING":
                logger.debug("Waiting for video processing...")
                time.sleep(1)
                file = genai.get_file(file.name)
            
            if file.state.name == "FAILED":
                logger.error(f"Video processing failed: {file.state.name}")
                return None
            
            logger.debug(f"Video upload complete: {file.name}")
            return file
            
        except Exception as e:
            logger.error(f"Failed to upload video to Gemini: {e}")
            return None
        finally:
            # Clean up temp files
            for path in [gif_path, mp4_path]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except:
                        pass
    
    def _call_with_retry(self, file: genai.types.File, prompt: str) -> Optional[str]:
        """
        Call Gemini API with retry logic for rate limits.
        
        Args:
            file: Uploaded GIF file
            prompt: Analysis prompt
            
        Returns:
            Generated description, or None if all retries fail
        """
        last_exception = None
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                logger.debug(f"Calling Gemini API (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    [file, prompt],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.4,  # Lower temp for accurate description
                        max_output_tokens=1024,
                    )
                )
                
                self.calls_made += 1
                self.last_call_time = time.time()
                
                if response.text:
                    return response.text.strip()
                else:
                    logger.warning("Empty response from Gemini")
                    return None
                    
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                logger.error(f"❌ Gemini API Error: {str(e)[:300]}")
                
                # Check if retryable
                is_rate_limit = any(term in error_str for term in [
                    "rate limit", "quota", "429", "resource exhausted",
                    "too many requests"
                ])
                
                is_transient = any(term in error_str for term in [
                    "timeout", "connection", "503", "502", "500", "temporarily"
                ])
                
                if not (is_rate_limit or is_transient):
                    logger.error("💀 Non-retryable error. Aborting.")
                    raise
                
                if attempt < MAX_RETRIES:
                    wait_time = RETRY_INTERVALS[attempt]
                    logger.warning(f"⏳ Waiting {wait_time}s before retry {attempt + 1}/{MAX_RETRIES}...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"💀 Max retries ({MAX_RETRIES}) exceeded.")
                    raise
        
        raise last_exception
    
    def analyze_gif_b1(self, gif_url: str) -> Optional[str]:
        """
        Analyze a GIF for Task B1 (GIF caption generation).
        
        Args:
            gif_url: URL of the GIF to analyze
            
        Returns:
            Detailed description of the GIF, or None if analysis fails
        """
        logger.info(f"🎬 Analyzing GIF for B1: {gif_url[:60]}...")
        
        # Download the GIF
        gif_bytes = self._download_gif(gif_url)
        if not gif_bytes:
            return None
        
        # Upload to Gemini
        file = self._upload_gif_to_gemini(gif_bytes)
        if not file:
            return None
        
        try:
            # Analyze with B1 prompt
            description = self._call_with_retry(file, PROMPT_B1_GIF_ANALYSIS)
            
            if description:
                logger.info(f"✅ GIF analysis complete ({len(description)} chars)")
                logger.debug(f"Description preview: {description[:200]}...")
            
            return description
            
        finally:
            # Clean up uploaded file
            try:
                genai.delete_file(file.name)
            except:
                pass
    
    def analyze_gif_b2(self, gif_url: str, prompt: str) -> Optional[str]:
        """
        Analyze a GIF for Task B2 (GIF + prompt caption generation).
        
        Args:
            gif_url: URL of the GIF to analyze
            prompt: The fill-in-the-blank prompt that the GIF will complete
            
        Returns:
            Detailed description of the GIF contextualized to the prompt,
            or None if analysis fails
        """
        logger.info(f"🎬 Analyzing GIF for B2: {gif_url[:60]}...")
        logger.info(f"📝 Prompt: {prompt}")
        
        # Download the GIF
        gif_bytes = self._download_gif(gif_url)
        if not gif_bytes:
            return None
        
        # Upload to Gemini
        file = self._upload_gif_to_gemini(gif_bytes)
        if not file:
            return None
        
        try:
            # Format B2 prompt with the fill-in-the-blank prompt
            analysis_prompt = PROMPT_B2_GIF_ANALYSIS.format(prompt=prompt)
            
            # Analyze with B2 prompt
            description = self._call_with_retry(file, analysis_prompt)
            
            if description:
                logger.info(f"✅ GIF analysis complete ({len(description)} chars)")
                logger.debug(f"Description preview: {description[:200]}...")
            
            return description
            
        finally:
            # Clean up uploaded file
            try:
                genai.delete_file(file.name)
            except:
                pass
    
    def get_stats(self) -> dict:
        """Get usage statistics."""
        return {
            "calls_made": self.calls_made,
            "last_call_time": self.last_call_time,
        }


# =========================================================================
# MODULE-LEVEL FUNCTIONS (for easy import)
# =========================================================================

# Singleton instance with thread-safe initialization
_analyzer_instance: Optional[GIFAnalyzer] = None
_analyzer_lock = threading.Lock()


def get_gif_analyzer() -> GIFAnalyzer:
    """Get or create the singleton GIF analyzer instance (thread-safe)."""
    global _analyzer_instance
    # Double-checked locking pattern for thread safety
    if _analyzer_instance is None:
        with _analyzer_lock:
            if _analyzer_instance is None:
                _analyzer_instance = GIFAnalyzer()
    return _analyzer_instance


def analyze_gif_for_b1(gif_url: str) -> Optional[str]:
    """
    Convenience function to analyze a GIF for Task B1.
    
    Args:
        gif_url: URL of the GIF
        
    Returns:
        Detailed description, or None if analysis fails
    """
    return get_gif_analyzer().analyze_gif_b1(gif_url)


def analyze_gif_for_b2(gif_url: str, prompt: str) -> Optional[str]:
    """
    Convenience function to analyze a GIF for Task B2.
    
    Args:
        gif_url: URL of the GIF
        prompt: The fill-in-the-blank prompt
        
    Returns:
        Detailed description contextualized to the prompt, or None if analysis fails
    """
    return get_gif_analyzer().analyze_gif_b2(gif_url, prompt)
