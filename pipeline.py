"""
Unified Pipeline Module for the MWAHAHA Humor Generation Pipeline.

Implements a single DSPy-based pipeline that handles all task types:
- Task A1: Headline-based joke generation
- Task A2: Word-inclusion joke generation
- Task B1: GIF caption generation
- Task B2: GIF + prompt caption generation

The pipeline uses a 5-module architecture:
1. ContextEnricher - Analyzes input
2. HumorArchitect - Designs humor logic
3. DeliveryStrategist - Plans delivery
4. ContentWriter - Generates jokes
5. HumorJudge - Selects best joke

Variation Strategy (4 architects) with PARALLEL execution:
- Generate NUM_ARCHITECT_VARIATIONS (4) different humor concepts IN PARALLEL
- Each concept uses 1 delivery strategy (NUM_STRATEGY_VARIATIONS = 1)
- Total candidates = NUM_ARCHITECT_VARIATIONS * NUM_STRATEGY_VARIATIONS (4 total)

Parallelization:
- Uses ThreadPoolExecutor for concurrent API calls
- Each branch has independent predictor instances (no shared state)
- Branches are fully independent - one failing doesn't affect others

Why Unified Pipeline Works:
- All signatures have IDENTICAL field names (original_input, situation, etc.)
- Only the docstrings and field descriptions differ per task
- The pipeline just pushes data through modules; the LLM behavior
  is controlled by the signature descriptions, not pipeline logic
"""

import dspy
from typing import Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random

from api import call_with_retry, track_tokens, token_tracker, get_module_lm
from validators import validate_joke
from logger import (
    logger,
    log_section,
    log_subsection,
    log_input,
    log_output,
    log_dspy_trace,
    log_error,
    # Prompt tuning mode functions
    pt_item_start,
    pt_context,
    pt_candidate_joke,
    pt_judgment,
    pt_judge_comparison,
    pt_judge_result,
)
from config import (
    NUM_CANDIDATES,
    NUM_ARCHITECT_VARIATIONS,
    NUM_STRATEGY_VARIATIONS,
    ENABLE_CONSTRAINT_CHECK,
    get_module_config,
)

# Import signatures
from signatures_A1 import (
    ContextEnricher as ContextEnricherA1,
    HumorArchitect as HumorArchitectA1,
    DeliveryStrategist as DeliveryStrategistA1,
    ContentWriter as ContentWriterA1,
    HumorJudge as HumorJudgeA1,
    WRITING_TIPS_A1_EN,
    WRITING_TIPS_A1_ES,
    WRITING_TIPS_A1_ZH,
    EVALUATION_CRITERIA_A1_EN,
    EVALUATION_CRITERIA_A1_ES,
    EVALUATION_CRITERIA_A1_ZH,
)

from signatures_A2 import (
    ContextEnricher as ContextEnricherA2,
    HumorArchitect as HumorArchitectA2,
    DeliveryStrategist as DeliveryStrategistA2,
    ContentWriter as ContentWriterA2,
    HumorJudge as HumorJudgeA2,
    WRITING_TIPS_A2_EN,
    WRITING_TIPS_A2_ES,
    WRITING_TIPS_A2_ZH,
    EVALUATION_CRITERIA_A2_EN,
    EVALUATION_CRITERIA_A2_ES,
    EVALUATION_CRITERIA_A2_ZH,
)

from signatures_B1 import (
    ContextEnricher as ContextEnricherB1,
    HumorArchitect as HumorArchitectB1,
    DeliveryStrategist as DeliveryStrategistB1,
    ContentWriter as ContentWriterB1,
    HumorJudge as HumorJudgeB1,
    WRITING_TIPS_B1,
    EVALUATION_CRITERIA_B1,
)

from signatures_B2 import (
    ContextEnricher as ContextEnricherB2,
    HumorArchitect as HumorArchitectB2,
    DeliveryStrategist as DeliveryStrategistB2,
    ContentWriter as ContentWriterB2,
    HumorJudge as HumorJudgeB2,
    WRITING_TIPS_B2,
    EVALUATION_CRITERIA_B2,
)

