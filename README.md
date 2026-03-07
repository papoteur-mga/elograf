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

**Best for:** Privacy-conscious users, offline environments, no-cost operation

### 2. **Whisper Docker**
Docker container running OpenAI's Whisper ASR webservice.

**Features:**
- High accuracy transcription
- Configurable models (tiny, base, small, medium, large-v3)
- Voice Activity Detection (VAD)
- Auto-reconnect on failures

**Best for:** High accuracy offline transcription, Docker-enabled systems

### 3. **Google Cloud Speech-to-Text V2**
Google's enterprise-grade speech recognition API with gRPC streaming.

**Features:**
- Real-time streaming recognition
- State-of-the-art accuracy with Chirp 3 model
- Multi-language support

**Best for:** Enterprise applications, multi-language support, maximum accuracy

### 4. **OpenAI Realtime API**
OpenAI's GPT-4o real-time transcription via WebSocket streaming.

**Features:**
- Ultra-low latency streaming
- WebSocket bidirectional connection
- Server-side VAD with configurable thresholds

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

For detailed installation instructions, requirements, and Wayland support, please see [INSTALL.md](INSTALL.md).

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

The configuration dialog appears automatically if no model is set. Access it anytime from the tray menu. Engine-specific settings for Whisper, Google Cloud, and OpenAI are available in the **Advanced** tab.

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

For information on the system architecture, component interaction, and state machine, please see [ARCHITECTURE.md](ARCHITECTURE.md).

### State Management
The tray icon displays real-time dictation state:
- 🔵 **Loading**: Model is loading
- 🟢 **Ready**: Waiting to start
- 🔴 **Dictating**: Actively recording
- 🟡 **Suspended**: Paused, ready to resume
- ⚫ **Stopped**: Not running

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
│   ├── engines/                        # Engine implementations
│   │   ├── nerd/                       # nerd-dictation
│   │   ├── whisper/                    # Whisper Docker
│   │   ├── google/                     # Google Cloud Speech
│   │   ├── openai/                     # OpenAI Realtime
│   │   └── assemblyai/                 # AssemblyAI Realtime
│   ├── tray_icon.py                    # System tray interface
│   ├── settings.py                     # Persistent configuration
│   ├── dialogs.py                      # Configuration dialogs
│   ├── elograf.py                      # Application entry point
│   └── ...
├── tests/                              # Test suite
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
