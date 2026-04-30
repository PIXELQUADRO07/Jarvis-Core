# JARVIS Phase 5 — Advanced Memory & RAG Implementation Guide

**Duration:** 4-5 hours  
**Start date:** After Phase 4 complete  
**Target:** Vector database, semantic search, auto-compression, user profiles

---

## Overview

Phase 5 adds intelligent memory:
1. **Vector Database** - ChromaDB for semantic similarity
2. **Embeddings** - Sentence transformers for text vectors
3. **Auto-Compression** - Summarize old messages automatically
4. **User Profile** - Learn user preferences over time

**Impact:** JARVIS remembers context better + learns from interactions

---

## Feature 1: Vector Database Integration

### Scope
- ChromaDB for vector storage
- Embed messages using sentence-transformers
- Semantic search across conversation history
- Auto-persistence to disk

### Implementation

**File:** `core/vector_db.py` (NEW)

```python
#!/usr/bin/env python3
"""
Vector database integration using ChromaDB.
Enables semantic search of conversation history.
"""

from typing import Optional, List
from datetime import datetime
from logger import debug, info, warning, error

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class VectorDatabase:
    """ChromaDB wrapper for semantic search"""
    
    def __init__(self, db_dir: str = ".chromadb", collection_name: str = "jarvis_memory"):
        if not CHROMADB_AVAILABLE:
            raise RuntimeError("ChromaDB not installed. Install: pip install chromadb")
        
        self.db_dir = db_dir
        self.collection_name = collection_name
        
        # Initialize ChromaDB
        settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=db_dir,
            anonymized_telemetry=False,
        )
        
        self.client = chromadb.Client(settings)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        info(f"Vector database initialized at {db_dir}")
    
    def add_message(
        self, 
        message_id: str, 
        text: str, 
        role: str = "user",
        metadata: dict = None
    ) -> bool:
        """
        Add message to vector database
        
        Args:
            message_id: Unique message ID
            text: Message text
            role: "user" or "assistant"
            metadata: Additional metadata (session, timestamp, etc.)
        
        Returns:
            True if successful
        """
        if not text or len(text.strip()) < 5:
            return False
        
        try:
            if metadata is None:
                metadata = {}
            
            metadata.update({
                "role": role,
                "timestamp": datetime.now().isoformat(),
            })
            
            # Add to collection (embedding done automatically)
            self.collection.add(
                ids=[message_id],
                documents=[text],
                metadatas=[metadata]
            )
            
            debug(f"Added message {message_id} to vector DB")
            return True
        
        except Exception as e:
            error(f"Failed to add message to vector DB: {e}")
            return False
    
    def search_similar(
        self, 
        query: str, 
        limit: int = 5,
        where: dict = None
    ) -> List[dict]:
        """
        Find messages similar to query
        
        Args:
            query: Search query
            limit: Max results to return
            where: Metadata filter (e.g., {"role": "user"})
        
        Returns:
            List of similar messages with scores
        """
        if not query or len(query.strip()) < 3:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where
            )
            
            # Format results
            messages = []
            for i, doc_id in enumerate(results["ids"][0]):
                messages.append({
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # cosine similarity
                })
            
            return messages
        
        except Exception as e:
            error(f"Search failed: {e}")
            return []
    
    def get_user_context(self, session: str, limit: int = 10) -> str:
        """Get relevant context from session history for LLM"""
        results = self.search_similar("", limit=limit, where={"session": session})
        
        context_lines = ["Recent context:"]
        for msg in results:
            role = msg["metadata"].get("role", "user")
            text = msg["text"][:100]
            context_lines.append(f"  {role}: {text}")
        
        return "\n".join(context_lines)
    
    def delete_collection(self):
        """Delete collection (for reset)"""
        self.client.delete_collection(name=self.collection_name)
        info(f"Deleted collection: {self.collection_name}")


# Module-level singleton
_vector_db: Optional[VectorDatabase] = None

def get_vector_db() -> Optional[VectorDatabase]:
    """Get singleton vector database"""
    global _vector_db
    if _vector_db is None:
        try:
            _vector_db = VectorDatabase()
        except RuntimeError:
            warning("ChromaDB not available")
            return None
    return _vector_db


if __name__ == "__main__":
    db = get_vector_db()
    if db:
        db.add_message("1", "Ciao JARVIS", role="user", metadata={"session": "main"})
        db.add_message("2", "Ciao! Come posso aiutarti?", role="assistant", metadata={"session": "main"})
        
        results = db.search_similar("saluto", limit=2)
        print(f"Found {len(results)} results:")
        for r in results:
            print(f"  {r['text'][:50]} (similarity: {r['similarity']:.2f})")
```