# =========================================================================
# SIGNATURE REGISTRY
# =========================================================================
# All signatures have identical field names; only descriptions differ.
# We load the appropriate signatures based on task type.

SIGNATURE_REGISTRY = {
    "a1": (ContextEnricherA1, HumorArchitectA1, DeliveryStrategistA1, ContentWriterA1, HumorJudgeA1),
    "a2": (ContextEnricherA2, HumorArchitectA2, DeliveryStrategistA2, ContentWriterA2, HumorJudgeA2),
    "b1": (ContextEnricherB1, HumorArchitectB1, DeliveryStrategistB1, ContentWriterB1, HumorJudgeB1),
    "b2": (ContextEnricherB2, HumorArchitectB2, DeliveryStrategistB2, ContentWriterB2, HumorJudgeB2),
}

# Writing tips registry
WRITING_TIPS_REGISTRY = {
    "a1": {"en": WRITING_TIPS_A1_EN, "es": WRITING_TIPS_A1_ES, "zh": WRITING_TIPS_A1_ZH},
    "a2": {"en": WRITING_TIPS_A2_EN, "es": WRITING_TIPS_A2_ES, "zh": WRITING_TIPS_A2_ZH},
    "b1": {"en": WRITING_TIPS_B1},
    "b2": {"en": WRITING_TIPS_B2},
}

# Evaluation criteria registry
EVALUATION_CRITERIA_REGISTRY = {
    "a1": {"en": EVALUATION_CRITERIA_A1_EN, "es": EVALUATION_CRITERIA_A1_ES, "zh": EVALUATION_CRITERIA_A1_ZH},
    "a2": {"en": EVALUATION_CRITERIA_A2_EN, "es": EVALUATION_CRITERIA_A2_ES, "zh": EVALUATION_CRITERIA_A2_ZH},
    "b1": {"en": EVALUATION_CRITERIA_B1},
    "b2": {"en": EVALUATION_CRITERIA_B2},
}

# Task B types (no language parameter)
TASK_B_TYPES = {"b1", "b2"}


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_writing_tips(task: str, language: str = "en") -> str:
    """Get writing tips for a specific task and language."""
    tips = WRITING_TIPS_REGISTRY.get(task, {})
    return tips.get(language, tips.get("en", ""))


def get_evaluation_criteria(task: str, language: str = "en") -> str:
    """Get evaluation criteria for a specific task and language."""
    criteria = EVALUATION_CRITERIA_REGISTRY.get(task, {})
    return criteria.get(language, criteria.get("en", ""))


def get_language_literal(language: str) -> str:
    """Convert language code to Literal value expected by signatures."""
    return {"en": "English", "es": "Spanish", "zh": "Chinese"}.get(language, "English")


def extract_outputs(prediction: Any) -> dict:
    """Extract output fields from a DSPy prediction as a dictionary.
    
    DSPy 3.0.4+ stores outputs in prediction._store, not directly in __dict__.
    """
    # DSPy 3.0.4+ uses _store for output fields
    if hasattr(prediction, '_store') and prediction._store:
        return dict(prediction._store)
    # Fallback for older DSPy versions or other prediction types
    if hasattr(prediction, '__dict__'):
        return {k: v for k, v in prediction.__dict__.items() if not k.startswith('_')}
    return {}


# =========================================================================
# UNIFIED PIPELINE
# =========================================================================

