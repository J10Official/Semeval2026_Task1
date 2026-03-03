# Official Guidelines
Guidelines for SemEval System Papers
This document is intended for participants in any of the SemEval shared tasks. It offers a template for how you, the author, can structure your system description paper to be as clear and complete as possible.

NOTES:

Be sure to use the official stylesheet and follow the SemEval paper requirements.
Your paper should stand on its own. Don’t assume that your reader is familiar with the task.
This document is just a guideline for structuring your paper. You can feel free to use a different structure if it makes more sense.
Some example system description papers from previous years that you can use as inspiration:
Best paper awardees at SemEval-2022
Best paper awardees at SemEval-2021
Best paper awardees at SemEval-2020
https://aclanthology.org/S16-1181
https://aclanthology.org/S14-2030
https://aclanthology.org/S18-1008
[multiple tasks] https://aclanthology.org/S07-1044
[multiple tasks] https://aclanthology.org/2022.semeval-1.233/
We would like to emphasize the importance of analysis of your system’s behavior beyond the overall scores. There will be a best paper award to recognize system papers with strong analysis.
Abstract
A few sentences summarizing the paper.
Introduction
What is the task about and why is it important? Be sure to mention the language(s) covered and cite the task overview paper. ~1 paragraph

What is the main strategy your system uses? ~1 paragraph

What did you discover by participating in this task? Key quantitative and qualitative results, such as how you ranked relative to other teams and what your system struggles with. ~1 paragraph

Have you released your code? Give a URL

Background
In your own words, summarize important details about the task setup: kind of input and output (give an example if possible); what datasets were used, including language, genre, and size. If there were multiple tracks, say which you participated in.

Here or in other sections, cite related work that will help the reader to understand your contribution and what aspects of it are novel.

System overview
Key algorithms and modeling decisions in your system; resources used beyond the provided training data; challenging aspects of the task and how your system addresses them. This may require multiple pages and several subsections, and should allow the reader to mostly reimplement your system’s algorithms.

Use equations and pseudocode if they help convey your original design decisions, as well as explaining them in English. If you are using a widely popular model/algorithm like logistic regression, an LSTM, or stochastic gradient descent, a citation will suffice—you do not need to spell out all the mathematical details.

Give an example if possible to describe concretely the stages of your algorithm.

If you have multiple systems/configurations, delineate them clearly.

This is likely to be the longest section of your paper.

Experimental setup
How data splits (train/dev/test) are used.

Key details about preprocessing, hyperparameter tuning, etc. that a reader would need to know to replicate your experiments. If space is limited, some of the details can go in an Appendix.

External tools/libraries used, preferably with version number and URL in a footnote.

Summarize the evaluation measures used in the task.

You do not need to devote much—if any—space to discussing the organization of your code or file formats.

Results
Main quantitative findings: How well did your system perform at the task according to official metrics? How does it rank in the competition?

Quantitative analysis: Ablations or other comparisons of different design decisions to better understand what works best. Indicate which data split is used for the analyses (e.g. in table captions). If you modify your system subsequent to the official submission, clearly indicate which results are from the modified system.

Error analysis: Look at some of your system predictions to get a feel for the kinds of mistakes it makes. If appropriate to the task, consider including a confusion matrix or other analysis of error subtypes—you may need to manually tag a small sample for this.

Conclusion
A few summary sentences about your system, results, and ideas for future work.
Acknowledgments
Anyone you wish to thank who is not an author, which may include grants and anonymous reviewers.
Appendix
Any low-level implementation details—rules and pre-/post-processing steps, features, hyperparameters, etc.—that would help the reader to replicate your system and experiments, but are not necessary to understand major design points of the system and experiments.

Any figures or results that aren’t crucial to the main points in your paper but might help an interested reader delve deeper.


---

SemEval
International Workshop on Semantic Evaluation
Paper Submission Requirements
This page describes requirements for papers submitted to and published in SemEval. For other questions about SemEval, see the FAQ.

There are two kinds of papers: system description papers, which every team participating in a task has the option to submit; and task description papers written by each set of task organizers. Papers accepted following peer review will be part of the official SemEval proceedings, and eligible for presentation at the workshop.

For your paper to be accepted and published, it must conform to the following guidelines. Contact your task organizers if you have questions about the guidelines.

Year-Specific Logistics
Dates, Submission Site
See the homepage for a detailed schedule with the submission deadline, acceptance notification date, and camera-ready submission deadline, as well as the link to the submission form.

Style Files
To write your paper, please use LaTeX style files issued by the conference SemEval is colocated with. The files contain details on the required page layout and formatting. Make sure to follow all those instructions—except the parts for which SemEval has separate requirements, specified below.

Length
Submissions for review
NEW Team participants are encouraged to only submit one paper regardless of number of tasks they participated in IF they use the same approach in both tasks.

NOTE: A task refers to a main task from the tasks page. It does not refer to subtasks within a single task.

System paper submissions for a single task can be up to 5 pages (regardless of number of subtasks the team participated in).

Teams participating in multiple tasks that use the same approach can add 2 additional pages per task to their system paper. e.g. If they participate in 2 tasks the limit is 7 pages and if they participate in 3 tasks the limit is 9 pages. NOTE: This is a change in submission requirements from previous years.

If the approach is different, or the team members differ, then separate papers should be written per task up to 5 pages each.

Task description papers (written by task organizers) can be up to 9 pages.

