#!/usr/bin/env python3
"""
MWAHAHA Humor Generation Pipeline - Main Entry Point

Usage:
    python main.py                           # Test mode, all tasks
    python main.py --full                    # Full mode, all tasks
    python main.py --task a-en               # Test mode, Task A English only
    python main.py --task b1 --full          # Full mode, Task B1 only
    python main.py --full --resume           # Full mode with resume capability
    python main.py --parallel 4              # Process 4 jokes in parallel
    python main.py -p 2 --task a-en --full   # 2 parallel workers, Task A English, full mode

Judge Mode (--judge):
    python main.py --judge --full            # Judge all tasks from complete/full
    python main.py --judge --full --task a-en  # Judge only Task A English
    
    Judge mode loads candidates from complete/{test,full}/{task}_llm_outputs.jsonl,
    validates constraints (with flexible regex for word inclusion), runs the
    HumorJudge module, and outputs winners to judged_outputs/{test,full}/{task}.tsv
    in the required submission format (id, text columns).

Tasks:
    a-en    Task A English (headlines + word inclusion)
    a-es    Task A Spanish
    a-zh    Task A Chinese
    b1      Task B1 (GIF captions)
    b2      Task B2 (GIF + prompt captions)
    all     All tasks (default)

Parallel Processing:
    --parallel N    Process N jokes concurrently (default: 1, max: 8)
    
    The pipeline tracks which items have been processed to avoid duplicates.
    Use --resume to continue from where you left off.
"""

import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional, List, Dict, Any

from config import (
    OUTPUT_DIR,
    TEST_OUTPUT_DIR,
    LOG_DIR,
    SAVE_COMPLETE_OUTPUT,
    PARALLEL_JOKES,
    MAX_PARALLEL_JOKES,
    COMPLETE_OUTPUT_DIR,
    JUDGED_OUTPUT_DIR,
)
import config  # For modifying SAVE_COMPLETE_OUTPUT at runtime
from api import configure_dspy, get_token_summary, reset_token_tracker, get_retry_summary, get_retry_formatted_summary, reset_all_trackers, is_openrouter_model_free, get_openrouter_model_name
from gif_analyzer import analyze_gif_for_b1, analyze_gif_for_b2
from data_loader import (
    load_task_a,
    load_task_b1,
    load_task_b2,
    load_existing_outputs,
    get_remaining_items,
    save_output,
    save_complete_output,
    get_task_file_name,
    sanitize_text_for_tsv,
)
from pipeline import UnifiedHumorPipeline
from validators import validate_joke, check_word_inclusion
from logger import (
    logger,
    log_section,
    log_progress,
    log_summary,
    log_error,
    create_run_logger,
    add_file_handler_to_logger,
    log_subsection,
)


# =========================================================================
# THREAD-SAFE PROGRESS TRACKER
# =========================================================================

class ProgressTracker:
    """
    Thread-safe progress tracker for parallel processing.
    
    Tracks which items have been processed to avoid duplicates and
    provides thread-safe statistics updates.
    """
    
    def __init__(self, total: int, task_name: str):
        self._lock = threading.Lock()
        self._processed_ids = set()
        self._stats = {"processed": 0, "errors": 0}
        self._total = total
        self._task_name = task_name
        self._completed = 0
    
    def is_processed(self, item_id: str) -> bool:
        """Check if an item has already been processed (thread-safe)."""
        with self._lock:
            return item_id in self._processed_ids
    
    def mark_processed(self, item_id: str) -> bool:
        """
        Mark an item as processed (thread-safe).
        
        Returns:
            True if item was newly marked, False if already processed
        """
        with self._lock:
            if item_id in self._processed_ids:
                return False
            self._processed_ids.add(item_id)
            self._completed += 1
            return True
    
    def increment_stat(self, stat_name: str, value: int = 1):
        """Increment a statistic (thread-safe)."""
        with self._lock:
            if stat_name not in self._stats:
                self._stats[stat_name] = 0
            self._stats[stat_name] += value
    
    def get_stats(self) -> dict:
        """Get a copy of current statistics (thread-safe)."""
        with self._lock:
            return self._stats.copy()
    
    def get_progress(self) -> tuple[int, int]:
        """Get current progress (completed, total)."""
        with self._lock:
            return self._completed, self._total
    
    def log_progress(self):
        """Log current progress."""
        completed, total = self.get_progress()
        log_progress(completed, total, self._task_name)


# =========================================================================
# JUDGE-ONLY MODE FUNCTIONS
# =========================================================================

import json
import csv


def load_candidates_from_jsonl(task_name: str, test_mode: bool = False) -> List[Dict]:
    """
    Load all candidates from the JSONL file in complete directory.
    
    Args:
        task_name: Name of the task (e.g., "task-a-en")
        test_mode: Whether to use test or full directory
    
    Returns:
        List of item records with candidates
    """
    input_dir = COMPLETE_OUTPUT_DIR / ("test" if test_mode else "full")
    jsonl_path = input_dir / f"{task_name}_llm_outputs.jsonl"
    
    if not jsonl_path.exists():
        logger.error(f"No JSONL file found: {jsonl_path}")
        return []
    
    items = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                # Only load items with candidates
                if record.get('candidates') and len(record['candidates']) > 0:
                    items.append(record)
    
    logger.info(f"Loaded {len(items)} items with candidates from {jsonl_path.name}")
    return items


