"""Interface de Linha de Comando (CLI) Rica e Interativa para a Empório da Música."""

from __future__ import annotations

import sys
from pathlib import Path

# Configuração de encoding UTF-8
sys.stdout.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.agent.core import EmporioAgent
from src.config import settings

console = Console()


def show_banner(agent: EmporioAgent) -> None:
    """Exibe o cabeçalho oficial do terminal."""
    mode_desc = f"[bold green]{agent.provider.upper()}[/bold green]" if agent._gemini_client or agent._openai_client else "[bold yellow]OFFLINE / DETERMINÍSTICO (Sem API Key)[/bold yellow]"

    banner_text = (
        "[bold cyan]🎸 EMPÓRIO DA MÚSICA — ATENDIMENTO INTELIGENTE 🎵[/bold cyan]\n"
        "[dim]Sua música começa aqui • Campo Grande, MS • Fundada em 2008[/dim]\n\n"
        f"• [bold]Provedor Ativo:[/bold] {mode_desc}\n"
        f"• [bold]Modelo Configurado:[/bold] {agent.model_name}\n"
        f"• [bold]Comandos Úteis:[/bold] [italic]/limpar[/italic] (novo chat), [italic]/promocoes[/italic], [italic]/exportar[/italic], [italic]/sair[/italic]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))
    console.print()


def export_conversation_to_examples(history: list[dict], filename: str = "conversa_recente.md") -> Path:
    """Exporta a conversa para a pasta examples/ em formato Markdown."""
    examples_dir = settings.BASE_DIR / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)
    out_file = examples_dir / filename

    with open(out_file, mode="w", encoding="utf-8") as f:
        f.write("# Transcrição de Atendimento — Empório da Música\n\n")
        for turn in history:
            role_title = "**Cliente:**" if turn["role"] == "user" else "**Assistente Empório da Música:**"
            f.write(f"### {role_title}\n\n{turn['content']}\n\n---\n\n")

    return out_file


def main() -> None:
    """Loop principal de conversação no terminal."""
    agent = EmporioAgent()
    show_banner(agent)

    console.print("[dim]Assistente pronto! Digite sua dúvida ou mensagem abaixo:[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold green]Você[/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Atendimento encerrado. Até logo![/yellow]")
            break

        cleaned_input = user_input.strip()
        if not cleaned_input:
            continue

        # Comandos internos do terminal
        if cleaned_input.lower() in ["/sair", "sair", "exit", "quit"]:
            console.print("[yellow]Obrigado por falar com a Empório da Música! Até mais![/yellow]")
            break

        if cleaned_input.lower() in ["/limpar", "/clear", "clear"]:
            agent.reset()
            console.clear()
            show_banner(agent)
            console.print("[green]✓ Histórico de conversa reiniciado.[/green]\n")
            continue

        if cleaned_input.lower() in ["/promocoes", "/promos"]:
            cleaned_input = "Quais são as promoções ativas da loja hoje?"

        if cleaned_input.lower().startswith("/exportar"):
            parts = cleaned_input.split()
            fname = parts[1] if len(parts) > 1 else "conversa_exportada.md"
            if not fname.endswith(".md"):
                fname += ".md"
            saved_path = export_conversation_to_examples(agent.get_history(), fname)
            console.print(f"[green]✓ Conversa exportada com sucesso para: {saved_path}[/green]\n")
            continue

        # Processar resposta do agente
        with console.status("[bold cyan]Consultando dados e raciocinando...[/bold cyan]", spinner="dots"):
            response = agent.chat(cleaned_input)

        # Exibir ferramentas executadas se houver
        if response["tools_executed"]:
            for t in response["tools_executed"]:
                console.print(
                    f"  [dim cyan]↳ Tool Call: [bold]{t['tool']}[/bold]({t['arguments']})[/dim cyan]"
                )

        console.print()
        console.print(Panel(Markdown(response["answer"]), title="[bold blue]Empório da Música[/bold blue]", border_style="blue"))
        console.print()


if __name__ == "__main__":
    main()
