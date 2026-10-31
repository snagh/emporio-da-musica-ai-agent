"""Retriever híbrido e busca semântica para as políticas do Empório da Música."""

from __future__ import annotations

import math
import re
from typing import Any, Optional

from src.rag.ingestion import DocumentChunk, chunk_policy_document, extract_and_clean_pdf

STOPWORDS_PT = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "sobre", "entre",
    "e", "ou", "que", "se", "como", "mas", "qual", "quais", "quando", "onde",
    "meu", "minha", "seu", "sua", "nosso", "nossa", "eu", "ele", "ela", "eles", "elas",
    "é", "são", "foi", "ser", "ter", "tem", "há", "está", "estão",
}


def tokenize(text: str) -> list[str]:
    """Tokeniza texto em palavras normalizadas em caixa baixa, sem pontuação e stopwords."""
    words = re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b", text.lower())
    return [w for w in words if w not in STOPWORDS_PT and len(w) > 1]


class BM25Retriever:
    """Implementação limpa e performática do algoritmo BM25 Okapi em Python puro."""

    def __init__(self, chunks: list[DocumentChunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.corpus_size = len(chunks)
        self.doc_lengths: list[int] = []
        self.doc_token_counts: list[dict[str, int]] = []
        self.doc_freqs: dict[str, int] = {}

        total_length = 0
        for chunk in chunks:
            tokens = tokenize(f"{chunk.section} {chunk.content}")
            self.doc_lengths.append(len(tokens))
            total_length += len(tokens)

            counts: dict[str, int] = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            self.doc_token_counts.append(counts)

            for t in counts:
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_doc_len = (total_length / self.corpus_size) if self.corpus_size > 0 else 1.0

        # Cálculo de IDF com correção
        self.idf: dict[str, float] = {}
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Busca os top_k chunks mais relevantes para a consulta."""
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores: list[float] = [0.0] * self.corpus_size

        for term in query_tokens:
            term_idf = self.idf.get(term, 0.0)
            if term_idf <= 0.0:
                # Termo não existe no corpus
                continue

            for doc_idx, counts in enumerate(self.doc_token_counts):
                tf = counts.get(term, 0)
                if tf > 0:
                    doc_len = self.doc_lengths[doc_idx]
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    scores[doc_idx] += term_idf * (numerator / denominator)

        ranked_indices = sorted(range(self.corpus_size), key=lambda i: scores[i], reverse=True)

        results: list[dict[str, Any]] = []
        for idx in ranked_indices[:top_k]:
            if scores[idx] > 0.01:
                chunk = self.chunks[idx]
                results.append({
                    "score": round(scores[idx], 4),
                    "section": chunk.section,
                    "page": chunk.page,
                    "content": chunk.content,
                })

        return results


class PolicyKnowledgeBase:
    """Singleton gerenciador da base de conhecimento de políticas da loja."""

    _instance: Optional[PolicyKnowledgeBase] = None
    _retriever: Optional[BM25Retriever] = None

    def __new__(cls) -> PolicyKnowledgeBase:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_retriever(self) -> BM25Retriever:
        if self._retriever is None:
            pages = extract_and_clean_pdf()
            chunks = chunk_policy_document(pages)
            self._retriever = BM25Retriever(chunks)
        return self._retriever

    def query(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        return self.get_retriever().retrieve(query, top_k=top_k)


def get_policy_knowledge_base() -> PolicyKnowledgeBase:
    return PolicyKnowledgeBase()
