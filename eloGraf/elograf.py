#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 08:15:47 2021

@author: papoteur
@license: GPL v3.0
"""

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from subprocess import Popen
import os
import eloGraf.elograf_rc

# Types.
from typing import (
    Tuple,
    List,
    Optional,
)

MODEL_BASE_PATH = "/usr/share/vosk-model"


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
        label = QtWidgets.QLabel(self.tr("Precommand:"))
        self.precommand = QtWidgets.QLineEdit()
        precommandlayout.addWidget(label)
        precommandlayout.addWidget(self.precommand)
        self.precommand.setText(settings.value("Precommand"))
        postcommandlayout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(postcommandlayout)
        label = QtWidgets.QLabel(self.tr("Postcommand:"))
        self.postcommand = QtWidgets.QLineEdit()
        postcommandlayout.addWidget(label)
        postcommandlayout.addWidget(self.postcommand)
        self.postcommand.setText(settings.value("Postcommand"))
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
            item = QtWidgets.QTableWidgetItem(language)
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
        layout.addWidget(buttonBox)

        # Events
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.close)
        self.customFilepicker.clicked.connect(self.selectCustom)
        self.customCB.stateChanged.connect(self.customCBchanged)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.resizeColumnsToContents()
        self.table.verticalHeader().hide()
        self.resize(
            self.table.horizontalHeader().length() + 24,
            self.precommand.sizeHint().height()
            + self.postcommand.sizeHint().height()
            + self.table.verticalHeader().length()
            + self.table.horizontalHeader().sizeHint().height()
            + buttonBox.sizeHint().height()
            + customLayout.sizeHint().height()
            + 40,
        )
        # Custom model location
        if settings.contains("Model/UseCustom"):
            if settings.value("Model/UseCustom") == "True":
                self.customCB.setCheckState(QtCore.Qt.Checked)
                if settings.contains("Model/CustomPath"):
                    self.customFilepicker.setText(settings.value("Model/CustomPath"))
            else:
                self.customFilepicker.setEnabled(False)
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
        modelName = ""
        for item in self.table.selectedItems():
            if item.text() and i == 1:
                modelname = item.text()
                break
            i += 1
        if self.precommand.text() == "":
            self.settings.remove("Precommand")
        else:
            self.settings.setValue("Precommand", self.precommand.text())
        if self.postcommand.text() == "":
            self.settings.remove("Postcommand")
        else:
            self.settings.setValue("Postcommand", self.postcommand.text())
        self.returnValue = [modelName]
        self.close()

    def cancel(self) -> None:
        self.close()

    def selectCustom(self) -> None:
        if os.path.isdir(self.customFilepicker.text()):
            path = QtCore.QUrl(QtCore.QDir(self.customFilepicker.text()))
        else:
            path = QtCore.QUrl(QtCore.QDir.homePath())
        url = QtWidgets.QFileDialog.getExistingDirectoryUrl(
            self, self.tr("Select the model path"), path
        )
        if url:
            self.settings.setValue("Model/CustomPath", url.toLocalFile())
            self.settings.setValue("Model/UseCustom", "True")
            self.customFilepicker.setText(url.toLocalFile())
        else:
            self.settings.setValue("Model/UseCustom", "False")

    def customCBchanged(self) -> None:
        if self.customCB.isChecked():
            self.customFilepicker.setEnabled(True)
            self.settings.setValue("Model/UseCustom", "True")
        else:
            self.customFilepicker.setEnabled(False)
            self.settings.setValue("Model/UseCustom", "False")


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
        if not self.nomicro:
            self.nomicro = QtGui.QIcon(":/icons/elograf/24/nomicro.png")
        self.micro = QtGui.QIcon.fromTheme("audio-input-microphone")
        if not self.micro:
            self.micro = QtGui.QIcon(":/icons/elograf/24/micro.png")
        self.setIcon(self.nomicro)
        self.activated.connect(self.commute)
        self.dictating = False

        self.settings = QtCore.QSettings("Elograf", "Elograf")

    def currentModel(self) -> str:
        model: str = ""
        if self.settings.contains("Model/name") or self.settings.contains(
            "Model/UseCustom"
        ):
            if self.settings.contains("Model/UseCustom"):
                if self.settings.value("Model/UseCustom") == "True":
                    model = self.settings.value("Model/CustomPath")
                else:
                    if self.settings.contains("Model/name"):
                        model = os.path.join(
                            MODEL_BASE_PATH, self.settings.value("Model/name")
                        )
        return model

    def exit(self) -> None:
        self.stop_dictate()
        QtCore.QCoreApplication.exit()

    def dictate(self) -> None:
        while not self.currentModel():
            dialog = ConfigPopup("", self.settings)
            dialog.exec_()
            if dialog.returnValue:
                self.setModel(dialog.returnValue[0])
        if self.settings.contains("Precommand"):
            Popen(self.settings.value("Precommand").split())
        Popen(
            [
                "nerd-dictation",
                "begin",
                f"--vosk-model-dir={self.currentModel()}",
                "--full-sentence",
                "--punctuate-from-previous-timeout=10",
            ]
        )
        self.setIcon(self.micro)

    def stop_dictate(self) -> None:
        Popen(
            [
                "nerd-dictation",
                "end",
            ]
        )
        self.setIcon(self.nomicro)
        if self.settings.contains("Postcommand"):
            Popen(self.settings.value("Postcommand").split())

    def commute(self) -> None:
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