def filter_valid_candidates(
    item: Dict,
    task_type: str,
    language: str = "en",
    word1: str = None,
    word2: str = None,
) -> List[str]:
    """
    Filter candidates that pass constraint validation.
    
    Uses flexible regex matching for word inclusion.
    
    Args:
        item: Item record with candidates
        task_type: One of "a1", "a2", "b1", "b2"
        language: Language code
        word1: First required word (for a2)
        word2: Second required word (for a2)
    
    Returns:
        List of valid candidate jokes
    """
    valid = []
    
    for candidate in item.get('candidates', []):
        joke = candidate.get('joke', '')
        
        if not joke or not joke.strip():
            continue
        
        # For word inclusion tasks, check with flexible regex
        if task_type == "a2" and word1 and word2:
            passed, details = check_word_inclusion(joke, word1, word2, flexible=True)
            if not passed:
                logger.debug(f"Candidate {candidate.get('candidate_num')} failed word inclusion: {details}")
                continue
        
        # General validation (char length, word count for task B, etc.)
        passed, failures = validate_joke(
            joke,
            task_type,
            language,
            word1 if task_type == "a2" else None,
            word2 if task_type == "a2" else None,
            f"candidate_{candidate.get('candidate_num')}",
        )
        
        if passed:
            valid.append(joke)
        else:
            logger.debug(f"Candidate {candidate.get('candidate_num')} failed validation: {failures}")
    
    return valid


def save_judged_output(
    task_name: str,
    results: List[tuple],  # List of (id, text) tuples
    test_mode: bool = False,
):
    """
    Save judged results to TSV file in the required submission format.
    
    Output format (as per task.md):
    - id: the input's unique identifier
    - text: the humorous text generated by your system
    
    Args:
        task_name: Name of the task (e.g., "task-a-en")
        results: List of (id, text) tuples
        test_mode: Whether to use test or full directory
    """
    output_dir = JUDGED_OUTPUT_DIR / ("test" if test_mode else "full")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Output file name matches submission format: task-a-en.tsv, task-b1.tsv, etc.
    tsv_path = output_dir / f"{task_name}.tsv"
    
    with open(tsv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['id', 'text'])
        
        for item_id, text in results:
            # Sanitize text for TSV (remove newlines)
            sanitized_text = sanitize_text_for_tsv(text)
            writer.writerow([item_id, sanitized_text])
    
    logger.info(f"💾 Saved {len(results)} judged results to {tsv_path}")
    return tsv_path


