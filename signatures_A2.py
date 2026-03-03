import dspy
from typing import Literal



# -------------------------------------------------------------------------
# ENGLISH
# -------------------------------------------------------------------------


WRITING_TIPS_A2_EN = """
### Tips for Writing Word-Inclusion Jokes:

* **WORDS MUST FEEL NECESSARY:** The two required words should feel like they BELONG in the joke - not shoehorned in. If removing either word would improve the joke, you've failed.
* **FIND THE COLLISION:** The humor often comes from making two unrelated words collide in an unexpected scenario. Find where they naturally crash together.
* **ECONOMY OF LANGUAGE:** Cut every unnecessary word. The required words should be load-bearing, not decorative.
* **SURPRISE + INEVITABILITY:** The punchline should be unexpected yet feel obvious in retrospect. Both words should contribute to this revelation.
* **NO EXPLAINING:** Never explain the joke. If you need to clarify why the words are there, rewrite it.
* **CONCRETE > ABSTRACT:** Specific details land harder. Use the words in concrete, vivid scenarios.
* **NATURAL FLOW:** The sentence should read smoothly. If the required words create awkward phrasing, find a different angle.
* **TRUTH RESONATES:** Ground the joke in recognizable reality, even if absurd.
* **COMMIT TO THE BIT:** Whatever scenario justifies both words, commit fully to that reality.

### Red Flags (usually means the joke fails):
* Words feel forced or awkwardly inserted
* Either word could be removed without hurting the joke
* Explaining why the words are together
* Obvious "I needed to use these words" energy
* Sacrificing humor quality just to include the words
* Unnatural sentence structure to accommodate words
"""

EVALUATION_CRITERIA_A2_EN = """
### Evaluation Framework for Word-Inclusion Jokes:

1. **WORD INTEGRATION:** Do BOTH required words appear naturally? Do they feel essential to the joke, not forced?
2. **THE LAUGH TEST:** Which joke would actually make someone laugh? Not which cleverly includes the words - which is FUNNY?
3. **SURPRISE & SETUP:** Does the punchline genuinely surprise while making both words feel inevitable?
4. **ECONOMY:** Is every word necessary? Are the required words load-bearing or just present?
5. **NATURAL FLOW:** Does the joke read smoothly, or is the sentence structure awkward to accommodate the words?
6. **LOGICAL SENSE:** Does the scenario that brings both words together make sense (even if absurd)?
7. **CREATIVE CONNECTION:** Is there a clever reason these two words appear together, or just coincidence?
8. **COMMITMENT:** Does it fully commit to the scenario, or does it feel like a word-inclusion exercise?

### Automatic Failures:
* Missing one or both required words
* Words present but clearly forced/awkward
* Joke would be better without one of the required words
* No logical connection between the words and the humor
"""


# -------------------------------------------------------------------------
# SPANISH
# -------------------------------------------------------------------------


WRITING_TIPS_A2_ES = """
### Consejos para Escribir Chistes con Inclusión de Palabras:

* **LAS PALABRAS DEBEN SENTIRSE NECESARIAS:** Las dos palabras requeridas deben PERTENECER al chiste - no estar metidas a la fuerza. Si quitar cualquier palabra mejoraría el chiste, has fallado.
* **ENCUENTRA LA COLISIÓN:** El humor frecuentemente viene de hacer que dos palabras no relacionadas choquen en un escenario inesperado. Encuentra dónde chocan naturalmente.
* **ECONOMÍA DEL LENGUAJE:** Elimina cada palabra innecesaria. Las palabras requeridas deben ser estructurales, no decorativas.
* **SORPRESA + INEVITABILIDAD:** El remate debe ser inesperado pero obvio en retrospectiva. Ambas palabras deben contribuir a esta revelación.
* **NO EXPLIQUES:** Nunca expliques el chiste. Si necesitas aclarar por qué las palabras están ahí, reescríbelo.
* **CONCRETO > ABSTRACTO:** Los detalles específicos pegan más fuerte. Usa las palabras en escenarios concretos y vívidos.
* **FLUJO NATURAL:** La oración debe leerse suavemente. Si las palabras requeridas crean frases torpes, busca otro ángulo.
* **LA VERDAD RESUENA:** Ancla el chiste en realidad reconocible, aunque sea absurda.
* **COMPROMÉTETE CON EL BIT:** Sea cual sea el escenario que justifique ambas palabras, comprométete completamente con esa realidad.

### Señales de Alerta (usualmente significa que el chiste falla):
* Las palabras se sienten forzadas o insertadas torpemente
* Cualquiera de las palabras podría eliminarse sin afectar el chiste
* Explicar por qué las palabras están juntas
* Energía obvia de "necesitaba usar estas palabras"
* Sacrificar la calidad del humor solo por incluir las palabras
* Estructura de oración antinatural para acomodar palabras
"""

