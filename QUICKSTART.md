# 🚀 JARVIS AI — Guida Rapida

## Requisiti
- Python 3.10+
- Ollama in esecuzione (`ollama serve`)
- Dipendenze installate

## Setup Veloce

```bash
# 1. Clone e accedi directory
cd /home/gaetal/Desktop/jarvis-core-fixed

# 2. Attiva virtual environment
source venv/bin/activate

# 3. Installa dipendenze (se necessario)
pip install -r requirements.txt

# 4. Avvia Ollama in un terminale
ollama serve

# 5. In un altro terminale, avvia JARVIS
python main.py
```

## Primi Comandi

```
❯ COMANDO // ciao
  // JARVIS scrive la risposta...

❯ COMANDO // /status
  📡 Sistema JARVIS
  Ollama: 🟢 ONLINE
  Modello: qwen2.5:7b
  ...

❯ COMANDO // meteo a Roma
  🌍 Roma: Partly cloudy, 15°C, ...

❯ COMANDO // chi è Leonardo da Vinci
  (Wikipedia info...)

❯ COMANDO // quanto fa 2 + 3 * 4
  Risultato: 14

❯ COMANDO // spazio disco
  Utilizzo spazio disco:
  Filesystem      Size  Used Avail Use% Mounted on
  /dev/sda1        50G   25G   23G  52% /

❯ COMANDO // quanti CPU hai
  Numero di CPU logici: 8

❯ COMANDO // /voice status
  🔊 Stato Sintesi Vocale:
    Abilitata: 🔴 DISABILITATA
    Disponibile: 🟢 DISPONIBILE
    Modello: voices/it_IT-riccardo-x_low.onnx
    Volume: 0.8

❯ COMANDO // /voice on
  ✓ Sintesi vocale abilitata. Disponibile: True

❯ COMANDO // /voice test
  ✓ Test sintesi vocale completato
  (JARVIS pronuncia: "Ciao! Questa è una prova della sintesi vocale di JARVIS.")

❯ COMANDO // /exit
  Sistemi in spegnimento. Arrivederci.
```

## Configurazione

### Modifica configurazione
Edita `jarvis_config.json` o usa ENV vars:

```bash
export OLLAMA_URL="http://localhost:11434/api/chat"
export JARVIS_MODEL="qwen2.5:7b"
python main.py
```

### Vedi configurazione attuale
```
❯ COMANDO // /config
  ⚙️ Configurazione Attuale:
  Ollama URL: http://localhost:11434/api/chat
  Modello: qwen2.5:7b
  Temperatura: 0.2
  ...
```

## Problemi Comuni

### ❌ "Ollama non raggiungibile"
```bash
# Verifica Ollama è in esecuzione
ollama serve

# O controlla URL
export OLLAMA_URL="http://localhost:11434/api/chat"
```

### ❌ "Nessun modello disponibile"
```bash
# Scarica un modello
ollama pull qwen2.5:7b
ollama pull neural-chat
```

### ❌ ImportError
```bash
# Reinstalla dipendenze
pip install -r requirements.txt
```

## Debug

### Vedi log
```bash
# Log in tempo reale
tail -f logs/jarvis_*.log

# O cerca errori specifici
grep ERROR logs/jarvis_*.log
```

### Reset completo
```bash
rm memory.json tools_cache.json jarvis_config.json
```

## Comandi Principali

| Comando | Funzione |
|---------|----------|
| `/help` | Mostra tutti i comandi |
| `/status` | Status Ollama e memoria |
| `/memory` | Statistiche conversazione |
| `/history` | Ultimi 10 messaggi |
| `/clear` | Azzera memoria |
| `/config` | Mostra config attuale |
| `/tools` | Strumenti disponibili |
| `/exit` | Chiude JARVIS |

## Esempi Utilizzo

### Domande Generali
```
❯ chi è Aristotele?
❯ cos'è la fotosintesi?
❯ parlami di quantum computing
```

### Calcoli
```
❯ quanto fa 2^10?
❯ calcola sin(pi/2)
❯ 100 * 50 - 200
```

### Meteo
```
❯ meteo a Milano
❯ previsioni per Roma
❯ tempo a Torino
```

### Web
```
❯ https://example.com
❯ scarica il titolo da https://news.google.com
```

### Sistema
```
❯ che distro ho?
❯ quanta RAM ho?
❯ quanti CPU?
```

## Tips & Tricks

1. **Memoria**: Usa `/history` per rivedere la conversazione
2. **Velocità**: La cache riduce latenza per query ripetute
3. **Config**: Modifica temperatura in `jarvis_config.json` per risposte più creative/conservative
4. **Modelli**: Prova diversi modelli Ollama per qualità diverse
5. **Log**: Controlla `logs/` per debuggare problemi

## Architettura

```
UI (CLI)
   ↓
Controller (dispatcher)
   ↓
Router (comandi / AI)
   ├→ Tool (meteo, wiki, math, etc.)
   └→ LLM (Ollama)
       ↓
   Memory (persistenza)
```

## Struttura File Importanti

- `main.py` - Entry point
- `config.py` - Configurazione
- `logger.py` - Sistema logging
- `core/llm.py` - Chiamate Ollama
- `core/memory.py` - Persistenza conversazione
- `core/commands.py` - Comandi slash
- `core/tools/` - Tool disponibili
- `ui/cli.py` - Interfaccia utente

## Sviluppo

Per aggiungere un nuovo tool:
1. Crea `core/tools/my_tool.py`
2. Implementa funzione `my_tool(query: str) -> str`
3. Aggiungi logica in `core/tools/router.py`
4. Test manuale

## License

Internal project - JARVIS AI v2.0

---

**Per altre info**: vedi `README.md` e `IMPROVEMENTS.md`
