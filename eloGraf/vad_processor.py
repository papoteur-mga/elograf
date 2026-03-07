"""Voice Activity Detection processors with state machine."""
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional
import time


class VADResult(Enum):
    """Results from VAD processing."""
    SILENCE = auto()
    SPEECH_START = auto()
    SPEECH_ONGOING = auto()
    SPEECH_END = auto()


class VADState(Enum):
    """Internal states of VAD state machine."""
    SILENCE = auto()
    SPEECH_STARTED = auto()
    SPEECH_ONGOING = auto()
    SILENCE_DETECTED = auto()


class VADProcessor(ABC):
    """Base class for Voice Activity Detection with state machine.
    
    State Machine:
        SILENCE -> SPEECH_STARTED (prob > threshold)
        SPEECH_STARTED -> SPEECH_ONGOING (continued speech)
        SPEECH_STARTED -> SILENCE (brief noise, < min_speech_duration)
        SPEECH_ONGOING -> SILENCE_DETECTED (silence detected)
        SILENCE_DETECTED -> SPEECH_ONGOING (speech resumes)
        SILENCE_DETECTED -> SILENCE (timeout exceeded) -> emit SPEECH_END
    """
    
    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        silence_timeout_ms: int = 500,
    ):
        self._threshold = threshold
        self._min_speech = min_speech_duration_ms
        self._silence_timeout = silence_timeout_ms
        
        self._state = VADState.SILENCE
        self._speech_start_time: Optional[float] = None
        self._silence_start_time: Optional[float] = None
    
    @abstractmethod
    def _compute_vad_probability(self, audio_chunk: bytes) -> float:
        """Compute probability [0.0, 1.0] of speech in audio chunk.
        
        Args:
            audio_chunk: Raw PCM audio data (16-bit, mono)
            
        Returns:
            Probability that the chunk contains speech
        """
        pass
    
    def process(self, audio_chunk: bytes) -> VADResult:
        """Process audio chunk through state machine.
        
        Returns:
            VADResult indicating current state transition
        """
        prob = self._compute_vad_probability(audio_chunk)
        now = time.time() * 1000  # milliseconds
        
        if self._state == VADState.SILENCE:
            if prob > self._threshold:
                self._state = VADState.SPEECH_STARTED
                self._speech_start_time = now
                return VADResult.SPEECH_START
            return VADResult.SILENCE
        
        elif self._state == VADState.SPEECH_STARTED:
            if prob > self._threshold:
                self._state = VADState.SPEECH_ONGOING
                return VADResult.SPEECH_ONGOING
            else:
                # Brief silence - check if minimum speech duration met
                if now - self._speech_start_time >= self._min_speech:
                    self._state = VADState.SILENCE_DETECTED
                    self._silence_start_time = now
                    return VADResult.SPEECH_ONGOING
                else:
                    # Too short, return to silence
                    self._state = VADState.SILENCE
                    return VADResult.SILENCE
        
        elif self._state == VADState.SPEECH_ONGOING:
            if prob < self._threshold:
                self._state = VADState.SILENCE_DETECTED
                self._silence_start_time = now
            return VADResult.SPEECH_ONGOING
        
        elif self._state == VADState.SILENCE_DETECTED:
            if prob > self._threshold:
                # Speech resumes
                self._state = VADState.SPEECH_ONGOING
                return VADResult.SPEECH_ONGOING
            elif now - self._silence_start_time >= self._silence_timeout:
                # Timeout - end of speech
                self._state = VADState.SILENCE
                return VADResult.SPEECH_END
            return VADResult.SPEECH_ONGOING
        
        return VADResult.SILENCE
    
    def reset(self) -> None:
        """Reset state machine to silence."""
        self._state = VADState.SILENCE
        self._speech_start_time = None
        self._silence_start_time = None


