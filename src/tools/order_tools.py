"""Ferramentas de consulta de status de pedidos, rastreamento e pós-venda para o Agente."""

from __future__ import annotations

import json
from typing import Optional
from pydantic import BaseModel, Field

from src.database.repository import find_orders_by_customer_identifier, get_order_by_id


class OrderStatusInput(BaseModel):
    order_id: Optional[int] = Field(
        default=None,
        description="ID numérico do pedido (ex: 1, 2, 3...). Use preferencialmente quando o cliente informar o número do pedido.",
    )
    customer_identifier: Optional[str] = Field(
        default=None,
        description="Nome, e-mail ou telefone do cliente caso ele não saiba o número do pedido.",
    )


def tool_get_order_status(
    order_id: Optional[int] = None,
    customer_identifier: Optional[str] = None,
) -> str:
    """Consulta o status de entrega, código de rastreio, itens e data prevista de um pedido."""
    if order_id is not None:
        order = get_order_by_id(order_id)
        if not order:
            return json.dumps(
                {"status": "not_found", "message": f"Pedido #{order_id} não localizado no sistema."},
                ensure_ascii=False,
            )
        return json.dumps({"status": "success", "orders": [order]}, ensure_ascii=False, indent=2)

    if customer_identifier:
        orders = find_orders_by_customer_identifier(customer_identifier)
        if not orders:
            return json.dumps(
                {
                    "status": "not_found",
                    "message": f"Nenhum pedido localizado associado a '{customer_identifier}'.",
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {"status": "success", "total_found": len(orders), "orders": orders},
            ensure_ascii=False,
            indent=2,
        )

    return json.dumps(
        {
            "status": "missing_parameters",
            "message": "Por favor, solicite ao cliente o número do pedido (order_id) ou o nome/e-mail/telefone cadastrado.",
        },
        ensure_ascii=False,
    )
