#!/usr/bin/env python3
"""
Validate and fix judged output TSV files for MWAHAHA submission.

Features:
1. Sorts IDs in correct order
2. Identifies missing IDs
3. Reports TSV format errors
4. Generates validation report

Usage:
    python validate_outputs.py [--fix]
    
    --fix: Also create fixed (sorted) versions of the TSV files
"""

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass


# Configuration
BASE_DIR = Path(__file__).parent
JUDGED_OUTPUT_DIR = BASE_DIR / "judged_outputs"
INPUT_DIR = BASE_DIR / "Input"

# Task configurations with expected ID patterns and counts
# Note: ID ranges are dynamically read from input files
TASK_CONFIG = {
    "task-a-en": {
        "id_pattern": r"^en_(\d+)$",
        "id_prefix": "en_",
        "max_chars": 900,
        "max_words": None,  # No word limit for Task A
    },
    "task-a-es": {
        "id_pattern": r"^es_(\d+)$",
        "id_prefix": "es_",
        "max_chars": 900,
        "max_words": None,
    },
    "task-a-zh": {
        "id_pattern": r"^zh_(\d+)$",
        "id_prefix": "zh_",
        "max_chars": 300,
        "max_words": None,
    },
    "task-b1": {
        "id_pattern": r"^img_(\d+)$",
        "id_prefix": "img_",
        "max_chars": 900,
        "max_words": 20,  # Task B: max 20 words
    },
    "task-b2": {
        "id_pattern": r"^img_2_(\d+)$",
        "id_prefix": "img_2_",
        "max_chars": 900,
        "max_words": 20,  # Task B: max 20 words
    },
}


@dataclass
class ValidationError:
    """Represents a TSV validation error."""
    line_number: int
    error_type: str
    message: str
    raw_line: Optional[str] = None


@dataclass
class ValidationResult:
    """Holds validation results for a single file."""
    file_path: Path
    task_name: str
    total_rows: int
    valid_rows: int
    errors: List[ValidationError]
    missing_ids: Set[str]
    duplicate_ids: Dict[str, List[int]]
    out_of_order_count: int
    oversized_texts: List[Tuple[str, int]]  # (id, char_count)
    overword_texts: List[Tuple[str, int, str]]   # (id, word_count, text) - texts exceeding word limit
    expected_count: int = 0
    order_mismatches: List[Tuple[int, str, str]] = None  # (line_num, expected_id, actual_id)
    

def get_expected_ids_from_input(task_name: str) -> Set[str]:
    """Load expected IDs from the corresponding input file."""
    input_file = INPUT_DIR / f"{task_name}.tsv"
    expected_ids = set()
    
    if not input_file.exists():
        print(f"  ⚠️  Input file not found: {input_file}")
        return expected_ids
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader, None)  # Skip header
        for row in reader:
            if row:
                expected_ids.add(row[0])
    
    return expected_ids


def get_expected_id_order(task_name: str) -> List[str]:
    """Load expected IDs in exact order from the input file."""
    input_file = INPUT_DIR / f"{task_name}.tsv"
    ordered_ids = []
    
    if not input_file.exists():
        return ordered_ids
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader, None)  # Skip header
        for row in reader:
            if row:
                ordered_ids.append(row[0])
    
    return ordered_ids


def extract_id_number(id_str: str, task_name: str) -> Optional[int]:
    """Extract numeric part from ID string for sorting."""
    config = TASK_CONFIG.get(task_name)
    if not config:
        return None
    
    match = re.match(config["id_pattern"], id_str)
    if match:
        return int(match.group(1))
    return None


