#!/usr/bin/env python3
"""
MWAHAHA Judge Script - Judges candidates from complete output files.

This script loads unjudged candidates from the 'complete' directory and
runs the HumorJudge module to select winners.

Usage:
    python judge.py                          # Judge all unjudged items in complete/test
    python judge.py --full                   # Judge items in complete/full
    python judge.py --task task-a-en         # Judge specific task file
    python judge.py --output results.tsv     # Custom output file name

Input:
    Reads from complete/{test,full}/{task_name}_llm_outputs.jsonl
    Only processes items where "judged" = false

Output:
    1. Prints winners to console
    2. Saves to complete/{test,full}/{task_name}_judged.tsv
    3. Updates the JSONL with winner info (optional with --update-jsonl)
"""

import argparse
import json
import csv
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    COMPLETE_OUTPUT_DIR,
    DEFAULT_MODEL,
    LOG_DIR,
)
from api import configure_dspy, get_token_summary, reset_all_trackers
from pipeline import UnifiedHumorPipeline
from logger import (
    logger,
    log_section,
    log_subsection,
    add_file_handler_to_logger,
)


def load_unjudged_items(task_name: str, test_mode: bool = True) -> list[dict]:
    """
    Load items that haven't been judged yet from the JSONL file.
    
    Args:
        task_name: Name of the task (e.g., "task-a-en")
        test_mode: Whether to use test or full directory
    
    Returns:
        List of item records that need judging
    """
    input_dir = COMPLETE_OUTPUT_DIR / ("test" if test_mode else "full")
    jsonl_path = input_dir / f"{task_name}_llm_outputs.jsonl"
    
    if not jsonl_path.exists():
        logger.warning(f"No JSONL file found: {jsonl_path}")
        return []
    
    items = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                # Only load unjudged items
                if not record.get('judged', False):
                    items.append(record)
    
    logger.info(f"Loaded {len(items)} unjudged items from {jsonl_path.name}")
    return items


def load_all_items(task_name: str, test_mode: bool = True) -> list[dict]:
    """
    Load all items from the JSONL file (for re-judging).
    
    Args:
        task_name: Name of the task (e.g., "task-a-en")
        test_mode: Whether to use test or full directory
    
    Returns:
        List of all item records
    """
    input_dir = COMPLETE_OUTPUT_DIR / ("test" if test_mode else "full")
    jsonl_path = input_dir / f"{task_name}_llm_outputs.jsonl"
    
    if not jsonl_path.exists():
        logger.warning(f"No JSONL file found: {jsonl_path}")
        return []
    
    items = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    
    logger.info(f"Loaded {len(items)} total items from {jsonl_path.name}")
    return items


def judge_item(pipeline: UnifiedHumorPipeline, item: dict) -> tuple[str, int]:
    """
    Judge candidates for a single item and return the winner.
    
    Args:
        pipeline: The UnifiedHumorPipeline instance with judge
        item: Item record from JSONL
    
    Returns:
        Tuple of (winning_joke, winning_candidate_num)
    """
    # Extract candidates
    candidates = [c['joke'] for c in item['candidates']]
    original_input = item['original_input']
    language = item.get('language', 'en')
    
    log_subsection(f"⚖️ Judging {item['id']} ({len(candidates)} candidates)")
    
    # Use the pipeline's judge
    winner = pipeline.judge_candidates(candidates, original_input, language)
    
    # Find which candidate number won
    winner_num = None
    for c in item['candidates']:
        if c['joke'] == winner:
            winner_num = c['candidate_num']
            break
    
    logger.info(f"🏆 Winner: Candidate {winner_num}")
    logger.info(f"   {winner[:100]}...")
    
    return winner, winner_num


def save_judged_results(
    task_name: str,
    results: list[tuple[str, str, int]],  # (id, winner_joke, winner_num)
    test_mode: bool = True,
):
    """
    Save judged results to TSV file.
    
    Args:
        task_name: Name of the task
        results: List of (id, winner_joke, winner_candidate_num) tuples
        test_mode: Whether to use test or full directory
    """
    output_dir = COMPLETE_OUTPUT_DIR / ("test" if test_mode else "full")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tsv_path = output_dir / f"{task_name}_judged.tsv"
    
    with open(tsv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['id', 'winner_candidate', 'text'])
        
        for item_id, winner_joke, winner_num in results:
            writer.writerow([item_id, winner_num, winner_joke])
    
    logger.info(f"💾 Saved {len(results)} judged results to {tsv_path}")
    return tsv_path


def get_available_tasks(test_mode: bool = True) -> list[str]:
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


