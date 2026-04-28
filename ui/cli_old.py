#!/usr/bin/env python3
"""
ui/cli.py — Interfaccia CLI di JARVIS
Responsabilità UNICA: renderizzare UIEvent ricevuti dal controller.
Zero logica AI, zero comandi, zero stato business.

Dipende da:
  controller.jarvis_controller  ← unico import logico
  core.state                    ← solo get_status() per lo spinner
  core.commands                 ← solo get_help() per render /help
"""

import time
import itertools
import threading
from datetime import datetime

from rich.console import Console
from rich.panel   import Panel
from rich.text    import Text
from rich.align   import Align
from rich.table   import Table
from rich.live    import Live
from rich.rule    import Rule
from rich         import box

from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style as PTStyle
from prompt_toolkit.formatted_text import HTML

from controller.jarvis_controller import handle_input, UIEvent
from core.state    import get_status
from core.commands import get_help

# ─── Palette ─────────────────────────────────────────────────────────────────
RED        = "bold red"
DIM_RED    = "dim red"
BRIGHT_RED = "bright_red"
ORANGE     = "dark_orange"

console = Console()

BANNER = r"""
 ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
 ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
 ██║███████║██████╔╝██║   ██║██║███████╗
██╔╝██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║  ██║ ╚████╔╝ ██║███████║
  ╚════╝ ╚═╝  ╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
                   A R T I F I C I A L   I N T E L L I G E N C E
"""

# ─── Render helpers — SOLO output visivo ─────────────────────────────────────

def render_banner():
    console.clear()
    console.print(Text(BANNER, style=RED, justify="center"))
    now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    console.print(Align.center(Text(f"SISTEMA ONLINE  ●  {now}", style=DIM_RED)))
    console.print(Rule(style="red"))
    console.print()


def render_jarvis_panel(text: str):
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
    ollama_ok    = info.get("ollama", False)
    model        = info.get("model", "—")
    history_len  = info.get("history_len", 0)
    updated_at   = info.get("memory_updated_at", "—")
    avail_models = info.get("models_available", [])

    color = BRIGHT_RED if ollama_ok else DIM_RED
    label = "ONLINE" if ollama_ok else "OFFLINE / NON RAGGIUNGIBILE"

    table = Table(box=box.SIMPLE, border_style="red", show_header=False, padding=(0, 2))
    table.add_column("", style=DIM_RED)
    table.add_column("", style=BRIGHT_RED)
    table.add_row("Ollama",              f"[{color}]{label}[/]")
    table.add_row("Modello attivo",      model)
    table.add_row("Messaggi in memoria", str(history_len))
    table.add_row("Ultima sessione",     updated_at)
    table.add_row("Stato interno",       get_status())
    table.add_row("Ora sistema",         datetime.now().strftime("%H:%M:%S"))
    if avail_models:
        table.add_row("Modelli disponibili", "  ".join(avail_models[:6]))
    console.print(Panel(table, title="[bold red]// STATUS SISTEMA[/]", border_style="red"))
    console.print()


# ─── Spinner — legge get_status(), indipendente dal thread AI ────────────────

class ThinkingSpinner:
    _FRAMES   = ["◢", "◣", "◤", "◥"]
    _FALLBACK = ["ELABORAZIONE", "ANALISI IN CORSO", "CALCOLO RISPOSTA", "SISTEMI ATTIVI"]

    def __init__(self):
        self._stop = threading.Event()

    def _run(self):
        i = 0
        with Live(console=console, refresh_per_second=8) as live:
            while not self._stop.is_set():
                status = get_status().upper()
                label  = status if status not in ("IDLE", "") else self._FALLBACK[(i // 4) % 4]
                live.update(Text(f"  {self._FRAMES[i % 4]}  {label}...", style=RED))
                i += 1
                time.sleep(0.12)

    def start(self):
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def stop(self):
        self._stop.set()
        self._t.join()
        console.print()


# ─── Dispatch evento singolo (comandi slash) ──────────────────────────────────

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
            render_system_msg("Memoria conversazione azzerata.", BRIGHT_RED)
        case "help":
            render_help()
        case "status":
            render_status(event.payload or {})
        case "system_msg":
            render_system_msg(str(event.payload), BRIGHT_RED)
        case _:
            render_system_msg(f"Evento sconosciuto: {event.kind}", DIM_RED)
    return True


# ─── Streaming render — token per token ──────────────────────────────────────

def _render_ai_stream(event_gen) -> bool:
    """
    Consuma gli UIEvent AI dal controller:
      user_msg  → render_user_panel
      ai_chunk  → streaming live token per token
      ai_done   → chiude con pannello finale
      ai_error  → pannello errore

    Spinner attivo finché non arriva il primo ai_chunk.
    Ritorna False solo se arriva "exit".
    """
    spinner           = ThinkingSpinner()
    spinner.start()
    streaming_started = False

    for event in event_gen:

        if event.kind == "user_msg":
            render_user_panel(event.payload)
            continue

        if event.kind == "ai_chunk":
            if not streaming_started:
                spinner.stop()
                streaming_started = True
                # intestazione streaming
                console.print(Text("  // JARVIS  ◈", style=DIM_RED))
            console.print(Text(event.payload, style=BRIGHT_RED), end="")
            continue

        if event.kind == "ai_done":
            if not streaming_started:
                spinner.stop()
            console.print()
            return True

        if event.kind == "ai_error":
            if not streaming_started:
                spinner.stop()
            console.print()
            render_jarvis_panel(f"[ERRORE SISTEMA]\n{event.payload}")
            return True

        # evento inatteso nel mezzo dello stream
        if not streaming_started:
            spinner.stop()
            streaming_started = True
        keep = _render_event(event)
        if not keep:
            return False

    if not streaming_started:
        spinner.stop()
    return True


# ─── Main loop ────────────────────────────────────────────────────────────────

def main():
    render_banner()
    render_jarvis_panel(
        "Sistemi online. Sono JARVIS, la tua intelligenza artificiale locale.\n"
        "Scrivi un messaggio o digita /help per i comandi disponibili."
    )

    session = PromptSession(style=PTStyle.from_dict({"prompt": "#cc2200 bold"}))

    while True:
        try:
            raw = session.prompt(
                HTML('<ansired><b>  ❯ COMANDO // </b></ansired>')
            ).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not raw:
            continue

        event_gen = handle_input(raw)
        first     = next(event_gen, None)
        if first is None:
            continue

        if first.kind == "user_msg":
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

    console.print(Rule(style="red"))
    console.print(Align.center(Text("JARVIS OFFLINE", style=RED)))
    console.print()
