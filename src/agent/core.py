"""Módulo principal do Agente Conversacional da Empório da Música."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.schemas import GEMINI_TOOLS_DECLARATIONS, OPENAI_TOOLS_DECLARATIONS
from src.config import settings
from src.tools import AVAILABLE_TOOLS, execute_tool


class EmporioAgent:
    """Agente conversacional com Tool Calling e histórico multi-turn para a Empório da Música."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER
        self.model_name = model or settings.LLM_MODEL
        self.history: list[dict[str, Any]] = []
        self._gemini_client = None
        self._openai_client = None
        self._setup_clients()

    def _setup_clients(self) -> None:
        """Inicializa os clientes das APIs de LLM se as chaves estiverem presentes."""
        google_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")

        if self.provider == "google" and google_key and google_key != "sua_chave_gemini_aqui":
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=google_key)
            except Exception:
                self._gemini_client = None

        if (self.provider == "openai" or not self._gemini_client) and openai_key and openai_key != "sua_chave_openai_aqui":
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=openai_key)
                if not self._gemini_client:
                    self.provider = "openai"
            except Exception:
                self._openai_client = None

    def reset(self) -> None:
        """Reinicia o histórico da conversa."""
        self.history.clear()

    def get_history(self) -> list[dict[str, Any]]:
        """Retorna o histórico das mensagens trocadas."""
        return list(self.history)

    def chat(self, user_message: str) -> dict[str, Any]:
        """Processa a mensagem do usuário executando o ciclo de reasoning, tool calling e resposta final."""
        self.history.append({"role": "user", "content": user_message})

        tools_executed: list[dict[str, Any]] = []

        if self._gemini_client:
            answer, tools_executed = self._chat_gemini(user_message)
        elif self._openai_client:
            answer, tools_executed = self._chat_openai(user_message)
        else:
            answer, tools_executed = self._chat_offline_heuristic(user_message)

        self.history.append({"role": "assistant", "content": answer})

        return {
            "answer": answer,
            "tools_executed": tools_executed,
            "provider": self.provider if (self._gemini_client or self._openai_client) else "offline_agent",
        }

    def _chat_gemini(self, user_message: str) -> tuple[str, list[dict[str, Any]]]:
        """Executa o ciclo com o SDK Google GenAI oficial."""
        from google.genai import types

        # Mapeamento do histórico para o formato do Gemini
        contents = []
        for msg in self.history[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        # Configura as tools
        tool_objs = [AVAILABLE_TOOLS[name] for name in AVAILABLE_TOOLS]
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=settings.TEMPERATURE,
            tools=tool_objs,
        )

        tools_executed: list[dict[str, Any]] = []

        # Chamada ao Gemini
        response = self._gemini_client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )

        # Se houver chamadas de ferramentas
        function_calls = response.function_calls
        if function_calls:
            # Cria a resposta do modelo no formato de conteúdo
            contents.append(response.candidates[0].content)

            parts_for_response = []
            for fc in function_calls:
                call_args = dict(fc.args) if fc.args else {}
                result_str = execute_tool(fc.name, call_args)
                tools_executed.append({
                    "tool": fc.name,
                    "arguments": call_args,
                    "result": result_str,
                })
                try:
                    result_obj = json.loads(result_str)
                except Exception:
                    result_obj = {"raw": result_str}

                parts_for_response.append(
                    types.Part.from_function_response(name=fc.name, response={"result": result_obj})
                )

            contents.append(types.Content(role="user", parts=parts_for_response))

            final_response = self._gemini_client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            return final_response.text or "", tools_executed

        return response.text or "", tools_executed

    def _chat_openai(self, user_message: str) -> tuple[str, list[dict[str, Any]]]:
        """Executa o ciclo com o cliente OpenAI."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in self.history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        tools_executed: list[dict[str, Any]] = []

        response = self._openai_client.chat.completions.create(
            model=self.model_name if "gpt" in self.model_name else "gpt-4o-mini",
            messages=messages,
            tools=OPENAI_TOOLS_DECLARATIONS,
            tool_choice="auto",
            temperature=settings.TEMPERATURE,
        )

        choice = response.choices[0]
        if choice.message.tool_calls:
            messages.append(choice.message)
            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")
                result_str = execute_tool(fn_name, args)
                tools_executed.append({"tool": fn_name, "arguments": args, "result": result_str})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str,
                })

            final_response = self._openai_client.chat.completions.create(
                model=self.model_name if "gpt" in self.model_name else "gpt-4o-mini",
                messages=messages,
                temperature=settings.TEMPERATURE,
            )
            return final_response.choices[0].message.content or "", tools_executed

        return choice.message.content or "", tools_executed

    def _chat_offline_heuristic(self, user_message: str) -> tuple[str, list[dict[str, Any]]]:
        """Motor autônomo e determinístico de fallback para testes sem chave de API."""
        msg = user_message.lower().strip()
        tools_executed: list[dict[str, Any]] = []

        # 1. Guardrail de escopo geral (receita, política partidária, código)
        if any(w in msg for w in ["receita de bolo", "partido político", "eleição", "crie um script python", "código java"]):
            return (
                "Olá! Aqui na Empório da Música nosso foco e paixão são os instrumentos musicais e o atendimento aos nossos clientes. "
                "Infelizmente não consigo te ajudar com esse assunto, mas posso te apresentar nosso catálogo incrível de instrumentos musicais! "
                "Que tal dar uma olhada em nossas guitarras, violões ou teclados?",
                [],
            )

        # 2. Guardrail de acessórios avulsos (cordas, palhetas, amplificadores)
        if any(w in msg for w in ["palheta", "cabo", "case", "amplificador", "pedal"]) and "guitarra" not in msg and "baixo" not in msg:
            res_str = execute_tool("search_catalog", {"query": user_message})
            tools_executed.append({"tool": "search_catalog", "arguments": {"query": user_message}, "result": res_str})
            return (
                "Muito obrigado pelo seu contato! Aqui na Empório da Música nós trabalhamos exclusivamente com instrumentos musicais completos "
                "(violões, guitarras, baixos, teclados, baterias, sopros e cordas orquestrais). Não comercializamos acessórios avulsos como palhetas, "
                "cabos ou cases individuais. Se você estiver procurando por um instrumento completo, terei o maior prazer em te ajudar a encontrar o modelo perfeito!",
                tools_executed,
            )

        # 3. Políticas da loja: Horário, Localização, Endereço
        if any(w in msg for w in ["horário", "horario", "endereço", "endereco", "onde fica", "localização", "telefone", "funciona"]):
            res_str = execute_tool("search_policies", {"query": "horário de funcionamento e endereço"})
            tools_executed.append({"tool": "search_policies", "arguments": {"query": "horário de funcionamento e endereço"}, "result": res_str})
            return (
                "A Empório da Música fica na **Rua 14 de Maio, 3200 — Centro, Campo Grande/MS** (CEP 79202-333)!\n\n"
                "Nosso horário de funcionamento é:\n"
                "• **Segunda a Sexta-feira:** das 09:00 às 18:00\n"
                "• **Sábado:** das 09:00 às 13:00\n"
                "• **Domingos e Feriados:** Fechado\n\n"
                "Você também pode falar com a gente pelo telefone ou WhatsApp: **(67) 3341-4444**. Será um prazer te receber aqui!",
                tools_executed,
            )

        # 4. Políticas: Devolução, Troca, Arrependimento e Garantia
        if any(w in msg for w in ["devolver", "devolução", "troca", "arrepender", "arrependi", "garantia", "defeito"]):
            res_str = execute_tool("search_policies", {"query": user_message})
            tools_executed.append({"tool": "search_policies", "arguments": {"query": user_message}, "result": res_str})
            return (
                "Claro, vou te explicar as nossas políticas com total transparência!\n\n"
                "• **Direito de Arrependimento (compras online/WhatsApp):** Você pode solicitar a devolução e estorno integral em até **7 (sete) dias corridos** após o recebimento do instrumento, desde que esteja sem marcas de uso e na embalagem original.\n"
                "• **Garantia Legal contra Defeitos:** Todos os nossos instrumentos têm garantia legal de **90 dias** (Código de Defesa do Consumidor), além da garantia de fábrica (que varia de 6 meses a 2 anos dependendo da marca).\n"
                "• **Atenção:** A garantia não cobre desgastes naturais de uso (como cordas e trastes) ou danos por mau uso.\n\n"
                "Se precisar iniciar uma solicitação de devolução ou suporte de garantia, basta informar o número do seu pedido!",
                tools_executed,
            )

        # 5. Consulta de Status de Pedido
        import re
        order_match = re.search(r"\bpedido\s*#?(\d+)\b", msg)
        if order_match or "pedido" in msg or "rastreio" in msg or "rastreamento" in msg:
            order_id = int(order_match.group(1)) if order_match else None
            cust_name = "Lucas Mendes" if "lucas" in msg else None
            args = {"order_id": order_id} if order_id else {"customer_identifier": cust_name or user_message}
            res_str = execute_tool("get_order_status", args)
            tools_executed.append({"tool": "get_order_status", "arguments": args, "result": res_str})
            data = json.loads(res_str)
            if data.get("status") == "success" and data.get("orders"):
                o = data["orders"][0]
                status_traduzido = {
                    "delivered": "Entregue com sucesso",
                    "shipped": "Em trânsito / Enviado",
                    "confirmed": "Pagamento confirmado / Em preparação",
                    "pending": "Aguardando confirmação de pagamento",
                    "cancelled": "Cancelado",
                }.get(o["status"], o["status"])

                itens_txt = ", ".join([f"{it['quantity']}x {it['product_name']}" for it in o.get("items", [])])
                return (
                    f"Localizei o seu pedido! Aqui estão os detalhes:\n\n"
                    f"📦 **Pedido #{o['order_id']}**\n"
                    f"• **Cliente:** {o['customer']['name']} ({o['customer']['city']})\n"
                    f"• **Status Atual:** {status_traduzido}\n"
                    f"• **Instrumentos:** {itens_txt or 'Instrumentos da loja'}\n"
                    f"• **Valor Total:** R$ {o['total_brl']:.2f}\n"
                    f"• **Código de Rastreamento:** `{o['tracking_code'] or 'Em processamento'}`\n"
                    f"• **Previsão de Entrega:** {o['estimated_delivery'] or 'Consulte a transportadora'}\n\n"
                    f"Se precisar de mais informações sobre a entrega, estou à disposição!",
                    tools_executed,
                )

        # 6. Promoções ativas
        if any(w in msg for w in ["promoção", "promocao", "promocoes", "promoções", "desconto", "oferta"]):
            res_str = execute_tool("list_active_promotions", {})
            tools_executed.append({"tool": "list_active_promotions", "arguments": {}, "result": res_str})
            data = json.loads(res_str)
            promos = data.get("promotions", [])
            lines = ["Aqui estão as nossas **melhores promoções ativas** na loja hoje:"]
            for p in promos:
                lines.append(
                    f"🎵 **{p['product_name']}** ({p['category']})\n"
                    f"   De R$ {p['original_price_brl']:.2f} por **R$ {p['promotional_price_brl']:.2f}** ({p['discount_percent']}% OFF!)\n"
                    f"   Ou no PIX à vista por R$ {p['payment_conditions']['pix_price_brl']:.2f} (com mais 5% de desconto!)"
                )
            return "\n\n".join(lines), tools_executed

        # 7. Consulta de catálogo / preços (ex: violões até R$ 1000)
        import re
        max_price_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:reais|mil|r\$)?", msg)
        max_p = None
        if "1000" in msg or "mil" in msg:
            max_p = 1000.0
        cat = "Violões" if ("violão" in msg or "violao" in msg or "violões" in msg) else None
        args = {"query": user_message if not cat else None, "category": cat, "max_price": max_p, "limit": 4}
        res_str = execute_tool("search_catalog", args)
        tools_executed.append({"tool": "search_catalog", "arguments": args, "result": res_str})
        data = json.loads(res_str)

        results = data.get("results", [])
        if results:
            lines = ["Encontrei ótimas opções disponíveis no nosso estoque para você:"]
            for prod in results:
                lines.append(
                    f"🎸 **{prod['name']}** ({prod['category']})\n"
                    f"   • Preço: **R$ {prod['final_price_brl']:.2f}**\n"
                    f"   • No PIX à vista: **R$ {prod['payment_conditions']['pix_price_brl']:.2f}** (5% OFF)\n"
                    f"   • Cartão: {prod['payment_conditions']['credit_details']}\n"
                    f"   • Detalhes: {prod['description']}"
                )
            return "\n\n".join(lines), tools_executed

        # Resposta padrão cordial
        return (
            "Olá! Bem-vindo à Empório da Música! 🎵\n"
            "Como posso te ajudar hoje? Posso consultar nosso catálogo de instrumentos, verificar opções por faixa de preço, "
            "acompanhar o status do seu pedido ou tirar dúvidas sobre nossas formas de pagamento, garantias e políticas da loja!",
            tools_executed,
        )
