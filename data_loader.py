"""
Data Loader Module for the MWAHAHA Humor Generation Pipeline.

Handles:
- Loading input TSV files for all tasks
- Resume capability (reading existing outputs)
- Data structure normalization
- Test/Full mode sample selection
"""

import csv
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import config
from config import (
    INPUT_DIR,
    OUTPUT_DIR,
    TEST_OUTPUT_DIR,
    COMPLETE_OUTPUT_DIR,
    TEST_LIMITS,
    BASE_DIR,
)
from logger import logger


def sanitize_text_for_tsv(text: str) -> str:
    """
    Sanitize text for TSV output by removing/replacing problematic characters.
    
    TSV format expects one record per line. Newlines within fields break parsing.
    
    Args:
        text: Raw text that may contain newlines
    
    Returns:
        Sanitized text with newlines replaced by spaces
    """
    if not text:
        return text
    
    # Replace all types of newlines with a single space
    sanitized = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    
    # Collapse multiple consecutive spaces into one
    while '  ' in sanitized:
        sanitized = sanitized.replace('  ', ' ')
    
    return sanitized.strip()


@dataclass
class TaskAItem:
    """Data structure for Task A items (headlines or word inclusion)."""
    id: str
    word1: Optional[str]  # None or "-" means headline task
    word2: Optional[str]
    headline: Optional[str]  # None or "-" means word inclusion task
    
    @property
    def is_headline_task(self) -> bool:
        """Check if this is a headline-based task."""
        return self.headline and self.headline != "-"
    
    @property
    def is_word_inclusion_task(self) -> bool:
        """Check if this is a word inclusion task."""
        return self.word1 and self.word1 != "-" and self.word2 and self.word2 != "-"
    
    @property
    def input_text(self) -> str:
        """Get the primary input text for this item."""
        if self.is_headline_task:
            return self.headline
        elif self.is_word_inclusion_task:
            return f"{self.word1}, {self.word2}"
        return ""


@dataclass
class TaskB1Item:
    """Data structure for Task B1 items (GIF caption)."""
    id: str
    url: str
    description: str = None  # Preprocessed GIF description
    
    @property
    def input_text(self) -> str:
        return self.description if self.description else self.url


@dataclass
class TaskB2Item:
    """Data structure for Task B2 items (GIF + prompt)."""
    id: str
    url: str
    prompt: str
    description: str = None  # Preprocessed GIF description
    
    @property
    def input_text(self) -> str:
        if self.description:
            return f"GIF Description: {self.description}\n\nPrompt to Complete: {self.prompt}"
        return f"{self.url}\nPrompt: {self.prompt}"


def load_task_a(language: str, test_mode: bool = True) -> list[TaskAItem]:
    """
    Load Task A data for a specific language.
    
    Args:
        language: Language code ("en", "es", "zh")
        test_mode: If True, limit samples for testing
    
    Returns:
        List of TaskAItem objects
    """
    file_path = INPUT_DIR / f"task-a-{language}.tsv"
    
    if not file_path.exists():
        logger.error(f"Input file not found: {file_path}")
        return []
    
    items = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            item = TaskAItem(
                id=row['id'],
                word1=row.get('word1'),
                word2=row.get('word2'),
                headline=row.get('headline'),
            )
            items.append(item)
    
    logger.info(f"Loaded {len(items)} items from {file_path.name}")
    
    if test_mode:
        # In test mode, get a mix of headline and word inclusion tasks
        headline_items = [i for i in items if i.is_headline_task]
        word_items = [i for i in items if i.is_word_inclusion_task]
        
        limit = TEST_LIMITS["task_a"]
        half_limit = limit // 2
        
        selected = headline_items[:half_limit] + word_items[:half_limit]
        logger.info(f"Test mode: selected {len(selected)} items ({half_limit} headlines, {half_limit} word inclusion)")
        return selected
    
    return items


