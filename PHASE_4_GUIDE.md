# JARVIS Phase 4 — Tool System Implementation Guide

**Duration:** 5-6 hours  
**Start date:** After Phase 2 complete  
**Target:** Modular plugin-based tool system with web search and file operations

---

## Overview

Phase 4 adds plugin system:
1. **Tool Base Interface** - Abstract base class for all tools
2. **Plugin Loader** - Dynamically load tools from folder
3. **Web Search Tool** - DuckDuckGo integration
4. **Filesystem Tool** - Safe read/write operations

**Impact:** Extensible tool ecosystem for custom integrations

---

## Feature 1: Tool Base Interface

### Scope
- Abstract Tool class
- Standardized interface for all tools
- Schema for parameters
- Help text and metadata

### Implementation

**File:** `core/tools/base.py` (NEW)

```python
#!/usr/bin/env python3
"""
Base Tool interface for JARVIS plugins.
All tools must inherit from Tool and implement execute().
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ToolParameter:
    """Describes a tool parameter"""
    name: str
    description: str
    type: str  # 'str', 'int', 'float', 'bool', 'list'
    required: bool = True
    default: Optional[Any] = None


class Tool(ABC):
    """Base class for all JARVIS tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name (e.g., 'weather', 'web_search')"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description for LLM"""
        pass
    
    @property
    def help(self) -> str:
        """Detailed help text (optional)"""
        return self.description
    
    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """List of tool parameters"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Execute tool with parameters.
        
        Args:
            **kwargs: Parameter values
        
        Returns:
            Result string
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    p.name: {
                        "type": p.type,
                        "description": p.description,
                        "required": p.required,
                    }
                    for p in self.parameters
                }
            }
        }
    
    def validate_params(self, **kwargs) -> tuple[bool, str]:
        """
        Validate parameters against schema.
        
        Returns:
            (is_valid, error_message)
        """
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False, f"Missing required parameter: {param.name}"
        
        return True, ""
    
    def __repr__(self) -> str:
        return f"Tool({self.name})"


# Example tool implementation
class ExampleTool(Tool):
    """Example tool showing how to implement"""
    
    @property
    def name(self) -> str:
        return "example"
    
    @property
    def description(self) -> str:
        return "Example tool for demonstration"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter("query", "What to search for", "str", required=True),
        ]
    
    def execute(self, **kwargs) -> str:
        query = kwargs.get("query", "")
        return f"Example result for: {query}"


if __name__ == "__main__":
    tool = ExampleTool()
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Schema: {tool.get_schema()}")
    
    result = tool.execute(query="test")
    print(f"Result: {result}")
```

---

## Feature 2: Plugin Loader

### Scope
- Auto-discover tools in `core/tools/plugins/` folder
- Dynamic import and instantiation
- Registry of loaded tools
- Error handling

### Implementation

**File:** `core/tools/plugin_loader.py` (NEW)

```python
#!/usr/bin/env python3
"""
Plugin loader for JARVIS tools.
Automatically discovers and loads tools from plugins/ directory.
"""

import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Optional
from logger import debug, info, warning, error

from core.tools.base import Tool


class PluginLoader:
    """Dynamically loads tool plugins"""
    
    def __init__(self, plugins_dir: str = "core/tools/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.tools: Dict[str, Tool] = {}
    
    def load_plugins(self) -> Dict[str, Tool]:
        """
        Discover and load all plugins from plugins/ directory.
        
        Convention: Each .py file should define a Tool subclass
                   or have a module-level TOOL variable
        """
        info(f"Loading plugins from: {self.plugins_dir}")
        
        for plugin_file in self.plugins_dir.glob("*.py"):
            # Skip private files
            if plugin_file.name.startswith("_"):
                continue
            
            try:
                self._load_plugin_file(plugin_file)
            except Exception as e:
                error(f"Failed to load {plugin_file.name}: {e}")
        
        info(f"Loaded {len(self.tools)} tools: {list(self.tools.keys())}")
        return self.tools
    
    def _load_plugin_file(self, plugin_file: Path):
        """Load a single plugin file"""
        module_name = plugin_file.stem
        
        try:
            # Import module
            spec = importlib.util.spec_from_file_location(
                f"jarvis_tool_{module_name}",
                plugin_file
            )
            if spec is None or spec.loader is None:
                return
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for Tool subclass or TOOL variable
            tool = None
            
            if hasattr(module, "TOOL"):
                tool = module.TOOL
            else:
                # Find first Tool subclass
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, Tool) and 
                        obj != Tool and
                        not name.startswith("_")):
                        tool = obj()
                        break
            
            if tool and isinstance(tool, Tool):
                self.tools[tool.name] = tool
                debug(f"Loaded tool: {tool.name}")
            else:
                warning(f"No Tool found in {module_name}")
        
        except Exception as e:
            raise RuntimeError(f"Error loading {plugin_file}: {e}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> list[str]:
        """List all loaded tool names"""
        return list(self.tools.keys())
    
    def execute_tool(self, name: str, **kwargs) -> str:
        """Execute tool by name"""
        tool = self.get_tool(name)
        if not tool:
            return f"❌ Tool not found: {name}"
        
        # Validate parameters
        valid, error_msg = tool.validate_params(**kwargs)
        if not valid:
            return f"❌ {error_msg}"
        
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            return f"❌ Tool error: {e}"


# Module-level singleton
_plugin_loader: Optional[PluginLoader] = None

def get_plugin_loader() -> PluginLoader:
    """Get singleton plugin loader"""
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader()
        _plugin_loader.load_plugins()
    return _plugin_loader


if __name__ == "__main__":
    loader = PluginLoader()
    tools = loader.load_plugins()
    print(f"Loaded {len(tools)} tools: {list(tools.keys())}")
```

