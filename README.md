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
ollama pull mistral

# 6. Avvia JARVIS
python main.py
```

## Cambiare modello

Modifica `core/llm.py`:

```python
MODEL = "llama3"   # o qualsiasi modello installato
```

## Comandi disponibili

| Comando   | Azione                          |
|-----------|---------------------------------|
| `/help`   | Mostra i comandi                |
| `/clear`  | Pulisce la schermata            |
| `/reset`  | Azzera la memoria               |
| `/status` | Stato Ollama + memoria          |
| `/exit`   | Esci                            |

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
