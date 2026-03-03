"""
Configuration file for the MWAHAHA Humor Generation Pipeline.

This file centralizes all configurable parameters including:
- API settings and retry logic
- LLM parameters for each module
- Mode settings (test/full)
- File paths and limits
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =========================================================================
# PATHS
# =========================================================================

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "Input"
OUTPUT_DIR = BASE_DIR / "outputs"
TEST_OUTPUT_DIR = BASE_DIR / "test_outputs"
COMPLETE_OUTPUT_DIR = BASE_DIR / "complete"  # Untruncated output with full LLM data
JUDGED_OUTPUT_DIR = BASE_DIR / "judged_outputs"  # Final judged outputs for submission

# =========================================================================
# API CONFIGURATION
# =========================================================================

# API Keys (loaded from .env)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Current provider: "gemini" or "openrouter" (fallback if not specified in model)
API_PROVIDER = os.getenv("API_PROVIDER", "openrouter")

# Model names per provider (legacy - prefer using DEFAULT_MODEL instead)
MODELS = {
    "gemini": "gemma-3-27b-it",  # Gemma 3 27B via Gemini API
    "openrouter": "deepseek/deepseek-v3.2",  # DeepSeek v3.2
}

# =========================================================================
# RETRY CONFIGURATION
# =========================================================================

# Retry intervals in seconds for rate limit handling
# Pattern: 5s, 5s, 10s, 20s, 30s, 30s, 30s, 2min, 2min, 2min
# This handles 429 rate limit errors automatically with exponential backoff
RETRY_INTERVALS = [5, 10, 20, 30, 60, 120, 120, 120]
MAX_RETRIES = len(RETRY_INTERVALS)

# =========================================================================
# MODE SETTINGS
# =========================================================================

# Test mode limits (per file)
TEST_LIMITS = {
    "task_a": 2,      # 10 total: 5 headlines + 5 word inclusion (if both exist)
    "task_b1": 1,
    "task_b2": 1,
}

# Full mode processes all samples
FULL_MODE = False  # Default to test mode

# Complete output mode - saves all candidates and full LLM outputs as JSON
SAVE_COMPLETE_OUTPUT = False  # Enable to save complete output with all candidates

# =========================================================================
# PARALLEL PROCESSING
# =========================================================================

# Number of jokes to process in parallel
# Higher values = faster but more API load, risk of rate limits
# Set to 1 for sequential processing (safer for rate-limited APIs)
PARALLEL_JOKES = 1  # Default: sequential processing

# Maximum parallel jokes allowed (safety limit)
MAX_PARALLEL_JOKES = 8

# =========================================================================
# LLM PARAMETERS (Per Module)
# =========================================================================

# Default model (format: "provider/model" or just "model" for current provider)
# Examples:
#   "openrouter/deepseek/deepseek-v3.2" - DeepSeek v3.2 via OpenRouter
#   "openrouter/google/gemma-3-27b-it" - Gemma 3 27B via OpenRouter
#   "gemini/gemma-3-27b-it" - Gemma 3 27B via Google Gemini
#   "deepseek/deepseek-v3.2" - Uses current API_PROVIDER
DEFAULT_MODEL = "google/gemma-3-27b-it"  # Gemma 3 27B IT via OpenRouter

# Default quantization for OpenRouter models
# Options: int4, int8, fp4, fp6, fp8, fp16, bf16, fp32, unknown
# Set to None to use any quantization (default OpenRouter behavior)
DEFAULT_QUANTIZATION = ["bf16"]  # Brain float 16-bit for Gemma

# Default parameters applied to all modules (used when no module-specific config)
# Per-module configurations are applied via MODULE_CONFIG below.
DEFAULT_LLM_PARAMS = {
    # "temperature": 0.8,
    # "top_p": 0.95,
    # "max_tokens": 2048,
    # "extra_body": {"enable_reasoning": False},  # Disable DeepSeek reasoning mode
}

# Per-module configuration: model and/or parameters
# 
# Model Override Formats:
#   "provider/model"  - Use specific provider (e.g., "gemini/gemma-3-27b-it")
#   "model"           - Use DEFAULT model's provider (e.g., "deepseek/deepseek-v3.2")
#   None              - Use DEFAULT_MODEL
#
# If 'model' is specified, it overrides the default model for that module
# If 'params' is specified, those params are merged with DEFAULT_LLM_PARAMS
# If neither is specified, the module uses global defaults
#
# This allows mixing providers! For example:
#   - Use Gemini for ContextEnricher (analytical)
#   - Use DeepSeek for ContentWriter (creative)
#
# Module Functions:
# - ContextEnricher: Analytical - extracts facts, subtext, targets (needs accuracy)
# - HumorArchitect: Creative design - creates GTVH humor blueprint (needs creativity)
# - DeliveryStrategist: Strategic - chooses format/style (balanced)
# - ContentWriter: Creative writing - writes final joke (needs max creativity)
# - HumorJudge: Evaluative - compares/judges jokes (needs consistency)
#
MODULE_CONFIG = {
    # ContextEnricher: Analytical task - extract facts and context accurately
    # Lower temperature for consistent, thorough analysis
    # No penalties - we want comprehensive, possibly repetitive pattern recognition
    "ContextEnricher": {
        "params": {
            # "temperature": 0.5,        # More focused for accurate extraction
            # "top_p": 0.9,              # Slightly narrower for reliability
            # "max_tokens": 1024,        # Context analysis doesn't need huge output
        },
    },
    
    # HumorArchitect: Creative design - find unexpected humor structures
    # Higher temperature + presence penalty to explore diverse humor angles
    "HumorArchitect": {
        "params": {
            # "temperature": 1,        # Maximum creativity for finding humor angles
            # "top_p": 0.95,             # Allow exploration of unlikely options
            # "max_tokens": 1536,        # Needs room for GTVH analysis
            # "presence_penalty": 0.3,   # Encourage exploring new concepts
            # "frequency_penalty": 0.2,  # Reduce repetitive phrasing
        },
    },
    
    # DeliveryStrategist: Strategic planning - balance creativity and coherence
    # Medium temperature, light penalties to avoid formulaic choices
    "DeliveryStrategist": {
        "params": {
            # "temperature": 0.9,        # Balanced - creative but coherent
            # "top_p": 0.9,              # Focused exploration
            # "max_tokens": 1024,        # Strategy doesn't need huge output
            # "frequency_penalty": 0.1,  # Light penalty to avoid repetitive formats
        },
    },
    
    # ContentWriter: Creative writing - write the actual joke
    # Uses DeepSeek v3.2 for maximum creativity and natural language generation
    # Highest creativity settings to avoid templated, predictable jokes
    "ContentWriter": {
        "params": {
            # "temperature": 0.9,        # Maximum creativity for joke writing
            # "top_p": 0.95,             # Allow unexpected word choices
            # "max_tokens": 1536,        # Room for draft + final joke
            # "presence_penalty": 0.1,   # Strong push for fresh vocabulary
            # "frequency_penalty": 0.1,  # Avoid repetitive phrases (kills comedy)
        },
    },
    
    # HumorJudge: Evaluative task - consistent, reliable judgment
    # Lowest temperature, no penalties - consistency is key
    "HumorJudge": {
        "params": {
            # "temperature": 0.5,        # Low for consistent judgment
            # "top_p": 0.85,             # Narrow for reliable decisions
            # "max_tokens": 1024,        # Critique + decision
            # # No penalties - we want consistent, reproducible evaluations
        },
    },
}

# Legacy: MODULE_LLM_PARAMS (deprecated, use MODULE_CONFIG instead)
# Kept for backward compatibility
MODULE_LLM_PARAMS = {
    # Deprecated - use MODULE_CONFIG
}

def get_module_config(module_name: str) -> dict:
    """
    Get configuration for a specific module.
    
    Returns:
        dict with keys:
            - 'model': Full model spec (e.g., "openrouter/deepseek/deepseek-v3.2")
                       None means use DEFAULT_MODEL
            - 'params': LLM parameters (merged with defaults)
    """
    config = MODULE_CONFIG.get(module_name, {})
    
    # Build params by merging defaults with module-specific
    params = DEFAULT_LLM_PARAMS.copy()
    if module_name in MODULE_LLM_PARAMS:  # Legacy support
        params.update(MODULE_LLM_PARAMS[module_name])
    if "params" in config:
        params.update(config["params"])
    
    return {
        "model": config.get("model"),  # None means use DEFAULT_MODEL
        "params": params,
    }


def parse_model_spec(model_spec: str) -> tuple[str, str]:
    """
    Parse a model specification into (provider, model_name).
    
    Formats:
        "provider/model" -> (provider, model)  
        Examples:
          - "openrouter/deepseek/deepseek-v3.2" -> ("openrouter", "deepseek/deepseek-v3.2")
          - "openrouter/gemma-3-27b-it/chutes/bf16" -> ("openrouter", "gemma-3-27b-it/chutes/bf16")
          - "gemini/gemma-3-27b-it" -> ("gemini", "gemma-3-27b-it")
        "model" -> (None, model)  e.g., "deepseek/deepseek-v3.2" (use default provider)
    
    Returns:
        (provider, model_name) tuple. provider may be None.
    """
    if not model_spec:
        return None, None
    
    # Check if it starts with a known provider prefix
    # Known providers must be at the start, followed by a slash
    known_providers = ["gemini", "openrouter"]
    
    for provider in known_providers:
        prefix = f"{provider}/"
        if model_spec.startswith(prefix):
            # Everything after "provider/" is the model name
            # This handles complex paths like "openrouter/gemma-3-27b-it/chutes/bf16"
            model_name = model_spec[len(prefix):]
            return provider, model_name
    
    # No provider prefix - return model as-is (will use default provider)
    return None, model_spec


def get_active_providers() -> dict:
    """
    Get a summary of which providers are being used by which modules.
    
    Returns:
        dict mapping provider -> list of modules using it
    """
    # Parse default model
    default_provider, default_model = parse_model_spec(DEFAULT_MODEL)
    if default_provider is None:
        default_provider = API_PROVIDER
    
    providers_used = {}
    
    # Check each module
    all_modules = ["ContextEnricher", "HumorArchitect", "DeliveryStrategist", "ContentWriter", "HumorJudge"]
    
    for module in all_modules:
        config = MODULE_CONFIG.get(module, {})
        module_model = config.get("model")
        
        if module_model:
            provider, model = parse_model_spec(module_model)
            if provider is None:
                provider = default_provider
            effective_model = module_model
        else:
            provider = default_provider
            effective_model = default_model or MODELS.get(default_provider, "unknown")
        
        if provider not in providers_used:
            providers_used[provider] = []
        providers_used[provider].append((module, effective_model))
    
    return providers_used

def get_module_params(module_name: str) -> dict:
    """Get LLM parameters for a specific module, merging defaults with overrides."""
    return get_module_config(module_name)["params"]

# =========================================================================
# TASK CONSTRAINTS
# =========================================================================

# Maximum character lengths
MAX_CHARS = {
    "en": 900,
    "es": 900,
    "zh": 300,
    "b1": 900,  # 20 words ~ approx chars
    "b2": 900,
}

# Maximum word count for Task B
MAX_WORDS_TASK_B = 20

# =========================================================================
# LOGGING CONFIGURATION
# =========================================================================

LOG_DIR = BASE_DIR / "logs"

# Log levels: DEBUG (verbose), INFO (standard), WARNING (minimal), PROMPT_TUNING (outputs only)
# PROMPT_TUNING is a special mode that only shows module outputs for tuning prompts
LOG_LEVEL = "INFO"  # DEBUG for verbose, INFO for standard, WARNING for minimal

LOG_TOKEN_USAGE = True  # Track token usage for cost analysis

# Prompt Tuning Mode: When True, logs are focused on module outputs only
# This creates clean, organized output for analyzing prompt effectiveness
PROMPT_TUNING_MODE = True  # Set to True for clean prompt-only output

# =========================================================================
# GENERATION SETTINGS
# =========================================================================

# Number of variations per pipeline stage
# HumorArchitect generates NUM_ARCHITECT_VARIATIONS different humor strategies
# Each strategy is then processed by NUM_STRATEGY_VARIATIONS different delivery approaches
# Total candidates = NUM_ARCHITECT_VARIATIONS * NUM_STRATEGY_VARIATIONS
NUM_ARCHITECT_VARIATIONS = 4  # Number of humor concepts from HumorArchitect
NUM_STRATEGY_VARIATIONS = 1   # Number of delivery strategies per concept

# Total number of candidate jokes to generate before judging
# (NUM_ARCHITECT_VARIATIONS * NUM_STRATEGY_VARIATIONS = 4 by default)
NUM_CANDIDATES = NUM_ARCHITECT_VARIATIONS * NUM_STRATEGY_VARIATIONS

# Enable/disable constraint checking
ENABLE_CONSTRAINT_CHECK = True

# =========================================================================
# GIF ANALYZER SETTINGS
# =========================================================================

# Timeout for GIF download requests (seconds)
GIF_DOWNLOAD_TIMEOUT = 15  # Reduced from 30s for faster batch processing

# Timeout for ffmpeg conversion (seconds)
GIF_CONVERSION_TIMEOUT = 60
