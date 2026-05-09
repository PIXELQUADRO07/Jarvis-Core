"""
api/rest_api.py — API REST FastAPI per integrazioni esterne.

Endpoint:
  POST /chat          — Invia messaggio, riceve risposta streaming (SSE)
  GET  /status        — Stato sistema
  GET  /sessions      — Lista sessioni
  POST /sessions      — Crea sessione
  GET  /history/{session} — Storico conversazione
  GET  /search?q=...  — Ricerca nello storico

Avvio:
  python -m api.rest_api
  o da main.py con --api
"""
from __future__ import annotations

try:
    from fastapi import FastAPI, HTTPException, Depends, Header  # type: ignore
    from fastapi.middleware.cors import CORSMiddleware              # type: ignore
    from fastapi.responses import StreamingResponse, JSONResponse   # type: ignore
    from pydantic import BaseModel                                   # type: ignore
    import uvicorn                                                   # type: ignore
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

import json
import threading
from typing import Optional, Generator

from config import get_config
from core.db import get_db
from core.security import sanitize_input, get_rate_limiter
from logger import info, error


def _check_api_key(x_api_key: Optional[str] = Header(None)):
    cfg = get_config()
    if cfg.api_key and x_api_key != cfg.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


def create_app() -> "FastAPI":
    if not _FASTAPI_AVAILABLE:
        raise ImportError("FastAPI non installato. Installa con: pip install fastapi uvicorn")

    app = FastAPI(
        title="JARVIS API",
        description="REST API per JARVIS AI locale",
        version="2.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Modelli Pydantic ────────────────────────────────────────────────────

    class ChatRequest(BaseModel):
        message: str
        session: str = "default"
        stream: bool = False

    class SessionCreateRequest(BaseModel):
        name: str

    # ── Endpoints ───────────────────────────────────────────────────────────

    @app.get("/status")
    def status(_auth=Depends(_check_api_key)):
        cfg = get_config()
        db = get_db()
        stats = db.get_stats()
        return {
            "status":   "online",
            "model":    cfg.model,
            "language": cfg.language,
            "db_stats": stats,
        }

    @app.post("/chat")
    def chat(req: ChatRequest, _auth=Depends(_check_api_key)):
        limiter = get_rate_limiter()
        if not limiter.allow():
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        clean_msg = sanitize_input(req.message)
        if not clean_msg:
            raise HTTPException(status_code=400, detail="Empty message")

        # Import qui per evitare circular imports
        from core.llm import stream_llm
        from core.session_manager import get_session_manager

        sm = get_session_manager()
        if sm.current_session is None or sm.current_session.name != req.session:
            sm.switch_session(req.session) or sm.create_session(req.session)

        if req.stream:
            def event_stream() -> Generator[str, None, None]:
                full = ""
                for chunk, meta in stream_llm(clean_msg):
                    full += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                yield f"data: {json.dumps({'done': True, 'full': full})}\n\n"

            return StreamingResponse(event_stream(), media_type="text/event-stream")

        # Non streaming
        full = ""
        last_meta = {}
        for chunk, meta in stream_llm(clean_msg):
            full += chunk
            last_meta = meta

        return {
            "response": full,
            "session":  req.session,
            "tokens":   last_meta,
        }

    @app.get("/sessions")
    def list_sessions(_auth=Depends(_check_api_key)):
        db = get_db()
        return db.list_sessions()

    @app.post("/sessions")
    def create_session(req: SessionCreateRequest, _auth=Depends(_check_api_key)):
        from core.session_manager import get_session_manager
        sm = get_session_manager()
        session = sm.create_session(req.name)
        return {"name": session.name, "created_at": session.created_at}

    @app.get("/history/{session}")
    def get_history(session: str, limit: int = 50, _auth=Depends(_check_api_key)):
        db = get_db()
        return db.load_session(session, limit=limit)

    @app.get("/search")
    def search(q: str, session: Optional[str] = None, _auth=Depends(_check_api_key)):
        db = get_db()
        return db.search(q, session=session)

    @app.get("/plugins")
    def list_plugins(_auth=Depends(_check_api_key)):
        from core.plugin_manager import get_plugin_manager
        return get_plugin_manager().list_plugins()

    return app


def run_api_server():
    """Avvia il server API in un thread separato (daemon)."""
    if not _FASTAPI_AVAILABLE:
        error("FastAPI non disponibile — API server non avviata")
        return

    cfg = get_config()
    app = create_app()

    def _run():
        uvicorn.run(app, host=cfg.api_host, port=cfg.api_port, log_level="warning")

    t = threading.Thread(target=_run, daemon=True, name="jarvis-api")
    t.start()
    info(f"API server started on http://{cfg.api_host}:{cfg.api_port}")


if __name__ == "__main__":
    if not _FASTAPI_AVAILABLE:
        print("Installa FastAPI: pip install fastapi uvicorn")
    else:
        cfg = get_config()
        app = create_app()
        import uvicorn  # type: ignore
        uvicorn.run(app, host=cfg.api_host, port=cfg.api_port)
