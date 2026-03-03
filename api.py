"""
API Module for the MWAHAHA Humor Generation Pipeline.

This module provides a unified interface for multiple LLM providers:
- Google Gemini API (current)
- OpenRouter API (future-ready)

Features:
- Automatic retry with configurable intervals for rate limit handling
- Token usage tracking
- Easy provider switching via config
- Caching DISABLED to ensure distinct outputs for variation strategy
"""

import time
import logging
import dspy
import litellm
import threading
from typing import Optional, Callable, Any
from functools import wraps

from config import (
    GEMINI_API_KEY,
    OPENROUTER_API_KEY,
    API_PROVIDER,
    MODELS,
    RETRY_INTERVALS,
    MAX_RETRIES,
    DEFAULT_LLM_PARAMS,
    DEFAULT_MODEL,
    get_module_config,
    parse_model_spec,
    get_active_providers,
)

# Disable LiteLLM caching globally
litellm.cache = None

# Get logger
logger = logging.getLogger("mwahaha")


def is_gemma_model(model_name: str) -> bool:
    """
    Check if a model is a Gemma model.
    
    Gemma models don't support JSON mode, so we need to avoid using it.
    This applies regardless of provider (Gemini or OpenRouter).
    
    Args:
        model_name: The model identifier (e.g., "gemma-3-27b-it", "google/gemma-2-9b-it:free")
    
    Returns:
        True if the model is a Gemma model
    """
    return "gemma" in model_name.lower()


class TokenTracker:
    """
    Tracks token usage across API calls for cost analysis.
    
    Thread-safe: Uses a lock for all mutations to support parallel execution.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_api_calls = 0  # Track total number of API calls
        self.calls = []
    
    def add_usage(self, input_tokens: int, output_tokens: int, module_name: str = ""):
        """Record token usage from an API call (thread-safe)."""
        with self._lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.calls.append({
                "module": module_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "timestamp": time.time(),
            })
    
    def increment_call_count(self):
        """Increment API call counter (thread-safe)."""
        with self._lock:
            self.total_api_calls += 1
    
    def get_summary(self) -> dict:
        """Get summary of token usage (thread-safe)."""
        with self._lock:
            return {
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_tokens": self.total_input_tokens + self.total_output_tokens,
                "total_api_calls": self.total_api_calls,
                "num_calls": len(self.calls),
            }
    
    def reset(self):
        """Reset the tracker (thread-safe)."""
        with self._lock:
            self.total_input_tokens = 0
            self.total_output_tokens = 0
            self.total_api_calls = 0
            self.calls = []


# Global token tracker instance
token_tracker = TokenTracker()


class RetryTracker:
    """
    Tracks retry attempts per module for debugging and optimization.
    
    Thread-safe: Uses a lock for all mutations to support parallel execution.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self.retries_by_module = {}  # module_name -> {"rate_limit": count, "transient": count}
        self.total_retries = 0
    
    def record_retry(self, module_name: str, error_type: str):
        """
        Record a retry attempt for a module (thread-safe).
        
        Args:
            module_name: Name of the module that triggered the retry
            error_type: Type of error ("rate_limit", "transient", or "json_parse")
        """
        with self._lock:
            if module_name not in self.retries_by_module:
                self.retries_by_module[module_name] = {"rate_limit": 0, "transient": 0, "json_parse": 0}
            self.retries_by_module[module_name][error_type] += 1
            self.total_retries += 1
    
    def get_summary(self) -> dict:
        """Get summary of retries per module (thread-safe)."""
        with self._lock:
            return {
                "total_retries": self.total_retries,
                "by_module": dict(self.retries_by_module),
            }
    
    def get_formatted_summary(self) -> str:
        """Get a formatted string summary for logging."""
        with self._lock:
            if self.total_retries == 0:
                return "No retries needed"
            
            lines = [f"Total Retries: {self.total_retries}"]
            for module, counts in sorted(self.retries_by_module.items()):
                total = counts["rate_limit"] + counts["transient"] + counts.get("json_parse", 0)
                details = []
                if counts["rate_limit"] > 0:
                    details.append(f"{counts['rate_limit']} rate limit")
                if counts["transient"] > 0:
                    details.append(f"{counts['transient']} transient")
                if counts.get("json_parse", 0) > 0:
                    details.append(f"{counts['json_parse']} json parse")
                lines.append(f"  {module}: {total} ({', '.join(details)})")
            return "\n".join(lines)
    
    def reset(self):
        """Reset the tracker (thread-safe)."""
        with self._lock:
            self.retries_by_module = {}
            self.total_retries = 0


