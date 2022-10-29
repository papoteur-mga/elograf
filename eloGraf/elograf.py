#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 08:15:47 2021

@author: papoteur
@license: GPL v3.0
"""

import sys
import os
import re
import ujson
import urllib.request, urllib.error
import logging
import argparse
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtCore import (
    QCoreApplication,
    QDir,
    QLibraryInfo,
    QLocale,
    QModelIndex,
    QSettings,
    QSize,
    Qt,
    QTranslator,
    QTimer,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QMenu,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSystemTrayIcon,
    QTableWidget,
    QVBoxLayout,
    QWidget,
    QTableView,
)
from subprocess import Popen, run
from zipfile import ZipFile
import eloGraf.elograf_rc  # type: ignore
import eloGraf.advanced as advanced  # type: ignore
import eloGraf.confirm as confirm  # type: ignore
import eloGraf.custom as custom  # type: ignore

# Types.
from typing import (
    Any,
    Tuple,
    List,
    Dict,
    Optional,
)

MODEL_USER_PATH = os.path.expanduser("~/.config/vosk-models")
MODEL_GLOBAL_PATH = "/opt/vosk-models"
MODEL_LIST = "model-list.json"
MODELS_URL = "https://alphacephei.com/vosk/models"

DEFAULT_RATE: int = 44100


def get_size(start_path=".") -> Tuple[float, str]:
    total_size: int = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    total: float = float(total_size)
    for unit in ("B", "Kb", "Mb", "Gb", "Tb"):
        if total < 1024:
            break
        total /= 1024
    return total, unit


class Models(QStandardItemModel):
    def __init__(self):
        QStandardItemModel.__init__(self, 0, 5)
        headers = [
            self.tr("Language"),
            self.tr("Name"),
            self.tr("Version"),
            self.tr("Size"),
            self.tr("Class"),
        ]
        i: int = 0
        for label in headers:
            self.setHeaderData(i, Qt.Horizontal, label)
            i += 1


class Settings(QSettings):
    def __init__(self):
        super(QSettings, self).__init__("Elograf", "Elograf")

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
        if self.contains("DirectClick"):
            self.directClick = self.value("DirectClick", type=bool)
        else:
            self.directClick: bool = False

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
        self.setValue("DirectClick", int(self.directClick))
        if self.freeCommand == "":
            self.remove("FreeCommand")
        else:
            self.setValue("FreeCommand", self.freeCommand)
        if self.deviceName == "default":
            self.remove("DeviceName")
        else:
            self.setValue("DeviceName", self.deviceName)


class AdvancedUI(QDialog):
    def __init__(self):
        super(QDialog, self).__init__()
        self.ui = advanced.Ui_Dialog()
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


class ConfirmDownloadUI(QDialog):
    def __init__(self, text: str) -> None:
        super(QDialog, self).__init__()
        self.ui = confirm.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.message.setText(text)


class CustomUI(QDialog):
    def __init__(self, index, settings):
        '''
        Dialog for creating or editing properties of a model
        index is set to -1 for creation, else to the index in the Models in settings
        '''
        super(QDialog, self).__init__()
        self.settings = settings
        self.ui = custom.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.filePicker.clicked.connect(self.selectCustom)
        self.index: int = index

    def selectCustom(self) -> None:
        if os.path.isdir(self.ui.filePicker.text()):
            path: str = self.ui.filePicker.text()
        else:
            path = QDir.homePath()
        newPath: str = QFileDialog.getExistingDirectory(
            self, self.tr("Select the model path"), path
        )
        if newPath:
            self.ui.filePicker.setText(newPath)
            self.ui.nameLineEdit.setText(os.path.basename(newPath))
            size, unit = get_size(newPath)
            unit = self.tr(unit)
            self.ui.sizeLineEdit.setText(f"{size:.2f} {unit}")

    def accept(self) -> None:
        name: str = self.ui.nameLineEdit.text()
        language: str = self.ui.languageLineEdit.text()
        if language == "":
            self.ui.languageLineEdit.setStyleSheet("border: 3px solid red")
            QTimer.singleShot(1000, lambda: self.ui.languageLineEdit.setStyleSheet(""))
            return
        if name == "":
            self.ui.nameLineEdit.setStyleSheet("border: 3px solid red")
            QTimer.singleShot(1000, lambda: self.ui.nameLineEdit.setStyleSheet(""))
            return
        new_path: str = self.ui.filePicker.text()
        if os.path.exists(new_path):
            logging.debug(f"Accepted ")
            n: int = self.settings.beginReadArray("Models")
            self.settings.endArray()
            self.settings.beginWriteArray("Models", n)
            if self.index == -1:
                self.index = n
            self.settings.setArrayIndex(self.index)
            self.settings.setValue("language", language)
            self.settings.setValue("name", name)
            self.settings.setValue("version", self.ui.versionLineEdit.text())
            self.settings.setValue("size", self.ui.sizeLineEdit.text())
            self.settings.setValue("type", self.ui.classLineEdit.text())
            self.settings.setValue("location", new_path)
            self.settings.endArray()
            self.close()


class DownloadPopup(QDialog):
    """
    Dialog class for displaying a list of models available on Vosk website
    and choosing one to download.
    The model can be saved in local user space or in system space.
    """
    def __init__(self, settings: QSettings, installed: List[str], parent=None) -> None:
        super(QDialog, self).__init__(parent)
        self.settings = settings
        self.setWindowTitle("Elograf")
        self.setWindowIcon(QIcon(":/icons/elograf/24/micro.png"))
        self.list = Models()
        with open(os.path.join(MODEL_USER_PATH, MODEL_LIST)) as remote_list:
            self.remote_models: Dict = ujson.loads(remote_list.read())
        for model_data in sorted(
            self.remote_models, key=lambda item: item["lang_text"]
        ):
            if (
                model_data["name"] not in [u for u in installed]
                and model_data["obsolete"] != "true"
            ):
                language_item = QStandardItem(model_data["lang_text"])
                name_item = QStandardItem(model_data["name"])
                size_item = QStandardItem(model_data["size_text"])
                version_item = QStandardItem(model_data["version"])
                class_item = QStandardItem(model_data["type"])
                self.list.appendRow(
                    [
                        language_item,
                        name_item,
                        version_item,
                        size_item,
                        class_item,
                    ]
                )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vbox = QVBoxLayout()
        self.table = QTableView()
        self.table.setModel(self.list)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.table.resizeColumnsToContents()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bar = QProgressBar()
        self.bar.setMaximum(100)
        self.bar.setMinimum(0)
        vbox.addWidget(self.bar)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Close)
        systemButton = QPushButton(self.tr("Import system wide"))
        buttonBox.addButton(systemButton, QDialogButtonBox.ActionRole)
        userButton = QPushButton(self.tr("Import in user space"))
        buttonBox.addButton(userButton, QDialogButtonBox.ActionRole)
        vbox.addWidget(buttonBox)
        systemButton.clicked.connect(self.system)
        userButton.clicked.connect(self.user)
        buttonBox.rejected.connect(self.close)

    def sizeHint(self) -> QSize:
        width = 0
        for i in range(self.list.columnCount()):
            width += self.table.columnWidth(i)
        width += self.table.verticalHeader().sizeHint().width()
        width += self.table.verticalScrollBar().sizeHint().width()
        width += self.table.frameWidth() * 2
        return QSize(width, self.height())

    def user(self):
        # Import and extract the imported model to local space
        rc, temp_file, name = self.import_model()
        if rc:
            try:
                with ZipFile(temp_file) as z:
                    z.extractall(MODEL_USER_PATH)
            except:
                logging.warning("Invalid file")
            self.register(os.path.join(MODEL_USER_PATH, name))
            self.close()

    def system(self):
        # Import and extract the imported model to system space
        rc, temp_file, name = self.import_model()
        if rc:
            while not os.path.exists(MODEL_GLOBAL_PATH):
                p = Popen(["pkexec", "mkdir", "-p", "-m=777", MODEL_GLOBAL_PATH])
                returncode = p.wait()
                if returncode != 0:
                    self.retry = ConfirmDownloadUI(
                        self.tr(
                            "The application failed to save the model. Do you want to retry?")
                    )
                    rc = self.retry.exec()
                    if not rc:
                        break
            p = Popen(["unzip", "-q", temp_file, "-d", MODEL_GLOBAL_PATH])
            returncode = p.wait()
            if returncode == 0:
                self.register(os.path.join(MODEL_GLOBAL_PATH, name))
            else:
                warning = ConfirmDownloadUI(
                    self.tr(
                        "The model can't be saved. Check for space available or credentials for {}"
                        ).format(MODEL_GLOBAL_PATH)
                )
                warning.exec()                
            self.close()

    def progress(self, n: int, size: int, total: int) -> None:
        if total is not None:
            self.bar.setValue(n * size * 100 // total)
        else:
            self.bar.setMaximum(0)
            self.bar.setValue(n)
        self.bar.repaint()
        QCoreApplication.processEvents()

    def import_model(self) -> Tuple[bool, str, str]:
        # download the selected model
        # model designated by the selected line in "table"
        selection = self.table.selectionModel().selectedRows()  # liste de QModelIndex
        if len(selection) == 0:
            logging.warning("No selected model")
            return False, "", ""
        size = self.list.data(self.list.index(selection[0].row(), 3))
        self.name = self.list.data(self.list.index(selection[0].row(), 1))
        self.confirm_dl = ConfirmDownloadUI(
            self.tr(
                "We will download the model {} of {} from {}. Do you agree?").format(
                    self.name, size, MODELS_URL
            )
        )
        rc = self.confirm_dl.exec()
        if rc:
            url = ""
            for model in self.remote_models:
                if model["name"] == self.name:
                    url = model["url"]
                    break
            if url != "":
                try:
                    temp_file, _ = urllib.request.urlretrieve(
                        url,
                        reporthook=self.progress,
                    )
                except urllib.error.URLError:
                    logging.warning("Network unavailable or bad URL")
                    return False, "", ""
                return True, temp_file, self.name
            else:
                logging.warning("The model has no url provided")
        return False, "", ""

    def register(self, location):
        # Check if the model is already registred
        n = self.settings.beginReadArray("Models")
        model_registred = False
        for i in range(0, n):
            self.settings.setArrayIndex(i)
            if self.name == self.settings.value("name"):
                model_registred = True
                break
        self.settings.endArray()
        if not model_registred:
            logging.debug(f"Registered {n}")
            selection = self.table.selectionModel().selectedRows()
            row = selection[0].row()
            self.settings.beginWriteArray("Models")
            self.settings.setArrayIndex(n)
            self.settings.setValue("language", self.list.data(self.list.index(row, 0)))
            self.settings.setValue("name", self.name)
            self.settings.setValue("version", self.list.data(self.list.index(row, 2)))
            self.settings.setValue("size", self.list.data(self.list.index(row, 3)))
            self.settings.setValue("type", self.list.data(self.list.index(row, 4)))
            self.settings.setValue("location", location)
            self.settings.endArray()


class ConfigPopup(QDialog):
    def __init__(self, currentModel: str, parent=None) -> None:
        super(ConfigPopup, self).__init__(parent)
        self.settings = Settings()
        self.currentModel = currentModel
        self.setWindowTitle("Elograf")
        self.setWindowIcon(QIcon(":/icons/elograf/24/micro.png"))
        layout = QVBoxLayout(self)
        if not os.path.exists(MODEL_USER_PATH):
            os.makedirs(MODEL_USER_PATH, exist_ok=True)
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)
        # read models data from settings
        self.list, selected = self.get_list()
        self.table.setModel(self.list)
        if selected is not None:
            self.table.selectRow(selected)
        self.interfaceCB = QCheckBox(self.tr("Active direct click on icon"))
        layout.addWidget(self.interfaceCB)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Close)
        remoteButton = QPushButton(self.tr("Import remote model"))
        buttonBox.addButton(remoteButton, QDialogButtonBox.ActionRole)
        localButton = QPushButton(self.tr("Import local model"))
        buttonBox.addButton(localButton, QDialogButtonBox.ActionRole)
        advancedButton = QPushButton(self.tr("Advanced"))
        buttonBox.addButton(advancedButton, QDialogButtonBox.ActionRole)
        layout.addWidget(buttonBox)

        # Events
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.accept)
        advancedButton.clicked.connect(self.advanced)
        localButton.clicked.connect(self.local)
        remoteButton.clicked.connect(self.remote)
        self.table.doubleClicked.connect(self.edit)
        self.interfaceCB.clicked.connect(self.interface)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.resizeColumnsToContents()
        self.table.verticalHeader().hide()
        self.button_height = buttonBox.sizeHint().height()
        self.settings.load()
        if self.settings.directClick:
            self.interfaceCB.setChecked(True)
        self.returnValue: List[str] = []

    def sizeHint(self) -> QSize:
        height = self.table.verticalHeader().length() \
            + self.table.horizontalHeader().sizeHint().height() \
            + self.button_height \
            + 40
        return QSize(self.width(), height)

    def get_single(self, i: int):
        # Provide items for the model in settings at range i
        # items are for including in model list for viewing
        self.settings.setArrayIndex(i)
        name = self.settings.value("name")
        language = self.settings.value("language")
        size = self.settings.value("size")
        type = self.settings.value("type")
        version = self.settings.value("version")
        language_item = QStandardItem(self.tr(language))
        language_item.setFlags(language_item.flags() & ~Qt.ItemIsEditable)
        name_item = QStandardItem(name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        size_item = QStandardItem(size)
        size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
        version_item = QStandardItem(version)
        version_item.setFlags(version_item.flags() & ~Qt.ItemIsEditable)
        class_item = QStandardItem(type)
        class_item.setFlags(class_item.flags() & ~Qt.ItemIsEditable)
        return language_item, name_item, size_item, version_item, class_item

    def update_list(self, selected: int) -> None:
        n = self.settings.beginReadArray("Models")
        logging.debug(f"Updating table with {n} models")
        #previous_names_list = [self.list.data(self.list.index(i, 1)) for i in range(0, n)]
        self.list.layoutAboutToBeChanged.emit()
        self.list.removeRows(0, self.list.rowCount())
        for i in range(0, n):
            language_item, name_item, size_item, version_item, class_item = self.get_single(i)
            self.list.beginInsertRows(QModelIndex(), n, n)
            self.list.appendRow(
                [
                    language_item,
                    name_item,
                    version_item,
                    size_item,
                    class_item,
                ]
            )
            self.list.endInsertRows()
        self.settings.endArray()
        self.table.resizeColumnsToContents()
        self.list.layoutChanged.emit()
        if selected is not None:
            self.table.selectRow(selected)
        
    def get_list(self):
        model_list = Models()  # type: ignore
        to_select = None
        n = self.settings.beginReadArray("Models")
        for i in range(0, n):
            language_item, name_item, size_item, version_item, class_item = self.get_single(i)
            model_list.appendRow(
                [
                    language_item,
                    name_item,
                    version_item,
                    size_item,
                    class_item,
                ]
            )
            if self.currentModel == name_item.text():
                to_select: int = i
        self.settings.endArray()
        return model_list, to_select

    def interface(self):
        if self.interfaceCB.isChecked():
            self.settings.directClick = True
        else:
            self.settings.directClick = False

    def accept(self) -> None:
        i = 0
        modelName: str = ""
        for index in self.table.selectedIndexes():
            modelName = self.list.data(self.list.index(index.row(), 1))
        self.settings.save()
        self.returnValue = [modelName]
        self.close()

    def local(self) -> None:
        dialog = CustomUI(-1, self.settings)
        rc = dialog.exec_()
        n: int = self.settings.beginReadArray("Models")
        self.settings.endArray()
        if rc:
            self.update_list(n-1)

    def remote(self) -> None:
        if not os.path.exists(os.path.join(MODEL_USER_PATH, MODEL_LIST)):
            # We have to download the model list
            self.confirm_dl = ConfirmDownloadUI(
                self.tr(
                    "We will download the list of models from {}. Do you agree?".format(
                        MODELS_URL
                    )
                )
            )
            rc = self.confirm_dl.exec()
            if rc:
                url = os.path.join(MODELS_URL, MODEL_LIST)
                try:
                    urllib.request.urlretrieve(
                        url,
                        os.path.join(MODEL_USER_PATH, MODEL_LIST),
                    )
                except urllib.error.URLError:
                    logging.warning("Network unavailable or bad URL")
                    return
            else:
                return
        installed: List[str] = []
        n: int = self.settings.beginReadArray("Models")
        model_registred = False
        for i in range(0, n):
            self.settings.setArrayIndex(i)
            installed.append(self.settings.value("name"))
        self.settings.endArray()
        dialog = DownloadPopup(self.settings, installed)
        rc = dialog.exec_()
        if rc:
            self.update_list(n-1)

    def edit(self):
        for index in self.table.selectedIndexes():
            n: int = self.settings.beginReadArray("Models")
            for i in range(0, n):
                self.settings.setArrayIndex(i)
                if self.settings.value("name") == self.list.data(self.list.index(index.row(), 1)):
                    break
            if i != n:
                logging.debug(f"Found {i} for {self.list.data(self.list.index(index.row(), 1))}")
                self.settings.setArrayIndex(i)
                dialog = CustomUI(i, self.settings)
                dialog.ui.filePicker.setText(self.settings.value('location'))
                dialog.ui.languageLineEdit.setText(self.settings.value('language'))
                dialog.ui.nameLineEdit.setText(self.settings.value('name'))
                dialog.ui.sizeLineEdit.setText(self.settings.value('size'))
                dialog.ui.classLineEdit.setText(self.settings.value('type'))
                dialog.ui.versionLineEdit.setText(self.settings.value('version'))
                self.settings.endArray()
                dialog.exec_()
            else:
                logging.debug(f"Not found index for {self.list.data(self.list.index(index.row(), 1))}")
                self.settings.endArray()
            # edit only one time, selected indexes contents all cells in the row
            break
        self.update_list(i)
        
    def advanced(self) -> None:
        # Display dialog for advanced settings
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
        i: int = 1
        chenv: Dict = os.environ.copy()
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


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, parent=None) -> None:
        QSystemTrayIcon.__init__(self, icon, parent)
        self.settings = Settings()
        menu = QMenu(parent)
        # single left click doesn't work in some environments. https://bugreports.qt.io/browse/QTBUG-55911
        # Thus by default we don't enable it, but add Start/Stop menu entries
        self.settings.load()
        if self.settings.directClick:
            self.activated.connect(lambda r: self.commute(r))
        else:
            startAction = menu.addAction(self.tr("Start dictation"))
            stopAction = menu.addAction(self.tr("Stop dictation"))
            startAction.triggered.connect(self.start)
            stopAction.triggered.connect(self.stop)
        configAction = menu.addAction(self.tr("Configuration"))
        exitAction = menu.addAction(self.tr("Exit"))
        self.setContextMenu(menu)
        exitAction.triggered.connect(self.exit)
        configAction.triggered.connect(self.config)
        self.nomicro = QIcon.fromTheme("microphone-sensitivity-muted")
        if self.nomicro.isNull():
            self.nomicro = QIcon(":/icons/elograf/24/nomicro.png")
        self.micro = QIcon.fromTheme("audio-input-microphone")
        if self.micro.isNull():
            self.micro = QIcon(":/icons/elograf/24/micro.png")
        self.setIcon(self.nomicro)
        self.dictating = False

    def currentModel(self) -> Tuple[str, str]:
        # Return the model name selected in settings and its location path
        model: str = ""
        location: str = ""
        if self.settings.contains("Model/name"):
            model = self.settings.value("Model/name")
            n = self.settings.beginReadArray("Models")
            for i in range(0, n):
                self.settings.setArrayIndex(i)
                if self.settings.value("name") == model:
                    location = self.settings.value("location")
                    break
            self.settings.endArray()
        return model, location

    def exit(self) -> None:
        self.stop_dictate()
        QCoreApplication.exit()

    def dictate(self) -> None:
        model, location = self.currentModel()
        if model == "":
            dialog = ConfigPopup("")
            dialog.exec_()
            if dialog.returnValue:
                self.setModel(dialog.returnValue[0])
                model, location = self.currentModel()
            else:
                logging.info("No model selected")
                return
        logging.debug(f"Start dictation with model {model} located in {location}")
        self.settings.load()
        if self.settings.precommand != "":
            Popen(self.settings.precommand.split())
        cmd = ["nerd-dictation", "begin"]
        if self.settings.sampleRate != DEFAULT_RATE:
            cmd.append(f"sample-rate={self.settings.sampleRate}")
        if self.settings.timeout != 0:
            cmd.append(f"--timeout={self.settings.timeout}")
            # idle time
        if self.settings.idleTime != 0:
            cmd.append(f"--idle-time={float(self.settings.idleTime)/ 1000}")
        if self.settings.fullSentence:
            cmd.append("--full-sentence")
        if self.settings.punctuate != 0:
            cmd.append(f"--punctuate-from-previous-timeout={self.settings.punctuate}")
        if self.settings.digits:
            cmd.append("--numbers-as-digits")
        if self.settings.useSeparator:
            cmd.append("--numbers-use-separator")
        if self.settings.deviceName != "default":
            cmd.append(f"--pulse-device-name={self.settings.deviceName}")
        cmd.append(f"--vosk-model-dir={location}")
        cmd.append("--output=SIMULATE_INPUT")
        cmd.append("--continuous")
        if os.name != "posix":
            cmd.append("--input-method=pynput")
        logging.debug("Starting nerd-dictation with the command {}".format(" ".join(cmd)))
        env: Dict = os.environ.copy()
        self.dictate_process = Popen(cmd, env=env)
        self.setIcon(self.micro)
        # A timer to watch the state of the process and update the icon
        self.processWatch = QTimer()
        self.processWatch.timeout.connect(self.watch)
        self.processWatch.start(3000)

    def watch(self):
        poll = self.dictate_process.poll()
        if poll != None:
            self.stop_dictate()
            self.dictating = False
            self.processWatch.stop()

    def stop_dictate(self) -> None:
        logging.debug("Stopping nerd-dictation")
        Popen(
            [
                "nerd-dictation",
                "end",
            ]
        )
        self.setIcon(self.nomicro)
        if hasattr(self.settings, "postcommand"):
            if self.settings.postcommand:
                Popen(self.settings.postcommand.split())

    def commute(self, reason) -> None:
        logging.debug(f"Commute dictation {'off' if self.dictating else 'on'}")
        if reason != QSystemTrayIcon.Context:
            if self.dictating:
                self.stop_dictate()
            else:
                self.dictate()
            self.dictating = not self.dictating

    def start(self) -> None:
        logging.debug(f"Start dictation")
        if not self.dictating:
            self.dictate()
            self.dictating = True
        else:
            print("Dictation already started")

    def stop(self) -> None:
        logging.debug(f"Stop dictation")
        self.stop_dictate()
        self.dictating = False

    def config(self) -> None:
        model, _ = self.currentModel()
        dialog = ConfigPopup(os.path.basename(model))
        dialog.exec_()
        if dialog.returnValue:
            self.setModel(dialog.returnValue[0])
        self.settings.load()
        if self.settings.directClick:
            self.activated.connect(lambda r: self.commute(r))

    def setModel(self, model: str) -> None:
        self.settings.setValue("Model/name", model)
        if self.dictating:
            logging.debug("Reload dictate process")
            self.stop_dictate()
            self.dictate()


def main() -> None:
    parser = argparse.ArgumentParser(description='Place an icon in systray to launch offline speech recognition.')
    parser.add_argument('-l', '--log', help='specify the log level ', dest="loglevel")
    args = parser.parse_args()
    if args.loglevel is not None:
        numeric_level = getattr(logging, args.loglevel.upper(), None)
    else:
        numeric_level = logging.INFO
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=numeric_level)
    app = QApplication(sys.argv)
    # don't close application when closing setting window)
    app.setQuitOnLastWindowClosed(False)
    LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
    locale = QLocale.system().name()
    qtTranslator = QTranslator()
    if qtTranslator.load(
        "qt_" + locale,
        QLibraryInfo.location(QLibraryInfo.TranslationsPath),
    ):
        app.installTranslator(qtTranslator)
    appTranslator = QTranslator()
    if appTranslator.load("elograf_" + locale, os.path.join(LOCAL_DIR, "translations")):
        app.installTranslator(appTranslator)

    w = QWidget()
    trayIcon = SystemTrayIcon(QIcon(":/icons/elograf/24/nomicro.png"), w)

    trayIcon.show()
    exit(app.exec_())


if __name__ == "__main__":
    main()