def append_judged_result(
    task_name: str,
    item_id: str,
    text: str,
    test_mode: bool = False,
    write_header: bool = False,
):
    """
    Append a single judged result to the TSV file immediately.
    
    Args:
        task_name: Name of the task (e.g., "task-a-en")
        item_id: Item ID
        text: Winner text
        test_mode: Whether to use test or full directory
        write_header: Whether to write the header row
    """
    output_dir = JUDGED_OUTPUT_DIR / ("test" if test_mode else "full")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tsv_path = output_dir / f"{task_name}.tsv"
    
    # Sanitize text
    sanitized_text = sanitize_text_for_tsv(text)
    
    with open(tsv_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        if write_header:
            writer.writerow(['id', 'text'])
        writer.writerow([item_id, sanitized_text])


def load_already_judged(task_name: str, test_mode: bool = False) -> set:
    """
    Load IDs of items already judged (for resume capability).
    
    Args:
        task_name: Name of the task
        test_mode: Whether to use test directory
    
    Returns:
        Set of already-judged item IDs
    """
    output_dir = JUDGED_OUTPUT_DIR / ("test" if test_mode else "full")
    tsv_path = output_dir / f"{task_name}.tsv"
    
    if not tsv_path.exists():
        return set()
    
    judged_ids = set()
    with open(tsv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            judged_ids.add(row['id'])
    
    return judged_ids


def judge_from_complete(
    task_name: str,
    test_mode: bool = False,
    provider: str = "openrouter",
    parallel_jobs: int = 1,
) -> Dict:
    """
    Run judge-only mode: load candidates from complete/full, validate, judge, and output winners.
    
    This bypasses the generation pipeline and only runs the judge module
    on existing candidates. Results are saved incrementally to support resume.
    
    Args:
        task_name: Name of the task (e.g., "task-a-en", "task-b1")
        test_mode: Whether to use test directory
        provider: API provider for the judge
        parallel_jobs: Number of items to judge in parallel
    
    Returns:
        Statistics dictionary
    """
    log_section(f"⚖️ JUDGE MODE: {task_name.upper()}")
    
    # Load candidates
    items = load_candidates_from_jsonl(task_name, test_mode)
    
    if not items:
        logger.warning(f"No items found for {task_name}")
        return {"processed": 0, "errors": 0, "no_valid_candidates": 0}
    
    # Check for already judged items (resume capability)
    already_judged = load_already_judged(task_name, test_mode)
    if already_judged:
        original_count = len(items)
        items = [item for item in items if item['id'] not in already_judged]
        logger.info(f"Resume: {len(already_judged)} already judged, {len(items)} remaining")
        if not items:
            logger.info("All items already judged!")
            return {"processed": 0, "skipped": original_count, "errors": 0}
    
    # Determine task type from task name
    if "task-a" in task_name:
        language = task_name.split("-")[-1]  # en, es, zh
    else:
        language = "en"  # Task B is English only
    
    # Pre-create pipelines for each task type (thread-safe - one per type)
    pipelines = {}
    task_types_needed = set(item.get('task_type', 'a1') for item in items)
    for tt in task_types_needed:
        pipelines[tt] = UnifiedHumorPipeline(tt)
    
    # Thread-safe for stats and file writing
    write_lock = threading.Lock()
    stats = {
        "processed": 0,
        "errors": 0,
        "no_valid_candidates": 0,
        "a1_items": 0,
        "a2_items": 0,
    }
    
    # Prepare output file (write header if new)
    output_dir = JUDGED_OUTPUT_DIR / ("test" if test_mode else "full")
    output_dir.mkdir(parents=True, exist_ok=True)
    tsv_path = output_dir / f"{task_name}.tsv"
    
    # Write header if file doesn't exist
    if not tsv_path.exists():
        with open(tsv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['id', 'text'])
    
    def judge_single_item(item: Dict) -> bool:
        """Judge a single item and save immediately. Returns True on success."""
        item_id = item['id']
        task_type = item.get('task_type', 'a1')
        word1 = item.get('word1')
        word2 = item.get('word2')
        original_input = item.get('original_input', '')
        
        try:
            # Filter valid candidates
            valid_candidates = filter_valid_candidates(
                item, task_type, language, word1, word2
            )
            
            no_valid = False
            if not valid_candidates:
                # No valid candidates - use first candidate with warning
                logger.warning(f"⚠️ {item_id}: No valid candidates! Using first candidate anyway.")
                all_jokes = [c['joke'] for c in item['candidates'] if c.get('joke')]
                if all_jokes:
                    valid_candidates = [all_jokes[0]]
                    no_valid = True
                else:
                    logger.error(f"❌ {item_id}: No candidates at all!")
                    with write_lock:
                        stats["errors"] += 1
                    return False
            
            logger.info(f"📋 {item_id} ({task_type}): {len(valid_candidates)} valid candidates")
            
            # Get the pipeline for this task type
            pipeline = pipelines[task_type]
            
            # Judge candidates
            if len(valid_candidates) == 1:
                winner = valid_candidates[0]
                logger.info(f"  {item_id}: Only 1 valid candidate, selecting it as winner")
            else:
                winner = pipeline.judge_candidates(valid_candidates, original_input, language)
            
            logger.info(f"🏆 {item_id}: {winner[:80]}...")
            
            # IMMEDIATELY save to file
            sanitized_text = sanitize_text_for_tsv(winner)
            with write_lock:
                with open(tsv_path, 'a', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerow([item_id, sanitized_text])
                
                stats["processed"] += 1
                if no_valid:
                    stats["no_valid_candidates"] += 1
                if task_type == "a1":
                    stats["a1_items"] += 1
                elif task_type == "a2":
                    stats["a2_items"] += 1
            
            return True
            
        except Exception as e:
            log_error(e, f"judging {item_id}")
            # Save first candidate as fallback
            if item.get('candidates'):
                first_joke = item['candidates'][0].get('joke', '[ERROR]')
                sanitized_text = sanitize_text_for_tsv(first_joke)
                with write_lock:
                    with open(tsv_path, 'a', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f, delimiter='\t')
                        writer.writerow([item_id, sanitized_text])
                    stats["errors"] += 1
            else:
                with write_lock:
                    stats["errors"] += 1
            return False
    
    # Process items with parallelization
    num_workers = max(1, min(parallel_jobs, MAX_PARALLEL_JOKES))
    
    if num_workers <= 1:
        # Sequential processing
        logger.info(f"Judging {len(items)} items sequentially...")
        for i, item in enumerate(items):
            judge_single_item(item)
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{len(items)} items judged")
    else:
        # Parallel processing
        logger.info(f"Judging {len(items)} items with {num_workers} parallel workers...")
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(judge_single_item, item): item for item in items}
            completed = 0
            
            try:
                for future in as_completed(futures):
                    try:
                        future.result()
                        completed += 1
                        if completed % 10 == 0:
                            logger.info(f"Progress: {completed}/{len(items)} items judged")
                    except Exception as e:
                        item = futures[future]
                        logger.error(f"Unexpected error for {item['id']}: {e}")
            except KeyboardInterrupt:
                logger.warning("Interrupted by user. Partial results have been saved.")
                executor.shutdown(wait=False, cancel_futures=True)
    
    logger.info(f"💾 Results saved to {tsv_path}")
    
    return stats


def get_available_complete_tasks(test_mode: bool = False) -> List[str]:
    """Get list of available task files in complete directory."""
    input_dir = COMPLETE_OUTPUT_DIR / ("test" if test_mode else "full")
    
    if not input_dir.exists():
        return []
    
    tasks = []
    for f in input_dir.glob("*_llm_outputs.jsonl"):
        # Extract task name from filename
        task_name = f.stem.replace("_llm_outputs", "")
        tasks.append(task_name)
    
    return sorted(tasks)


def run_judge_mode(args) -> Dict:
    """
    Run the judge-only mode for all or selected tasks.
    
    Args:
        args: Command line arguments
    
    Returns:
        Combined statistics
    """
    test_mode = not args.full
    mode_str = "FULL" if args.full else "TEST"
    
    # Determine parallelism
    parallel_jobs = args.parallel if args.parallel else config.PARALLEL_JOKES
    parallel_jobs = min(parallel_jobs, MAX_PARALLEL_JOKES)
    
    log_section(f"⚖️ MWAHAHA JUDGE MODE - {mode_str}")
    logger.info(f"Parallel workers: {parallel_jobs}")
    
    # Get tasks to process
    if args.task and args.task != "all":
        # Map task argument to task name
        task_map = {
            "a-en": "task-a-en",
            "a-es": "task-a-es",
            "a-zh": "task-a-zh",
            "b1": "task-b1",
            "b2": "task-b2",
        }
        tasks = [task_map.get(args.task, args.task)]
    else:
        tasks = get_available_complete_tasks(test_mode)
    
    if not tasks:
        logger.error(f"No task files found in {COMPLETE_OUTPUT_DIR / ('test' if test_mode else 'full')}")
        return {}
    
    logger.info(f"Tasks to judge: {', '.join(tasks)}")
    
    # Configure API
    try:
        configure_dspy(provider_name=args.provider)
        logger.info(f"✅ API configured: {args.provider or 'default'}")
    except Exception as e:
        logger.error(f"❌ Failed to configure API: {e}")
        return {}
    
    reset_all_trackers()
    
    # Process each task
    all_stats = {}
    
    for task_name in tasks:
        try:
            stats = judge_from_complete(task_name, test_mode, args.provider, parallel_jobs)
            all_stats[task_name] = stats
        except Exception as e:
            log_error(e, f"processing {task_name}")
            all_stats[task_name] = {"error": str(e)}
    
    # Summary
    log_section("📊 JUDGE MODE SUMMARY")
    
    total_processed = 0
    total_errors = 0
    for task_name, stats in all_stats.items():
        if isinstance(stats, dict):
            processed = stats.get("processed", 0)
            errors = stats.get("errors", 0)
            no_valid = stats.get("no_valid_candidates", 0)
            
            logger.info(f"  {task_name}: {processed} judged, {errors} errors, {no_valid} no valid candidates")
            total_processed += processed
            total_errors += errors
    
    logger.info(f"\n✨ Total: {total_processed} items judged, {total_errors} errors")
    logger.info(f"📁 Output directory: {JUDGED_OUTPUT_DIR / ('test' if test_mode else 'full')}")
    
    # Token usage
    token_summary = get_token_summary()
    logger.info(f"\n📈 Token Usage:")
    logger.info(f"  API Calls: {token_summary['total_api_calls']}")
    logger.info(f"  Input: {token_summary['total_input_tokens']:,}")
    logger.info(f"  Output: {token_summary['total_output_tokens']:,}")
    
    return all_stats


def process_task_a(
    language: str,
    test_mode: bool = True,
    resume: bool = False,
    parallel_jobs: int = None,
) -> dict:
    """
    Process Task A for a specific language with optional parallel processing.
    
    Args:
        language: Language code ("en", "es", "zh")
        test_mode: If True, process limited samples
        resume: If True, skip already processed items
        parallel_jobs: Number of parallel workers (None = use config.PARALLEL_JOKES)
    
    Returns:
        Statistics dictionary
    """
    log_section(f"📰 TASK A - {language.upper()}")
    
    # Determine parallelism
    num_workers = parallel_jobs or config.PARALLEL_JOKES
    num_workers = min(num_workers, MAX_PARALLEL_JOKES)
    
    # Sensitive topics that may trigger LLM censorship (headline task only)
    SENSITIVE_TOPICS = {
        "en": [
            "china", "chinese", "beijing", "xi jinping", "ccp", "prc",
            "taiwan", "hong kong", "tibet", "uyghur", "xinjiang",
            "tiananmen", "dalai lama", "falun gong",
        ],
        "es": [
            "china", "chino", "chinos", "pekín", "beijing", "xi jinping", "pcc",
            "taiwán", "taiwan", "hong kong", "tíbet", "tibet", "uigur", "xinjiang",
            "tiananmen", "dalái lama", "falun gong",
        ],
        "zh": [
            "中国", "中國", "北京", "习近平", "習近平", "共产党", "共產黨",
            "台湾", "台灣", "香港", "西藏", "维吾尔", "維吾爾", "新疆",
            "天安门", "天安門", "达赖喇嘛", "達賴喇嘛", "法轮功", "法輪功",
        ],
    }
    
    def contains_sensitive_topic(text: str, lang: str) -> bool:
        """Check if text contains any sensitive topics for the given language."""
        text_lower = text.lower()
        topics = SENSITIVE_TOPICS.get(lang, SENSITIVE_TOPICS["en"])
        return any(topic.lower() in text_lower for topic in topics)
    
    # Load data
    items = load_task_a(language, test_mode=test_mode)
    
    if not items:
        logger.warning(f"No items found for Task A {language}")
        return {"processed": 0, "errors": 0}
    
    # Check for existing outputs if resuming
    task_name = get_task_file_name("a", language)
    existing = {}
    if resume:
        existing = load_existing_outputs(
            task_name, 
            test_mode=test_mode,
            complete_mode=config.SAVE_COMPLETE_OUTPUT
        )
        items = get_remaining_items(items, existing)
    
    if not items:
        logger.info("All items already processed!")
        return {"processed": 0, "skipped": len(existing), "errors": 0}
    
    # Create thread-safe progress tracker
    tracker = ProgressTracker(len(items), f"Task A {language.upper()}")
    
    # Thread-safe lock for file operations
    file_lock = threading.Lock()
    
    # Initialize pipelines - each worker will create its own
    # but we need signature definitions from one
    headline_pipeline = UnifiedHumorPipeline("a1")
    word_pipeline = UnifiedHumorPipeline("a2")
    
    def process_single_item(item, item_idx: int) -> dict:
        """Process a single item (designed for parallel execution)."""
        result = {"success": False, "type": None, "error": None}
        
        # Check if already processed (thread-safe)
        if tracker.is_processed(item.id):
            logger.debug(f"Skipping {item.id} - already processed")
            return result
        
        try:
            if item.is_headline_task:
                result["type"] = "headline"
                try:
                    joke, all_candidates = headline_pipeline.forward(
                        original_input=item.headline,
                        language=language,
                        skip_judge=config.SAVE_COMPLETE_OUTPUT,
                    )
                except Exception as first_error:
                    if contains_sensitive_topic(item.headline, language):
                        logger.warning(f"⚠️ {item.id}: Sensitive topic detected, likely censorship")
                        with file_lock:
                            save_output(task_name, item.id, "[CENSORED: Sensitive geopolitical topic]", test_mode=test_mode)
                        tracker.mark_processed(item.id)
                        tracker.increment_stat("errors")
                        return result
                    else:
                        raise first_error
                
                with file_lock:
                    save_complete_output(
                        task_name, item.id, joke, all_candidates, test_mode=test_mode,
                        original_input=item.headline, language=language, task_type="a1"
                    )
                
            elif item.is_word_inclusion_task:
                result["type"] = "word_inclusion"
                joke, all_candidates = word_pipeline.forward(
                    original_input=f"{item.word1}, {item.word2}",
                    language=language,
                    word1=item.word1,
                    word2=item.word2,
                    skip_judge=config.SAVE_COMPLETE_OUTPUT,
                )
                
                with file_lock:
                    save_complete_output(
                        task_name, item.id, joke, all_candidates, test_mode=test_mode,
                        original_input=f"{item.word1}, {item.word2}",
                        language=language, word1=item.word1, word2=item.word2, task_type="a2"
                    )
            else:
                logger.warning(f"Item {item.id} has neither headline nor words")
                return result
            
            # Save output
            with file_lock:
                if joke is not None:
                    save_output(task_name, item.id, joke, test_mode=test_mode)
                    logger.info(f"✅ {item.id}: {joke[:80]}...")
                else:
                    logger.info(f"✅ {item.id}: Generated {len(all_candidates)} candidates (no judging)")
            
            # Mark as processed and update stats
            tracker.mark_processed(item.id)
            tracker.increment_stat("processed")
            if result["type"] == "headline":
                tracker.increment_stat("headlines")
            else:
                tracker.increment_stat("word_inclusion")
            
            result["success"] = True
            tracker.log_progress()
            
        except Exception as e:
            result["error"] = str(e)
            log_error(e, f"processing {item.id}")
            tracker.increment_stat("errors")
            tracker.mark_processed(item.id)  # Mark to avoid retry
            with file_lock:
                save_output(task_name, item.id, f"[ERROR: {str(e)[:50]}]", test_mode=test_mode)
        
        return result
    
    # Process items
    if num_workers <= 1:
        # Sequential processing
        logger.info(f"Processing {len(items)} items sequentially...")
        for i, item in enumerate(items):
            try:
                process_single_item(item, i)
            except KeyboardInterrupt:
                logger.warning("Interrupted by user. Progress has been saved.")
                break
    else:
        # Parallel processing
        logger.info(f"Processing {len(items)} items with {num_workers} parallel workers...")
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(process_single_item, item, i): item
                for i, item in enumerate(items)
            }
            
            try:
                for future in as_completed(futures):
                    item = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Unexpected error for {item.id}: {e}")
            except KeyboardInterrupt:
                logger.warning("Interrupted by user. Cancelling pending tasks...")
                executor.shutdown(wait=False, cancel_futures=True)
    
    return tracker.get_stats()


def process_task_b1(
    test_mode: bool = True,
    resume: bool = False,
    parallel_jobs: int = None,
) -> dict:
    """
    Process Task B1 (GIF captions) with optional parallel processing.
    
    Uses preprocessed GIF descriptions from cache or analyzes GIFs
    on-the-fly using Gemini 2.5 Flash Lite.
    
    Args:
        test_mode: If True, process limited samples
        resume: If True, skip already processed items
        parallel_jobs: Number of parallel workers (None = use config.PARALLEL_JOKES)
    
    Returns:
        Statistics dictionary
    """
    log_section("🖼️ TASK B1 - GIF CAPTIONS")
    
    # Determine parallelism
    num_workers = parallel_jobs or config.PARALLEL_JOKES
    num_workers = min(num_workers, MAX_PARALLEL_JOKES)
    
    # Load data
    items = load_task_b1(test_mode=test_mode)
    
    if not items:
        logger.warning("No items found for Task B1")
        return {"processed": 0, "errors": 0}
    
    # Check for existing outputs if resuming
    task_name = "task-b1"
    existing = {}
    if resume:
        existing = load_existing_outputs(
            task_name, 
            test_mode=test_mode,
            complete_mode=config.SAVE_COMPLETE_OUTPUT
        )
        items = get_remaining_items(items, existing)
    
    if not items:
        logger.info("All items already processed!")
        return {"processed": 0, "skipped": len(existing), "errors": 0}
    
    # Create thread-safe progress tracker
    tracker = ProgressTracker(len(items), "Task B1")
    
    # Thread-safe lock for file operations
    file_lock = threading.Lock()
    
    # Initialize pipeline
    pipeline = UnifiedHumorPipeline("b1")
    
    def process_single_item(item, item_idx: int) -> dict:
        """Process a single B1 item (designed for parallel execution)."""
        result = {"success": False, "error": None}
        
        # Check if already processed (thread-safe)
        if tracker.is_processed(item.id):
            logger.debug(f"Skipping {item.id} - already processed")
            return result
        
        try:
            # Use preprocessed description or analyze GIF
            if item.description:
                logger.info(f"📝 [{item.id}] Using preprocessed description")
                gif_description = item.description
            else:
                logger.info(f"🎬 [{item.id}] Analyzing GIF: {item.url[:60]}...")
                gif_description = analyze_gif_for_b1(item.url)
                
                if not gif_description:
                    logger.error(f"❌ Failed to analyze GIF for {item.id}")
                    tracker.increment_stat("gif_analysis_failed")
                    tracker.increment_stat("errors")
                    tracker.mark_processed(item.id)
                    with file_lock:
                        save_output(task_name, item.id, "[ERROR: GIF analysis failed]", test_mode=test_mode)
                    return result
            
            logger.info(f"📝 [{item.id}] GIF description: {gif_description[:100]}...")
            
            # Generate caption using the humor pipeline
            caption, all_candidates = pipeline.forward(
                original_input=gif_description,
                skip_judge=config.SAVE_COMPLETE_OUTPUT,
            )
            
            with file_lock:
                save_complete_output(
                    task_name, item.id, caption, all_candidates, test_mode=test_mode,
                    original_input=gif_description, task_type="b1"
                )
                
                if caption is not None:
                    save_output(task_name, item.id, caption, test_mode=test_mode)
                    logger.info(f"✅ {item.id}: {caption}")
                else:
                    logger.info(f"✅ {item.id}: Generated {len(all_candidates)} candidates (no judging)")
            
            tracker.mark_processed(item.id)
            tracker.increment_stat("processed")
            result["success"] = True
            tracker.log_progress()
            
        except Exception as e:
            result["error"] = str(e)
            log_error(e, f"processing {item.id}")
            tracker.increment_stat("errors")
            tracker.mark_processed(item.id)
            with file_lock:
                save_output(task_name, item.id, f"[ERROR: {str(e)[:50]}]", test_mode=test_mode)
        
        return result
    
    # Process items
    if num_workers <= 1:
        logger.info(f"Processing {len(items)} items sequentially...")
        for i, item in enumerate(items):
            try:
                process_single_item(item, i)
            except KeyboardInterrupt:
                logger.warning("Interrupted by user. Progress has been saved.")
                break
    else:
        logger.info(f"Processing {len(items)} items with {num_workers} parallel workers...")
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(process_single_item, item, i): item
                for i, item in enumerate(items)
            }
            
            try:
                for future in as_completed(futures):
                    item = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Unexpected error for {item.id}: {e}")
            except KeyboardInterrupt:
                logger.warning("Interrupted by user. Cancelling pending tasks...")
                executor.shutdown(wait=False, cancel_futures=True)
    
    return tracker.get_stats()