---

## Feature 2: Auto-Compression

### Scope
- Summarize messages older than N days
- Replace with summaries to save space
- Keep recent messages intact
- Configurable thresholds

### Implementation

**File:** `core/summarizer.py` (NEW)

```python
#!/usr/bin/env python3
"""
Auto-compression: Summarize old conversations.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from logger import debug, info

from core.llm import stream_llm


class ConversationSummarizer:
    """Summarize conversations to save memory"""
    
    def __init__(
        self,
        days_to_keep: int = 7,
        summary_prompt: str = "Riassumi brevemente questa conversazione (max 3 righe):"
    ):
        self.days_to_keep = days_to_keep
        self.summary_prompt = summary_prompt
    
    def should_compress(self, timestamp_str: str) -> bool:
        """Check if message is older than threshold"""
        try:
            msg_time = datetime.fromisoformat(timestamp_str)
            cutoff = datetime.now() - timedelta(days=self.days_to_keep)
            return msg_time < cutoff
        except:
            return False
    
    def summarize_conversation(self, messages: list) -> str:
        """
        Summarize a list of messages
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            Summary string
        """
        # Format messages for LLM
        formatted = "\n".join([
            f"{msg['role']}: {msg['content'][:100]}"
            for msg in messages[:10]  # Summarize last 10
        ])
        
        prompt = f"{self.summary_prompt}\n\n{formatted}"
        
        try:
            summary = ""
            for chunk in stream_llm(prompt, []):
                summary += chunk
            
            return summary[:200]  # Limit summary length
        
        except Exception as e:
            debug(f"Summarization failed: {e}")
            return "[Conversation - details omitted]"
    
    def compress_memory(self, memory_file: str) -> int:
        """
        Compress memory file by summarizing old messages.
        
        Returns:
            Number of messages compressed
        """
        import json
        
        path = Path(memory_file)
        if not path.exists():
            return 0
        
        try:
            data = json.loads(path.read_text())
            if not isinstance(data, list):
                return 0
            
            compressed_count = 0
            new_data = []
            old_messages = []
            
            for msg in data:
                timestamp = msg.get("timestamp", "")
                
                if self.should_compress(timestamp):
                    old_messages.append(msg)
                else:
                    # Keep recent messages
                    new_data.append(msg)
            
            # Create summary if old messages exist
            if old_messages:
                summary_text = self.summarize_conversation(old_messages)
                new_data.insert(0, {
                    "role": "system",
                    "content": f"[SUMMARY] {summary_text}",
                    "timestamp": datetime.now().isoformat(),
                })
                compressed_count = len(old_messages)
            
            # Save compressed memory
            path.write_text(json.dumps(new_data, indent=2))
            info(f"Compressed {compressed_count} messages in {path.name}")
            
            return compressed_count
        
        except Exception as e:
            debug(f"Compression failed: {e}")
            return 0


# Module-level functions
def compress_all_sessions(sessions_dir: str = "memory_sessions") -> int:
    """Compress all session memory files"""
    summarizer = ConversationSummarizer()
    total = 0
    
    for session_file in Path(sessions_dir).glob("memory_*.json"):
        total += summarizer.compress_memory(str(session_file))
    
    return total


if __name__ == "__main__":
    summarizer = ConversationSummarizer(days_to_keep=7)
    
    messages = [
        {"role": "user", "content": "Ciao"},
        {"role": "assistant", "content": "Ciao! Come stai?"},
        {"role": "user", "content": "Bene grazie"},
    ]
    
    summary = summarizer.summarize_conversation(messages)
    print(f"Summary: {summary[:100]}")
```

---

## Feature 3: User Profile

### Scope
- Track user preferences and patterns
- Learn from interactions over time
- Suggest personalized responses
- Update profile dynamically

### Implementation

**File:** `core/user_profile.py` (NEW)

