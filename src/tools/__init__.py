"""Módulo central de ferramentas do Agente Empório da Música."""

from __future__ import annotations

from typing import Any, Callable

from src.tools.catalog_tools import (
    tool_get_product_details,
    tool_list_active_promotions,
    tool_list_categories,
    tool_search_catalog,
)
from src.tools.order_tools import tool_get_order_status


# Registro central das ferramentas disponíveis para execução
AVAILABLE_TOOLS: dict[str, Callable[..., str]] = {
    "search_catalog": tool_search_catalog,
    "get_product_details": tool_get_product_details,
    "list_active_promotions": tool_list_active_promotions,
    "list_categories": tool_list_categories,
    "get_order_status": tool_get_order_status,
}


def execute_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """Executa a ferramenta solicitada pelo LLM e retorna o resultado em JSON formatado."""
    if tool_name not in AVAILABLE_TOOLS:
        return f'{{"error": "Ferramenta \'{tool_name}\' não encontrada no sistema."}}'
    
    fn = AVAILABLE_TOOLS[tool_name]
    try:
        return fn(**arguments)
    except Exception as e:
        return f'{{"error": "Falha na execução da ferramenta \'{tool_name}\': {str(e)}"}}'
