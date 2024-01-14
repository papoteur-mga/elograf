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
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem, QInputMethod
from PyQt6.QtCore import (
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
from PyQt6.QtWidgets import (
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
            self.setHeaderData(i, Qt.Orientation.Horizontal, label)
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
        if self.contains("Tool"):
            self.tool = self.value("Tool", type=str)
        else:
            self.tool: str = ""
        if self.contains("Env"):
            self.env = self.value("Env", type=str)
        else:
            self.env: str = ""
        if self.contains("DeviceName"):
            self.deviceName = self.value("DeviceName", type=str)
        else:
            self.deviceName: str = "default"
        if self.contains("DirectClick"):
            self.directClick = self.value("DirectClick", type=bool)
        else:
            self.directClick: bool = False
        if self.contains("Keyboard"):
            self.keyboard = self.value("Keyboard", type=str)
        else:
            self.keyboard: str = ""
        self.models = []
        to_select = None
        n = self.beginReadArray("Models")
        for i in range(0, n):
            self.setArrayIndex(i)
            entry = {}
            entry["name"] = self.value("name")
            entry["language"] = self.value("language")
            entry["size"] = self.value("size")
            entry["type"] = self.value("type")
            entry["version"] = self.value("version")
            entry["location"] = self.value("location")
            self.models.append(entry)
        self.endArray()

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
        self.setValue("Tool",self.tool)
        if self.freeCommand == "":
            self.remove("FreeCommand")
        else:
            self.setValue("FreeCommand", self.freeCommand)
        if self.env == "":
            self.remove("Env")
        else:
            self.setValue("Env", self.env)
        if self.keyboard == "":
            self.remove("Keyboard")
        else:
            self.setValue("Keyboard", self.keyboard)
        if self.deviceName == "default":
            self.remove("DeviceName")
        else:
            self.setValue("DeviceName", self.deviceName)

    def add_model(self, language, name, version, size, mclass, location):
        entry = {}
        entry["name"] = name
        entry["language"] = language
        entry["size"] = size
        entry["type"] = mclass
        entry["version"] = version
        entry["location"] = location
        self.models.append(entry)
        self.write_models()

    def remove_model(self, index):
        del self.models[index]
        self.write_models()

    def write_models(self):
        # clean config file
        n = self.beginReadArray("Models")
        self.endArray()
        self.beginWriteArray("Models")
        for i in range(0, n):
            self.setArrayIndex(i)
            self.remove(str(i))
        self.endArray()
        # write the list
        n = len(self.models)
        self.beginWriteArray("Models")
        for i in range(0, n):
            self.setArrayIndex(i)
            self.setValue("language", self.models[i]["language"])
            self.setValue("name", self.models[i]["name"])
            self.setValue("version", self.models[i]["version"])
            self.setValue("size", self.models[i]["size"])
            self.setValue("type", self.models[i]["type"])
            self.setValue("location", self.models[i]["location"])
        self.endArray()


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
        """
        Dialog for creating or editing properties of a model
        index is set to -1 for creation, else to the index in the Models in settings
        """
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
            if self.index == -1:
                self.settings.add_model(
                    language,
                    name,
                    self.ui.versionLineEdit.text(),
                    self.ui.sizeLineEdit.text(),
                    self.ui.classLineEdit.text(),
                    new_path,
                )
                self.index = len(self.settings.models)
            else:
                # update existing values
                self.settings.models[self.index]["language"] = language
                self.settings.models[self.index]["name"] = name
                self.settings.models[self.index][
                    "version"
                ] = self.ui.versionLineEdit.text()
                self.settings.models[self.index]["size"] = self.ui.sizeLineEdit.text()
                self.settings.models[self.index]["type"] = self.ui.classLineEdit.text()
                self.settings.models[self.index]["location"] = new_path
            self.done(self.index)


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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        vbox = QVBoxLayout()
        self.table = QTableView()
        self.table.setModel(self.list)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.table.resizeColumnsToContents()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.bar = QProgressBar()
        self.bar.setMaximum(100)
        self.bar.setMinimum(0)
        vbox.addWidget(self.bar)
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        systemButton = QPushButton(self.tr("Import system wide"))
        buttonBox.addButton(systemButton, QDialogButtonBox.ButtonRole.ActionRole)
        userButton = QPushButton(self.tr("Import in user space"))
        buttonBox.addButton(userButton, QDialogButtonBox.ButtonRole.ActionRole)
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
            self.done(1)

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
                            "The application failed to save the model. Do you want to retry?"
                        )
                    )
                    rc = self.retry.exec()
                    if not rc:
                        break
            try:
                with ZipFile(temp_file) as z:
                    z.extractall(MODEL_GLOBAL_PATH)
                    self.register(os.path.join(MODEL_GLOBAL_PATH, name))
            except:
                warning = ConfirmDownloadUI(
                    self.tr(
                        "The model can't be saved. Check for space available or credentials for {}"
                    ).format(MODEL_GLOBAL_PATH)
                )
                warning.exec()
            self.done(1)

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
                "We will download the model {} of {} from {}. Do you agree?"
            ).format(self.name, size, MODELS_URL)
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
        # Check if the model is already registred, based on the name
        n = len(self.settings.models)
        model_registred = False
        for i in range(0, n):
            if self.name == self.settings.models[i]["name"]:
                model_registred = True
                break
        if not model_registred:
            logging.debug(f"Registered {n + 1}")
            selection = self.table.selectionModel().selectedRows()
            row = selection[0].row()
            newmodel = {}
            self.settings.add_model(
                self.list.data(self.list.index(row, 0)),
                self.name,
                self.list.data(self.list.index(row, 2)),
                self.list.data(self.list.index(row, 3)),
                self.list.data(self.list.index(row, 4)),
                location,
            )