EVALUATION_CRITERIA_A2_ES = """
### Marco de Evaluación para Chistes con Inclusión de Palabras:

1. **INTEGRACIÓN DE PALABRAS:** ¿AMBAS palabras requeridas aparecen naturalmente? ¿Se sienten esenciales para el chiste, no forzadas?
2. **LA PRUEBA DE LA RISA:** ¿Cuál chiste realmente haría reír a alguien? No cuál incluye las palabras ingeniosamente - ¿cuál es GRACIOSO?
3. **SORPRESA Y SETUP:** ¿El remate genuinamente sorprende mientras hace que ambas palabras se sientan inevitables?
4. **ECONOMÍA:** ¿Cada palabra es necesaria? ¿Las palabras requeridas son estructurales o solo están presentes?
5. **FLUJO NATURAL:** ¿El chiste se lee suavemente, o la estructura de la oración es torpe para acomodar las palabras?
6. **SENTIDO LÓGICO:** ¿El escenario que une ambas palabras tiene sentido (aunque sea absurdo)?
7. **CONEXIÓN CREATIVA:** ¿Hay una razón ingeniosa por la que estas dos palabras aparecen juntas, o es solo coincidencia?
8. **COMPROMISO:** ¿Se compromete completamente con el escenario, o se siente como un ejercicio de inclusión de palabras?

### Fallos Automáticos:
* Falta una o ambas palabras requeridas
* Palabras presentes pero claramente forzadas/torpes
* El chiste sería mejor sin una de las palabras requeridas
* Sin conexión lógica entre las palabras y el humor
"""


# -------------------------------------------------------------------------
# CHINESE
# -------------------------------------------------------------------------


WRITING_TIPS_A2_ZH = """
### 指定词汇笑话写作技巧：

* **词汇必须自然：** 两个指定词汇应该自然地属于笑话——不是硬塞进去的。如果去掉任何一个词笑话会更好，那就失败了。
* **找到碰撞点：** 幽默通常来自让两个不相关的词在意想不到的场景中碰撞。找到它们自然相遇的地方。
* **语言精炼：** 删除所有不必要的字。指定词汇应该是承重结构，不是装饰品。
* **意外+必然：** 包袱要出人意料，但事后一想又觉得理所当然。两个词都应该为这个揭示做贡献。
* **不要解释：** 永远不要解释笑话。如果需要解释为什么这两个词在一起，就重写。
* **具体胜于抽象：** 具体的细节更有冲击力。把词汇用在具体、生动的场景中。
* **自然流畅：** 句子要读起来顺畅。如果指定词汇造成别扭的表达，换个角度。
* **真实引共鸣：** 把笑话扎根于可识别的现实，即使是荒诞的现实。
* **全力以赴：** 无论什么场景能让两个词合理出现，都要完全投入那个现实。

### 危险信号（通常意味着笑话失败）：
* 词汇感觉强行插入或别扭
* 任何一个词都可以删掉而不影响笑话
* 解释为什么这两个词在一起
* 明显的"我需要用这些词"的感觉
* 为了包含词汇而牺牲笑话质量
* 为了容纳词汇而使用不自然的句子结构
"""

EVALUATION_CRITERIA_A2_ZH = """
### 指定词汇笑话评估框架：

1. **词汇整合：** 两个指定词汇都自然出现了吗？它们感觉是笑话必不可少的，而不是强行加入的？
2. **笑果测试：** 哪个笑话真的能让人笑？不是哪个巧妙地包含了词汇——而是哪个更好笑？
3. **意外与铺垫：** 包袱是真的出人意料，同时让两个词都感觉必然？
4. **精炼度：** 每个字都必要吗？指定词汇是承重结构还是只是存在？
5. **自然流畅：** 笑话读起来顺畅，还是句子结构别扭以容纳词汇？
6. **逻辑性：** 把两个词联系在一起的场景合理吗（即使是荒诞的）？
7. **创意连接：** 这两个词出现在一起有巧妙的理由，还是只是巧合？
8. **投入度：** 完全投入场景，还是感觉像是一个词汇包含练习？

### 自动失败：
* 缺少一个或两个指定词汇
* 词汇存在但明显强行/别扭
* 去掉其中一个指定词汇笑话会更好
* 词汇和幽默之间没有逻辑联系
"""


# -------------------------------------------------------------------------
# SIGNATURES FOR TASK A2: WORD INCLUSION HUMOR GENERATION
# Generate jokes that must include two specific words
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
# MODULE 1: CONTEXT ENRICHMENT (The Analyst)
# -------------------------------------------------------------------------

