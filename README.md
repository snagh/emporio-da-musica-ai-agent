# Empório da Música — Intelligent Customer Support AI Agent 🎵

[![Unit Tests](https://img.shields.io/badge/pytest-31%20passed-brightgreen.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue.svg)](pyproject.toml)
[![Architecture](https://img.shields.io/badge/architecture-hybrid%20tool%20calling%20%2B%20rag-orange.svg)](#-architecture-overview)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

*Read this document in Portuguese: [README_pt.md](README_pt.md)*

Prototype of an Intelligent Conversational AI Agent developed as a comprehensive solution for the **Artefact AI Engineer Technical Case (2026)**.

The solution addresses the customer support overload at **Empório da Música** (a premier musical instrument retail store founded in 2008 in Campo Grande/MS, Brazil). It automates high-frequency inquiries regarding product catalogs, real-time inventory, pricing, order tracking, and institutional policies using **Deterministic Tool Calling** and **Semantic Retrieval-Augmented Generation (RAG)**.

---

## 📑 Executive Summary

1. [Architecture Overview](#-architecture-overview)
2. [Technical Decisions & Design Rationale](#-technical-decisions--design-rationale)
3. [Quickstart Guide](#-quickstart-guide)
4. [Automated Testing Suite](#-automated-testing-suite)
5. [Interaction Examples & Edge Cases](#-interaction-examples--edge-cases)
6. [Known Limitations & Future Roadmap](#-known-limitations--future-roadmap)
7. [AI-Assisted Workflow Transparency](#-ai-assisted-workflow-transparency)

---

## 🏛️ Architecture Overview

The system adopts a **decoupled hybrid architecture**, strictly separating structured relational queries (via in-memory SQL) from unstructured normative policy queries (via semantic RAG):

```text
                               ┌────────────────────────────────┐
                               │    Customer (Rich Terminal)    │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │   EmporioAgent (Orchestrator)  │
                               │  - Store Persona & Hospitality │
                               │  - Multi-turn Conversational   │
                               │  - Strict Business Guardrails  │
                               └───────┬────────────────┬───────┘
                                       │                │
                   ┌───────────────────┴──┐          ┌──┴───────────────────┐
                   │ Structured Relational│          │ Unstructured Policies│
                   ▼                      ▼          ▼                      ▼
        ┌──────────────────────┐  ┌─────────────┐ ┌─────────────────────────┐
        │ search_catalog       │  │ order_status│ │ search_policies         │
        │ get_product_details  │  │ active_promo│ │ (Returns, Warranties,   │
        │ list_categories      │  └──────┬──────┘ │  Hours & Delivery)      │
        └──────────┬───────────┘         │        └────────────┬────────────┘
                   │                     │                     │
                   ▼                     ▼                     ▼
        ┌───────────────────────────────────────┐ ┌─────────────────────────┐
        │      SQLite In-Memory Engine          │ │  BM25 Semantic Engine   │
        │ (Products, Orders, Customers, Promos) │ │ (Normalized PDF Chunks) │
        └───────────────────────────────────────┘ └─────────────────────────┘
```

### Directory Structure

```text
emporio-da-musica/
├── data/                                # Original store datasets & PDF manual
│   ├── desafio_tecnico_ai_eng - *.csv  # Relational operational tables
│   └── políticas_da_loja.pdf           # Internal procedures & policy guide
├── examples/                            # Real conversation transcripts (edge cases)
│   ├── 01_consulta_catalogo_e_precos.md
│   ├── 02_politicas_devolucao_e_garantia.md
│   ├── 03_status_pedido_e_rastreamento.md
│   └── 04_cenario_complexo_promocao_e_acessorios.md
├── scripts/
│   ├── inspect_data.py                  # Exploratory analysis & key integrity check
│   └── generate_submission_pdf.py       # Artefact official submission PDF compiler
├── src/
│   ├── agent/                           # Orchestrator, Prompts, Persona & Schemas
│   ├── database/                        # In-memory SQLite ingestion & queries
│   ├── rag/                             # PDF text normalization, chunker & BM25 engine
│   ├── tools/                           # Pydantic-typed tools for LLM Function Calling
│   ├── ui/                              # Interactive CLI with Rich formatting
│   └── config.py                        # Pydantic Settings & environment variables
├── tests/                               # 31 unit tests (pytest) - 100% green
│   ├── test_agent.py
│   ├── test_database.py
│   ├── test_rag.py
│   └── test_tools.py
├── .env.example                         # Environment configuration template
├── pyproject.toml                       # Python package specification
├── requirements.txt                     # Pinned dependencies
├── main.py                              # Application entrypoint
└── README.md                            # English documentation (Primary)
```

---

## 🎯 Technical Decisions & Design Rationale

### 1. Hybrid Approach: Deterministic Function Calling vs. Free-form Text-to-SQL
- **Why avoid raw Text-to-SQL?** Allowing a model to generate arbitrary SQL directly poses severe risks of prompt injection, hallucinated table joins, and slow query latency. Instead, we designed **deterministic, strictly typed tools via Pydantic** (`search_catalog`, `get_order_status`, `list_active_promotions`, `search_policies`).
- **Why SQLite in-memory (`:memory:`)?** The dataset spans 6 CSVs totaling dozens of kilobytes. Loading them in an in-memory SQLite store provides **sub-millisecond (< 1 ms)** relational queries without requiring external database services (PostgreSQL/MySQL), ensuring the evaluator can run the project out-of-the-box.

### 2. Retrieval-Augmented Generation (RAG) for Store Policies
- **Handling PDF Extraction Anomalies:** The provided `políticas_da_loja.pdf` exhibited line-breaks between individual tokens upon raw extraction with `pypdf`. We engineered a **text stream normalizer** in [src/rag/ingestion.py](src/rag/ingestion.py) that reconstructs clean sentences prior to chunking.
- **Topic-Aware Semantic Chunking:** The document was segmented into topic-focused chunks using a sliding window of 130 words with a 30-word overlap, capturing section headers and page metadata.
- **Zero-Dependency BM25 Okapi Engine:** To ensure complete independence from external embedding API costs and network latency during local evaluation, we implemented an optimized **BM25 Okapi retriever** in pure Python ([src/rag/retriever.py](src/rag/retriever.py)). It delivers relevant matches in **0.001 s** while supporting Brazilian Portuguese tokenization and stopword filtering.

### 3. Model Agnostic & Resilient Fallback
- Full compatibility with modern providers: **Google Gemini (`gemini-2.5-flash` / `gemini-1.5-flash`)** via the modern `google-genai` SDK and **OpenAI (`gpt-4o-mini`)**.
- **Autonomous Deterministic Fallback:** If the evaluator runs the application without configuring API keys, the agent seamlessly operates in offline demonstration mode, ensuring zero runtime crashes and instant usability.

### 4. Persona & Domain Guardrails
- **Persona:** Warm, polite, professional, and equipped with deep luthier and musical expertise (tonewoods, string gauges, scale length, pickup configurations).
- **Core Business Guardrail (Crucial Rule):** The store **exclusively sells complete musical instruments** and **does not sell standalone accessories** (individual strings, loose picks, cables, strap-locks, standalone cases, effect pedals, or amps). The agent politely refuses accessory inquiries and suggests complete instruments.
- **Scope Guardrail:** Off-topic prompts (political debates, baking recipes, code generation) are cordially declined while steering the conversation back to music.

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.11+ installed.

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/snagh/emporio-da-musica-ai-agent.git
cd emporio-da-musica-ai-agent

python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables (Optional for Live API Execution)

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Provide your `GOOGLE_API_KEY` or `OPENAI_API_KEY`. If left empty, the agent runs in **Autonomous Local Mode** with identical business logic and zero API consumption.

### 4. Launch the Interactive CLI

```bash
python main.py
```

---

## 🧪 Automated Testing Suite

The repository includes **31 automated unit tests** covering data integrity, calculation of payment terms, RAG semantic retrieval, Pydantic tools, and agent guardrails:

```bash
python -m pytest -v
```

*All 31 tests pass in approximately 2.2 seconds.*

---

## 💬 Interaction Examples & Edge Cases

Transcripts are located in [`examples/`](examples/):

1. **`01_consulta_catalogo_e_precos.md`**: Budget-filtered query for acoustic guitars under R$ 1,000 with nylon string filtering.
2. **`02_politicas_devolucao_e_garantia.md`**: Store address inquiry and legal 7-day right of withdrawal for online purchases.
3. **`03_status_pedido_e_rastreamento.md`**: End-to-end order status tracking with carrier tracking codes and estimated arrival.
4. **`04_cenario_complexo_promocao_e_acessorios.md` (Complex Scenario)**: Customer inquires about loose guitar picks (politely declined per store policy), browses active promotion items, and computes the 5% instant PIX discount.

---

## 🔮 Known Limitations & Future Roadmap

With additional engineering bandwidth, the following improvements are prioritized:
1. **Session-Persistent Memory**: Integrating a Redis-backed or disk-persisted SQLite chat history indexed by `session_id`.
2. **Dense + Sparse Hybrid Search**: Adding 768-dimensional vector embeddings (`text-embedding-004`) coupled with a Cross-Encoder reranker.
3. **Omnichannel Messaging**: Providing an async FastAPI webhook for direct WhatsApp/Telegram integration (matching the store's primary sales channel).
4. **LangGraph Agentic State Machine**: Defining an explicit state graph with checkpointing and self-correcting feedback loops.

---

## 🤖 AI-Assisted Workflow Transparency

In compliance with the Artefact evaluation criteria, we transparently detail the usage of AI coding assistants:

- **Assistant Used:** **Google Antigravity** (Google's agentic pair-programming assistant powered by Gemini).
- **Workflow Highlights:**
  1. **Automated Exploratory Data Analysis:** Generating [scripts/inspect_data.py](scripts/inspect_data.py) to audit relational foreign-key integrity across all CSVs and identify whitespace corruption in the policies PDF.
  2. **Prompt Engineering:** Tailoring the System Prompt in [src/agent/prompts.py](src/agent/prompts.py) to enforce the store's commercial boundaries (accessory restrictions, 5% PIX discount, 12x credit card rules).
  3. **Comprehensive Unit Testing:** Crafting 31 pytest scenarios to prevent functional regressions.
- **Human Engineer Responsibility:**
  - Selecting an in-memory hybrid architecture over fragile Text-to-SQL.
  - Designing the token extraction and stopword sanitization algorithm.
  - Ensuring strict Conventional Commits across the Git development trajectory.
