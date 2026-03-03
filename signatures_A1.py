import dspy
from typing import Literal



# -------------------------------------------------------------------------
# ENGLISH
# -------------------------------------------------------------------------


WRITING_TIPS_A1_EN = """
### Tips for Writing Headline-Based Jokes:

* **ECONOMY OF LANGUAGE:** Cut every unnecessary word. If you can say it in 5 words instead of 10, do it. The funniest jokes are lean and mean.
* **SETUP MISDIRECTION:** The setup should read like a normal observation about the headline, NOT like "here comes a joke." Make it feel organic.
* **SURPRISE + INEVITABILITY:** The punchline should be unexpected yet feel obvious in retrospect. "I didn't see it coming, but of course!"
* **NO EXPLAINING:** Never explain the joke. If the punchline needs clarification, rewrite it. The reveal should be instant.
* **CONCRETE > ABSTRACT:** "He ate 47 pancakes" is funnier than "He ate a lot of pancakes." Specific numbers, names, and details land harder.
* **RHYTHM IS REAL:** The joke should have natural flow and cadence. The punchline should arrive at exactly the right moment.
* **TRUTH RESONATES:** The best comedy contains truth. People laugh when they recognize something real about the headline's subject.
* **CONVERSATIONAL TONE:** Write how people actually talk (unless the voice demands otherwise). Avoid academic or robotic phrasing.
* **COMMIT TO THE BIT:** Whatever voice/style you choose, go all in. Half-committed jokes fall flat.

### Red Flags (usually means the joke fails):
* Explaining the joke after the punchline
* Using "because" after the reveal (sign of over-explaining)
* Formulaic structure that feels template-generated
* Punchline that's just "imagine if X was Y" without actual wit
* Generic jokes that could apply to any headline
* Words that break the rhythm or flow
"""

EVALUATION_CRITERIA_A1_EN = """
### Evaluation Framework for Headline Jokes:

1. **THE LAUGH TEST:** Which joke would actually make someone laugh, smile, or react? Not which is "clever" - which is FUNNY?
2. **SURPRISE & SETUP:** Does the punchline genuinely surprise while still making sense? Or is it telegraphed/predictable?
3. **ECONOMY:** Is every word necessary? Excess words kill momentum. Tighter is almost always better.
4. **HEADLINE RELEVANCE:** Does it actually connect to THIS specific headline, or is it a generic joke slapped on top?
5. **NATURALNESS:** Does it sound like something a human would say? Or is it stiff, forced, or trying too hard?
6. **LOGICAL PUNCHLINE:** Does the punchline make sense? Absurdity is fine, but illogical nonsense isn't funny.
7. **TRUTH/RECOGNITION:** Do people recognize something real in it? The best jokes contain truth about the headline's subject.
8. **COMMITMENT:** Does it fully commit to the bit, or does it hedge/explain itself?

### Automatic Failures:
* Joke explains itself after the punchline
* Could be about literally any headline (not specific enough)
* Offensive without being clever
* Setup and punchline don't connect logically
"""


# -------------------------------------------------------------------------
# SPANISH
# -------------------------------------------------------------------------


WRITING_TIPS_A1_ES = """
### Consejos para Escribir Chistes Basados en Titulares:

* **ECONOMÍA DEL LENGUAJE:** Elimina cada palabra innecesaria. Si puedes decirlo en 5 palabras en vez de 10, hazlo. Los mejores chistes son concisos y directos.
* **MISDIRECCIÓN EN EL SETUP:** El setup debe leerse como una observación normal sobre el titular, NO como "aquí viene un chiste." Que fluya de forma orgánica.
* **SORPRESA + INEVITABILIDAD:** El remate debe ser inesperado pero parecer obvio en retrospectiva. "No lo vi venir, ¡pero claro que sí!"
* **NO EXPLIQUES:** Nunca expliques el chiste. Si el remate necesita aclaración, reescríbelo. La revelación debe ser instantánea.
* **CONCRETO > ABSTRACTO:** "Se comió 47 tacos" es más gracioso que "Se comió muchos tacos." Números específicos, nombres y detalles pegan más fuerte.
* **EL RITMO IMPORTA:** El chiste debe tener flujo y cadencia natural. El remate debe llegar en el momento exacto.
* **LA VERDAD RESUENA:** El mejor humor contiene verdad. La gente se ríe cuando reconoce algo real sobre el tema del titular.
* **TONO CONVERSACIONAL:** Escribe como la gente realmente habla (a menos que el estilo demande otra cosa). Evita frases académicas o robóticas.
* **COMPROMÉTETE CON EL BIT:** Sea cual sea el estilo que elijas, ve con todo. Los chistes a medias no funcionan.

### Señales de Alerta (usualmente significa que el chiste falla):
* Explicar el chiste después del remate
* Usar "porque" después de la revelación (señal de sobre-explicación)
* Estructura formulaica que se siente generada por plantilla
* Remate que es solo "imagina si X fuera Y" sin ingenio real
* Chistes genéricos que podrían aplicar a cualquier titular
* Palabras que rompen el ritmo o el flujo
"""

