# JARVIS Phase 3 — Voice Enhancement Implementation Guide

**Duration:** 6-8 hours  
**Start date:** After Phase 2 complete (optional)  
**Target:** Voice input (wake words, STT), interruption control, model selection

---

## Overview

Phase 3 adds voice capabilities:
1. **Wake Word Detection** - "Ehi JARVIS" via microphone
2. **STT (Speech-to-Text)** - Transcribe audio to text
3. **Voice Interruption** - Stop TTS playback mid-sentence
4. **Voice Model Selection** - /voice model [name]

**Impact:** Full voice interaction - speak instead of typing

---

## Feature 1: Wake Word Detection

### Scope
- Listen for "Ehi JARVIS" phrase
- Lightweight (use Porcupine or PocketSphinx for efficiency)
- Non-blocking (background listener)
- Trigger STT when detected

### Implementation

**File:** `core/wake_word.py` (NEW)

```python
#!/usr/bin/env python3
"""
Wake word detection using PocketSphinx + PyAudio.
Listens for "Ehi JARVIS" trigger phrase.
"""

import threading
import queue
from typing import Callable, Optional
from logger import debug, info, warning, error

# Use PocketSphinx for lightweight wake word detection
try:
    from pocketsphinx import Decoder
    POCKETSPHINX_AVAILABLE = True
except ImportError:
    POCKETSPHINX_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class WakeWordDetector:
    """Detects wake word "Ehi JARVIS" using PocketSphinx"""
    
    def __init__(self, wake_phrase: str = "ehi jarvis", sensitivity: float = 1.0):
        if not POCKETSPHINX_AVAILABLE or not PYAUDIO_AVAILABLE:
            raise RuntimeError(
                "PocketSphinx or PyAudio not installed. "
                "Install: pip install pocketsphinx pyaudio"
            )
        
        self.wake_phrase = wake_phrase
        self.sensitivity = sensitivity
        self.running = False
        self.listener_thread: Optional[threading.Thread] = None
        self.detection_queue: queue.Queue = queue.Queue()
        
        # Initialize decoder
        try:
            config = {
                'keyphrase': 'wakeword',
                'kws_threshold': max(1e-50, 1e-50 / sensitivity),  # Lower = more sensitive
            }
            self.decoder = Decoder(keyphrase=self.wake_phrase.lower(), **config)
        except Exception as e:
            warning(f"Failed to initialize PocketSphinx: {e}")
            self.decoder = None
    
    def start_listening(self, on_detection: Callable = None):
        """Start background listener thread"""
        if self.running:
            return
        
        if self.decoder is None:
            warning("PocketSphinx decoder not initialized")
            return
        
        self.running = True
        self.on_detection = on_detection
        
        self.listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self.listener_thread.start()
        info("Wake word listener started")
    
    def stop_listening(self):
        """Stop listener thread"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=2)
        info("Wake word listener stopped")
    
    def _listen_loop(self):
        """Background listener loop"""
        if not PYAUDIO_AVAILABLE:
            return
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=512
        )
        
        try:
            while self.running:
                data = stream.read(512)
                
                if self.decoder:
                    self.decoder.start_utt()
                    self.decoder.process_raw(data, False, False)
                    self.decoder.end_utt()
                    
                    if self.decoder.hyp() and self.decoder.hyp().hypstr == self.wake_phrase:
                        info("Wake word detected: Ehi JARVIS")
                        if self.on_detection:
                            self.on_detection()
                        # Brief cooldown to avoid duplicate detections
                        threading.Event().wait(1.0)
        
        except Exception as e:
            error(f"Error in wake word listener: {e}")
        
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()


# Fallback: Simple keyword matcher for testing (without PocketSphinx)
class SimpleWakeWordDetector:
    """Fallback wake word detector using simple keyword matching"""
    
    def __init__(self, wake_phrase: str = "ehi jarvis"):
        self.wake_phrase = wake_phrase.lower()
        self.running = False
        self.listener_thread = None
        self.on_detection = None
    
    def start_listening(self, on_detection: Callable = None):
        """Start listening"""
        self.running = True
        self.on_detection = on_detection
        info("Simple wake word detector started (testing mode)")
    
    def stop_listening(self):
        """Stop listening"""
        self.running = False
        info("Simple wake word detector stopped")
    
    def check_text(self, text: str) -> bool:
        """Check if text contains wake phrase"""
        if self.wake_phrase in text.lower():
            info("Wake word detected in text")
            if self.on_detection:
                self.on_detection()
            return True
        return False


# Use PocketSphinx if available, fallback to simple detector
def get_wake_word_detector() -> WakeWordDetector:
    """Get wake word detector"""
    try:
        return WakeWordDetector(wake_phrase="ehi jarvis")
    except RuntimeError:
        warning("Falling back to simple wake word detector")
        return SimpleWakeWordDetector(wake_phrase="ehi jarvis")


# Test
if __name__ == "__main__":
    print("Wake Word Detection Test")
    print("=" * 40)
    
    detector = get_wake_word_detector()
    print(f"Detector type: {type(detector).__name__}")
    
    # For SimpleWakeWordDetector
    if isinstance(detector, SimpleWakeWordDetector):
        print("\nTesting with text input:")
        print(detector.check_text("Ehi JARVIS ciao"))  # True
        print(detector.check_text("ciao amico"))  # False
```

