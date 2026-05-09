#!/usr/bin/env python3
"""
JARVIS PRO — Entry point
Avvia: VoiceEngine, API server (opzionale), plugin manager, CLI.
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from logger import info, error


def parse_args():
    p = argparse.ArgumentParser(description="JARVIS PRO — Local AI Assistant")
    p.add_argument("--no-voice",   action="store_true", help="Disabilita voce")
    p.add_argument("--api",        action="store_true", help="Avvia API server REST")
    p.add_argument("--api-port",   type=int,            help="Porta API (default 8000)")
    p.add_argument("--lang",       type=str,            help="Lingua: it|en|es|fr|de")
    p.add_argument("--silent",     action="store_true", help="Modalità silenziosa")
    p.add_argument("--no-plugins", action="store_true", help="Disabilita plugin")
    p.add_argument("--cleanup",    action="store_true", help="Pulizia DB all'avvio ed esci")
    return p.parse_args()


if __name__ == "__main__":
    args   = parse_args()
    config = get_config()

    # Applica argomenti CLI
    if args.no_voice:
        config.enable_voice = False
    if args.api:
        config.enable_api = True
    if args.api_port:
        config.api_port = args.api_port
    if args.silent:
        config.silent_mode = True
    if args.no_plugins:
        config.enable_plugins = False
    if args.lang:
        from core.i18n import set_language
        set_language(args.lang)
        config.language = args.lang

    info("JARVIS PRO starting...")
    info(f"Model={config.model} | Lang={config.language} | Voice={config.enable_voice} | Silent={config.silent_mode}")

    # ── Cleanup DB opzionale ──────────────────────────────────────────────
    if args.cleanup:
        from core.memory import auto_cleanup_old_messages
        auto_cleanup_old_messages()
        info("Cleanup complete — uscita")
        sys.exit(0)

    # ── Plugin manager ────────────────────────────────────────────────────
    if config.enable_plugins:
        try:
            from core.plugin_manager import get_plugin_manager
            n = get_plugin_manager().load_all()
            info(f"Plugins loaded: {n}")
        except Exception as e:
            error(f"Plugin load error: {e}")

    # ── Voice engine ──────────────────────────────────────────────────────
    from core.voice_engine import get_voice_engine
    engine = get_voice_engine()
    if config.enable_voice:
        engine.start()
        info("VoiceEngine started")

    # ── API REST server ───────────────────────────────────────────────────
    if config.enable_api:
        try:
            from api.rest_api import run_api_server
            run_api_server()
            info(f"API server started on :{config.api_port}")
        except ImportError:
            error("FastAPI non installato. pip install fastapi uvicorn")
        except Exception as e:
            error(f"API server error: {e}")

    # ── Avvia DB (crea schema se non esiste) ──────────────────────────────
    try:
        from core.db import get_db
        get_db()
    except Exception as e:
        error(f"DB init error: {e}")

    # ── Auto-cleanup all'avvio ────────────────────────────────────────────
    try:
        from core.memory import auto_cleanup_old_messages
        auto_cleanup_old_messages()
    except Exception:
        pass

    # ── CLI ───────────────────────────────────────────────────────────────
    try:
        from ui.cli import main
        main()
    except KeyboardInterrupt:
        info("Interrupted by user")
    except Exception as e:
        error(f"Fatal error: {e}", exc=e)
        sys.exit(1)
    finally:
        engine.stop()
        info("JARVIS PRO shutdown complete")
