"""
core/tools/git_tool.py — Git operations.
"""
import subprocess
import shutil
from typing import List, Optional

def git_command(args: List[str], cwd: str = ".") -> str:
    """Run a git command and return output."""
    if shutil.which("git") is None:
        return "Error: git is not installed or not in PATH."

    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr

        if not output.strip():
            return "(no output)"
        return output
    except Exception as e:
        return f"Git error: {str(e)}"

def handle_git_query(query: str) -> Optional[str]:
    """Route git-related queries."""
    q = query.lower().strip()

    if "git status" in q:
        return git_command(["status"])

    if "git log" in q:
        return git_command(["log", "--oneline", "-n", "10"])

    if "git diff" in q:
        return git_command(["diff"])

    if "git add" in q:
        # Simple parsing for 'git add .' or 'git add file'
        parts = query.split("add", 1)
        if len(parts) > 1:
            target = parts[1].strip()
            return git_command(["add", target])

    if "git commit" in q:
        # Simple parsing for 'git commit -m "message"'
        if "-m" in query:
            try:
                msg = query.split("-m", 1)[1].strip().strip('"').strip("'")
                return git_command(["commit", "-m", msg])
            except IndexError:
                return "Error: missing commit message."
        return "Usage: git commit -m \"your message\""

    return None
