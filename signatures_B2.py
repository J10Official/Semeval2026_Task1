import dspy
from typing import Literal


WRITING_TIPS_B2 = """
### Tips for Completing Fill-in-the-Blank GIF Prompts:

* **20 WORDS TOTAL - INCLUDING THE PROMPT:** The COMPLETE sentence must be 20 words or fewer. Plan accordingly.
* **GRAMMATICAL FIT:** Your completion must flow naturally into the blank. Read the full sentence aloud - any awkwardness = rewrite.
* **THE GIF IS YOUR PUNCHLINE:** The prompt is the setup; the GIF is the visual payoff. Your completion should make the GIF feel INEVITABLE.
* **DON'T FIGHT THE PROMPT:** Work WITH the structure given. The prompt tells you what KIND of completion it expects - deliver that, but unexpectedly.
* **SPECIFICITY IN THE BLANK:** Generic completions ("happy," "sad," "confused") waste the opportunity. Be specific and vivid.
* **THE REVEAL MOMENT:** When someone reads your completion and sees the GIF, they should think "YES, exactly that."
* **ECONOMY WITHIN THE BLANK:** Your completion should be as tight as possible. Don't pad with unnecessary words.
* **COMMIT TO THE VISUAL:** Whatever the GIF shows, lean into it. Don't try to make the GIF something it's not.
* **CONVERSATIONAL FLOW:** The complete sentence should sound like something a person would actually say/post.

### Red Flags (usually means the completion fails):
* Complete sentence exceeds 20 words
* Completion doesn't grammatically fit the blank
* GIF doesn't actually support the completed statement
* Generic/boring completion that wastes the opportunity
* Fighting against what the prompt wants
* Needing to explain why the GIF fits
"""

EVALUATION_CRITERIA_B2 = """
### Evaluation Framework for Prompt Completions:

1. **WORD COUNT CHECK:** Is the COMPLETE sentence 20 words or fewer? Over = automatic failure.
2. **GRAMMATICAL FIT:** Does the completion flow naturally into the blank? Is the full sentence grammatically correct?
3. **THE LAUGH TEST:** Would someone actually laugh when they read the completion and see the GIF?
4. **GIF INEVITABILITY:** Does the GIF feel like the perfect, obvious visual for this completed sentence?
5. **SURPRISE FACTOR:** Is the completion unexpected yet fitting? Does it subvert what you'd normally expect in that blank?
6. **SPECIFICITY:** Is the completion vivid and specific, or generic and forgettable?
7. **PROMPT SYNERGY:** Does the completion work WITH the prompt's structure, not against it?
8. **SHAREABILITY:** Would someone actually post this as a meme?

### Automatic Failures:
* Complete sentence over 20 words
* Grammatically awkward when inserted into blank
* GIF doesn't actually support or match the completion
* Completion is boring/predictable
* Fighting against the prompt's intended structure
"""

# -------------------------------------------------------------------------
# SIGNATURES FOR TASK B2: GIF CAPTION GENERATION (Image + Prompt)
# Complete a given text prompt with humorous content inspired by a GIF
# English only - the output must complete the provided fill-in-the-blank prompt
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
# MODULE 1: CONTEXT ENRICHMENT (The Analyst)
# -------------------------------------------------------------------------