class UnifiedHumorPipeline(dspy.Module):
    """
    Unified pipeline for all humor generation tasks.
    
    The pipeline dynamically loads task-specific signatures but uses
    identical data flow logic. Signatures differ only in their docstrings
    and field descriptions, which guide the LLM's behavior.
    
    Variation Strategy (4 architects) with PARALLEL execution:
    - Generate NUM_ARCHITECT_VARIATIONS (4) different humor concepts IN PARALLEL
    - Each concept uses 1 delivery strategy (NUM_STRATEGY_VARIATIONS = 1)
    - This produces NUM_CANDIDATES (4) total jokes for judging
    
    Thread Safety:
    - Each parallel branch creates its OWN predictor instances
    - No shared mutable state between branches
    - Token tracking uses thread-safe operations
    
    Args:
        task_type: One of "a1", "a2", "b1", "b2"
    """
    
    # Thread-local storage for logging context
    _local = threading.local()
    
    def __init__(self, task_type: str):
        super().__init__()
        
        if task_type not in SIGNATURE_REGISTRY:
            raise ValueError(f"Unknown task type: {task_type}. Available: {list(SIGNATURE_REGISTRY.keys())}")
        
        self.task_type = task_type
        self.is_task_b = task_type in TASK_B_TYPES
        
        # Load task-specific signatures (store classes, not instances)
        (
            self.ContextEnricherSig,
            self.HumorArchitectSig,
            self.DeliveryStrategistSig,
            self.ContentWriterSig,
            self.HumorJudgeSig,
        ) = SIGNATURE_REGISTRY[task_type]
        
        # Initialize predictors for non-parallel operations with module-specific LMs
        self.context_enricher = self._create_predictor_with_lm(
            self.ContextEnricherSig, "ContextEnricher"
        )
        self.humor_judge = self._create_predictor_with_lm(
            self.HumorJudgeSig, "HumorJudge"
        )
        
        # Pre-create LM instances for branch predictors (must be done in main thread)
        # These will be attached to predictors when branches are created
        self._architect_lm = get_module_lm("HumorArchitect")
        self._strategist_lm = get_module_lm("DeliveryStrategist")
        self._writer_lm = get_module_lm("ContentWriter")
        
        # Storage for intermediate outputs (thread-safe via per-item usage)
        self.module_outputs = {}
    
    def _create_predictor_with_lm(self, signature, module_name: str) -> dspy.Predict:
        """
        Create a predictor with module-specific LM configuration.
        
        This is the proper way to configure per-module LLM parameters (temperature,
        penalties, etc.) - attach the LM to the predictor at creation time, not
        during execution. The predictor will always use its own LM.
        
        Args:
            signature: DSPy signature class
            module_name: Name of the module (for config lookup)
        
        Returns:
            Configured dspy.Predict instance with module-specific LM
        """
        predictor = dspy.Predict(signature)
        
        # Get module-specific LM if configured
        module_lm = get_module_lm(module_name)
        if module_lm:
            predictor.lm = module_lm
            logger.debug(f"Configured {module_name} with custom LM (temp={module_lm.kwargs.get('temperature', 'default')})")
        
        return predictor
    
    def _create_branch_predictors(self):
        """
        Create fresh predictor instances for a parallel branch.
        
        Each branch gets its own predictors with module-specific LM configurations.
        Uses pre-created LM instances from __init__ (created in main thread) to avoid
        DSPy's thread-safety restrictions. The LMs are attached to fresh predictors.
        
        Returns:
            Dictionary of predictor instances for the branch
        """
        # Create fresh predictors and attach the pre-created LMs
        # DO NOT call get_module_lm() here - we're in a worker thread!
        architect = dspy.Predict(self.HumorArchitectSig)
        architect.lm = self._architect_lm
        
        strategist = dspy.Predict(self.DeliveryStrategistSig)
        strategist.lm = self._strategist_lm
        
        writer = dspy.Predict(self.ContentWriterSig)
        writer.lm = self._writer_lm
        
        return {
            "architect": architect,
            "strategist": strategist,
            "writer": writer,
        }
    
    def _call_module_simple(self, module: dspy.Module, module_name: str, branch_id: str = "", **kwargs) -> Any:
        """
        Call a DSPy module with retry (simplified logging for parallel execution).
        
        The module's LM is already configured at predictor creation time via
        _create_predictor_with_lm(), so no context switching is needed here.
        
        Args:
            module: The DSPy module to call (already has its LM configured)
            module_name: Name for logging
            branch_id: Identifier for the parallel branch (e.g., "[1,2]")
            **kwargs: Arguments to pass to the module
        
        Returns:
            Module prediction
        """
        # Log with branch context
        prefix = f"[Branch {branch_id}] " if branch_id else ""
        logger.debug(f"{prefix}🔧 Calling {module_name}...")
        
        # Call with retry - module already has its LM configured
        caller_id = f"{module_name}[{branch_id}]" if branch_id else module_name
        prediction = call_with_retry(module, caller_id=caller_id, **kwargs)
        
        return prediction
    
    def _call_module(self, module: dspy.Module, module_name: str, **kwargs) -> Any:
        """
        Call a DSPy module with retry and logging (for sequential operations).
        
        The module's LM is already configured at predictor creation time via
        _create_predictor_with_lm(), so no context switching is needed here.
        
        Args:
            module: The DSPy module to call (already has its LM configured)
            module_name: Name for logging
            **kwargs: Arguments to pass to the module
        
        Returns:
            Module prediction
        """
        log_subsection(f"🔧 {module_name}")
        log_input(kwargs, module_name)
        
        # Call with retry - module already has its LM configured at creation
        prediction = call_with_retry(module, caller_id=module_name, **kwargs)
        
        # Track tokens - use module's LM if set, otherwise global
        lm_to_track = getattr(module, 'lm', None) or dspy.settings.lm
        if lm_to_track:
            track_tokens(lm_to_track, module_name)
            log_dspy_trace(lm_to_track, module_name)
        
        # Extract and log outputs
        outputs = extract_outputs(prediction)
        log_output(outputs, module_name)
        
        # Store for later reference
        self.module_outputs[module_name] = outputs
        
        # Trigger prompt tuning context logging for ContextEnricher
        if module_name == "ContextEnricher":
            semantic_associations = outputs.get("semantic_associations")
            if isinstance(semantic_associations, str):
                semantic_associations = semantic_associations.split(", ") if semantic_associations else None
            
            pt_context(
                outputs.get("situation", ""),
                semantic_associations
            )
        
        return prediction
    
    def _generate_single_candidate(
        self,
        arch_idx: int,
        strat_idx: int,
        context_situation: str,
        context_semantic_associations: list,
        original_input: str,
        lang_literal: str,
        writing_tips: str,
    ) -> tuple[int, int, str, dict, Exception]:
        """
        Generate a single candidate joke (runs in parallel thread).
        
        This method is designed to be completely independent - it creates
        its own predictor instances and has no shared mutable state.
        
        Returns:
            Tuple of (arch_idx, strat_idx, joke, outputs_dict, error)
            If error is not None, the generation failed.
        """
        branch_id = f"{arch_idx + 1},{strat_idx + 1}"
        
        try:
            # Note: ChatAdapter is configured once at startup in api.py
            # DSPy 3.0.4+ enforces thread-safety - settings can only be changed by main thread
            # The global adapter configuration is inherited by all threads
            
            # Create fresh predictors for this branch (complete isolation)
            predictors = self._create_branch_predictors()
            
            # Build kwargs helper
            def make_kwargs(**extra):
                kwargs = {"original_input": original_input, **extra}
                if not self.is_task_b:
                    kwargs["target_language_and_culture"] = lang_literal
                return kwargs
            
            # Step 1: HumorArchitect
            logger.info(f"🧠 [{branch_id}] Running HumorArchitect...")
            architecture = self._call_module_simple(
                predictors["architect"],
                "HumorArchitect",
                branch_id,
                **make_kwargs(
                    situation=context_situation,
                    semantic_associations=context_semantic_associations,
                )
            )
            
            # Step 2: DeliveryStrategist
            logger.info(f"🎬 [{branch_id}] Running DeliveryStrategist...")
            strategy = self._call_module_simple(
                predictors["strategist"],
                "DeliveryStrategist",
                branch_id,
                **make_kwargs(
                    situation=context_situation,
                    focal_targets=architecture.focal_targets,
                    logical_mechanism=architecture.logical_mechanism,
                    script_opposition=architecture.script_opposition,
                )
            )
            
            # Step 3: ContentWriter
            logger.info(f"✍️ [{branch_id}] Running ContentWriter...")
            content = self._call_module_simple(
                predictors["writer"],
                "ContentWriter",
                branch_id,
                **make_kwargs(
                    situation=context_situation,
                    focal_targets=architecture.focal_targets,
                    cognitive_manipulation=architecture.cognitive_manipulation,
                    logical_mechanism=architecture.logical_mechanism,
                    script_opposition=architecture.script_opposition,
                    strategic_analysis=strategy.strategic_analysis,
                    narrative_strategy=strategy.narrative_strategy,
                    language_style=strategy.language_style,
                    writing_guidelines=writing_tips,
                )
            )
            
            # Collect outputs
            candidate_outputs = {
                "architecture": extract_outputs(architecture),
                "strategy": extract_outputs(strategy),
                "content": extract_outputs(content),
            }
            
            joke = content.final_joke
            logger.info(f"✅ [{branch_id}] Generated: {joke[:80]}...")
            
            # Log for prompt tuning mode
            pt_candidate_joke(
                branch_id,
                joke,
                candidate_outputs["architecture"],
                candidate_outputs["strategy"]
            )
            
            return (arch_idx, strat_idx, joke, candidate_outputs, None)
            
        except Exception as e:
            logger.error(f"❌ [{branch_id}] Failed: {str(e)[:200]}")
            return (arch_idx, strat_idx, None, None, e)
    
    def generate_with_variation(
        self,
        original_input: str,
        language: str = "en",
        word1: str = None,
        word2: str = None,
    ) -> list[tuple[str, dict]]:
        """
        Generate jokes using 4 architect variations with PARALLEL execution.
        
        1. Run ContextEnricher once (sequential - needed by all branches)
        2. Run ALL architect+strategist+writer branches IN PARALLEL (4 total)
        3. Collect results and handle any failures gracefully
        
        Parallelization Benefits:
        - ~4x faster (all branches run concurrently)
        - Better API utilization (closer to rate limits)
        - Independent branches (one failure doesn't affect others)
        
        Returns:
            List of (joke, module_outputs) tuples
        """
        writing_tips = get_writing_tips(self.task_type, language)
        lang_literal = get_language_literal(language)
        
        # Build base kwargs
        def make_kwargs(**extra):
            kwargs = {"original_input": original_input, **extra}
            if not self.is_task_b:
                kwargs["target_language_and_culture"] = lang_literal
            return kwargs
        
        # Step 1: Context Enrichment (sequential - shared by all branches)
        log_subsection("📋 Context Enrichment (shared)")
        context = self._call_module(
            self.context_enricher,
            "ContextEnricher",
            **make_kwargs()
        )
        
        # Extract semantic associations for HumorArchitect
        # Each architect gets the same semantic associations and decides its own targets
        semantic_associations = context.semantic_associations
        if isinstance(semantic_associations, str):
            semantic_associations = semantic_associations.split(", ") if semantic_associations else []
        
        # Step 2: Generate ALL candidates in PARALLEL
        log_subsection(f"🚀 Generating {NUM_ARCHITECT_VARIATIONS * NUM_STRATEGY_VARIATIONS} candidates in PARALLEL")
        
        candidates = []
        failed_branches = []
        
        # Use ThreadPoolExecutor for parallel API calls
        # Max workers = number of parallel branches (all independent)
        max_workers = NUM_ARCHITECT_VARIATIONS * NUM_STRATEGY_VARIATIONS
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all branch tasks
            futures = {}
            for arch_idx in range(NUM_ARCHITECT_VARIATIONS):
                for strat_idx in range(NUM_STRATEGY_VARIATIONS):
                    future = executor.submit(
                        self._generate_single_candidate,
                        arch_idx,
                        strat_idx,
                        context.situation,
                        semantic_associations,  # HumorArchitect decides its own targets
                        original_input,
                        lang_literal,
                        writing_tips,
                    )
                    futures[future] = (arch_idx, strat_idx)
            
            # Collect results as they complete
            for future in as_completed(futures):
                arch_idx, strat_idx, joke, outputs, error = future.result()
                branch_id = f"{arch_idx + 1},{strat_idx + 1}"
                
                if error is not None:
                    failed_branches.append((branch_id, error))
                    logger.warning(f"⚠️ Branch [{branch_id}] failed, continuing with others...")
                else:
                    # Add context to outputs
                    outputs["context"] = extract_outputs(context)
                    candidates.append((arch_idx, strat_idx, joke, outputs))
        
        # Sort candidates by branch order for consistent output
        candidates.sort(key=lambda x: (x[0], x[1]))
        
        # Log summary
        logger.info(f"📊 Parallel generation complete: {len(candidates)} succeeded, {len(failed_branches)} failed")
        
        # Log each successful candidate
        for arch_idx, strat_idx, joke, outputs in candidates:
            logger.info(f"Candidate [{arch_idx + 1},{strat_idx + 1}]: {joke[:100]}...")
        
        # Convert to expected format (just joke and outputs)
        return [(joke, outputs) for _, _, joke, outputs in candidates]
    
    def judge_candidates(
        self,
        candidates: list[str],
        original_input: str,
        language: str = "en",
    ) -> str:
        """
        Judge candidates using tournament-style pairwise comparison.
        
        For 4 candidates: (1 vs 2) AND (3 vs 4) run IN PARALLEL, then final.
        """
        if len(candidates) == 0:
            raise ValueError("Cannot judge empty candidates list")
        if len(candidates) == 1:
            return candidates[0]
        
        eval_criteria = get_evaluation_criteria(self.task_type, language)
        lang_literal = get_language_literal(language)
        
        def judge_pair(joke1: str, joke2: str, match_name: str = "") -> tuple[str, str]:
            """Judge a pair and return the winner and which joke won."""
            judge_kwargs = {
                "original_input": original_input,
                "joke_candidate_1": joke1,
                "joke_candidate_2": joke2,
                "evaluation_criteria": eval_criteria,
            }
            if not self.is_task_b:
                judge_kwargs["target_language_and_culture"] = lang_literal
            
            if match_name:
                log_subsection(f"⚖️ {match_name}")
            
            # Log which jokes are being compared (prompt tuning mode)
            pt_judge_comparison(joke1, joke2, match_name)
            
            judgment = self._call_module(self.humor_judge, "HumorJudge", **judge_kwargs)
            winner_id = "1" if judgment.better_joke == "Joke 1" else "2"
            winner = joke1 if winner_id == "1" else joke2
            
            # Log the result (prompt tuning mode)
            critique = getattr(judgment, 'critique', '')
            pt_judge_result(winner_id, critique)
            
            return winner
        
        # Tournament bracket
        if len(candidates) == 2:
            log_subsection("⚖️ Final: Candidate 1 vs 2")
            return judge_pair(candidates[0], candidates[1], "Final: Candidate 1 vs 2")
        elif len(candidates) >= 4:
            # Semi-finals run IN PARALLEL
            log_subsection("⚖️ Semi-finals (parallel)")
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                future1 = executor.submit(judge_pair, candidates[0], candidates[1], "Semi-final 1: Candidate 1 vs 2")
                future2 = executor.submit(judge_pair, candidates[2], candidates[3], "Semi-final 2: Candidate 3 vs 4")
                
                winner1 = future1.result()
                winner2 = future2.result()
            
            # Final (sequential)
            log_subsection("⚖️ Final: Winner 1 vs Winner 2")
            return judge_pair(winner1, winner2, "Final: Winner 1 vs Winner 2")
        else:
            # For 3 candidates: 1 vs 2, winner vs 3
            log_subsection("⚖️ Round 1: Candidate 1 vs 2")
            winner = judge_pair(candidates[0], candidates[1], "Round 1: Candidate 1 vs 2")
            log_subsection("⚖️ Final: Winner vs Candidate 3")
            return judge_pair(winner, candidates[2], "Final: Winner vs Candidate 3")
    
    def forward(
        self,
        original_input: str,
        language: str = "en",
        word1: str = None,
        word2: str = None,
        skip_judge: bool = False,
    ) -> tuple[str, list[tuple[str, dict]]]:
        """
        Generate and select the best joke.
        
        Args:
            original_input: The input text (headline, words, or GIF description)
            language: Target language code (for Task A)
            word1: First required word (for Task A2)
            word2: Second required word (for Task A2)
            skip_judge: If True, skip judging and return None as winner (for --complete mode)
        
        Returns:
            Tuple of (best_joke, all_candidates)
            - best_joke: The winning joke selected by the judge (None if skip_judge=True)
            - all_candidates: List of (joke, module_outputs) tuples for all candidates
        
        Raises:
            ValueError: If original_input is empty or invalid
        """
        # Input validation
        if not original_input or not original_input.strip():
            raise ValueError("original_input cannot be empty or whitespace only")
        
        # Log task header
        task_labels = {
            "a1": f"HEADLINE JOKE PIPELINE [{language.upper()}]",
            "a2": f"WORD INCLUSION PIPELINE [{language.upper()}]",
            "b1": "GIF CAPTION PIPELINE [B1]",
            "b2": "GIF PROMPT CAPTION PIPELINE [B2]",
        }
        log_section(f"🎭 {task_labels[self.task_type]}")
        logger.info(f"Input: {original_input[:200]}{'...' if len(original_input) > 200 else ''}")
        
        # Log for prompt tuning mode
        pt_item_start("current", self.task_type, original_input)
        
        # Generate candidates with 2x2 variation
        candidate_results = self.generate_with_variation(
            original_input, language, word1, word2
        )
        
        # Handle case where all candidates failed
        if not candidate_results:
            logger.error("❌ All candidate generations failed!")
            raise RuntimeError("Failed to generate any valid candidates. All branches failed.")
        
        # Separate jokes and validate
        all_jokes = [joke for joke, _ in candidate_results]
        valid_jokes = []
        
        if ENABLE_CONSTRAINT_CHECK:
            for i, joke in enumerate(all_jokes):
                passed, failures = validate_joke(
                    joke,
                    self.task_type,
                    language,
                    word1,
                    word2,
                    f"candidate_{i}",
                )
                if passed:
                    valid_jokes.append(joke)
                else:
                    logger.warning(f"Candidate {i + 1} failed validation: {failures}")
        else:
            valid_jokes = all_jokes
        
        # Use valid candidates if available, else fall back to all
        candidates_to_judge = valid_jokes if valid_jokes else all_jokes
        
        # Skip judging if requested (--complete mode)
        if skip_judge:
            logger.info(f"⏭️ Skipping judge (--complete mode). Generated {len(candidate_results)} candidates.")
            return None, candidate_results
        
        # Judge and select winner
        log_subsection(f"🏆 Judging {len(candidates_to_judge)} Candidates")
        best_joke = self.judge_candidates(candidates_to_judge, original_input, language)
        
        logger.info(f"🏆 Final Winner: {best_joke}")
        
        # Log for prompt tuning mode
        pt_judgment(best_joke, "Selected as best joke from tournament bracket")
        
        return best_joke, candidate_results


# =========================================================================
# FACTORY FUNCTION
# =========================================================================

def get_pipeline(task_type: str) -> UnifiedHumorPipeline:
    """
    Get the appropriate pipeline for a task type.
    
    Args:
        task_type: One of "a1", "a2", "b1", "b2"
    
    Returns:
        Instantiated UnifiedHumorPipeline configured for the task
    """
    return UnifiedHumorPipeline(task_type)
