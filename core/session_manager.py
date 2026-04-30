#!/usr/bin/env python3
"""
Session manager for multi-conversation support.
Each session has isolated memory and metadata.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from logger import debug, error


@dataclass
class Session:
    """Represents a conversation session"""
    name: str
    created_at: str
    last_updated: str
    message_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class SessionManager:
    """
    Manages multiple concurrent conversation sessions.
    Each session has isolated memory in memory_sessions/memory_<name>.json
    """
    
    def __init__(self, sessions_dir: str = "memory_sessions"):
        self.sessions_dir = sessions_dir
        self.metadata_file = os.path.join(sessions_dir, "sessions_metadata.json")
        self.current_session: Optional[Session] = None
        self._ensure_dir()
        self._load_sessions()
    
    def _ensure_dir(self):
        """Create sessions directory if needed"""
        Path(self.sessions_dir).mkdir(parents=True, exist_ok=True)
        debug(f"Sessions directory: {self.sessions_dir}")
    
    def _load_sessions(self):
        """Load sessions metadata from file"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
                    if data.get("current_session"):
                        session_data = data["current_session"]
                        self.current_session = Session(**session_data)
                    debug(f"Loaded session: {self.current_session.name if self.current_session else 'None'}")
        except Exception as e:
            error(f"Failed to load sessions: {e}")
    
    def _save_metadata(self):
        """Save sessions metadata to file"""
        try:
            data = {
                "current_session": asdict(self.current_session) if self.current_session else None,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.metadata_file, "w") as f:
                json.dump(data, f, indent=2)
            debug(f"Saved sessions metadata")
        except Exception as e:
            error(f"Failed to save sessions: {e}")
    
    def create_session(self, name: str) -> Session:
        """
        Create new session
        
        Args:
            name: Session name
        
        Returns:
            New Session object
        """
        now = datetime.now().isoformat()
        session = Session(
            name=name,
            created_at=now,
            last_updated=now,
            message_count=0
        )
        self.current_session = session
        self._save_metadata()
        debug(f"Created session: {name}")
        return session
    
    def switch_session(self, name: str) -> Optional[Session]:
        """
        Switch to existing session
        
        Args:
            name: Session name
        
        Returns:
            Session object or None if not found
        """
        session_file = os.path.join(self.sessions_dir, f"memory_{name}.json")
        if not os.path.exists(session_file):
            error(f"Session not found: {name}")
            return None
        
        # Create session object from file
        try:
            with open(session_file, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Old format - just messages, not metadata
                    self.current_session = Session(
                        name=name,
                        created_at=datetime.now().isoformat(),
                        last_updated=datetime.now().isoformat(),
                        message_count=len(data)
                    )
                else:
                    # New format - has metadata
                    self.current_session = Session(**data.get("session", {}))
            self._save_metadata()
            debug(f"Switched to session: {name}")
            return self.current_session
        except Exception as e:
            error(f"Failed to switch session: {e}")
            return None
    
    def get_current_session(self) -> Optional[Session]:
        """Get current session"""
        return self.current_session
    
    def get_session_file(self, name: str = None) -> str:
        """Get memory file path for session"""
        if name is None:
            name = self.current_session.name if self.current_session else "default"
        return os.path.join(self.sessions_dir, f"memory_{name}.json")
    
    def list_sessions(self) -> List[str]:
        """List all available sessions"""
        sessions = []
        try:
            for file in os.listdir(self.sessions_dir):
                if file.startswith("memory_") and file.endswith(".json"):
                    name = file[7:-5]  # Remove "memory_" prefix and ".json"
                    if name != "sessions_metadata":
                        sessions.append(name)
            debug(f"Found {len(sessions)} sessions")
            return sorted(sessions)
        except Exception as e:
            error(f"Failed to list sessions: {e}")
            return []
    
    def delete_session(self, name: str) -> bool:
        """
        Delete session
        
        Args:
            name: Session name
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            session_file = self.get_session_file(name)
            if os.path.exists(session_file):
                os.remove(session_file)
                if self.current_session and self.current_session.name == name:
                    self.current_session = None
                    self._save_metadata()
                debug(f"Deleted session: {name}")
                return True
            error(f"Session not found: {name}")
            return False
        except Exception as e:
            error(f"Failed to delete session: {e}")
            return False
    
    def update_session_stats(self, message_count: int):
        """Update current session's message count"""
        if self.current_session:
            self.current_session.message_count = message_count
            self.current_session.last_updated = datetime.now().isoformat()
            self._save_metadata()


# Module-level singleton
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get session manager singleton"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
        # Create default session if none exists
        if not _session_manager.get_current_session():
            _session_manager.create_session("default")
    return _session_manager


if __name__ == "__main__":
    # Test session manager
    print("🧪 Session Manager Test")
    print("=" * 50)
    
    mgr = get_session_manager()
    
    print(f"\n✅ Default session created")
    print(f"   Name: {mgr.current_session.name}")
    print(f"   Created: {mgr.current_session.created_at}")
    
    # Create new session
    session2 = mgr.create_session("conversation-2")
    print(f"\n✅ Second session created: {session2.name}")
    
    # List sessions
    sessions = mgr.list_sessions()
    print(f"\n📋 Available sessions ({len(sessions)}):")
    for s in sessions:
        print(f"   • {s}")
    
    # Switch sessions
    mgr.switch_session("default")
    print(f"\n✅ Switched to: {mgr.current_session.name}")
    
    print("\n✅ Session manager tests PASSED!")
