"""Esquemas de definição de ferramentas para os provedores de LLM (Gemini e OpenAI)."""

from __future__ import annotations

GEMINI_TOOLS_DECLARATIONS = [
    {
        "name": "search_catalog",
        "description": "Busca instrumentos musicais no catálogo da Empório da Música aplicando filtros de texto, categoria, preço máximo/mínimo e estoque.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Termo de busca textual (ex: 'yamaha', 'nylon', 'tagima', 'violão')."},
                "category": {"type": "STRING", "description": "Categoria (ex: 'Violões', 'Guitarras', 'Baixos', 'Teclados', 'Sopros')."},
                "max_price": {"type": "NUMBER", "description": "Preço máximo em reais (BRL)."},
                "min_price": {"type": "NUMBER", "description": "Preço mínimo em reais (BRL)."},
                "only_in_stock": {"type": "BOOLEAN", "description": "Se verdadeiro, filtra apenas instrumentos em estoque. Padrão: true."},
                "limit": {"type": "INTEGER", "description": "Quantidade máxima de instrumentos a retornar."},
            },
        },
    },
    {
        "name": "get_product_details",
        "description": "Recupera ficha técnica completa de um instrumento por ID (madeiras, cordas, estoque, descontos ativos e condições de pagamento).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "product_id": {"type": "INTEGER", "description": "ID numérico único do instrumento."},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "list_active_promotions",
        "description": "Lista todas as promoções e descontos atualmente vigentes no catálogo da loja.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        },
    },
    {
        "name": "list_categories",
        "description": "Lista as categorias de instrumentos musicais comercializadas pela Empório da Música.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        },
    },
    {
        "name": "get_order_status",
        "description": "Consulta o status de entrega, código de rastreamento e itens comprados de um pedido.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "order_id": {"type": "INTEGER", "description": "Número ID do pedido."},
                "customer_identifier": {"type": "STRING", "description": "Nome, e-mail ou telefone do cliente cadastrado."},
            },
        },
    },
    {
        "name": "search_policies",
        "description": "Consulta o manual interno oficial de políticas da loja (devolução, arrependimento em 7 dias, garantia, horários, endereço em Campo Grande e frete).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Dúvida ou tópico a pesquisar nas políticas internas."},
                "top_k": {"type": "INTEGER", "description": "Número de trechos relevantes a recuperar."},
            },
            "required": ["query"],
        },
    },
]

OPENAI_TOOLS_DECLARATIONS = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    k: {"type": v["type"].lower(), "description": v["description"]}
                    for k, v in t["parameters"].get("properties", {}).items()
                },
                "required": t["parameters"].get("required", []),
            },
        },
    }
    for t in GEMINI_TOOLS_DECLARATIONS
]
