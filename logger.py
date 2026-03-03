"""
Logging Module for the MWAHAHA Humor Generation Pipeline.

Provides detailed logging of:
- LLM inputs and outputs
- DSPy internals (prompts, completions)
- Token usage
- Pipeline progress

Logging Levels:
- DEBUG: Very verbose, includes DSPy traces and all internals
- INFO: Standard progress and results
- WARNING: Minimal, only errors and warnings

Special Mode:
- PROMPT_TUNING_MODE: Clean, organized output showing only module outputs
  for analyzing and tuning prompts without noise

Uses a structured, easy-to-read format for debugging and analysis.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List, Dict
import dspy

from config import LOG_DIR, LOG_LEVEL, LOG_TOKEN_USAGE, PROMPT_TUNING_MODE


# Create log directory
LOG_DIR.mkdir(exist_ok=True)

# Custom log level for prompt tuning output
PROMPT_OUTPUT = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(PROMPT_OUTPUT, "OUTPUT")


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'OUTPUT': '\033[96m',    # Bright Cyan (for prompt tuning output)
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m',
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


class PromptTuningFormatter(logging.Formatter):
    """Clean formatter for prompt tuning mode - no timestamps, minimal noise."""
    
    def format(self, record):
        return record.getMessage()


def setup_logger(name: str = "mwahaha", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.
    
    Args:
        name: Logger name
        log_file: Optional log file path
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Set level based on mode
    if PROMPT_TUNING_MODE:
        logger.setLevel(PROMPT_OUTPUT)
    else:
        logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if PROMPT_TUNING_MODE:
        # Clean output for prompt tuning
        console_handler.setLevel(PROMPT_OUTPUT)
        console_handler.setFormatter(PromptTuningFormatter())
    else:
        # Normal colored output
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        console_format = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
    
    logger.addHandler(console_handler)
    
    # File handler (if specified) - always full logging
    if log_file:
        file_path = LOG_DIR / log_file
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


# Global logger instance
logger = setup_logger()


def add_file_handler_to_logger(log_file: str):
    """
    Add a file handler to the global logger.
    
    Call this at the start of a run to enable file logging.
    
    Args:
        log_file: Log file name (will be created in LOG_DIR)
    """
    file_path = LOG_DIR / log_file
    file_handler = logging.FileHandler(file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    return file_path


# =========================================================================
# PROMPT TUNING MODE - Clean output for analyzing prompts
# =========================================================================

def pt_output(message: str):
    """Log output at PROMPT_OUTPUT level (visible in prompt tuning mode)."""
    logger.log(PROMPT_OUTPUT, message)


def pt_section(title: str, char: str = "═", width: int = 80):
    """Print a major section header for prompt tuning output."""
    if PROMPT_TUNING_MODE:
        line = char * width
        pt_output(f"\n{line}")
        pt_output(f"  {title}")
        pt_output(f"{line}")


def pt_subsection(title: str, char: str = "─", width: int = 70):
    """Print a subsection header for prompt tuning output."""
    if PROMPT_TUNING_MODE:
        line = char * width
        pt_output(f"\n{line}")
        pt_output(f"  {title}")
        pt_output(f"{line}")


def pt_field(name: str, value: Any, indent: int = 2):
    """Print a single field for prompt tuning output."""
    if PROMPT_TUNING_MODE:
        prefix = " " * indent
        str_value = str(value)
        if '\n' in str_value:
            pt_output(f"{prefix}{name}:")
            for line in str_value.split('\n'):
                pt_output(f"{prefix}  {line}")
        elif isinstance(value, list):
            pt_output(f"{prefix}{name}:")
            for item in value:
                pt_output(f"{prefix}  • {item}")
        else:
            pt_output(f"{prefix}{name}: {str_value}")


def pt_module_output(module_name: str, outputs: Dict[str, Any], branch_id: str = ""):
    """
    Log module outputs in prompt tuning mode.
    
    Clean, readable format showing exactly what each module produced.
    """
    if not PROMPT_TUNING_MODE:
        return
    
    header = f"📦 {module_name}"
    if branch_id:
        header += f" [Branch {branch_id}]"
    pt_subsection(header)
    
    for key, value in outputs.items():
        pt_field(key, value)


def pt_candidate_joke(branch_id: str, joke: str, architecture: dict, strategy: dict):
    """Log a complete candidate joke with its reasoning in prompt tuning mode."""
    if not PROMPT_TUNING_MODE:
        return
    
    pt_subsection(f"🎯 CANDIDATE [{branch_id}]")
    
    # Show the architecture reasoning
    pt_output("\n  HUMOR ARCHITECTURE:")
    pt_field("focal_targets", architecture.get("focal_targets", ""), 4)
    pt_field("cognitive_manipulation", architecture.get("cognitive_manipulation", ""), 4)
    pt_field("logical_mechanism", architecture.get("logical_mechanism", ""), 4)
    pt_field("script_opposition", architecture.get("script_opposition", ""), 4)
    
    # Show delivery strategy
    pt_output("\n  DELIVERY STRATEGY:")
    pt_field("narrative_strategy", strategy.get("narrative_strategy", ""), 4)
    pt_field("language_style", strategy.get("language_style", ""), 4)
    
    # Show the final joke prominently
    pt_output("\n  GENERATED JOKE:")
    pt_output(f"    ┌{'─' * 60}┐")
    # Word wrap the joke
    words = joke.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= 58:
            line += (" " if line else "") + word
        else:
            pt_output(f"    │ {line:<58} │")
            line = word
    if line:
        pt_output(f"    │ {line:<58} │")
    pt_output(f"    └{'─' * 60}┘")


def pt_judgment(winner_joke: str, critique: str):
    """Log the final judgment in prompt tuning mode."""
    if not PROMPT_TUNING_MODE:
        return
    
    pt_section("🏆 FINAL SELECTION")
    pt_output("\n  JUDGE'S CRITIQUE:")
    for line in critique.split('\n'):
        pt_output(f"    {line}")
    
    pt_output("\n  WINNING JOKE:")
    pt_output(f"    ┌{'─' * 60}┐")
    words = winner_joke.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= 58:
            line += (" " if line else "") + word
        else:
            pt_output(f"    │ {line:<58} │")
            line = word
    if line:
        pt_output(f"    │ {line:<58} │")
    pt_output(f"    └{'─' * 60}┘")


def pt_judge_comparison(joke1: str, joke2: str, match_name: str = ""):
    """
    Log which jokes are being compared in prompt tuning mode.
    
    Helps contextualize the judgment by showing what the judge is evaluating.
    """
    if not PROMPT_TUNING_MODE:
        return
    
    def format_joke_full(joke: str, max_len: int = 70) -> list[str]:
        """Format joke for display in a box, showing full content."""
        words = joke.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= max_len:
                current_line += (" " if current_line else "") + word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines
    
    title = f"⚖️ JUDGING: {match_name}" if match_name else "⚖️ JUDGING COMPARISON"
    pt_subsection(title)
    
    # Joke 1
    pt_output("\n  📝 JOKE 1:")
    pt_output(f"    ┌{'─' * 72}┐")
    for line in format_joke_full(joke1):
        pt_output(f"    │ {line:<70} │")
    pt_output(f"    └{'─' * 72}┘")
    
    # Joke 2
    pt_output("\n  📝 JOKE 2:")
    pt_output(f"    ┌{'─' * 72}┐")
    for line in format_joke_full(joke2):
        pt_output(f"    │ {line:<70} │")
    pt_output(f"    └{'─' * 72}┘")


def pt_judge_result(winner: str, critique: str = ""):
    """
    Log the judgment result in prompt tuning mode.
    """
    if not PROMPT_TUNING_MODE:
        return
    
    pt_output(f"\n  🏆 WINNER: {'Joke 1' if winner == '1' else 'Joke 2'}")
    if critique:
        pt_output("\n  📋 CRITIQUE:")
        # Truncate critique for display
        critique_lines = critique.split('\\n')[:5]
        for line in critique_lines:
            if len(line) > 70:
                line = line[:67] + "..."
            pt_output(f"    {line}")


def pt_item_start(item_id: str, task_type: str, original_input: str):
    """Log the start of processing an item in prompt tuning mode."""
    if not PROMPT_TUNING_MODE:
        return
    
    task_names = {
        "a1": "Headline Joke",
        "a2": "Word Inclusion Joke", 
        "b1": "GIF Caption",
        "b2": "GIF+Prompt Caption"
    }
    
    pt_section(f"🎭 {task_names.get(task_type, task_type).upper()} - {item_id}")
    pt_output(f"\n  INPUT: {original_input[:200]}{'...' if len(original_input) > 200 else ''}")


def pt_context(situation: str, semantic_associations: List[str] = None):
    """Log context enrichment output in prompt tuning mode."""
    if not PROMPT_TUNING_MODE:
        return
    
    pt_subsection("📋 CONTEXT ANALYSIS")
    pt_field("situation", situation)
    if semantic_associations:
        pt_field("semantic_associations", semantic_associations)


# =========================================================================
# STANDARD LOGGING FUNCTIONS (improved consistency)
# =========================================================================

def log_section(title: str, char: str = "=", width: int = 80):
    """Log a section header. Also triggers prompt tuning section."""
    line = char * width
    logger.info(f"\n{line}")
    logger.info(f" {title}")
    logger.info(f"{line}")


def log_subsection(title: str, char: str = "-", width: int = 60):
    """Log a subsection header."""
    line = char * width
    logger.info(f"\n{line}")
    logger.info(f" {title}")
    logger.info(f"{line}")


def log_input(input_data: dict, module_name: str = ""):
    """
    Log input data in a readable format.
    
    Args:
        input_data: Dictionary of input fields
        module_name: Name of the module receiving the input
    """
    logger.debug(f"📥 INPUT → {module_name}")
    for key, value in input_data.items():
        if isinstance(value, list):
            logger.debug(f"  {key}:")
            for item in value:
                logger.debug(f"    - {item}")
        else:
            str_value = str(value)
            if len(str_value) > 200:
                str_value = str_value[:200] + "..."
            logger.debug(f"  {key}: {str_value}")


def log_output(output_data: dict, module_name: str = "", branch_id: str = ""):
    """
    Log output data in a readable format.
    
    Args:
        output_data: Dictionary of output fields
        module_name: Name of the module that produced the output
        branch_id: Optional branch identifier for parallel execution
    """
    header = f"📤 OUTPUT ← {module_name}"
    if branch_id:
        header += f" [{branch_id}]"
    
    logger.info(header)
    for key, value in output_data.items():
        if isinstance(value, list):
            logger.info(f"  {key}:")
            for item in value:
                logger.info(f"    - {item}")
        else:
            str_value = str(value)
            if '\n' in str_value:
                logger.info(f"  {key}:")
                for line in str_value.split('\n'):
                    logger.info(f"    {line}")
            else:
                if len(str_value) > 200:
                    str_value = str_value[:200] + "..."
                logger.info(f"  {key}: {str_value}")
    
    # Also log to prompt tuning if enabled
    pt_module_output(module_name, output_data, branch_id)


def log_dspy_trace(lm: dspy.LM, module_name: str = ""):
    """
    Log DSPy internals including the prompt and completion.
    
    Args:
        lm: DSPy LM instance
        module_name: Name of the module
    """
    if not hasattr(lm, 'history') or not lm.history:
        logger.debug("No DSPy history available")
        return
    
    last_call = lm.history[-1]
    
    log_subsection(f"🔍 DSPy TRACE [{module_name}]")
    
    # Log the prompt
    if 'prompt' in last_call:
        prompt = last_call['prompt']
        if isinstance(prompt, list):
            # Chat format
            for msg in prompt:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                logger.debug(f"  [{role}]: {content[:500]}..." if len(content) > 500 else f"  [{role}]: {content}")
        else:
            logger.debug(f"  Prompt: {prompt[:500]}..." if len(str(prompt)) > 500 else f"  Prompt: {prompt}")
    
    # Log the completion
    if 'response' in last_call:
        response = last_call['response']
        logger.debug(f"  Response: {str(response)[:500]}...")
    
    # Log token usage
    if LOG_TOKEN_USAGE:
        # Use shared utility for token extraction
        from utils import extract_token_usage
        input_tokens, output_tokens = extract_token_usage(last_call)
        
        logger.info(f"  📊 Tokens: {input_tokens} in / {output_tokens} out = {input_tokens + output_tokens} total")


def log_joke_generation(
    item_id: str,
    input_text: str,
    generated_joke: str,
    module_outputs: dict,
    token_usage: dict,
):
    """
    Log a complete joke generation with all intermediate steps.
    
    Args:
        item_id: ID of the input item
        input_text: Original input (headline/words/GIF description)
        generated_joke: Final generated joke
        module_outputs: Dictionary of outputs from each module
        token_usage: Token usage statistics
    """
    log_section(f"🎭 JOKE GENERATION: {item_id}")
    
    logger.info(f"\n📝 Original Input: {input_text}")
    
    # Log each module's output
    for module_name, outputs in module_outputs.items():
        log_output(outputs, module_name)
    
    logger.info(f"\n🎯 FINAL JOKE:\n{'-'*40}\n{generated_joke}\n{'-'*40}")
    
    # Log token usage
    if token_usage:
        logger.info(f"\n📊 Token Usage: {token_usage['total_input_tokens']} in / {token_usage['total_output_tokens']} out")


def log_constraint_check(
    item_id: str,
    constraint_type: str,
    passed: bool,
    details: dict,
):
    """
    Log constraint satisfaction check results.
    
    Args:
        item_id: ID of the item
        constraint_type: Type of constraint (word_inclusion, length, etc.)
        passed: Whether the constraint was satisfied
        details: Additional details about the check
    """
    status = "✅ PASSED" if passed else "❌ FAILED"
    logger.info(f"  Constraint [{constraint_type}]: {status}")
    for key, value in details.items():
        logger.info(f"    {key}: {value}")


def log_progress(current: int, total: int, task: str = ""):
    """Log progress through the dataset."""
    percentage = (current / total) * 100 if total > 0 else 0
    bar_length = 30
    filled = int(bar_length * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)
    logger.info(f"Progress [{task}]: |{bar}| {current}/{total} ({percentage:.1f}%)")


def log_error(error: Exception, context: str = ""):
    """Log an error with context."""
    logger.error(f"❌ Error in {context}: {type(error).__name__}: {str(error)}")


def log_summary(stats: dict):
    """Log final summary statistics."""
    log_section("📈 SUMMARY")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")


def create_run_logger(run_id: str = None) -> logging.Logger:
    """
    Create a logger for a specific run with its own log file.
    
    Args:
        run_id: Unique identifier for this run (defaults to timestamp)
    
    Returns:
        Logger instance
    """
    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    log_file = f"run_{run_id}.log"
    return setup_logger(f"mwahaha_{run_id}", log_file)
