"""Testes unitários para o banco de dados SQLite e repositório da Empório da Música."""

import pytest
from src.database.db import get_db_connection
from src.database.repository import (
    calculate_payment_options,
    find_orders_by_customer_identifier,
    get_order_by_id,
    get_product_by_id,
    list_active_promotions,
    list_categories,
    search_products,
)


def test_database_loads_all_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    tables = ["categories", "customers", "products", "orders", "order_items", "promotions"]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cursor.fetchone()["count"]
        assert count > 0, f"Tabela '{table}' deveria conter dados carregados."


def test_calculate_payment_options():
    # Preço R$ 1000: PIX R$ 950 (5% off), até 10x de R$ 100 s/ juros
    options = calculate_payment_options(1000.0)
    assert options["pix_price_brl"] == 950.0
    assert options["pix_discount_percent"] == 5
    assert options["max_installments"] == 10
    assert options["installment_value_brl"] == 100.0


def test_search_products_filter_price():
    # Violões até R$ 1000
    results = search_products(category="Violões", max_price=1000.0)
    assert len(results) > 0
    for prod in results:
        assert prod["price_brl"] <= 1000.0
        assert prod["category"] == "Violões"


def test_search_products_query_specs():
    # Buscar instrumento com madeira 'Spruce'
    results = search_products(query="Spruce")
    assert len(results) > 0
    for prod in results:
        specs_str = str(prod["specs"]).lower() + prod["name"].lower() + prod["description"].lower()
        assert "spruce" in specs_str


def test_get_product_by_id():
    prod = get_product_by_id(81)
    assert prod is not None
    assert prod["product_id"] == 81
    assert "Yamaha C40" in prod["name"]
    assert prod["stock_quantity"] > 0
    assert "payment_conditions" in prod


def test_get_order_by_id_with_items():
    order = get_order_by_id(1)
    assert order is not None
    assert order["order_id"] == 1
    assert len(order["items"]) > 0
    assert "customer" in order
    assert order["customer"]["name"] is not None


def test_find_orders_by_customer_identifier():
    orders = find_orders_by_customer_identifier("Lucas Mendes")
    assert len(orders) > 0
    assert orders[0]["order_id"] is not None


def test_list_active_promotions():
    promos = list_active_promotions()
    assert len(promos) == 4  # Conforme identificado na análise exploratória
    for promo in promos:
        assert promo["discount_percent"] > 0
        assert promo["promotional_price_brl"] < promo["original_price_brl"]


def test_list_categories():
    categories = list_categories()
    assert len(categories) == 9
    cat_names = [c["name"] for c in categories]
    assert "Guitarras" in cat_names
    assert "Violões" in cat_names