def process_task_b2(
    test_mode: bool = True,
    resume: bool = False,
    parallel_jobs: int = None,
) -> dict:
    """
    Process Task B2 (GIF + prompt captions) with optional parallel processing.
    
    Uses preprocessed GIF descriptions from cache or analyzes GIFs
    on-the-fly using Gemini 2.5 Flash Lite.
    
    Args:
        test_mode: If True, process limited samples
        resume: If True, skip already processed items
        parallel_jobs: Number of parallel workers (None = use config.PARALLEL_JOKES)
    
    Returns:
        Statistics dictionary
    """
    log_section("🖼️ TASK B2 - GIF + PROMPT CAPTIONS")
    
    # Determine parallelism
    num_workers = parallel_jobs or config.PARALLEL_JOKES
    num_workers = min(num_workers, MAX_PARALLEL_JOKES)
    
    # Load data
    items = load_task_b2(test_mode=test_mode)
    
    if not items:
        logger.warning("No items found for Task B2")
        return {"processed": 0, "errors": 0}
    
    # Check for existing outputs if resuming
    task_name = "task-b2"
    existing = {}
    if resume:
        existing = load_existing_outputs(
            task_name, 
            test_mode=test_mode,
            complete_mode=config.SAVE_COMPLETE_OUTPUT
        )
        items = get_remaining_items(items, existing)
    
    if not items:
        logger.info("All items already processed!")
        return {"processed": 0, "skipped": len(existing), "errors": 0}
    
    # Create thread-safe progress tracker
    tracker = ProgressTracker(len(items), "Task B2")
    
    # Thread-safe lock for file operations
    file_lock = threading.Lock()
    
    # Initialize pipeline
    pipeline = UnifiedHumorPipeline("b2")
    
    def process_single_item(item, item_idx: int) -> dict:
        """Process a single B2 item (designed for parallel execution)."""
        result = {"success": False, "error": None}
        
        # Check if already processed (thread-safe)
        if tracker.is_processed(item.id):
            logger.debug(f"Skipping {item.id} - already processed")
            return result
        
        try:
            # Use preprocessed description or analyze GIF
            logger.info(f"📝 [{item.id}] Prompt: {item.prompt}")
            
            if item.description:
                logger.info(f"📝 [{item.id}] Using preprocessed description")
                gif_description = item.description
            else:
                logger.info(f"🎬 [{item.id}] Analyzing GIF: {item.url[:60]}...")
                gif_description = analyze_gif_for_b2(item.url, item.prompt)
                
                if not gif_description:
                    logger.error(f"❌ Failed to analyze GIF for {item.id}")
                    tracker.increment_stat("gif_analysis_failed")
                    tracker.increment_stat("errors")
                    tracker.mark_processed(item.id)
                    with file_lock:
                        save_output(task_name, item.id, "[ERROR: GIF analysis failed]", test_mode=test_mode)
                    return result
            
            logger.info(f"📝 [{item.id}] GIF description: {gif_description[:100]}...")
            
            # Generate caption using the humor pipeline
            # IMPORTANT: Include both the prompt AND the description for Task B2
            pipeline_input = f"GIF Description: {gif_description}\n\nPrompt to Complete: {item.prompt}"
            caption, all_candidates = pipeline.forward(
                original_input=pipeline_input,
                skip_judge=config.SAVE_COMPLETE_OUTPUT,
            )
            
            with file_lock:
                save_complete_output(
                    task_name, item.id, caption, all_candidates, test_mode=test_mode,
                    original_input=pipeline_input, task_type="b2"
                )
                
                if caption is not None:
                    save_output(task_name, item.id, caption, test_mode=test_mode)
                    logger.info(f"✅ {item.id}: {caption}")
                else:
                    logger.info(f"✅ {item.id}: Generated {len(all_candidates)} candidates (no judging)")
            
            tracker.mark_processed(item.id)
            tracker.increment_stat("processed")
            result["success"] = True
            tracker.log_progress()
            
        except Exception as e:
            result["error"] = str(e)
            log_error(e, f"processing {item.id}")
            tracker.increment_stat("errors")
            tracker.mark_processed(item.id)
            with file_lock:
                save_output(task_name, item.id, f"[ERROR: {str(e)[:50]}]", test_mode=test_mode)
        
        return result
    
    # Process items
    if num_workers <= 1:
        logger.info(f"Processing {len(items)} items sequentially...")
        for i, item in enumerate(items):
            try:
                process_single_item(item, i)
            except KeyboardInterrupt:
                logger.warning("Interrupted by user. Progress has been saved.")
                break
    else:
        logger.info(f"Processing {len(items)} items with {num_workers} parallel workers...")
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(process_single_item, item, i): item
                for i, item in enumerate(items)
            }
            
            try:
                for future in as_completed(futures):
                    item = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Unexpected error for {item.id}: {e}")
            except KeyboardInterrupt:
                logger.warning("Interrupted by user. Cancelling pending tasks...")
                executor.shutdown(wait=False, cancel_futures=True)
    
    return tracker.get_stats()


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="MWAHAHA Humor Generation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--task",
        choices=["a-en", "a-es", "a-zh", "b1", "b2", "all"],
        default="all",
        help="Task to run (default: all)"
    )
    
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run in full mode (process all samples)"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing outputs (only in full mode)"
    )
    
    parser.add_argument(
        "--complete",
        action="store_true",
        help="Save complete output (all candidates + LLM outputs as JSON)"
    )
    
    parser.add_argument(
        "--provider",
        choices=["gemini", "openrouter"],
        default=None,
        help="API provider to use (overrides DEFAULT_MODEL in config.py)"
    )
    
    parser.add_argument(
        "--default-provider",
        choices=["gemini", "openrouter"],
        default=None,
        help="Set default provider for models without explicit provider prefix"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        type=int,
        default=None,
        metavar="N",
        help=f"Number of jokes to process in parallel (default: {PARALLEL_JOKES}, max: {MAX_PARALLEL_JOKES})"
    )
    
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Judge-only mode: load candidates from complete/full, validate, judge, and output winners"
    )
    
    args = parser.parse_args()
    
    # If --judge flag is set, run judge mode and exit
    if args.judge:
        # Setup logging for judge mode
        LOG_DIR.mkdir(exist_ok=True)
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = add_file_handler_to_logger(f"judge_{run_id}.log")
        logger.info(f"📁 Log file: {log_file_path}")
        
        run_judge_mode(args)
        sys.exit(0)
    
    # Setup
    test_mode = not args.full
    mode_str = "FULL" if args.full else "TEST"
    
    # Apply default provider override if specified
    if args.default_provider:
        config.API_PROVIDER = args.default_provider
        logger.info(f"🔧 Default provider override: {args.default_provider}")
    
    # Determine parallelism
    parallel_jobs = args.parallel
    if parallel_jobs is not None:
        if parallel_jobs < 1:
            logger.error("❌ --parallel must be at least 1")
            sys.exit(1)
        if parallel_jobs > MAX_PARALLEL_JOKES:
            logger.warning(f"⚠️ --parallel {parallel_jobs} exceeds max ({MAX_PARALLEL_JOKES}), using {MAX_PARALLEL_JOKES}")
            parallel_jobs = MAX_PARALLEL_JOKES
        config.PARALLEL_JOKES = parallel_jobs
    
    # Enable complete output if requested
    if args.complete:
        config.SAVE_COMPLETE_OUTPUT = True
        logger.info("📋 Complete output mode enabled (all candidates + LLM outputs)")
    
    # Create output directories
    output_dir = OUTPUT_DIR if args.full else TEST_OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    
    # Create complete output directory if needed
    if config.SAVE_COMPLETE_OUTPUT:
        from config import COMPLETE_OUTPUT_DIR
        complete_dir = COMPLETE_OUTPUT_DIR / ("full" if args.full else "test")
        complete_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Complete output directory: {complete_dir}")
    
    # Create run-specific logger that writes to file
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = add_file_handler_to_logger(f"run_{run_id}.log")
    
    log_section(f"🎭 MWAHAHA PIPELINE - {mode_str} MODE")
    logger.info(f"Task: {args.task}")
    logger.info(f"Provider: {args.provider}")
    logger.info(f"Resume: {args.resume}")
    logger.info(f"Parallel jobs: {config.PARALLEL_JOKES}")
    logger.info(f"📁 Log file: {log_file_path}")
    
    # Check for paid OpenRouter model and warn user
    # Note: Provider is determined from DEFAULT_MODEL in config, --provider is a fallback
    model_name = get_openrouter_model_name()
    if "openrouter" in model_name or args.provider == "openrouter":
        if not is_openrouter_model_free(model_name):
            logger.warning(f"⚠️  WARNING: OpenRouter model '{model_name}' is NOT a free model!")
            logger.warning(f"⚠️  This will incur API costs. Free models must end with ':free'")
            logger.warning(f"⚠️  Example free model: meta-llama/llama-3.3-70b-instruct:free")
            print()
            confirm = input("Do you want to proceed with this PAID model? (yes/no): ").strip().lower()
            if confirm != "yes":
                logger.info("Aborted by user. Please update DEFAULT_MODEL in config.py to use a free model.")
                sys.exit(0)
            logger.info("User confirmed paid model usage. Proceeding...")
        else:
            logger.info(f"✅ Using free OpenRouter model: {model_name}")
    
    # Configure API
    try:
        print(f"\n🔍 DEBUG: args.provider = {args.provider}")
        print(f"🔍 DEBUG: config.DEFAULT_MODEL = {config.DEFAULT_MODEL}")
        print(f"🔍 DEBUG: config.API_PROVIDER = {config.API_PROVIDER}\n")
        
        lm = configure_dspy(provider_name=args.provider)
        # Determine actual provider used
        if args.provider:
            provider_used = args.provider
        else:
            from config import parse_model_spec
            provider_used, _ = parse_model_spec(config.DEFAULT_MODEL)
            provider_used = provider_used or config.API_PROVIDER
        print(f"✅ API configured: {provider_used}\n")
        logger.info(f"✅ API configured: {provider_used}")
    except Exception as e:
        logger.error(f"❌ Failed to configure API: {e}")
        logger.error("Make sure API keys are set in .env file")
        sys.exit(1)
    
    # Reset all trackers (tokens and retries)
    reset_all_trackers()
    
    # Track overall stats
    all_stats = {}
    start_time = datetime.now()
    
    try:
        # Run selected tasks
        if args.task in ("a-en", "all"):
            all_stats["a-en"] = process_task_a("en", test_mode, args.resume, parallel_jobs)
        
        if args.task in ("a-es", "all"):
            all_stats["a-es"] = process_task_a("es", test_mode, args.resume, parallel_jobs)
        
        if args.task in ("a-zh", "all"):
            all_stats["a-zh"] = process_task_a("zh", test_mode, args.resume, parallel_jobs)
        
        if args.task in ("b1", "all"):
            all_stats["b1"] = process_task_b1(test_mode, args.resume, parallel_jobs)
        
        if args.task in ("b2", "all"):
            all_stats["b2"] = process_task_b2(test_mode, args.resume, parallel_jobs)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Pipeline interrupted. Partial results have been saved.")
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    token_summary = get_token_summary()
    retry_summary = get_retry_summary()
    
    log_summary({
        "Duration": str(duration),
        "Mode": mode_str,
        "Output Directory": str(output_dir),
        "Total Input Tokens": token_summary["total_input_tokens"],
        "Total Output Tokens": token_summary["total_output_tokens"],
        "Total API Calls": token_summary["total_api_calls"],
        "Total Retries": retry_summary["total_retries"],
        **{f"{task} processed": stats.get("processed", 0) for task, stats in all_stats.items()},
        **{f"{task} errors": stats.get("errors", 0) for task, stats in all_stats.items()},
    })
    
    # Log retry breakdown if there were any retries
    if retry_summary["total_retries"] > 0:
        logger.info("\n📊 Retry Breakdown by Module:")
        for module, counts in sorted(retry_summary["by_module"].items()):
            total = counts["rate_limit"] + counts["transient"]
            details = []
            if counts["rate_limit"] > 0:
                details.append(f"{counts['rate_limit']} rate limit")
            if counts["transient"] > 0:
                details.append(f"{counts['transient']} transient")
            logger.info(f"   {module}: {total} ({', '.join(details)})")
    
    logger.info(f"\n✨ Pipeline complete! Outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