EVALUATION_CRITERIA_A1_ES = """
### Marco de Evaluación para Chistes de Titulares:

1. **LA PRUEBA DE LA RISA:** ¿Cuál chiste realmente haría reír, sonreír o reaccionar a alguien? No cuál es más "ingenioso" - ¿cuál es GRACIOSO?
2. **SORPRESA Y SETUP:** ¿El remate genuinamente sorprende mientras tiene sentido? ¿O es predecible/telegrafiado?
3. **ECONOMÍA:** ¿Cada palabra es necesaria? Las palabras de más matan el momentum. Más conciso casi siempre es mejor.
4. **RELEVANCIA AL TITULAR:** ¿Realmente conecta con ESTE titular específico, o es un chiste genérico pegado encima?
5. **NATURALIDAD:** ¿Suena como algo que diría un humano? ¿O es rígido, forzado, o se esfuerza demasiado?
6. **LÓGICA DEL REMATE:** ¿El remate tiene sentido? Lo absurdo está bien, pero el sinsentido ilógico no es gracioso.
7. **VERDAD/RECONOCIMIENTO:** ¿La gente reconoce algo real en él? Los mejores chistes contienen verdad sobre el tema del titular.
8. **COMPROMISO:** ¿Se compromete completamente con el bit, o se cubre/se explica a sí mismo?

### Fallos Automáticos:
* El chiste se explica a sí mismo después del remate
* Podría ser sobre literalmente cualquier titular (no es suficientemente específico)
* Ofensivo sin ser ingenioso
* El setup y el remate no conectan lógicamente
"""

# -------------------------------------------------------------------------
# CHINESE
# -------------------------------------------------------------------------


WRITING_TIPS_A1_ZH = """
### 新闻标题笑话写作技巧：

* **语言精炼：** 删除所有不必要的字。能用五个字说清楚，就不要用十个。最好笑的段子都是精简有力的。
* **铺垫要自然：** 铺垫应该像普通评论一样自然，不要让人一看就知道"笑话来了"。要不露痕迹。
* **意外+必然：** 抖包袱要出人意料，但事后一想又觉得理所当然。"没想到，但确实是这样！"
* **不要解释：** 永远不要解释笑话。如果包袱需要解释，就重写。笑点要一击即中。
* **具体胜于抽象：** "他吃了47个包子"比"他吃了很多包子"更好笑。具体的数字、名字和细节更有冲击力。
* **节奏很重要：** 笑话要有自然的节奏感。包袱要在恰到好处的时机抖出来——不早不晚。
* **真实引共鸣：** 最好的幽默包含真实。当人们认出现实中的某些东西时，才会发笑。
* **口语化表达：** 用人们实际说话的方式写（除非风格另有要求）。避免书面语或机械化的表达。
* **全力以赴：** 无论选择什么风格，都要全情投入。三心二意的笑话没人笑。

### 危险信号（通常意味着笑话失败）：
* 在包袱后面解释笑话
* 在揭示后使用"因为"（过度解释的信号）
* 公式化结构，感觉像模板生成的
* 包袱只是"想象如果X是Y"，没有真正的机智
* 可以套用到任何标题的通用笑话
* 打断节奏或流畅度的词语
"""

EVALUATION_CRITERIA_A1_ZH = """
### 标题笑话评估框架：

1. **笑果测试：** 哪个笑话真的能让人笑、微笑或有反应？不是哪个更"聪明"——而是哪个更好笑？
2. **意外与铺垫：** 包袱是真的出人意料同时又合情合理？还是一眼就能猜到？
3. **精炼度：** 每个字都必要吗？多余的字会拖垮节奏。越精简通常越好。
4. **标题相关性：** 真的与这个具体标题相关，还是随便贴上去的通用笑话？
5. **自然度：** 听起来像人说的话吗？还是生硬、牵强、太刻意？
6. **逻辑性：** 包袱合理吗？荒诞可以，但不合逻辑的胡说不好笑。
7. **真实/共鸣：** 人们能在其中认出真实的东西吗？最好的笑话包含关于标题主题的真相。
8. **投入度：** 完全投入这个梗，还是在犹豫/自我解释？

### 自动失败：
* 笑话在包袱后自我解释
* 可以套用到任何标题（不够具体）
* 冒犯但不机智
* 铺垫和包袱逻辑上不连贯
"""


