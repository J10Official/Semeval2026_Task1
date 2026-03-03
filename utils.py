"""
Shared Utilities Module for the MWAHAHA Humor Generation Pipeline.

Provides common utility functions used across multiple modules to avoid
code duplication and ensure consistent behavior.
"""

from typing import Any, Tuple
import logging

logger = logging.getLogger("mwahaha")


def extract_token_usage(last_call: dict) -> Tuple[int, int]:
    """
    Extract token usage from a DSPy LM history entry.
    
    Handles multiple possible formats from DSPy 3.0, LiteLLM, and Gemini.
    
    Args:
        last_call: The last entry from lm.history
    
    Returns:
        Tuple of (input_tokens, output_tokens)
    """
    if not last_call:
        return 0, 0
    
    usage = last_call.get('usage', {})
    
    # Try standard OpenAI/LiteLLM format first
    input_tokens = (
        usage.get('prompt_tokens') or 
        usage.get('input_tokens') or 
        usage.get('promptTokens') or 
        0
    )
    output_tokens = (
        usage.get('completion_tokens') or 
        usage.get('output_tokens') or 
        usage.get('completionTokens') or 
        usage.get('candidatesTokenCount') or
        0
    )
    
    # Check for Gemini-specific usageMetadata format
    if input_tokens == 0 and 'usageMetadata' in last_call:
        metadata = last_call['usageMetadata']
        input_tokens = metadata.get('promptTokenCount', 0)
        output_tokens = metadata.get('candidatesTokenCount', 0)
    
    # Check response object for usage metadata (Gemini/LiteLLM ModelResponse format)
    response = last_call.get('response')
    if response and input_tokens == 0:
        if hasattr(response, 'usage') and response.usage:
            resp_usage = response.usage
            if hasattr(resp_usage, 'prompt_tokens'):
                input_tokens = resp_usage.prompt_tokens or 0
                output_tokens = getattr(resp_usage, 'completion_tokens', 0) or 0
            elif isinstance(resp_usage, dict):
                input_tokens = resp_usage.get('prompt_tokens', 0)
                output_tokens = resp_usage.get('completion_tokens', 0)
    
    # Log debug info if still 0
    if input_tokens == 0 and output_tokens == 0:
        logger.debug(f"[Token Debug] usage keys: {list(usage.keys()) if usage else 'empty'}")
        logger.debug(f"[Token Debug] last_call keys: {list(last_call.keys())}")
        if response and hasattr(response, 'usage'):
            logger.debug(f"[Token Debug] response.usage: {response.usage}")
    
    return input_tokens, output_tokens
