#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 08:15:47 2021

@author: papoteur
@license: GPL v3.0
"""

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from subprocess import Popen, run
import os
import re
import multiprocessing
import eloGraf.elograf_rc
from eloGraf.advanced import Ui_Dialog
import  nd

# Types.
from typing import (
    Tuple,
    List,
    Optional,
)

MODEL_BASE_PATH = "/usr/share/vosk-model"
DEFAULT_RATE:int = 44100


def _dictate(**kwargs):                
	nd.main_begin(**kwargs)

class Settings(QtCore.QSettings):
    def __init__(self):
        super(QtCore.QSettings, self).__init__("Elograf", "Elograf")

    def load(self):
        if self.contains("Precommand"):
            self.precommand: str = self.value("Precommand", type=str)
        else:
            self.precommand: str = ""
        if self.contains("Postcommand"):
            self.postcommand = self.value("Postcommand", type=str)
        else:
            self.postcommand: str = ""
        if self.contains("SampleRate"):
            self.sampleRate: int = self.value("SampleRate", type=int)
        else:
            self.sampleRate: int = DEFAULT_RATE
        if self.contains("Timeout"):
            self.timeout = self.value("Timeout", type=int)
        else:
            self.timeout: int = 0
        if self.contains("IdleTime"):
            self.idleTime = self.value("IdleTime", type=int)
        else:
            self.idleTime: int = 100
        if self.contains("Punctuate"):
            self.punctuate = self.value("Punctuate", type=int)
        else:
            self.punctuate: int = 0
        if self.contains("FullSentence"):
            self.fullSentence = self.value("FullSentence", type=bool)
        else:
            self.fullSentence: bool = False
        if self.contains("Digits"):
            self.digits: bool = self.value("Digits", type=bool)
        else:
            self.digits: bool = False
        if self.contains("UseSeparator"):
            self.useSeparator = self.value("UseSeparator", type=bool)
        else:
            self.useSeparator: bool = False
        if self.contains("FreeCommand"):
            self.freeCommand = self.value("FreeCommand", type=str)
        else:
            self.freeCommand: str = ""
        if self.contains("DeviceName"):
            self.deviceName = self.value("DeviceName", type=str)
        else:
            self.deviceName: str = "default"

    def save(self):
        if self.precommand == "":
            self.remove("Precommand")
        else:
            self.setValue("Precommand", self.precommand)
        if self.postcommand == "":
            self.remove("Postcommand")
        else:
            self.setValue("Postcommand", self.postcommand)
        if self.timeout == 0:
            self.remove("Timeout")
        else:
            self.setValue("Timeout", self.timeout)
        if self.sampleRate == DEFAULT_RATE:
            self.remove("SampleRate")
        else:
            self.setValue("SampleRate", self.sampleRate)
        if self.idleTime == 100:
            self.remove("IdleTime")
        else:
            self.setValue("IdleTime", self.idleTime)
        if self.punctuate == 0:
            self.remove("Punctuate")
        else:
            self.setValue("Punctuate", self.punctuate)
        self.setValue("FullSentence", int(self.fullSentence))
        self.setValue("Digits", int(self.digits))
        self.setValue("UseSeparator", int(self.useSeparator))
        if self.freeCommand == "":
            self.remove("FreeCommand")
        else:
            self.setValue("FreeCommand", self.freeCommand)
        if self.deviceName == "default":
            self.remove("DeviceName")
        else:
            self.setValue("DeviceName", self.deviceName)


class AdvancedUI(QtWidgets.QDialog):
    def __init__(self):
        super(QtWidgets.QDialog, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.timeout.valueChanged.connect(self.timeoutChanged)
        self.ui.idleTime.valueChanged.connect(self.idleChanged)
        self.ui.punctuate.valueChanged.connect(self.punctuateChanged)

    def timeoutChanged(self, num: int):
        self.ui.timeoutDisplay.setText(str(num))

    def idleChanged(self, num: int):
        self.ui.idleDisplay.setText(str(num))

    def punctuateChanged(self, num: int):
        self.ui.punctuateDisplay.setText(str(num))


class ConfigPopup(QtWidgets.QDialog):
    def __init__(
        self, currentModel: str, settings: QtCore.QSettings, parent=None
    ) -> None:
        super(ConfigPopup, self).__init__(parent)
        self.settings = settings
        self.setWindowTitle("Elograf")
        self.setWindowIcon(QtGui.QIcon(":/icons/elograf/24/micro.png"))
        layout = QtWidgets.QVBoxLayout(self)
        dirList = [
            name for name in os.listdir(MODEL_BASE_PATH) if not os.path.isfile(name)
        ]
        numberModels = len(dirList)
        self.table = QtWidgets.QTableWidget(numberModels, 5, self)
        precommandlayout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(precommandlayout)
        customLayout = QtWidgets.QHBoxLayout(self)
        self.customCB = QtWidgets.QCheckBox(self.tr("Use custom model location"))
        self.customFilepicker = QtWidgets.QPushButton(self.tr("Select directory"))
        customLayout.addWidget(self.customCB)
        customLayout.addWidget(self.customFilepicker)
        layout.addLayout(customLayout)
        layout.addWidget(self.table)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setHorizontalHeaderLabels(
            [
                self.tr("Language"),
                self.tr("Name"),
                self.tr("Description"),
                self.tr("Size"),
                self.tr("License"),
            ]
        )
        i = 0
        selectedLine = None
        for dirModel in dirList:
            descriptionPath = os.path.join(MODEL_BASE_PATH, dirModel, "description.txt")
            if os.path.isfile(descriptionPath):
                name, language, description, size, license = self.readDesc(
                    descriptionPath
                )
            else:
                name = dirModel
                language = self.tr("Not provided")
                description = self.tr("Not provided")
                size = self.tr("Not provided")
                license = self.tr("Not provided")
            item = QtWidgets.QTableWidgetItem(self.tr(language))
            self.table.setItem(i, 0, item)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            item = QtWidgets.QTableWidgetItem(name)
            self.table.setItem(i, 1, item)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            item = QtWidgets.QTableWidgetItem(description)
            self.table.setItem(i, 2, item)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            item = QtWidgets.QTableWidgetItem(size)
            self.table.setItem(i, 3, item)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            item = QtWidgets.QTableWidgetItem(license)
            self.table.setItem(i, 4, item)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            if currentModel == name:
                selectedLine = i
                self.table.setCurrentItem(item)
            i += 1
        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        advancedButton = QtWidgets.QPushButton(self.tr("Advanced"))
        buttonBox.addButton(advancedButton, QtWidgets.QDialogButtonBox.ActionRole)
        layout.addWidget(buttonBox)

        # Events
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.close)
        self.customFilepicker.clicked.connect(self.selectCustom)
        self.customCB.stateChanged.connect(self.customCBchanged)
        advancedButton.clicked.connect(self.advanced)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.resizeColumnsToContents()
        self.table.verticalHeader().hide()
        self.resize(
            self.table.horizontalHeader().length() + 24,
            +self.table.verticalHeader().length()
            + self.table.horizontalHeader().sizeHint().height()
            + buttonBox.sizeHint().height()
            + customLayout.sizeHint().height()
            + advancedButton.sizeHint().height()
            + 40,
        )
        self.settings.load()
        if settings.contains("Model/UseCustom"):
            if settings.value("Model/UseCustom", type=bool):
                self.customCB.setCheckState(QtCore.Qt.Checked)
            else:
                self.customFilepicker.setEnabled(False)
        if settings.contains("Model/CustomPath"):
            self.customFilepicker.setText(settings.value("Model/CustomPath"))
        self.returnValue: List[str] = []

    def readDesc(self, path: str) -> Tuple[str, str, str, str, str]:
        with open(path, "r") as f:
            name = f.readline().rstrip()
            language = f.readline().rstrip()
            description = f.readline().rstrip()
            size = f.readline().rstrip()
            license = f.readline().rstrip()
            return name, language, description, size, license

    def accept(self) -> None:
        i = 0
        modelName: str = ""
        for item in self.table.selectedItems():
            if item.text() and i == 1:
                modelName = item.text()
                break
            i += 1
        self.settings.save()
        if self.customCB.isChecked():
            self.settings.setValue("Model/CustomPath", self.customFilepicker.text())
            self.settings.setValue("Model/UseCustom", True)
        else:
            self.settings.setValue("Model/UseCustom", False)
        self.returnValue = [modelName]
        self.close()

    def cancel(self) -> None:
        self.close()

    def selectCustom(self) -> None:
        if os.path.isdir(self.customFilepicker.text()):
            path = self.customFilepicker.text()
        else:
            path = QtCore.QDir.homePath()
        newPath = QtWidgets.QFileDialog.getExistingDirectory(
            self, self.tr("Select the model path"), path
        )
        if newPath:
            self.settings.setValue("Model/CustomPath", newPath)
            self.settings.setValue("Model/UseCustom", True)
            self.customFilepicker.setText(newPath)
        else:
            self.settings.setValue("Model/UseCustom", False)

    def customCBchanged(self) -> None:
        if self.customCB.isChecked():
            self.customFilepicker.setEnabled(True)
            self.settings.setValue("Model/UseCustom", True)
        else:
            self.customFilepicker.setEnabled(False)
            self.settings.setValue("Model/UseCustom", False)

    def advanced(self):
        advWindow = AdvancedUI()
        advWindow.ui.precommand.setText(self.settings.precommand)
        advWindow.ui.postcommand.setText(self.settings.postcommand)
        advWindow.ui.sampleRate.setText(str(self.settings.sampleRate))
        advWindow.ui.timeout.setValue(self.settings.timeout)
        advWindow.ui.idleTime.setValue(self.settings.idleTime)
        advWindow.ui.timeoutDisplay.setText(str(self.settings.timeout))
        advWindow.ui.idleDisplay.setText(str(self.settings.idleTime))
        advWindow.ui.punctuateDisplay.setText(str(self.settings.punctuate))
        advWindow.ui.punctuate.setValue(self.settings.punctuate)
        advWindow.ui.freecommand.setText(self.settings.freeCommand)
        if self.settings.fullSentence:
            advWindow.ui.fullSentence.setChecked(True)
        if self.settings.digits:
            advWindow.ui.digits.setChecked(True)
        if self.settings.useSeparator:
            advWindow.ui.useSeparator.setChecked(True)
        advWindow.ui.deviceName.addItem(self.tr("Default"), "default")
        i = 1
        chenv = os.environ.copy()
        chenv["LC_ALL"] = "C"
        p = run(["pactl", "list", "sources"], capture_output=True, text=True, env=chenv)
        sortie = p.stdout
        for m in re.finditer(
            "Name: (?P<name>.*)\n\s*Description: (?P<description>.*)", sortie
        ):
            advWindow.ui.deviceName.addItem(m.group("description"), m.group("name"))
            if self.settings.deviceName == m.group("name"):
                advWindow.ui.deviceName.setCurrentIndex(i)
            i += 1
        rc = advWindow.exec()
        if rc:
            # Save the values
            # precommand
            self.settings.precommand = advWindow.ui.precommand.text()
            # postcommand
            self.settings.postcommand = advWindow.ui.postcommand.text()
            # samplerate
            self.settings.sampleRate = int(advWindow.ui.sampleRate.text())
            # timeout
            self.settings.timeout = advWindow.ui.timeout.value()
            # idle time
            self.settings.idleTime = advWindow.ui.idleTime.value()
            # punctuate from previous timeout
            self.settings.punctuate = advWindow.ui.punctuate.value()
            self.settings.fullSentence = advWindow.ui.fullSentence.isChecked()
            self.settings.digits = advWindow.ui.digits.isChecked()
            self.settings.useSeparator = advWindow.ui.useSeparator.isChecked()
            self.settings.deviceName = advWindow.ui.deviceName.currentData()
            self.settings.freeCommand = advWindow.ui.freecommand.text()


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon: QtGui.QIcon, parent=None) -> None:
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtWidgets.QMenu(parent)
        exitAction = menu.addAction(self.tr("Exit"))
        configAction = menu.addAction(self.tr("Configuration"))
        self.setContextMenu(menu)
        exitAction.triggered.connect(self.exit)
        configAction.triggered.connect(self.config)
        self.nomicro = QtGui.QIcon.fromTheme("microphone-sensitivity-muted")
        if self.nomicro.isNull():
            self.nomicro = QtGui.QIcon(":/icons/elograf/24/nomicro.png")
        self.micro = QtGui.QIcon.fromTheme("audio-input-microphone")
        if self.micro.isNull():
            self.micro = QtGui.QIcon(":/icons/elograf/24/micro.png")
        self.setIcon(self.nomicro)
        self.activated.connect(lambda r: self.commute(r))
        self.dictating = False

        self.settings = Settings()
        self.thread = None

    def currentModel(self) -> str:
        model: str = ""
        if self.settings.contains("Model/name") or self.settings.contains(
            "Model/UseCustom"
        ):
            if self.settings.contains("Model/UseCustom") and self.settings.value(
                "Model/UseCustom", type=bool
            ):
                model = self.settings.value("Model/CustomPath")
            elif self.settings.contains("Model/name"):
                model = self.settings.value("Model/name")
                if model != "":
                    model = os.path.join(MODEL_BASE_PATH, model)
        return model

    def exit(self) -> None:
        self.stop_dictate()
        QtCore.QCoreApplication.exit()

    def dictate(self) -> None:
        while self.currentModel() == "":
            dialog = ConfigPopup("", self.settings)
            dialog.exec_()
            if dialog.returnValue:
                self.setModel(dialog.returnValue[0])
        self.settings.load()
        if self.settings.precommand != "":
            Popen(self.settings.precommand.split())
        args:dict = {}
        if self.settings.sampleRate != DEFAULT_RATE:
            args['sample_rate']=self.settings.sampleRate
        if self.settings.timeout != 0:
            args["timeout"] = self.settings.timeout
            # idle time
        if self.settings.idleTime != 0:
            args["idle_time"] = float(self.settings.idleTime)/ 1000
        if self.settings.fullSentence:
            args["full_sentence"] = True
        if self.settings.punctuate != 0:
            args["punctuate_from_previous_timeout"] = self.settings.punctuate
        if self.settings.digits:
            args["numbers_as_digits"] = True
        if self.settings.useSeparator:
            args["numbers_use_separator"] = True
        if self.settings.deviceName != "default":
            args["pulse_device_name"] = self.settings.deviceName
        #Popen(cmd)
        args['vosk_model_dir'] = self.currentModel()
        args["output"] = "SIMULATE_INPUT"
        args['progressive'] = True
        if os.name != "posix":
            args['input_method'] = "pynput"
        self.thread = multiprocessing.Process(target=_dictate, kwargs=args)
        self.thread.start()
        self.setIcon(self.micro)
        # A timer to watch the state of the thread and update the icon 
        self.processWatch = QtCore.QTimer()
        self.processWatch.timeout.connect(self.watch)
        self.processWatch.start(3000)

    def watch(self):
        if not self.thread.is_alive():
            self.stop_dictate()
            self.dictating = False
            self.processWatch.stop()
            
    def stop_dictate(self) -> None:
        if self.thread and self.thread.is_alive():
            self.thread.terminate()
        self.setIcon(self.nomicro)
        if hasattr(self.settings, 'postcommand'):
            if self.settings.postcommand:
                Popen(self.settings.postcommand.split())

    def commute(self, reason) -> None:
        if reason != QtWidgets.QSystemTrayIcon.Context:
            if self.dictating:
                self.stop_dictate()
            else:
                self.dictate()
            self.dictating = not self.dictating

    def config(self) -> None:
        dialog = ConfigPopup(os.path.basename(self.currentModel()), self.settings)
        dialog.exec_()
        if dialog.returnValue:
            self.setModel(dialog.returnValue[0])

    def setModel(self, model: str) -> None:
        self.settings.setValue("Model/name", model)
        if self.dictating:
            self.stop_dictate()
            self.dictate()


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    # don't close application when closing setting window)
    app.setQuitOnLastWindowClosed(False)
    LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
    locale = QtCore.QLocale.system().name()
    qtTranslator = QtCore.QTranslator()
    if qtTranslator.load(
        "qt_" + locale,
        QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath),
    ):
        app.installTranslator(qtTranslator)
    appTranslator = QtCore.QTranslator()
    if appTranslator.load("elograf_" + locale, os.path.join(LOCAL_DIR, "translations")):
        app.installTranslator(appTranslator)

    w = QtWidgets.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon(":/icons/elograf/24/nomicro.png"), w)

    trayIcon.show()
    exit(app.exec_())


if __name__ == "__main__":
    main()
