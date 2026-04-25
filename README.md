# JARVIS AI — Core

Assistente AI locale con architettura a layer separati.

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
# 1. Installa dipendenze Python
pip install -r requirements.txt

# 2. Assicurati che Ollama sia in esecuzione
ollama serve

# 3. Scarica il modello (se non l'hai già)
ollama pull mistral

# 4. Avvia JARVIS
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
