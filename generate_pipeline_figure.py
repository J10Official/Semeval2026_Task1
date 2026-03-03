"""
Generate a pipeline trace figure for the paper.
Shows the full 5-module pipeline execution for headline en_2009,
including all 4 candidate branches with diverse logical mechanisms.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import textwrap

# ─── Configuration ───────────────────────────────────────────────────────────

DPI = 200
FIG_W, FIG_H = 18, 24

# Colors
C_INPUT    = "#2C3E50"   # dark blue-grey
C_CONTEXT  = "#2980B9"   # blue
C_ARCH     = "#E67E22"   # orange
C_STRAT    = "#8E44AD"   # purple
C_CONTENT  = "#27AE60"   # green
C_JUDGE    = "#C0392B"   # red
C_WINNER   = "#F1C40F"   # gold
C_BG       = "#FAFAFA"
C_TEXT     = "#1A1A1A"
C_LIGHT    = "#FFFFFF"

FONT_TITLE = 11
FONT_LABEL = 9.5
FONT_BODY  = 7.5
FONT_SMALL = 6.8

# ─── Data ────────────────────────────────────────────────────────────────────

HEADLINE = "I stayed at one of only two hotels in Malta's Silent City"
ITEM_ID = "en_2009"

SITUATION = (
    "This headline describes a travel experience — staying in a hotel in Mdina, "
    "Malta, known as the \"Silent City.\" The \"only two hotels\" part suggests "
    "Mdina is small, exclusive, and not overly commercialized. There's a subtle "
    "suggestion that the place is very tourist-focused despite attempts to "
    "maintain a 'silent' atmosphere."
)

ASSOCIATIONS = [
    "Malta: Mediterranean island, history, sunshine, tourism, small size",
    "Silent City (Mdina): quiet, medieval, walled city, restrictive access",
    "Hotels: comfort, convenience, sometimes impersonal",
    "Two: limited options, scarcity, feeling 'in the know'",
]

CANDIDATES = [
    {
        "num": 1,
        "mechanism": "Double Entendre",
        "opposition": "Ambient Quietude vs.\nSocial Silence/Awkwardness",
        "strategy": "Q&A  ·  Dry/Cynical",
        "joke": (
            "I just got back from Malta. Stayed in Mdina, the \"Silent City.\" "
            "Turns out \"silent\" doesn't mean peaceful. It means nobody talks "
            "to each other in the hotel. Two hotels in the whole city, and "
            "still zero socializing."
        ),
    },
    {
        "num": 2,
        "mechanism": "Recontextualization",
        "opposition": "Natural Quiet vs.\nImposed/Artificial Silence",
        "strategy": "Fake News  ·  Deadpan",
        "joke": (
            "BREAKING: Mdina, Malta — authorities are reporting strict noise control "
            "at the \"Silent City\" hotels. Any audible breathing above 15 decibels "
            "will result in eviction and a mandatory course in monastic vow of silence."
        ),
    },
    {
        "num": 3,
        "mechanism": "Ignoring the Obvious",
        "opposition": "Absolute Quiet vs.\nRelative Quiet",
        "strategy": "Dialogue  ·  Dry/Cynical",
        "joke": (
            "Tourist: Mdina is exactly what I needed. The brochure said 'Silent City'. "
            "Absolute serenity.  Local: Right. You get used to the sound of keycards "
            "swiping and people complaining about the breakfast buffet."
        ),
    },
    {
        "num": 4,
        "mechanism": "Irony",
        "opposition": "Peaceful Solitude vs.\nCompetitive Restraint",
        "strategy": "Dialogue  ·  Dry/Cynical",
        "joke": (
            "Tourist: \"Malta's Silent City is… well, silent. I stayed at one of only "
            "two hotels there.\"  Local: \"Oh yeah, they're locked in a cold war. "
            "Neither wants to be the first to offer free breakfast.\""
        ),
        "winner": True,
    },
]


# ─── Helper Functions ────────────────────────────────────────────────────────

def draw_box(ax, x, y, w, h, color, title, body_lines, title_size=FONT_LABEL,
             body_size=FONT_BODY, alpha=0.92, title_color="white", radius=0.015):
    """Draw a rounded box with title bar and body text."""
    # Body box
    body_box = FancyBboxPatch(
        (x, y - h), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=C_LIGHT, edgecolor=color, linewidth=1.8, alpha=alpha,
        transform=ax.transAxes, zorder=2,
    )
    ax.add_patch(body_box)

    # Title bar
    title_h = 0.022
    title_box = FancyBboxPatch(
        (x, y - title_h), w, title_h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=color, edgecolor=color, linewidth=1.5,
        transform=ax.transAxes, zorder=3,
    )
    ax.add_patch(title_box)

    # Title text
    ax.text(x + w / 2, y - title_h / 2, title,
            ha="center", va="center", fontsize=title_size,
            fontweight="bold", color=title_color, transform=ax.transAxes, zorder=4)

    # Body text
    text_y = y - title_h - 0.008
    for line in body_lines:
        ax.text(x + 0.008, text_y, line,
                ha="left", va="top", fontsize=body_size,
                color=C_TEXT, transform=ax.transAxes, zorder=4,
                fontfamily="monospace" if line.startswith("  ") else "sans-serif")
        text_y -= 0.014

    return y - h


def draw_arrow(ax, x1, y1, x2, y2, color="#666666", lw=1.2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->,head_width=0.25,head_length=0.15",
                                color=color, lw=lw),
                zorder=1)


def wrap(text, width=65):
    return textwrap.fill(text, width=width)


# ─── Main Figure ─────────────────────────────────────────────────────────────

fig, ax = plt.subplots(1, 1, figsize=(FIG_W, FIG_H), dpi=DPI)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
fig.patch.set_facecolor(C_BG)
ax.set_facecolor(C_BG)

# Title
ax.text(0.5, 0.985, f"Pipeline Trace: {ITEM_ID}", ha="center", va="top",
        fontsize=14, fontweight="bold", color=C_TEXT, transform=ax.transAxes)
ax.text(0.5, 0.972, f"Headline: \"{HEADLINE}\"", ha="center", va="top",
        fontsize=10.5, fontstyle="italic", color="#444", transform=ax.transAxes)

# ─── Input Box ───────────────────────────────────────────────────────────────
input_y = 0.955
draw_box(ax, 0.30, input_y, 0.40, 0.038, C_INPUT,
         "INPUT  (Headline)", [f'"{HEADLINE}"'], title_size=FONT_LABEL, body_size=FONT_BODY)

# Arrow from input to context
draw_arrow(ax, 0.50, input_y - 0.038, 0.50, input_y - 0.048)

# ─── Module 1: ContextEnricher ──────────────────────────────────────────────
ctx_y = input_y - 0.052
sit_wrapped = textwrap.wrap(SITUATION, width=95)
assoc_lines = [f"  • {a}" for a in ASSOCIATIONS]
ctx_body = ["situation:"] + [f"  {l}" for l in sit_wrapped] + ["", "semantic_associations:"] + assoc_lines
ctx_h = 0.022 + len(ctx_body) * 0.014 + 0.012
draw_box(ax, 0.06, ctx_y, 0.88, ctx_h, C_CONTEXT,
         "MODULE 1 — ContextEnricher  (Situation, Target)   [shared across all branches]",
         ctx_body, title_size=FONT_LABEL, body_size=FONT_SMALL)

# Arrow from context to branch split
branch_top = ctx_y - ctx_h
draw_arrow(ax, 0.50, branch_top, 0.50, branch_top - 0.01)

# ─── Modules 2-4: Four Parallel Branches ────────────────────────────────────
branch_y = branch_top - 0.016
branch_w = 0.215
branch_gap = 0.012
branch_x_start = 0.05

ARCH_COLORS = ["#D35400", "#E67E22", "#F39C12", "#E74C3C"]

for i, cand in enumerate(CANDIDATES):
    bx = branch_x_start + i * (branch_w + branch_gap)

    # Module 2: HumorArchitect
    arch_body = [
        f"mechanism: {cand['mechanism']}",
        f"opposition:",
        f"  {cand['opposition'].split(chr(10))[0]}",
    ]
    if "\n" in cand["opposition"]:
        arch_body.append(f"  {cand['opposition'].split(chr(10))[1]}")

    arch_h = 0.022 + len(arch_body) * 0.014 + 0.010
    draw_box(ax, bx, branch_y, branch_w, arch_h, ARCH_COLORS[i],
             f"MODULE 2 — Architect #{cand['num']}",
             arch_body, title_size=FONT_SMALL + 1, body_size=FONT_SMALL)

    # Arrow
    a2_bottom = branch_y - arch_h
    draw_arrow(ax, bx + branch_w / 2, a2_bottom, bx + branch_w / 2, a2_bottom - 0.008)

    # Module 3: DeliveryStrategist
    strat_y = a2_bottom - 0.012
    strat_body = [f"strategy: {cand['strategy']}"]
    strat_h = 0.022 + len(strat_body) * 0.014 + 0.008
    draw_box(ax, bx, strat_y, branch_w, strat_h, C_STRAT,
             f"MODULE 3 — Strategy #{cand['num']}",
             strat_body, title_size=FONT_SMALL + 1, body_size=FONT_SMALL)

    # Arrow
    a3_bottom = strat_y - strat_h
    draw_arrow(ax, bx + branch_w / 2, a3_bottom, bx + branch_w / 2, a3_bottom - 0.008)

    # Module 4: ContentWriter
    content_y = a3_bottom - 0.012
    joke_wrapped = textwrap.wrap(cand["joke"], width=35)
    content_body = ["final_joke:"] + [f"  {l}" for l in joke_wrapped]
    content_h = 0.022 + len(content_body) * 0.014 + 0.012
    border_color = C_WINNER if cand.get("winner") else C_CONTENT
    lw_override = 3.0 if cand.get("winner") else 1.8

    body_box = FancyBboxPatch(
        (bx, content_y - content_h), branch_w, content_h,
        boxstyle="round,pad=0,rounding_size=0.015",
        facecolor=C_LIGHT if not cand.get("winner") else "#FFFDE7",
        edgecolor=border_color, linewidth=lw_override, alpha=0.95,
        transform=ax.transAxes, zorder=2,
    )
    ax.add_patch(body_box)
    title_h = 0.022
    title_box = FancyBboxPatch(
        (bx, content_y - title_h), branch_w, title_h,
        boxstyle="round,pad=0,rounding_size=0.015",
        facecolor=border_color, edgecolor=border_color, linewidth=1.5,
        transform=ax.transAxes, zorder=3,
    )
    ax.add_patch(title_box)
    label_text = f"MODULE 4 — Writer #{cand['num']}"
    if cand.get("winner"):
        label_text += "  ★ WINNER"
    ax.text(bx + branch_w / 2, content_y - title_h / 2, label_text,
            ha="center", va="center", fontsize=FONT_SMALL + 1,
            fontweight="bold", color="white", transform=ax.transAxes, zorder=4)
    text_y = content_y - title_h - 0.008
    for line in content_body:
        ax.text(bx + 0.008, text_y, line,
                ha="left", va="top", fontsize=FONT_SMALL,
                color=C_TEXT, transform=ax.transAxes, zorder=4)
        text_y -= 0.014

    a4_bottom = content_y - content_h

    # Store bottom for arrows to judge
    if i == 0:
        arrows_bottom = a4_bottom

# ─── Arrows converging to judge ─────────────────────────────────────────────
judge_top = arrows_bottom - 0.025
for i in range(4):
    bx = branch_x_start + i * (branch_w + branch_gap)
    draw_arrow(ax, bx + branch_w / 2, arrows_bottom - 0.002,
               0.50, judge_top + 0.002, color="#888")

# ─── Module 5: HumorJudge ───────────────────────────────────────────────────
judge_body = [
    "Tournament bracket (single-elimination):",
    "  Semi-final 1:  Candidate 1 vs. Candidate 2",
    "  Semi-final 2:  Candidate 3 vs. Candidate 4",
    "  Final:  SF1 winner vs. SF2 winner",
    "",
    "Result: Candidate 4 selected as winner",
    "  (Irony mechanism, Dialogue delivery)",
]
judge_h = 0.022 + len(judge_body) * 0.014 + 0.012
draw_box(ax, 0.20, judge_top, 0.60, judge_h, C_JUDGE,
         "MODULE 5 — HumorJudge  (Tournament Selection)",
         judge_body, title_size=FONT_LABEL, body_size=FONT_BODY)

# Arrow to output
judge_bottom = judge_top - judge_h
draw_arrow(ax, 0.50, judge_bottom, 0.50, judge_bottom - 0.01)

# ─── Output Box ──────────────────────────────────────────────────────────────
out_y = judge_bottom - 0.014
winner_joke = CANDIDATES[3]["joke"]
winner_wrapped = textwrap.wrap(winner_joke, width=80)
out_body = [f"  {l}" for l in winner_wrapped]
out_h = 0.022 + len(out_body) * 0.014 + 0.010
draw_box(ax, 0.15, out_y, 0.70, out_h, C_WINNER,
         "OUTPUT — Winning Joke",
         out_body, title_size=FONT_LABEL, body_size=FONT_BODY, title_color=C_TEXT)

# ─── Legend ──────────────────────────────────────────────────────────────────
legend_y = out_y - out_h - 0.018
legend_items = [
    (C_CONTEXT, "ContextEnricher (GTVH: SI, TA)"),
    (C_ARCH,    "HumorArchitect (GTVH: LM, SO)"),
    (C_STRAT,   "DeliveryStrategist (GTVH: NS)"),
    (C_CONTENT, "ContentWriter (GTVH: LA)"),
    (C_JUDGE,   "HumorJudge (Selection)"),
]
for j, (color, label) in enumerate(legend_items):
    lx = 0.08 + j * 0.18
    rect = FancyBboxPatch(
        (lx, legend_y), 0.015, 0.012,
        boxstyle="round,pad=0,rounding_size=0.003",
        facecolor=color, edgecolor=color, transform=ax.transAxes, zorder=5,
    )
    ax.add_patch(rect)
    ax.text(lx + 0.02, legend_y + 0.006, label,
            ha="left", va="center", fontsize=FONT_SMALL,
            color=C_TEXT, transform=ax.transAxes, zorder=5)

# ─── Save ────────────────────────────────────────────────────────────────────
outpath = "Images/pipeline_trace.png"
fig.savefig(outpath, dpi=DPI, bbox_inches="tight", facecolor=C_BG, pad_inches=0.3)
plt.close(fig)
print(f"Saved: {outpath}")
print(f"Size: {FIG_W}x{FIG_H} inches @ {DPI} DPI")
