"""
plugins/example_hello.py — Plugin di esempio.
Rinomina in hello.py (rimuovi "example_") per attivarlo.

Come funziona:
  1. Il PluginManager carica tutti i file *.py in plugins/
  2. Trova classi che ereditano da PluginBase
  3. Chiama can_handle(query) per ogni messaggio
  4. Se True, chiama handle(query) e usa il risultato invece del LLM
"""
from core.plugin_manager import PluginBase


class HelloPlugin(PluginBase):
    name        = "hello"
    description = "Risponde ai saluti con un messaggio personalizzato"
    version     = "1.0.0"
    author      = "Tu"

    _GREETINGS = ("ciao", "salve", "buongiorno", "buonasera", "hey", "hello", "hi")

    def can_handle(self, query: str) -> bool:
        q = query.lower().strip()
        return any(q.startswith(g) for g in self._GREETINGS) and len(q) < 30

    def handle(self, query: str) -> str:
        from datetime import datetime
        hour = datetime.now().hour
        if hour < 12:
            saluto = "Buongiorno"
        elif hour < 18:
            saluto = "Buon pomeriggio"
        else:
            saluto = "Buonasera"
        return f"{saluto}! Sono JARVIS PRO. Come posso aiutarti oggi?"