### Testing
```bash
# Install dependencies first
pip install pocketsphinx pyaudio

# Run test
python core/wake_word.py

# In JARVIS with voice enabled:
# Say "Ehi JARVIS" → should trigger STT
```

---

## Feature 2: STT (Speech-to-Text)

### Scope
- Transcribe audio to text using OpenAI Whisper
- Auto-detect language (Italian or English)
- Save audio files temporarily
- Error handling for noisy input

### Implementation

**File:** `core/stt.py` (NEW)

```python
#!/usr/bin/env python3
"""
Speech-to-Text using OpenAI Whisper.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
from logger import debug, info, warning, error

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class SpeechToText:
    """Convert audio to text using Whisper"""
    
    def __init__(self, model: str = "base", language: str = "it"):
        """
        Initialize STT
        
        Args:
            model: Whisper model size - tiny, base, small, medium, large
            language: Language code - 'it' for Italian, 'en' for English
        """
        if not WHISPER_AVAILABLE:
            raise RuntimeError(
                "Whisper not installed. Install: pip install openai-whisper"
            )
        
        self.model_name = model
        self.language = language
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model"""
        try:
            debug(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            info(f"Whisper {self.model_name} loaded")
        except Exception as e:
            error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe_file(self, audio_file: str) -> Optional[str]:
        """
        Transcribe audio file
        
        Args:
            audio_file: Path to .wav, .mp3, .m4a, etc.
        
        Returns:
            Transcribed text or None if failed
        """
        try:
            debug(f"Transcribing: {audio_file}")
            
            result = self.model.transcribe(
                audio_file,
                language=self.language,
                fp16=False,  # Use float32 for compatibility
            )
            
            text = result.get("text", "").strip()
            info(f"Transcribed: {text[:100]}")
            return text
        
        except Exception as e:
            error(f"Transcription failed: {e}")
            return None
    
    def record_and_transcribe(self, duration: int = 5, timeout: int = 10) -> Optional[str]:
        """
        Record audio from microphone and transcribe
        
        Args:
            duration: Recording duration in seconds
            timeout: Transcription timeout in seconds
        
        Returns:
            Transcribed text or None if failed
        """
        if not PYAUDIO_AVAILABLE:
            error("PyAudio not available for recording")
            return None
        
        try:
            import pyaudio
            import wave
            
            # Record audio
            audio_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            audio_path = audio_file.name
            audio_file.close()
            
            info(f"Recording for {duration} seconds...")
            
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            frames = []
            for _ in range(int(16000 / 1024 * duration)):
                data = stream.read(1024)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Save to file
            wf = wave.open(audio_path, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paFloat32))
            wf.setframerate(16000)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # Transcribe
            text = self.transcribe_file(audio_path)
            
            # Clean up
            Path(audio_path).unlink()
            
            return text
        
        except Exception as e:
            error(f"Record and transcribe failed: {e}")
            return None


# Module-level singleton
_stt: Optional[SpeechToText] = None

def get_stt(model: str = "base", language: str = "it") -> Optional[SpeechToText]:
    """Get singleton STT instance"""
    global _stt
    if _stt is None:
        try:
            _stt = SpeechToText(model=model, language=language)
        except RuntimeError:
            warning("Whisper not available")
            return None
    return _stt


# Test
if __name__ == "__main__":
    print("STT Test")
    print("=" * 40)
    
    stt = get_stt()
    if stt:
        print("STT ready. Run: stt.record_and_transcribe(duration=5)")
    else:
        print("Whisper not available")
```

### Testing
```bash
# Install Whisper
pip install openai-whisper

# Test
python core/stt.py
# Then: stt.record_and_transcribe(duration=5)
```

---

## Feature 3: Voice Interruption

### Scope
- Stop TTS playback when user speaks or says "basta"
- Flag in VoiceEngine checked during playback
- Graceful interrupt (no crashes)

### Implementation

**Modify `core/voice_engine.py`:**

