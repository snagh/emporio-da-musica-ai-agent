# Empório da Música — Agente de Atendimento Inteligente 🎵

Protótipo de Agente Conversacional desenvolvido como solução para o **Desafio Técnico de AI Engineer (2026)** da consultoria **Artefact**.

O projeto resolve o problema de sobrecarga no atendimento da **Empório da Música** (loja tradicional fundada em 2008 em Campo Grande/MS), automatizando dúvidas recorrentes sobre catálogo de instrumentos, disponibilidade, preços, status de pedidos e políticas internas da loja através de **Tool Calling** e **RAG**.

---

## 📑 Sumário Executivo

1. [Visão Geral da Arquitetura](#-visão-geral-da-arquitetura)
2. [Justificativas Técnicas e Decisões de Design](#-justificativas-técnicas-e-decisões-de-design)
3. [Como Executar o Projeto](#-como-executar-o-projeto)
4. [Execução dos Testes Automatizados](#-execução-dos-testes-automatizados)
5. [Exemplos de Interação (Casos de Uso)](#-exemplos-de-interação-casos-de-uso)
6. [Limitações Conhecidas & Roadmap Futuro](#-limitações-conhecidas--roadmap-futuro)
7. [Transparência no Uso de Assistentes de IA](#-transparência-no-uso-de-assistentes-de-ia-workflow)

---

## 🏛️ Visão Geral da Arquitetura

O sistema adota uma **arquitetura híbrida desacoplada**, separando estritamente consultas a dados tabulares relacionais (via SQL) de consultas textuais normativas (via RAG):

```text
                               ┌────────────────────────────────┐
                               │     Cliente (Terminal CLI)     │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │   EmporioAgent (Orquestrador)  │
                               │  - Persona Empório da Música   │
                               │  - Histórico Multi-turn        │
                               │  - Guardrails de Escopo        │
                               └───────┬────────────────┬───────┘
                                       │                │
                   ┌───────────────────┴──┐          ┌──┴───────────────────┐
                   │ Structured Queries   │          │ Unstructured Policies│
                   ▼                      ▼          ▼                      ▼
        ┌──────────────────────┐  ┌─────────────┐ ┌─────────────────────────┐
        │ search_catalog       │  │ order_status│ │ search_policies         │
        │ get_product_details  │  │ active_promo│ │ (Trocas, Devoluções,     │
        │ list_categories      │  └──────┬──────┘ │  Garantia, Horários)    │
        └──────────┬───────────┘         │        └────────────┬────────────┘
                   │                     │                     │
                   ▼                     ▼                     ▼
        ┌───────────────────────────────────────┐ ┌─────────────────────────┐
        │     SQLite In-Memory (:memory:)       │ │  BM25 Semantic Engine   │
        │ (Products, Orders, Customers, Promos) │ │ (Chunks do PDF com Meta)│
        └───────────────────────────────────────┘ └─────────────────────────┘
```

### Estrutura de Diretórios

```text
emporio-da-musica/
├── data/                                # Dados originais fornecidos pela loja
│   ├── desafio_tecnico_ai_eng - *.csv  # Tabelas operacionais
│   └── políticas_da_loja.pdf           # Manual institucional
├── examples/                            # 4 Transcrições completas de interações reais
│   ├── 01_consulta_catalogo_e_precos.md
│   ├── 02_politicas_devolucao_e_garantia.md
│   ├── 03_status_pedido_e_rastreamento.md
│   └── 04_cenario_complexo_promocao_e_acessorios.md
├── scripts/
│   └── inspect_data.py                  # Script exploratório com validação de chaves
├── src/
│   ├── agent/                           # Prompts, Persona, Schemas e Orquestrador
│   ├── database/                        # Ingestão SQLite em memória e queries
│   ├── rag/                             # Parser de PDF, chunker e BM25 retriever
│   ├── tools/                           # Schemas Pydantic e Tool Calling
│   ├── ui/                              # Interface CLI formatada com Rich
│   └── config.py                        # Pydantic Settings e variáveis de ambiente
├── tests/                               # 31 testes unitários automatizados (pytest)
│   ├── test_agent.py
│   ├── test_database.py
│   ├── test_rag.py
│   └── test_tools.py
├── .env.example                         # Template de variáveis de ambiente
├── pyproject.toml                       # Dependências e metadados
├── requirements.txt                     # Pacotes fixados
└── main.py                              # Entrypoint rápido da aplicação
```

---

## 🎯 Justificativas Técnicas e Decisões de Design

### 1. Framework e Abordagem do Agente: Híbrido com Tool Calling Nativo
- **Por que não um Text-to-SQL direto para o usuário?** Deixar o LLM gerar SQL arbitrário expõe o banco a riscos de injeção, alucinação de esquemas e respostas lentas. Optamos por **ferramentas determinísticas tipadas (Function Calling)** com contratos de dados validados via Pydantic (`search_catalog`, `get_order_status`, `search_policies`).
- **Por que SQLite em memória (`:memory:`)?** As tabelas totalizam algumas dezenas de kilobytes. Carregá-las em memória garante respostas em menos de **1 ms** sem dependências de infraestrutura de banco externo, tornando o projeto 100% autocontido para os avaliadores.

### 2. Retrieval-Augmented Generation (RAG) para Políticas
- **Desafio do PDF Original:** O arquivo `políticas_da_loja.pdf` possuía quebras de linha em cada palavra individualmente após a extração padrão do `pypdf`. Desenvolvemos um **normalizador de fluxo textual** em [src/rag/ingestion.py](file:///d:/Downloads/Desafio_Técnico_AI_Engineer_2026-20260616T150750Z-3-001/Desafio%20Técnico%20AI%20Engineer%202026/src/rag/ingestion.py) que restaura a integridade das frases antes do chunking.
- **Chunking Semântico:** Divisão orientada a tópicos com sobreposição (*sliding window* de 130 tokens com overlap de 30 tokens), preservando o número da página e o título da seção.
- **Motor BM25 Okapi Nativo:** Implementamos um retriever semântico baseado no algoritmo BM25 Okapi em Python puro ([src/rag/retriever.py](file:///d:/Downloads/Desafio_Técnico_AI_Engineer_2026-20260616T150750Z-3-001/Desafio%20Técnico%20AI%20Engineer%202026/src/rag/retriever.py)) com tokenização em português e remoção de stopwords. Isso permite que qualquer pessoa execute a busca semântica em **0,001 s** sem depender obrigatoriamente de chaves de API pagas ou serviços em nuvem.

### 3. Modelo e Provedor (Agnóstico e Resiliente)
- Suporte oficial aos modelos mais modernos e econômicos do mercado: **Google Gemini (`gemini-2.5-flash` / `gemini-1.5-flash`)** via SDK oficial `google-genai` e **OpenAI (`gpt-4o-mini`)**.
- **Modo Offline/Heurístico Determinístico:** Se nenhuma chave for fornecida no `.env`, o agente entra automaticamente em modo de fallback inteligente, permitindo validar o fluxo conversacional e todas as ferramentas sem gerar custos ou travar por falta de credenciais.

### 4. Persona e Guardrails de Negócio
- **Persona:** Especialista simpático, prestativo e com vocabulário técnico de luthieria/música (tampo maciço, escala, cordas de nylon, captação).
- **Guardrail de Escopo de Produtos (Regra de Ouro):** A loja **não vende acessórios avulsos** (cordas soltas, palhetas avulsas, cases individuais, cabos ou amplificadores). Quando perguntado, o agente não alucina: explica a política com simpatia e oferece instrumentos completos equivalentes.
- **Guardrail Fora de Escopo:** O agente recusa educadamente pedidos sobre receitas culinárias, disputas políticas ou código de computação.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- Python 3.11+ instalado.

### 1. Clonar o repositório e criar ambiente virtual

```bash
git clone https://github.com/snagh/emporio-da-musica-ai-agent.git
cd emporio-da-musica-ai-agent

python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente (Opcional para modo LLM em nuvem)

Copie o `.env.example` para `.env`:
```bash
cp .env.example .env
```
Preencha sua `GOOGLE_API_KEY` (Gemini) ou `OPENAI_API_KEY`. Se optar por não preencher nenhuma chave, o agente ativará automaticamente o **Modo Offline Demonstrativo**, executando todas as ferramentas perfeitamente.

### 4. Iniciar a CLI Interativa

```bash
python main.py
```

---

## 🧪 Execução dos Testes Automatizados

O projeto conta com **31 testes unitários** com 100% de sucesso, cobrindo banco de dados, repositório de consultas, motor RAG, ferramentas Pydantic e guardrails do agente:

```bash
python -m pytest -v
```

---

## 💬 Exemplos de Interação (Casos de Uso)

As transcrições completas geradas pelo agente estão salvas na pasta [`examples/`](file:///d:/Downloads/Desafio_Técnico_AI_Engineer_2026-20260616T150750Z-3-001/Desafio%20Técnico%20AI%20Engineer%202026/examples):

1. **`01_consulta_catalogo_e_precos.md`**: Filtro de violões até R$ 1.000,00 com busca de especificações (tampo e cordas de nylon).
2. **`02_politicas_devolucao_e_garantia.md`**: Consulta institucional sobre localização em Campo Grande/MS, horários e aplicação do prazo legal de 7 dias para devolução por arrependimento.
3. **`03_status_pedido_e_rastreamento.md`**: Consulta por ID de pedido com rastreamento dos Correios/transportadora e relação de itens.
4. **`04_cenario_complexo_promocao_e_acessorios.md` (Cenário Não Trivial)**: O cliente solicita acessórios avulsos (o agente recusa educadamente com base nas políticas da loja), consulta promoções ativas de instrumentos e confere a regra de 5% de desconto no PIX.

---

## 🔮 Limitações Conhecidas & Roadmap Futuro

O que faríamos com mais tempo de desenvolvimento:
1. **Histórico Persistente por Sessão / Redis**: Implementar armazenamento de histórico em Redis ou SQLite em disco indexado por `session_id`, permitindo que o cliente retome atendimentos passados.
2. **Embeddings Vetoriais Híbridos (Dense + Sparse)**: Integrar embeddings vetoriais de 768 dimensões (`text-embedding-004`) com re-ranking via Cross-Encoder para consultas institucionais ainda mais nuances.
3. **Interface Web / WhatsApp**: Criar um endpoint FastAPI com webhook compatível com a Evolution API / Twilio para atendimento direto via WhatsApp, alinhado com o canal principal da loja física.
4. **Agentic Router com LangGraph**: Construir um grafo de estados explícito com checkpointing e loops de reflexão/auto-correção caso o estoque de um produto acabe durante o atendimento.

---

## 🤖 Transparência no Uso de Assistentes de IA (Workflow)

Em estrita consonância com as orientações do edital da **Artefact**, documentamos o uso de ferramentas de IA durante a concepção e implementação desta solução:

- **Assistente Utilizado:** **Google Antigravity** (ambiente oficial de pair programming agentic da Google com modelo Gemini).
- **Como a IA foi utilizada no workflow:**
  1. **Análise Exploratória Automatizada:** Criação do script [scripts/inspect_data.py](file:///d:/Downloads/Desafio_Técnico_AI_Engineer_2026-20260616T150750Z-3-001/Desafio%20Técnico%20AI%20Engineer%202026/scripts/inspect_data.py) para auditar 100% da integridade referencial dos CSVs e detectar anomalias de formatação no PDF original da loja.
  2. **Engenharia de Prompt e Persona:** Refinamento do System Prompt em [src/agent/prompts.py](file:///d:/Downloads/Desafio_Técnico_AI_Engineer_2026-20260616T150750Z-3-001/Desafio%20Técnico%20AI%20Engineer%202026/src/agent/prompts.py) para incorporar as restrições estritas da loja (ausência de venda de acessórios avulsos, regras de parcelamento e desconto PIX de 5%).
  3. **Aceleração da Suite de Testes:** Elaboração de 31 casos de teste unitário no `pytest` para blindar o comportamento das ferramentas contra regressões.
- **Papel do Engenheiro Humano:**
  - Decisão arquitetural de descartar Text-to-SQL arbitrário em favor de **Function Calling determinístico** para segurança e confiabilidade.
  - Modelagem do banco em memória SQLite e estratégia de chunking semântico para o RAG.
  - Validação manual de todas as regras de negócio e versionamento atômico do Git commit a commit.
