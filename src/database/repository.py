"""Repositório de acesso e consultas estruturadas de negócio da Empório da Música."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional

from src.database.db import get_db_connection


def calculate_payment_options(price: float) -> dict[str, Any]:
    """Calcula as condições de pagamento oficiais da Empório da Música."""
    pix_price = round(price * 0.95, 2)  # 5% de desconto no PIX
    
    # Parcelamento sem juros: até 12x com parcela mínima de R$ 100
    max_installments = 1
    if price >= 100.0:
        max_installments = min(12, int(price // 100))
        # Se for até 3x, parcela mínima é R$ 50
        if max_installments < 3 and price >= 150:
            max_installments = 3
    
    installment_value = round(price / max_installments, 2) if max_installments > 0 else price

    return {
        "pix_price_brl": pix_price,
        "pix_discount_percent": 5,
        "max_installments": max_installments,
        "installment_value_brl": installment_value,
        "credit_details": f"Em até {max_installments}x de R$ {installment_value:.2f} sem juros no cartão",
    }


def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    only_in_stock: bool = True,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Busca produtos no catálogo da loja aplicando filtros flexíveis."""
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions: list[str] = ["p.status = 'active'"]
    params: list[Any] = []

    if only_in_stock:
        conditions.append("p.stock_quantity > 0")

    if max_price is not None:
        conditions.append("p.price_brl <= ?")
        params.append(max_price)

    if min_price is not None:
        conditions.append("p.price_brl >= ?")
        params.append(min_price)

    if category:
        conditions.append("(c.name LIKE ? OR c.description LIKE ?)")
        cat_term = f"%{category.strip()}%"
        params.extend([cat_term, cat_term])

    if query:
        import re
        stop_words = {"quanto", "custa", "qual", "preco", "preço", "valor", "o", "a", "os", "as", "de", "do", "da", "em", "para", "com", "tem", "voce", "voces"}
        raw_words = re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b", query.lower())
        tokens = [w for w in raw_words if w not in stop_words and len(w) > 1]
        
        if tokens:
            for token in tokens:
                token_term = f"%{token}%"
                conditions.append("(LOWER(p.name) LIKE ? OR LOWER(p.description) LIKE ? OR LOWER(p.specs) LIKE ?)")
                params.extend([token_term, token_term, token_term])
        else:
            query_term = f"%{query.strip().lower()}%"
            conditions.append("(LOWER(p.name) LIKE ? OR LOWER(p.description) LIKE ? OR LOWER(p.specs) LIKE ?)")
            params.extend([query_term, query_term, query_term])

    where_clause = " AND ".join(conditions)
    sql = f"""
        SELECT 
            p.product_id,
            p.name,
            p.price_brl,
            p.stock_quantity,
            p.specs,
            p.description,
            c.name as category_name,
            pr.discount_percent,
            pr.description as promo_description
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN promotions pr ON p.product_id = pr.product_id AND pr.is_active = 1
        WHERE {where_clause}
        ORDER BY p.price_brl ASC
        LIMIT ?
    """
    params.append(limit)

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        price = float(row["price_brl"])
        discount_percent = float(row["discount_percent"]) if row["discount_percent"] else 0.0
        final_price = round(price * (1.0 - discount_percent / 100.0), 2) if discount_percent > 0 else price

        specs_dict = {}
        if row["specs"]:
            try:
                specs_dict = json.loads(row["specs"])
            except Exception:
                pass

        results.append({
            "product_id": row["product_id"],
            "name": row["name"],
            "category": row["category_name"],
            "price_brl": price,
            "has_promo": discount_percent > 0,
            "discount_percent": discount_percent,
            "final_price_brl": final_price,
            "stock_quantity": row["stock_quantity"],
            "is_in_stock": row["stock_quantity"] > 0,
            "description": row["description"],
            "specs": specs_dict,
            "payment_conditions": calculate_payment_options(final_price),
        })

    return results


