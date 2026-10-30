"""Fill the Review III template with the Claim Sense project content."""
import copy
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# usage: python build.py struct.pptx out.pptx   (struct.pptx: the Review III template with its slides duplicated)
SRC, OUT = sys.argv[1], sys.argv[2]
IMG = str(Path(__file__).resolve().parent / "img") + "/"
PROJECT = "Claim Sense: RAG-Based Insurance Claims Adjudication & Policy Knowledge Assistant"

NAVY, BLUE, SKY, GREEN, TEXT, MUTED = "1F3864", "2E75B6", "00A3E0", "548235", "242424", "595959"
TINT_BLUE, TINT_GREEN, TINT_GREY, WHITE = "DEEBF7", "E2F0D9", "F2F2F2", "FFFFFF"
SUB = "5583D1"  # the template's subtopic colour


def rgb(h):
    return RGBColor.from_string(h)


prs = Presentation(SRC)
slides = list(prs.slides)


# ---------------------------------------------------------------- helpers
def find(slide, pred):
    return next(sh for sh in slide.shapes if pred(sh))


def set_runs(paragraph, text, size=None):
    """Keep the first run's formatting, drop the others, set the text."""
    runs = paragraph.runs
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    if size:
        runs[0].font.size = Pt(size)


def header_and_title(slide, title):
    head = find(slide, lambda s: s.has_text_frame and "Project Title" in s.text_frame.text)
    head.left, head.width = Inches(3.4), Inches(9.85)
    set_runs(head.text_frame.paragraphs[0], PROJECT, 16)
    for p in head.text_frame.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    t = find(slide, lambda s: s.has_text_frame and abs(s.top - Inches(0.55)) < Inches(0.05) and not s.is_placeholder)
    set_runs(t.text_frame.paragraphs[0], title)
    for p in t.text_frame.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    for sh in list(slide.shapes):  # body placeholder: replaced by composed content
        if sh.is_placeholder:
            sh._element.getparent().remove(sh._element)


def _bullet(p, char="•", indent=0.22):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(int(Inches(indent))))
    pPr.set("indent", str(-int(Inches(indent))))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", char)