Acknowledgments, references, and appendices do NOT count toward page limits.

Camera-ready versions
Once accepted, your final paper may have an additional page so you can address reviewer feedback. Thus: 6 pages for a single-task system, 10 pages for task descriptions (not counting acknowledgments/references/appendices).

Title
SemEval paper titles follow a fixed template, where YYYY represents the year and N represents the task number:

System description papers for one task (any number of subtasks) are titled "Team Name at SemEval-YYYY Task N: Descriptive Title"
Note "at", not "@"
Note that "SemEval" and the year are separated by a hyphen and no spaces, e.g. "SemEval-2020"
Note that the task number is followed by a colon, not a dash
Note that the colon has a space after it but not before it
Authors are free to choose the Descriptive Title as they would a normal paper title; it may mention a particular question addressed, method used, or finding discussed in the paper
System description papers for multiple tasks are titled "Team Name at SemEval-YYYY Tasks N1 and N2: Descriptive Title" (2 tasks) or "Team Name at SemEval-YYYY Tasks N1, N2, and N3: Descriptive Title" (3 or more tasks)
(UPDATED) Task description papers are titled "SemEval-YYYY Task N: Task Name"
Authors
At SemEval, papers are not anonymous when submitted for review (for both system description papers and task description papers). Enter your names and affiliations on the paper.

Contents
System description papers should focus on:

Replicability: present all details that will allow someone else to replicate your system
Analysis: focus more on results and analysis and less on discussing rankings; report results on several runs of the system (even beyond the official submissions); present ablation experiments showing usefulness of different features and techniques; show comparisons with baselines.
Duplication: cite the task description paper; you can avoid repeating details of the task and data, however, briefly outlining the task and relevant aspects of the data is a good idea. (The official BibTeX citations for papers will not be released until the camera-ready submission period, so during the initial submission, please use some sort of placeholder citation.)
For a detailed outline, as well as links to some past system description papers, see these guidelines.

Task description papers should focus on:

Replicability: present all details that will allow someone else to replicate the data creation process and evaluation.
Analysis: focus more on results and analysis and less on discussing rankings
Summary of systems: Summarize the techniques, features, and resources used. Highlight what tended to work and what did not, across the systems.
Paper awards
Two overall awards are given to papers—one for organizers of a task and one for a team participating in a task. The awards are:

Best Task (task organizers): This award recognizes a task that stands out for making an important intellectual contribution to empirical computational semantics, as demonstrated by a creative, interesting, and scientifically rigorous dataset and evaluation design, and a well-written task overview paper.
Best Paper (task participants): This award recognizes a system description paper that advances our understanding of a problem and available solutions with respect to a task. It need not be the highest-scoring system in the task, but it must have a strong analysis component in the evaluation, as well as a clear and reproducible description of the problem, algorithms, and methodology.
SemEval-2020 winners: https://semeval.github.io/semeval2020-awards

SemEval-2021 winners: https://semeval.github.io/SemEval2021/awards

SemEval-2022 winners: https://semeval.github.io/SemEval2022/awards

SemEval-2023 winners: https://semeval.github.io/SemEval2023/awards

Reminders for final version
Ensure that author names are properly capitalized in START metadata and appear in the same order/spelling/capitalization as the PDF
Ensure that you have mentioned the language(s) of data used in the paper
If you are releasing code or data, include the URL in the paper
If the research raises ethical considerations (e.g. potential for misuse), these should be discussed in the paper
If a system paper, make sure to cite the task description paper
Published with GitHub Pages


# Task description


Subtasks
Subtask A: Text-based Humor Generation
Given a set of text-based constraints, generate a joke. This subtask will be conducted in English, Spanish, and Chinese.

Constraints:
Each generated joke must respect one of the following constraints, designed to make it difficult to simply retrieve existing jokes from the web:

Word Inclusion: Must contain two specific words (from a list of rare word combinations).
News Headline: Must be related to a given news article headline (it could be a punchline, or a joke inspired by the headline).
Subtask B: Multimodal Humor Generation with Images
This subtask explores humor in a multimodal context, combining visual inputs with text generation. This subtask is in English only.

Image-Based Caption Generation
Given an image in GIF format, generate a humorous caption (max 20 words) that enhances its comedic effect, in two variants:

Subtask B1: Only use the GIF image to inspire the caption.
Subtask B2: Use the GIF file and complete a given text prompt with humorous content.
Data and Resources
No labels
In line with the task's focus on genuine generation over memorization, and given the diversity of humor and the difficulty of evaluating jokes, we will not provide labeled data; instead, we will provide only inputs. Participants are encouraged to use any publicly available data, pre-trained models, API, or rule-based systems.

Get the Data
To download the data, please refer to our CodaBench page.

You can also download the baselines for the evaluation trial phase use, and the prompts used to create them.

For task A, the baseline consists of prompting the Gemini 2.5 Flash model with simple, task-specific prompts for both the two-word constraint and the news title. The prompts are written in English. For Spanish and Chinese, a simple indication of the expected output language is appended to the prompt. For tasks B1 and B2, the first frame of the GIF is extracted and provided to the same model, together with task-specific prompts.

Evaluation
The evaluation will be based on human preference judgments. We will use a pairwise comparison setup ("battle"), where annotators choose the funnier of the two generated texts produced under the same conditions. We will use a web interface inspired by Chatbot Arena to crowdsource annotations from anybody on the Internet. The systems will be ranked using an Elo-based leaderboard.

