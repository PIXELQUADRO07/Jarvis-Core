"""
ui/cli.py — JARVIS PRO CLI
Features:
  • Animated "Thinking…" spinner
  • AI response panel with Markdown rendering (rich.Markdown)
  • Live streaming panel (rich.Live)
  • Token counter in footer
  • Tab autocomplete for /slash commands
  • Persistent history across sessions (FileHistory)
  • Multiline input (Shift+Enter)
  • Silent mode
  • Multi-language support
"""
import itertools
import threading
import time
from datetime import datetime
from pathlib import Path

from rich.console    import Console
from rich.live       import Live
from rich.markdown   import Markdown
from rich.panel      import Panel
from rich.text       import Text
from rich.align      import Align
from rich.table      import Table
from rich.rule       import Rule
from rich            import box

from prompt_toolkit                   import PromptSession
from prompt_toolkit.history           import FileHistory
from prompt_toolkit.auto_suggest      import AutoSuggestFromHistory
from prompt_toolkit.completion        import WordCompleter
from prompt_toolkit.styles            import Style as PTStyle
from prompt_toolkit.formatted_text    import HTML
from prompt_toolkit.key_binding       import KeyBindings

from controller.jarvis_controller import handle_input, UIEvent
from core.state    import get_status
from core.commands import get_help
from core.voice    import speak_text
from core.voice_queue import pop_complete_sentence
from core.i18n     import t, get_language
from config        import get_config
from logger        import error as log_error

# ── Palette ───────────────────────────────────────────────────────────────────
RED    = "bold red"
DIM_R  = "dim red"
BRRED  = "bright_red"
ORANGE = "dark_orange"
GREEN  = "bold green"
YELLOW = "bold yellow"
GREY   = "dim white"

console = Console()

BANNER = r"""
 ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
 ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
 ██║███████║██████╔╝██║   ██║██║███████║
██╔╝██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║  ██║ ╚████╔╝ ██║███████║
  ╚════╝ ╚═╝  ╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
           A R T I F I C I A L   I N T E L L I G E N C E   P R O
"""

# ── Comandi per autocompletamento ─────────────────────────────────────────────
_ALL_COMMANDS = [
    "/help", "/h", "/tools", "/plugins", "/memory", "/m",
    "/model list", "/model set", "/model current",
    "/session create", "/session switch", "/session list",
    "/session current", "/session delete",
    "/search", "/export", "/clear", "/cleanup",
    "/status", "/s", "/config", "/history",
    "/lang it", "/lang en", "/lang es", "/lang fr", "/lang de",
    "/silent on", "/silent off",
    "/voice on", "/voice off", "/voice status", "/voice test",
    "/encrypt on", "/encrypt off",
    "/api on", "/api off",
    "/exit", "/quit",
]

# ── Render helpers ────────────────────────────────────────────────────────────

def render_banner():
    config = get_config()
    console.clear()
    console.print(Text(BANNER, style=RED, justify="center"))
    now  = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    lang = get_language().upper()
    voice_s = "🔊" if config.enable_voice else "🔇"
    silent_s = " · 🤫 SILENT" if config.silent_mode else ""
    console.print(Align.center(Text(
        f"ONLINE  ●  {now}  ●  {voice_s}  ●  LANG:{lang}{silent_s}", style=DIM_R
    )))
    console.print(Rule(style="red"))
    console.print()


def render_jarvis_panel(text: str, tokens: dict = None):
    """Render JARVIS response with optional Markdown and token footer."""
    config = get_config()
    if config.render_markdown:
        content = Markdown(text)
    else:
        content = Text(text, style=BRRED)

    footer = ""
    if config.show_token_count and tokens:
        p = tokens.get("prompt_tokens", 0)
        c = tokens.get("completion_tokens", 0)
        footer = f" [dim]● {p}+{c}={p+c} token[/]"

    console.print(Panel(
        content,
        title=f"[bold red]// JARVIS[/]{footer}",
        title_align="left",
        border_style="red",
        padding=(0, 2),
        box=box.HEAVY,
    ))
    console.print()


def render_user_panel(text: str):
    console.print(Align.right(Panel(
        Text(text, style=ORANGE),
        title="[dark_orange]// USER[/]",
        title_align="right",
        border_style="dark_orange",
        padding=(0, 2),
        box=box.SIMPLE,
    )))
    console.print()


