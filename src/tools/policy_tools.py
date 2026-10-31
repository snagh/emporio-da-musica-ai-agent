"""Ferramenta de busca semântica em políticas internas da loja para o Agente."""

from __future__ import annotations

import json
from pydantic import BaseModel, Field
from src.rag.retriever import get_policy_knowledge_base


class PolicySearchInput(BaseModel):
    query: str = Field(
        ...,
        description="Dúvida ou tema sobre as políticas da loja (ex: 'regras de devolução e arrependimento', 'horário de funcionamento', 'garantia de instrumentos', 'formas de pagamento e parcelamento', 'prazos e frete para Campo Grande').",
    )
    top_k: int = Field(
        default=3,
        description="Número de trechos relevantes a recuperar (padrão: 3).",
    )


def tool_search_policies(query: str, top_k: int = 3) -> str:
    """Consulta o manual interno oficial de políticas e procedimentos da Empório da Música."""
    kb = get_policy_knowledge_base()
    matches = kb.query(query, top_k=top_k)

    if not matches:
        return json.dumps(
            {
                "status": "not_found",
                "message": "Nenhum trecho correspondente encontrado no manual de políticas para essa consulta.",
                "results": [],
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "status": "success",
            "total_matches": len(matches),
            "results": matches,
        },
        ensure_ascii=False,
        indent=2,
    )
