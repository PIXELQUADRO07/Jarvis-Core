# JARVIS AI — Core

Assistente AI locale con architettura a layer separati.


















<img width="1022" height="647" alt="Screenshot_20260425_175655" src="https://github.com/user-attachments/assets/01804166-a5e0-4bb0-8779-69f0a96c3bb9" />



## Struttura

```
jarvis-core/
├── main.py                        ← entry point
├── requirements.txt
├── memory.json                    ← memoria persistente (auto-generata)
│
├── core/
│   ├── llm.py                     ← streaming Ollama
│   ├── memory.py                  ← persistenza conversazioni
│   ├── state.py                   ← status globale thread-safe
│   └── commands.py                ← routing comandi /slash
│
├── controller/
│   └── jarvis_controller.py       ← unico bridge UI ↔ core
│
└── ui/
    └── cli.py                     ← solo rendering, zero logica
```

## Setup

```bash
# 1. Clona la repo
git clone https://github.com/PIXELQUADRO07/Jarvis-Core

# 2. Installa dipendenze Python
pip install -r requirements.txt

# 3. Scarica Ollama
\\ARCH LINUX:
sudo pacman -S ollama

\\KALI LINUX o altre distro:
sudo apt install ollama

# 4. Assicurati che Ollama sia in esecuzione
ollama serve

# 5. Scarica il modello (se non l'hai già)
ollama pull qwen2.5:7b

# 6. Avvia JARVIS
python main.py
```

## Cambiare modello

Il modello può essere cambiato in diversi modi:

### 1. Modifica `config.py`
Cambia il valore di default in `config.py`:
```python
model: str = "qwen2.5:7b"  # o qualsiasi modello installato
```

### 2. Usa variabile d'ambiente
```bash
export JARVIS_MODEL="qwen2.5:7b"
python main.py
```

### 3. Crea file `jarvis_config.json`
```json
{
  "model": "qwen2.5:7b"
}
```

## Comandi disponibili

| Comando   | Azione                          |
|-----------|---------------------------------|
| `/help`   | Mostra i comandi                |
| `/clear`  | Pulisce la schermata            |
| `/reset`  | Azzera la memoria               |
| `/status` | Stato Ollama + memoria          |
| `/config` | Mostra configurazione attuale    |
| `/voice`  | Controlla sintesi vocale        |
| `/exit`   | Esci                            |

## Comandi Sistema

JARVIS supporta anche comandi naturali per la gestione del sistema:

### 📊 Monitoraggio (senza root)
- **"quanta RAM hai?"** → Mostra utilizzo memoria
- **"spazio disco"** → Utilizzo spazio su disco
- **"uptime"** → Tempo di attività del sistema
- **"mostra rete"** → Informazioni interfacce di rete
- **"processi attivi"** → Lista processi in esecuzione
- **"temperatura CPU"** → Temperature sistema (se disponibile)
- **"stato batteria"** → Livello batteria (se laptop)

### 🔧 Gestione Sistema (richiede root)
- **"aggiorna sistema"** → Aggiorna pacchetti
- **"installa firefox"** → Installa pacchetto
- **"rimuovi firefox"** → Rimuovi pacchetto
- **"servizio start apache2"** → Gestisci servizi systemd
- **"hostname nuovo-nome"** → Cambia hostname
- **"mostra log"** → Ultimi log di sistema

### 🌐 Applicazioni
- **"apri firefox"** → Apri Firefox
- **"firefox cerca python"** → Cerca su Google con Firefox
- **"apri gedit"** → Apri qualsiasi applicazione

### 💻 Sistema
- **"che distro è?"** → Mostra distribuzione Linux
- **"quanti CPU hai?"** → Numero processori logici

## Sintesi Vocale

JARVIS supporta la sintesi vocale tramite Piper TTS per rendere le risposte udibili.

### Installazione
```bash
# Installa Piper
pip install piper-tts

# Scarica modello voce italiano (già presente)
# I modelli sono in voices/
```

### Comandi Voce
```
/voice on      → Abilita sintesi vocale
/voice off     → Disabilita sintesi vocale  
/voice status  → Mostra stato voce
/voice test    → Test sintesi vocale
```

### Configurazione
```json
{
  "enable_voice": true,
  "voice_model": "voices/it_IT-riccardo-x_low.onnx",
  "voice_volume": 0.8
}
```

### Variabili Ambiente
```bash
export JARVIS_VOICE_ENABLED="true"
export JARVIS_VOICE_MODEL="voices/it_IT-riccardo-x_low.onnx"
export JARVIS_VOICE_VOLUME="0.8"
```

## Architettura

```
UI (cli.py)
  ↓ input grezzo
Controller (jarvis_controller.py)
  ↓ UIEvent generator
  ├── /comando → core/commands → UIEvent(action)
  └── testo    → core/llm     → UIEvent(ai_chunk) × N → UIEvent(ai_done)
UI
  ↓ renderizza ogni UIEvent
```

La UI non conosce mai Ollama, la memoria o i comandi.
Il core non conosce mai Rich o prompt_toolkit.