# -------------------------------------------------------------------------
# MODULE 1: CONTEXT ENRICHMENT (The Analyst)
# -------------------------------------------------------------------------

class ContextEnricher(dspy.Signature):
    """
    Analyzes a news headline to extract the factual subtext, implicit assumptions, and cultural context required to construct a grounded joke.
    
    Role: You are a comedy researcher analyzing the raw material before writing.
    Goal: Identify the 'Situation' and potential targets without trying to write the joke yet, just setup the background.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(
        desc="The news headline to be analyzed."
    )
    
    target_language_and_culture: Literal["English", "Spanish", "Chinese"] = dspy.InputField(
        desc="The target language and cultural context for joke generation."
    )

    # --- Outputs ---
    situation: str = dspy.OutputField(
        desc="Elaborate on the headline. Explain the factual reality and subtext. What is actually happening? What are the unsaid implications?"
    )
    
    semantic_associations: list[str] = dspy.OutputField(
        desc="List specific stereotypes, properties, cultural references, or associations linked to the key terms of the headline. Include the term and its associations."
    )


# -------------------------------------------------------------------------
# MODULE 2: HUMOR ARCHITECT (The Brain)
# -------------------------------------------------------------------------

class HumorArchitect(dspy.Signature):
    """
    Deconstructs the context into a formal GTVH (General Theory of Verbal Humor) structural blueprint.
    
    Role: You are the Logic Engine and Lead Comedy Writer. You do not write the final prose; you design the cognitive mechanism that makes the joke work. You find the 'incongruity' that causes the laughter.
    Goal: Define the abstract 'Script Opposition' (SO) and 'Logical Mechanism' (LM) that will serve as the core DNA of the joke.
    
    Tips for Genuine Humor:
    - Find REAL incongruities that humans naturally find funny, not forced academic constructs
    - The best jokes have an element of truth or recognition - what makes us laugh is often what we've all thought but never said
    - Avoid over-complicated logic - if the mechanism requires a PhD to understand, it won't land
    - Surprise is key: the opposing script should be unexpected but make perfect sense in hindsight
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The original headline used as reference.")
    situation: str = dspy.InputField(desc="The grounded reality and context surrounding the scenario.")
    semantic_associations: list[str] = dspy.InputField(desc="Stereotypes, properties, cultural references, or associations linked to key terms. Use these to inform your target selection.")
    target_language_and_culture: Literal["English", "Spanish", "Chinese"] = dspy.InputField(
        desc="The target language and cultural context for joke generation."
    )

    # --- Outputs ---
    focal_targets: str = dspy.OutputField(
        desc="The specific 'Hinge' concepts you've chosen to target. Which exact words, persons, or ideas from the input will be the victims or pivot points of the joke? Determine this yourself based on what has the most comedic potential."
    )
    
    cognitive_manipulation: str = dspy.OutputField(
        desc="A precise, one-sentence instruction on how to twist the focal targets. Describe the unique semantic or logical shift applied in this specific context. Do not use generic labels like 'Exaggeration' alone; explicitly define the mental operation."
    )
    
    logical_mechanism: str = dspy.OutputField(
        desc="The GTVH Label for the manipulation. Examples: [False Analogy, Literal Interpretation, Role Reversal, Exaggeration, Garden Path, Juxtaposition, Parallelism, Ignoring the Obvious, Reasoning from False Premises, Missing the Point, Over-specificity, Recontextualization, Meta-Humor, Irony, Double Entendre, Circular Logic, Absurdity]."
    )
    
    expected_script: str = dspy.OutputField(
        desc="The 'Normal' expectation the reader has when reading the setup."
    )
    
    opposing_script: str = dspy.OutputField(
        desc="The 'Abnormal' or 'Hidden' reality revealed by the punchline."
    )
    
    script_opposition: str = dspy.OutputField(
        desc="The abstract semantic axis on which these two scripts clash. Format: [Concept A] vs. [Concept B]. Derive the opposition strictly from the content above; do not default to generic high-level pairs."
    )