```python
# Add interrupt flag
class VoiceEngine:
    def __init__(self):
        # ... existing code ...
        self.interrupt_requested = False
    
    def request_interrupt(self):
        """Request voice playback to stop"""
        self.interrupt_requested = True
        info("Voice interrupt requested")
    
    def _play_chunk(self, text_chunk: str):
        """Play chunk with interrupt check"""
        # Check interrupt before starting
        if self.interrupt_requested:
            self.interrupt_requested = False
            return
        
        # Play chunk (generate and play audio)
        audio_data = self.tts_model.generate(text_chunk)
        
        # Check interrupt during playback (between chunks)
        if self.interrupt_requested:
            self.interrupt_requested = False
            info("Voice interrupted")
            return
        
        # Actual playback
        self._write_audio(audio_data)
```

---

## Feature 4: /voice model [nome]

### Scope
- List available voice models
- Switch model live
- Show current voice settings

### Implementation

**Modify `core/commands.py`:**

```python
def handle_voice_command(args: list) -> str:
    """
    Handle /voice commands:
    - /voice list        → list available models
    - /voice set [name]  → set current model
    - /voice current     → show current model
    - /voice speed [0-2] → set speech speed
    """
    config = get_config()
    
    if not args:
        return "Usage: /voice list|set|current|speed [value]"
    
    command = args[0].lower()
    
    if command == "list":
        from pathlib import Path
        voices_dir = Path("voices")
        if voices_dir.exists():
            models = [f.stem for f in voices_dir.glob("*.onnx")]
            return "🎵 Available voice models:\n" + "\n".join(f"  • {m}" for m in models)
        return "❌ No voice models found"
    
    elif command == "set" and len(args) > 1:
        model_name = args[1]
        config.voice_model = model_name
        return f"✅ Voice model set to: {model_name}"
    
    elif command == "current":
        speed = getattr(config, "voice_speed", 1.0)
        return f"🎵 Current: {config.voice_model} (speed: {speed}x)"
    
    elif command == "speed" and len(args) > 1:
        try:
            speed = float(args[1])
            speed = max(0.5, min(2.0, speed))  # Clamp 0.5-2.0
            config.voice_speed = speed
            return f"✅ Voice speed set to: {speed}x"
        except ValueError:
            return "❌ Invalid speed (use 0.5-2.0)"
    
    return "Unknown subcommand"
```

---

## 📋 Phase 3 Implementation Checklist

### Step 1: Dependencies (15 min)
- [ ] Install: `pip install pocketsphinx pyaudio openai-whisper`
- [ ] Note: Downloads ~100MB for Whisper models

### Step 2: Wake Word Detection (1-1.5 hours)
- [ ] Create `core/wake_word.py`
- [ ] Implement `WakeWordDetector` class
- [ ] Implement fallback `SimpleWakeWordDetector`
- [ ] Test: `python core/wake_word.py`

### Step 3: STT (1.5-2 hours)
- [ ] Create `core/stt.py`
- [ ] Implement `SpeechToText` class
- [ ] Test recording: `stt.record_and_transcribe()`
- [ ] Test file: `stt.transcribe_file()`

### Step 4: Voice Interruption (30-45 min)
- [ ] Add `interrupt_requested` flag to VoiceEngine
- [ ] Add `request_interrupt()` method
- [ ] Check interrupt in `_play_chunk()`
- [ ] Test: Stop TTS mid-sentence

### Step 5: /voice Command (30-45 min)
- [ ] Create `handle_voice_command()` in `core/commands.py`
- [ ] Add "voice" to COMMANDS registry
- [ ] Test: /voice list, /voice set, /voice current

### Step 6: Integration (1-1.5 hours)
- [ ] Wire wake word detector to STT
- [ ] Hook STT output to main CLI input
- [ ] Test full flow: Say "Ehi JARVIS" → hears input

### Step 7: Testing (1 hour)
- [ ] Test wake word detection
- [ ] Test STT transcription
- [ ] Test voice interruption
- [ ] Test /voice commands
- [ ] Check microphone/speaker working

---

## ✅ Success Criteria

Phase 3 = SUCCESS when:

✅ Wake word detected correctly  
✅ STT transcribes audio to text  
✅ Voice can be interrupted mid-playback  
✅ /voice model [name] works  
✅ /voice list shows models  
✅ /voice current shows settings  
✅ No microphone crashes  

**Estimated time:** 6-8 hours  
**Complexity:** High (audio I/O)  
**Risk:** Medium (external audio hardware)  

---

Created: 30 Apr 2026  
Last updated: 30 Apr 2026  
Next: PHASE_4_GUIDE.md (Tool System)

