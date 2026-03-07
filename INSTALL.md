# Installation

Elograf can be installed using various methods, with `uv` being the recommended approach for modern Python environments.

## Using `uv` (Recommended)

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

## Requirements

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

## Wayland Support

For **Wayland** (including KDE Plasma Wayland), Elograf uses **dotool** instead of xdotool for text input simulation.

### Installing dotool

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

### Configuration

1. Open Elograf's **Advanced Settings**
2. Set **Input Tool** to `DOTOOL`
3. Set **Keyboard Layout** if needed (e.g., `us`, `es`, `fr`)

### Note on Permissions

dotool uses uinput to simulate keyboard input. The `sudo ./build.sh install` command automatically installs udev rules that grant necessary permissions. You may need to log out and back in for group changes to take effect.
