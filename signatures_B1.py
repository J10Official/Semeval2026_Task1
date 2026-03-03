import dspy
from typing import Literal


WRITING_TIPS_B1 = """
### Tips for Writing GIF Captions:

* **20 WORDS MAX - NO EXCEPTIONS:** Brevity is mandatory. If you can say it in 8 words, don't use 15. The GIF does half the work.
* **RECONTEXTUALIZE, DON'T DESCRIBE:** Never describe what's happening in the GIF. Instead, tell us what it MEANS or what it REPRESENTS.
* **THE "WHEN YOU..." FORMULA:** Works because it's relatable. But only use it if it genuinely fits - forced relatability is worse than none.
* **CAPTION + GIF > EITHER ALONE:** The humor should come from the COMBINATION. Neither caption nor GIF should be funny alone.
* **MATCH THE ENERGY:** A chaotic GIF needs punchy text. A slow-burn GIF can handle a longer setup. Read the visual rhythm.
* **SPECIFICITY WINS:** "When your 3rd alarm goes off and you're still bargaining with God" beats "When you're tired."
* **NO EXPLAINING:** The caption sets up; the GIF delivers. If you need to explain, the pairing doesn't work.
* **UNIVERSAL > NICHE:** Unless you're sure of your audience, go for broadly relatable experiences.
* **COMMIT TO THE VOICE:** Whether deadpan, chaotic, or self-deprecating - pick a lane and stay in it.

### Red Flags (usually means the caption fails):
* Describing what's literally happening in the GIF
* Over 20 words
* Caption is funny without the GIF (means the GIF isn't contributing)
* Generic caption that could work with any GIF
* Trying too hard to be relatable
* Explaining the joke or the visual
"""

EVALUATION_CRITERIA_B1 = """
### Evaluation Framework for GIF Captions:

1. **WORD COUNT CHECK:** Is it 20 words or fewer? Over = automatic failure.
2. **THE LAUGH TEST:** Would someone actually laugh, save it, or share it? Not "clever" - genuinely funny as a meme.
3. **VISUAL-TEXT SYNERGY:** Does the caption transform how we see the GIF? Is the combination funnier than either alone?
4. **RELATABILITY:** Can people see themselves in this? "This is so me" energy is powerful.
5. **SPECIFICITY:** Is it specific enough to hit hard, or generic enough to be forgettable?
6. **BREVITY:** Even under 20 words - could it be tighter? Every word should earn its place.
7. **ORIGINALITY:** Does it feel fresh, or like a caption we've seen 100 times?
8. **SHAREABILITY:** Would someone actually send this to a friend or post it?

### Automatic Failures:
* Over 20 words
* Describes the GIF instead of recontextualizing it
* Caption would be funny without any GIF (not a true pairing)
* So generic it could caption any GIF
"""



# -------------------------------------------------------------------------
# SIGNATURES FOR TASK B1: GIF CAPTION GENERATION (Image Only)
# Generate humorous captions (max 20 words) for GIF images
# English only - no language selection required
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
# MODULE 1: CONTEXT ENRICHMENT (The Analyst)
# -------------------------------------------------------------------------