class RMSVADProcessor(VADProcessor):
    """Simple VAD based on RMS (Root Mean Square) audio level.
    
    Fast but not very accurate. Good for testing or low-CPU environments.
    """
    
    def _compute_vad_probability(self, audio_chunk: bytes) -> float:
        """Compute speech probability from RMS level."""
        import struct
        
        if len(audio_chunk) < 2:
            return 0.0
        
        # Unpack 16-bit samples
        num_samples = len(audio_chunk) // 2
        samples = struct.unpack(f"<{num_samples}h", audio_chunk[:num_samples*2])
        
        if not samples:
            return 0.0
        
        # Calculate RMS
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        
        # Normalize to [0, 1] - 1000 is roughly "normal speech level"
        probability = min(rms / 1000.0, 1.0)
        return probability


class SileroVADProcessor(VADProcessor):
    """High-quality VAD using Silero VAD model (PyTorch-based).
    
    Requires: pip install silero torch torchaudio
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = None
        self._utils = None
        self._audio_buffer = bytearray()
        self._load_model()
    
    def _load_model(self) -> None:
        """Load Silero VAD model."""
        import torch
        import logging
        
        # Respect global log level
        is_verbose = logging.getLogger().getEffectiveLevel() <= logging.INFO
        
        # Check if model is available, if not it will be downloaded
        # snakers4/silero-vad is the official repository
        self._model, self._utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            verbose=is_verbose
        )
        self._model.eval()
    
    def _compute_vad_probability(self, audio_chunk: bytes) -> float:
        """Compute speech probability using Silero model.
        
        Silero VAD v4 requires fixed chunk sizes: 512, 1024, or 1536 samples for 16kHz.
        """
        if self._model is None:
            return 0.0
        
        import torch
        import numpy as np
        
        # Add to local buffer
        self._audio_buffer.extend(audio_chunk)
        
        # Silero VAD v4 expects 512 samples for 16000Hz
        # 512 samples * 2 bytes (int16) = 1024 bytes
        window_size_bytes = 1024 
        
        if len(self._audio_buffer) < window_size_bytes:
            return 0.0
            
        # Get the most recent window
        chunk_to_process = self._audio_buffer[-window_size_bytes:]
        # Clear buffer to avoid processing same data
        self._audio_buffer.clear()
        
        # Convert bytes to numpy array (int16 -> float32 [-1, 1])
        audio_array = np.frombuffer(chunk_to_process, dtype=np.int16)
        audio_tensor = torch.from_numpy(audio_array.astype(np.float32) / 32768.0)
        
        # Add batch dimension
        audio_tensor = audio_tensor.unsqueeze(0)
        
        with torch.no_grad():
            speech_prob = self._model(audio_tensor, 16000).item()
        
        return speech_prob

    def reset(self) -> None:
        """Reset state machine and internal buffer."""
        super().reset()
        self._audio_buffer.clear()


class WebRTCVADProcessor(VADProcessor):
    """Lightweight VAD using WebRTC VAD (no PyTorch required).
    
    Requires: pip install webrtcvad
    """
    
    def __init__(self, aggressiveness: int = 2, *args, **kwargs):
        """
        Args:
            aggressiveness: 0-3, higher = more aggressive filtering
        """
        super().__init__(*args, **kwargs)
        import webrtcvad
        self._vad = webrtcvad.Vad(aggressiveness)
    
    def _compute_vad_probability(self, audio_chunk: bytes) -> float:
        """Compute speech probability using WebRTC VAD.
        
        WebRTC VAD requires exact frame durations: 10, 20, or 30ms.
        For 16kHz: 10ms = 320 bytes, 20ms = 640 bytes, 30ms = 960 bytes.
        """
        import webrtcvad
        
        # We'll use 30ms frames (960 bytes at 16kHz)
        frame_size = 960
        sample_rate = 16000
        
        if len(audio_chunk) < frame_size:
            return 0.0
            
        # Split chunk into valid frames and count speech detections
        speech_frames = 0
        total_frames = 0
        
        for i in range(0, len(audio_chunk) - frame_size + 1, frame_size):
            frame = audio_chunk[i:i + frame_size]
            if self._vad.is_speech(frame, sample_rate):
                speech_frames += 1
            total_frames += 1
            
        if total_frames == 0:
            return 0.0
            
        # Return ratio of speech frames
        return speech_frames / total_frames
