"""Threaded inference runner using composition (not inheritance)."""
import queue
import threading
import logging
from typing import Optional, Callable

from eloGraf.inference_backend import InferenceBackend
from eloGraf.audio_pipeline import AudioPipeline
from eloGraf.text_formatter import TextFormatter
from eloGraf.stt_engine import STTController


class ThreadedInferenceRunner:
    """Runner that separates audio capture from inference using threads.
    
    Unlike StreamingRunnerBase which uses inheritance, this class uses
    composition with AudioPipeline and InferenceBackend.
    """
    
    def __init__(
        self,
        controller: STTController,
        inference_backend: InferenceBackend,
        audio_pipeline: AudioPipeline,
        text_formatter: Optional[TextFormatter] = None,
        max_queue_depth: int = 3,
    ):
        """
        Args:
            controller: STT controller for state transitions
            inference_backend: Backend for transcription
            audio_pipeline: Pipeline for audio capture and VAD
            text_formatter: Optional formatter for post-processing
            max_queue_depth: Maximum items in inference queue
        """
        self._controller = controller
        self._backend = inference_backend
        self._pipeline = audio_pipeline
        self._formatter = text_formatter
        self._max_queue = max_queue_depth
        
        # Configure audio pipeline callback
        self._pipeline.speech_callback = self._on_speech_detected
        
        # Optional callback for transcriptions (used for typing)
        self.transcription_callback: Optional[Callable[[str], None]] = None
        
        # Threading components
        self._inference_queue: queue.Queue[bytes] = queue.Queue(maxsize=max_queue_depth)
        self._stop_event = threading.Event()
        self._inference_thread: Optional[threading.Thread] = None
    
    def start(self) -> bool:
        """Start all threads.
        
        Returns:
            True if started successfully
        """
        self._stop_event.clear()
        
        # Start audio pipeline
        self._pipeline.start()
        
        # Start inference thread
        self._inference_thread = threading.Thread(
            target=self._inference_loop,
            daemon=True,
            name="InferenceThread"
        )
        self._inference_thread.start()
        
        logging.info("ThreadedInferenceRunner started")
        return True
    
    def stop(self) -> None:
        """Stop all threads and cleanup."""
        self._stop_event.set()
        
        # Stop audio pipeline
        self._pipeline.stop()
        
        # Wait for inference thread
        if self._inference_thread and self._inference_thread.is_alive():
            self._inference_thread.join(timeout=3.0)
        
        logging.info("ThreadedInferenceRunner stopped")
    
    def suspend(self) -> None:
        """Suspend audio processing."""
        self._pipeline.suspend()
    
    def resume(self) -> None:
        """Resume audio processing."""
        self._pipeline.resume()
    
    def _on_speech_detected(self, audio: bytes) -> None:
        """Callback from AudioPipeline when VAD detects end of speech.
        
        Args:
            audio: Complete audio segment to transcribe
        """
        try:
            # Try to add without blocking
            self._inference_queue.put_nowait(audio)
            self._controller.transition_to("transcribing")
        except queue.Full:
            logging.warning("Inference queue full, dropping audio segment")
            self._controller.emit_error(
                "CPU too slow - consider smaller model or faster hardware"
            )
    
    def _inference_loop(self) -> None:
        """Main loop for inference thread (consumer)."""
        logging.info("Inference thread started")
        
        while not self._stop_event.is_set():
            try:
                # Wait for audio with timeout to check stop_event periodically
                audio = self._inference_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            
            try:
                self._process_audio(audio)
            except Exception as exc:
                logging.exception("Inference failed")
                self._controller.emit_error(f"Transcription error: {exc}")
        
        logging.info("Inference thread stopped")
    
    def _process_audio(self, audio: bytes) -> None:
        """Process single audio segment.
        
        Args:
            audio: Audio bytes to transcribe
        """
        if not self._backend.is_loaded:
            logging.warning("Inference requested but model not loaded yet. Skipping segment.")
            self._controller.transition_to("ready")
            return

        # Transcribe
        text = self._backend.transcribe(audio)
        
        if not text:
            # If no text, ensure we return to a sensible state
            self._controller.transition_to("ready")
            return
        
        # Apply formatting if configured
        if self._formatter:
            text = self._formatter.format(text)
        
        # Emit result to listeners
        self._controller.emit_transcription(text)
        
        # Call internal callback (for typing)
        if self.transcription_callback:
            self.transcription_callback(text)
    
    # For testing - process one item
    def _process_one_item(self) -> None:
        """Process a single item from queue (for testing)."""
        try:
            audio = self._inference_queue.get(timeout=1.0)
            self._process_audio(audio)
        except queue.Empty:
            pass
