"""
plugins/example_hello.py — Example plugin.
Rename to hello.py (remove "example_") to activate it.

How it works:
  1. PluginManager loads all *.py files in plugins/
  2. Finds classes inheriting from PluginBase
  3. Calls can_handle(query) for each message
  4. If True, calls handle(query) and uses the result instead of the LLM
"""
from core.plugin_manager import PluginBase


class HelloPlugin(PluginBase):
    name        = "hello"
    description = "Replies to greetings with a custom message"
    version     = "1.0.0"
    author      = "You"

    _GREETINGS = ("hello", "hi", "hey", "good morning", "good afternoon", "good evening")

    def can_handle(self, query: str) -> bool:
        q = query.lower().strip()
        return any(q.startswith(g) for g in self._GREETINGS) and len(q) < 30

    def handle(self, query: str) -> str:
        from datetime import datetime
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        return f"{greeting}! I am JARVIS PRO. How can I help you today?"
