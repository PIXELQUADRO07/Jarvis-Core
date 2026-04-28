# JARVIS AI — Miglioramenti v2.0

Questo documento descrive tutti i miglioramenti implementati al progetto JARVIS AI.

## 📊 Sommario Miglioramenti

### ✅ **Sistema di Configurazione Centralizzato**
- **File**: `config.py`
- Configurazione gestita da un singleton `JarvisConfig`
- Override via variabili ambiente (ENV variables)
- Supporto salvataggio config su file `jarvis_config.json`
- Parametri configurabili:
  - URL e modello Ollama
  - Temperature, timeout, max response length
  - Limiti storia conversazione
  - Velocità spinner, comportamenti CLI
  - Enable/disable singoli tool

### ✅ **Sistema di Logging Centralizzato**
- **File**: `logger.py`
- Logging su file con timestamp giornaliero in `logs/`
- Funzioni: `debug()`, `info()`, `warning()`, `error()`, `critical()`
- Tracciamento completo di errori e flussi
- Console output limitato (solo WARNING e ERROR)

### ✅ **Memoria Conversazione Migliorata**
- **File**: `core/memory.py`
- Nuovo: `get_memory_stats()` - Statistiche memoria
- Nuovo: `clear_memory()` - Pulisce completamente memoria
- Limite configurabile messaggi (default 100)
- Filtri hallucination migliorati
- Miglior handling JSON errors
- Debug logging per ogni operazione

### ✅ **LLM Streaming Migliorato**
- **File**: `core/llm.py`
- Usa config centralizzata
- Logging completo di richieste
- Migliore gestione error HTTP vs timeout
- Truncation intelligente risposta
- Debug della lunghezza risposta

### ✅ **Comandi Slash Espansi**
- **File**: `core/commands.py`
- **Nuovi comandi**:
  - `/memory` o `/m` - Statistiche memoria dettagliate
  - `/clear` - Azzera memoria (rinominato da `/reset`)
  - `/history` - Mostra ultimi 10 messaggi
  - `/config` - Mostra configurazione attuale
  - `/status` o `/s` - Status Ollama + modelli disponibili
- **Migliorati**:
  - `/help` - Tabella meglio formattata
  - `/tools` - Descrizioni più dettagliate con emoji
- Verifica stato Ollama in background

### ✅ **Router Query Intelligente**
- **File**: `core/tools/router.py`
- Prioritizzazione migliore query
- Logging di ogni routing
- Nuove frasi riconosciute:
  - "previsione", "previsioni" per meteo
  - "informazioni su", "dimmi di", "definizione di"
- Miglior parsing query complesse
- Fallback intelligente se tool fallisce

### ✅ **Tool API Migliorati**

#### **Meteo (api_weather.py)**
- Logging di cache hit/miss
- Emoji nel risultato 🌍
- Distingue tra errori (timeout vs connection)
- Fallback con dati memorizzati
- Timeout specifico gestito

#### **Wikipedia (api_wiki.py)**
- Logging di cache e ricerca
- Fallback a scraper if API fails
- Normalization query migliorato
- Emoji nel risultato 📚
- Migliori messaggi errore

#### **Scraper (scraper.py)**
- Logging dettagliato
- Emoji nei risultati 📄
- Timeout e connection errors distinti
- Filtra paragrafi Wikipedia troppo corti
- Messaggi errore più descrittivi

#### **Math (math.py)**
- ✅ Già buono, mantiene formato

### ✅ **CLI Completamente Rinnovata**
- **File**: `ui/cli.py` (ricreato da zero)
- Nuove funzioni render:
  - `render_error_msg()` - Per errori rossi
  - `render_success_msg()` - Per successi verdi
  - Emoji nella UI
- Migliore gestione Ctrl+C
  - Non esce, mostra prompt per digitar /exit
  - Message amichevole
- Miglior display status
  - Mostra tutti i modelli disponibili
  - Formato più leggibile
- Error recovery
  - Try-catch nel main loop
  - Continua dopo errori unexpected
- Spinner configurabile in velocity
- Logging di errori CLI
- Gestione eventi "message" dal controller

### ✅ **Entry Point (main.py)**
- Inizializzazione proper config e logging
- Log startup info
- Traccia Ollama URL e model usato
- Better error handling
- Graceful shutdown on Ctrl+C

### ✅ **Miglioramenti Generali**

#### **Gestione Errori**
- Try-catch specifici per differenti eccezioni
- Logging di ogni errore
- Messaggi utente friendly
- Suggerimenti quando possibile (es: "ollama serve" per Ollama offline)

#### **Performance**
- Cache system migliorato (max 100 entries)
- TTL configurabile per ogni cache entry
- Logging su file (non rallenta CLI)
- Spinner ottimizzato

#### **Robustezza**
- Resistenza a malformed JSON
- Graceful degradation quando tool fallisce
- Fallback chain per Wikipedia (API → scraper)
- Stale cache usabile se no connection

#### **Debug**
- Logging completo di ogni operazione
- File di log giornalieri in `logs/`
- Easy per diagnosticare problemi
- Config salvatile per reprodurre problemi

## 📁 Struttura Nuova

