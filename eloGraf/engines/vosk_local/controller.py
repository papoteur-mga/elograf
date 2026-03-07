"""Controller for VoskLocal engine."""
from enum import Enum, auto
from eloGraf.base_controller import StreamingControllerBase
from .settings import VoskLocalSettings


class VoskLocalState(Enum):
    """States for VoskLocal engine."""
    IDLE = auto()
    LOADING = auto()
    READY = auto()
    RECORDING = auto()
    TRANSCRIBING = auto()
    SUSPENDED = auto()
    FAILED = auto()


STATE_MAP = {
    "idle": VoskLocalState.IDLE,
    "loading": VoskLocalState.LOADING,
    "ready": VoskLocalState.READY,
    "recording": VoskLocalState.RECORDING,
    "transcribing": VoskLocalState.TRANSCRIBING,
    "suspended": VoskLocalState.SUSPENDED,
    "failed": VoskLocalState.FAILED,
}


class VoskLocalController(StreamingControllerBase[VoskLocalState]):
    """Controller for VoskLocal STT engine."""
    
    def __init__(self, settings: VoskLocalSettings):
        super().__init__(
            initial_state=VoskLocalState.IDLE,
            state_map=STATE_MAP,
            engine_name="VoskLocal",
        )
        self._settings = settings

    def start(self) -> None:
        """Signal that the STT process is starting."""
        self.transition_to("loading")

    def stop_requested(self) -> None:
        """Signal that a stop has been requested."""
        self.transition_to("idle")

    def handle_output(self, line: str) -> None:
        """Process a line of output from the STT engine (no-op for threaded)."""
        pass

    def handle_exit(self, return_code: int) -> None:
        """Handle process termination (no-op for threaded)."""
        self._emit_exit(return_code)
    
    def get_status_string(self) -> str:
        """Return status string for UI."""
        from pathlib import Path
        model_name = Path(self._settings.model_path).name if self._settings.model_path else "Not selected"
        return f"Vosk Local | Model: {model_name}"
    
    @property
    def dictation_status(self):
        """Return generic dictation status."""
        from eloGraf.status import DictationStatus
        
        if self.state in (VoskLocalState.LOADING,):
            return DictationStatus.INITIALIZING
        elif self.state in (VoskLocalState.READY, VoskLocalState.RECORDING, VoskLocalState.TRANSCRIBING):
            return DictationStatus.LISTENING
        elif self.state == VoskLocalState.SUSPENDED:
            return DictationStatus.SUSPENDED
        elif self.state == VoskLocalState.FAILED:
            return DictationStatus.FAILED
        else:
            return DictationStatus.IDLE
