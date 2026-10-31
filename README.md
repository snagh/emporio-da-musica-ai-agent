# Empório da Música - Agente de Atendimento Inteligente 🎵

Protótipo de Agente Conversacional desenvolvido como solução para o **Desafio Técnico de AI Engineer (2026)** da consultoria **Artefact**.

O agente atende clientes da loja fictícia **Empório da Música** (Campo Grande/MS), combinando raciocínio técnico sobre instrumentos musicais com **Function Calling** (dados estruturados) e **RAG** (políticas institucionais).

---

## 🏛️ Arquitetura do Projeto

```text
├── data/                                # Dados operacionais e manuais internos
│   ├── desafio_tecnico_ai_eng - *.csv  # Catálogo, clientes, pedidos e promoções
│   └── políticas_da_loja.pdf           # Manual de regras, garantias e horários
├── examples/                            # Transcrições reais de conversas (3 a 5 cenários)
├── scripts/
│   └── inspect_data.py                  # Script de análise exploratória e integridade
├── src/
│   ├── agent/                           # Orquestrador do Agente, Prompts e Persona
│   ├── database/                        # Ingestão em memória (SQLite) e views relacionais
│   ├── rag/                             # Ingestão do PDF, Chunks e Busca Semântica
│   ├── tools/                           # Ferramentas Pydantic (Catálogo, Pedidos, Políticas)
│   ├── ui/                              # Interface interativa CLI (Rich Terminal)
│   └── config.py                        # Configurações globais e pydantic-settings
├── tests/                               # Testes unitários automatizados
├── .env.example                         # Template de variáveis de ambiente
├── pyproject.toml                       # Metadados e dependências do projeto
└── requirements.txt                     # Pacotes necessários
```

---

## 🚀 Como Iniciar

### 1. Criar e ativar ambiente virtual (Python 3.11+)

```bash
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

### 3. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e adicione sua chave de API:

```bash
cp .env.example .env
```

### 4. Executar inspeção exploratória dos dados

```bash
python scripts/inspect_data.py
```

---

## 📊 Síntese dos Dados & Decisões de Modelagem

A inspeção executada via `scripts/inspect_data.py` revelou:

1. **Catálogo de Produtos (`products.csv`)**:
   - 65 instrumentos cadastrados (62 ativos e 3 inativos).
   - Preços variando de **R$ 159,90** a **R$ 19.567,00**.
   - Coluna `specs` em JSON com atributos de alto valor técnico (tampo, cordas nylon/aço, captadores, afinação).
2. **Integridade de Chaves**:
   - 100% de integridade referencial validada (zero chaves órfãs entre clientes, pedidos, itens de pedidos e promoções).
3. **Manual de Políticas (`políticas_da_loja.pdf`)**:
   - Regra estrita: **a loja NÃO vende acessórios avulsos** (cordas soltas, cabos, amplificadores, capas). O agente deve recusar educadamente essas buscas e direcionar para instrumentos.
   - Prazos: 7 dias corridos para devolução por arrependimento (compras online); 90 dias de garantia legal para defeitos.
   - Condições de pagamento: PIX à vista com 5% de desconto; Cartão de Crédito até 12x sem juros (parcela mínima R$ 100,00).
