"""Testes unitários para o Agente Conversacional e Guardrails."""

import pytest
from src.agent.core import EmporioAgent


@pytest.fixture
def agent():
    return EmporioAgent()


def test_agent_general_guardrails_off_topic(agent):
    # Pergunta fora de escopo (receita culinária)
    resp = agent.chat("Como faço para assar um bolo de chocolate fofinho?")
    answer = resp["answer"].lower()
    assert "empório da música" in answer or "instrumento" in answer
    assert "bolo" not in answer or "não consigo" in answer or "foco" in answer


def test_agent_accessory_scope_guardrails(agent):
    # Pergunta sobre palhetas avulsas que a loja não comercializa
    resp = agent.chat("Vocês vendem palheta de guitarra?")
    answer = resp["answer"].lower()
    assert "exclusivamente" in answer or "não comercializamos" in answer or "instrumentos" in answer


def test_agent_catalog_search_violao(agent):
    # Consulta de violões até R$ 1000
    resp = agent.chat("Quais opções de violões disponíveis custando até R$ 1000?")
    answer = resp["answer"]
    assert "R$" in answer
    assert len(resp["tools_executed"]) > 0
    assert any(t["tool"] == "search_catalog" for t in resp["tools_executed"])


def test_agent_policies_store_address(agent):
    # Consulta de endereço e horário
    resp = agent.chat("Qual é o endereço da loja e o horário de funcionamento?")
    answer = resp["answer"]
    assert "14 de Maio" in answer
    assert "09:00" in answer
    assert any(t["tool"] == "search_policies" for t in resp["tools_executed"])


def test_agent_policies_return_period(agent):
    # Dúvida sobre devolução por arrependimento
    resp = agent.chat("Me arrependi da minha compra pela internet, posso devolver meu pedido?")
    answer = resp["answer"]
    assert "7" in answer or "sete" in answer
    assert any(t["tool"] == "search_policies" for t in resp["tools_executed"])


def test_agent_order_status(agent):
    # Consulta de pedido
    resp = agent.chat("Qual o status do pedido 1?")
    answer = resp["answer"]
    assert "Pedido #1" in answer or "1" in answer
    assert any(t["tool"] == "get_order_status" for t in resp["tools_executed"])


def test_agent_multi_turn_history(agent):
    agent.reset()
    assert len(agent.get_history()) == 0
    agent.chat("Olá!")
    agent.chat("Vocês têm promoções?")
    assert len(agent.get_history()) == 4  # 2 user + 2 assistant