def validate_tsv_file(file_path: Path, task_name: str) -> ValidationResult:
    """Validate a single TSV output file."""
    config = TASK_CONFIG.get(task_name)
    errors: List[ValidationError] = []
    seen_ids: Dict[str, List[int]] = {}  # id -> list of line numbers
    valid_entries: List[Tuple[str, str, int]] = []  # (id, text, line_number)
    oversized: List[Tuple[str, int]] = []
    overword: List[Tuple[str, int, str]] = []  # (id, word_count, text) - texts exceeding word limit
    
    # Get expected IDs from input file (source of truth)
    expected_ids = get_expected_ids_from_input(task_name)
    expected_id_order = get_expected_id_order(task_name)  # Exact order from input
    expected_count = len(expected_ids)
    
    if not file_path.exists():
        return ValidationResult(
            file_path=file_path,
            task_name=task_name,
            total_rows=0,
            valid_rows=0,
            errors=[ValidationError(0, "FILE_NOT_FOUND", f"File does not exist: {file_path}")],
            missing_ids=expected_ids,
            duplicate_ids={},
            out_of_order_count=0,
            oversized_texts=[],
            overword_texts=[],
            expected_count=expected_count,
            order_mismatches=[],
        )
    
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        line_num = 0
        has_header = False
        
        for line in f:
            line_num += 1
            raw_line = line.rstrip('\n\r')
            
            # Check for header
            if line_num == 1 and raw_line.startswith("id\t"):
                has_header = True
                continue
            
            # Empty line check
            if not raw_line.strip():
                errors.append(ValidationError(line_num, "EMPTY_LINE", "Empty line found", raw_line))
                continue
            
            # Split by tab
            parts = raw_line.split('\t')
            
            # Check column count
            if len(parts) < 2:
                errors.append(ValidationError(
                    line_num, "MISSING_COLUMNS", 
                    f"Expected 2 columns (id, text), found {len(parts)}", 
                    raw_line[:100] + "..." if len(raw_line) > 100 else raw_line
                ))
                continue
            
            if len(parts) > 2:
                errors.append(ValidationError(
                    line_num, "EXTRA_COLUMNS",
                    f"Expected 2 columns, found {len(parts)} (text may contain unescaped tabs)",
                    raw_line[:100] + "..." if len(raw_line) > 100 else raw_line
                ))
            
            item_id = parts[0].strip()
            text = parts[1].strip() if len(parts) > 1 else ""
            
            # Validate ID format
            if config:
                match = re.match(config["id_pattern"], item_id)
                if not match:
                    errors.append(ValidationError(
                        line_num, "INVALID_ID_FORMAT",
                        f"ID '{item_id}' doesn't match expected pattern {config['id_pattern']}",
                        raw_line[:80]
                    ))
                    continue
                
                # Check if ID is in expected set (from input file)
                if expected_ids and item_id not in expected_ids:
                    errors.append(ValidationError(
                        line_num, "UNEXPECTED_ID",
                        f"ID '{item_id}' not found in input file",
                        None
                    ))
            
            # Check for empty text
            if not text:
                errors.append(ValidationError(
                    line_num, "EMPTY_TEXT",
                    f"Empty text for ID '{item_id}'",
                    None
                ))
            
            # Check text length (characters)
            if config and len(text) > config["max_chars"]:
                oversized.append((item_id, len(text)))
                errors.append(ValidationError(
                    line_num, "TEXT_TOO_LONG",
                    f"Text for '{item_id}' is {len(text)} chars (max {config['max_chars']})",
                    None
                ))
            
            # Check word count (for Task B: max 20 words)
            if config and config.get("max_words"):
                word_count = len(text.split())
                if word_count > config["max_words"]:
                    overword.append((item_id, word_count, text))  # Store full text
                    errors.append(ValidationError(
                        line_num, "TEXT_TOO_MANY_WORDS",
                        f"Text for '{item_id}' is {word_count} words (max {config['max_words']})",
                        None
                    ))
            
            # Track seen IDs for duplicate detection
            if item_id in seen_ids:
                seen_ids[item_id].append(line_num)
            else:
                seen_ids[item_id] = [line_num]
            
            valid_entries.append((item_id, text, line_num))
    
    # Find duplicates
    duplicates = {id_: lines for id_, lines in seen_ids.items() if len(lines) > 1}
    for dup_id, lines in duplicates.items():
        errors.append(ValidationError(
            lines[0], "DUPLICATE_ID",
            f"ID '{dup_id}' appears {len(lines)} times at lines: {lines}",
            None
        ))
    
    # Check ordering against input file order (exact match required)
    out_of_order = 0
    order_mismatches: List[Tuple[int, str, str]] = []
    
    # Build list of output IDs in order
    output_ids_in_order = [item_id for item_id, _, _ in valid_entries]
    
    # Compare against expected order from input file
    for idx, (actual_id, expected_id) in enumerate(zip(output_ids_in_order, expected_id_order)):
        if actual_id != expected_id:
            out_of_order += 1
            if len(order_mismatches) < 10:  # Store first 10 mismatches for display
                order_mismatches.append((idx + 2, expected_id, actual_id))  # +2 for 1-based + header
    
    # Find missing ones (expected_ids already loaded at start)
    found_ids = set(seen_ids.keys())
    missing_ids = expected_ids - found_ids
    
    return ValidationResult(
        file_path=file_path,
        task_name=task_name,
        total_rows=len(valid_entries) + len([e for e in errors if "MISSING_COLUMNS" in e.error_type]),
        valid_rows=len(valid_entries),
        errors=errors,
        missing_ids=missing_ids,
        duplicate_ids=duplicates,
        out_of_order_count=out_of_order,
        oversized_texts=oversized,
        overword_texts=overword,
        expected_count=expected_count,
        order_mismatches=order_mismatches,
    )


