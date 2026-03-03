#!/usr/bin/env python3
"""
analyze_results.py — Post-hoc analysis of pipeline outputs.

Produces two reports:
  1. Logical Mechanism Distribution  (from JSONL intermediate outputs)
  2. Judge Positional Bias           (from judged TSVs matched to candidate TSVs)

Usage:
    python analyze_results.py
"""

import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent
JSONL_DIR = ROOT / "complete" / "full"
COMPLETE_DIR = ROOT / "complete" / "full"
JUDGED_DIR = ROOT / "judged_outputs" / "full"

TASKS = {
    "A (en)": {"jsonl": "task-a-en_llm_outputs.jsonl",
               "complete": "task-a-en_complete.tsv",
               "judged": "task-a-en.tsv"},
    "A (es)": {"jsonl": "task-a-es_llm_outputs.jsonl",
               "complete": "task-a-es_complete.tsv",
               "judged": "task-a-es.tsv"},
    "A (zh)": {"jsonl": "task-a-zh_llm_outputs.jsonl",
               "complete": "task-a-zh_complete.tsv",
               "judged": "task-a-zh.tsv"},
    "B1":     {"jsonl": "task-b1_llm_outputs.jsonl",
               "complete": "task-b1_complete.tsv",
               "judged": "task-b1.tsv"},
    "B2":     {"jsonl": "task-b2_llm_outputs.jsonl",
               "complete": "task-b2_complete.tsv",
               "judged": "task-b2.tsv"},
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_jsonl(path):
    """Yield parsed JSON objects from a JSONL file."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_tsv(path):
    """Return list of dicts from a TSV file."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def fmt_pct(n, total):
    return f"{100 * n / total:.1f}%" if total else "–"


def bar(pct, width=30):
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


# ── 1. Logical Mechanism Distribution ────────────────────────────────────────

def analyze_mechanisms():
    print("=" * 72)
    print("  LOGICAL MECHANISM DISTRIBUTION")
    print("=" * 72)

    global_counter = Counter()
    per_task = {}

    for label, files in TASKS.items():
        path = JSONL_DIR / files["jsonl"]
        if not path.exists():
            print(f"  [skip] {path.name} not found")
            continue

        task_counter = Counter()
        n_items = 0
        n_candidates = 0

        for item in load_jsonl(path):
            n_items += 1
            for cand in item.get("candidates", []):
                arch = cand.get("module_outputs", {}).get("architecture", {})
                lm = arch.get("logical_mechanism", "")
                if lm:
                    task_counter[lm] += 1
                    n_candidates += 1

        per_task[label] = (task_counter, n_items, n_candidates)
        global_counter.update(task_counter)

    total_candidates = sum(global_counter.values())
    total_items = sum(v[1] for v in per_task.values())
    unique = len(global_counter)

    print(f"\n  Items: {total_items}   Candidates: {total_candidates}   "
          f"Unique mechanisms: {unique}\n")

    # Per-task breakdown
    print(f"  {'Subtask':<10} {'Items':>6} {'Candidates':>11} {'Avg/item':>9}")
    print(f"  {'─' * 10} {'─' * 6} {'─' * 11} {'─' * 9}")
    for label, (_, ni, nc) in per_task.items():
        avg = f"{nc / ni:.1f}" if ni else "–"
        print(f"  {label:<10} {ni:>6} {nc:>11} {avg:>9}")

    # Top mechanisms
    print(f"\n  {'Rank':<5} {'Mechanism':<30} {'Count':>6} {'%':>7}  Distribution")
    print(f"  {'─' * 5} {'─' * 30} {'─' * 6} {'─' * 7}  {'─' * 30}")
    for rank, (mech, count) in enumerate(global_counter.most_common(15), 1):
        pct = 100 * count / total_candidates
        print(f"  {rank:<5} {mech:<30} {count:>6} {fmt_pct(count, total_candidates):>7}"
              f"  {bar(pct)}")

    remaining = total_candidates - sum(c for _, c in global_counter.most_common(15))
    print(f"  {'':5} {'(other ' + str(unique - 15) + ' mechanisms)':<30} "
          f"{remaining:>6} {fmt_pct(remaining, total_candidates):>7}")

    # Task-specific highlights
    print(f"\n  Task-specific patterns:")
    for label, (tc, _, nc) in per_task.items():
        top3 = tc.most_common(3)
        descs = [f"{m} ({fmt_pct(c, nc)})" for m, c in top3]
        print(f"    {label:<10} {', '.join(descs)}")

    print()


# ── 2. Judge Positional Bias ─────────────────────────────────────────────────

def analyze_positional_bias():
    print("=" * 72)
    print("  JUDGE POSITIONAL BIAS")
    print("=" * 72)

    overall = Counter()
    task_results = {}

    for label, files in TASKS.items():
        complete_path = COMPLETE_DIR / files["complete"]
        judged_path = JUDGED_DIR / files["judged"]

        if not complete_path.exists() or not judged_path.exists():
            print(f"  [skip] missing files for {label}")
            continue

        # Build candidate lookup: id → {candidate_num → joke_text}
        candidates = defaultdict(dict)
        for row in load_tsv(complete_path):
            candidates[row["id"]][int(row["candidate_num"])] = row["joke"].strip()

        # Load judged winners
        winners = {row["id"]: row["text"].strip() for row in load_tsv(judged_path)}

        # Match winners to candidate positions
        pos_counter = Counter()
        matched = 0
        for item_id, winner_text in winners.items():
            cands = candidates.get(item_id, {})
            found = False

            # Exact match
            for cnum, ctext in cands.items():
                if ctext == winner_text:
                    pos_counter[cnum] += 1
                    found = True
                    break

            # Fuzzy fallback (substring containment)
            if not found:
                for cnum, ctext in cands.items():
                    if ctext in winner_text or winner_text in ctext:
                        pos_counter[cnum] += 1
                        found = True
                        break

            if found:
                matched += 1

        overall.update(pos_counter)
        n = sum(pos_counter.values())
        task_results[label] = (pos_counter, matched, len(winners))

    total_matched = sum(v[1] for v in task_results.values())
    total_judged = sum(v[2] for v in task_results.values())
    total_wins = sum(overall.values())

    print(f"\n  Matched {total_matched} / {total_judged} items "
          f"({fmt_pct(total_matched, total_judged)})\n")

    # Overall distribution
    print(f"  {'Position':<10} {'Wins':>6} {'%':>7}  Distribution")
    print(f"  {'─' * 10} {'─' * 6} {'─' * 7}  {'─' * 30}")
    for pos in sorted(overall):
        pct = 100 * overall[pos] / total_wins
        print(f"  C{pos:<9} {overall[pos]:>6} {fmt_pct(overall[pos], total_wins):>7}"
              f"  {bar(pct)}")
    print(f"  {'Expected':<10} {'':>6} {'25.0%':>7}  {bar(25)}")

    # Per-task breakdown
    print(f"\n  {'Subtask':<10} {'C1':>6} {'C2':>6} {'C3':>6} {'C4':>6}"
          f"  {'Matched':>10}")
    print(f"  {'─' * 10} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6}  {'─' * 10}")
    for label, (pc, m, total) in task_results.items():
        n = sum(pc.values())
        vals = [fmt_pct(pc.get(p, 0), n) for p in [1, 2, 3, 4]]
        print(f"  {label:<10} {vals[0]:>6} {vals[1]:>6} {vals[2]:>6} {vals[3]:>6}"
              f"  {m:>4}/{total:<4}")

    # Observations
    if task_results:
        most_biased = max(task_results, key=lambda k: task_results[k][0].get(1, 0) /
                          max(sum(task_results[k][0].values()), 1))
        least_biased = min(task_results, key=lambda k: task_results[k][0].get(1, 0) /
                           max(sum(task_results[k][0].values()), 1))
        mb_pct = 100 * task_results[most_biased][0].get(1, 0) / sum(task_results[most_biased][0].values())
        lb_pct = 100 * task_results[least_biased][0].get(1, 0) / sum(task_results[least_biased][0].values())

        print(f"\n  Notes:")
        print(f"    • Strongest C1 bias:  {most_biased} ({mb_pct:.0f}%)")
        print(f"    • Weakest C1 bias:    {least_biased} ({lb_pct:.0f}%)")
        c1_pct = 100 * overall.get(1, 0) / total_wins
        print(f"    • Overall C1 win rate {c1_pct:.1f}% vs. expected 25.0% "
              f"(Δ = {c1_pct - 25:.1f}pp)")

    print()


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    analyze_mechanisms()
    analyze_positional_bias()