def text(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, name=None):
    """paras: list of dicts {t, size, bold, color, bullet, after, align, italic} or (str) shorthands."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.04)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    for i, spec in enumerate(paras):
        if isinstance(spec, str):
            spec = {"t": spec}
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        runs = spec["t"] if isinstance(spec["t"], list) else [(spec["t"], {})]
        for rt, ro in runs:
            r = p.add_run()
            r.text = rt
            f = r.font
            f.name = "Calibri"
            f.size = Pt(ro.get("size", spec.get("size", 16)))
            f.bold = ro.get("bold", spec.get("bold", False))
            f.italic = ro.get("italic", spec.get("italic", False))
            f.color.rgb = rgb(ro.get("color", spec.get("color", TEXT)))
        p.alignment = spec.get("align", PP_ALIGN.LEFT)
        p.space_after = Pt(spec.get("after", 6))
        if spec.get("bullet"):
            _bullet(p, spec.get("char", "•"), spec.get("indent", 0.22))
    return tb


def box(slide, x, y, w, h, fill, paras=None, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, anchor=MSO_ANCHOR.MIDDLE,
        name=None, radius=0.12, margin=0.08, shadow=False):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        s.name = name
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    if not shadow:
        sppr = s._element.spPr
        etree.SubElement(sppr, qn("a:effectLst"))
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    for i, spec in enumerate(paras or []):
        if isinstance(spec, str):
            spec = {"t": spec}
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = spec["t"]
        f = r.font
        f.name = "Calibri"
        f.size = Pt(spec.get("size", 14))
        f.bold = spec.get("bold", False)
        f.italic = spec.get("italic", False)
        f.color.rgb = rgb(spec.get("color", TEXT))
        p.alignment = spec.get("align", PP_ALIGN.CENTER)
        p.space_after = Pt(spec.get("after", 0))
        if spec.get("bullet"):
            _bullet(p)
    return s


def arrow(slide, x1, y1, x2, y2, color=MUTED, width=1.75, name=None):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    if name:
        c.name = name
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn("a:tailEnd"))
    tail.set("type", "triangle")
    tail.set("w", "med")
    tail.set("len", "med")
    return c


def picture(slide, path, x, y, w, name):
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))
    pic.name = name
    pic.line.color.rgb = rgb("BFBFBF")
    pic.line.width = Pt(0.75)
    return pic


def H(t, size=18, color=NAVY, after=4):
    return {"t": t, "size": size, "bold": True, "color": color, "after": after}


def B(t, size=15, after=5, color=TEXT):
    return {"t": t, "size": size, "bullet": True, "after": after, "color": color}


# ---------------------------------------------------------------- 1. title
s = slides[0]
tb = find(s, lambda sh: sh.has_text_frame and "Review III" in sh.text_frame.text)
ps = tb.text_frame.paragraphs
set_runs(ps[1], "Claim Sense", 40)
set_runs(ps[2], "RAG-Based Insurance Claims Adjudication & Policy Knowledge Assistant", 28)
for r in ps[2].runs:
    r.font.name = "Calibri"
ps[3]._p.find(qn("a:endParaRPr")).set("sz", "1600")
set_runs(ps[4], "S.K. Sricharan", 26)
set_runs(ps[5], "T-SERIES ID: T9984", 24)
for p in ps[6:]:
    p._p.getparent().remove(p._p)
tb.left, tb.width = Inches(1.2), Inches(10.93)

# ---------------------------------------------------------------- 2. introduction
s = slides[1]
header_and_title(s, "Introduction")
text(s, 0.35, 1.5, 7.3, 5.2, [
    H("Why claims adjudication needs help"),
    B("Settling an insurance claim means reading the claim packet, finding the policy wording in force on the "
      "incident date, applying limits, waiting periods and exclusions, and working out the payable amount."),
    B("Done by hand this is slow and inconsistent, and a wrong rejection must be defended clause by clause."),
    H("What Claim Sense does", after=4),
    B("AI agents read the documents and retrieve the exact policy clauses (Retrieval-Augmented Generation)."),
    B("A deterministic rules engine calculates the payable amount in exact decimal arithmetic."),
    B("Every recommendation goes to a human reviewer, with the evidence and an audit trail."),
], name="Intro text")
for i, (big, small, fill, col) in enumerate([
    ("6", "lines: health, motor, home, travel, personal accident, life", TINT_BLUE, BLUE),
    ("8", "specialised agents in one supervised pipeline", TINT_GREEN, GREEN),
    ("72", "synthetic claims analysed end to end", TINT_BLUE, BLUE),
    ("Live", "deployed at claim-sense.onrender.com", TINT_GREEN, GREEN),
]):
    y = 1.55 + i * 1.28
    box(s, 8.0, y, 4.95, 1.1, fill, name=f"Intro stat {i + 1}")
    text(s, 8.15, y + 0.12, 1.45, 0.86, [{"t": big, "size": 34 if len(big) < 4 else 26, "bold": True, "color": col,
                                           "align": PP_ALIGN.CENTER, "after": 0}], anchor=MSO_ANCHOR.MIDDLE)
    text(s, 9.65, y + 0.12, 3.2, 0.86, [{"t": small, "size": 15, "color": TEXT, "after": 0}], anchor=MSO_ANCHOR.MIDDLE)

# ---------------------------------------------------------------- 3. objective
s = slides[2]
header_and_title(s, "Objective")
objs = [
    ("Understand claim documents", "Classify each uploaded document and extract facts with the file, line and confidence they came from."),
    ("Ground decisions in policy text", "Retrieve the clause from the wording in force on the incident date, and cite it in every finding."),
    ("Calculate exactly", "Compute payable amounts with a Decimal rules engine; an LLM never does financial arithmetic."),
    ("Flag risk transparently", "Score fraud and risk with explainable rules: duplicates, early claims, amount mismatches, missing documents."),
    ("Keep people in control", "Route every claim to a review queue; approval limits, reviewer notes and a complete audit trail."),
    ("Prove it works", "Hand-worked golden evaluation, automated tests in CI, and checks against the live deployment."),
]
for i, (h, d) in enumerate(objs):
    col, row = i % 3, i // 3
    # the second row is shifted right to stay clear of the corner artwork
    x, y = (0.35 if row == 0 else 2.45) + col * 3.55, 1.6 + row * 2.6
    w = 3.35
    box(s, x, y, w, 2.3, TINT_BLUE if (i % 2 == 0) else TINT_GREEN, name=f"Objective {i + 1}")
    box(s, x + 0.2, y + 0.2, 0.55, 0.55, NAVY if i % 2 == 0 else GREEN, [{"t": str(i + 1), "size": 18, "bold": True,
                                                                          "color": WHITE}],
        shape=MSO_SHAPE.OVAL, name=f"Objective {i + 1} number")
    text(s, x + 0.9, y + 0.22, w - 1.05, 0.55, [{"t": h, "size": 17, "bold": True, "color": NAVY, "after": 0}],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.2, y + 0.9, w - 0.35, 1.35, [{"t": d, "size": 14, "color": TEXT, "after": 0}])
# second row starts right of the corner art, so shift the other two cards along
for sh in s.shapes:
    pass

# ---------------------------------------------------------------- 4-7. modules
modules = [
    ("Module 1 - Document Intelligence & Intake", "From an uploaded claim packet to one consolidated claim view", [
        "Upload claim forms, bills, estimates and reports as text or PDF (page-preserving extraction with pypdf).",
        "Each document is classified (14 types: discharge summary, repair estimate, loss assessment, death certificate ...).",
        "Facts are extracted with their source file, line and confidence; itemised charges are categorised per line of business.",
        "Text addressed to an AI inside a document is flagged for the reviewer and never followed.",
        "A reviewer can correct a fact with a reason; the next analysis uses it and the change is audited.",
    ], "02-claim-analysis.png", "Claim analysis screen: recommendation, amounts and evidence"),
    ("Module 2 - Policy RAG & Knowledge Assistant", "Find the right clause in the right version, or refuse", [
        "Policy wordings (Markdown or PDF) are parsed into clause-level chunks keeping page, section and clause number.",
        "The wording version in force on the incident date is matched first (e.g. HLT-SHIELD 2024.1 vs 2025.1).",
        "Hybrid retrieval: BM25 on stemmed words + TF-IDF on character n-grams, fused by reciprocal rank, with an insurance synonym map.",
        "The assistant answers only from retrieved clauses with citations, and refuses when evidence is too weak.",
        "PDF ingestion pipeline: validation, SHA-256 duplicate check, extraction, clause parsing, indexing.",
    ], "07-policy-assistant.png", "Policy assistant: cited answer from the matched wording"),
    ("Module 3 - Deterministic Adjudication Engine", "A cited, step-by-step payment waterfall in exact decimal arithmetic", [
        "Health: room and ICU per-day limits, non-payable consumables, deductible, co-payment, sum insured cap.",
        "Motor: depreciation by part type and vehicle age, deductible by engine size, cap at the insured declared value.",
        "Home: depreciation and the average clause for underinsurance; travel: per-item and per-benefit limits.",
        "Personal accident and life: a benefit schedule (% of the capital sum insured) and the sum assured.",
        "Every step (R10-R99) names the policy clause it applies; terms citing a missing clause are rejected at ingestion.",
    ], "20-property-claim-adjudication.png", "Home claim waterfall with the average clause"),
    ("Module 4 - Risk, Review & Audit", "Explainable risk signals and a human decision on every claim", [
        "Rule-based risk score: duplicate, early claim, high amount ratio, amount or name mismatch, missing documents, life contestable period.",
        "Recommendation: reject (cite clause), request information, investigate, partial approval or approve.",
        "Routed to adjuster, supervisor, SIU investigation or pending-information queues with settlement-clock tracking.",
        "Role-based access: approval limits, supervisor escalation, read-only auditors; adverse decisions need notes.",
        "Settlement and repudiation letters, CSV export, dashboard and a full audit trail.",
    ], "08-review-queue.png", "Review queue with risk, age and assignee"),
]
for k, (title, sub, bullets, img, cap) in enumerate(modules):
    s = slides[3 + k]
    header_and_title(s, title)
    paras = [{"t": sub, "size": 20, "bold": True, "color": SUB, "after": 8}] + [B(b, 16, 8) for b in bullets]
    text(s, 0.35, 1.48, 6.75, 4.1, paras, name="Module content")
    picture(s, IMG + img, 7.35, 1.6, 5.65, f"Screenshot - {cap}")
    text(s, 7.35, 1.6 + 5.65 * 760 / 1208 + 0.08, 5.65, 0.4,
         [{"t": cap, "size": 12, "italic": True, "color": MUTED, "after": 0}], name="Caption")

# ---------------------------------------------------------------- 8. problem statement
s = slides[7]
header_and_title(s, "Problem Statement")
box(s, 0.35, 1.55, 12.6, 1.35, TINT_BLUE, [
    {"t": "Build a claims decision-support system that reads a claim packet, finds the applicable clause in the policy "
          "version in force, calculates the payable amount exactly, flags risk, and hands a cited, auditable "
          "recommendation to a human who makes the decision.", "size": 18, "bold": True, "color": NAVY,
     "align": PP_ALIGN.LEFT}], name="Problem statement", margin=0.25)
pains = [
    ("Manual and slow", "Handlers cross-check documents against long wordings with versions, sub-limits, waiting periods and exclusions."),
    ("Inconsistent outcomes", "The same claim can be settled differently by different handlers; rejections are hard to defend."),
    ("LLMs alone are unsafe", "Generic chatbots invent clauses and do arithmetic unreliably: not acceptable for money or for regulators."),
    ("Fraud slips through", "Duplicates, early claims and mismatched amounts need systematic, explainable signals."),
]
for i, (h, d) in enumerate(pains):
    x = 2.45 + (i % 2) * 5.3
    y = 3.2 + (i // 2) * 1.75
    box(s, x, y, 5.0, 1.5, WHITE, line="BDD7EE", name=f"Pain point {i + 1}")
    box(s, x + 0.18, y + 0.2, 0.42, 0.42, BLUE if i % 2 == 0 else GREEN, [{"t": "!", "size": 16, "bold": True, "color": WHITE}],
        shape=MSO_SHAPE.OVAL, name=f"Pain icon {i + 1}")
    text(s, x + 0.75, y + 0.15, 4.1, 0.45, [{"t": h, "size": 17, "bold": True, "color": NAVY, "after": 0}], anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.75, y + 0.62, 4.1, 0.85, [{"t": d, "size": 13, "color": TEXT, "after": 0}])
text(s, 0.35, 3.25, 1.95, 2.2, [{"t": "Today's pain points", "size": 18, "bold": True, "color": NAVY, "after": 4},
                                 {"t": "Four gaps the project closes", "size": 13, "color": MUTED}], name="Pain heading")

# ---------------------------------------------------------------- 9. methodology - architecture
s = slides[8]
header_and_title(s, "Methodology - System Architecture")
# layer labels
layers = [("Users", 1.5), ("Presentation", 2.35), ("API", 3.3), ("Services", 4.25), ("Data", 5.55)]
for name, y in layers:
    text(s, 0.3, y, 1.25, 0.6, [{"t": name, "size": 13, "bold": True, "color": MUTED, "after": 0}], anchor=MSO_ANCHOR.MIDDLE)
# users
for i, u in enumerate(["Adjuster", "Supervisor", "Auditor"]):
    box(s, 2.6 + i * 2.35, 1.5, 2.05, 0.55, TINT_GREY, [{"t": u, "size": 14, "bold": True, "color": NAVY}], name=f"User {u}")
# frontend
box(s, 1.6, 2.3, 8.75, 0.7, BLUE, [{"t": "React + TypeScript single-page app (Vite)", "size": 15, "bold": True, "color": WHITE},
                                    {"t": "Dashboard  ·  Claims  ·  New claim  ·  Review queue  ·  Policy library  ·  Assistant  ·  Audit  ·  Evaluation",
                                     "size": 11, "color": WHITE}], name="Frontend")
# api
box(s, 1.6, 3.25, 8.75, 0.65, NAVY, [{"t": "FastAPI REST API  /api/v1   ·   sign-in tokens and roles   ·   security headers",
                                      "size": 14, "bold": True, "color": WHITE}], name="API")
# services
svc = [("Agent Supervisor", "8 agents, tool calls logged, fails safely"),
       ("Hybrid RAG", "BM25 + char n-gram, version match"),
       ("Rules Engine", "Decimal waterfall with clause refs"),
       ("Review & Letters", "queues, SLA, letters, analytics")]
for i, (h, d) in enumerate(svc):
    box(s, 1.6 + i * 2.23, 4.15, 2.06, 1.1, TINT_BLUE, [{"t": h, "size": 14, "bold": True, "color": NAVY},
                                                       {"t": d, "size": 11, "color": TEXT}], name=f"Service {h}")
# data
data = [("PostgreSQL / SQLite", "claims, facts, runs, decisions, tasks, audit"),
        ("Policy corpus", "7 wordings + structured terms, PDF ingestion"),
        ("Document storage", "uploaded claim files"),
        ("Source registry", "SHA-256 provenance, RAG manifest")]
for i, (h, d) in enumerate(data):
    box(s, 2.35 + i * 2.05, 5.5, 1.9, 1.05, TINT_GREEN, [{"t": h, "size": 13, "bold": True, "color": GREEN},
                                                         {"t": d, "size": 10.5, "color": TEXT}], name=f"Data {h}")
# arrows between layers
for x in (3.6, 5.95, 8.3):
    arrow(s, x, 2.05, x, 2.3)
arrow(s, 5.97, 3.0, 5.97, 3.25)
for i in range(4):
    arrow(s, 2.63 + i * 2.23, 3.9, 2.63 + i * 2.23, 4.15)
for i in range(4):
    arrow(s, 3.3 + i * 2.05, 5.25, 3.3 + i * 2.05, 5.5)
# side panel
box(s, 10.65, 1.5, 2.35, 2.45, TINT_GREY, [
    {"t": "Optional LLM", "size": 14, "bold": True, "color": NAVY, "after": 4},
    {"t": "Writes the explanation narrative only. Off by default: answers are extractive. Never decides or calculates.",
     "size": 11, "color": TEXT}], anchor=MSO_ANCHOR.TOP, name="LLM panel")
box(s, 10.65, 4.1, 2.35, 2.45, TINT_GREY, [
    {"t": "Delivery", "size": 14, "bold": True, "color": NAVY, "after": 4},
    {"t": "One Docker image (UI built into the API). GitHub Actions CI. Live on Render; a verify-deployment workflow snapshots the live claims and runs the smoke test.",
     "size": 11, "color": TEXT}], anchor=MSO_ANCHOR.TOP, name="Delivery panel")
arrow(s, 10.65, 4.7, 10.35, 4.7)

# ---------------------------------------------------------------- 10. methodology - workflow
s = slides[9]
header_and_title(s, "Methodology - Claim Workflow")
steps = [("Upload", "claim packet"), ("0 Document", "classify, extract"), ("1 Intake", "consolidate facts"),
         ("2 Policy", "version + RAG"), ("3 Coverage", "waiting, exclusions"),
         ("4 Adjudicate", "Decimal waterfall"), ("5 Risk", "fraud signals"), ("6 Evidence", "recommendation"),
         ("7 Review", "route to queue"), ("8 Audit", "record event")]
w, gap, x0 = 2.25, 0.32, 0.45
for i, (h, d) in enumerate(steps):
    row, col = divmod(i, 5)
    x = x0 + col * (w + gap) if row == 0 else x0 + (4 - col) * (w + gap)
    y = 1.6 if row == 0 else 3.2
    fill = NAVY if i == 0 else (BLUE if i < 5 else GREEN)
    box(s, x, y, w, 1.05, fill, [{"t": h, "size": 16, "bold": True, "color": WHITE},
                                 {"t": d, "size": 12, "color": WHITE}], name=f"Step {h}")
    if i < 9:
        if i == 4:
            arrow(s, x + w / 2, y + 1.05, x + w / 2, 3.2)
        elif row == 0:
            arrow(s, x + w, y + 0.52, x + w + gap, y + 0.52)
        else:
            arrow(s, x, y + 0.52, x - gap, y + 0.52)
# human decision
box(s, 0.45, 4.6, 2.25, 1.05, "C55A11", [{"t": "Human decision", "size": 16, "bold": True, "color": WHITE},
                                           {"t": "approve, reject, ask, investigate", "size": 12, "color": WHITE}],
    name="Human decision")
arrow(s, 0.45 + w / 2, 4.25, 0.45 + w / 2, 4.6)
box(s, 3.05, 4.6, 2.25, 1.05, "C55A11", [{"t": "Letter + audit", "size": 16, "bold": True, "color": WHITE},
                                           {"t": "settlement or repudiation", "size": 12, "color": WHITE}], name="Letter")
arrow(s, 2.7, 5.12, 3.05, 5.12)
box(s, 5.65, 4.45, 7.35, 2.15, TINT_GREY, [
    {"t": "Recommendation rules (checked in order)", "size": 15, "bold": True, "color": NAVY, "align": PP_ALIGN.LEFT, "after": 4},
    {"t": "1. Not covered  ->  recommend reject, citing the failing clause", "size": 13, "align": PP_ALIGN.LEFT, "after": 2},
    {"t": "2. Missing documents  ->  request information", "size": 13, "align": PP_ALIGN.LEFT, "after": 2},
    {"t": "3. High risk score  ->  investigate (SIU queue)", "size": 13, "align": PP_ALIGN.LEFT, "after": 2},
    {"t": "4. Payable below claimed  ->  partial approval; otherwise approve", "size": 13, "align": PP_ALIGN.LEFT, "after": 2},
    {"t": "Any agent error stops the run safely and marks the claim for attention.", "size": 12, "italic": True,
     "color": MUTED, "align": PP_ALIGN.LEFT}], anchor=MSO_ANCHOR.TOP, name="Decision rules", margin=0.2)

# ---------------------------------------------------------------- 11. approach / algorithms / tools
s = slides[10]
header_and_title(s, "Approach / Algorithms / Tools")
cols = [
    ("Algorithms", BLUE, TINT_BLUE, [
        "Hybrid retrieval: BM25 (weight 1.5) + TF-IDF over character 3-5 grams (weight 1.0), fused by weighted reciprocal rank",
        "Policy version matching by incident date",
        "Rules waterfall in Python Decimal, rounded to paise",
        "Weighted risk rules: score 0-100, Low / Medium (25+) / High (50+)",
        "Refusal below a minimum retrieval score",
    ]),
    ("Tools & Stack", NAVY, TINT_GREY, [
        "Python 3, FastAPI, SQLAlchemy, Pydantic",
        "PostgreSQL (Docker Compose) and SQLite",
        "pypdf for PDF text extraction",
        "React, TypeScript, Vite",
        "Docker, Render, GitHub Actions",
        "pytest, Playwright, ruff",
    ]),
    ("Data & Evaluation", GREEN, TINT_GREEN, [
        "Synthetic only: 7 policy wordings across 6 lines",
        "72 claim packets; 10,000-claim synthetic portfolio",
        "Golden set: 72 claim cases + 30 questions, worked by hand",
        "SHA-256 source registry; CAS Schedule P industry benchmark (not used in decisions)",
        "CI fails on any failed check",
    ]),
]
for i, (h, c, tint, items) in enumerate(cols):
    x = 0.35 + i * 4.25
    y, hgt = 1.55, 3.95
    box(s, x, y, 4.0, hgt, tint, name=f"{h} panel")
    box(s, x + 0.2, y + 0.18, 3.6, 0.5, c, [{"t": h, "size": 17, "bold": True, "color": WHITE}], name=f"{h} heading")
    text(s, x + 0.2, y + 0.82, 3.65, hgt - 0.95, [B(t, 13.5, 6) for t in items], name=f"{h} list")

# ---------------------------------------------------------------- 12. findings - claims
s = slides[11]
header_and_title(s, "Findings and Results - Claims")
stats = [("72", "claims across 6 lines"), ("₹2.22 Cr", "billed"), ("₹1.62 Cr", "recommended payable (72.9%)"),
         ("986/986", "golden checks passed")]
for i, (big, small) in enumerate(stats):
    x = 0.35 + i * 3.17
    box(s, x, 1.5, 2.95, 1.3, TINT_BLUE if i % 2 == 0 else TINT_GREEN, name=f"Stat {i + 1}")
    text(s, x + 0.1, 1.55, 2.75, 0.7, [{"t": big, "size": 30, "bold": True, "color": BLUE if i % 2 == 0 else GREEN,
                                        "align": PP_ALIGN.CENTER, "after": 0}], anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.1, 2.2, 2.75, 0.5, [{"t": small, "size": 13, "color": TEXT, "align": PP_ALIGN.CENTER, "after": 0}])
cd = CategoryChartData()
# live site, Verify deployment run 41115415499 (30 Oct 2026)
cd.categories = ["Health (21)", "Motor (11)", "Home (11)", "Travel (14)", "PA (8)", "Life (7)"]
cd.add_series("Billed (₹ lakh)", (21.62, 6.81, 29.43, 29.10, 28.23, 107.00))
cd.add_series("Payable (₹ lakh)", (11.91, 3.04, 19.01, 19.45, 26.57, 82.00))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(2.4), Inches(3.0), Inches(6.2), Inches(3.75), cd)
gf.name = "Billed vs payable chart"
ch = gf.chart
ch.has_title = True
ch.chart_title.text_frame.text = "Billed vs recommended payable by line (₹ lakh)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(13)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
ch.chart_title.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(NAVY)
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout = False
ch.legend.font.size = Pt(11)
for ser, col in zip(ch.plots[0].series, (BLUE, GREEN)):
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = rgb(col)
plot = ch.plots[0]
plot.gap_width = 60
plot.has_data_labels = True
plot.data_labels.font.size = Pt(10)
plot.data_labels.number_format = "0.0"
plot.data_labels.number_format_is_linked = False
plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
ch.category_axis.tick_labels.font.size = Pt(11)
ch.value_axis.tick_labels.font.size = Pt(10)
ch.value_axis.has_major_gridlines = True
ch.value_axis.major_gridlines.format.line.color.rgb = rgb("D9D9D9")
box(s, 8.85, 3.0, 4.15, 3.75, TINT_GREY, [
    {"t": "Recommendations", "size": 15, "bold": True, "color": NAVY, "align": PP_ALIGN.LEFT, "after": 4},
    {"t": "Partial approval: 33", "size": 13, "align": PP_ALIGN.LEFT, "after": 1},
    {"t": "Reject with cited clause: 25", "size": 13, "align": PP_ALIGN.LEFT, "after": 1},
    {"t": "Request information: 6", "size": 13, "align": PP_ALIGN.LEFT, "after": 1},
    {"t": "Investigate: 4  ·  Approve: 4", "size": 13, "align": PP_ALIGN.LEFT, "after": 6},
    {"t": "Every claim went to a human review queue; the system decided none. Every exclusion, waiting period and "
          "limit in the wordings is exercised by at least one claim.", "size": 12, "color": TEXT, "align": PP_ALIGN.LEFT,
     "after": 8},
    {"t": "Live site, 30 Oct 2026", "size": 15, "bold": True, "color": NAVY, "align": PP_ALIGN.LEFT, "after": 4},
    {"t": "The figures above are the live snapshot. They match the repository's prediction to the rupee, and the "
          "smoke test then filed and assessed one new claim on each line.", "size": 12, "color": TEXT, "align": PP_ALIGN.LEFT}],
    anchor=MSO_ANCHOR.TOP, name="Recommendations panel", margin=0.2)

# ---------------------------------------------------------------- 13. findings - quality
s = slides[12]
header_and_title(s, "Findings and Results - Quality and Deployment")
dims = [("Retrieval correctness", "130/130"), ("Citation correctness", "80/80"), ("Groundedness", "156/156"),
        ("Coverage state", "143/143"), ("Adjudication amount", "182/182"), ("Risk classification", "79/79"),
        ("Workflow outcome", "216/216")]
rows, cols_n = len(dims) + 1, 2
tbl = s.shapes.add_table(rows, cols_n, Inches(0.35), Inches(1.55), Inches(5.3), Inches(0.42 * rows)).table
tbl.columns[0].width, tbl.columns[1].width = Inches(3.6), Inches(1.7)
for r, (a, b) in enumerate([("Golden evaluation dimension", "Checks passed")] + dims):
    for c, v in enumerate((a, b)):
        cell = tbl.cell(r, c)
        cell.text = v
        p = cell.text_frame.paragraphs[0]
        p.runs[0].font.size = Pt(13)
        p.runs[0].font.bold = r == 0
        p.runs[0].font.color.rgb = rgb(WHITE if r == 0 else TEXT)
        p.alignment = PP_ALIGN.RIGHT if c == 1 else PP_ALIGN.LEFT
        cell.fill.solid()
        cell.fill.fore_color.rgb = rgb(NAVY if r == 0 else (TINT_BLUE if r % 2 else WHITE))
        cell.margin_top = cell.margin_bottom = Inches(0.04)
text(s, 2.45, 5.05, 3.2, 1.5, [
    {"t": "Retrieval hit@1 100%  ·  MRR 1.00", "size": 13, "bold": True, "color": NAVY, "after": 3},
    {"t": "Refusals correct 100%", "size": 13, "bold": True, "color": NAVY, "after": 3},
    {"t": "Risk rules on 10,000 synthetic claims: precision 90.1%, recall 78.3% (injected patterns only)",
     "size": 12, "color": TEXT}], name="Retrieval metrics")
picture(s, IMG + "23-dashboard-interactive.png", 6.0, 1.55, 7.0, "Screenshot - live dashboard")
text(s, 6.0, 1.55 + 7.0 * 760 / 1208 + 0.08, 7.0, 0.4,
     [{"t": "Claims dashboard: every tile, line and bar opens the matching claims", "size": 12, "italic": True,
       "color": MUTED, "after": 0}], name="Caption")
text(s, 6.0, 6.45, 7.0, 0.4, [
    {"t": [("158 backend tests  ·  12 browser tests  ·  live site checks passed (30 Oct 2026)", {"bold": True})],
     "size": 13, "color": GREEN, "after": 0}], name="Test summary")

# ---------------------------------------------------------------- 14. conclusion
s = slides[13]
header_and_title(s, "Conclusion")
text(s, 0.35, 1.5, 7.4, 5.0, [
    H("What was achieved"),
    B("Project complete: every item in the definition of done is met and verified on the live site."),
    B("A working, deployed claims decision-support system for health, motor, home, travel, personal accident and life insurance."),
    B("Retrieval-augmented, cited reasoning over versioned policy wordings, with refusal when evidence is weak."),
    B("Exact, explainable payable amounts: 986/986 hand-worked checks pass, and every step cites its clause."),
    B("People stay in charge: review queues, approval limits, reviewer notes, letters and a complete audit trail."),
    H("Limitations", after=4),
    B("Synthetic data only; the LLM narrative is not yet scored; no OCR for scanned images."),
    B("The free hosting tier restarts with the 72 seeded claims, so claims filed on the live site are not kept."),
], name="Conclusion text")
box(s, 8.0, 1.55, 4.95, 4.1, TINT_GREEN, [
    {"t": "Future work", "size": 18, "bold": True, "color": GREEN, "align": PP_ALIGN.LEFT, "after": 8},
    {"t": "Ingest real IRDAI circulars after a licence review", "size": 14, "bullet": True, "align": PP_ALIGN.LEFT, "after": 6},
    {"t": "Embedding retriever alongside BM25", "size": 14, "bullet": True, "align": PP_ALIGN.LEFT, "after": 6},
    {"t": "OCR for scanned claim documents", "size": 14, "bullet": True, "align": PP_ALIGN.LEFT, "after": 6},
    {"t": "Score LLM-written explanations sentence by sentence against cited clauses", "size": 14, "bullet": True,
     "align": PP_ALIGN.LEFT, "after": 6},
    {"t": "Azure Container Apps deployment, single sign-on and an ML fraud model", "size": 14, "bullet": True,
     "align": PP_ALIGN.LEFT, "after": 6},
    {"t": "Persistent database on a paid hosting tier", "size": 14, "bullet": True, "align": PP_ALIGN.LEFT, "after": 6}], anchor=MSO_ANCHOR.TOP, name="Future work", margin=0.3)

# ---------------------------------------------------------------- 15. acknowledgement
s = slides[14]
header_and_title(s, "Acknowledgement")
text(s, 2.4, 2.0, 8.5, 3.8, [
    {"t": "I sincerely thank the University and LTIMindtree for the M.Tech Advanced Industry Integrated Program, "
          "and L&T EduTech for its support as implementation partner.", "size": 20, "color": TEXT, "after": 14},
    {"t": "I am grateful to my project guide and mentors for their guidance, reviews and encouragement throughout "
          "this project, and to my family and friends for their constant support.", "size": 20, "color": TEXT, "after": 24},
    {"t": "S.K. Sricharan  ·  T-SERIES ID: T9984", "size": 18, "bold": True, "color": NAVY, "after": 0},
], name="Acknowledgement text")

# ---------------------------------------------------------------- 16. references
s = slides[15]
header_and_title(s, "References")
refs = [
    "P. Lewis et al., \"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,\" Advances in Neural Information Processing Systems (NeurIPS), 2020.",
    "S. Robertson and H. Zaragoza, \"The Probabilistic Relevance Framework: BM25 and Beyond,\" Foundations and Trends in Information Retrieval, vol. 3, no. 4, 2009.",
    "G. V. Cormack, C. L. A. Clarke and S. Buettcher, \"Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods,\" Proc. ACM SIGIR, 2009.",
    "Insurance Regulatory and Development Authority of India (IRDAI), Master Circulars on Health Insurance Business and on Protection of Policyholders' Interests, 2024. https://irdai.gov.in",
    "Casualty Actuarial Society, Loss Reserving Data Pulled From NAIC Schedule P (accident years 1998-2007), compiled for the CAS by S&P Global Market Intelligence. https://www.casact.org",
    "FastAPI documentation, https://fastapi.tiangolo.com  ·  React documentation, https://react.dev  ·  SQLAlchemy documentation, https://www.sqlalchemy.org",
    "Project source code: https://github.com/sricharansk/CLAIM-SENSE  ·  Live application: https://claim-sense.onrender.com",
]
text(s, 0.35, 1.5, 12.6, 4.2, [{"t": f"[{i + 1}]  {r}", "size": 14, "color": TEXT, "after": 8} for i, r in enumerate(refs)],
     name="Reference list")

prs.save(OUT)
print("saved", OUT)
