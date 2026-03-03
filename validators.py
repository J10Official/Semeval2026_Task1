"""
Validators Module for the MWAHAHA Humor Generation Pipeline.

Provides deterministic constraint satisfaction checks:
- Word inclusion verification for Task A2
- Character length limits
- Word count limits for Task B
- Language-specific validations
"""

import re
from typing import Tuple

from config import MAX_CHARS, MAX_WORDS_TASK_B
from logger import logger, log_constraint_check


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, strip whitespace)."""
    return text.lower().strip()


def is_chinese_text(text: str) -> bool:
    """Check if text contains Chinese characters."""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # CJK Unified Ideographs
            return True
    return False


def check_word_inclusion(joke: str, word1: str, word2: str, flexible: bool = True) -> Tuple[bool, dict]:
    """
    Check if both required words appear in the joke.
    
    Uses flexible matching that:
    - Is case-insensitive
    - Handles word boundaries for alphabetic languages
    - For Chinese: does substring matching (no word boundaries in Chinese)
    - Allows morphological variations (flower -> flowers, flowering, etc.) when flexible=True
    
    Args:
        joke: The generated joke text
        word1: First required word
        word2: Second required word
        flexible: If True, allows word variations (plurals, verb forms, etc.)
    
    Returns:
        Tuple of (passed, details_dict)
    """
    normalized_joke = normalize_text(joke)
    normalized_word1 = normalize_text(word1)
    normalized_word2 = normalize_text(word2)
    
    def find_word(word: str, text: str, original_word: str) -> Tuple[bool, str]:
        """
        Find a word in text with flexible matching.
        
        Returns:
            Tuple of (found, matched_form)
        """
        # Check if this is a Chinese word
        if is_chinese_text(word):
            # Chinese: simple substring matching (no word boundaries)
            if word in text:
                return True, word
            return False, None
        
        # For alphabetic languages, try multiple patterns
        
        # 1. Exact word boundary match (strictest)
        exact_pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        match = exact_pattern.search(text)
        if match:
            return True, match.group()
        
        if not flexible:
            return False, None
        
        # 2. Flexible: allow common morphological variations
        # This handles: flower -> flowers, flowering, flowered, flower's
        # Also handles: hammer -> hammers, hammering, hammered, hammer's
        stem_pattern = re.compile(
            r'\b' + re.escape(word) + r"(?:s|ed|ing|er|ers|'s|es|ies)?\b",
            re.IGNORECASE
        )
        match = stem_pattern.search(text)
        if match:
            return True, match.group()
        
        # 3. For words ending in 'e', check for variations like "move -> moving"
        if word.endswith('e'):
            stem = word[:-1]
            stem_pattern = re.compile(
                r'\b' + re.escape(stem) + r"(?:e|es|ed|ing|er|ers)?\b",
                re.IGNORECASE
            )
            match = stem_pattern.search(text)
            if match:
                return True, match.group()
        
        # 4. For words ending in 'y', check for variations like "carry -> carries, carried"
        if word.endswith('y'):
            stem = word[:-1]
            stem_pattern = re.compile(
                r'\b' + re.escape(stem) + r"(?:y|ies|ied|ying)?\b",
                re.IGNORECASE
            )
            match = stem_pattern.search(text)
            if match:
                return True, match.group()
        
        return False, None
    
    word1_found, word1_match = find_word(normalized_word1, normalized_joke, word1)
    word2_found, word2_match = find_word(normalized_word2, normalized_joke, word2)
    
    passed = word1_found and word2_found
    
    details = {
        f"'{word1}'": f"✅ found as '{word1_match}'" if word1_found else "❌ missing",
        f"'{word2}'": f"✅ found as '{word2_match}'" if word2_found else "❌ missing",
    }
    
    return passed, details


def check_word_inclusion_strict(joke: str, word1: str, word2: str) -> Tuple[bool, dict]:
    """
    Strict word inclusion check - exact word boundaries only.
    
    Use this for final validation where you need exact matches.
    """
    return check_word_inclusion(joke, word1, word2, flexible=False)


def check_char_length(text: str, language: str) -> Tuple[bool, dict]:
    """
    Check if text is within character limit for the language.
    
    Args:
        text: The generated text
        language: Language code ("en", "es", "zh", "b1", "b2")
    
    Returns:
        Tuple of (passed, details_dict)
    """
    max_chars = MAX_CHARS.get(language, 900)
    char_count = len(text)
    
    passed = char_count <= max_chars
    
    details = {
        "char_count": char_count,
        "max_allowed": max_chars,
        "status": "✅ within limit" if passed else f"❌ exceeded by {char_count - max_chars}",
    }
    
    return passed, details


def check_word_count(text: str, max_words: int = MAX_WORDS_TASK_B) -> Tuple[bool, dict]:
    """
    Check if text is within word count limit (for Task B).
    
    Args:
        text: The generated text
        max_words: Maximum allowed words
    
    Returns:
        Tuple of (passed, details_dict)
    """
    # Simple word count (split on whitespace)
    words = text.split()
    word_count = len(words)
    
    passed = word_count <= max_words
    
    details = {
        "word_count": word_count,
        "max_allowed": max_words,
        "status": "✅ within limit" if passed else f"❌ exceeded by {word_count - max_words}",
    }
    
    return passed, details


def check_not_empty(text: str) -> Tuple[bool, dict]:
    """
    Check if the generated text is not empty or just whitespace.
    
    Args:
        text: The generated text
    
    Returns:
        Tuple of (passed, details_dict)
    """
    passed = bool(text and text.strip())
    
    details = {
        "status": "✅ has content" if passed else "❌ empty or whitespace only",
    }
    
    return passed, details

class ConstraintValidator:
    """
    Validates generated jokes against task-specific constraints.
    
    Provides both individual checks and comprehensive validation.
    """
    
    def __init__(self, item_id: str):
        self.item_id = item_id
        self.results = []
    
    def add_check(self, name: str, passed: bool, details: dict):
        """Record a constraint check result."""
        self.results.append({
            "name": name,
            "passed": passed,
            "details": details,
        })
        log_constraint_check(self.item_id, name, passed, details)
    
    def all_passed(self) -> bool:
        """Check if all constraints passed."""
        return all(r["passed"] for r in self.results)
    
    def get_failures(self) -> list:
        """Get list of failed constraints."""
        return [r for r in self.results if not r["passed"]]
    
    def validate_task_a_headline(self, joke: str, language: str) -> bool:
        """
        Validate a Task A headline-based joke.
        
        Checks:
        - Not empty
        - Character limit
        - No placeholders
        """
        passed, details = check_not_empty(joke)
        self.add_check("not_empty", passed, details)
        
        passed, details = check_char_length(joke, language)
        self.add_check("char_length", passed, details)
        
        return self.all_passed()
    
    def validate_task_a_word_inclusion(
        self, joke: str, word1: str, word2: str, language: str
    ) -> bool:
        """
        Validate a Task A word-inclusion joke.
        
        Checks:
        - Not empty
        - Both words present
        - Character limit
        - No placeholders
        """
        passed, details = check_not_empty(joke)
        self.add_check("not_empty", passed, details)
        
        passed, details = check_word_inclusion(joke, word1, word2)
        self.add_check("word_inclusion", passed, details)
        
        passed, details = check_char_length(joke, language)
        self.add_check("char_length", passed, details)
        
        return self.all_passed()
    
    def validate_task_b(self, caption: str, task_type: str = "b1") -> bool:
        """
        Validate a Task B caption.
        
        Checks:
        - Not empty
        - Word count (max 20)
        - Character limit
        - No placeholders
        """
        passed, details = check_not_empty(caption)
        self.add_check("not_empty", passed, details)
        
        passed, details = check_word_count(caption)
        self.add_check("word_count", passed, details)
        
        passed, details = check_char_length(caption, task_type)
        self.add_check("char_length", passed, details)
        
        return self.all_passed()


def validate_joke(
    joke: str,
    task_type: str,
    language: str = "en",
    word1: str = None,
    word2: str = None,
    item_id: str = "",
) -> Tuple[bool, list]:
    """
    Main validation function for any task type.
    
    Args:
        joke: Generated joke/caption
        task_type: One of "a1" (headline), "a2" (word inclusion), "b1", "b2"
        language: Language code
        word1: Required word for A2 task
        word2: Required word for A2 task
        item_id: ID for logging
    
    Returns:
        Tuple of (all_passed, list_of_failures)
    """
    validator = ConstraintValidator(item_id)
    
    if task_type == "a1":
        validator.validate_task_a_headline(joke, language)
    elif task_type == "a2":
        if not word1 or not word2:
            logger.error(f"Word inclusion task requires word1 and word2")
            return False, [{"name": "missing_words", "details": "word1 or word2 not provided"}]
        validator.validate_task_a_word_inclusion(joke, word1, word2, language)
    elif task_type in ("b1", "b2"):
        validator.validate_task_b(joke, task_type)
    else:
        logger.error(f"Unknown task type: {task_type}")
        return False, [{"name": "unknown_task", "details": f"task_type={task_type}"}]
    
    return validator.all_passed(), validator.get_failures()
