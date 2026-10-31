"""Script de Análise Exploratória e Validação Estrutural dos Dados.

Inspeciona tabelas operacionais (*.csv) e manual interno de políticas (*.pdf)
da 'Empório da Música', validando chaves de relacionamento, dados faltantes
e estrutura semântica para subsidiar o Agente e as Ferramentas.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Garantir UTF-8 no stdout
sys.stdout.reconfigure(encoding="utf-8")

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.tree import Tree
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def print_header(title: str) -> None:
    if RICH_AVAILABLE:
        console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))
    else:
        print(f"\n{'='*60}\n{title}\n{'='*60}")


def infer_type(val: str) -> str:
    if not val or val.strip() == "":
        return "empty"
    val = val.strip()
    if val.isdigit():
        return "int"
    try:
        float(val)
        return "float"
    except ValueError:
        pass
    if (val.startswith("{") and val.endswith("}")) or (val.startswith("[") and val.endswith("]")):
        try:
            json.loads(val)
            return "json"
        except Exception:
            pass
    if len(val) == 10 and val[4] == "-" and val[7] == "-":
        return "date"
    return "str"


def inspect_csvs() -> dict[str, list[dict[str, Any]]]:
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    datasets: dict[str, list[dict[str, Any]]] = {}

    print_header(f"📦 INSPEÇÃO DE CSVs ({len(csv_files)} arquivos encontrados)")

    for file_path in csv_files:
        clean_name = file_path.stem.split("-")[-1].strip().lower()
        rows: list[dict[str, Any]] = []

        with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            for row in reader:
                rows.append(row)

        datasets[clean_name] = rows

        # Coletar estatísticas de tipos e nulos
        col_types: dict[str, set[str]] = {col: set() for col in fieldnames}
        col_nulls: dict[str, int] = {col: 0 for col in fieldnames}

        for r in rows:
            for col in fieldnames:
                v = r.get(col, "")
                t = infer_type(v)
                if t == "empty":
                    col_nulls[col] += 1
                col_types[col].add(t)

        if RICH_AVAILABLE:
            table = Table(
                title=f"Tabela: [bold green]{clean_name}[/bold green] ({file_path.name}) - Total: {len(rows)} linhas",
                show_lines=True,
            )
            table.add_column("Coluna", style="bold yellow")
            table.add_column("Tipos Detectados", style="magenta")
            table.add_column("Valores Nulos", justify="right")
            table.add_column("Amostra (Linha 1)", style="dim")

            sample_row = rows[0] if rows else {}
            for col in fieldnames:
                types_str = ", ".join(sorted(col_types[col]))
                null_str = f"[red]{col_nulls[col]}[/red]" if col_nulls[col] > 0 else "[green]0[/green]"
                raw_sample = str(sample_row.get(col, ""))
                if len(raw_sample) > 55:
                    raw_sample = raw_sample[:52] + "..."
                table.add_row(col, types_str, null_str, raw_sample)

            console.print(table)
            console.print()
        else:
            print(f"\n--- {clean_name} ({len(rows)} linhas) ---")
            print(f"Colunas: {fieldnames}")
            if rows:
                print(f"Amostra: {rows[0]}")

    return datasets


def validate_relationships(datasets: dict[str, list[dict[str, Any]]]) -> None:
    print_header("🔗 VALIDAÇÃO DE INTEGRIDADE REFERENCIAL E RELACIONAMENTOS")

    # Mapeamentos de chaves
    categories = {r["category_id"]: r["name"] for r in datasets.get("categories", [])}
    customers = {r["customer_id"]: r["name"] for r in datasets.get("customers", [])}
    products = {r["product_id"]: r["name"] for r in datasets.get("products", [])}
    orders = {r["order_id"]: r for r in datasets.get("orders", [])}
    order_items = datasets.get("order_items", [])
    promotions = datasets.get("promotions", [])

    results: list[tuple[str, str, bool, str]] = []

    # 1. products.category_id -> categories.category_id
    orphan_cat = [
        p["product_id"] for p in datasets.get("products", [])
        if p.get("category_id") not in categories
    ]
    results.append((
        "products -> categories",
        "category_id",
        len(orphan_cat) == 0,
        f"0 órfãos de {len(datasets.get('products', []))} produtos" if not orphan_cat else f"{len(orphan_cat)} órfãos",
    ))

    # 2. orders.customer_id -> customers.customer_id
    orphan_cust = [
        o["order_id"] for o in datasets.get("orders", [])
        if o.get("customer_id") not in customers
    ]
    results.append((
        "orders -> customers",
        "customer_id",
        len(orphan_cust) == 0,
        f"0 órfãos de {len(datasets.get('orders', []))} pedidos" if not orphan_cust else f"{len(orphan_cust)} órfãos",
    ))

    # 3. order_items.order_id -> orders.order_id
    orphan_items_order = [
        item["order_id"] for item in order_items
        if item.get("order_id") not in orders
    ]
    results.append((
        "order_items -> orders",
        "order_id",
        len(orphan_items_order) == 0,
        f"0 órfãos de {len(order_items)} itens" if not orphan_items_order else f"{len(orphan_items_order)} órfãos",
    ))

    # 4. order_items.product_id -> products.product_id
    orphan_items_prod = [
        item["product_id"] for item in order_items
        if item.get("product_id") not in products
    ]
    results.append((
        "order_items -> products",
        "product_id",
        len(orphan_items_prod) == 0,
        f"0 órfãos de {len(order_items)} itens" if not orphan_items_prod else f"{len(orphan_items_prod)} órfãos",
    ))

    # 5. promotions.product_id -> products.product_id
    orphan_promo = [
        promo["product_id"] for promo in promotions
        if promo.get("product_id") not in products
    ]
    results.append((
        "promotions -> products",
        "product_id",
        len(orphan_promo) == 0,
        f"0 órfãos de {len(promotions)} promoções" if not orphan_promo else f"{len(orphan_promo)} órfãos",
    ))

    if RICH_AVAILABLE:
        table = Table(title="Cruzamento de Chaves Primárias / Estrangeiras", show_lines=True)
        table.add_column("Relação", style="bold cyan")
        table.add_column("Chave Estrangeira", style="yellow")
        table.add_column("Status Integridade", justify="center")
        table.add_column("Detalhes", style="dim")

        for rel, fk, valid, detail in results:
            status = "[bold green]✓ VÁLIDO[/bold green]" if valid else "[bold red]✗ INVÁLIDO[/bold red]"
            table.add_row(rel, fk, status, detail)
        console.print(table)
        console.print()
    else:
        for rel, fk, valid, detail in results:
            status = "OK" if valid else "FAIL"
            print(f"[{status}] {rel} ({fk}): {detail}")


def inspect_business_insights(datasets: dict[str, list[dict[str, Any]]]) -> None:
    print_header("📊 INSIGHTS OPERACIONAIS RELEVANTES PARA O AGENTE")

    # Status dos Pedidos
    orders = datasets.get("orders", [])
    order_statuses = Counter(o.get("status", "") for o in orders)

    # Promoções ativas
    promotions = datasets.get("promotions", [])
    active_promos = [p for p in promotions if p.get("is_active") == "1"]

    # Produtos
    products = datasets.get("products", [])
    active_prods = [p for p in products if p.get("status") == "active"]
    prices = [float(p["price_brl"]) for p in active_prods if p.get("price_brl")]

    if RICH_AVAILABLE:
        tree = Tree("[bold green]🎵 Empório da Música - Visão Geral do Sistema[/bold green]")

        p_node = tree.add(f"[bold]Catálogo de Produtos:[/bold] {len(products)} cadastrados ({len(active_prods)} ativos)")
        if prices:
            p_node.add(f"Faixa de preço: R$ {min(prices):.2f} até R$ {max(prices):.2f} (Média: R$ {sum(prices)/len(prices):.2f})")

        o_node = tree.add(f"[bold]Pedidos Registrados:[/bold] {len(orders)} pedidos")
        for st, count in order_statuses.items():
            o_node.add(f"Status '{st}': {count} pedido(s)")

        pr_node = tree.add(f"[bold]Promoções:[/bold] {len(promotions)} no total ({len(active_promos)} ativas no momento)")
        for promo in active_promos:
            pr_node.add(f"Produto #{promo['product_id']}: {promo['discount_percent']}% OFF - [italic]{promo['description']}[/italic]")

        # Exemplo de specs JSON
        sample_prod_with_specs = next((p for p in products if p.get("specs")), None)
        if sample_prod_with_specs:
            spec_node = tree.add(f"[bold]Exemplo de Atributos Técnicos (JSON Specs):[/bold] {sample_prod_with_specs['name']}")
            try:
                specs_dict = json.loads(sample_prod_with_specs["specs"])
                for k, v in list(specs_dict.items())[:6]:
                    spec_node.add(f"{k}: [cyan]{v}[/cyan]")
            except Exception:
                spec_node.add(f"Raw specs: {sample_prod_with_specs['specs']}")

        console.print(tree)
        console.print()
    else:
        print(f"Produtos: {len(products)} ({len(active_prods)} ativos)")
        print(f"Status pedidos: {dict(order_statuses)}")
        print(f"Promoções ativas: {len(active_promos)}")


def inspect_pdf_policies() -> None:
    print_header("📄 INSPEÇÃO DO MANUAL DE POLÍTICAS (PDF)")

    pdf_files = list(DATA_DIR.glob("*.pdf"))
    if not pdf_files:
        print("Nenhum arquivo PDF encontrado na pasta data/.")
        return

    pdf_path = pdf_files[0]
    if not PYPDF_AVAILABLE:
        print(f"Arquivo encontrado: {pdf_path.name}, mas pypdf não está instalado.")
        return

    reader = pypdf.PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    sections_found: list[tuple[int, str]] = []
    full_text = ""

    import re

    # Identificar tópicos no formato '1. Sobre a Empório da Música'
    section_pattern = re.compile(
        r"(\b\d{1,2}\.\s+[A-ZÀ-Ú][a-zA-ZÀ-ÿ\s–—\-]{2,50}?)(?=\s+[A-ZÀ-Ú][a-z]|\s+\d{1,2}\.|\Z)"
    )

    for idx, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        normalized = " ".join(raw.split())
        full_text += f"\n--- Página {idx+1} ---\n" + normalized
        
        matches = section_pattern.findall(normalized)
        for match in matches:
            cleaned_match = match.strip()
            # Filtro para evitar ruídos de pontuação ou números avulsos
            if any(cleaned_match.startswith(f"{i}.") for i in range(1, 15)):
                sections_found.append((idx + 1, cleaned_match))

    if RICH_AVAILABLE:
        table = Table(
            title=f"Manual de Políticas: [bold blue]{pdf_path.name}[/bold blue] ({total_pages} páginas)",
            show_lines=True,
        )
        table.add_column("Página", justify="center", style="yellow")
        table.add_column("Seção / Tópico Identificado", style="cyan")

        for page_num, section_title in sections_found:
            table.add_row(str(page_num), section_title)

        console.print(table)

        summary_panel = Panel(
            "[bold green]Destaques para o RAG:[/bold green]\n"
            "• [bold]Localização & Horários:[/bold] Rua 14 de Maio, 3200 - Centro, Campo Grande/MS. Seg-Sex 09h às 18h, Sáb 09h às 13h.\n"
            "• [bold]Formas de Pagamento:[/bold] PIX (5% desc), Débito, Crédito até 12x sem juros (parcela min R$100), Boleto à vista.\n"
            "• [bold]Trocas e Devoluções:[/bold] Direito de arrependimento (compras online) em até 7 dias corridos. Defeito: 90 dias.\n"
            "• [bold]Garantia:[/bold] Legal 90 dias + Fabricante (6m a 2a). Desgastes naturais (cordas, trastes) não cobertos.\n"
            "• [bold]Restrições de Catálogo:[/bold] A loja NÃO vende acessórios avulsos (cordas soltas, palhetas, cases, amplificadores).\n"
            "• [bold]LGPD & Segurança:[/bold] Dados cadastrais protegidos; respeita solicitações de exclusão do cliente.",
            title="Sumário Executivo das Regras de Negócio",
            border_style="green",
        )
        console.print(summary_panel)
    else:
        print(f"PDF {pdf_path.name}: {total_pages} páginas.")
        for p, s in sections_found:
            print(f"Página {p}: {s}")


def main() -> None:
    if not DATA_DIR.exists():
        print(f"Diretório de dados não encontrado em: {DATA_DIR}")
        sys.exit(1)

    datasets = inspect_csvs()
    validate_relationships(datasets)
    inspect_business_insights(datasets)
    inspect_pdf_policies()

    if RICH_AVAILABLE:
        console.print("\n[bold green]✓ Análise exploratória concluída com sucesso![/bold green]\n")


if __name__ == "__main__":
    main()
