"""
core/plugin_manager.py — Auto-loading plugin system.

How to create a plugin:
  1. Create a file in plugins/my_plugin.py
  2. Define a class that inherits from PluginBase
  3. Implement `name`, `description`, `can_handle(query)`, `handle(query)`
  4. The plugin is loaded automatically at startup

Example (plugins/hello.py):
    from core.plugin_manager import PluginBase
    class HelloPlugin(PluginBase):
        name = "hello"
        description = "Replies to greetings"
        def can_handle(self, query):
            return "hello" in query.lower()
        def handle(self, query):
            return "Hello! How can I assist you?"
"""

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import List, Optional, Dict, Type
from logger import debug, error, warning


class PluginBase:
    """Base class for all plugins."""

    name: str = "base"
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    enabled: bool = True

    def can_handle(self, query: str) -> bool:
        """Return True if the plugin can handle the query."""
        return False

    def handle(self, query: str) -> Optional[str]:
        """Handle the query and return a string response, or None to pass to the LLM."""
        return None

    def on_load(self):
        """Called when the plugin is loaded."""
        pass

    def on_unload(self):
        """Called when the plugin is unloaded."""
        pass


class PluginManager:
    """Loads and manages plugins from the plugins/ folder."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self._plugins: List[PluginBase] = []
        self._registry: Dict[str, PluginBase] = {}

    def load_all(self) -> int:
        """Load all plugins from the directory. Returns the number loaded."""
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
        """Load a single plugin file."""
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
        """Try each plugin in order.
        Returns the first non-None response, or None if no plugin handles the query.
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
