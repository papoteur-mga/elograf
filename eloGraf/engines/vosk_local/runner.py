"""Runner for VoskLocal using ThreadedInferenceRunner."""
import logging
from typing import Callable, Optional, Sequence

from eloGraf.threaded_runner import ThreadedInferenceRunner
from eloGraf.audio_pipeline import AudioPipeline, AudioCapture, AudioBuffer
from eloGraf.vad_processor import SileroVADProcessor, WebRTCVADProcessor, RMSVADProcessor
from eloGraf.text_formatter import TextFormatter
from eloGraf.input_simulator import type_text

from .controller import VoskLocalController
from .settings import VoskLocalSettings
from .inference_backend import VoskInferenceBackend


class VoskLocalRunner:
    """Runner for VoskLocal engine.
    
    Uses composition with ThreadedInferenceRunner instead of inheritance.
    """
    
    def __init__(
        self,
        controller: VoskLocalController,
        settings: VoskLocalSettings,
        input_simulator: Optional[Callable[[str], None]] = None,
    ):
        self._controller = controller
        self._settings = settings
        self._input_simulator = input_simulator or type_text
        
        # Create VAD processor based on settings (handles fallbacks internally)
        vad = self._create_vad()
        
        # Create inference backend
        self._backend = VoskInferenceBackend(sample_rate=settings.sample_rate)
        
        # Create audio pipeline
        from eloGraf.audio_pipeline import AudioCapture
        self._pipeline = AudioPipeline(
            capture=AudioCapture(sample_rate=settings.sample_rate, device=settings.device, chunk_duration=0.1),
            vad=vad,
            buffer=AudioBuffer(max_duration=30.0, sample_rate=settings.sample_rate),
            speech_callback=self._on_speech_end,
            partial_callback=self._on_partial if settings.partial_results else None,
            controller=controller,
        )
        
        # Create text formatter
        formatter = TextFormatter(locale=settings.locale) if settings.text_formatting else None
        
        # Compose ThreadedInferenceRunner
        self._runner = ThreadedInferenceRunner(
            controller=controller,
            inference_backend=self._backend,
            audio_pipeline=self._pipeline,
            text_formatter=formatter,
            max_queue_depth=settings.max_queue_depth,
        )
        # Override the controller's emission to also type the text
        self._runner.transcription_callback = self._on_transcription
        self._loading = False

    def _create_vad(self):
        """Create VAD processor based on settings."""
        common_args = {
            'threshold': self._settings.vad_threshold,
            'silence_timeout_ms': self._settings.silence_timeout_ms,
        }
        
        try:
            if self._settings.vad_type == "silero":
                return SileroVADProcessor(**common_args)
            elif self._settings.vad_type == "webrtc":
                return WebRTCVADProcessor(aggressiveness=2, **common_args)
        except (ImportError, ModuleNotFoundError) as e:
            logging.error(f"Requested VAD '{self._settings.vad_type}' not available: {e}. Falling back to RMS.")
            
        return RMSVADProcessor(**common_args)
    
    def start(self, command: Sequence[str], env: Optional[dict] = None) -> bool:
        """Start the engine."""
        self._loading = True
        self._controller.transition_to("loading")
        
        # Start the runner threads (audio pipeline and inference loop)
        # Even if model is not loaded yet, they will wait or skip.
        self._runner.start()
        
        # Load the model in a background thread
        def load_async():
            try:
                logging.info("Loading Vosk model in background...")
                self._backend.load_model(
                    self._settings.model_path,
                    partial_callback=self._on_partial if self._settings.partial_results else None,
                )
                self._controller.transition_to("ready")
                logging.info("Vosk engine ready")
            except Exception as exc:
                logging.exception("Failed to load Vosk model")
                self._controller.emit_error(f"Failed to load model: {exc}")
                self._controller.fail_to_start()
            finally:
                self._loading = False

        import threading
        loading_thread = threading.Thread(target=load_async, daemon=True, name="VoskLoadThread")
        loading_thread.start()
        
        return True
    
    def stop(self) -> None:
        """Stop the engine."""
        self._runner.stop()
        if not self._loading:
            self._backend.unload_model()
        self._controller.transition_to("idle")
    
    def suspend(self) -> None:
        """Suspend dictation."""
        self._runner.suspend()
        self._controller.transition_to("suspended")
    
    def resume(self) -> None:
        """Resume dictation."""
        self._runner.resume()
        self._controller.transition_to("ready")
    
    def poll(self) -> None:
        """No-op for threaded implementation."""
        pass
    
    def is_running(self) -> bool:
        """Check if running."""
        return self._backend.is_loaded
    
    def force_stop(self) -> None:
        """Force stop."""
        self.stop()
    
    def _on_speech_end(self, audio: bytes) -> None:
        """Callback when VAD detects end of speech."""
        # Transition to ready state after a segment is finished
        self._controller.transition_to("ready")
    
    def _on_partial(self, text: str) -> None:
        """Callback for partial results."""
        # Optional: could emit signal for UI tooltip
        pass

    def _on_transcription(self, text: str) -> None:
        """Callback when a full transcription is available."""
        if text:
            self._input_simulator(text)
