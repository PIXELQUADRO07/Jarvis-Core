#!/usr/bin/env python3
"""
ui/cli.py — Interfaccia CLI di JARVIS
Responsabilità UNICA: renderizzare UIEvent ricevuti dal controller.
Zero logica AI, zero comandi, zero stato business.

Miglioramenti rispetto alla versione precedente:
- Stato "Thinking..." animato ispirato a Claude/ChatGPT
- Risposta AI raccolta e renderizzata in un pannello completo (non chunk raw)
- Prompt con stile moderno (❯) e gestione input robusta
- Voce delegata interamente a VoiceEngine (no doppio TTS)
"""

import itertools
import threading
import time
from datetime import datetime

from rich.console import Console
from rich.live    import Live
from rich.panel   import Panel
from rich.text    import Text
from rich.align   import Align
from rich.table   import Table
from rich.rule    import Rule
from rich         import box

from prompt_toolkit            import PromptSession
from prompt_toolkit.styles     import Style as PTStyle
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding    import KeyBindings

from controller.jarvis_controller import handle_input, UIEvent
from core.state    import get_status
from core.commands import get_help
from core.voice    import speak_text
from core.voice_queue import pop_complete_sentence
from config        import get_config
from logger        import error as log_error

# ─── Palette ──────────────────────────────────────────────────────────────────
RED        = "bold red"
DIM_RED    = "dim red"
BRIGHT_RED = "bright_red"
ORANGE     = "dark_orange"
GREEN      = "bold green"
YELLOW     = "bold yellow"
GREY       = "dim white"

console = Console()

BANNER = r"""
 ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
 ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
 ██║███████║██████╔╝██║   ██║██║███████║
██╔╝██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║  ██║ ╚████╔╝ ██║███████║
  ╚════╝ ╚═╝  ╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
               A R T I F I C I A L   I N T E L L I G E N C E
"""

# ─── Render helpers ───────────────────────────────────────────────────────────

def render_banner():
    console.clear()
    console.print(Text(BANNER, style=RED, justify="center"))
    now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    config = get_config()
    voice_status = "🔊 VOCE ON" if config.enable_voice else "🔇 MUTO"
    console.print(Align.center(Text(
        f"SISTEMA ONLINE  ●  {now}  ●  {voice_status}", style=DIM_RED
    )))
    console.print(Rule(style="red"))
    console.print()


def render_jarvis_panel(text: str):
    """Risposta completa di JARVIS in un pannello con bordo."""
    console.print(Panel(
        Text(text, style=BRIGHT_RED),
        title="[bold red]// JARVIS[/]",
        title_align="left",
        border_style="red",
        padding=(0, 2),
        box=box.HEAVY,
    ))
    console.print()


def render_user_panel(text: str):
    console.print(Align.right(Panel(
        Text(text, style=ORANGE),
        title="[dark_orange]// UTENTE[/]",
        title_align="right",
        border_style="dark_orange",
        padding=(0, 2),
        box=box.SIMPLE,
    )))
    console.print()


def render_system_msg(text: str, style: str = DIM_RED):
    console.print(f"  [dim]>[/] [{style}]{text}[/]")


def render_error_msg(text: str):
    console.print(f"  [bold red]✗[/] [bright_red]{text}[/]")


def render_success_msg(text: str):
    console.print(f"  [bold green]✓[/] [green]{text}[/]")


def render_help():
    table = Table(box=box.SIMPLE, border_style="red",
                  header_style=RED, show_header=True, padding=(0, 2))
    table.add_column("Comando",     style=BRIGHT_RED, no_wrap=True)
    table.add_column("Descrizione", style=DIM_RED)
    for cmd, desc in get_help().items():
        table.add_row(cmd, desc)
    console.print(Panel(table, title="[bold red]// COMANDI[/]", border_style="red"))
    console.print()


def render_status(info: dict = None):
    if info is None:
        info = {}
    ollama_ok = info.get("ollama", False)
    model     = info.get("model", "—")
    models    = info.get("models_available", [])

    color = BRIGHT_RED if ollama_ok else DIM_RED
    label = "🟢 ONLINE" if ollama_ok else "🔴 OFFLINE"

    table = Table(box=box.SIMPLE, border_style="red", show_header=False, padding=(0, 2))
    table.add_column("", style=DIM_RED, width=25)
    table.add_column("", style=BRIGHT_RED)
    table.add_row("Ollama",              f"[{color}]{label}[/]")
    table.add_row("Modello attivo",      model)
    table.add_row("Stato interno",       get_status())
    table.add_row("Ora sistema",         datetime.now().strftime("%H:%M:%S"))
    if models:
        model_str = ", ".join(models[:3])
        if len(models) > 3:
            model_str += f", ... (+{len(models)-3})"
        table.add_row("Modelli disponibili", model_str)
    else:
        table.add_row("Modelli disponibili", "[dim]nessuno rilevato[/]")

    console.print(Panel(table, title="[bold red]// STATUS SISTEMA[/]", border_style="red"))
    console.print()


# ─── Thinking Spinner ─────────────────────────────────────────────────────────