def main():
    parser = argparse.ArgumentParser(
        description="Judge candidates from complete output files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--task",
        help="Specific task to judge (e.g., 'task-a-en'). If not specified, judges all tasks."
    )
    
    parser.add_argument(
        "--full",
        action="store_true",
        help="Use complete/full directory instead of complete/test"
    )
    
    parser.add_argument(
        "--rejudge",
        action="store_true",
        help="Re-judge all items, even those already judged"
    )
    
    parser.add_argument(
        "--provider",
        choices=["gemini", "openrouter"],
        default="openrouter",
        help="API provider to use for judging (default: openrouter)"
    )
    
    args = parser.parse_args()
    
    test_mode = not args.full
    mode_str = "FULL" if args.full else "TEST"
    
    # Setup logging
    LOG_DIR.mkdir(exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = add_file_handler_to_logger(f"judge_{run_id}.log")
    
    log_section(f"⚖️ MWAHAHA JUDGE - {mode_str} MODE")
    logger.info(f"📁 Log file: {log_file_path}")
    
    # Get tasks to process
    if args.task:
        tasks = [args.task]
    else:
        tasks = get_available_tasks(test_mode)
        if not tasks:
            logger.error(f"No task files found in {COMPLETE_OUTPUT_DIR / ('test' if test_mode else 'full')}")
            sys.exit(1)
    
    logger.info(f"Tasks to judge: {', '.join(tasks)}")
    
    # Configure API
    try:
        configure_dspy(provider_name=args.provider)
        logger.info(f"✅ API configured: {args.provider}")
    except Exception as e:
        logger.error(f"❌ Failed to configure API: {e}")
        sys.exit(1)
    
    reset_all_trackers()
    
    # Process each task
    all_results = {}
    
    for task_name in tasks:
        log_section(f"📋 Processing {task_name}")
        
        # Initialize results list at the start of each task
        results = []
        
        # Determine task type from task name
        if "task-a" in task_name:
            # Need to check if it's a1 or a2 - load first item to check
            items = load_all_items(task_name, test_mode) if args.rejudge else load_unjudged_items(task_name, test_mode)
            
            if not items:
                logger.info(f"No items to judge for {task_name}")
                continue
            
            # Group by task type
            a1_items = [i for i in items if i.get('task_type') == 'a1']
            a2_items = [i for i in items if i.get('task_type') == 'a2']
            
            if a1_items:
                pipeline = UnifiedHumorPipeline("a1")
                for item in a1_items:
                    try:
                        winner, winner_num = judge_item(pipeline, item)
                        results.append((item['id'], winner, winner_num))
                    except Exception as e:
                        logger.error(f"❌ Failed to judge {item['id']}: {e}")
            
            if a2_items:
                pipeline = UnifiedHumorPipeline("a2")
                for item in a2_items:
                    try:
                        winner, winner_num = judge_item(pipeline, item)
                        results.append((item['id'], winner, winner_num))
                    except Exception as e:
                        logger.error(f"❌ Failed to judge {item['id']}: {e}")
            
        elif "task-b1" in task_name:
            items = load_all_items(task_name, test_mode) if args.rejudge else load_unjudged_items(task_name, test_mode)
            
            if not items:
                logger.info(f"No items to judge for {task_name}")
                continue
            
            pipeline = UnifiedHumorPipeline("b1")
            
            for item in items:
                try:
                    winner, winner_num = judge_item(pipeline, item)
                    results.append((item['id'], winner, winner_num))
                except Exception as e:
                    logger.error(f"❌ Failed to judge {item['id']}: {e}")
        
        elif "task-b2" in task_name:
            items = load_all_items(task_name, test_mode) if args.rejudge else load_unjudged_items(task_name, test_mode)
            
            if not items:
                logger.info(f"No items to judge for {task_name}")
                continue
            
            pipeline = UnifiedHumorPipeline("b2")
            
            for item in items:
                try:
                    winner, winner_num = judge_item(pipeline, item)
                    results.append((item['id'], winner, winner_num))
                except Exception as e:
                    logger.error(f"❌ Failed to judge {item['id']}: {e}")
        else:
            logger.warning(f"Unknown task type: {task_name}")
            continue
        
        # Save results
        if results:
            output_path = save_judged_results(task_name, results, test_mode)
            all_results[task_name] = {
                "judged": len(results),
                "output_file": str(output_path),
            }
    
    # Summary
    log_section("📊 JUDGING SUMMARY")
    
    total_judged = 0
    for task_name, stats in all_results.items():
        logger.info(f"  {task_name}: {stats['judged']} items judged")
        logger.info(f"    → {stats['output_file']}")
        total_judged += stats['judged']
    
    logger.info(f"\n✨ Total: {total_judged} items judged")
    
    # Token usage
    token_summary = get_token_summary()
    logger.info(f"\n📈 Token Usage:")
    logger.info(f"  API Calls: {token_summary['total_api_calls']}")
    logger.info(f"  Input: {token_summary['total_input_tokens']:,}")
    logger.info(f"  Output: {token_summary['total_output_tokens']:,}")
    logger.info(f"  Total: {token_summary['total_tokens']:,}")


if __name__ == "__main__":
    main()
