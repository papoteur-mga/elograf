from __future__ import annotations

import logging
import os
import urllib.error
from pathlib import Path
from typing import List, Optional, Tuple

from subprocess import Popen
from zipfile import ZipFile
from PyQt6.QtCore import QCoreApplication, QDir, QSize, Qt, QTimer
from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QKeySequenceEdit,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTableView,
    QVBoxLayout,
)

import eloGraf.advanced as advanced  # type: ignore
import eloGraf.confirm as confirm  # type: ignore
import eloGraf.custom as custom  # type: ignore

from eloGraf.model_repository import (
    MODEL_GLOBAL_PATH,
    MODEL_LIST,
    MODEL_USER_PATH,
    MODELS_URL,
    download_model_archive,
    download_model_list,
    filter_available_models,
    get_size,
    load_model_index,
    model_list_path,
)
from eloGraf.settings import DEFAULT_RATE, Settings
import eloGraf.version as version  # type: ignore


class Models(QStandardItemModel):
    def __init__(self) -> None:
        super().__init__(0, 5)
        headers = [
            self.tr("Language"),
            self.tr("Name"),
            self.tr("Version"),
            self.tr("Size"),
            self.tr("Class"),
        ]
        for index, label in enumerate(headers):
            self.setHeaderData(index, Qt.Orientation.Horizontal, label)