def get_product_by_id(product_id: int) -> Optional[dict[str, Any]]:
    """Recupera detalhes aprofundados de um produto específico."""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT 
            p.product_id,
            p.name,
            p.price_brl,
            p.stock_quantity,
            p.status,
            p.specs,
            p.description,
            c.name as category_name,
            pr.discount_percent,
            pr.description as promo_description
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN promotions pr ON p.product_id = pr.product_id AND pr.is_active = 1
        WHERE p.product_id = ?
    """
    cursor.execute(sql, (product_id,))
    row = cursor.fetchone()
    if not row:
        return None

    price = float(row["price_brl"])
    discount_percent = float(row["discount_percent"]) if row["discount_percent"] else 0.0
    final_price = round(price * (1.0 - discount_percent / 100.0), 2) if discount_percent > 0 else price

    specs_dict = {}
    if row["specs"]:
        try:
            specs_dict = json.loads(row["specs"])
        except Exception:
            pass

    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "category": row["category_name"],
        "status": row["status"],
        "price_brl": price,
        "discount_percent": discount_percent,
        "promo_description": row["promo_description"],
        "final_price_brl": final_price,
        "stock_quantity": row["stock_quantity"],
        "is_in_stock": row["stock_quantity"] > 0,
        "description": row["description"],
        "specs": specs_dict,
        "payment_conditions": calculate_payment_options(final_price),
    }


def get_order_by_id(order_id: int) -> Optional[dict[str, Any]]:
    """Consulta detalhes, status e itens de um pedido pelo seu ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql_order = """
        SELECT 
            o.order_id,
            o.order_date,
            o.status,
            o.total_brl,
            o.payment_method,
            o.tracking_code,
            o.estimated_delivery,
            o.notes,
            c.customer_id,
            c.name as customer_name,
            c.phone as customer_phone,
            c.email as customer_email,
            c.city as customer_city
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_id = ?
    """
    cursor.execute(sql_order, (order_id,))
    order_row = cursor.fetchone()
    if not order_row:
        return None

    # Consultar itens do pedido
    sql_items = """
        SELECT 
            oi.quantity,
            p.product_id,
            p.name as product_name,
            p.price_brl
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
    """
    cursor.execute(sql_items, (order_id,))
    items_rows = cursor.fetchall()

    items = [
        {
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "unit_price_brl": float(item["price_brl"]),
            "quantity": item["quantity"],
            "subtotal_brl": round(float(item["price_brl"]) * item["quantity"], 2),
        }
        for item in items_rows
    ]

    return {
        "order_id": order_row["order_id"],
        "customer": {
            "customer_id": order_row["customer_id"],
            "name": order_row["customer_name"],
            "city": order_row["customer_city"],
        },
        "order_date": order_row["order_date"],
        "status": order_row["status"],
        "total_brl": float(order_row["total_brl"]),
        "payment_method": order_row["payment_method"],
        "tracking_code": order_row["tracking_code"],
        "estimated_delivery": order_row["estimated_delivery"],
        "notes": order_row["notes"],
        "items": items,
    }


def find_orders_by_customer_identifier(identifier: str) -> list[dict[str, Any]]:
    """Busca pedidos por telefone, e-mail ou nome parcial do cliente."""
    conn = get_db_connection()
    cursor = conn.cursor()

    clean_id = identifier.strip().lower()
    term = f"%{clean_id}%"

    sql = """
        SELECT DISTINCT o.order_id
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE LOWER(c.name) LIKE ? OR LOWER(c.email) LIKE ? OR c.phone LIKE ?
        ORDER BY o.order_date DESC
    """
    cursor.execute(sql, (term, term, term))
    order_ids = [row["order_id"] for row in cursor.fetchall()]

    orders = []
    for oid in order_ids:
        order_details = get_order_by_id(oid)
        if order_details:
            orders.append(order_details)
    return orders


def list_active_promotions() -> list[dict[str, Any]]:
    """Lista todas as promoções ativas na loja com os dados dos respectivos instrumentos."""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT 
            pr.promotion_id,
            pr.discount_percent,
            pr.description as promo_description,
            p.product_id,
            p.name as product_name,
            p.price_brl,
            p.stock_quantity,
            c.name as category_name
        FROM promotions pr
        JOIN products p ON pr.product_id = p.product_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE pr.is_active = 1
        ORDER BY pr.discount_percent DESC
    """
    cursor.execute(sql)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        price = float(r["price_brl"])
        discount = float(r["discount_percent"])
        discounted_price = round(price * (1.0 - discount / 100.0), 2)
        results.append({
            "promotion_id": r["promotion_id"],
            "product_id": r["product_id"],
            "product_name": r["product_name"],
            "category": r["category_name"],
            "discount_percent": discount,
            "original_price_brl": price,
            "promotional_price_brl": discounted_price,
            "campaign": r["promo_description"],
            "is_in_stock": r["stock_quantity"] > 0,
            "payment_conditions": calculate_payment_options(discounted_price),
        })
    return results


def list_categories() -> list[dict[str, Any]]:
    """Retorna as categorias de instrumentos disponíveis na loja."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category_id, name, description FROM categories ORDER BY name ASC")
    return [
        {"category_id": r["category_id"], "name": r["name"], "description": r["description"]}
        for r in cursor.fetchall()
    ]
