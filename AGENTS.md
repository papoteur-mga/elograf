# Project Description

EloGraf is a desktop utility written in Python that facilitates voice dictation on Linux by integrating with multiple speech recognition engines, including nerd-dictation, Whisper Docker, Google Cloud Speech, OpenAI Realtime, AssemblyAI Realtime, and Gemini Live API. The application offers a system tray, global shortcuts, and an advanced interface for configuring audio devices, pre/post commands, and engine-specific parameters for each STT engine.

## Main Capabilities
- Graphical launcher and CLI to start, stop, suspend, and resume dictation
- Model management and downloads from remote repositories
- Configuration persistence via QSettings and multilanguage support through Qt
- IPC integration (D-Bus/local sockets) to coordinate with other system components

## Technical Structure

The code is organized as a Python package with a modular architecture. Core application logic (UI, state management, etc.) is kept separate from the STT engine implementations. Each speech recognition engine is a self-contained sub-package within the `eloGraf/engines/` directory, which makes the system extensible and easy to maintain.

### Engine Module Structure

Each engine is a sub-package that adheres to a common contract:
- `controller.py`: Implements the engine-specific state machine and communication logic.
- `engine.py`: Defines the engine metadata for the `STTFactory`.
- `settings.py`: Defines a `dataclass` schema for the engine's configuration parameters with UI metadata.

### Abstract STT Interface and Base Implementations

To ensure consistency and reduce code duplication, the application relies on a set of abstract and concrete base classes.

**STT Interfaces (`stt_engine.py`)**
- `STTController`: An abstract interface that all engine controllers implement.
- `STTProcessRunner`: An abstract interface for classes that manage the engine's lifecycle.

**Controller Base Classes (`base_controller.py`)**
- `EnumStateController`: A generic base class that provides a shared implementation for controllers using a Python `Enum` for their state machine.
- `StreamingControllerBase`: Inherits from `EnumStateController` and adds shared logic for suspend/resume functionality, common to all streaming engines.

**Runner Base Class (`streaming_runner_base.py`)**
- `StreamingRunnerBase`: A crucial base class for all streaming runners. It correctly implements the main recording loop, thread management, and audio capture logic. Child runners inherit from it and only need to implement the engine-specific logic: `_initialize_connection()`, `_process_audio_chunk()`, and `_cleanup_connection()`.

**Audio Capture (`audio_recorder.py`)**
- `AudioRecorder`: Unified audio recording with pluggable backends (PyAudio and parec).
- `PyAudioBackend`: Cross-platform audio capture using PyAudio library.
- `ParecBackend`: Linux PulseAudio capture via parec subprocess, supports device selection.
- `get_audio_devices()`: Query available audio input devices for a given backend.

The AudioRecorder automatically selects the best available backend (prefers parec on Linux, falls back to PyAudio) and provides a consistent interface for all streaming engines.

### Lifecycle Management with EngineManager

`engine_manager.py` manages creation, refresh, and failure recovery:
- **Safe creation**: Disconnects timers and listeners before swapping engines
- **Circuit breaker**: Classifies failures and switches to fallback engines after repeated errors
- **Retry with exponential backoff**: Automatic retries with incremental delay
- **Refresh timeout**: Safety timer that forces shutdown if an engine refuses to stop

## Speech Recognition Engines

### 1. nerd-dictation (Default)

The nerd-dictation integration is implemented in the `eloGraf/engines/nerd/` package and provides a local, privacy-focused CLI-based speech recognition solution.

#### Architecture

nerd-dictation is an external command-line tool that EloGraf wraps and monitors. The controller parses stdout to detect state changes.

**Key Features:**
- Fully offline operation with no network requirements
- Local Vosk model processing
- Direct subprocess management
- State detection via output parsing

#### State Machine

States are detected by parsing nerd-dictation's stdout messages:

- **IDLE**: No dictation active
- **STARTING**: Process launching
- **LOADING**: "loading model" detected in output
- **READY**: "model loaded", "listening", or "ready" detected
- **DICTATING**: "dictation started" detected
- **SUSPENDED**: "suspended" detected
- **STOPPING**: Stop command sent
- **FAILED**: Non-zero exit or error

#### Process Management

Unlike other engines, nerd-dictation uses separate command invocations for control:

```bash
nerd-dictation begin         # Start dictation
nerd-dictation end           # Stop dictation
nerd-dictation suspend       # Pause
nerd-dictation resume        # Continue
```

EloGraf spawns the main process and monitors stdout, sending control commands via separate subprocess calls.

#### Requirements

- `nerd-dictation` installed separately (not included)
- Vosk model files downloaded
- PulseAudio or ALSA for audio capture

### 2. Whisper Docker

The Whisper Docker integration is implemented in the `eloGraf/engines/whisper/` package and runs OpenAI's Whisper ASR in a Docker container as a REST API service.

#### Architecture

Uses the `onerahmet/openai-whisper-asr-webservice` Docker image, which exposes a REST API at port 9000 (configurable).

**Key Features:**
- High accuracy with Whisper models (tiny, base, small, medium, large-v3)
- Automatic container lifecycle management
- Voice Activity Detection (VAD) to skip silence
- Auto-reconnect on API failures

