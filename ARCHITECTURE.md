# Architecture

Elograf is designed with a modular architecture that separates the UI and system integration from the specific speech-to-text (STT) engines.

## Abstract Interface Design

Elograf uses an abstract interface pattern to support multiple STT engines through a common API:

```
┌─────────────────────────────────────────────────────────────┐
│                     STT Engine Interface                      │
│                    (stt_engine.py)                           │
├─────────────────────────────────────────────────────────────┤
│  STTController (ABC)          STTProcessRunner (ABC)        │
│  ├─ add_state_listener()      ├─ start()                    │
│  ├─ add_output_listener()     ├─ stop()                     │
│  ├─ add_exit_listener()       ├─ suspend()                  │
│  ├─ remove_exit_listener()    ├─ resume()                   │
│  ├─ start()                   ├─ poll()                     │
│  ├─ stop_requested()          └─ is_running()               │
│  ├─ suspend_requested()                                      │
│  └─ resume_requested()                                       │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Hierarchy

```
STTController                    STTProcessRunner
     │                                  │
     ├── NerdDictationController        ├── NerdDictationProcessRunner
     │   └── NerdDictationState         │   └── Manages nerd-dictation CLI
     │                                  │
     ├── WhisperDockerController        ├── WhisperDockerProcessRunner
     │   └── WhisperDockerState         │   ├── Docker container management
     │                                  │   ├── Audio recording (AudioRecorder)
     │                                  │   ├── REST API client
     │                                  │   └── Voice Activity Detection
     │                                  │
     ├── GoogleCloudSpeechController    ├── GoogleCloudSpeechProcessRunner
     │   └── GoogleCloudSpeechState     │   ├── gRPC streaming client
     │                                  │   ├── Audio recording (AudioRecorder)
     │                                  │   └── Credentials management
     │                                  │
     ├── OpenAIRealtimeController       ├── OpenAIRealtimeProcessRunner
     │   └── OpenAIRealtimeState        │   ├── WebSocket client
     │                                  │   ├── Audio recording (AudioRecorder)
     │                                  │   └── Real-time streaming
     │                                  │
     └── AssemblyAIRealtimeController   └── AssemblyAIRealtimeProcessRunner
         └── AssemblyAIRealtimeState        ├── WebSocket client
                                            ├── Audio recording (AudioRecorder)
                                            └── Real-time streaming
```

## Component Interaction Flow

```
┌──────────────┐
│  SystemTray  │  User clicks icon / CLI command
│     Icon     │
└──────┬───────┘
       │
       ↓
┌──────────────────┐
│  STT Factory     │  create_stt_engine(engine_type, **kwargs)
│  (stt_factory)   │  → Returns (Controller, Runner)
└──────┬───────────┘
       │
       ↓
┌──────────────────────────────────────────┐
│     Controller        ←→      Runner     │
│  ┌─────────────┐          ┌───────────┐ │
│  │   States    │          │  Process  │ │
│  │  Listeners  │          │  Control  │ │
│  └──────┬──────┘          └─────┬─────┘ │
│         │                        │       │
│         └────── Events ──────────┘       │
└──────────────────────────────────────────┘
       │                        │
       ↓                        ↓
  State Updates          Audio/Transcription
  (Icon changes)         (Text input simulation)
```

## State Machine

Each engine implements its own state enum, but follows a common pattern:

```
IDLE
  ↓
STARTING  ──error──→  FAILED
  ↓
READY
  ↓
RECORDING  ←──resume──  SUSPENDED
  ↓              ↑
  └──suspend────┘
  ↓
TRANSCRIBING
  ↓
