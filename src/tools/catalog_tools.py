"""Ferramentas de consulta de catálogo, produtos, categorias e promoções para o Agente."""

from __future__ import annotations

import json
from typing import Any, Optional
from pydantic import BaseModel, Field

from src.database.repository import (
    get_product_by_id,
    list_active_promotions,
    list_categories,
    search_products,
)


class SearchCatalogInput(BaseModel):
    query: Optional[str] = Field(
        default=None,
        description="Termo de busca textual para encontrar instrumentos (ex: 'violão nylon', 'yamaha', 'stratocaster', 'teclado').",
    )
    category: Optional[str] = Field(
        default=None,
        description="Categoria do instrumento (ex: 'Guitarras', 'Baixos', 'Violões', 'Teclados', 'Baterias e Percussão', 'Sopros').",
    )
    max_price: Optional[float] = Field(
        default=None,
        description="Preço máximo em reais (BRL). Útil quando o cliente estabelece um teto de orçamento (ex: 'até R$ 1000').",
    )
    min_price: Optional[float] = Field(
        default=None,
        description="Preço mínimo em reais (BRL).",
    )
    only_in_stock: bool = Field(
        default=True,
        description="Se verdadeiro, lista apenas produtos disponíveis em estoque físico. Padrão: True.",
    )
    limit: int = Field(
        default=5,
        description="Quantidade máxima de resultados para retornar (padrão: 5).",
    )


class ProductDetailsInput(BaseModel):
    product_id: int = Field(
        ...,
        description="ID numérico único do produto para recuperar especificações completas, estoque e descontos.",
    )


def tool_search_catalog(
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    only_in_stock: bool = True,
    limit: int = 5,
) -> str:
    """Busca instrumentos musicais no catálogo da Empório da Música aplicando filtros de preço, categoria e disponibilidade."""
    results = search_products(
        query=query,
        category=category,
        max_price=max_price,
        min_price=min_price,
        only_in_stock=only_in_stock,
        limit=limit,
    )

    if not results:
        msg = "Nenhum produto encontrado com os filtros fornecidos."
        if query and any(term in query.lower() for term in ["corda", "palheta", "cabo", "amplificador", "case", "pedal"]):
            msg += (
                " Nota de escopo: A Empório da Música comercializa exclusivamente instrumentos musicais "
                "completos e não vende acessórios avulsos (como encordoamentos avulsos, palhetas ou amplificadores)."
            )
        return json.dumps({"status": "empty", "message": msg, "results": []}, ensure_ascii=False)

    return json.dumps(
        {
            "status": "success",
            "count": len(results),
            "results": results,
        },
        ensure_ascii=False,
        indent=2,
    )


def tool_get_product_details(product_id: int) -> str:
    """Obtém informações aprofundadas de um instrumento por ID (madeiras, escala, estoque, desconto e condições de pagamento)."""
    product = get_product_by_id(product_id)
    if not product:
        return json.dumps(
            {"status": "not_found", "message": f"Produto com ID {product_id} não encontrado no catálogo."},
            ensure_ascii=False,
        )
    return json.dumps({"status": "success", "product": product}, ensure_ascii=False, indent=2)


def tool_list_active_promotions() -> str:
    """Retorna todas as promoções e descontos atualmente vigentes no catálogo da loja."""
    promotions = list_active_promotions()
    if not promotions:
        return json.dumps(
            {"status": "no_promotions", "message": "No momento não há promoções ativas cadastradas.", "promotions": []},
            ensure_ascii=False,
        )
    return json.dumps(
        {"status": "success", "total_active": len(promotions), "promotions": promotions},
        ensure_ascii=False,
        indent=2,
    )


def tool_list_categories() -> str:
    """Retorna a lista oficial de categorias de instrumentos musicais comercializados pela loja."""
    categories = list_categories()
    return json.dumps({"status": "success", "categories": categories}, ensure_ascii=False, indent=2)
