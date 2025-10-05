from __future__ import annotations

from typing import Dict, List, Optional

from PyQt6.QtCore import QSettings

DEFAULT_RATE: int = 44100


class Settings:
    """Wrapper around QSettings storing Elograf preferences and models."""

    def __init__(self, backend: Optional[QSettings] = None) -> None:
        self._backend = backend or QSettings("Elograf", "Elograf")
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
        self.directClick: bool = False
        self.keyboard: str = ""
        self.beginShortcut: str = ""
        self.endShortcut: str = ""
        self.suspendShortcut: str = ""
        self.resumeShortcut: str = ""
        self.toggleShortcut: str = ""

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
        self.directClick = backend.value("DirectClick", False, type=bool)
        self.keyboard = backend.value("Keyboard", "", type=str)
        self.beginShortcut = backend.value("BeginShortcut", "", type=str)
        self.endShortcut = backend.value("EndShortcut", "", type=str)
        self.suspendShortcut = backend.value("SuspendShortcut", "", type=str)
        self.resumeShortcut = backend.value("ResumeShortcut", "", type=str)
        self.toggleShortcut = backend.value("ToggleShortcut", "", type=str)

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