class ConfigPopup(QDialog):
    def __init__(self, currentModel: str, parent=None) -> None:
        super(ConfigPopup, self).__init__(parent)
        self.settings = Settings()
        self.currentModel = currentModel
        import importlib.metadata

        self.setWindowTitle("Elograf " + importlib.metadata.version("eloGraf"))
        self.setWindowIcon(QIcon(":/icons/elograf/24/micro.png"))
        layout = QVBoxLayout(self)
        if not os.path.exists(MODEL_USER_PATH):
            os.makedirs(MODEL_USER_PATH, exist_ok=True)
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.table)
        # read models data from settings
        self.settings.load()
        self.list, selected = self.get_list()
        self.table.setModel(self.list)
        if selected is not None:
            self.table.selectRow(selected)
        self.interfaceCB = QCheckBox(self.tr("Active direct click on icon"))
        layout.addWidget(self.interfaceCB)
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        remoteButton = QPushButton(self.tr("Import remote model"))
        buttonBox.addButton(remoteButton, QDialogButtonBox.ButtonRole.ActionRole)
        localButton = QPushButton(self.tr("Import local model"))
        buttonBox.addButton(localButton, QDialogButtonBox.ButtonRole.ActionRole)
        advancedButton = QPushButton(self.tr("Advanced"))
        buttonBox.addButton(advancedButton, QDialogButtonBox.ButtonRole.ActionRole)
        layout.addWidget(buttonBox)

        # Events
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.accept)
        advancedButton.clicked.connect(self.advanced)
        localButton.clicked.connect(self.local)
        remoteButton.clicked.connect(self.remote)
        self.table.doubleClicked.connect(self.edit)
        self.interfaceCB.clicked.connect(self.interface)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.resizeColumnsToContents()
        self.table.verticalHeader().hide()
        self.button_height = buttonBox.sizeHint().height()
        if self.settings.directClick:
            self.interfaceCB.setChecked(True)
        self.returnValue: List[str] = []

    def sizeHint(self) -> QSize:
        height = (
            self.table.verticalHeader().length()
            + self.table.horizontalHeader().sizeHint().height()
            + self.button_height
            + self.interfaceCB.height()
            + 40
        )
        return QSize(self.width(), height)

    def get_single(self, i: int):
        # Provide items for the model in settings at range i
        # items are for including in model list for viewing
        name = self.settings.models[i]["name"]
        language = self.settings.models[i]["language"]
        size = self.settings.models[i]["size"]
        mclass = self.settings.models[i]["type"]
        version = self.settings.models[i]["version"]
        language_item = QStandardItem(self.tr(language))
        language_item.setFlags(language_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        name_item = QStandardItem(name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        size_item = QStandardItem(size)
        size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        version_item = QStandardItem(version)
        version_item.setFlags(version_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        class_item = QStandardItem(mclass)
        class_item.setFlags(class_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return language_item, name_item, size_item, version_item, class_item

    def update_list(self, selected: int) -> None:
        n = len(self.settings.models)
        logging.debug(f"Updating table with {n} models")
        # previous_names_list = [self.list.data(self.list.index(i, 1)) for i in range(0, n)]
        self.list.layoutAboutToBeChanged.emit()
        self.list.removeRows(0, self.list.rowCount())
        for i in range(0, n):
            (
                language_item,
                name_item,
                size_item,
                version_item,
                class_item,
            ) = self.get_single(i)
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
        self.table.resizeColumnsToContents()
        self.list.layoutChanged.emit()
        if selected is not None:
            self.table.selectRow(selected)

    def get_list(self):
        model_list = Models()  # type: ignore
        to_select = None
        n = len(self.settings.models)
        for i in range(0, n):
            (
                language_item,
                name_item,
                size_item,
                version_item,
                class_item,
            ) = self.get_single(i)
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
        # rc contents the index of the edited or newly created model
        rc: int = dialog.exec()
        if rc:
            logging.debug(f"Model updated {rc}")
            self.update_list(rc - 1)

    def remote(self) -> None:
        if not os.path.exists(os.path.join(MODEL_USER_PATH, MODEL_LIST)):
            # We have to download the model list
            self.confirm_dl = ConfirmDownloadUI(
                self.tr(
                    "We will download the list of models from {}.\nDo you agree?".format(
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
        n: int = len(self.settings.models)
        model_registred = False
        for i in range(0, n):
            installed.append(self.settings.models[i]["name"])
        dialog = DownloadPopup(self.settings, installed)
        rc = dialog.exec()
        if rc:
            n = len(self.settings.models)
            self.update_list(n - 1)

    def edit(self):
        for index in self.table.selectedIndexes():
            n: int = len(self.settings.models)
            for i in range(0, n):
                if self.settings.models[i]["name"] == self.list.data(
                    self.list.index(index.row(), 1)
                ):
                    break
            if i != n:
                logging.debug(
                    f"Found {i} for {self.list.data(self.list.index(index.row(), 1))}"
                )
                dialog = CustomUI(i, self.settings)
                dialog.ui.filePicker.setText(self.settings.models[i]["location"])
                dialog.ui.languageLineEdit.setText(self.settings.models[i]["language"])
                dialog.ui.nameLineEdit.setText(self.settings.models[i]["name"])
                dialog.ui.sizeLineEdit.setText(self.settings.models[i]["size"])
                dialog.ui.classLineEdit.setText(self.settings.models[i]["type"])
                dialog.ui.versionLineEdit.setText(self.settings.models[i]["version"])
                dialog.exec()
            else:
                logging.debug(
                    f"Not found index for {self.list.data(self.list.index(index.row(), 1))}"
                )
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
        advWindow.ui.env.setText(self.settings.env)
        advWindow.ui.keyboard_le.setText(self.settings.keyboard)
        advWindow.ui.tool_cb.setCurrentIndex(advWindow.ui.tool_cb.findText(self.settings.tool))
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
            self.settings.env = advWindow.ui.env.text()
            self.settings.keyboard = advWindow.ui.keyboard_le.text()
            self.settings.tool = advWindow.ui.tool_cb.currentText()



class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon,  start: bool, parent=None) -> None:
        QSystemTrayIcon.__init__(self, icon, parent)
        self.settings = Settings()
        menu = QMenu(parent)
        # single left click doesn't work in some environments. https://bugreports.qt.io/browse/QTBUG-55911
        # Thus by default we don't enable it, but add Start/Stop menu entries
        self.settings.load()
        if not self.settings.directClick:
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
        self.activated.connect(lambda r: self.commute(r))
        if start:
            self.dictate()

    def currentModel(self) -> Tuple[str, str]:
        # Return the model name selected in settings and its location path
        model: str = ""
        location: str = ""
        if self.settings.contains("Model/name"):
            model = self.settings.value("Model/name")
            n = len(self.settings.models)
            for i in range(0, n):
                if self.settings.models[i]["name"] == model:
                    location = self.settings.models[i]["location"]
                    break
        return model, location

    def exit(self) -> None:
        if self.dictating:
            self.stop_dictate()
        QCoreApplication.exit()

    def dictate(self) -> None:
        model, location = self.currentModel()
        if model == "":
            dialog = ConfigPopup("")
            dialog.exec()
            logging.info(f"Return {dialog.returnValue} with {dialog.returnValue[0]}.")
            if dialog.returnValue and dialog.returnValue[0] != "":
                self.settings.setValue("Model/name", dialog.returnValue[0])
                model, location = self.currentModel()
            else:
                logging.info("No model selected")
                self.dictating = False
                return
        logging.debug(f"Start dictation with model {model} located in {location}")
        kb_lang, _ = QApplication.inputMethod().locale().name().split("_")
        self.settings.load()
        if self.settings.precommand != "":
            cmd = self.settings.precommand.split()
            if len(cmd) != 0:
                Popen(cmd)
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
        if self.settings.freeCommand != "":
            cmd.append(self.settings.freeCommand)
        env: Dict = os.environ.copy()
        if self.settings.env != "":
            try:
                for variable in self.settings.env.split(" "):
                    key, value = variable.split("=")
                    env[key] = value
            except:
                logging.warn("Environment variables should be in the form key1=value1 key2=value2")
        if self.settings.tool == "DOTOOL":
            if self.settings.keyboard != "":
                env["DOTOOL_XKB_LAYOUT"] = self.settings.keyboard
            cmd.append("--simulate-input-tool=DOTOOL")
        cmd.append(f"--vosk-model-dir={location}")
        cmd.append("--output=SIMULATE_INPUT")
        cmd.append("--continuous")
        if os.name != "posix":
            cmd.append("--input-method=pynput")
        logging.debug(
            "Starting nerd-dictation with the command {}".format(" ".join(cmd))
        )
        self.dictate_process = Popen(cmd, env=env)
        self.setIcon(self.micro)
        # A timer to watch the state of the process and update the icon
        self.processWatch = QTimer()
        self.processWatch.timeout.connect(self.watch)
        self.processWatch.start(3000)

    def watch(self):
        poll = self.dictate_process.poll()
        if poll != None and self.dictating:
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
        if reason != QSystemTrayIcon.ActivationReason.Context:
            if self.dictating:
                self.stop_dictate()
                self.dictating = False
            else:
                self.dictating = True
                self.dictate()

    def start(self) -> None:
        logging.debug(f"Start dictation")
        if not self.dictating:
            self.dictating = True
            self.dictate()
        else:
            print("Dictation already started")

    def stop(self) -> None:
        logging.debug(f"Stop dictation")
        if self.dictating:
            self.stop_dictate()
        self.dictating = False

    def config(self) -> None:
        model, _ = self.currentModel()
        dialog = ConfigPopup(os.path.basename(model))
        dialog.exec()
        if dialog.returnValue:
            self.setModel(dialog.returnValue[0])
        self.settings.load()

    def setModel(self, model: str) -> None:
        self.settings.setValue("Model/name", model)
        if self.dictating:
            logging.debug("Reload dictate process")
            self.stop_dictate()
            self.dictate()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Place an icon in systray to launch offline speech recognition."
    )
    parser.add_argument("-l", "--log", help="specify the log level ", dest="loglevel")
    parser.add_argument("-s", "--start", help="launch the dictation directly", action='store_true')
    args = parser.parse_args()
    if args.loglevel is not None:
        numeric_level = getattr(logging, args.loglevel.upper(), None)
    else:
        numeric_level = logging.INFO
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % args.loglevel)
    logging.basicConfig(level=numeric_level)
    app = QApplication(sys.argv)
    # don't close application when closing setting window)
    app.setQuitOnLastWindowClosed(False)
    LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
    locale = QLocale.system().name()
    qtTranslator = QTranslator()
    if qtTranslator.load(
        "qt_" + locale,
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath),
    ):
        app.installTranslator(qtTranslator)
    appTranslator = QTranslator()
    if appTranslator.load("elograf_" + locale, os.path.join(LOCAL_DIR, "translations")):
        app.installTranslator(appTranslator)

    w = QWidget()
    trayIcon = SystemTrayIcon(QIcon(":/icons/elograf/24/nomicro.png"), args.start, w)

    trayIcon.show()
    exit(app.exec())


if __name__ == "__main__":
    main()