class ContextEnricher(dspy.Signature):
    """
    Analyzes a GIF image description to extract comedic potential by reimagining the visual scene in unexpected ways.
    
    Role: You are a visual comedy analyst examining the raw material of a GIF to find humor angles.
    Goal: Identify a humorous 'Situation' (SI) by reinterpreting what's shown in the GIF - the comedy comes from the gap between what we see and how we describe it.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(
        desc="A detailed description of the GIF: the scene, characters/subjects, actions, movements, expressions, setting, and any notable visual elements."
    )

    # --- Outputs ---
    situation: str = dspy.OutputField(
        desc="Reimagine the GIF scenario humorously. What funny situation could this visual be depicting? Create an unexpected narrative or context that transforms the mundane into the absurd."
    )
    
    semantic_associations: list[str] = dspy.OutputField(
        desc="List associations, stereotypes, or cultural references linked to the key visual elements: the subjects, actions, setting, and expressions. What does each element evoke?"
    )


# -------------------------------------------------------------------------
# MODULE 2: HUMOR ARCHITECT (The Brain)
# -------------------------------------------------------------------------

class HumorArchitect(dspy.Signature):
    """
    Deconstructs the visual context into a formal GTVH (General Theory of Verbal Humor) structural blueprint for caption humor.
    
    Role: You are the Logic Engine and Lead Comedy Writer. You design the cognitive mechanism that makes the caption funny when paired with the GIF. You find the 'incongruity' between what's seen and what's said.
    Goal: Define the abstract 'Script Opposition' (SO) and 'Logical Mechanism' (LM) that creates humor when the caption meets the visual.
    
    Tips for Visual Humor:
    - The best GIF captions recontextualize what we see - same visual, completely different meaning
    - Relatable situations ("When you..." "Me after...") work because viewers recognize themselves
    - The caption should ADD meaning, not just describe what's already visible
    - Misdirection works well: describe what it LOOKS like, not what it IS
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The detailed description of the GIF.")
    situation: str = dspy.InputField(desc="The reimagined humorous scenario for the GIF.")
    semantic_associations: list[str] = dspy.InputField(desc="Associations, stereotypes, or cultural references linked to the key visual elements. Use these to inform your target selection.")

    # --- Outputs ---
    focal_targets: str = dspy.OutputField(
        desc="The specific visual elements, actions, or expressions you've chosen to target. What in the GIF will the caption twist or reframe? Determine this yourself based on what has the most comedic potential."
    )
    
    cognitive_manipulation: str = dspy.OutputField(
        desc="A precise, one-sentence instruction on how to twist what's shown in the GIF. Describe the recontextualization or reinterpretation that makes it funny."
    )
    
    logical_mechanism: str = dspy.OutputField(
        desc="The GTVH Label for the manipulation. Examples: [Recontextualization, Relatable Situation, Anthropomorphization, Misattribution, Exaggeration, Role Reversal, Juxtaposition, Ignoring the Obvious, Over-specificity, Internal Monologue, Meta-Commentary, Absurdity]."
    )
    
    expected_script: str = dspy.OutputField(
        desc="What the viewer naturally assumes is happening in the GIF at face value."
    )
    
    opposing_script: str = dspy.OutputField(
        desc="The unexpected interpretation or narrative that the caption will impose on the visual."
    )
    
    script_opposition: str = dspy.OutputField(
        desc="The abstract semantic axis on which the visual reality and caption's narrative clash. Format: [What It Is] vs. [What We Say It Is]."
    )


# -------------------------------------------------------------------------
# MODULE 3: DELIVERY STRATEGIST (The Director)
# -------------------------------------------------------------------------