class ContextEnricher(dspy.Signature):
    """
    Analyzes two unrelated words to discover a plausible scenario, shared context, or narrative that naturally brings them together for comedic potential.
    
    Role: You are a comedy researcher finding the unlikely connection between two disparate words.
    Goal: Identify a 'Situation' (SI) that forces these two words into the same context, and explore the absurdity or humor potential in their pairing.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(
        desc="The two words that must appear in the joke."
    )
    
    target_language_and_culture: Literal["English", "Spanish", "Chinese"] = dspy.InputField(
        desc="The target language and cultural context for joke generation."
    )

    # --- Outputs ---
    situation: str = dspy.OutputField(
        desc="Describe a list of scenarios, settings, or narratives that naturally force both words to coexist. What situations makes these two words collide? Why would someone encounter both in the same context?"
    )
    
    semantic_associations: list[str] = dspy.OutputField(
        desc="List specific stereotypes, properties, typical uses, or cultural connotations for each word. Include what each word evokes, its common contexts, and any double meanings."
    )


# -------------------------------------------------------------------------
# MODULE 2: HUMOR ARCHITECT (The Brain)
# -------------------------------------------------------------------------

class HumorArchitect(dspy.Signature):
    """
    Deconstructs the word pairing into a formal GTVH (General Theory of Verbal Humor) structural blueprint.
    
    Role: You are the Logic Engine and Lead Comedy Writer. You do not write the final prose; you design the cognitive mechanism that makes the joke work. You find the 'incongruity' in the forced word combination.
    Goal: Define the abstract 'Script Opposition' (SO) and 'Logical Mechanism' (LM) that will serve as the core DNA of the joke using both words.
    
    Tips for Genuine Humor:
    - The humor often comes from the UNEXPECTED connection between the two words
    - Find what's absurd, ironic, or surprising about these words appearing together
    - The best jokes make the forced pairing feel natural in retrospect
    - Exploit double meanings, homonyms, or unexpected interpretations of either word
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The two words that must appear in the joke.")
    situation: str = dspy.InputField(desc="The scenarios or contexts that brings both words together.")
    semantic_associations: list[str] = dspy.InputField(desc="Stereotypes, properties, typical uses, or cultural connotations for each word. Use these to inform your target selection.")
    target_language_and_culture: Literal["English", "Spanish", "Chinese"] = dspy.InputField(
        desc="The target language and cultural context for joke generation."
    )

    # --- Outputs ---
    focal_targets: str = dspy.OutputField(
        desc="The specific 'Hinge' concepts you've chosen to target. Which word(s), their meanings, or their interaction will be the pivot point of the joke? Both words must be leveraged. Determine this yourself based on what has the most comedic potential."
    )
    
    cognitive_manipulation: str = dspy.OutputField(
        desc="A precise, one-sentence instruction on how to twist the word pairing. Describe the unique semantic or logical shift that makes their combination funny. Do not use generic labels alone; explicitly define the mental operation."
    )
    
    logical_mechanism: str = dspy.OutputField(
        desc="The GTVH Label for the manipulation. Examples: [False Analogy, Literal Interpretation, Role Reversal, Exaggeration, Garden Path, Juxtaposition, Parallelism, Ignoring the Obvious, Reasoning from False Premises, Missing the Point, Over-specificity, Recontextualization, Meta-Humor, Irony, Double Entendre, Circular Logic, Absurdity]."
    )
    
    expected_script: str = dspy.OutputField(
        desc="The 'Normal' expectation when encountering either word individually or the setup scenario."
    )
    
    opposing_script: str = dspy.OutputField(
        desc="The 'Abnormal' or 'Hidden' reality revealed when both words collide in the punchline."
    )
    
    script_opposition: str = dspy.OutputField(
        desc="The abstract semantic axis on which these two scripts clash. Format: [Concept A] vs. [Concept B]. Derive the opposition from the word pairing's inherent tension."
    )


# -------------------------------------------------------------------------
# MODULE 3: DELIVERY STRATEGIST (The Director)
# -------------------------------------------------------------------------

