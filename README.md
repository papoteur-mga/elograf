# Elograf

**Multi-engine voice recognition utility**

Elograf is a desktop application that provides a graphical interface for multiple speech-to-text engines. Originally designed for [nerd-dictation](https://github.com/ideasman42/nerd-dictation), it now supports multiple STT backends including Whisper Docker, Google Cloud Speech, and OpenAI Realtime API. It runs in your system tray and offers easy control over dictation through an intuitive icon and menu system.

---

## Features

### 🎤 Quick Access Control
- **System tray icon** reflecting current state (loading, ready, dictating, suspended, stopped)
- **Single-click operation**: Click to cycle through start → suspend → resume
- **Menu controls**: Start, suspend/resume, or stop dictation
- **CLI integration**: Control dictation from command line with `--begin`, `--end`, `--toggle`

### ⚙️ Advanced Configuration
- **Multiple language models**: Download and manage models from alphacei website
- **Model storage**: Install models in user space or system-wide (with polkit authentication)
- **Custom models**: Add your own model directories with unique names
- **Audio device selection**: Choose from available PulseAudio input devices
- **Input simulation**: Support for both XDOTOOL (X11) and DOTOOL (Wayland)
- **Pre/post commands**: Run custom commands before and after dictation

### ⌨️ Global Keyboard Shortcuts (KDE)
With PyQt6-DBus installed on KDE, configure system-wide shortcuts for:
- Begin dictation
- End dictation
- Toggle dictation
- Suspend/resume dictation

### 🔧 Flexible Options
- Customize sample rate, timeout, idle time
- Punctuation from previous timeout
- Numbers as digits or words
- Full sentence capitalization
- Environment variable configuration

---

## Speech-to-Text Engines

Elograf supports four different STT engines, each with unique strengths:

### 1. **nerd-dictation** (Default)
Local, privacy-focused CLI tool with multiple backend support.

**Features:**
- Fully offline operation
- Multiple model support (Vosk, etc.)
- Direct system integration
- No API costs

**Requirements:**
- nerd-dictation installed separately
- Vosk model files

**Best for:** Privacy-conscious users, offline environments, no-cost operation

### 2. **Whisper Docker**
Docker container running OpenAI's Whisper ASR webservice.

**Features:**
- High accuracy transcription
- Configurable models (tiny, base, small, medium, large-v3)
- Voice Activity Detection (VAD)
- Auto-reconnect on failures
- Suspend/resume support
- Configurable chunk duration

**Requirements:**
- Docker installed
- Internet for first-time image download (~2GB)
- Docker image: `onerahmet/openai-whisper-asr-webservice`

**Configuration:**
- Model: Choose size/accuracy tradeoff
- Language: Auto-detect or specify
- Port: API port (default: 9000)
- Chunk Duration: Audio processing interval
- VAD: Skip silent audio chunks

**Best for:** High accuracy offline transcription, Docker-enabled systems

### 3. **Google Cloud Speech-to-Text V2**
Google's enterprise-grade speech recognition API with gRPC streaming.

**Features:**
- Real-time streaming recognition
- State-of-the-art accuracy with Chirp 3 model
- Multi-language support
- Server-side VAD
- Suspend/resume support
- Automatic project detection

**Requirements:**
- Google Cloud account
- Service account credentials JSON file
- `google-cloud-speech` Python library
- Project with Speech-to-Text API enabled

**Configuration:**
- Credentials Path: Path to service account JSON
- Project ID: GCP project (auto-detected if empty)
- Language Code: e.g., "en-US", "es-ES"
- Model: chirp_3, latest_long, etc.

**Best for:** Enterprise applications, multi-language support, maximum accuracy

### 4. **OpenAI Realtime API**
OpenAI's GPT-4o real-time transcription via WebSocket streaming.

**Features:**
- Ultra-low latency streaming
- WebSocket bidirectional connection
- Server-side VAD with configurable thresholds
- Partial and final transcriptions
- Model selection (full vs mini)
- Suspend/resume support

**Requirements:**
- OpenAI API key
- `websocket-client` Python library
- Internet connection

**Configuration:**
- API Key: OpenAI API key (required)
- Model: `gpt-4o-transcribe` (full) or `gpt-4o-mini-transcribe` (faster)
- API Version: default "2025-08-28"
- VAD Threshold: Sensitivity (0.0-1.0)
- VAD Timing: Prefix padding and silence duration

**Pricing:**
- Input: $32/1M audio tokens ($0.40 cached)
- Output: $64/1M audio tokens

**Best for:** Real-time applications, minimal latency requirements, cloud-based workflows

### Selecting an Engine

Configure the STT engine in **Advanced Settings**:
1. Open configuration from system tray menu
2. Go to "Advanced" tab
3. Select "STT Engine" from dropdown
4. Configure engine-specific settings below
5. Save and restart dictation

---

## Installation

### Using `uv` (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package and project manager that handles dependencies automatically.

**Install globally as a tool:**
```bash
uv tool install git+https://github.com/papoteur-mga/elograf
```

**For development:**
```bash
# Clone the repository
git clone https://github.com/papoteur-mga/elograf
cd elograf

# Install with all dependencies
uv pip install -e .
```

**Run without installing:**
```bash
uv run elograf
```

### Requirements

**Core Dependencies:**
- Python 3.7+
- PyQt6 (includes D-Bus support for KDE global shortcuts)
- ujson
- AudioRecorder with backends:
  - parec (PulseAudio utils) - Linux, supports device selection
  - PyAudio - Cross-platform fallback
- vosk

**Engine-Specific Dependencies:**
- **nerd-dictation**: Must be installed separately (not included)
- **Whisper Docker**: `requests` (auto-installed), Docker
- **Google Cloud Speech**: `google-cloud-speech` (auto-installed)
- **OpenAI Realtime**: `websocket-client` (auto-installed)

**All Python dependencies are automatically installed by `uv`:**
```bash
uv pip install -e .
```

This installs: `ujson`, `PyQt6`, `vosk`, `pyaudio` (optional), `requests`, `google-cloud-speech`, and `websocket-client`.

### Wayland Support

For **Wayland** (including KDE Plasma Wayland), Elograf uses **dotool** instead of xdotool for text input simulation.

#### Installing dotool

**Arch/Manjaro:**
```bash
sudo pacman -S dotool
```

**Fedora:**
```bash
sudo dnf install dotool
```

**Ubuntu/Debian/KDE Neon:**
```bash
# Install dependencies
sudo apt install -y build-essential golang-go libevdev-dev scdoc libxkbcommon-dev

# Build from source
cd /tmp
git clone https://git.sr.ht/~geb/dotool
cd dotool
./build.sh
sudo ./build.sh install

# Reload udev rules (no reboot required)
sudo udevadm control --reload-rules
sudo udevadm trigger
```

**Verification:**
```bash
dotool <<< "type hello"
# Should type "hello" in your active window
```

#### Configuration

1. Open Elograf's **Advanced Settings**
2. Set **Input Tool** to `DOTOOL`
3. Set **Keyboard Layout** if needed (e.g., `us`, `es`, `fr`)

#### Note on Permissions

dotool uses uinput to simulate keyboard input. The `sudo ./build.sh install` command automatically installs udev rules that grant necessary permissions. You may need to log out and back in for group changes to take effect.

---

## Usage

### Starting Elograf

Launch at desktop startup to display the system tray icon. Add `elograf` to your desktop environment's autostart applications.

```bash
elograf                   # Launch application with system tray icon
elograf --version         # Show version and exit
```

### Direct Click Mode

Enable "Active direct click on icon" in preferences:
- Single left-click starts dictation
- Another click stops it
- Right-click opens menu (configure, exit)

### Command Line Interface

Control a running Elograf instance from the terminal:

```bash
elograf --begin                    # Start dictation
elograf -s                         # Start dictation (short form, backward compatible)
elograf --end                      # Stop dictation
elograf --toggle                   # Toggle dictation state
elograf --exit                     # Exit application
elograf --list-models              # List all models (● shows current)
elograf --set-model vosk-en-us     # Switch to specific model
elograf -l DEBUG                   # Set log level (DEBUG, INFO, WARNING, ERROR)
```

> 💡 **Single Instance**: Only one Elograf instance runs at a time. Commands communicate via IPC (D-Bus or local sockets).

### Configuration

The configuration dialog appears automatically if no model is set. Access it anytime from the tray menu:

#### Models Tab
- Select from installed models
- Download new models from alphacei
- Add custom model directories
- Store models in user (`~/.config/vosk-models`) or system space (`/usr/share/vosk-models`)

#### Advanced Settings

**General Settings:**
- **Audio Device**: Select microphone from available PulseAudio sources
- **Pre-command**: Run before STT engine starts (e.g., `setxkbmap fr`)
- **Post-command**: Run after STT engine stops
- **Input Tool**: XDOTOOL (X11) or DOTOOL (Wayland)
- **Keyboard Layout**: Required for DOTOOL (e.g., 'fr', 'de', 'us')
- **Global Shortcuts**: KDE-only system-wide keyboard shortcuts

**STT Engine Selection:**
- **STT Engine**: Choose between nerd-dictation, whisper-docker, google-cloud-speech, or openai-realtime

**nerd-dictation Settings:**
- **Sample Rate**: Recording sample rate (default: 44100 Hz)
- **Timeout**: Auto-stop after silence (0 disables)
- **Idle Time**: CPU vs responsiveness trade-off (default: 100ms)
- **Punctuation Timeout**: Add punctuation based on pause duration

**Whisper Docker Settings:**
- **Whisper Model**: Model size (tiny, base, small, medium, large-v3)
- **Whisper Language**: Language code or auto-detect
- **Whisper Port**: API port (default: 9000)
- **Whisper Chunk Duration**: Audio processing interval (seconds)
- **Whisper Sample Rate, Channels**: Audio quality settings
- **Whisper VAD**: Voice activity detection to skip silence
- **Whisper Auto-reconnect**: Retry on API failures

**Google Cloud Speech Settings:**
- **GCS Credentials Path**: Path to service account JSON
- **GCS Project ID**: GCP project (auto-detected if empty)
- **GCS Language Code**: e.g., "en-US", "es-ES"
- **GCS Model**: chirp_3, latest_long, etc.
- **GCS Sample Rate, Channels**: Audio quality settings
- **GCS VAD**: Voice activity detection

**OpenAI Realtime Settings:**
- **OpenAI API Key**: Required for authentication
- **OpenAI Model**: gpt-4o-transcribe or gpt-4o-mini-transcribe
- **OpenAI API Version**: API version (default: 2025-08-28)
- **OpenAI Sample Rate, Channels**: Audio quality settings
- **OpenAI VAD**: Voice activity detection with threshold
- **OpenAI VAD Timing**: Prefix padding and silence duration

---

## Signal Handling & Daemon Management

Elograf runs as a foreground daemon with graceful signal handling:

```bash
# Graceful shutdown
kill $(cat ~/.config/Elograf/elograf.pid)

# Alternative: send SIGHUP
kill -HUP $(cat ~/.config/Elograf/elograf.pid)
```

**Supported signals:**
- `SIGTERM`: Stop dictation, cleanup resources, exit
- `SIGINT` (Ctrl+C): Same as SIGTERM
- `SIGHUP`: Graceful shutdown

**PID file location:** `~/.config/Elograf/elograf.pid`

---

## Technical Details

### Architecture
- **Language**: Python 3
- **GUI Framework**: Qt6 (PyQt6)
- **IPC System**: Adaptive communication layer
  - D-Bus on Linux/KDE (with KGlobalAccel for shortcuts)
  - Qt Local Sockets on other platforms

### File Locations
| Item | Path |
|------|------|
| Configuration | `~/.config/Elograf/Elograf.conf` |
| PID file | `~/.config/Elograf/elograf.pid` |
| User models | `~/.config/vosk-models` |
| System models | `/usr/share/vosk-models` |
| Translations | `/usr/share/elograf/translations` |

### State Management
The tray icon displays real-time dictation state:
- 🔵 **Loading**: Model is loading
- 🟢 **Ready**: Waiting to start
- 🔴 **Dictating**: Actively recording
- 🟡 **Suspended**: Paused, ready to resume
- ⚫ **Stopped**: Not running

---

## Architecture

### Abstract Interface Design

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

### Implementation Hierarchy

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

### Component Interaction Flow

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

### State Machine

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

### Key Classes

#### `stt_engine.py`
Abstract base classes defining the interface contract:
- **STTController**: State management and event notification
  - Provides listener registration/unregistration to prevent race conditions
  - `remove_exit_listener()` prevents old controller exit events from affecting new engines
- **STTProcessRunner**: Process lifecycle and audio handling

**Race Condition Prevention**: When refreshing engines, old controller exit handlers could fire after a new engine was created, incorrectly incrementing the failure counter for the new engine. The `remove_exit_listener()` method allows EngineManager to unregister callbacks from the old controller before creating a new one, ensuring old process exit events don't affect new engine state.

#### `stt_factory.py`
Factory functions for engine creation:
- `create_stt_engine(engine_type, **kwargs)` → (Controller, Runner)
- `get_available_engines()` → List of engine names
- `is_engine_available(engine_type)` → bool

#### Engine Implementations

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

#### `engine_manager.py`
Manages STT engine lifecycle, configuration, and failure recovery:
- **Engine Creation**: Creates engines via factory with proper listener registration
- **Refresh Logic**: Safely replaces running engines with updated configuration
  - Unregisters old controller callbacks before creating new engine
  - Prevents race conditions from late exit events
- **Failure Handling**: Implements circuit breaker pattern with fallback chain
- **Retry Logic**: Exponential backoff for transient failures
- **Timeout Protection**: Safety timer for stuck engine shutdowns

#### `tray_icon.py`
System tray interface that:
1. Loads settings
2. Creates EngineManager with appropriate configuration
3. Delegates engine lifecycle to EngineManager
4. Updates icon based on state
5. Handles user interactions

#### `settings.py`
Persistent configuration using QSettings:
- Core settings (device, shortcuts, etc.)
- Engine-specific settings (grouped by prefix)
- Load/save with defaults

### Audio Recording

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

### Text Input Simulation

All engines use the same input simulation strategy:

```python
def _default_input_simulator(text: str):
    try:
        run(["dotool", "type", text])  # Wayland
    except:
        run(["xdotool", "type", "--", text])  # X11
```

### Configuration Storage

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

---

## Development

### Running Tests
```bash
uv run pytest
```

### Project Structure
```
elograf/
├── eloGraf/                            # Main application code
│   ├── stt_engine.py                   # Abstract STT interface (ABC)
│   ├── stt_factory.py                  # Factory for creating engines
│   ├── engine_manager.py               # Engine lifecycle and failure recovery
│   ├── nerd_controller.py              # nerd-dictation implementation
│   ├── whisper_docker_controller.py    # Whisper Docker implementation
│   ├── google_cloud_speech_controller.py  # Google Cloud Speech implementation
│   ├── openai_realtime_controller.py   # OpenAI Realtime implementation
│   ├── assemblyai_realtime_controller.py  # AssemblyAI Realtime implementation
│   ├── tray_icon.py                    # System tray interface
│   ├── settings.py                     # Persistent configuration
│   ├── dialogs.py                      # Configuration dialogs
│   ├── elograf.py                      # Application entry point
│   └── ...
├── tests/                              # Test suite
│   ├── test_nerd_controller.py
│   ├── test_whisper_docker_controller.py
│   ├── test_google_cloud_speech_controller.py
│   ├── test_openai_realtime_controller.py
│   ├── test_engine_manager.py          # Engine manager tests
│   └── test_integration_workflows.py   # End-to-end integration tests
└── pyproject.toml                      # Project configuration
```

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

## License

GPL-3.0 License - See LICENSE file for details

---

## Authors

- **papoteur** - Original author
- **Pablo Caro** - Co-author (PulseAudio device selection)

---

## Links

- [GitHub Repository](https://github.com/papoteur-mga/elograf)
- [nerd-dictation](https://github.com/ideasman42/nerd-dictation)
- [Vosk Models (alphacei)](https://alphacephei.com/vosk/models)
