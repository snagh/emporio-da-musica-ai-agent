"""Testes unitários para a camada RAG e recuperação de políticas da Empório da Música."""

import json
from src.rag.ingestion import chunk_policy_document, extract_and_clean_pdf
from src.rag.retriever import get_policy_knowledge_base
from src.tools.policy_tools import tool_search_policies


def test_pdf_extraction_and_cleaning():
    pages = extract_and_clean_pdf()
    assert len(pages) == 8
    # Verificar que o texto está normalizado sem quebras no meio de palavras
    assert "Empório da Música" in pages[1][1]
    assert "14 de Maio" in pages[0][1] or "14 de Maio" in pages[1][1]


def test_chunking_creates_meaningful_chunks():
    pages = extract_and_clean_pdf()
    chunks = chunk_policy_document(pages)
    assert len(chunks) > 10
    sections = {c.section for c in chunks}
    assert any("Horário" in s for s in sections)
    assert any("Pagamento" in s for s in sections)
    assert any("Trocas" in s or "Devoluções" in s for s in sections)


def test_bm25_retrieval_working_hours():
    kb = get_policy_knowledge_base()
    results = kb.query("qual o horário de funcionamento da loja?", top_k=2)
    assert len(results) > 0
    top_content = results[0]["content"].lower()
    assert "09:00" in top_content or "horário" in top_content or "sábado" in top_content


def test_bm25_retrieval_return_policy():
    kb = get_policy_knowledge_base()
    results = kb.query("posso devolver meu produto se me arrepender da compra?", top_k=2)
    assert len(results) > 0
    content = " ".join([r["content"].lower() for r in results])
    assert "7" in content or "arrependimento" in content or "devolução" in content


def test_bm25_retrieval_warranty():
    kb = get_policy_knowledge_base()
    results = kb.query("qual o prazo de garantia contra defeitos de fabricação?", top_k=2)
    assert len(results) > 0
    content = " ".join([r["content"].lower() for r in results])
    assert "90" in content or "garantia" in content


def test_tool_search_policies_success():
    raw_response = tool_search_policies(query="como funciona o pagamento com pix?")
    data = json.loads(raw_response)
    assert data["status"] == "success"
    assert data["total_matches"] > 0
    first_match = data["results"][0]
    assert "content" in first_match
    assert "page" in first_match