#### Container Management

The runner automatically:
1. Checks if container exists and matches requested model
2. Stops/recreates container if model changed
3. Starts container if stopped
4. Waits for API readiness (up to 180s timeout)

```bash
docker run -d --name elograf-whisper \
  -p 9000:9000 \
  -e ASR_MODEL=base \
  -e ASR_ENGINE=openai_whisper \
  onerahmet/openai-whisper-asr-webservice:latest
```

#### Audio Processing Flow

1. **Record**: Captures audio chunks via AudioRecorder (configurable duration, default 5s)
2. **VAD Check**: Calculates RMS audio level, skips if below threshold
3. **Transcribe**: POSTs WAV file to `/asr` endpoint with parameters
4. **Simulate**: Types transcribed text using dotool/xdotool
5. **Retry**: Auto-reconnects and retries on failures (up to 3 attempts)

#### Requirements

- Docker installed and running
- Network access for initial image download (~2GB)
- AudioRecorder (parec or PyAudio) for audio recording

### 3. Google Cloud Speech-to-Text V2

The Google Cloud Speech integration is implemented in the `eloGraf/engines/google/` package and uses Google's enterprise-grade speech recognition API with gRPC streaming.

#### Architecture

Uses the `google-cloud-speech` Python library to stream audio in real-time to Google Cloud Speech-to-Text V2 API.

**Key Features:**
- Real-time streaming recognition with bidirectional gRPC
- State-of-the-art accuracy with Chirp 3 model
- Multi-language support
- Server-side processing
- Automatic project ID detection from credentials

#### Authentication

Supports Service Account Key Files and Application Default Credentials.

#### Streaming Flow

1. **Setup**: Creates SpeechClient and configures recognizer
2. **Generator**: Yields audio chunks as StreamingRecognizeRequest
3. **Stream**: Bidirectional gRPC stream processes audio in real-time
4. **Output**: Only final results are emitted and typed

#### Requirements

- Google Cloud account with Speech-to-Text API enabled
- Service account credentials JSON file
- `google-cloud-speech` Python library
- AudioRecorder (parec or PyAudio) for audio recording

### 4. OpenAI Realtime API

The OpenAI Realtime API integration is implemented in the `eloGraf/engines/openai/` package and uses a WebSocket-based communication model for real-time voice transcription.

#### Architecture

Uses WebSocket bidirectional connection to `wss://api.openai.com/v1/realtime`.

**Key Features:**
- Ultra-low latency streaming
- Server-side VAD (Voice Activity Detection)
- Configurable models (`gpt-4o-realtime-preview`, `gpt-4o-mini-realtime-preview`)
- Partial and final transcriptions

#### Audio Data Flow

1. **Capture**: Audio captured via AudioRecorder (PCM 16-bit, 16kHz, mono)
2. **Send**: Chunks of 200ms are Base64 encoded and sent as `input_audio_buffer.append` events.
3. **Transcription**: Server processes audio and sends delta fragments followed by a final completion event.
4. **Input simulation**: Transcribed text is written via dotool or xdotool.

#### Requirements

- OpenAI API key
- Internet connectivity
- `websocket-client` Python library
- AudioRecorder (parec or PyAudio) for audio recording

### 5. AssemblyAI Realtime

The AssemblyAI integration is implemented in the `eloGraf/engines/assemblyai/` package and provides another cloud-hosted, low-latency streaming engine with optional live transcript formatting.

#### Architecture

AssemblyAI exposes a secured WebSocket endpoint that accepts PCM16 audio frames and returns interim/final transcripts.

**Key Features:**
- Real-time streaming with interim and final results
- Support for multiple languages
- Easy authentication via API Key or temporary tokens

#### Requirements

- AssemblyAI API key
- Internet connectivity
- `websocket-client` Python library
- AudioRecorder (parec or PyAudio) for audio recording

### 6. Gemini Live API

The Gemini Live API integration is implemented in the `eloGraf/engines/gemini/` package and uses Google's Gemini models for real-time speech-to-text via WebSockets.

#### Architecture

Connects to the Gemini Live API using WebSockets for bidirectional audio and text streaming.

**Key Features:**
- Real-time transcription with Gemini models (e.g., `gemini-2.5-flash`)
- Server-side VAD support
- Multi-language support via BCP-47 codes
- High accuracy and low latency

#### Requirements

- Google AI API key (from AI Studio)
- Internet connectivity
- `websocket-client` Python library
- AudioRecorder (parec or PyAudio) for audio recording

## Testing

The project uses pytest for testing. Tests are located in the `tests/` directory.

### Running Tests

Run all tests:
```bash
uv run python -m pytest
```

### Test Structure

- `tests/engines/` - Engine-specific tests for each STT implementation
- `tests/test_*.py` - Core functionality tests (settings, audio, IPC, etc.)

## Translations

The application interface is available in multiple languages. The translation source files (`.ts`) are located in the `eloGraf/translations/` directory.

### Compiling Translations

To make new or updated translations visible in the application, the `.ts` source files must be compiled into the binary `.qm` format:

```bash
uv run pyside6-lrelease eloGraf/translations/*.ts
```
