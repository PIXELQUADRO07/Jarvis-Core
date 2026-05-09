# JARVIS PRO — Local AI Assistant

Assistente AI locale basato su Ollama con CLI avanzata, voce, API REST, plugin e molto altro.

---

## Installazione rapida

```bash
# 1. Clona / estrai il progetto
cd jarvis-pro

# 2. Crea venv e installa dipendenze
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Avvia Ollama (in un altro terminale)
ollama serve
ollama pull qwen2.5:7b         # o il modello che preferisci

# 4. Avvia JARVIS
python main.py
```

---

## Avvio con opzioni

```bash
python main.py --lang en           # Avvia in inglese
python main.py --silent            # Modalità risposte brevi
python main.py --api               # Abilita API REST (porta 8000)
python main.py --no-voice          # Disabilita sintesi vocale
python main.py --no-plugins        # Disabilita plugin
python main.py --cleanup           # Pulizia DB vecchio ed esci
```

---

## Docker

```bash
# Build e avvio
docker-compose up -d

# Solo JARVIS (Ollama già in esecuzione)
docker build -t jarvis-pro .
docker run -it --rm -e OLLAMA_URL=http://host.docker.internal:11434/api/chat jarvis-pro
```

---

## Comandi CLI

| Comando | Descrizione |
|---------|-------------|
| `/help` | Lista comandi |
| `/status` | Stato sistema e Ollama |
| `/config` | Configurazione attuale |
| `/lang [it\|en\|es\|fr\|de]` | Cambia lingua |
| `/silent on\|off` | Risposte brevi |
| `/model list` | Modelli Ollama disponibili |
| `/model set [nome]` | Cambia modello |
| `/session create [nome]` | Nuova sessione |
| `/session switch [nome]` | Cambia sessione |
| `/session list` | Lista sessioni |
| `/export` | Esporta chat in Markdown |
| `/search [testo]` | Cerca nello storico |
| `/cleanup` | Rimuovi messaggi vecchi |
| `/voice on\|off\|test` | Gestione voce |
| `/encrypt on\|off` | Crittografia memoria |
| `/api on\|off` | Server API REST |
| `/plugins` | Lista plugin |
| `/clear` | Azzera memoria sessione |
| `/history` | Ultimi messaggi |
| `/exit` | Chiudi |

---

## API REST

Con `python main.py --api` (o `/api on`):

```bash
# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "ciao", "session": "default"}'

# Stato
curl http://localhost:8000/status

# Sessioni
curl http://localhost:8000/sessions

# Storico
curl http://localhost:8000/history/default

# Ricerca
curl "http://localhost:8000/search?q=meteo"

# Con API key (se configurata)
curl -H "X-API-Key: la-tua-chiave" http://localhost:8000/status
```

Documentazione interattiva: **http://localhost:8000/docs**

---

## Plugin

Crea un file in `plugins/mio_plugin.py`:

```python
from core.plugin_manager import PluginBase

class MioPlugin(PluginBase):
    name        = "mio_plugin"
    description = "Cosa fa il plugin"
    version     = "1.0.0"

    def can_handle(self, query: str) -> bool:
        return "mia_parola_chiave" in query.lower()

    def handle(self, query: str) -> str:
        return "Risposta del mio plugin!"
```

Il plugin viene caricato automaticamente al prossimo avvio.

---

## Crittografia memoria

```bash
pip install cryptography

# In CLI
/encrypt on
```

La chiave AES viene generata in `.jarvis_key` (non committare nel repo).

---

## Test

```bash
pytest tests/ -v
pytest tests/ --cov=core --cov-report=term-missing
```

---

## Struttura progetto

```
jarvis-pro/
├── main.py                    # Entry point
├── config.py                  # Configurazione (JSON + YAML + env)
├── logger.py                  # Logging JSON strutturato con rotazione
├── jarvis_config.json         # Config di default
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│
├── core/
│   ├── llm.py                 # LLM streaming (Ollama)
│   ├── memory.py              # Memoria (SQLite + file JSON)
│   ├── db.py                  # Database SQLite persistente
│   ├── state.py               # Stato interno thread-safe
│   ├── commands.py            # Dispatcher comandi slash
│   ├── security.py            # AES, rate limiting, sanitizzazione
│   ├── i18n.py                # Multi-lingua (it/en/es/fr/de)
│   ├── notifications.py       # Notifiche desktop
│   ├── plugin_manager.py      # Sistema plugin auto-caricante
│   ├── retry_handler.py       # Retry + circuit breaker
│   ├── session_manager.py     # Sessioni multiple
│   ├── token_counter.py       # Contatore token
│   ├── voice.py               # Facade voce
│   ├── voice_engine.py        # Worker TTS daemon
│   ├── voice_queue.py         # Coda TTS prioritaria
│   ├── audio_fx.py            # Effetti audio Iron Man
│   ├── tts_piper.py           # Sintesi Piper
│   └── tools/
│       ├── router.py          # Router tool + plugin
│       ├── api_weather.py     # Meteo
│       ├── api_wiki.py        # Wikipedia
│       ├── web_search.py      # Ricerca web DuckDuckGo
│       ├── math.py            # Calcoli
│       ├── scraper.py         # URL scraping
│       ├── system.py          # Info sistema
│       └── cache.py           # Cache risposte
│
├── controller/
│   └── jarvis_controller.py   # Controller UI↔core
│
├── ui/
│   └── cli.py                 # CLI avanzata
│
├── api/
│   └── rest_api.py            # API REST FastAPI
│
├── plugins/                   # Plugin utente
│   └── example_hello.py
│
├── tests/
│   └── test_core.py           # Test unitari pytest
│
├── logs/                      # Log JSON rotanti
├── exports/                   # Chat esportate in Markdown
├── db/                        # Database SQLite
├── memory_sessions/           # File sessioni JSON
└── voices/                    # Modelli vocali Piper (.onnx)
```

---

## Variabili d'ambiente

```bash
OLLAMA_URL=http://localhost:11434/api/chat
JARVIS_MODEL=qwen2.5:7b
JARVIS_TEMPERATURE=0.2
JARVIS_LANGUAGE=it
JARVIS_VOICE_ENABLED=false
JARVIS_VOICE_MODEL=voices/it_IT-riccardo-x_low.onnx
JARVIS_ENABLE_API=false
JARVIS_API_PORT=8000
JARVIS_API_KEY=chiave-segreta
JARVIS_ENCRYPT_MEMORY=false
JARVIS_SILENT_MODE=false
```