def load_task_b1(test_mode: bool = True) -> list[TaskB1Item]:
    """
    Load Task B1 data (GIF captions) from preprocessed file.
    
    Args:
        test_mode: If True, limit samples for testing
    
    Returns:
        List of TaskB1Item objects with preprocessed GIF descriptions
    """
    # Try preprocessed file first (contains GIF descriptions)
    preprocessed_path = BASE_DIR / "preprocessed" / "task-b1-preprocessed.tsv"
    
    if preprocessed_path.exists():
        items = []
        with open(preprocessed_path, 'r', encoding='utf-8') as f:
            # Task B1 preprocessed file has no header, columns are: id, url, description
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    item = TaskB1Item(
                        id=parts[0],
                        url=parts[1],
                        description=parts[2],
                    )
                    items.append(item)
        
        logger.info(f"Loaded {len(items)} preprocessed items from {preprocessed_path.name}")
    else:
        # Fallback to original file (will need GIF analysis)
        file_path = INPUT_DIR / "task-b1.tsv"
        
        if not file_path.exists():
            logger.error(f"Input file not found: {file_path}")
            return []
        
        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                item = TaskB1Item(
                    id=row['id'],
                    url=row['url'],
                    description=None,  # Will need GIF analysis
                )
                items.append(item)
        
        logger.info(f"Loaded {len(items)} items from {file_path.name}")
    
    if test_mode:
        limit = TEST_LIMITS["task_b1"]
        logger.info(f"Test mode: selected {limit} items")
        return items[:limit]
    
    return items