# -------------------------------------------------------------------------
# MODULE 3: DELIVERY STRATEGIST (The Director)
# -------------------------------------------------------------------------

class DeliveryStrategist(dspy.Signature):
    """
    Determines the best Narrative Strategy and Language to deliver the humor.
    
    Role: You are a Comedy Director. You analyze the logic provided and decide *how* to perform it.
    Goal: Ensure the delivery format supports the Logical Mechanism (e.g., don't use a visual format for a verbal pun).
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The original headline used as reference.")
    situation: str = dspy.InputField(desc="The grounded reality and context surrounding the scenario.")
    focal_targets: str = dspy.InputField(desc="The concepts being targeted.")
    logical_mechanism: str = dspy.InputField(desc="The abstract rule defined by the Architect to connect the expected and opposing scripts.")
    script_opposition: str = dspy.InputField(desc="The incongruity being portrayed by two opposing scripts.")
    target_language_and_culture: Literal["English", "Spanish", "Chinese"] = dspy.InputField(
        desc="The target language and cultural context for joke generation."
    )

    # --- Outputs ---
    strategic_analysis: str = dspy.OutputField(
        desc="Analyze the compatibility between the Logical Mechanism and potential delivery formats. Why would one format work better than another for this specific logic?"
    )
    
    narrative_strategy: str = dspy.OutputField(
        desc="The chosen delivery format. Examples: [Dialogue, Fake News Snippet, One-Liner, Q&A, Breaking News, ...]."
    )
    
    language_style: str = dspy.OutputField(
        desc="The specific 'Voice' or 'Register'. Examples: [Dry/Cynical, Deadpan, Sarcastic, Hyperbolic/Excited, Passive-Aggressive, ...]."
    )


# -------------------------------------------------------------------------
# MODULE 4: CONTENT WRITER (The Artist)
# -------------------------------------------------------------------------

class ContentWriter(dspy.Signature):
    """
    Executes the joke generation based on strict GTVH constraints.
    
    Role: You are a Comedy Writer. You take the blueprint and write the final prose.
    Goal: Write a joke that lands the specific 'Script Opposition' using the chosen 'Voice' and 'Strategy'.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(desc="The original headline used as reference.")
    situation: str = dspy.InputField(desc="The grounded reality and context surrounding the scenario.")
    focal_targets: str = dspy.InputField(desc="The primary targets of the joke.")
    cognitive_manipulation: str = dspy.InputField(desc="The precise semantic or logical shift to apply to the focal target.")
    logical_mechanism: str = dspy.InputField(desc="The abstract rule defined by the Architect to connect the expected and opposing scripts.")
    script_opposition: str = dspy.InputField(desc="The incongruity being portrayed by two opposing scripts.")
    strategic_analysis: str = dspy.InputField(desc="Analysis of why the chosen format works for this specific logic.")
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
        desc="The build-up. Establish the 'Expected Script' using the requested 'Language Style'. Draw the audience in."
    )
    
    draft_punchline: str = dspy.OutputField(
        desc="The reveal. Switch to the 'Opposing Script' via the 'Logical Mechanism'."
    )
    
    final_joke: str = dspy.OutputField(
        desc="The complete, polished joke text combining setup and punchline. Ensure timing and flow are perfect. Avoid using tags and formatting as output should be plain text."
    )


# -------------------------------------------------------------------------
# MODULE 5: HUMOR JUDGE (The Critic)
# -------------------------------------------------------------------------

class HumorJudge(dspy.Signature):
    """
    Evaluates two jokes in a pairwise comparison to determine which one will actually make humans laugh.
    
    Role: You are an expert comedy critic who has seen thousands of jokes. You know the difference between jokes that work in theory and jokes that get real laughs from real audiences.
    
    Your job: Pick the joke that would get the bigger laugh from a real human audience, not the one that sounds more "correct" or academic.
    """
    
    # --- Inputs ---
    original_input: str = dspy.InputField(
        desc="The original headline the jokes are based on. Jokes must be relevant to this."
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
        desc="Analyze both jokes using the evaluation framework. Highlight strengths and weaknesses in humor, relevance, delivery, and cultural fit."
    )
    
    better_joke: Literal["Joke 1", "Joke 2"] = dspy.OutputField(
        desc="The winner. Return exactly 'Joke 1' or 'Joke 2'."
    )