class ThinkingSpinner:
    """
    Spinner animato stile 'Claude thinking…' / ChatGPT.
    Mostra un indicatore animato con testo di stato mentre l'AI elabora.
    """
    _DOTS    = ["   ", ".  ", ".. ", "..."]
    _STATES  = ["Pensando", "Elaborando", "Analizzando", "Rispondo"]

    def __init__(self):
        self._stop   = threading.Event()
        self._thread = None

    def _run(self):
        i = 0
        with Live(console=console, refresh_per_second=8, transient=True) as live:
            while not self._stop.is_set():
                status = get_status().upper()
                label  = self._STATES[(i // 4) % len(self._STATES)] if status in ("THINKING", "IDLE", "") else status.capitalize()
                dots   = self._DOTS[i % len(self._DOTS)]
                line   = Text.assemble(
                    ("  ◈ ", "bold red"),
                    (f"{label}{dots}", "dim red"),
                )
                live.update(line)
                i += 1
                time.sleep(0.12)

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.5)


# ─── Event rendering ──────────────────────────────────────────────────────────

def _render_event(event: UIEvent) -> bool:
    """Renderizza un UIEvent non-AI. Ritorna False se il loop deve terminare."""
    match event.kind:
        case "exit":
            render_system_msg("Sistemi in spegnimento. Arrivederci.", RED)
            time.sleep(0.4)
            return False
        case "clear":
            render_banner()
        case "reset":
            render_success_msg("Memoria conversazione azzerata.")
        case "help":
            render_help()
        case "status":
            render_status(event.payload or {})
        case "banner_update":
            render_banner()
        case "system_msg":
            render_system_msg(str(event.payload), BRIGHT_RED)
        case "message":
            render_jarvis_panel(str(event.payload))
        case _:
            render_system_msg(f"Evento sconosciuto: {event.kind}", DIM_RED)
    return True


def _render_ai_stream(event_gen) -> bool:
    """
    Consuma gli UIEvent AI dal controller.
    - Mostra spinner "Thinking…" fino al primo token
    - Raccoglie tutti i chunk in un buffer
    - Al termine renderizza la risposta completa in un pannello
    - Delega la voce al VoiceEngine (già avviato da main.py)
    """
    spinner       = ThinkingSpinner()
    spinner.start()

    full_response = ""
    speech_buffer = ""
    streaming     = False
    config        = get_config()

    for event in event_gen:

        if event.kind == "user_msg":
            render_user_panel(event.payload)
            continue

        if event.kind == "ai_chunk":
            if not streaming:
                spinner.stop()
                streaming = True

            chunk = event.payload
            full_response += chunk
            speech_buffer += chunk

            # Estrai frasi complete per la voce (non-bloccante grazie al worker)
            while True:
                sentence, speech_buffer = pop_complete_sentence(speech_buffer)
                if not sentence:
                    break
                if config.enable_voice:
                    speak_text(sentence)
            continue

        if event.kind == "ai_done":
            spinner.stop()
            # Voce: residuo nel buffer
            if speech_buffer.strip() and config.enable_voice:
                speak_text(speech_buffer.strip())
            # Render risposta completa in pannello
            if full_response.strip():
                render_jarvis_panel(full_response.strip())
            return True

        if event.kind == "ai_error":
            spinner.stop()
            error_text = str(event.payload)
            render_error_msg(error_text)
            if "Ollama non raggiungibile" in error_text:
                render_system_msg(
                    "Assicurati che Ollama sia in esecuzione: ollama serve", ORANGE
                )
            return True

        # Altri eventi (es. system_msg da tool) durante lo stream
        if not streaming:
            spinner.stop()
            streaming = True
        keep = _render_event(event)
        if not keep:
            return False

    spinner.stop()
    return True


# ─── Main loop ────────────────────────────────────────────────────────────────

def main():
    """Entry point CLI principale."""
    config = get_config()

    if config.show_banner:
        render_banner()

    render_jarvis_panel(
        "Sistemi online. Sono JARVIS, la tua intelligenza artificiale locale.\n"
        "Scrivi un messaggio o digita [bold]/help[/] per i comandi disponibili."
    )

    # Stile prompt moderno
    pt_style = PTStyle.from_dict({
        "prompt":      "#cc2200 bold",
        "placeholder": "#555555 italic",
    })

    session = PromptSession(
        style=pt_style,
        placeholder="Scrivi un messaggio… (Invio per inviare)",
    )

    while True:
        try:
            raw = session.prompt(
                HTML("<ansired><b>❯ </b></ansired>"),
            ).strip()
        except KeyboardInterrupt:
            render_system_msg(
                "Interrotto (Ctrl+C). Digita /exit per uscire.", YELLOW
            )
            continue
        except EOFError:
            break

        if not raw:
            continue

        try:
            event_gen = handle_input(raw)
            first     = next(event_gen, None)
            if first is None:
                continue

            if first.kind in ("user_msg", "ai_chunk", "ai_done", "ai_error"):
                if not _render_ai_stream(itertools.chain([first], event_gen)):
                    break
                continue

            should_exit = False
            for ev in itertools.chain([first], event_gen):
                if not _render_event(ev):
                    should_exit = True
                    break
            if should_exit:
                break

        except Exception as e:
            log_error(f"Error in main loop: {e}", exc=e)
            render_error_msg(f"Errore inatteso: {e}")
            render_system_msg("Tenta di nuovo o digita /help", ORANGE)

    console.print(Rule(style="red"))
    console.print(Align.center(Text("JARVIS OFFLINE", style=RED)))
    console.print()