```
jarvis-core-fixed/
├── main.py                        ← entry point migliorato
├── config.py                      ← NEW: configurazione centralizzata
├── logger.py                      ← NEW: logging system
├── requirements.txt               ← aggiornato
├── jarvis_config.json             ← auto-generated config
├── logs/                          ← NEW: log files
├── memory.json                    ← memoria conversazione
├── tools_cache.json               ← cache dei tool
│
├── core/
│   ├── llm.py                     ← migliorato: logging, config
│   ├── memory.py                  ← migliorato: stats, clear, limits
│   ├── state.py                   ← (invariato)
│   ├── commands.py                ← migliorato: comandi nuovi/espansi
│   └── tools/
│       ├── router.py              ← migliorato: routing intelligente
│       ├── api_weather.py         ← migliorato: logging, emoji, errors
│       ├── api_wiki.py            ← migliorato: logging, fallback
│       ├── cache.py               ← (migliorato in precedenza)
│       ├── math.py                ← (invariato, già buono)
│       ├── scraper.py             ← migliorato: logging, errors
│       └── system.py              ← (invariato, già robusto)
│
├── controller/
│   └── jarvis_controller.py       ← (invariato, bridge perfetto)
│
└── ui/
    └── cli.py                     ← completamente ricreato: UI migliorato
```

## 🎯 Comandi Disponibili

```
/help, /h          → Mostra elenco comandi
/tools             → Mostra tool disponibili
/memory, /m        → Statistiche memoria conversazione
/clear             → Azzera la memoria
/status, /s        → Status sistema e Ollama
/config            → Mostra configurazione attuale
/history           → Ultimi 10 messaggi
/voice on          → Abilita sintesi vocale
/voice off         → Disabilita sintesi vocale
/voice status      → Stato sintesi vocale
/voice test        → Test sintesi vocale
/exit, /quit       → Chiude JARVIS
```

### 💻 Comandi Sistema Naturali

**Monitoraggio (senza privilegi):**
- "spazio disco" → Utilizzo disco
- "uptime" → Tempo attività sistema  
- "mostra rete" → Info interfacce rete
- "processi attivi" → Lista processi
- "temperatura CPU" → Temperature sistema
- "stato batteria" → Livello batteria

**Gestione (richiede root/sudo):**
- "aggiorna sistema" → Aggiorna pacchetti
- "installa htop" → Installa pacchetto
- "rimuovi htop" → Rimuovi pacchetto
- "servizio start apache2" → Gestisci servizi
- "hostname nuovo-nome" → Cambia hostname
- "mostra log" → Log di sistema

**Voce:**
- "/voice on" → Abilita sintesi vocale
- "/voice test" → Prova la voce

## ⚙️ Configurazione

### Via File `jarvis_config.json`
```json
{
  "ollama_url": "http://localhost:11434/api/chat",
  "model": "qwen2.5:7b",
  "temperature": 0.2,
  "max_response_length": 2000,
  "request_timeout": 120,
  "max_history_messages": 100,
  "show_banner": true,
  "spinner_speed": 0.12,
  "enable_voice": false,
  "voice_model": "voices/it_IT-riccardo-x_low.onnx",
  "voice_volume": 0.8
}
```

### Via Environment Variables
```bash
export OLLAMA_URL="http://custom:11434/api/chat"
export JARVIS_MODEL="neural-chat"
export JARVIS_TEMPERATURE="0.5"
```

## 📝 Logging

Log file giornalieri in `logs/jarvis_YYYYMMDD.log`:
```
2026-04-27 14:23:45 - jarvis - INFO - JARVIS starting...
2026-04-27 14:23:45 - jarvis - INFO - Ollama URL: http://localhost:11434/api/chat
2026-04-27 14:23:46 - jarvis - DEBUG - Routing query: chi è aristotele?
2026-04-27 14:23:46 - jarvis - DEBUG - Searching Wikipedia for: aristotele
2026-04-27 14:23:47 - jarvis - DEBUG - Wiki cache hit for aristotele
```

## 🚀 Avvio

```bash
# Assicurati che Ollama sia in esecuzione
ollama serve

# In un altro terminale
cd /home/gaetal/Desktop/jarvis-core-fixed
source venv/bin/activate
python main.py
```

### 🗣️ Sintesi Vocale

JARVIS supporta la sintesi vocale tramite Piper TTS:

```bash
# Abilita voce
/voice on

# Test
/voice test

# Controlla stato
/voice status
```

**Nota**: Assicurati di avere un player audio installato (paplay, aplay, play, etc.)

## 🐛 Troubleshooting

### Ollama Non Raggiungibile
```
❌ Ollama connection error
Assicurati che Ollama sia in esecuzione: ollama serve
```

### Controllare Log
```bash
tail -f logs/jarvis_*.log
```

### Resettare Tutto
```bash
rm memory.json tools_cache.json jarvis_config.json logs/*
```

## 🎨 Nuove Caratteristiche

- ✅ Emoji nei messaggi sistema
- ✅ Spinner animato configurabile  
- ✅ Status bar con info modelli
- ✅ Cronologia messaggi consultabile
- ✅ Statistiche memoria dettagliate
- ✅ Config file salvabile
- ✅ Logging completo per debug
- ✅ Error recovery graceful
- ✅ Fallback intelligenti nei tool
- ✅ Cache system robusto

## 📊 Metriche

- **Comandi**: 8 (era 5)
- **Tool**: 5 (invariato)
- **Logging**: DEBUG + INFO + WARNING + ERROR + CRITICAL (era nessuno)
- **Config**: 14 parametri configurabili
- **Cache**: Max 100 entries, TTL configurabile
- **Memory**: Limit 100 msg (era illimitato)

## 🔄 Versione Precedente

Backup della vecchia CLI salvata in `ui/cli_old.py` per reference.

---

**Ultima aggiornamento**: 27 Aprile 2026
**Versione**: 2.0
**Status**: ✅ Pronto per uso