class DeliveryStrategist(dspy.Signature):
    """
    Determines the best Narrative Strategy (NS) and Language (LA) to deliver the word-inclusion humor.
    
    Role: You are a Comedy Director. You analyze the logic provided and decide *how* to perform it.
    Goal: Ensure the delivery format naturally incorporates both words and supports the Logical Mechanism.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The two words that must appear in the joke.")
    situation: str = dspy.InputField(desc="The scenarios that brings both words together.")
    focal_targets: str = dspy.InputField(desc="The word(s) or concepts being targeted.")
    logical_mechanism: str = dspy.InputField(desc="The abstract rule defined by the Architect to connect the expected and opposing scripts.")
    script_opposition: str = dspy.InputField(desc="The incongruity being portrayed by two opposing scripts.")
    target_language_and_culture: Literal["English", "Spanish", "Chinese"] = dspy.InputField(
        desc="The target language and cultural context for joke generation."
    )

    # --- Outputs ---
    strategic_analysis: str = dspy.OutputField(
        desc="Analyze how to naturally weave both words into the joke. Which format allows both words to appear organically without feeling forced?"
    )
    
    narrative_strategy: str = dspy.OutputField(
        desc="The chosen delivery format. Examples: [Dialogue, One-Liner, Third-Person Narrative, Q&A, Fake News Snippet, ...]."
    )
    
    language_style: str = dspy.OutputField(
        desc="The specific 'Voice' or 'Register'. Examples: [Dry/Cynical, Deadpan, Sarcastic, Whimsical, Passive-Aggressive, ...]."
    )

# -------------------------------------------------------------------------
# MODULE 4: CONTENT WRITER (The Artist)
# -------------------------------------------------------------------------

class ContentWriter(dspy.Signature):
    """
    Executes the joke generation ensuring both required words appear naturally in the final text.
    
    Role: You are a Comedy Writer. You take the blueprint and write the final prose.
    Goal: Write a joke that lands the specific 'Script Opposition' using the chosen 'Voice' and 'Strategy', while MANDATORY including both words.
    
    CRITICAL CONSTRAINT: Both words from the original input MUST appear in the final joke. The joke fails if either word is missing.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The two words that MUST appear in the final joke.")
    situation: str = dspy.InputField(desc="The scenarios that brings both words together.")
    focal_targets: str = dspy.InputField(desc="The primary targets of the joke.")
    cognitive_manipulation: str = dspy.InputField(desc="The precise semantic or logical shift to apply to the focal target.")
    logical_mechanism: str = dspy.InputField(desc="The abstract rule defined by the Architect to connect the expected and opposing scripts.")
    script_opposition: str = dspy.InputField(desc="The incongruity being portrayed by two opposing scripts.")
    strategic_analysis: str = dspy.InputField(desc="Analysis of how to naturally incorporate both words.")
    narrative_strategy: str = dspy.InputField(desc="The format constraint")
    language_style: str = dspy.InputField(desc="The tone constraint")
    target_language_and_culture: Literal["English", "Spanish", "Chinese"] = dspy.InputField(
        desc="The target language and cultural context for joke generation."
    )
    writing_guidelines: str = dspy.InputField(
        desc="Language-specific and cultural guidelines for writing effective jokes in the target language."
    )

    # --- Outputs ---
    draft_setup: str = dspy.OutputField(
        desc="The build-up. Establish the scenario using the requested 'Language Style'. At least one required word should appear here naturally."
    )
    
    draft_punchline: str = dspy.OutputField(
        desc="The reveal. Switch to the 'Opposing Script' via the 'Logical Mechanism'. The remaining required word(s) should land here."
    )
    
    final_joke: str = dspy.OutputField(
        desc="The complete, polished joke text combining setup and punchline. VERIFY: Both required words must appear. Ensure timing and flow are perfect. Avoid using tags and formatting as output should be plain text."
    )


# -------------------------------------------------------------------------
# MODULE 5: HUMOR JUDGE (The Critic)
# -------------------------------------------------------------------------

class HumorJudge(dspy.Signature):
    """
    Evaluates two word-inclusion jokes in a pairwise comparison to determine which one will actually make humans laugh.
    
    Role: You are an expert comedy critic who has seen thousands of jokes. You know the difference between jokes that work in theory and jokes that get real laughs from real audiences.
    
    Your job: Pick the joke that would get the bigger laugh from a real human audience. Additionally, verify that both required words appear in each joke - a missing word is an automatic disqualification.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(
        desc="The two words that must appear in each joke. Both jokes should contain these words."
    )
    
    joke_candidate_1: str = dspy.InputField(desc="Option A.")
    joke_candidate_2: str = dspy.InputField(desc="Option B.")
    
    target_language_and_culture: Literal["English", "Spanish", "Chinese"] = dspy.InputField(
        desc="The target language and cultural context for evaluation."
    )
    
    evaluation_criteria: str = dspy.InputField(
        desc="Language-specific and culturally-appropriate evaluation framework for judging humor quality."
    )

    # --- Outputs ---
    critique: str = dspy.OutputField(
        desc="First verify both required words appear in each joke. Then analyze both jokes using the evaluation framework. Highlight how naturally the words are integrated, humor quality, and delivery. A joke missing either word automatically loses."
    )
    
    better_joke: Literal["Joke 1", "Joke 2"] = dspy.OutputField(
        desc="The winner. Return exactly 'Joke 1' or 'Joke 2'."
    )