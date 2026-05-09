"""
core/plugin_manager.py — Sistema plugin auto-caricante.

Come creare un plugin:
  1. Crea un file in plugins/mio_plugin.py
  2. Definisci una classe che eredita da PluginBase
  3. Implementa `name`, `description`, `can_handle(query)`, `handle(query)`
  4. Il plugin viene caricato automaticamente all'avvio

Esempio (plugins/hello.py):
    from core.plugin_manager import PluginBase
    class HelloPlugin(PluginBase):
        name = "hello"
        description = "Risponde ai saluti"
        def can_handle(self, query):
            return "ciao" in query.lower()
        def handle(self, query):
            return "Ciao! Come posso aiutarti?"
"""

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import List, Optional, Dict, Type
from logger import debug, error, warning


class PluginBase:
    """Classe base per tutti i plugin."""

    name: str = "base"
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    enabled: bool = True

    def can_handle(self, query: str) -> bool:
        """Ritorna True se il plugin può gestire la query."""
        return False

    def handle(self, query: str) -> Optional[str]:
        """
        Gestisce la query e ritorna una risposta stringa,
        oppure None per passare al LLM.
        """
        return None

    def on_load(self):
        """Chiamato al caricamento del plugin."""
        pass

    def on_unload(self):
        """Chiamato allo scaricamento del plugin."""
        pass


class PluginManager:
    """Carica e gestisce i plugin dalla cartella plugins/."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self._plugins: List[PluginBase] = []
        self._registry: Dict[str, PluginBase] = {}

    def load_all(self) -> int:
        """Carica tutti i plugin dalla directory. Ritorna il numero caricato."""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True)
            debug(f"Created plugins directory: {self.plugins_dir}")
            return 0

        loaded = 0
        for py_file in sorted(self.plugins_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            try:
                self._load_file(py_file)
                loaded += 1
            except Exception as e:
                error(f"Failed to load plugin {py_file.name}: {e}")

        debug(f"PluginManager: loaded {loaded} plugins")
        return loaded

    def _load_file(self, path: Path):
        """Carica un singolo file plugin."""
        module_name = f"plugins.{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        for _, cls in inspect.getmembers(module, inspect.isclass):
            if (cls is not PluginBase
                    and issubclass(cls, PluginBase)
                    and cls.name != "base"):
                instance = cls()
                instance.on_load()
                self._plugins.append(instance)
                self._registry[cls.name] = instance
                debug(f"Plugin loaded: {cls.name} v{cls.version}")

    def route(self, query: str) -> Optional[str]:
        """
        Prova ogni plugin in ordine.
        Ritorna la prima risposta non None, o None se nessun plugin gestisce.
        """
        for plugin in self._plugins:
            if not plugin.enabled:
                continue
            try:
                if plugin.can_handle(query):
                    result = plugin.handle(query)
                    if result is not None:
                        debug(f"Plugin '{plugin.name}' handled query")
                        return result
            except Exception as e:
                error(f"Plugin '{plugin.name}' error: {e}")
        return None

    def list_plugins(self) -> List[Dict]:
        return [
            {
                "name":        p.name,
                "description": p.description,
                "version":     p.version,
                "author":      p.author,
                "enabled":     p.enabled,
            }
            for p in self._plugins
        ]

    def enable(self, name: str) -> bool:
        if name in self._registry:
            self._registry[name].enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        if name in self._registry:
            self._registry[name].enabled = False
            return True
        return False


# ── Singleton ────────────────────────────────────────────────────────────────
_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    global _manager
    if _manager is None:
        from config import get_config
        cfg = get_config()
        _manager = PluginManager(cfg.plugins_dir)
        if cfg.enable_plugins:
            _manager.load_all()
    return _manager
