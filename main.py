#!/usr/bin/env python3
"""
JARVIS AI — Entry point
Inizializza config, logging, avvia il VoiceEngine e la CLI.
"""
import sys
from pathlib import Path

# Assicura che gli import funzionino dal root del progetto
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from logger import info, error

# Avvia il motore vocale (worker thread daemon) prima della CLI
from core.voice_engine import get_voice_engine

# Importa la CLI
from ui.cli import main

if __name__ == "__main__":
    try:
        config = get_config()
        info("JARVIS starting...")
        info(f"Ollama URL: {config.ollama_url}")
        info(f"Model:      {config.model}")
        info(f"Voice:      {'enabled' if config.enable_voice else 'disabled'}")

        # Avvia il worker TTS se la voce è abilitata
        engine = get_voice_engine()
        if config.enable_voice:
            engine.start()

        main()

        engine.stop()

    except KeyboardInterrupt:
        info("JARVIS interrupted by user")
        sys.exit(0)
    except Exception as e:
        error(f"Fatal error in JARVIS: {e}", exc=e)
        sys.exit(1)