def fix_and_sort_tsv(file_path: Path, task_name: str, output_path: Optional[Path] = None) -> Path:
    """Sort a TSV file by ID and write to output path."""
    config = TASK_CONFIG.get(task_name)
    entries: Dict[str, str] = {}  # id -> text (keeps last if duplicate)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader, None)
        
        # Check if first row is header
        if header and header[0] != "id":
            # First row is data, not header
            if len(header) >= 2:
                entries[header[0]] = header[1]
        
        for row in reader:
            if len(row) >= 2:
                item_id = row[0].strip()
                text = row[1].strip()
                if item_id and text:
                    entries[item_id] = text
    
    # Sort by input file order (exact match)
    expected_order = get_expected_id_order(task_name)
    
    # Use input file order, only include IDs that exist in our entries
    sorted_ids = [id_ for id_ in expected_order if id_ in entries]
    
    # Add any extra IDs not in input (shouldn't happen, but be safe)
    extra_ids = set(entries.keys()) - set(expected_order)
    if extra_ids:
        sorted_ids.extend(sorted(extra_ids))
    
    # Write sorted output
    if output_path is None:
        output_path = file_path.with_suffix('.sorted.tsv')
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerow(['id', 'text'])
        for item_id in sorted_ids:
            writer.writerow([item_id, entries[item_id]])
    
    return output_path


def print_report(result: ValidationResult) -> None:
    """Print a detailed validation report."""
    print(f"\n{'='*60}")
    print(f"📄 {result.task_name.upper()}")
    print(f"   File: {result.file_path}")
    print(f"{'='*60}")
    
    if not result.file_path.exists():
        print("   ❌ FILE NOT FOUND")
        print(f"   Expected {result.expected_count} IDs")
        return
    
    config = TASK_CONFIG.get(result.task_name, {})
    expected = result.expected_count
    
    # Summary stats
    print(f"\n📊 SUMMARY:")
    print(f"   Total rows:     {result.total_rows}")
    print(f"   Valid rows:     {result.valid_rows}")
    print(f"   Expected rows:  {expected}")
    print(f"   Out of order:   {result.out_of_order_count}")
    
    # Status indicators
    is_complete = len(result.missing_ids) == 0
    is_ordered = result.out_of_order_count == 0
    has_errors = len(result.errors) > 0
    
    print(f"\n✅ STATUS:")
    print(f"   Complete:   {'✅ Yes' if is_complete else '❌ No'}")
    print(f"   Sorted:     {'✅ Yes (matches input order)' if is_ordered else '❌ No (order mismatch with input)'}")
    print(f"   Error-free: {'✅ Yes' if not has_errors else '❌ No'}")
    
    # Order mismatches
    if result.order_mismatches:
        print(f"\n🔀 ORDER MISMATCHES (first {len(result.order_mismatches)} shown):")
        for line_num, expected_id, actual_id in result.order_mismatches:
            print(f"   Line {line_num}: expected '{expected_id}', got '{actual_id}'")
        if result.out_of_order_count > len(result.order_mismatches):
            print(f"   ... and {result.out_of_order_count - len(result.order_mismatches)} more mismatches")
    
    # Missing IDs
    if result.missing_ids:
        print(f"\n❌ MISSING IDs ({len(result.missing_ids)}):")
        sorted_missing = sorted(result.missing_ids, 
                               key=lambda x: extract_id_number(x, result.task_name) or 999999)
        # Group consecutive IDs
        if len(sorted_missing) <= 20:
            for mid in sorted_missing:
                print(f"   - {mid}")
        else:
            print(f"   First 10: {sorted_missing[:10]}")
            print(f"   Last 10:  {sorted_missing[-10:]}")
    
    # Duplicate IDs
    if result.duplicate_ids:
        print(f"\n⚠️  DUPLICATE IDs ({len(result.duplicate_ids)}):")
        for dup_id, lines in list(result.duplicate_ids.items())[:10]:
            print(f"   - {dup_id}: lines {lines}")
        if len(result.duplicate_ids) > 10:
            print(f"   ... and {len(result.duplicate_ids) - 10} more")
    
    # Oversized texts (character limit)
    if result.oversized_texts:
        print(f"\n📏 OVERSIZED TEXTS ({len(result.oversized_texts)}):")
        max_chars = config.get("max_chars", 900)
        for item_id, char_count in result.oversized_texts[:10]:
            print(f"   - {item_id}: {char_count} chars (max {max_chars})")
        if len(result.oversized_texts) > 10:
            print(f"   ... and {len(result.oversized_texts) - 10} more")
    
    # Overword texts (word limit - Task B only) - show ALL with full text
    if result.overword_texts:
        print(f"\n📝 TOO MANY WORDS ({len(result.overword_texts)}):")
        max_words = config.get("max_words", 20)
        for item_id, word_count, text in result.overword_texts:
            print(f"\n   [{item_id}] {word_count} words (max {max_words}):")
            print(f"   \"{text}\"")
    
    # Other errors
    other_errors = [e for e in result.errors 
                    if e.error_type not in ("DUPLICATE_ID", "TEXT_TOO_LONG", "TEXT_TOO_MANY_WORDS")]
    if other_errors:
        print(f"\n🚨 TSV ERRORS ({len(other_errors)}):")
        for error in other_errors[:15]:
            print(f"   Line {error.line_number}: [{error.error_type}] {error.message}")
            if error.raw_line:
                print(f"      Raw: {error.raw_line[:60]}...")
        if len(other_errors) > 15:
            print(f"   ... and {len(other_errors) - 15} more errors")