---

## Feature 3: Web Search Tool

### Scope
- Search DuckDuckGo for web results
- Return formatted results
- Error handling for no results

### Implementation

**File:** `core/tools/plugins/web_search.py` (NEW)

```python
#!/usr/bin/env python3
"""
Web Search tool using DuckDuckGo.
"""

from typing import Optional
from logger import debug
from core.tools.base import Tool, ToolParameter

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


class WebSearchTool(Tool):
    """Search the web using DuckDuckGo"""
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web for information"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter("query", "What to search for", "str", required=True),
            ToolParameter("results", "Number of results (1-10)", "int", required=False, default=5),
        ]
    
    def execute(self, **kwargs) -> str:
        if not DDGS_AVAILABLE:
            return "❌ DuckDuckGo not installed (pip install duckduckgo-search)"
        
        query = kwargs.get("query", "")
        max_results = kwargs.get("results", 5)
        max_results = min(10, max_results)  # Cap at 10
        
        if not query:
            return "❌ Query required"
        
        try:
            debug(f"Web search: {query}")
            
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                return f"❌ No results for: {query}"
            
            # Format results
            lines = [f"🌐 Search results for '{query}' ({len(results)} found):"]
            for i, result in enumerate(results, 1):
                title = result.get("title", "")[:60]
                body = result.get("body", "")[:100]
                lines.append(f"\n{i}. {title}")
                lines.append(f"   {body}")
            
            return "\n".join(lines)
        
        except Exception as e:
            return f"❌ Search error: {e}"


# Export for plugin loader
TOOL = WebSearchTool()
```

---

## Feature 4: Filesystem Tool

### Scope
- Safe file read/write operations
- Restricted to `jarvis_files/` directory
- Prevent path traversal attacks
- Support: read, write, list, delete

### Implementation

**File:** `core/tools/plugins/filesystem.py` (NEW)

