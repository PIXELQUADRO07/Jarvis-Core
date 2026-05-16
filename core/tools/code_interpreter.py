"""
core/tools/code_interpreter.py — Safe Python code execution.
"""
import subprocess
import sys
from typing import Optional

_BLOCKED_PATTERNS = [
    "os.system", "os.popen", "subprocess.", "shutil.rmtree",
    "os.remove", "os.unlink", "os.rmdir", "__import__",
    "eval(", "exec(", "compile(", "open("
]

def execute_python(code: str, timeout: int = 30) -> str:
    """Execute Python code in a separate process."""
    if not code:
        return "No code provided."

    # Simple security check
    for pattern in _BLOCKED_PATTERNS:
        if pattern in code:
            return f"Error: Blocked pattern detected: {pattern}"

    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr

        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {timeout} seconds."
    except Exception as e:
        return f"Error: {str(e)}"

def handle_code_query(query: str) -> Optional[str]:
    """Route code execution queries."""
    q = query.lower().strip()
    if q.startswith("python:"):
        code = query[7:].strip()
        return execute_python(code)

    if q.startswith("esegui python"):
        code = query[13:].strip()
        return execute_python(code)

    return None