def load_task_b2(test_mode: bool = True) -> list[TaskB2Item]:
    """
    Load Task B2 data (GIF + prompt) from preprocessed file.
    
    Args:
        test_mode: If True, limit samples for testing
    
    Returns:
        List of TaskB2Item objects with preprocessed GIF descriptions
    """
    # Try preprocessed file first (contains GIF descriptions)
    preprocessed_path = BASE_DIR / "preprocessed" / "task-b2-preprocessed.tsv"
    
    if preprocessed_path.exists():
        items = []
        with open(preprocessed_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                item = TaskB2Item(
                    id=row['id'],
                    url=row['url'],
                    prompt=row['prompt'],
                    description=row['description'],
                )
                items.append(item)
        
        logger.info(f"Loaded {len(items)} preprocessed items from {preprocessed_path.name}")
    else:
        # Fallback to original file (will need GIF analysis)
        file_path = INPUT_DIR / "task-b2.tsv"
        
        if not file_path.exists():
            logger.error(f"Input file not found: {file_path}")
            return []
        
        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                item = TaskB2Item(
                    id=row['id'],
                    url=row['url'],
                    prompt=row['prompt'],
                    description=None,  # Will need GIF analysis
                )
                items.append(item)
        
        logger.info(f"Loaded {len(items)} items from {file_path.name}")
    
    if test_mode:
        limit = TEST_LIMITS["task_b2"]
        logger.info(f"Test mode: selected {limit} items")
        return items[:limit]
    
    return items


def load_existing_outputs(task_name: str, test_mode: bool = True, complete_mode: bool = False) -> dict[str, str]:
    """
    Load existing outputs for resume capability.
    
    Args:
        task_name: Name of the task file (e.g., "task-a-en")
        test_mode: Determines which output directory to use
        complete_mode: If True, loads from complete output directory instead
    
    Returns:
        Dictionary mapping id -> generated text (or special marker)
        
        Special markers:
        - "[NO_VALID_CANDIDATES]" - Item was processed but all candidates failed validation
        - "[ERROR: ...]" - Item failed with an error
        - Normal text - Item successfully processed with valid candidates
    """
    if complete_mode:
        # For complete mode, check the JSONL file for processed items
        output_dir = COMPLETE_OUTPUT_DIR / ("test" if test_mode else "full")
        jsonl_path = output_dir / f"{task_name}_llm_outputs.jsonl"
        
        if not jsonl_path.exists():
            logger.info(f"No existing complete output file found: {jsonl_path}")
            return {}
        
        existing = {}
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    item_id = record.get('id')
                    candidates = record.get('candidates', [])
                    
                    if not item_id:
                        continue
                    
                    # Check if there are any valid candidates
                    if not candidates or len(candidates) == 0:
                        # Item was processed but produced no candidates
                        existing[item_id] = "[NO_VALID_CANDIDATES]"
                    else:
                        # Use the first candidate as placeholder text to indicate it exists
                        existing[item_id] = candidates[0].get('joke', '[GENERATED]')
        
        logger.info(f"Loaded {len(existing)} existing complete outputs from {jsonl_path.name}")
        
        # Count items needing regeneration
        no_candidates = sum(1 for v in existing.values() if v == "[NO_VALID_CANDIDATES]")
        if no_candidates > 0:
            logger.warning(f"⚠️  Found {no_candidates} items with no valid candidates (will regenerate)")
        
        return existing
    
    output_dir = TEST_OUTPUT_DIR if test_mode else OUTPUT_DIR
    file_path = output_dir / f"{task_name}.tsv"
    
    if not file_path.exists():
        logger.info(f"No existing output file found: {file_path}")
        return {}
    
    existing = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            existing[row['id']] = row['text']
    
    logger.info(f"Loaded {len(existing)} existing outputs from {file_path.name}")
    return existing


def get_remaining_items(items: list, existing_outputs: dict) -> list:
    """
    Filter items to only those not yet processed or that failed with errors.
    
    Items with ERROR placeholders (e.g., "[ERROR: ...]") are considered
    unprocessed and will be retried on resume.
    
    Items with "[NO_VALID_CANDIDATES]" marker (all candidates failed validation)
    are also retried to regenerate with different variations.
    
    Args:
        items: List of input items
        existing_outputs: Dictionary of already processed items
    
    Returns:
        List of items still needing processing (including failed ones)
    """
    remaining = []
    skipped_success = 0
    retrying_errors = 0
    retrying_no_candidates = 0
    
    for item in items:
        if item.id not in existing_outputs:
            # Not processed yet
            remaining.append(item)
        elif existing_outputs[item.id].startswith("[ERROR"):
            # Previously failed - retry it
            remaining.append(item)
            retrying_errors += 1
        elif existing_outputs[item.id] == "[NO_VALID_CANDIDATES]":
            # All candidates were rejected (failed validation) - regenerate
            remaining.append(item)
            retrying_no_candidates += 1
        else:
            # Successfully processed with valid candidates
            skipped_success += 1
    
    if skipped_success > 0 or retrying_errors > 0 or retrying_no_candidates > 0:
        msg = f"Resuming: {skipped_success} succeeded (skipping)"
        if retrying_errors > 0:
            msg += f", {retrying_errors} failed (retrying)"
        if retrying_no_candidates > 0:
            msg += f", {retrying_no_candidates} no valid candidates (regenerating)"
        msg += f", {len(remaining) - retrying_errors - retrying_no_candidates} new"
        logger.info(msg)
    
    return remaining


def save_output(
    task_name: str,
    item_id: str,
    text: str,
    test_mode: bool = True,
    append: bool = True,
):
    """
    Save a generated output to the appropriate TSV file.
    
    Args:
        task_name: Name of the task file (e.g., "task-a-en")
        item_id: ID of the item
        text: Generated text
        test_mode: Determines which output directory to use
        append: If True, append to existing file
    """
    output_dir = TEST_OUTPUT_DIR if test_mode else OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    
    file_path = output_dir / f"{task_name}.tsv"
    
    # Check if file exists and has header
    file_exists = file_path.exists()
    
    mode = 'a' if append and file_exists else 'w'
    
    # Sanitize text to ensure single-line format for TSV
    sanitized_text = sanitize_text_for_tsv(text)
    
    with open(file_path, mode, encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        
        # Write header if new file
        if mode == 'w':
            writer.writerow(['id', 'text'])
        
        writer.writerow([item_id, sanitized_text])


def save_outputs_batch(
    task_name: str,
    outputs: dict[str, str],
    test_mode: bool = True,
):
    """
    Save multiple outputs at once, preserving order.
    
    Args:
        task_name: Name of the task file
        outputs: Dictionary mapping id -> text
        test_mode: Determines which output directory to use
    """
    output_dir = TEST_OUTPUT_DIR if test_mode else OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    
    file_path = output_dir / f"{task_name}.tsv"
    
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['id', 'text'])
        
        for item_id, text in outputs.items():
            # Sanitize each text to ensure single-line format for TSV
            sanitized_text = sanitize_text_for_tsv(text)
            writer.writerow([item_id, sanitized_text])
    
    logger.info(f"Saved {len(outputs)} outputs to {file_path}")


def get_task_file_name(task: str, language: str = None) -> str:
    """
    Get the standard file name for a task.
    
    Args:
        task: Task type ("a", "b1", "b2")
        language: Language code for Task A
    
    Returns:
        File name without extension
    """
    if task == "a" and language:
        return f"task-a-{language}"
    elif task == "b1":
        return "task-b1"
    elif task == "b2":
        return "task-b2"
    else:
        raise ValueError(f"Unknown task: {task}")


def save_complete_output(
    task_name: str,
    item_id: str,
    winner_joke: str,
    all_candidates: list[tuple[str, dict]],
    test_mode: bool = True,
    original_input: str = None,
    language: str = None,
    word1: str = None,
    word2: str = None,
    task_type: str = None,
):
    """
    Save complete output with all candidates and full LLM outputs.
    
    Creates two files in the 'complete' directory:
    1. {task_name}_complete.tsv - All candidates (untruncated)
    2. {task_name}_llm_outputs.jsonl - Full LLM outputs for analysis
    
    Args:
        task_name: Name of the task file (e.g., "task-a-en")
        item_id: ID of the item
        winner_joke: The final selected joke (None if judging was skipped)
        all_candidates: List of (joke, module_outputs) tuples
        test_mode: Determines which output directory to use
        original_input: Original input text (for later judging)
        language: Language code (for later judging)
        word1: First required word (for Task A2)
        word2: Second required word (for Task A2)
        task_type: Task type ("a1", "a2", "b1", "b2")
    """
    if not config.SAVE_COMPLETE_OUTPUT:
        return
    
    output_dir = COMPLETE_OUTPUT_DIR / ("test" if test_mode else "full")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Save complete TSV with all candidates
    tsv_path = output_dir / f"{task_name}_complete.tsv"
    tsv_exists = tsv_path.exists()
    
    with open(tsv_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        
        # Write header if new file
        if not tsv_exists:
            # Include is_winner column only if we have a winner
            if winner_joke is not None:
                writer.writerow(['id', 'candidate_num', 'is_winner', 'joke'])
            else:
                writer.writerow(['id', 'candidate_num', 'joke'])
        
        # Write all candidates
        for idx, (joke, _) in enumerate(all_candidates, 1):
            # Sanitize joke text to ensure single-line format for TSV
            sanitized_joke = sanitize_text_for_tsv(joke)
            if winner_joke is not None:
                is_winner = 'YES' if joke == winner_joke else 'NO'
                writer.writerow([item_id, idx, is_winner, sanitized_joke])
            else:
                writer.writerow([item_id, idx, sanitized_joke])
    
    # 2. Save full LLM outputs as JSONL
    jsonl_path = output_dir / f"{task_name}_llm_outputs.jsonl"
    
    with open(jsonl_path, 'a', encoding='utf-8') as f:
        record = {
            'id': item_id,
            'original_input': original_input,
            'task_type': task_type,
            'language': language,
            'word1': word1,
            'word2': word2,
            'winner_joke': winner_joke,  # None if judging skipped
            'judged': winner_joke is not None,
            'candidates': [
                {
                    'candidate_num': idx,
                    'joke': joke,
                    'is_winner': joke == winner_joke if winner_joke else None,
                    'module_outputs': outputs,
                }
                for idx, (joke, outputs) in enumerate(all_candidates, 1)
            ],
        }
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    logger.debug(f"Saved complete output for {item_id} to {output_dir}")
