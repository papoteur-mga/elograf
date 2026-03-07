from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional, Union

from PyQt6.QtCore import QSettings

from eloGraf.engine_plugin import normalize_engine_name, get_plugin
from eloGraf.base_settings import EngineSettings
from eloGraf.engines.nerd.settings import NerdSettings
from eloGraf.engines.whisper.settings import WhisperSettings
from eloGraf.engines.google.settings import GoogleCloudSettings
from eloGraf.engines.openai.settings import OpenAISettings
from eloGraf.engines.assemblyai.settings import AssemblyAISettings
from eloGraf.engines.gemini.settings import GeminiSettings
from eloGraf.engines.vosk_local.settings import VoskLocalSettings

DEFAULT_RATE: int = 44100


class Settings:
    """Wrapper around QSettings storing Elograf preferences and models."""

    def __init__(self, backend: Optional[QSettings] = None) -> None:
        if backend is None:
            if os.environ.get("PYTEST_CURRENT_TEST"):
                backend = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "ElografTests", "Elograf")
                backend.clear()
            else:
                backend = QSettings("Elograf", "Elograf")
        self._backend = backend
        self.models: List[Dict[str, str]] = []
        self.precommand: str = ""
        self.postcommand: str = ""
        self.sampleRate: int = DEFAULT_RATE
        self.timeout: int = 0
        self.idleTime: int = 100
        self.punctuate: int = 0
        self.fullSentence: bool = False
        self.digits: bool = False
        self.useSeparator: bool = False
        self.freeCommand: str = ""
        self.tool: str = ""
        self.env: str = ""
        self.deviceName: str = "default"
        self.directClick: bool = True
        self.keyboard: str = ""
        self.beginShortcut: str = ""
        self.endShortcut: str = ""
        self.suspendShortcut: str = ""
        self.resumeShortcut: str = ""
        self.toggleShortcut: str = ""
        self.sttEngine: str = "nerd-dictation"
        self.whisperModel: str = "base"
        self.whisperLanguage: str = ""
        self.whisperPort: int = 9000
        self.whisperChunkDuration: float = 5.0
        self.whisperSampleRate: int = 16000
        self.whisperChannels: int = 1
        self.whisperVadEnabled: bool = True
        self.whisperVadThreshold: float = 500.0
        self.whisperAutoReconnect: bool = True
        self.googleCloudCredentialsPath: str = ""
        self.googleCloudProjectId: str = ""
        self.googleCloudLanguageCode: str = "en-US"
        self.googleCloudModel: str = "chirp_3"
        self.googleCloudSampleRate: int = 16000
        self.googleCloudChannels: int = 1
        self.googleCloudVadEnabled: bool = True
        self.googleCloudVadThreshold: float = 500.0
        self.openaiApiKey: str = ""
        self.openaiModel: str = "gpt-4o-transcribe"
        self.openaiApiVersion: str = "2025-08-28"
        self.openaiSampleRate: int = 16000
        self.openaiChannels: int = 1
        self.openaiVadEnabled: bool = True
        self.openaiVadThreshold: float = 0.5
        self.openaiVadPrefixPaddingMs: int = 300
        self.openaiVadSilenceDurationMs: int = 200
        self.openaiLanguage: str = "en-US"
        self.assemblyApiKey: str = ""
        self.assemblyModel: str = "universal"
        self.assemblyLanguage: str = ""
        self.assemblySampleRate: int = 16000
        self.assemblyChannels: int = 1
        self.geminiApiKey: str = ""
        self.geminiModel: str = "gemini-2.5-flash"
        self.geminiLanguageCode: str = "en-US"
        self.geminiSampleRate: int = 16000
        self.geminiChannels: int = 1
        self.geminiVadEnabled: bool = True
        self.geminiVadThreshold: float = 500.0

        # Vosk Local settings
        self.voskModelPath: str = ""
        self.voskVadType: str = "silero"
        self.voskVadThreshold: float = 0.5
        self.voskSilenceTimeoutMs: int = 500
        self.voskSampleRate: int = 16000
        self.voskPartialResults: bool = False
        self.voskTextFormatting: bool = True
        self.voskLocale: str = "en_US"
        self.voskMaxQueueDepth: int = 3

    def load(self) -> None:
        backend = self._backend
        self.precommand = backend.value("Precommand", "", type=str)
        self.postcommand = backend.value("Postcommand", "", type=str)
        self.sampleRate = backend.value("SampleRate", DEFAULT_RATE, type=int)
        self.timeout = backend.value("Timeout", 0, type=int)
        self.idleTime = backend.value("IdleTime", 100, type=int)
        self.punctuate = backend.value("Punctuate", 0, type=int)
        self.fullSentence = backend.value("FullSentence", False, type=bool)
        self.digits = backend.value("Digits", False, type=bool)
        self.useSeparator = backend.value("UseSeparator", False, type=bool)
        self.freeCommand = backend.value("FreeCommand", "", type=str)
        self.tool = backend.value("Tool", "", type=str)
        self.env = backend.value("Env", "", type=str)
        self.deviceName = backend.value("DeviceName", "default", type=str)
        self.directClick = backend.value("DirectClick", True, type=bool)
        self.keyboard = backend.value("Keyboard", "", type=str)
        self.beginShortcut = backend.value("BeginShortcut", "", type=str)
        self.endShortcut = backend.value("EndShortcut", "", type=str)
        self.suspendShortcut = backend.value("SuspendShortcut", "", type=str)
        self.resumeShortcut = backend.value("ResumeShortcut", "", type=str)
        self.toggleShortcut = backend.value("ToggleShortcut", "", type=str)
        self.sttEngine = backend.value("STTEngine", "nerd-dictation", type=str)
        self.sttEngine = normalize_engine_name(self.sttEngine)
        self.whisperModel = backend.value("WhisperModel", "base", type=str)
        self.whisperLanguage = backend.value("WhisperLanguage", "", type=str)
        self.whisperPort = backend.value("WhisperPort", 9000, type=int)
        self.whisperChunkDuration = backend.value("WhisperChunkDuration", 5.0, type=float)
        self.whisperSampleRate = backend.value("WhisperSampleRate", 16000, type=int)
        self.whisperChannels = backend.value("WhisperChannels", 1, type=int)
        self.whisperVadEnabled = backend.value("WhisperVadEnabled", True, type=bool)
        self.whisperVadThreshold = backend.value("WhisperVadThreshold", 500.0, type=float)
        self.whisperAutoReconnect = backend.value("WhisperAutoReconnect", True, type=bool)
        self.googleCloudCredentialsPath = backend.value("GoogleCloudCredentialsPath", "", type=str)
        self.googleCloudProjectId = backend.value("GoogleCloudProjectId", "", type=str)
        self.googleCloudLanguageCode = backend.value("GoogleCloudLanguageCode", "en-US", type=str)
        self.googleCloudModel = backend.value("GoogleCloudModel", "chirp_3", type=str)
        self.googleCloudSampleRate = backend.value("GoogleCloudSampleRate", 16000, type=int)
        self.googleCloudChannels = backend.value("GoogleCloudChannels", 1, type=int)
        self.googleCloudVadEnabled = backend.value("GoogleCloudVadEnabled", True, type=bool)
        self.googleCloudVadThreshold = backend.value("GoogleCloudVadThreshold", 500.0, type=float)
        self.openaiApiKey = backend.value("OpenaiApiKey", "", type=str)
        self.openaiModel = backend.value("OpenaiModel", "gpt-4o-transcribe", type=str)
        legacy_session_models = {
            "gpt-4o-realtime-preview": "gpt-4o-transcribe",
            "gpt-4o-mini-realtime-preview": "gpt-4o-mini-transcribe",
        }
        if self.openaiModel in legacy_session_models:
            self.openaiModel = legacy_session_models[self.openaiModel]
            backend.setValue("OpenaiModel", self.openaiModel)
        self.openaiApiVersion = backend.value("OpenaiApiVersion", "2025-08-28", type=str)
        self.openaiSampleRate = backend.value("OpenaiSampleRate", 16000, type=int)
        self.openaiChannels = backend.value("OpenaiChannels", 1, type=int)
        self.openaiVadEnabled = backend.value("OpenaiVadEnabled", True, type=bool)
        self.openaiVadThreshold = backend.value("OpenaiVadThreshold", 0.5, type=float)
        self.openaiVadPrefixPaddingMs = backend.value("OpenaiVadPrefixPaddingMs", 300, type=int)
        self.openaiVadSilenceDurationMs = backend.value("OpenaiVadSilenceDurationMs", 200, type=int)
        self.openaiLanguage = backend.value("OpenaiLanguage", "en-US", type=str)
        self.assemblyApiKey = backend.value("AssemblyApiKey", "", type=str)
        self.assemblyModel = backend.value("AssemblyModel", "universal", type=str)
        self.assemblyLanguage = backend.value("AssemblyLanguage", "", type=str)
        self.assemblySampleRate = backend.value("AssemblySampleRate", 16000, type=int)
        self.assemblyChannels = backend.value("AssemblyChannels", 1, type=int)
        self.geminiApiKey = backend.value("GeminiApiKey", "", type=str)
        self.geminiModel = backend.value("GeminiModel", "gemini-2.5-flash", type=str)
        self.geminiLanguageCode = backend.value("GeminiLanguageCode", "en-US", type=str)
        self.geminiSampleRate = backend.value("GeminiSampleRate", 16000, type=int)
        self.geminiChannels = backend.value("GeminiChannels", 1, type=int)
        self.geminiVadEnabled = backend.value("GeminiVadEnabled", True, type=bool)
        self.geminiVadThreshold = backend.value("GeminiVadThreshold", 500.0, type=float)

        # Vosk Local
        self.voskModelPath = backend.value("VoskModelPath", "", type=str)
        self.voskVadType = backend.value("VoskVadType", "silero", type=str)
        self.voskVadThreshold = backend.value("VoskVadThreshold", 0.5, type=float)
        self.voskSilenceTimeoutMs = backend.value("VoskSilenceTimeoutMs", 500, type=int)
        self.voskSampleRate = backend.value("VoskSampleRate", 16000, type=int)
        self.voskPartialResults = backend.value("VoskPartialResults", False, type=bool)
        self.voskTextFormatting = backend.value("VoskTextFormatting", True, type=bool)
        self.voskLocale = backend.value("VoskLocale", "en_US", type=str)
        self.voskMaxQueueDepth = backend.value("VoskMaxQueueDepth", 3, type=int)

        self.models = []
        count = backend.beginReadArray("Models")
        for index in range(count):
            backend.setArrayIndex(index)
            entry = {
                "name": backend.value("name", ""),
                "language": backend.value("language", ""),
                "size": backend.value("size", ""),
                "type": backend.value("type", ""),
                "version": backend.value("version", ""),
                "location": backend.value("location", ""),
            }
            self.models.append(entry)
        backend.endArray()

    def save(self) -> None:
        backend = self._backend
        self._set_or_remove("Precommand", self.precommand)
        self._set_or_remove("Postcommand", self.postcommand)
        if self.timeout == 0:
            backend.remove("Timeout")
        else:
            backend.setValue("Timeout", self.timeout)
        if self.sampleRate == DEFAULT_RATE:
            backend.remove("SampleRate")
        else:
            backend.setValue("SampleRate", self.sampleRate)
        if self.idleTime == 100:
            backend.remove("IdleTime")
        else:
            backend.setValue("IdleTime", self.idleTime)
        if self.punctuate == 0:
            backend.remove("Punctuate")
        else:
            backend.setValue("Punctuate", self.punctuate)

        backend.setValue("FullSentence", int(self.fullSentence))
        backend.setValue("Digits", int(self.digits))
        backend.setValue("UseSeparator", int(self.useSeparator))
        backend.setValue("DirectClick", int(self.directClick))
        backend.setValue("Tool", self.tool)
        self._set_or_remove("FreeCommand", self.freeCommand)
        self._set_or_remove("Env", self.env)
        self._set_or_remove("Keyboard", self.keyboard)
        self._set_or_remove("BeginShortcut", self.beginShortcut)
        self._set_or_remove("EndShortcut", self.endShortcut)
        self._set_or_remove("SuspendShortcut", self.suspendShortcut)
        self._set_or_remove("ResumeShortcut", self.resumeShortcut)
        self._set_or_remove("ToggleShortcut", self.toggleShortcut)
        backend.setValue("STTEngine", self.sttEngine)
        backend.setValue("WhisperModel", self.whisperModel)
        self._set_or_remove("WhisperLanguage", self.whisperLanguage)
        if self.whisperPort == 9000:
            backend.remove("WhisperPort")
        else:
            backend.setValue("WhisperPort", self.whisperPort)
        if self.whisperChunkDuration == 5.0:
            backend.remove("WhisperChunkDuration")
        else:
            backend.setValue("WhisperChunkDuration", self.whisperChunkDuration)
        if self.whisperSampleRate == 16000:
            backend.remove("WhisperSampleRate")
        else:
            backend.setValue("WhisperSampleRate", self.whisperSampleRate)
        if self.whisperChannels == 1:
            backend.remove("WhisperChannels")
        else:
            backend.setValue("WhisperChannels", self.whisperChannels)
        backend.setValue("WhisperVadEnabled", int(self.whisperVadEnabled))
        if self.whisperVadThreshold == 500.0:
            backend.remove("WhisperVadThreshold")
        else:
            backend.setValue("WhisperVadThreshold", self.whisperVadThreshold)
        backend.setValue("WhisperAutoReconnect", int(self.whisperAutoReconnect))
        self._set_or_remove("GoogleCloudCredentialsPath", self.googleCloudCredentialsPath)
        self._set_or_remove("GoogleCloudProjectId", self.googleCloudProjectId)
        if self.googleCloudLanguageCode == "en-US":
            backend.remove("GoogleCloudLanguageCode")
        else:
            backend.setValue("GoogleCloudLanguageCode", self.googleCloudLanguageCode)
        if self.googleCloudModel == "chirp_3":
            backend.remove("GoogleCloudModel")
        else:
            backend.setValue("GoogleCloudModel", self.googleCloudModel)
        if self.googleCloudSampleRate == 16000:
            backend.remove("GoogleCloudSampleRate")
        else:
            backend.setValue("GoogleCloudSampleRate", self.googleCloudSampleRate)
        if self.googleCloudChannels == 1:
            backend.remove("GoogleCloudChannels")
        else:
            backend.setValue("GoogleCloudChannels", self.googleCloudChannels)
        backend.setValue("GoogleCloudVadEnabled", int(self.googleCloudVadEnabled))
        if self.googleCloudVadThreshold == 500.0:
            backend.remove("GoogleCloudVadThreshold")
        else:
            backend.setValue("GoogleCloudVadThreshold", self.googleCloudVadThreshold)
        self._set_or_remove("OpenaiApiKey", self.openaiApiKey)
        if self.openaiModel == "gpt-4o-transcribe":
            backend.remove("OpenaiModel")
        else:
            backend.setValue("OpenaiModel", self.openaiModel)
        if self.openaiApiVersion == "2025-08-28":
            backend.remove("OpenaiApiVersion")
        else:
            backend.setValue("OpenaiApiVersion", self.openaiApiVersion)
        if self.openaiSampleRate == 16000:
            backend.remove("OpenaiSampleRate")
        else:
            backend.setValue("OpenaiSampleRate", self.openaiSampleRate)
        if self.openaiChannels == 1:
            backend.remove("OpenaiChannels")
        else:
            backend.setValue("OpenaiChannels", self.openaiChannels)
        backend.setValue("OpenaiVadEnabled", int(self.openaiVadEnabled))
        if self.openaiVadThreshold == 0.5:
            backend.remove("OpenaiVadThreshold")
        else:
            backend.setValue("OpenaiVadThreshold", self.openaiVadThreshold)
        if self.openaiVadPrefixPaddingMs == 300:
            backend.remove("OpenaiVadPrefixPaddingMs")
        else:
            backend.setValue("OpenaiVadPrefixPaddingMs", self.openaiVadPrefixPaddingMs)
        if self.openaiVadSilenceDurationMs == 200:
            backend.remove("OpenaiVadSilenceDurationMs")
        else:
            backend.setValue("OpenaiVadSilenceDurationMs", self.openaiVadSilenceDurationMs)
        if self.openaiLanguage == "en-US":
            backend.remove("OpenaiLanguage")
        else:
            backend.setValue("OpenaiLanguage", self.openaiLanguage)
        self._set_or_remove("AssemblyApiKey", self.assemblyApiKey)
        if self.assemblyModel == "universal":
            backend.remove("AssemblyModel")
        else:
            backend.setValue("AssemblyModel", self.assemblyModel)
        self._set_or_remove("AssemblyLanguage", self.assemblyLanguage)
        if self.assemblySampleRate == 16000:
            backend.remove("AssemblySampleRate")
        else:
            backend.setValue("AssemblySampleRate", self.assemblySampleRate)
        if self.assemblyChannels == 1:
            backend.remove("AssemblyChannels")
        else:
            backend.setValue("AssemblyChannels", self.assemblyChannels)
        self._set_or_remove("GeminiApiKey", self.geminiApiKey)
        if self.geminiModel == "gemini-2.5-flash":
            backend.remove("GeminiModel")
        else:
            backend.setValue("GeminiModel", self.geminiModel)
        if self.geminiLanguageCode == "en-US":
            backend.remove("GeminiLanguageCode")
        else:
            backend.setValue("GeminiLanguageCode", self.geminiLanguageCode)
        if self.geminiSampleRate == 16000:
            backend.remove("GeminiSampleRate")
        else:
            backend.setValue("GeminiSampleRate", self.geminiSampleRate)
        if self.geminiChannels == 1:
            backend.remove("GeminiChannels")
        else:
            backend.setValue("GeminiChannels", self.geminiChannels)
        backend.setValue("GeminiVadEnabled", int(self.geminiVadEnabled))
        if self.geminiVadThreshold == 500.0:
            backend.remove("GeminiVadThreshold")
        else:
            backend.setValue("GeminiVadThreshold", self.geminiVadThreshold)

        # Vosk Local
        self._set_or_remove("VoskModelPath", self.voskModelPath)
        if self.voskVadType == "silero":
            backend.remove("VoskVadType")
        else:
            backend.setValue("VoskVadType", self.voskVadType)
        if self.voskVadThreshold == 0.5:
            backend.remove("VoskVadThreshold")
        else:
            backend.setValue("VoskVadThreshold", self.voskVadThreshold)
        if self.voskSilenceTimeoutMs == 500:
            backend.remove("VoskSilenceTimeoutMs")
        else:
            backend.setValue("VoskSilenceTimeoutMs", self.voskSilenceTimeoutMs)
        if self.voskSampleRate == 16000:
            backend.remove("VoskSampleRate")
        else:
            backend.setValue("VoskSampleRate", self.voskSampleRate)
        backend.setValue("VoskPartialResults", int(self.voskPartialResults))
        backend.setValue("VoskTextFormatting", int(self.voskTextFormatting))
        if self.voskLocale == "en_US":
            backend.remove("VoskLocale")
        else:
            backend.setValue("VoskLocale", self.voskLocale)
        if self.voskMaxQueueDepth == 3:
            backend.remove("VoskMaxQueueDepth")
        else:
            backend.setValue("VoskMaxQueueDepth", self.voskMaxQueueDepth)

        if self.deviceName == "default":
            backend.remove("DeviceName")
        else:
            backend.setValue("DeviceName", self.deviceName)

    def add_model(self, language, name, version, size, mclass, location) -> None:
        entry = {
            "name": name,
            "language": language,
            "size": size,
            "type": mclass,
            "version": version,
            "location": location,
        }
        self.models.append(entry)
        self.write_models()

    def remove_model(self, index) -> None:
        del self.models[index]
        self.write_models()

    def write_models(self) -> None:
        backend = self._backend
        count = backend.beginReadArray("Models")
        backend.endArray()
        backend.beginWriteArray("Models")
        for idx in range(count):
            backend.setArrayIndex(idx)
            backend.remove(str(idx))
        backend.endArray()

        backend.beginWriteArray("Models")
        for idx, model in enumerate(self.models):
            backend.setArrayIndex(idx)
            backend.setValue("language", model.get("language", ""))
            backend.setValue("name", model.get("name", ""))
            backend.setValue("version", model.get("version", ""))
            backend.setValue("size", model.get("size", ""))
            backend.setValue("type", model.get("type", ""))
            backend.setValue("location", model.get("location", ""))
        backend.endArray()
        backend.sync()

    def setValue(self, key: str, value) -> None:  # noqa: N802 - Qt naming
        self._backend.setValue(key, value)

    def value(self, key: str, default=None, type=None):  # noqa: N802
        if type is None:
            return self._backend.value(key, default)
        return self._backend.value(key, default, type=type)

    def contains(self, key: str) -> bool:  # noqa: N802
        return self._backend.contains(key)

    def remove(self, key: str) -> None:  # noqa: N802
        self._backend.remove(key)

    def beginReadArray(self, prefix: str) -> int:  # noqa: N802
        return self._backend.beginReadArray(prefix)

    def beginWriteArray(self, prefix: str) -> None:  # noqa: N802
        self._backend.beginWriteArray(prefix)

    def endArray(self) -> None:  # noqa: N802
        self._backend.endArray()

    def setArrayIndex(self, index: int) -> None:  # noqa: N802
        self._backend.setArrayIndex(index)

    def _set_or_remove(self, key: str, value: str) -> None:
        backend = self._backend
        if value:
            backend.setValue(key, value)
        else:
            backend.remove(key)

    def current_model(self):
        name = ""
        location = ""
        if self.contains("Model/name"):
            name = self.value("Model/name")
            for entry in self.models:
                if entry.get("name") == name:
                    location = entry.get("location", "")
                    break
        if not location:
            for entry in self.models:
                loc = entry.get("location", "")
                if loc:
                    name = entry.get("name", name)
                    location = loc
                    break
        return name, location

    def get_engine_settings(
        self, engine_type: Optional[str] = None
    ) -> Union[NerdSettings, WhisperSettings, GoogleCloudSettings, OpenAISettings, AssemblyAISettings, GeminiSettings, VoskLocalSettings, EngineSettings]:
        """
        Get type-safe engine settings dataclass for the requested engine.

        Args:
            engine_type: Optional override; defaults to current ``sttEngine``.

        Returns:
            Dataclass instance with validated settings for the engine.
        """
        requested_type = engine_type or self.sttEngine
        canonical_type = normalize_engine_name(requested_type)

        if canonical_type == "nerd-dictation":
            _, model_location = self.current_model()
            return NerdSettings(
                engine_type=canonical_type,
                device_name=self.deviceName,
                sample_rate=self.sampleRate,
                timeout=self.timeout,
                idle_time=self.idleTime,
                punctuate_timeout=self.punctuate,
                full_sentence=self.fullSentence,
                digits=self.digits,
                use_separator=self.useSeparator,
                free_command=self.freeCommand,
                model_path=model_location,
            )
        if canonical_type == "whisper-docker":
            return WhisperSettings(
                engine_type=canonical_type,
                device_name=self.deviceName,
                model=self.whisperModel,
                port=self.whisperPort,
                language=self.whisperLanguage or None,
                chunk_duration=self.whisperChunkDuration,
                sample_rate=self.whisperSampleRate,
                channels=self.whisperChannels,
                vad_enabled=self.whisperVadEnabled,
                vad_threshold=self.whisperVadThreshold,
                auto_reconnect=self.whisperAutoReconnect,
            )
        if canonical_type == "google-cloud-speech":
            return GoogleCloudSettings(
                engine_type=canonical_type,
                device_name=self.deviceName,
                credentials_path=self.googleCloudCredentialsPath,
                project_id=self.googleCloudProjectId,
                language_code=self.googleCloudLanguageCode,
                model=self.googleCloudModel,
                sample_rate=self.googleCloudSampleRate,
                channels=self.googleCloudChannels,
                vad_enabled=self.googleCloudVadEnabled,
                vad_threshold=self.googleCloudVadThreshold,
            )
        if canonical_type == "openai-realtime":
            return OpenAISettings(
                engine_type=canonical_type,
                device_name=self.deviceName,
                api_key=self.openaiApiKey,
                model=self.openaiModel,
                api_version=self.openaiApiVersion,
                sample_rate=self.openaiSampleRate,
                channels=self.openaiChannels,
                vad_enabled=self.openaiVadEnabled,
                vad_threshold=self.openaiVadThreshold,
                vad_prefix_padding_ms=self.openaiVadPrefixPaddingMs,
                vad_silence_duration_ms=self.openaiVadSilenceDurationMs,
                language=self.openaiLanguage,
            )
        if canonical_type == "assemblyai":
            return AssemblyAISettings(
                engine_type=canonical_type,
                device_name=self.deviceName,
                api_key=self.assemblyApiKey,
                model=self.assemblyModel,
                language=self.assemblyLanguage,
                sample_rate=self.assemblySampleRate,
                channels=self.assemblyChannels,
            )
        if canonical_type == "gemini-live":
            return GeminiSettings(
                engine_type=canonical_type,
                device_name=self.deviceName,
                api_key=self.geminiApiKey,
                model=self.geminiModel,
                language_code=self.geminiLanguageCode,
                sample_rate=self.geminiSampleRate,
                channels=self.geminiChannels,
                vad_enabled=self.geminiVadEnabled,
                vad_threshold=self.geminiVadThreshold,
            )
        if canonical_type == "vosk-local":
            return VoskLocalSettings(
                engine_type=canonical_type,
                device_name=self.deviceName,
                model_path=self.voskModelPath,
                sample_rate=self.voskSampleRate,
                device=None,  # Uses deviceName from Settings
                vad_threshold=self.voskVadThreshold,
                vad_type=self.voskVadType,
                silence_timeout_ms=self.voskSilenceTimeoutMs,
                partial_results=self.voskPartialResults,
                text_formatting=self.voskTextFormatting,
                locale=self.voskLocale,
                max_queue_depth=self.voskMaxQueueDepth,
            )
        return EngineSettings(
            engine_type=canonical_type,
            device_name=self.deviceName,
        )

    def update_from_dataclass(
        self, engine_settings: Union[NerdSettings, WhisperSettings, GoogleCloudSettings, OpenAISettings, AssemblyAISettings, GeminiSettings, VoskLocalSettings]
    ) -> None:
        """
        Update settings from a dataclass instance via its plugin.

        Args:
            engine_settings: Validated engine settings dataclass.
        """
        plugin = get_plugin(engine_settings.engine_type)
        plugin.apply_to_settings(self, engine_settings)