```python
#!/usr/bin/env python3
"""
Filesystem tool for safe file operations.
All operations restricted to jarvis_files/ directory.
"""

from pathlib import Path
from logger import debug, warning
from core.tools.base import Tool, ToolParameter


class FilesystemTool(Tool):
    """Read/write files in jarvis_files/ directory"""
    
    def __init__(self, base_dir: str = "jarvis_files"):
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.base_dir.mkdir(exist_ok=True)
    
    @property
    def name(self) -> str:
        return "filesystem"
    
    @property
    def description(self) -> str:
        return "Read, write, and manage files in jarvis_files/ directory"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter("action", "read|write|list|delete", "str", required=True),
            ToolParameter("path", "File path (relative to jarvis_files/)", "str", required=True),
            ToolParameter("content", "File content (for write)", "str", required=False),
        ]
    
    def execute(self, **kwargs) -> str:
        action = kwargs.get("action", "").lower()
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        
        if not path:
            return "❌ Path required"
        
        try:
            # Validate path (prevent traversal)
            full_path = (self.base_dir / path).resolve()
            if not str(full_path).startswith(str(self.base_dir)):
                return "❌ Path outside jarvis_files/ (security)"
            
            if action == "read":
                return self._read(full_path)
            elif action == "write":
                return self._write(full_path, content)
            elif action == "list":
                return self._list(full_path)
            elif action == "delete":
                return self._delete(full_path)
            else:
                return f"❌ Unknown action: {action}"
        
        except Exception as e:
            return f"❌ Error: {e}"
    
    def _read(self, path: Path) -> str:
        """Read file"""
        if not path.exists():
            return f"❌ File not found: {path.name}"
        if not path.is_file():
            return f"❌ Not a file: {path.name}"
        
        content = path.read_text()
        return f"📄 {path.name} ({len(content)} bytes)\n\n{content}"
    
    def _write(self, path: Path, content: str) -> str:
        """Write file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"✅ Written to {path.name} ({len(content)} bytes)"
    
    def _list(self, path: Path) -> str:
        """List directory"""
        if not path.exists():
            path = self.base_dir
        
        if not path.is_dir():
            return f"❌ Not a directory: {path}"
        
        items = sorted(path.iterdir())
        if not items:
            return f"📁 Directory empty: {path.name}"
        
        lines = [f"📁 {path.name}/"]
        for item in items:
            if item.is_dir():
                lines.append(f"  📂 {item.name}/")
            else:
                size = item.stat().st_size
                lines.append(f"  📄 {item.name} ({size} bytes)")
        
        return "\n".join(lines)
    
    def _delete(self, path: Path) -> str:
        """Delete file"""
        if not path.exists():
            return f"❌ File not found: {path.name}"
        
        path.unlink()
        return f"✅ Deleted: {path.name}"


# Export for plugin loader
TOOL = FilesystemTool()
```

---

## Feature 5: Integration with Router

**Modify `core/tools/router.py`:**

```python
from core.tools.plugin_loader import get_plugin_loader

def route_to_tool(text: str) -> Optional[str]:
    """Route user message to appropriate tool"""
    
    loader = get_plugin_loader()
    
    # Detect web search
    if any(word in text.lower() for word in ["search", "find", "google", "web"]):
        web_tool = loader.get_tool("web_search")
        if web_tool:
            # Extract query
            query = text.replace("search", "").replace("find", "").strip()
            return web_tool.execute(query=query, results=5)
    
    # Detect file operations
    if any(word in text.lower() for word in ["read", "write", "file", "directory"]):
        fs_tool = loader.get_tool("filesystem")
        if fs_tool:
            # Parse action and path from text
            # e.g., "read config.txt" → action="read", path="config.txt"
            pass
    
    # Fallback to LLM
    return None
```

---

## 📋 Phase 4 Implementation Checklist

### Step 1: Tool Base Interface (1 hour)
- [ ] Create `core/tools/base.py`
- [ ] Implement `Tool` abstract class
- [ ] Implement `ToolParameter` dataclass
- [ ] Test: `python core/tools/base.py`

### Step 2: Plugin Loader (1 hour)
- [ ] Create `core/tools/plugin_loader.py`
- [ ] Implement `PluginLoader` class
- [ ] Create `core/tools/plugins/` directory
- [ ] Test: `python core/tools/plugin_loader.py`

### Step 3: Web Search Tool (45 min)
- [ ] Install: `pip install duckduckgo-search`
- [ ] Create `core/tools/plugins/web_search.py`
- [ ] Implement `WebSearchTool` class
- [ ] Test: Search queries

### Step 4: Filesystem Tool (45 min)
- [ ] Create `core/tools/plugins/filesystem.py`
- [ ] Implement `FilesystemTool` class
- [ ] Create `jarvis_files/` directory
- [ ] Test: Read, write, list operations

### Step 5: Router Integration (1 hour)
- [ ] Update `core/tools/router.py`
- [ ] Wire plugin loader
- [ ] Test tool routing

### Step 6: Testing (1 hour)
- [ ] Test web search tool
- [ ] Test filesystem tool
- [ ] Test plugin discovery
- [ ] Test error handling

---

## ✅ Success Criteria

Phase 4 = SUCCESS when:

✅ Tool base interface working  
✅ Plugins auto-discovered from folder  
✅ Web search returns results  
✅ File read/write working  
✅ Path traversal prevented  
✅ No tool crashes  

**Estimated time:** 5-6 hours  
**Complexity:** Medium  
**Risk:** Low (isolated module)  

---

Created: 30 Apr 2026  
Last updated: 30 Apr 2026  
Next: PHASE_5_GUIDE.md (Memory Advanced)

