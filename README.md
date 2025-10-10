# Elograf

**Voice recognition utility for nerd-dictation**

Elograf is a desktop application that provides a graphical interface for launching and configuring [nerd-dictation](https://github.com/ideasman42/nerd-dictation) for voice recognition. It runs in your system tray and offers easy control over dictation through an intuitive icon and menu system.

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

## Installation

### Method 1: Using `uv` (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package and project manager that handles dependencies automatically.

**Install globally as a tool:**
```bash
uv tool install git+https://github.com/papoteur-mga/elograf
```

**For development:**
```bash
uv pip install .
```

### Method 2: Using `pip`

**System-wide (as root):**
```bash
pip install .
```

**User installation:**
```bash
pip install --user .
```

> ⚠️ **Note**: Ensure `~/.local/bin` is in your PATH for user installations.

### Requirements
- Python 3.7+
- PyQt6 (includes D-Bus support for KDE global shortcuts)
- ujson
- urllib

> ⚠️ **nerd-dictation** is not included and must be installed separately.

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
- **Audio Device**: Select microphone from available PulseAudio sources
- **Pre-command**: Run before nerd-dictation starts (e.g., `setxkbmap fr`)
- **Post-command**: Run after nerd-dictation stops
- **Sample Rate**: Recording sample rate (default: 44100 Hz)
- **Timeout**: Auto-stop after silence (0 disables)
- **Idle Time**: CPU vs responsiveness trade-off (default: 100ms)
- **Punctuation Timeout**: Add punctuation based on pause duration
- **Input Tool**: XDOTOOL (X11) or DOTOOL (Wayland)
- **Keyboard Layout**: Required for DOTOOL (e.g., 'fr', 'de', 'us')
- **Global Shortcuts**: KDE-only system-wide keyboard shortcuts

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

## Development

### Running Tests
```bash
uv run pytest
```

### Project Structure
```
elograf/
├── eloGraf/           # Main application code
│   ├── dialogs.py     # Configuration and model dialogs
│   ├── elograf.py     # Application entry point
│   ├── tray_icon.py   # System tray interface
│   └── ...
├── tests/             # Test suite
└── pyproject.toml     # Project configuration
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
