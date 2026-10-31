"""Testes unitários para as ferramentas Pydantic/JSON expostas ao Agente."""

import json
from src.tools import AVAILABLE_TOOLS, execute_tool
from src.tools.catalog_tools import (
    tool_get_product_details,
    tool_list_active_promotions,
    tool_list_categories,
    tool_search_catalog,
)
from src.tools.order_tools import tool_get_order_status


def test_tool_registry():
    assert "search_catalog" in AVAILABLE_TOOLS
    assert "get_product_details" in AVAILABLE_TOOLS
    assert "list_active_promotions" in AVAILABLE_TOOLS
    assert "list_categories" in AVAILABLE_TOOLS
    assert "get_order_status" in AVAILABLE_TOOLS


def test_tool_search_catalog_success():
    raw_response = tool_search_catalog(query="Yamaha", max_price=1000.0)
    data = json.loads(raw_response)
    assert data["status"] == "success"
    assert data["count"] > 0
    assert data["results"][0]["price_brl"] <= 1000.0


def test_tool_search_catalog_scope_warning():
    # Pergunta sobre acessório avulso que a loja não vende
    raw_response = tool_search_catalog(query="palheta fender")
    data = json.loads(raw_response)
    assert data["status"] == "empty"
    assert "exclusivamente instrumentos musicais" in data["message"]


def test_tool_get_product_details():
    raw_response = tool_get_product_details(product_id=81)
    data = json.loads(raw_response)
    assert data["status"] == "success"
    assert data["product"]["product_id"] == 81
    assert "Yamaha C40" in data["product"]["name"]


def test_tool_get_product_details_not_found():
    raw_response = tool_get_product_details(product_id=999999)
    data = json.loads(raw_response)
    assert data["status"] == "not_found"


def test_tool_get_order_status_by_id():
    raw_response = tool_get_order_status(order_id=1)
    data = json.loads(raw_response)
    assert data["status"] == "success"
    assert len(data["orders"]) == 1
    assert data["orders"][0]["order_id"] == 1


def test_tool_get_order_status_by_customer():
    raw_response = tool_get_order_status(customer_identifier="Lucas Mendes")
    data = json.loads(raw_response)
    assert data["status"] == "success"
    assert len(data["orders"]) >= 1


def test_tool_list_active_promotions():
    raw_response = tool_list_active_promotions()
    data = json.loads(raw_response)
    assert data["status"] == "success"
    assert data["total_active"] == 4


def test_execute_tool_dispatcher():
    result = execute_tool("list_categories", {})
    data = json.loads(result)
    assert data["status"] == "success"
    assert len(data["categories"]) == 9
