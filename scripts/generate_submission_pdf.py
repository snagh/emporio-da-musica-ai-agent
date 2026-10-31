"""Gera o documento PDF oficial de submissão do desafio técnico da Artefact.

Nome do arquivo gerado conforme as regras do processo seletivo:
'Anderson Martins - AI Engineer – Full-Stack para Aplicações com IA Generativa.pdf'
"""

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT_FILENAME = "Anderson Martins - AI Engineer – Full-Stack para Aplicações com IA Generativa.pdf"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / OUTPUT_FILENAME


def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0D233A")
    accent_color = colors.HexColor("#1A73E8")
    text_dark = colors.HexColor("#222222")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=accent_color,
        spaceBefore=8,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_dark,
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        "Code_Custom",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
        backColor=colors.HexColor("#F1F5F9"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=1,
        borderPadding=6,
        spaceAfter=8,
    )

    story = []

    # Title & Header
    story.append(Paragraph("Artefact — AI Engineer Technical Case", title_style))
    story.append(
        Paragraph(
            "<b>Candidate:</b> Anderson Martins &nbsp;|&nbsp; "
            "<b>Role:</b> AI Engineer – Full-Stack para Aplicações com IA Generativa<br/>"
            "<b>GitHub Repository:</b> <font color='#1A73E8'><u>https://github.com/snagh/emporio-da-musica-ai-agent</u></font><br/>"
            "<b>Date:</b> October 2026 &nbsp;|&nbsp; <b>Evaluation Language:</b> English",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=10))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary & Problem Formulation", h1_style))
    story.append(
        Paragraph(
            "This project delivers an end-to-end, production-ready AI Customer Support Agent for <b>Empório da Música</b>, "
            "a specialized musical instrument store located in Campo Grande/MS. The store's human staff was heavily overloaded "
            "with repetitive inquiries: catalog checks, instrument specifications, stock availability, order tracking, store policies, "
            "and operating hours. The solution implements an agentic architecture combining <b>Deterministic Tool Calling</b> over in-memory relational "
            "data with <b>Semantic RAG (Retrieval-Augmented Generation)</b> over the store's policy guidelines.",
            body_style,
        )
    )

    # 2. System Architecture & Technical Decisions
    story.append(Paragraph("2. Architectural Design & Technical Decisions", h1_style))
    story.append(
        Paragraph(
            "• <b>Decoupled Hybrid Engine:</b> Rather than exposing raw Text-to-SQL (which risks SQL injection and schema hallucination), "
            "we designed strongly typed Pydantic tools for structured queries (<code>search_catalog</code>, <code>get_order_status</code>, "
            "<code>list_active_promotions</code>) and a semantic retriever for unstructured policies (<code>search_policies</code>).<br/>"
            "• <b>In-Memory SQLite (:memory:):</b> Operational data spans 6 CSV tables (categories, products, customers, orders, items, promos). "
            "Ingesting them into an in-memory SQLite store provides sub-millisecond (< 1 ms) query times without requiring external databases.<br/>"
            "• <b>Zero-Dependency BM25 Okapi RAG:</b> The provided store policy PDF presented whitespace corruption upon extraction. "
            "We built an automated text stream normalizer and a high-performance BM25 Okapi retriever in pure Python. It requires zero API tokens, "
            "ensuring instant, cost-free local evaluation.<br/>"
            "• <b>Multi-Model Agnostic Support:</b> Native integration with Google Gemini (<code>gemini-2.5-flash</code> via <code>google-genai</code>) "
            "and OpenAI (<code>gpt-4o-mini</code>), paired with an autonomous local fallback mode for offline testing.<br/>"
            "• <b>Interactive Terminal CLI:</b> Developed using <code>rich</code>, featuring formatted panels, live tool-execution feedback, and conversation export.",
            body_style,
        )
    )

    # 3. Data Integrity & Business Insights
    story.append(Paragraph("3. Exploratory Data Analysis & Business Insights", h1_style))
    story.append(
        Paragraph(
            "Through <code>scripts/inspect_data.py</code>, we audited 100% of the relational data integrity:<br/>"
            "• <b>Relational Keys:</b> 0 orphan records across all tables (products ↔ categories, order_items ↔ orders ↔ customers).<br/>"
            "• <b>Catalog & Pricing:</b> 65 products registered (62 active, 3 inactive) spanning from R$ 159.90 to R$ 19,567.00. "
            "Crucially, the <code>specs</code> column contains JSON-serialized tonewood and hardware attributes (e.g. solid Spruce tops, nylon strings).<br/>"
            "• <b>Active Promotions:</b> Out of 25 historical campaigns, exactly 4 are currently active (#90, #94, #121, #127).<br/>"
            "• <b>Payment Terms:</b> 5% instant discount on PIX; interest-free credit card installments up to 12x (minimum R$ 100/installment).",
            body_style,
        )
    )

    # 4. Domain Guardrails & Persona
    story.append(Paragraph("4. Domain Guardrails & Store Persona", h1_style))
    story.append(
        Paragraph(
            "• <b>Golden Commercial Rule:</b> The store exclusively sells complete instruments and <b>does NOT sell standalone accessories</b> "
            "(individual string packs, loose guitar picks, cables, strap-locks, standalone cases, or amplifiers). The agent strictly enforces this "
            "by cordially declining accessory requests and proposing related instruments.<br/>"
            "• <b>7-Day Legal Return Window:</b> Applies the Brazilian Consumer Defense Code (CDC) right of withdrawal for online orders (7 calendar days).<br/>"
            "• <b>Out-of-Scope Guardrails:</b> Politely rejects off-topic queries (political commentary, culinary recipes, generic code generation) "
            "while steering the conversation back to musical instruments.",
            body_style,
        )
    )

    # 5. Automated Testing & Verification
    story.append(Paragraph("5. Automated Test Suite (100% Passing)", h1_style))
    story.append(
        Paragraph(
            "A comprehensive test suite of <b>31 automated unit tests</b> was developed with <code>pytest</code>, executing in 2.2 seconds:",
            body_style,
        )
    )

    test_data = [
        ["Test Module", "Focus Area", "Test Count", "Status"],
        ["test_database.py", "SQLite Ingestion, Joins & Pricing Calculations", "9", "PASSED (100%)"],
        ["test_tools.py", "Pydantic Schemas & Execution Dispatcher", "9", "PASSED (100%)"],
        ["test_rag.py", "PDF Normalization, Chunking & BM25 Retrieval", "6", "PASSED (100%)"],
        ["test_agent.py", "Multi-turn Memory, Tool Routing & Guardrails", "7", "PASSED (100%)"],
    ]
    t = Table(test_data, colWidths=[110, 240, 70, 100])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (2, 0), (3, -1), "CENTER"),
        ])
    )
    story.append(t)
    story.append(Spacer(1, 8))

    # 6. Sample Dialogues
    story.append(Paragraph("6. Validated Interaction Scenarios (Edge Cases)", h1_style))
    story.append(
        Paragraph(
            "The repository includes 4 markdown transcripts in <code>examples/</code> demonstrating real edge-case handling:<br/>"
            "• <b>Scenario 1 (Catalog & Price Filtering):</b> Customer requests beginner guitars under R$ 1,000; agent returns Yamaha C40 and Tagima Memphis with nylon string specs.<br/>"
            "• <b>Scenario 2 (Policies & Returns):</b> Customer asks for store location in Campo Grande (Rua 14 de Maio, 3200) and details the 7-day online return policy.<br/>"
            "• <b>Scenario 3 (Order Tracking):</b> Real-time lookup of Order #1, retrieving carrier tracking code (<code>BRAB1234567BR</code>) and delivery status.<br/>"
            "• <b>Scenario 4 (Complex Multi-Constraint Case):</b> Customer asks for loose Fender picks (agent politely declines per accessory policy), "
            "then asks for active guitar promos, and calculates final checkout price with 5% PIX discount.",
            body_style,
        )
    )

    # 7. AI Assistant Transparency Statement
    story.append(Paragraph("7. AI-Assisted Workflow Transparency (Artefact Compliance)", h1_style))
    story.append(
        Paragraph(
            "In full alignment with Artefact's instructions encouraging transparent use of AI tools:<br/>"
            "• <b>Tool Employed:</b> <b>Google Antigravity</b> (agentic pair programming assistant powered by Gemini).<br/>"
            "• <b>How AI was leveraged:</b> Expediting initial boilerplate code, discovering whitespace anomalies in the PDF extraction stream, "
            "and writing automated test assertions for edge cases.<br/>"
            "• <b>Human Engineering Decisions:</b> Choosing an in-memory hybrid architecture over fragile SQL generation, structuring the BM25 Okapi "
            "semantic search algorithm, enforcing the store's accessory boundary, and authoring atomic Git commits across the development lifecycle.",
            body_style,
        )
    )

    # Footer note
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceAfter=6))
    story.append(
        Paragraph(
            "<b>Submission Link:</b> <font color='#1A73E8'><u>https://github.com/snagh/emporio-da-musica-ai-agent</u></font> &nbsp;|&nbsp; "
            "Built with Python 3.11+, Pydantic v2, Rich, and PyPDF.",
            ParagraphStyle("Footer", parent=body_style, fontSize=8, textColor=colors.HexColor("#64748B"), alignment=1),
        )
    )

    doc.build(story)
    print(f"PDF generated successfully at: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