def main():
    parser = argparse.ArgumentParser(description="Validate and fix judged output TSV files")
    parser.add_argument("--fix", action="store_true", 
                        help="Create sorted versions of TSV files")
    parser.add_argument("--task", type=str, 
                        help="Validate only specific task (e.g., 'a-en', 'b1')")
    parser.add_argument("--mode", type=str, choices=["test", "full"], default="full",
                        help="Which output folder to validate (default: full)")
    args = parser.parse_args()
    
    output_dir = JUDGED_OUTPUT_DIR / args.mode
    
    print(f"\n🔍 VALIDATING JUDGED OUTPUTS")
    print(f"   Directory: {output_dir}")
    print(f"   Mode: {args.mode}")
    
    if not output_dir.exists():
        print(f"\n❌ Output directory not found: {output_dir}")
        return 1
    
    # Determine which tasks to validate
    if args.task:
        task_name = f"task-{args.task}" if not args.task.startswith("task-") else args.task
        tasks = [task_name]
    else:
        tasks = list(TASK_CONFIG.keys())
    
    results: List[ValidationResult] = []
    
    for task_name in tasks:
        file_path = output_dir / f"{task_name}.tsv"
        result = validate_tsv_file(file_path, task_name)
        results.append(result)
        print_report(result)
        
        # Fix/sort if requested
        if args.fix and file_path.exists() and result.out_of_order_count > 0:
            sorted_path = file_path  # Overwrite original
            print(f"\n   🔧 Fixing: Sorting {task_name}...")
            fix_and_sort_tsv(file_path, task_name, sorted_path)
            print(f"   ✅ Sorted and saved to: {sorted_path}")
    
    # Final summary
    print(f"\n{'='*60}")
    print("📋 FINAL SUMMARY")
    print(f"{'='*60}")
    
    total_missing = sum(len(r.missing_ids) for r in results)
    total_errors = sum(len(r.errors) for r in results)
    total_unordered = sum(1 for r in results if r.out_of_order_count > 0)
    
    for result in results:
        if not result.file_path.exists():
            status = "❌ NOT FOUND"
        elif len(result.missing_ids) > 0:
            status = f"⚠️  INCOMPLETE ({len(result.missing_ids)} missing)"
        elif result.out_of_order_count > 0:
            status = f"⚠️  JUMBLED"
        elif len(result.errors) > 0:
            status = f"⚠️  {len(result.errors)} errors"
        else:
            status = "✅ READY"
        print(f"   {result.task_name}: {status}")
    
    print(f"\n   Total missing IDs: {total_missing}")
    print(f"   Total errors: {total_errors}")
    print(f"   Files needing sort: {total_unordered}")
    
    if args.fix:
        print(f"\n   ℹ️  Files have been sorted in place.")
    elif total_unordered > 0:
        print(f"\n   💡 Run with --fix to sort files in place")
    
    return 0 if total_missing == 0 and total_errors == 0 else 1


if __name__ == "__main__":
    exit(main())