def render_system_msg(text: str, style: str = DIM_R):
    console.print(f"  [dim]>[/] [{style}]{text}[/]")


def render_error_msg(text: str):
    console.print(f"  [bold red]✗[/] [bright_red]{text}[/]")


def render_success_msg(text: str):
    console.print(f"  [bold green]✓[/] [green]{text}[/]")


def render_help():
    table = Table(box=box.SIMPLE, border_style="red",
                  header_style=RED, show_header=True, padding=(0, 2))
    table.add_column("Command",     style=BRRED, no_wrap=True)
    table.add_column("Description", style=DIM_R)
    for cmd, desc in get_help().items():
        table.add_row(cmd, desc)
    console.print(Panel(table, title="[bold red]// COMMANDS[/]", border_style="red"))
    console.print()


def render_status(info: dict = None):
    config = get_config()
    if info is None:
        info = {}
    ok    = info.get("ollama", False)
    model = info.get("model", "—")
    models= info.get("models_available", [])

    color = BRRED if ok else DIM_R
    label = "🟢 ONLINE" if ok else "🔴 OFFLINE"

    table = Table(box=box.SIMPLE, border_style="red", show_header=False, padding=(0, 2))
    table.add_column("", style=DIM_R, width=28)
    table.add_column("", style=BRRED)
    table.add_row("Ollama",             f"[{color}]{label}[/]")
    table.add_row("Active model",       model)
    table.add_row("Language",           get_language().upper())
    table.add_row("Silent mode",        "ON" if config.silent_mode else "OFF")
    table.add_row("Internal state",     get_status())
    table.add_row("System time",        datetime.now().strftime("%H:%M:%S"))
    table.add_row("Plugins enabled",    str(config.enable_plugins))
    table.add_row("API server",         "ON" if config.enable_api else "OFF")
    if models:
        ms = ", ".join(models[:4]) + (f", +{len(models)-4}" if len(models) > 4 else "")
        table.add_row("Available models", ms)
    console.print(Panel(table, title="[bold red]// SYSTEM STATUS[/]", border_style="red"))
    console.print()


# ── Spinner "Thinking…" ───────────────────────────────────────────────────────

