"""Audio pipeline components: buffer, capture, and orchestration."""
import threading
import time
import logging
from typing import Optional, Callable
from collections import deque

from eloGraf.audio_recorder import AudioRecorder
from eloGraf.vad_processor import VADProcessor, VADResult
from eloGraf.stt_engine import STTController


class AudioBuffer:
    """Thread-safe circular buffer for raw audio data with time limit."""
    
    def __init__(self, max_duration: float = 30.0, sample_rate: int = 16000):
        """
        Args:
            max_duration: Maximum seconds of audio to keep
            sample_rate: Sample rate in Hz
        """
        self._sample_rate = sample_rate
        self._bytes_per_second = sample_rate * 2  # 16-bit mono
        self._max_bytes = int(max_duration * self._bytes_per_second)
        
        self._buffer = bytearray()
        self._lock = threading.Lock()
    
    def append(self, data: bytes) -> None:
        """Append audio data to buffer, dropping old data if over limit."""
        with self._lock:
            self._buffer.extend(data)
            # Drop oldest data if over limit
            if len(self._buffer) > self._max_bytes:
                excess = len(self._buffer) - self._max_bytes
                self._buffer = self._buffer[excess:]
    
    def get_slice(self, start_ms: int, end_ms: int = 0) -> bytes:
        """Extract audio slice by time in milliseconds.
        
        Args:
            start_ms: Start time (negative = from end)
            end_ms: End time (0 = end, negative = from end)
        """
        with self._lock:
            total_bytes = len(self._buffer)
            bytes_per_ms = self._bytes_per_second // 1000
            
            if start_ms < 0:
                start_byte = max(0, total_bytes + (start_ms * bytes_per_ms))
            else:
                start_byte = start_ms * bytes_per_ms
            
            if end_ms <= 0:
                end_byte = total_bytes + (end_ms * bytes_per_ms)
            else:
                end_byte = end_ms * bytes_per_ms
            
            start_byte = max(0, min(start_byte, total_bytes))
            end_byte = max(0, min(end_byte, total_bytes))
            
            return bytes(self._buffer[start_byte:end_byte])
    
    def clear(self) -> None:
        """Clear all audio data."""
        with self._lock:
            self._buffer.clear()
    
    def __len__(self) -> int:
        """Return current size in bytes."""
        with self._lock:
            return len(self._buffer)
    
    @property
    def duration_ms(self) -> int:
        """Return current duration in milliseconds."""
        with self._lock:
            return (len(self._buffer) * 1000) // self._bytes_per_second


class AudioCapture:
    """Wrapper for AudioRecorder to provide continuous capture."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        device: Optional[str] = None,
        chunk_duration: float = 0.1,
    ):
        self._sample_rate = sample_rate
        self._device = device
        self._chunk_duration = chunk_duration
        self._recorder: Optional[AudioRecorder] = None
    
    def open(self) -> None:
        """Initialize the recorder."""
        self._recorder = AudioRecorder(
            sample_rate=self._sample_rate,
            device=self._device
        )
    
    def read_chunk(self) -> bytes:
        """Read a single chunk of audio."""
        if not self._recorder:
            raise RuntimeError("Capture not opened")
        # AudioRecorder.record_chunk returns WAV, we want raw PCM
        wav_data = self._recorder.record_chunk(self._chunk_duration)
        # WAV header is 44 bytes for standard PCM
        return wav_data[44:]
    
    def close(self) -> None:
        """Close the recorder."""
        if self._recorder:
            self._recorder.close()
            self._recorder = None


class AudioPipeline:
    """Orchestrates audio capture, buffering, and VAD processing."""
    
    def __init__(
        self,
        capture: AudioCapture,
        vad: VADProcessor,
        buffer: AudioBuffer,
        speech_callback: Callable[[bytes], None],
        partial_callback: Optional[Callable[[str], None]] = None,
        controller: Optional[STTController] = None,
    ):
        self._capture = capture
        self._vad = vad
        self._buffer = buffer
        self.speech_callback = speech_callback
        self.partial_callback = partial_callback
        self._controller = controller
        
        self._stop_event = threading.Event()
        self._suspended = False
        self._thread: Optional[threading.Thread] = None
        
        # Track start of speech for extraction
        self._speech_start_ms: Optional[int] = None
    
    def start(self) -> None:
        """Start the capture thread."""
        self._stop_event.clear()
        self._capture.open()
        self._thread = threading.Thread(target=self._run, daemon=True, name="AudioPipeline")
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the capture thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._capture.close()
    
    def suspend(self) -> None:
        """Suspend processing (keep capture running but ignore audio)."""
        self._suspended = True
        self._vad.reset()
    
    def resume(self) -> None:
        """Resume processing."""
        self._suspended = False
    
    def _run(self) -> None:
        """Main loop for audio capture and VAD."""
        logging.info("AudioPipeline thread started")
        
        # Track speech timing
        speech_start_time = None
        
        while not self._stop_event.is_set():
            try:
                chunk = self._capture.read_chunk()
                if self._suspended:
                    continue
                
                # Store in buffer
                self._buffer.append(chunk)
                
                # Process VAD
                result = self._vad.process(chunk)
                
                if result == VADResult.SPEECH_START:
                    speech_start_time = time.time()
                    logging.debug("VAD: Speech started")
                    if self._controller:
                        self._controller.transition_to("recording")
                
                elif result == VADResult.SPEECH_END:
                    if speech_start_time is not None:
                        # Calculate duration of speech
                        duration_s = time.time() - speech_start_time
                        # Extract the last (duration + padding) milliseconds
                        # Using negative start_ms to be relative to the end of buffer
                        lookback_ms = int((duration_s + 0.3) * 1000) # 300ms padding
                        segment = self._buffer.get_slice(start_ms=-lookback_ms)
                        
                        logging.debug(f"VAD: Speech ended, segment length: {len(segment)} bytes")
                        self.speech_callback(segment)
                        speech_start_time = None
                
                elif result == VADResult.SPEECH_ONGOING:
                    pass
                
            except Exception as exc:
                logging.exception("Error in AudioPipeline loop")
                time.sleep(0.1)
        
        logging.info("AudioPipeline thread stopped")