class AdvancedUI(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.ui = advanced.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.timeout.valueChanged.connect(self.timeoutChanged)
        self.ui.idleTime.valueChanged.connect(self.idleChanged)
        self.ui.punctuate.valueChanged.connect(self.punctuateChanged)
        self._add_shortcuts_config()

    def _add_shortcuts_config(self) -> None:
        row_count = self.ui.gridLayout.rowCount()

        label_begin = QLabel(self.tr("Global shortcut: Begin"))
        label_begin.setToolTip(self.tr("Global keyboard shortcut to begin dictation (KDE only)"))
        self.beginShortcut = QKeySequenceEdit()
        self.ui.gridLayout.addWidget(label_begin, row_count, 0)
        self.ui.gridLayout.addWidget(self.beginShortcut, row_count, 1)

        label_end = QLabel(self.tr("Global shortcut: End"))
        label_end.setToolTip(self.tr("Global keyboard shortcut to end dictation (KDE only)"))
        self.endShortcut = QKeySequenceEdit()
        self.ui.gridLayout.addWidget(label_end, row_count + 1, 0)
        self.ui.gridLayout.addWidget(self.endShortcut, row_count + 1, 1)

        label_toggle = QLabel(self.tr("Global shortcut: Toggle"))
        label_toggle.setToolTip(self.tr("Global keyboard shortcut to toggle dictation (KDE only)"))
        self.toggleShortcut = QKeySequenceEdit()
        self.ui.gridLayout.addWidget(label_toggle, row_count + 2, 0)
        self.ui.gridLayout.addWidget(self.toggleShortcut, row_count + 2, 1)

        label_suspend = QLabel(self.tr("Global shortcut: Suspend"))
        label_suspend.setToolTip(self.tr("Global keyboard shortcut to suspend dictation (KDE only)"))
        self.suspendShortcut = QKeySequenceEdit()
        self.ui.gridLayout.addWidget(label_suspend, row_count + 3, 0)
        self.ui.gridLayout.addWidget(self.suspendShortcut, row_count + 3, 1)

        label_resume = QLabel(self.tr("Global shortcut: Resume"))
        label_resume.setToolTip(self.tr("Global keyboard shortcut to resume dictation (KDE only)"))
        self.resumeShortcut = QKeySequenceEdit()
        self.ui.gridLayout.addWidget(label_resume, row_count + 4, 0)
        self.ui.gridLayout.addWidget(self.resumeShortcut, row_count + 4, 1)

        self.ui.gridLayout.removeWidget(self.ui.buttonBox)
        self.ui.gridLayout.addWidget(self.ui.buttonBox, row_count + 5, 1)

    def timeoutChanged(self, num: int) -> None:
        self.ui.timeoutDisplay.setText(str(num))

    def idleChanged(self, num: int) -> None:
        self.ui.idleDisplay.setText(str(num))

    def punctuateChanged(self, num: int) -> None:
        self.ui.punctuateDisplay.setText(str(num))


class ConfirmDownloadUI(QDialog):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.ui = confirm.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.message.setText(text)


class CustomUI(QDialog):
    def __init__(self, index: int, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.ui = custom.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.filePicker.clicked.connect(self.selectCustom)
        self.index = index

    def selectCustom(self) -> None:
        current_path = self.ui.filePicker.text()
        path = current_path if os.path.isdir(current_path) else QDir.homePath()
        new_path = QFileDialog.getExistingDirectory(
            self, self.tr("Select the model path"), path
        )
        if new_path:
            self.ui.filePicker.setText(new_path)
            self.ui.nameLineEdit.setText(os.path.basename(new_path))
            size, unit = get_size(new_path)
            unit = self.tr(unit)
            self.ui.sizeLineEdit.setText(f"{size:.2f} {unit}")

    def accept(self) -> None:
        name = self.ui.nameLineEdit.text()
        language = self.ui.languageLineEdit.text()
        if not language:
            self.ui.languageLineEdit.setStyleSheet("border: 3px solid red")
            QTimer.singleShot(1000, lambda: self.ui.languageLineEdit.setStyleSheet(""))
            return
        if not name:
            self.ui.nameLineEdit.setStyleSheet("border: 3px solid red")
            QTimer.singleShot(1000, lambda: self.ui.nameLineEdit.setStyleSheet(""))
            return
        new_path = self.ui.filePicker.text()
        if os.path.exists(new_path):
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
                model = self.settings.models[self.index]
                model["language"] = language
                model["name"] = name
                model["version"] = self.ui.versionLineEdit.text()
                model["size"] = self.ui.sizeLineEdit.text()
                model["type"] = self.ui.classLineEdit.text()
                model["location"] = new_path
            self.done(self.index)


class DownloadPopup(QDialog):
    def __init__(self, settings: Settings, installed: List[str], parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Elograf")
        self.setWindowIcon(QIcon(":/icons/elograf/24/micro.png"))
        self.list = Models()
        raw_models = load_model_index()
        self.remote_models = filter_available_models(raw_models, installed)
        for model_data in sorted(
            self.remote_models, key=lambda item: item["lang_text"]
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
        layout = QVBoxLayout(self)
        self.table = QTableView()
        self.table.setModel(self.list)
        layout.addWidget(self.table)
        self.table.resizeColumnsToContents()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.bar = QProgressBar()
        self.bar.setMaximum(100)
        self.bar.setMinimum(0)
        layout.addWidget(self.bar)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        system_button = QPushButton(self.tr("Import system wide"))
        button_box.addButton(system_button, QDialogButtonBox.ButtonRole.ActionRole)
        user_button = QPushButton(self.tr("Import in user space"))
        button_box.addButton(user_button, QDialogButtonBox.ButtonRole.ActionRole)
        layout.addWidget(button_box)
        system_button.clicked.connect(self.system)
        user_button.clicked.connect(self.user)
        button_box.rejected.connect(self.close)

    def sizeHint(self) -> QSize:  # type: ignore[override]
        width = sum(self.table.columnWidth(i) for i in range(self.list.columnCount()))
        width += self.table.verticalHeader().sizeHint().width()
        width += self.table.verticalScrollBar().sizeHint().width()
        width += self.table.frameWidth() * 2
        return QSize(width, self.height())

    def user(self) -> None:
        rc, temp_file, name = self.import_model()
        if rc:
            try:
                with ZipFile(temp_file) as archive:
                    archive.extractall(str(MODEL_USER_PATH))
            except Exception:
                logging.warning("Invalid file")
            self.register(str((MODEL_USER_PATH / name)))
            self.done(1)

    def system(self) -> None:
        rc, temp_file, name = self.import_model()
        if rc:
            while not MODEL_GLOBAL_PATH.exists():
                process = Popen(["pkexec", "mkdir", "-p", "-m=777", str(MODEL_GLOBAL_PATH)])
                if process.wait() != 0:
                    retry = ConfirmDownloadUI(
                        self.tr("The application failed to save the model. Do you want to retry?")
                    )
                    if not retry.exec():
                        break
            try:
                with ZipFile(temp_file) as archive:
                    archive.extractall(str(MODEL_GLOBAL_PATH))
                    self.register(str((MODEL_GLOBAL_PATH / name)))
            except Exception:
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
        selection = self.table.selectionModel().selectedRows()
        if not selection:
            logging.warning("No selected model")
            return False, "", ""
        self.name = self.list.data(self.list.index(selection[0].row(), 1))
        size = self.list.data(self.list.index(selection[0].row(), 3))
        confirmation = ConfirmDownloadUI(
            self.tr("We will download the model {} of {} from {}. Do you agree?").format(
                self.name, size, MODELS_URL
            )
        )
        if not confirmation.exec():
            return False, "", ""
        url = next((model["url"] for model in self.remote_models if model["name"] == self.name), "")
        if not url:
            logging.warning("The model has no url provided")
            return False, "", ""
        try:
            temp_file = download_model_archive(url, reporthook=self.progress)
        except urllib.error.URLError:
            logging.warning("Network unavailable or bad URL")
            return False, "", ""
        return True, temp_file, self.name

    def register(self, location: str) -> None:
        existing_names = {model["name"] for model in self.settings.models}
        if self.name not in existing_names:
            selection = self.table.selectionModel().selectedRows()
            if not selection:
                return
            row = selection[0].row()
            self.settings.add_model(
                self.list.data(self.list.index(row, 0)),
                self.name,
                self.list.data(self.list.index(row, 2)),
                self.list.data(self.list.index(row, 3)),
                self.list.data(self.list.index(row, 4)),
                location,
            )


class ConfigPopup(QDialog):
    def __init__(self, current_model: str, parent=None) -> None:
        super().__init__(parent)
        self.settings = Settings()
        self.currentModel = current_model

        self.setWindowTitle("Elograf - " + version.__version__)
        self.setWindowIcon(QIcon(":/icons/elograf/24/micro.png"))
        layout = QVBoxLayout(self)
        model_list_path()
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.table)
        self.settings.load()
        self.list, selected = self.get_list()
        self.table.setModel(self.list)
        if selected is not None:
            self.table.selectRow(selected)
        self.interfaceCB = QCheckBox(self.tr("Active direct click on icon"))
        layout.addWidget(self.interfaceCB)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        remote_button = QPushButton(self.tr("Import remote model"))
        button_box.addButton(remote_button, QDialogButtonBox.ButtonRole.ActionRole)
        local_button = QPushButton(self.tr("Import local model"))
        button_box.addButton(local_button, QDialogButtonBox.ButtonRole.ActionRole)
        advanced_button = QPushButton(self.tr("Advanced"))
        button_box.addButton(advanced_button, QDialogButtonBox.ButtonRole.ActionRole)
        layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.accept)
        advanced_button.clicked.connect(self.advanced)
        local_button.clicked.connect(self.local)
        remote_button.clicked.connect(self.remote)
        self.table.doubleClicked.connect(self.edit)
        self.interfaceCB.clicked.connect(self.interface)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.resizeColumnsToContents()
        self.table.verticalHeader().hide()
        self.button_height = button_box.sizeHint().height()

    def update_list(self, selected: int) -> None:
        self.list, _ = self.get_list()
        self.table.setModel(self.list)
        self.table.resizeColumnsToContents()
        self.list.layoutChanged.emit()
        if selected is not None:
            self.table.selectRow(selected)

    def get_list(self) -> Tuple[Models, Optional[int]]:
        model_list = Models()
        selected_index: Optional[int] = None
        for index, settings_model in enumerate(self.settings.models):
            language_item = QStandardItem(settings_model["language"])
            name_item = QStandardItem(settings_model["name"])
            version_item = QStandardItem(settings_model["version"])
            size_item = QStandardItem(settings_model["size"])
            class_item = QStandardItem(settings_model["type"])
            model_list.appendRow(
                [language_item, name_item, version_item, size_item, class_item]
            )
            if self.currentModel == name_item.text():
                selected_index = index
        return model_list, selected_index

    def interface(self) -> None:
        self.settings.directClick = self.interfaceCB.isChecked()

    @staticmethod
    def _get_ui_attr(ui, *names):
        for name in names:
            if hasattr(ui, name):
                return getattr(ui, name)
        return None

    def accept(self) -> None:  # type: ignore[override]
        selected_indexes = self.table.selectedIndexes()
        model_name = ""
        for index in selected_indexes:
            model_name = self.list.data(self.list.index(index.row(), 1))
        self.settings.save()
        self.returnValue = [model_name]
        self.close()

    def local(self) -> None:
        dialog = CustomUI(-1, self.settings)
        rc = dialog.exec()
        if rc:
            self.update_list(rc - 1)

    def remote(self) -> None:
        index_path = model_list_path()
        if not index_path.exists():
            confirmation = ConfirmDownloadUI(
                self.tr(
                    "We will download the list of models from {}.\nDo you agree?".format(
                        MODELS_URL
                    )
                )
            )
            if confirmation.exec():
                try:
                    download_model_list()
                except urllib.error.URLError:
                    logging.warning("Network unavailable or bad URL")
                    return
            else:
                return
        installed = [model["name"] for model in self.settings.models]
        dialog = DownloadPopup(self.settings, installed)
        if dialog.exec():
            self.update_list(len(self.settings.models) - 1)

    def edit(self) -> None:
        for index in self.table.selectedIndexes():
            for i, model in enumerate(self.settings.models):
                if model["name"] == self.list.data(self.list.index(index.row(), 1)):
                    dialog = CustomUI(i, self.settings)
                    dialog.ui.filePicker.setText(model["location"])
                    dialog.ui.languageLineEdit.setText(model["language"])
                    dialog.ui.nameLineEdit.setText(model["name"])
                    dialog.ui.sizeLineEdit.setText(model["size"])
                    dialog.ui.classLineEdit.setText(model["type"])
                    dialog.ui.versionLineEdit.setText(model["version"])
                    dialog.exec()
                    break
            break
        self.update_list(i)

    def advanced(self) -> None:
        adv_window = AdvancedUI()
        field_precommand = self._get_ui_attr(adv_window.ui, 'precommand', 'preCommand')
        if field_precommand:
            field_precommand.setText(self.settings.precommand)
        field_postcommand = self._get_ui_attr(adv_window.ui, 'postcommand', 'postCommand')
        if field_postcommand:
            field_postcommand.setText(self.settings.postcommand)
        sample_rate_field = self._get_ui_attr(adv_window.ui, "sampleRate", "sample_rate")
        if sample_rate_field:
            sample_rate_field.setText(str(self.settings.sampleRate))
        adv_window.ui.timeout.setValue(self.settings.timeout)
        adv_window.ui.timeoutDisplay.setText(str(self.settings.timeout))
        adv_window.ui.idleTime.setValue(self.settings.idleTime)
        adv_window.ui.idleDisplay.setText(str(self.settings.idleTime))
        adv_window.ui.punctuate.setValue(self.settings.punctuate)
        adv_window.ui.punctuateDisplay.setText(str(self.settings.punctuate))
        adv_window.ui.fullSentence.setChecked(self.settings.fullSentence)
        adv_window.ui.digits.setChecked(self.settings.digits)
        adv_window.ui.useSeparator.setChecked(self.settings.useSeparator)
        direct_click_checkbox = getattr(adv_window.ui, "directClick", None)
        if direct_click_checkbox is not None:
            direct_click_checkbox.setChecked(self.settings.directClick)
        field_freeCommand = self._get_ui_attr(adv_window.ui, 'freecommand', 'freeCommand')
        if field_freeCommand:
            field_freeCommand.setText(self.settings.freeCommand)
        field_env = self._get_ui_attr(adv_window.ui, 'env')
        if field_env:
            field_env.setText(self.settings.env)
        tool_field = self._get_ui_attr(adv_window.ui, "tool", "tool_cb")
        if tool_field and hasattr(tool_field, "setCurrentText"):
            tool_field.setCurrentText(self.settings.tool)
        adv_window.beginShortcut.setKeySequence(self.settings.beginShortcut)
        adv_window.endShortcut.setKeySequence(self.settings.endShortcut)
        adv_window.toggleShortcut.setKeySequence(self.settings.toggleShortcut)
        adv_window.suspendShortcut.setKeySequence(self.settings.suspendShortcut)
        adv_window.resumeShortcut.setKeySequence(self.settings.resumeShortcut)
        if adv_window.exec():
            pre_field = self._get_ui_attr(adv_window.ui, "precommand", "preCommand")
            self.settings.precommand = pre_field.text() if pre_field else ""
            post_field = self._get_ui_attr(adv_window.ui, "postcommand", "postCommand")
            self.settings.postcommand = post_field.text() if post_field else ""
            sample_rate_field = self._get_ui_attr(adv_window.ui, "sampleRate", "sample_rate")
            try:
                self.settings.sampleRate = int(sample_rate_field.text()) if sample_rate_field else DEFAULT_RATE
            except (ValueError, TypeError):
                self.settings.sampleRate = DEFAULT_RATE
            self.settings.timeout = adv_window.ui.timeout.value()
            self.settings.idleTime = adv_window.ui.idleTime.value()
            self.settings.punctuate = adv_window.ui.punctuate.value()
            self.settings.fullSentence = adv_window.ui.fullSentence.isChecked()
            self.settings.digits = adv_window.ui.digits.isChecked()
            self.settings.useSeparator = adv_window.ui.useSeparator.isChecked()
            direct_click_checkbox = getattr(adv_window.ui, "directClick", None)
            if direct_click_checkbox is not None:
                self.settings.directClick = direct_click_checkbox.isChecked()
            free_field = self._get_ui_attr(adv_window.ui, "freecommand", "freeCommand")
            self.settings.freeCommand = free_field.text() if free_field else ""
            env_field = self._get_ui_attr(adv_window.ui, "env")
            self.settings.env = env_field.text() if env_field else ""
            device_field = self._get_ui_attr(adv_window.ui, "deviceName", "device_name")
            if device_field and hasattr(device_field, "currentText"):
                self.settings.deviceName = device_field.currentText()
            elif device_field and hasattr(device_field, "text"):
                self.settings.deviceName = device_field.text()
            else:
                self.settings.deviceName = ""
            tool_field = self._get_ui_attr(adv_window.ui, "tool", "tool_cb")
            if tool_field and hasattr(tool_field, "currentText"):
                self.settings.tool = tool_field.currentText()
            else:
                self.settings.tool = ""
            self.settings.beginShortcut = adv_window.beginShortcut.keySequence().toString()
            self.settings.endShortcut = adv_window.endShortcut.keySequence().toString()
            self.settings.toggleShortcut = adv_window.toggleShortcut.keySequence().toString()
            self.settings.suspendShortcut = adv_window.suspendShortcut.keySequence().toString()
            self.settings.resumeShortcut = adv_window.resumeShortcut.keySequence().toString()
            self.settings.save()

    def setModel(self, model: str) -> None:
        self.settings.setValue("Model/name", model)
        self.settings.save()