class DeliveryStrategist(dspy.Signature):
    """
    Determines the best caption format and tone for maximum comedic impact with the GIF.
    
    Role: You are a Meme Director. You analyze the visual content and humor logic to decide the perfect caption style.
    Goal: Choose a caption format that complements the GIF's energy and delivers the punchline in 20 words or less.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The detailed description of the GIF.")
    situation: str = dspy.InputField(desc="The reimagined humorous scenario.")
    focal_targets: str = dspy.InputField(desc="The visual elements being targeted for humor.")
    logical_mechanism: str = dspy.InputField(desc="The recontextualization or twist being applied.")
    script_opposition: str = dspy.InputField(desc="The incongruity between visual and narrative.")

    # --- Outputs ---
    strategic_analysis: str = dspy.OutputField(
        desc="Analyze what caption style would best complement this GIF. Should it be relatable ('When you...'), observational, or something else? Consider the GIF's energy and pacing."
    )
    
    narrative_strategy: str = dspy.OutputField(
        desc="The chosen caption format. Examples: [Relatable 'When you...', 'Me when...', 'POV:', Internal Monologue, Observational Statement, ...]."
    )
    
    language_style: str = dspy.OutputField(
        desc="The specific 'Voice' or 'Register'. Examples: [Dry/Cynical, Deadpan, Self-Deprecating, Relatable Exhaustion, Overly Specific, ...]."
    )


# -------------------------------------------------------------------------
# MODULE 4: CONTENT WRITER (The Artist)
# -------------------------------------------------------------------------

class ContentWriter(dspy.Signature):
    """
    Executes the caption generation with a strict 20-word maximum limit.
    
    Role: You are a Meme Caption Writer. You craft the perfect short text to pair with a GIF.
    Goal: Write a caption that lands the humor in 20 words or less. Every word must earn its place. Caption must fit in with the GIF.z
    
    CRITICAL CONSTRAINT: Maximum 20 words. Shorter is usually better. The GIF does half the work - your caption just needs to reframe it.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The detailed description of the GIF for reference.")
    situation: str = dspy.InputField(desc="The reimagined humorous scenario.")
    focal_targets: str = dspy.InputField(desc="The visual elements targeted for humor.")
    cognitive_manipulation: str = dspy.InputField(desc="The recontextualization or twist being applied.")
    logical_mechanism: str = dspy.InputField(desc="The humor mechanism connecting visual to caption.")
    script_opposition: str = dspy.InputField(desc="The incongruity between what's seen and what's said.")
    strategic_analysis: str = dspy.InputField(desc="Analysis of why the chosen caption style works.")
    narrative_strategy: str = dspy.InputField(desc="The caption format constraint.")
    language_style: str = dspy.InputField(desc="The tone constraint.")
    writing_guidelines: str = dspy.InputField(
        desc="Guidelines for writing effective GIF captions: brevity, punch, and visual-text synergy."
    )

    # --- Outputs ---
    draft_setup: str = dspy.OutputField(
        desc="The framing or context-setting portion of the caption (if applicable). For 'When you...' formats, this is the setup clause."
    )
    
    draft_punchline: str = dspy.OutputField(
        desc="The payoff - the specific scenario or twist that makes viewers see the GIF differently."
    )
    
    final_joke: str = dspy.OutputField(
        desc="The complete caption. MUST be 20 words or fewer. Make every word count. The caption + GIF should be funnier than either alone. Avoid using tags and formatting as output should be plain text."
    )


# -------------------------------------------------------------------------
# MODULE 5: HUMOR JUDGE (The Critic)
# -------------------------------------------------------------------------

class HumorJudge(dspy.Signature):
    """
    Evaluates two GIF captions in a pairwise comparison to determine which creates the funnier meme.
    
    Role: You are a meme connoisseur and comedy critic who understands internet humor. You know what makes a caption go viral vs fall flat.
    
    Your job: Pick the caption that would get more shares, laughs, and 'this is so me' reactions when paired with the GIF. A caption over 20 words automatically loses.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(
        desc="The detailed description of the GIF that both captions are written for."
    )
    
    joke_candidate_1: str = dspy.InputField(desc="Caption Option A.")
    joke_candidate_2: str = dspy.InputField(desc="Caption Option B.")
    
    evaluation_criteria: str = dspy.InputField(
        desc="Criteria for judging GIF caption quality: brevity, visual-text synergy, relatability, and comedic punch."
    )

    # --- Outputs ---
    critique: str = dspy.OutputField(
        desc="First verify both captions are 20 words or fewer (over = automatic loss). Then analyze: Which better transforms the GIF? Which is more relatable/shareable? Which has better comedic timing? Does the caption add meaning or just describe?"
    )
    
    better_joke: Literal["Joke 1", "Joke 2"] = dspy.OutputField(
        desc="The winner. Return exactly 'Joke 1' or 'Joke 2'."
    )