class ContextEnricher(dspy.Signature):
    """
    Analyzes a GIF image description alongside a fill-in-the-blank prompt to find the comedic intersection between visual and textual context.
    
    Role: You are a visual-textual comedy analyst examining how the GIF relates to the given prompt scenario.
    Goal: Identify a humorous 'Situation' (SI) that bridges the GIF's content with the prompt's narrative setup - the comedy comes from how the visual perfectly (or absurdly) fits the described scenario.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(
        desc="Two parts: (1) A detailed description of the GIF: scene, subjects, actions, expressions, setting. (2) The fill-in-the-blank prompt that must be completed, e.g., 'When your office prank goes too far and everyone is like ______'."
    )

    # --- Outputs ---
    situation: str = dspy.OutputField(
        desc="Reimagine how the GIF depicts the scenario described in the prompt. Why does this visual perfectly capture the prompt's situation? What makes the pairing funny or relatable?"
    )
    
    semantic_associations: list[str] = dspy.OutputField(
        desc="List associations linking the GIF's visual elements to the prompt's context. How do the subjects, actions, and expressions map to the scenario being described?"
    )


# -------------------------------------------------------------------------
# MODULE 2: HUMOR ARCHITECT (The Brain)
# -------------------------------------------------------------------------

class HumorArchitect(dspy.Signature):
    """
    Designs the cognitive mechanism that makes the prompt completion funny when paired with the GIF visual.
    
    Role: You are the Logic Engine and Lead Comedy Writer. You find the 'incongruity' between the prompt's setup and the GIF's visual punchline. The blank is your canvas.
    Goal: Define the abstract 'Script Opposition' (SO) and 'Logical Mechanism' (LM) that creates humor when the visual completes the textual setup.
    
    Tips for Prompt-Completion Visual Humor:
    - The prompt provides the SETUP, the GIF provides the VISUAL PUNCHLINE - your completion bridges them
    - The blank often represents a reaction, emotion, or state - describe it through the GIF's lens
    - Consider what the prompt EXPECTS vs. what the GIF unexpectedly PROVIDES
    - The completion should feel inevitable once you see the GIF, yet surprising before
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The GIF description and the fill-in-the-blank prompt.")
    situation: str = dspy.InputField(desc="The reimagined scenario connecting the GIF to the prompt context.")
    semantic_associations: list[str] = dspy.InputField(desc="Associations linking the GIF's visual elements to the prompt's context. Use these to inform your target selection.")

    # --- Outputs ---
    focal_targets: str = dspy.OutputField(
        desc="The specific visual element, action, or expression you've chosen to target. What does the viewer SEE that becomes the punchline? Determine this yourself based on what has the most comedic potential."
    )
    
    cognitive_manipulation: str = dspy.OutputField(
        desc="A precise, one-sentence instruction on how to convert the visual into a textual completion. How do we describe what we see in a way that completes the prompt hilariously?"
    )
    
    logical_mechanism: str = dspy.OutputField(
        desc="The GTVH Label for the manipulation. Examples: [Relatable Visualization, Visual Hyperbole, Anthropomorphized Reaction, Mood Embodiment, Over-specific Description, Meme Reference, Universal Experience, Absurd Literalization, Internal Monologue, Meta-Commentary]."
    )
    
    expected_script: str = dspy.OutputField(
        desc="What a typical, predictable completion to this prompt would be - the 'normal' answer."
    )
    
    opposing_script: str = dspy.OutputField(
        desc="The unexpected, GIF-inspired completion that subverts expectations while fitting the visual perfectly."
    )
    
    script_opposition: str = dspy.OutputField(
        desc="The abstract semantic axis on which the expected completion and GIF-based completion clash. Format: [Expected Response] vs. [Visual Reality]."
    )


# -------------------------------------------------------------------------
# MODULE 3: DELIVERY STRATEGIST (The Director)
# -------------------------------------------------------------------------