class ThinkingSpinner:
    _DOTS   = ["   ", ".  ", ".. ", "..."]
    _STATES = ["Thinking", "Processing", "Analyzing", "Responding"]

    def __init__(self):
        self._stop   = threading.Event()
        self._thread = None

    def _run(self):
        i = 0
        with Live(console=console, refresh_per_second=8, transient=True) as live:
            while not self._stop.is_set():
                status = get_status().upper()
                label  = self._STATES[(i // 4) % len(self._STATES)] \
                         if status in ("THINKING", "IDLE", "") \
                         else status.capitalize()
                dots = self._DOTS[i % len(self._DOTS)]
                live.update(Text.assemble(("  ◈ ", "bold red"), (f"{label}{dots}", "dim red")))
                i += 1
                time.sleep(0.12)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.5)


# ── Streaming live panel ──────────────────────────────────────────────────────

def _render_ai_stream(event_gen) -> bool:
    """
    Streaming AI con:
    - Spinner fino al primo token
    - Live panel that updates text in real time
    - Render Markdown finale nel pannello completo
    - Voce delegata al VoiceEngine
    - Contatore token nel footer
    """
    spinner       = ThinkingSpinner()
    spinner.start()

    full_response = ""
    speech_buffer = ""
    last_meta     = {}
    streaming     = False
    config        = get_config()
    live          = None  # rich.Live panel, created on first token

    def _panel_for(text: str, tokens: dict):
        content = Markdown(text) if config.render_markdown else Text(text, style=BRRED)
        footer = ""
        if config.show_token_count and tokens:
            p = tokens.get("prompt_tokens", 0)
            c = tokens.get("completion_tokens", 0)
            footer = f" [dim]● {p}+{c}={p + c} token[/]"
        return Panel(
            content,
            title=f"[bold red]// JARVIS[/]{footer}",
            title_align="left",
            border_style="red",
            padding=(0, 2),
            box=box.HEAVY,
        )

    try:
        for event in event_gen:

            if event.kind == "user_msg":
                render_user_panel(event.payload)
                continue

            if event.kind == "ai_chunk":
                chunk, meta = event.payload
                last_meta   = meta

                if not streaming:
                    spinner.stop()
                    streaming = True
                    live = Live(console=console, refresh_per_second=12, transient=True)
                    live.start()

                full_response += chunk
                speech_buffer += chunk

                # Render the text as it arrives, not just at the end.
                if live is not None:
                    live.update(_panel_for(full_response, last_meta))

                # Estrai frasi per TTS in parallelo
                while True:
                    sentence, speech_buffer = pop_complete_sentence(speech_buffer)
                    if not sentence:
                        break
                    if config.enable_voice:
                        speak_text(sentence)
                continue

            if event.kind == "ai_done":
                spinner.stop()
                if live is not None:
                    live.stop()
                # Residuo TTS
                if speech_buffer.strip() and config.enable_voice:
                    speak_text(speech_buffer.strip())
                # Render finale (persistente, non transient come il Live panel)
                if full_response.strip():
                    render_jarvis_panel(full_response.strip(), last_meta)
                return True
    finally:
        if live is not None:
            live.stop()

        if event.kind == "ai_error":
            spinner.stop()
            err = str(event.payload)
            render_error_msg(err)
            if "raggiungibile" in err or "Ollama" in err:
                render_system_msg("Check: Ollama service must be running.", ORANGE)
            return True

        # Non-AI event during stream (e.g. system_msg from tool)
        if not streaming:
            spinner.stop()
            streaming = True
        keep = _render_event(event)
        if not keep:
            return False

    spinner.stop()
    return True


# ── Event routing ─────────────────────────────────────────────────────────────

def _render_event(event: UIEvent) -> bool:
    match event.kind:
        case "exit":
            render_system_msg("Shutting down systems. Goodbye.", RED)
            time.sleep(0.3)
            return False
        case "clear":
            render_banner()
        case "reset":
            render_success_msg(t("memory_cleared"))
        case "help":
            render_help()
        case "status":
            render_status(event.payload or {})
        case "banner_update":
            render_banner()
        case "system_msg":
            # Supports Markdown even in system messages
            text = str(event.payload)
            config = get_config()
            if config.render_markdown and ("**" in text or "```" in text or "#" in text):
                console.print(Panel(Markdown(text), border_style="dim red", box=box.SIMPLE))
            else:
                render_system_msg(text, BRRED)
        case "message":
            render_jarvis_panel(str(event.payload))
        case _:
            render_system_msg(f"Event: {event.kind}", DIM_R)
    return True


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    config = get_config()

    if config.show_banner:
        render_banner()

    render_jarvis_panel(
        f"{t('greeting')}\n{t('help_hint')}"
    )

    # Autocompletamento comandi slash
    completer = WordCompleter(_ALL_COMMANDS, pattern=r"[/\w\s-]+", sentence=True)

    # Cronologia persistente su file
    Path(".jarvis_history").touch(exist_ok=True)
    history = FileHistory(".jarvis_history")

    # Stile prompt
    pt_style = PTStyle.from_dict({
        "prompt":      "#cc2200 bold",
        "placeholder": "#444444 italic",
    })

    # Key bindings: Shift+Enter = newline (multiriga)
    kb = KeyBindings()

    @kb.add("escape", "enter")
    def _newline(event):
        event.current_buffer.insert_text("\n")

    session = PromptSession(
        style=pt_style,
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        complete_while_typing=True,
        key_bindings=kb,
        placeholder=t("input_hint"),
        multiline=False,
    )

    while True:
        try:
            raw = session.prompt(HTML("<ansired><b>❯ </b></ansired>")).strip()
        except KeyboardInterrupt:
            render_system_msg("Ctrl+C — use /exit to quit.", YELLOW)
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
            log_error(f"CLI loop error: {e}", exc=e)
            render_error_msg(f"Unexpected error: {e}")
            render_system_msg("Try again or use /help", ORANGE)

    console.print(Rule(style="red"))
    console.print(Align.center(Text("JARVIS PRO OFFLINE", style=RED)))
    console.print()