# Global retry tracker instance
retry_tracker = RetryTracker()


def with_retry(func: Callable) -> Callable:
    """
    Decorator that adds retry logic with configurable intervals.
    
    Retry intervals: 5s, 5s, 10s, 20s, 30s, 30s, 30s, 2min, 2min, 2min
    
    Tracks retries per module via the caller_id kwarg for debugging.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        last_exception = None
        # Extract caller_id for retry tracking (module name)
        caller_id = kwargs.get("caller_id", "unknown")
        # Extract base module name (strip branch info like "[1,2]")
        module_name = caller_id.split("[")[0].strip() if caller_id else "unknown"
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                error_type = type(e).__name__
                
                # Log the error details
                logger.error(f"❌ API Error [{error_type}]: {str(e)[:500]}")
                
                # Check if it's a rate limit or quota error
                is_rate_limit = any(term in error_str for term in [
                    "rate limit", "quota", "429", "resource exhausted",
                    "too many requests", "overloaded", "capacity"
                ])
                
                # Check if it's a transient error worth retrying
                is_transient = any(term in error_str for term in [
                    "timeout", "connection", "503", "502", "500",
                    "temporarily", "unavailable", "retry"
                ])
                
                # Check if it's a JSON mode/parse error (DSPy race condition)
                # This happens when DSPy incorrectly falls back to JSON mode
                # for models like gemma-3-27b-it that don't support it
                is_json_error = any(term in error_str for term in [
                    "json_repair", "could not parse", "json mode",
                    "badrequest", "bad request", "response_mime_type"
                ])
                
                if is_json_error:
                    # Check if we're using a Gemma model
                    current_lm = dspy.settings.lm
                    if current_lm and hasattr(current_lm, 'model'):
                        model_str = str(current_lm.model)
                        if is_gemma_model(model_str):
                            # For Gemma models, ensure ChatAdapter is used (no JSON mode fallback)
                            logger.warning(f"🔧 JSON mode error for Gemma model. Re-enforcing ChatAdapter (Gemma doesn't support JSON mode)...")
                            try:
                                dspy.configure(adapter=dspy.ChatAdapter())
                            except Exception as adapter_error:
                                logger.debug(f"Note: Could not reconfigure adapter (thread-safety): {adapter_error}")
                                logger.debug("ChatAdapter should already be configured from startup")
                        else:
                            logger.warning(f"🔧 JSON mode error detected. Will retry with existing adapter config...")
                    else:
                        logger.warning(f"🔧 JSON mode error detected. Will retry with existing adapter config...")
                
                if not (is_rate_limit or is_transient or is_json_error):
                    # Not a retryable error, raise immediately
                    logger.error(f"💀 Non-retryable error. Aborting.")
                    raise
                
                # Track the retry
                if is_rate_limit:
                    retry_type = "rate_limit"
                elif is_json_error:
                    retry_type = "json_parse"
                else:
                    retry_type = "transient"
                retry_tracker.record_retry(module_name, retry_type)
                
                if attempt < MAX_RETRIES:
                    wait_time = RETRY_INTERVALS[attempt]
                    error_reason = "Rate limit" if is_rate_limit else "Transient error"
                    logger.warning(f"⏳ {error_reason} hit. Waiting {wait_time}s before retry {attempt + 1}/{MAX_RETRIES}...")
                    time.sleep(wait_time)
                    logger.info(f"🔄 Retrying now (attempt {attempt + 2}/{MAX_RETRIES + 1})...")
                else:
                    logger.error(f"💀 Max retries ({MAX_RETRIES}) exceeded. Giving up.")
                    raise
        
        raise last_exception
    
    return wrapper


class APIProvider:
    """
    Base class for API providers.
    Defines the interface that all providers must implement.
    """
    
    def __init__(self):
        self.lm = None
    
    def configure(self, **kwargs) -> dspy.LM:
        """Configure and return the DSPy LM instance."""
        raise NotImplementedError
    
    def get_token_usage(self) -> tuple[int, int]:
        """Get (input_tokens, output_tokens) from last call."""
        raise NotImplementedError


class GeminiProvider(APIProvider):
    """Google Gemini API provider."""
    
    # Parameters not supported by Gemini models
    UNSUPPORTED_PARAMS = {'presence_penalty', 'frequency_penalty'}
    
    def __init__(self):
        super().__init__()
        self.api_key = GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    def configure(self, model: Optional[str] = None, **kwargs) -> dspy.LM:
        """
        Configure Gemini LM for DSPy.
        
        Args:
            model: Model name (defaults to config setting)
            **kwargs: Additional LLM parameters
        
        Returns:
            Configured DSPy LM instance
        """
        model_name = model or MODELS["gemini"]
        
        # Merge default params with provided kwargs
        params = DEFAULT_LLM_PARAMS.copy()
        params.update(kwargs)
        
        # Filter out unsupported parameters for Gemini
        unsupported_found = []
        for param in self.UNSUPPORTED_PARAMS:
            if param in params:
                unsupported_found.append(f"{param}={params.pop(param)}")
        
        if unsupported_found:
            logger.debug(f"Gemini: Filtered unsupported params: {', '.join(unsupported_found)}")
        
        # Create the LM instance with caching DISABLED
        # We want fresh responses for each variation to ensure diversity
        self.lm = dspy.LM(
            model=f"gemini/{model_name}",
            api_key=self.api_key,
            cache=False,  # Disable caching to ensure distinct outputs
            **params
        )
        
        # Configure DSPy adapter based on model capabilities
        # Gemma models don't support JSON mode, so use ChatAdapter only
        if is_gemma_model(model_name):
            dspy.configure(adapter=dspy.ChatAdapter())
            logger.debug(f"Gemma model detected ({model_name}): Using ChatAdapter (no JSON mode)")
        
        return self.lm
    
    def get_token_usage(self) -> tuple[int, int]:
        """Extract token usage from Gemini response."""
        # DSPy stores history in lm.history
        if self.lm and hasattr(self.lm, 'history') and self.lm.history:
            last_call = self.lm.history[-1]
            # Token usage depends on DSPy version and provider
            input_tokens = last_call.get('usage', {}).get('prompt_tokens', 0)
            output_tokens = last_call.get('usage', {}).get('completion_tokens', 0)
            return input_tokens, output_tokens
        return 0, 0


class OpenRouterProvider(APIProvider):
    """
    OpenRouter API provider (future-ready).
    
    OpenRouter provides access to multiple models through a unified API.
    """
    
    def __init__(self):
        super().__init__()
        self.api_key = OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    def configure(self, model: Optional[str] = None, **kwargs) -> dspy.LM:
        """
        Configure OpenRouter LM for DSPy.
        
        Args:
            model: Model name (defaults to config setting)
            **kwargs: Additional LLM parameters
        
        Returns:
            Configured DSPy LM instance
        """
        from config import DEFAULT_QUANTIZATION
        
        model_name = model or MODELS["openrouter"]
        
        # Merge default params with provided kwargs
        params = DEFAULT_LLM_PARAMS.copy()
        params.update(kwargs)
        
        # Build provider preferences for OpenRouter
        provider_params = {}
        
        # Add default quantization if specified (can be overridden by params)
        if DEFAULT_QUANTIZATION:
            provider_params["quantizations"] = DEFAULT_QUANTIZATION
        
        # Merge with extra_body if provided (module-specific overrides)
        extra_body = params.pop("extra_body", {})
        
        # Merge provider params - module-specific settings override defaults
        if "provider" in extra_body:
            # Module has custom provider settings - merge with defaults
            module_provider = extra_body["provider"]
            # Module settings take precedence over defaults
            merged_provider = provider_params.copy()
            merged_provider.update(module_provider)
            extra_body["provider"] = merged_provider
        elif provider_params:
            # No module override - use defaults
            extra_body["provider"] = provider_params
        
        # OpenRouter uses OpenAI-compatible API
        self.lm = dspy.LM(
            model=f"openrouter/{model_name}",
            api_key=self.api_key,
            api_base="https://openrouter.ai/api/v1",
            cache=False,  # Disable caching to ensure distinct outputs
            extra_headers={
                "HTTP-Referer": "https://github.com/mwahaha-pipeline",  # Required by OpenRouter
                "X-Title": "MWAHAHA Humor Pipeline",  # Optional app name
            },
            extra_body=extra_body if extra_body else None,
            **params
        )
        
        # Configure DSPy adapter based on model capabilities
        # Gemma models don't support JSON mode regardless of provider
        if is_gemma_model(model_name):
            dspy.configure(adapter=dspy.ChatAdapter())
            logger.debug(f"Gemma model detected ({model_name}): Using ChatAdapter (no JSON mode)")
        
        return self.lm
    
    def get_token_usage(self) -> tuple[int, int]:
        """Extract token usage from OpenRouter response."""
        if self.lm and hasattr(self.lm, 'history') and self.lm.history:
            last_call = self.lm.history[-1]
            input_tokens = last_call.get('usage', {}).get('prompt_tokens', 0)
            output_tokens = last_call.get('usage', {}).get('completion_tokens', 0)
            return input_tokens, output_tokens
        return 0, 0


# Provider registry
PROVIDERS = {
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
}


def is_openrouter_model_free(model_name: str = None) -> bool:
    """
    Check if the OpenRouter model is a free tier model.
    
    Free models on OpenRouter end with ':free' suffix.
    
    Args:
        model_name: Model name to check. If None, uses DEFAULT_MODEL.
    
    Returns:
        True if model is free tier, False otherwise.
    """
    if model_name is None:
        _, model_name = parse_model_spec(DEFAULT_MODEL)
    if model_name is None:
        model_name = MODELS.get("openrouter", "")
    return model_name.endswith(":free")


def get_openrouter_model_name() -> str:
    """Get the currently configured OpenRouter model name."""
    _, model = parse_model_spec(DEFAULT_MODEL)
    if model:
        return model
    return MODELS.get("openrouter", "")


def get_provider(provider_name: Optional[str] = None) -> APIProvider:
    """
    Get an API provider instance.
    
    Args:
        provider_name: Name of provider ("gemini" or "openrouter")
                      Defaults to API_PROVIDER from config
    
    Returns:
        Configured APIProvider instance
    """
    name = provider_name or API_PROVIDER
    
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS.keys())}")
    
    return PROVIDERS[name]()


def configure_dspy(provider_name: Optional[str] = None, **kwargs) -> dspy.LM:
    """
    Configure DSPy with the specified provider.
    
    This is the main entry point for setting up the LLM.
    Prints which providers are being used by which modules.
    
    Args:
        provider_name: Name of provider (defaults to config)
        **kwargs: Additional LLM parameters
    
    Returns:
        Configured DSPy LM instance
    
    Example:
        >>> lm = configure_dspy()  # Uses default provider from config
        >>> lm = configure_dspy("openrouter", temperature=0.8)
    """
    # Parse default model to determine provider
    default_provider, default_model = parse_model_spec(DEFAULT_MODEL)
    actual_provider = provider_name or default_provider or API_PROVIDER
    
    provider = get_provider(actual_provider)
    lm = provider.configure(model=default_model, **kwargs)
    dspy.configure(lm=lm)
    
    # Log which providers are being used
    _log_active_providers()
    
    return lm


def _log_active_providers():
    """Log a summary of which providers are being used by which modules."""
    providers_used = get_active_providers()
    
    logger.info("\n" + "=" * 60)
    logger.info("🔧 MODEL CONFIGURATION")
    logger.info("=" * 60)
    logger.info(f"Default Model: {DEFAULT_MODEL}")
    logger.info("")
    
    for provider, modules in sorted(providers_used.items()):
        logger.info(f"📡 Provider: {provider.upper()}")
        for module, model in modules:
            logger.info(f"   • {module}: {model}")
        logger.info("")
    
    # Warn if multiple providers
    if len(providers_used) > 1:
        logger.info(f"⚠️  Multiple providers active: {', '.join(providers_used.keys())}")
        logger.info("   (Ensure all API keys are configured)")
    
    logger.info("=" * 60 + "\n")


def get_module_lm(module_name: str) -> Optional[dspy.LM]:
    """
    Get an LM instance configured for a specific module.
    
    If the module has custom configuration (model or params), creates a new LM.
    Supports mixed providers - a module can use a different provider than default.
    
    Args:
        module_name: Name of the module (e.g., "HumorArchitect")
    
    Returns:
        Configured LM instance, or None if using global defaults
    """
    config = get_module_config(module_name)
    
    # If no custom config, return None (use global)
    if config["model"] is None and config["params"] == DEFAULT_LLM_PARAMS:
        return None
    
    # Parse model spec to get provider and model
    module_model_spec = config["model"]
    params = config["params"]
    
    if module_model_spec:
        # Module has explicit model - parse it
        provider_name, model_name = parse_model_spec(module_model_spec)
        
        if provider_name is None:
            # No provider specified - use default provider
            default_provider, _ = parse_model_spec(DEFAULT_MODEL)
            provider_name = default_provider or API_PROVIDER
    else:
        # No module model - use default model's provider
        default_provider, model_name = parse_model_spec(DEFAULT_MODEL)
        provider_name = default_provider or API_PROVIDER
        logger.debug(f"Module {module_name}: Using DEFAULT_MODEL provider={provider_name}, model={model_name}")
        # model_name stays as default
    
    # Get provider and create LM
    provider = get_provider(provider_name)
    return provider.configure(model=model_name, **params)


@with_retry
def call_with_retry(predictor: dspy.Module, caller_id: str = "", **kwargs) -> Any:
    """
    Call a DSPy predictor with automatic retry on rate limits.
    
    The @with_retry decorator handles 429 errors using RETRY_INTERVALS.
    Ensures ChatAdapter is used for Gemma models (no JSON mode support).
    
    Args:
        predictor: DSPy predictor/module to call
        caller_id: Identifier for logging (unused, kept for compatibility)
        **kwargs: Arguments to pass to the predictor
    
    Returns:
        Predictor output
    """
    # Safety check: Ensure ChatAdapter for Gemma models
    # Gemma models don't support JSON mode, so we must enforce ChatAdapter
    current_lm = getattr(predictor, 'lm', None) or dspy.settings.lm
    if current_lm and hasattr(current_lm, 'model'):
        model_str = str(current_lm.model)
        if is_gemma_model(model_str):
            # Ensure ChatAdapter is configured (thread-safe check)
            current_adapter = getattr(dspy.settings, 'adapter', None)
            if not isinstance(current_adapter, dspy.ChatAdapter):
                try:
                    dspy.configure(adapter=dspy.ChatAdapter())
                    logger.debug(f"Enforced ChatAdapter for Gemma model: {model_str}")
                except Exception as e:
                    # Thread-safety restriction - adapter should already be set from startup
                    logger.debug(f"Note: ChatAdapter enforcement skipped (thread-safety): {e}")
    
    # Count this API call (thread-safe)
    # This ensures we count ALL calls, including parallel branches
    # where token tracking may not happen due to DSPy thread restrictions
    token_tracker.increment_call_count()
    
    return predictor(**kwargs)


def track_tokens(lm: dspy.LM, module_name: str = "") -> None:
    """
    Track token usage from the last LLM call.
    
    Args:
        lm: DSPy LM instance
        module_name: Name of the module that made the call
    """
    if hasattr(lm, 'history') and lm.history:
        last_call = lm.history[-1]
        
        # Use shared utility for token extraction
        from utils import extract_token_usage
        input_tokens, output_tokens = extract_token_usage(last_call)
        
        token_tracker.add_usage(input_tokens, output_tokens, module_name)
        logger.debug(f"Token tracking [{module_name}]: {input_tokens} in / {output_tokens} out")


def get_token_summary() -> dict:
    """Get summary of all token usage."""
    return token_tracker.get_summary()


def reset_token_tracker():
    """Reset the token tracker."""
    token_tracker.reset()


def get_retry_summary() -> dict:
    """Get summary of retries per module."""
    return retry_tracker.get_summary()


def get_retry_formatted_summary() -> str:
    """Get a formatted string summary of retries for logging."""
    return retry_tracker.get_formatted_summary()


def reset_retry_tracker():
    """Reset the retry tracker."""
    retry_tracker.reset()


def reset_all_trackers():
    """Reset both token and retry trackers."""
    token_tracker.reset()
    retry_tracker.reset()
