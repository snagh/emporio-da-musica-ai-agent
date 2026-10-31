"""Módulo de ingestão, normalização e chunking das políticas da loja (PDF)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pypdf
from src.config import settings


@dataclass
class DocumentChunk:
    chunk_id: str
    section: str
    page: int
    content: str

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "section": self.section,
            "page": self.page,
            "content": self.content,
        }


def extract_and_clean_pdf(pdf_path: Optional[Path] = None) -> list[tuple[int, str]]:
    """Extrai texto do PDF de políticas normalizando quebras de linha e espaçamentos corrompidos."""
    if pdf_path is None:
        matches = list(settings.DATA_DIR.glob("*.pdf"))
        if not matches:
            raise FileNotFoundError("Nenhum arquivo PDF encontrado em data/")
        pdf_path = matches[0]

    reader = pypdf.PdfReader(str(pdf_path))
    pages_text: list[tuple[int, str]] = []

    for page_num, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        # Normaliza espaços contínuos e quebras de linha token a token
        cleaned_text = " ".join(raw_text.split())
        pages_text.append((page_num, cleaned_text))

    return pages_text


def chunk_policy_document(pages_text: list[tuple[int, str]]) -> list[DocumentChunk]:
    """Segmenta o texto das políticas em chunks baseados em seções de negócio e tópicos."""
    chunks: list[DocumentChunk] = []

    # Regex para capturar tópicos numerados: ex '1. Sobre', '3. Formas de Pagamento', '4. Política de Trocas'
    section_regex = re.compile(r"(\b\d{1,2}(?:\.\d)?\.\s+[A-ZÀ-Ú][^.]+?)(?=\s+\d{1,2}(?:\.\d)?\.|\Z)")

    chunk_counter = 0

    for page_num, text in pages_text:
        # Se for a capa ou sumário
        if page_num == 1:
            chunks.append(
                DocumentChunk(
                    chunk_id=f"chunk_{chunk_counter}",
                    section="Apresentação e Dados da Loja",
                    page=page_num,
                    content=text,
                )
            )
            chunk_counter += 1
            continue

        # Segmentação por tamanho de janela com overlap se o texto for contínuo
        words = text.split()
        window_size = 130
        overlap = 30
        step = window_size - overlap

        for i in range(0, len(words), step):
            sub_words = words[i : i + window_size]
            sub_content = " ".join(sub_words)

            # Detectar seção predominante
            section_name = f"Políticas e Procedimentos (Pág. {page_num})"
            if "horário de funcionamento" in sub_content.lower():
                section_name = "Horário de Funcionamento e Atendimento"
            elif "formas de pagamento" in sub_content.lower() or "pix" in sub_content.lower() or "parcelamento" in sub_content.lower():
                section_name = "Formas de Pagamento e Parcelamento"
            elif "troca" in sub_content.lower() or "devolução" in sub_content.lower() or "arrependimento" in sub_content.lower():
                section_name = "Trocas, Devoluções e Arrependimento"
            elif "entrega" in sub_content.lower() or "frete" in sub_content.lower() or "envio" in sub_content.lower():
                section_name = "Frete, Entregas e Prazos"
            elif "garantia" in sub_content.lower() or "defeito" in sub_content.lower():
                section_name = "Garantia Legal e Fabricante"
            elif "lgpd" in sub_content.lower() or "privacidade" in sub_content.lower():
                section_name = "Privacidade e Proteção de Dados (LGPD)"
            elif "acessórios" in sub_content.lower() or "não comercializamos" in sub_content.lower():
                section_name = "Escopo de Produtos da Loja"

            chunks.append(
                DocumentChunk(
                    chunk_id=f"chunk_{chunk_counter}",
                    section=section_name,
                    page=page_num,
                    content=sub_content,
                )
            )
            chunk_counter += 1

    return chunks