IDLE (on stop)
```

**State-specific behaviors:**
- **IDLE**: No engine running
- **STARTING**: Engine initialization
- **READY**: Engine ready to record
- **RECORDING**: Actively capturing audio
- **TRANSCRIBING**: Processing audio (Whisper/Cloud only)
- **SUSPENDED**: Paused, not recording
- **FAILED**: Error occurred

## Key Classes

### `stt_engine.py`
Abstract base classes defining the interface contract:
- **STTController**: State management and event notification
  - Provides listener registration/unregistration to prevent race conditions
  - `remove_exit_listener()` prevents old controller exit events from affecting new engines
- **STTProcessRunner**: Process lifecycle and audio handling

**Race Condition Prevention**: When refreshing engines, old controller exit handlers could fire after a new engine was created, incorrectly incrementing the failure counter for the new engine. The `remove_exit_listener()` method allows EngineManager to unregister callbacks from the old controller before creating a new one, ensuring old process exit events don't affect new engine state.

### `stt_factory.py`
Factory functions for engine creation:
- `create_stt_engine(engine_type, **kwargs)` → (Controller, Runner)
- `get_available_engines()` → List of engine names
- `is_engine_available(engine_type)` → bool

### Engine Implementations

**`nerd_controller.py`**
- Manages nerd-dictation subprocess
- Parses stdout for state changes
- Direct CLI integration

**`whisper_docker_controller.py`**
- Docker container lifecycle management
- REST API communication (POST /asr)
- Voice Activity Detection (VAD)
- Automatic reconnection
- Audio recording with AudioRecorder

**`google_cloud_speech_controller.py`**
- gRPC streaming client
- Service account authentication
- Audio chunk streaming
- Project auto-detection

**`openai_realtime_controller.py`**
- WebSocket bidirectional streaming
- Server-side VAD configuration
- Real-time partial transcriptions
- Base64 audio encoding

### `engine_manager.py`
Manages STT engine lifecycle, configuration, and failure recovery:
- **Engine Creation**: Creates engines via factory with proper listener registration
- **Refresh Logic**: Safely replaces running engines with updated configuration
  - Unregisters old controller callbacks before creating new engine
  - Prevents race conditions from late exit events
- **Failure Handling**: Implements circuit breaker pattern with fallback chain
- **Retry Logic**: Exponential backoff for transient failures
- **Timeout Protection**: Safety timer for stuck engine shutdowns

### `tray_icon.py`
System tray interface that:
1. Loads settings
2. Creates EngineManager with appropriate configuration
3. Delegates engine lifecycle to EngineManager
4. Updates icon based on state
5. Handles user interactions

### `settings.py`
Persistent configuration using QSettings:
- Core settings (device, shortcuts, etc.)
- Engine-specific settings (grouped by prefix)
- Load/save with defaults

## Audio Recording

All streaming engines (Whisper, Google Cloud, OpenAI, AssemblyAI) use a unified `AudioRecorder` class with pluggable backends:

```python
class AudioRecorder:
    """Unified audio recorder with selectable backend."""

    def __init__(self, sample_rate: int, channels: int,
                 backend: str = "auto", device: Optional[str] = None)
    def record_chunk(self, duration: float) -> bytes  # Returns WAV
```

**Backends:**
- **parec** (Linux/PulseAudio): Preferred on Linux, supports device selection
- **PyAudio**: Cross-platform fallback for other systems

**Features:**
- Format: PCM16 (16-bit signed integer)
- Configurable sample rate and channels
- Returns WAV-formatted audio data
- Automatic backend detection (prefers parec on Linux)
- Device selection support (parec backend only)

## Text Input Simulation

All engines use the same input simulation strategy:

```python
def _default_input_simulator(text: str):
    try:
        run(["dotool", "type", text])  # Wayland
    except:
        run(["xdotool", "type", "--", text])  # X11
```

## Configuration Storage

Settings are stored per-engine with clear prefixes:

```
# Whisper Docker
whisperModel, whisperLanguage, whisperPort,
whisperChunkDuration, whisperSampleRate, whisperChannels,
whisperVadEnabled, whisperVadThreshold, whisperAutoReconnect

# Google Cloud Speech
googleCloudCredentialsPath, googleCloudProjectId,
googleCloudLanguageCode, googleCloudModel,
googleCloudSampleRate, googleCloudChannels,
googleCloudVadEnabled, googleCloudVadThreshold

# OpenAI Realtime
openaiApiKey, openaiModel, openaiApiVersion,
openaiSampleRate, openaiChannels,
openaiVadEnabled, openaiVadThreshold,
openaiVadPrefixPaddingMs, openaiVadSilenceDurationMs
```

## File Locations

| Item | Path |
|------|------|
| Configuration | `~/.config/Elograf/Elograf.conf` |
| PID file | `~/.config/Elograf/elograf.pid` |
| User models | `~/.config/vosk-models` |
| System models | `/usr/share/vosk-models` |
| Translations | `/usr/share/elograf/translations` |
