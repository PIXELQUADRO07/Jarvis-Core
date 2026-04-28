"""
config.py — Configurazione centralizzata di JARVIS
Supporta valori di default e override da file .env o comando
"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict

CONFIG_FILE = Path("jarvis_config.json")


@dataclass
class JarvisConfig:
    """Configurazione di JARVIS"""
    # LLM settings
    ollama_url: str = "http://localhost:11434/api/chat"
    model: str = "qwen2.5:7b"
    temperature: float = 0.2
    max_response_length: int = 2000
    request_timeout: int = 120
    
    # Memory settings
    memory_file: str = "memory.json"
    max_history_messages: int = 100
    
    # CLI settings
    show_banner: bool = True
    show_timestamps: bool = True
    spinner_speed: float = 0.12
    
    # Voice settings
    enable_voice: bool = False
    voice_model: str = "voices/it_IT-riccardo-x_low.onnx"
    voice_volume: float = 0.8
    voice_length_scale: float = 0.95
    voice_sentence_silence: float = 0.05

    # Tool settings
    enable_weather: bool = True
    enable_wiki: bool = True
    enable_math: bool = True
    enable_scraper: bool = True
    enable_system: bool = True
    weather_cache_ttl: int = 3600
    
    # Behavior
    auto_connect: bool = True
    verbose_errors: bool = False
    
    @classmethod
    def load(cls):
        """Carica configurazione da file, env vars, e defaults"""
        config = cls()
        
        # Leggi da file se esiste
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            except Exception:
                pass
        
        # Override con variabili ambiente
        if os.getenv("OLLAMA_URL"):
            config.ollama_url = os.getenv("OLLAMA_URL")
        if os.getenv("JARVIS_MODEL"):
            config.model = os.getenv("JARVIS_MODEL")
        if os.getenv("JARVIS_TEMPERATURE"):
            try:
                config.temperature = float(os.getenv("JARVIS_TEMPERATURE"))
            except:
                pass
        if os.getenv("JARVIS_VOICE_ENABLED"):
            config.enable_voice = os.getenv("JARVIS_VOICE_ENABLED").lower() in ("true", "1", "yes")
        if os.getenv("JARVIS_VOICE_MODEL"):
            config.voice_model = os.getenv("JARVIS_VOICE_MODEL")
        if os.getenv("JARVIS_VOICE_VOLUME"):
            try:
                config.voice_volume = float(os.getenv("JARVIS_VOICE_VOLUME"))
            except:
                pass
        if os.getenv("JARVIS_VOICE_LENGTH_SCALE"):
            try:
                config.voice_length_scale = float(os.getenv("JARVIS_VOICE_LENGTH_SCALE"))
            except:
                pass
        if os.getenv("JARVIS_VOICE_SENTENCE_SILENCE"):
            try:
                config.voice_sentence_silence = float(os.getenv("JARVIS_VOICE_SENTENCE_SILENCE"))
            except:
                pass
        
        return config
    
    def save(self):
        """Salva configurazione a file"""
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2))


# Singleton globale
_config = None

def get_config() -> JarvisConfig:
    global _config
    if _config is None:
        _config = JarvisConfig.load()
    return _config

def set_config(config: JarvisConfig):
    global _config
    _config = config