class DeliveryStrategist(dspy.Signature):
    """
    Determines the best approach to complete the fill-in-the-blank for maximum comedic impact with the GIF.
    
    Role: You are a Meme Director. You analyze the visual content and prompt structure to decide how to fill the blank.
    Goal: Choose a completion style that makes the GIF feel like the perfect visual punchline to the prompt's setup.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The GIF description and the fill-in-the-blank prompt.")
    situation: str = dspy.InputField(desc="The reimagined scenario connecting GIF to prompt.")
    focal_targets: str = dspy.InputField(desc="The visual element that will become the punchline.")
    logical_mechanism: str = dspy.InputField(desc="The mechanism converting visual to completion.")
    script_opposition: str = dspy.InputField(desc="The incongruity between expected and visual response.")

    # --- Outputs ---
    strategic_analysis: str = dspy.OutputField(
        desc="Analyze the prompt's structure. What does the blank expect (emotion, action, description)? How can the GIF deliver something unexpected yet fitting?"
    )
    
    narrative_strategy: str = dspy.OutputField(
        desc="The approach to completing the blank. Examples: [Direct Visual Description, Emotional Embodiment, Mood Label, Over-specific Detail, Relatable State, ...]."
    )
    
    language_style: str = dspy.OutputField(
        desc="The specific 'Voice' for the completion. Examples: [Dry/Cynical, Deadpan, Self-Deprecating, Overly Specific, Internet Vernacular, ...]."
    )


# -------------------------------------------------------------------------
# MODULE 4: CONTENT WRITER (The Artist)
# -------------------------------------------------------------------------

class ContentWriter(dspy.Signature):
    """
    Executes the prompt completion with a strict 20-word maximum for the entire completed sentence.
    
    Role: You are a Meme Caption Completer. You fill in the blank to create a perfectly paired caption for the GIF.
    Goal: Complete the prompt in a way that makes viewers laugh when they see the GIF as the visual punchline.
    
    CRITICAL CONSTRAINT: Your completion MUST fit naturally into the blank AND the FULL completed sentence must be 20 words or fewer. The completion should feel like the only possible answer once you see the GIF.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The GIF description and the fill-in-the-blank prompt for reference.")
    situation: str = dspy.InputField(desc="The reimagined scenario connecting GIF to prompt.")
    focal_targets: str = dspy.InputField(desc="The visual element being translated into the completion.")
    cognitive_manipulation: str = dspy.InputField(desc="How to convert the visual into the textual completion.")
    logical_mechanism: str = dspy.InputField(desc="The humor mechanism being employed.")
    script_opposition: str = dspy.InputField(desc="The incongruity between expected and visual response.")
    strategic_analysis: str = dspy.InputField(desc="Analysis of how to approach the blank.")
    narrative_strategy: str = dspy.InputField(desc="The completion approach constraint.")
    language_style: str = dspy.InputField(desc="The tone constraint.")
    writing_guidelines: str = dspy.InputField(
        desc="Guidelines for completing fill-in-the-blank prompts: seamless integration, visual payoff, and natural grammar."
    )

    # --- Outputs ---
    draft_setup: str = dspy.OutputField(
        desc="The original prompt with the blank clearly identified. Restate what you're completing."
    )
    
    draft_punchline: str = dspy.OutputField(
        desc="Your completion for the blank - the words that will fill the '______'. This is what makes the GIF the perfect visual punchline."
    )
    
    final_joke: str = dspy.OutputField(
        desc="The COMPLETE sentence with your completion inserted into the blank. MUST be 20 words or fewer total. Should read as a natural, grammatically correct sentence.Avoid using tags and formatting as output should be plain text."
    )


# -------------------------------------------------------------------------
# MODULE 5: HUMOR JUDGE (The Critic)
# -------------------------------------------------------------------------

class HumorJudge(dspy.Signature):
    """
    Evaluates two prompt completions in a pairwise comparison to determine which creates the funnier meme when paired with the GIF.
    
    Role: You are a meme connoisseur and comedy critic who understands internet humor. You know what makes a fill-in-the-blank meme land vs miss.
    
    Your job: Pick the completion that makes the GIF feel like the inevitable, perfect visual punchline. A completion that exceeds 20 words total automatically loses.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(
        desc="The GIF description and the fill-in-the-blank prompt that both completions are answering."
    )
    
    joke_candidate_1: str = dspy.InputField(desc="Completion Option A (the full completed sentence).")
    joke_candidate_2: str = dspy.InputField(desc="Completion Option B (the full completed sentence).")
    
    evaluation_criteria: str = dspy.InputField(
        desc="Criteria for judging prompt completion quality: GIF fit, comedic surprise, grammatical flow, and relatability."
    )

    # --- Outputs ---
    critique: str = dspy.OutputField(
        desc="First verify both completions are 20 words or fewer (over = automatic loss). Then analyze: Which completion makes the GIF feel more like the perfect visual punchline? Which is more surprising yet fitting? Which reads more naturally? Does the completion feel inevitable when you see the GIF?"
    )
    
    better_joke: Literal["Joke 1", "Joke 2"] = dspy.OutputField(
        desc="The winner. Return exactly 'Joke 1' or 'Joke 2'."
    )
