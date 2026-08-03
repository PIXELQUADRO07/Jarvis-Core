# Modifiche rispetto al progetto originale

Vedi la conversazione per il dettaglio, riassunto qui per riferimento rapido.

## 🔴 Fix critici (sicurezza)

- **`core/tools/system.py`** — chiusa una command injection reale in
  `install_package`/`remove_package`/`shell_exec`: costruivano comandi
  shell con `shell=True` da testo utente non validato. Ora: argv liste
  (mai `shell=True`), validazione stretta del nome pacchetto
  (`_validate_safe_name`), e i tre tool sono **disattivati di default**
  (`enable_package_management`, `enable_shell_exec` in config —
  opt-in esplicito richiesto).
- **`core/tools/code_interpreter.py`** — aggiunti limiti reali di
  CPU/memoria/processi (`resource.setrlimit`), environment ripulito,
  `python -I`. Documentato che non è un sandbox vero (serve
  Docker/Firejail per isolamento reale).
- **`core/security.py`** — `sanitize_input` non riscrive più
  silenziosamente i messaggi (prima cancellava parole come "subprocess"
  da domande legittime). `encrypt_json_file` non fa più fallback
  silenzioso in chiaro: solleva `EncryptionUnavailableError`.
- **`api/rest_api.py`** — confronto API key a tempo costante
  (`hmac.compare_digest`, prima vulnerabile a timing attack); CORS non
  più `allow_credentials=True` con `allow_origins=["*"]`; rate limiting
  per-client (API key o IP) invece che globale condiviso; warning
  all'avvio se l'API è esposta oltre localhost senza `api_key`.

## 🟡 Miglioramenti

- **`ui/cli.py`** — lo streaming ora è visibile davvero: prima i token
  arrivavano ma la CLI li accumulava in silenzio (solo spinner) e
  stampava tutto insieme alla fine. Ora renderizza incrementalmente via
  `rich.Live`.
- **`tests/test_tools_security.py`** (nuovo) — coverage per system.py,
  code_interpreter, scraper (mockato), git_tool, encryption, rate
  limiter, API auth, tool-calling round trip. 2 test preesistenti rotti
  in `test_core.py` corretti.

## 🟢 Aggiunte

- **`core/tools/registry.py`** (nuovo) + refactor di `core/llm.py` e
  `controller/jarvis_controller.py` — tool-calling nativo via Ollama al
  posto del router a keyword come meccanismo primario. Il modello
  decide da solo se/quale tool chiamare, con round trip automatici
  (max `config.max_tool_call_rounds`). Fallback automatico al router
  regex (`core/tools/router.py`, ora legacy) se il modello/Ollama non
  supporta i tool. **Per design, i tool pericolosi (install/remove
  pacchetti, shell_exec) non sono mai esposti come tool auto-invocabili
  dall'LLM** — restano dietro l'opt-in umano esplicito in config.

## Non implementato (roadmap, non iniziato)

- STT locale (whisper.cpp) per l'input vocale.
- RAG su documenti personali con embeddings locali.
- Sandboxing containerizzato per il code interpreter (Docker/Firejail).

## Nuovi flag di configurazione (tutti già in `jarvis_config.json`)

| Flag | Default | Note |
|---|---|---|
| `enable_shell_exec` | `false` | opt-in esplicito richiesto |
| `enable_package_management` | `false` | opt-in esplicito richiesto |
| `require_encryption` | `false` | riservato per uso futuro |
| `code_exec_timeout` | `10` | secondi |
| `code_exec_max_memory_mb` | `256` | MB |
| `use_native_tool_calling` | `true` | fallback automatico al router se non supportato |
| `max_tool_call_rounds` | `3` | round trip massimi modello↔tool |
