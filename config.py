"""
config.py — Configurazione centralizzata JARVIS PRO
Supporta JSON, YAML, variabili d'ambiente, e validazione.
"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional

CONFIG_FILE = Path("jarvis_config.json")
YAML_CONFIG = Path("jarvis_config.yaml")


@dataclass
class JarvisConfig:
    """Configurazione completa JARVIS PRO"""

    # ── LLM ───────────────────────────────────────
    ollama_url: str = "http://localhost:11434/api/chat"
    model: str = "qwen2.5:7b"
    temperature: float = 0.2
    max_response_length: int = 2000
    request_timeout: int = 120

    # ── Memory & Sessioni ─────────────────────────
    memory_file: str = "memory.json"
    max_history_messages: int = 100
    db_file: str = "db/jarvis.db"
    memory_cleanup_days: int = 30

    # ── CLI ───────────────────────────────────────
    show_banner: bool = True
    show_timestamps: bool = True
    spinner_speed: float = 0.12
    render_markdown: bool = True
    show_token_count: bool = True

    # ── Voce ──────────────────────────────────────
    enable_voice: bool = False
    voice_model: str = "voices/it_IT-riccardo-x_low.onnx"
    voice_volume: float = 0.8
    voice_length_scale: float = 0.95
    voice_sentence_silence: float = 0.05

    # ── Tool ──────────────────────────────────────
    enable_weather: bool = True
    enable_wiki: bool = True
    enable_math: bool = True
    enable_scraper: bool = True
    enable_system: bool = True
    enable_web_search: bool = True
    weather_cache_ttl: int = 3600

    # ── Sicurezza ─────────────────────────────────
    encrypt_memory: bool = False
    encryption_key_file: str = ".jarvis_key"
    rate_limit_requests: int = 60
    rate_limit_window: int = 60
    sanitize_input: bool = True

    # ── Web / API ─────────────────────────────────
    enable_api: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = ""
    enable_web_ui: bool = False
    web_port: int = 7860

    # ── Plugin ────────────────────────────────────
    enable_plugins: bool = True
    plugins_dir: str = "plugins"

    # ── Notifiche ─────────────────────────────────
    enable_notifications: bool = False
    notification_level: str = "important"

    # ── Lingua ────────────────────────────────────
    language: str = "it"
    languages_supported: list = field(default_factory=lambda: ["it", "en", "es", "fr", "de"])

    # ── Modalità silenziosa ───────────────────────
    silent_mode: bool = False
    silent_max_words: int = 20

    # ── Behaviour ─────────────────────────────────
    auto_connect: bool = True
    verbose_errors: bool = False
    context_window_size: int = 4096

    @classmethod
    def load(cls) -> "JarvisConfig":
        config = cls()

        # 1. Prova YAML (se disponibile)
        if YAML_CONFIG.exists():
            try:
                import yaml  # type: ignore
                data = yaml.safe_load(YAML_CONFIG.read_text())
                if isinstance(data, dict):
                    for k, v in data.items():
                        if hasattr(config, k):
                            setattr(config, k, v)
            except ImportError:
                pass
            except Exception:
                pass

        # 2. JSON (sovrascrive YAML)
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                for k, v in data.items():
                    if hasattr(config, k):
                        setattr(config, k, v)
            except Exception:
                pass

        # 3. Variabili d'ambiente (massima priorità)
        _env_str = lambda k, attr: setattr(config, attr, os.getenv(k)) if os.getenv(k) else None
        _env_bool = lambda k, attr: setattr(config, attr, os.getenv(k, "").lower() in ("true", "1", "yes")) if os.getenv(k) else None
        _env_int = lambda k, attr: setattr(config, attr, int(os.getenv(k))) if os.getenv(k) else None
        _env_float = lambda k, attr: setattr(config, attr, float(os.getenv(k))) if os.getenv(k) else None

        _env_str("OLLAMA_URL", "ollama_url")
        _env_str("JARVIS_MODEL", "model")
        _env_float("JARVIS_TEMPERATURE", "temperature")
        _env_bool("JARVIS_VOICE_ENABLED", "enable_voice")
        _env_str("JARVIS_VOICE_MODEL", "voice_model")
        _env_bool("JARVIS_ENCRYPT_MEMORY", "encrypt_memory")
        _env_bool("JARVIS_ENABLE_API", "enable_api")
        _env_int("JARVIS_API_PORT", "api_port")
        _env_str("JARVIS_API_KEY", "api_key")
        _env_bool("JARVIS_SILENT_MODE", "silent_mode")
        _env_str("JARVIS_LANGUAGE", "language")

        config._validate()
        return config

    def _validate(self):
        """Validazione configurazione"""
        assert 0.0 <= self.temperature <= 2.0, "temperature deve essere 0-2"
        assert 1 <= self.max_history_messages <= 10000
        assert self.request_timeout >= 5
        assert self.rate_limit_requests >= 1
        if self.language not in self.languages_supported:
            self.language = "it"

    def save(self):
        """Salva configurazione JSON"""
        data = asdict(self)
        CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def save_yaml(self):
        """Salva configurazione YAML"""
        try:
            import yaml  # type: ignore
            YAML_CONFIG.write_text(yaml.dump(asdict(self), default_flow_style=False, allow_unicode=True))
        except ImportError:
            self.save()


# ── Singleton ───────────────────────────────────────────────────────────────
_config: Optional[JarvisConfig] = None


def get_config() -> JarvisConfig:
    global _config
    if _config is None:
        _config = JarvisConfig.load()
    return _config


def set_config(config: JarvisConfig):
    global _config
    _config = config