```python
#!/usr/bin/env python3
"""
User profile: learns preferences from interactions.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from logger import debug, info


class UserProfile:
    """Learn and store user preferences"""
    
    def __init__(self, profile_file: str = "user_profile.json"):
        self.profile_file = Path(profile_file)
        self.profile = self._load_profile()
    
    def _load_profile(self) -> dict:
        """Load profile from disk"""
        if self.profile_file.exists():
            try:
                return json.loads(self.profile_file.read_text())
            except:
                pass
        
        return {
            "name": "User",
            "preferences": {},
            "topics": {},
            "interaction_count": 0,
            "created_at": datetime.now().isoformat(),
        }
    
    def save_profile(self):
        """Save profile to disk"""
        self.profile_file.write_text(json.dumps(self.profile, indent=2))
        debug("Profile saved")
    
    def record_interaction(self, user_text: str, assistant_response: str):
        """Record user interaction for learning"""
        # Count interactions
        self.profile["interaction_count"] += 1
        
        # Extract topics from user text
        topics = self._extract_topics(user_text)
        for topic in topics:
            if topic not in self.profile["topics"]:
                self.profile["topics"][topic] = 0
            self.profile["topics"][topic] += 1
        
        # Track preferences
        self._update_preferences(user_text)
        
        self.save_profile()
    
    def _extract_topics(self, text: str) -> list:
        """Extract potential topics from text"""
        keywords = ["meteo", "news", "sport", "musica", "film", "ricetta", "aiuto"]
        return [kw for kw in keywords if kw in text.lower()]
    
    def _update_preferences(self, text: str):
        """Update user preferences"""
        # Detect language preference
        if len([c for c in text if ord(c) > 127]) > len(text) * 0.3:
            self.profile["preferences"]["language"] = "italian"
        else:
            self.profile["preferences"]["language"] = "english"
        
        # Detect response style preference (formal/casual)
        if any(word in text.lower() for word in ["per favore", "potresti", "grazie"]):
            self.profile["preferences"]["style"] = "formal"
        else:
            self.profile["preferences"]["style"] = "casual"
    
    def get_profile_summary(self) -> str:
        """Get human-readable profile"""
        lines = [
            f"👤 Profile: {self.profile['name']}",
            f"💬 Interactions: {self.profile['interaction_count']}",
            f"🎯 Top topics: {', '.join(list(self.profile['topics'].keys())[:3]) or 'None yet'}",
            f"⚙️ Preferences: {self.profile['preferences']}",
        ]
        return "\n".join(lines)
    
    def get_preference(self, key: str, default: str = None) -> str:
        """Get specific preference"""
        return self.profile["preferences"].get(key, default)


# Module-level singleton
_user_profile: Optional[UserProfile] = None

def get_user_profile() -> UserProfile:
    """Get singleton user profile"""
    global _user_profile
    if _user_profile is None:
        _user_profile = UserProfile()
    return _user_profile


if __name__ == "__main__":
    profile = UserProfile()
    
    profile.record_interaction(
        "Ciao, mi piacerebbe sapere il meteo",
        "Il meteo è soleggiato"
    )
    
    print(profile.get_profile_summary())
```

---

## 📋 Phase 5 Implementation Checklist

### Step 1: Vector Database (1.5 hours)
- [ ] Install: `pip install chromadb sentence-transformers`
- [ ] Create `core/vector_db.py`
- [ ] Implement `VectorDatabase` class
- [ ] Test: Add and search messages

### Step 2: Auto-Compression (1 hour)
- [ ] Create `core/summarizer.py`
- [ ] Implement `ConversationSummarizer` class
- [ ] Test compression on old messages
- [ ] Wire to auto-run daily

### Step 3: User Profile (45 min)
- [ ] Create `core/user_profile.py`
- [ ] Implement `UserProfile` class
- [ ] Add profile view command: `/profile`
- [ ] Test learning from interactions

### Step 4: Integration (30-45 min)
- [ ] Add vector DB queries to `core/commands.py`
- [ ] Add profile tracking to message save
- [ ] Add `/memory search [query]` command
- [ ] Wire auto-compression to memory save

### Step 5: Testing (1 hour)
- [ ] Test vector search accuracy
- [ ] Test compression effectiveness
- [ ] Test profile updates
- [ ] Verify disk persistence

---

## ✅ Success Criteria

Phase 5 = SUCCESS when:

✅ ChromaDB stores messages  
✅ Semantic search finds similar messages  
✅ Auto-compression summarizes old messages  
✅ User profile learns from interactions  
✅ /memory search works  
✅ /profile shows learned preferences  

**Estimated time:** 4-5 hours  
**Complexity:** Medium-High (vector math)  
**Risk:** Low (isolated subsystem)  

---

Created: 30 Apr 2026  
Last updated: 30 Apr 2026  
Next: PHASE_6_GUIDE.md (Architecture & Testing)

