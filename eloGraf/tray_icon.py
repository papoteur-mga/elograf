from __future__ import annotations

import logging
import os
from subprocess import Popen

from PyQt6.QtCore import QCoreApplication, QTimer
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from eloGraf.dialogs import ConfigPopup
from eloGraf.dictation import CommandBuildError, build_dictation_command
from eloGraf.nerd_controller import (
    NerdDictationController,
    NerdDictationProcessRunner,
    NerdDictationState,
)
from eloGraf.settings import DEFAULT_RATE, Settings
from eloGraf.pidfile import remove_pid_file

class SystemTrayIcon(QSystemTrayIcon):
    """Tray icon controller with model-aware tooltip."""

    def _update_tooltip(self) -> None:
        name, _ = self.currentModel()
        tooltip = "EloGraf"
        if name:
            tooltip += f"\nModel: {name}"
        self.setToolTip(tooltip)

    def __init__(self, icon: QIcon, start: bool, ipc: IPCManager, parent=None) -> None:
        QSystemTrayIcon.__init__(self, icon, parent)
        self.settings = Settings()
        try:
            self.settings.load()
        except Exception as exc:
            logging.warning("Failed to load settings: %s", exc)
        self.ipc = ipc

        menu = QMenu(parent)
        # single left click doesn't work in some environments. https://bugreports.qt.io/browse/QTBUG-55911
        # Thus by default we don't enable it, but add Start/Stop menu entries
        if not self.settings.directClick:
            startAction = menu.addAction(self.tr("Start dictation"))
            stopAction = menu.addAction(self.tr("Stop dictation"))
            startAction.triggered.connect(self.begin)
            stopAction.triggered.connect(self.end)
        self.toggleAction = menu.addAction(self.tr("Toggle dictation"))
        self.suspendAction = menu.addAction(self.tr("Suspend dictation"))
        self.resumeAction = menu.addAction(self.tr("Resume dictation"))
        self.toggleAction.triggered.connect(self.toggle)
        self.suspendAction.triggered.connect(self.suspend)
        self.resumeAction.triggered.connect(self.resume)
        self.toggleAction.setEnabled(True)
        self.suspendAction.setEnabled(False)
        self.resumeAction.setEnabled(False)
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
        self.dictation_controller = NerdDictationController()
        self.dictation_controller.add_state_listener(self._handle_dictation_state)
        self.dictation_controller.add_output_listener(self._handle_dictation_output)
        self.dictation_controller.add_exit_listener(self._handle_dictation_exit)
        self.dictation_runner = NerdDictationProcessRunner(self.dictation_controller)
        self.dictation_timer = QTimer(self)
        self.dictation_timer.setInterval(200)
        self.dictation_timer.timeout.connect(self.dictation_runner.poll)
        self.dictating = False
        self.suspended = False
        self._postcommand_ran = True
        self._update_action_states()
        self._update_tooltip()
        self.activated.connect(lambda r: self.commute(r))
        self.start_cli = start
        self._update_tooltip()

        # Connect IPC command handler
        self.ipc.command_received.connect(self._handle_ipc_command)

        # Start IPC server
        if not self.ipc.start_server():
            logging.error("Failed to start IPC server")

        # Register global shortcuts if supported
        self._register_global_shortcuts()

        if start:
            self.dictate()
            self.dictating = True

    def _get_loading_icon(self):
        """Get microphone icon with red loading indicator"""
        from PyQt6.QtGui import QPixmap, QPainter, QColor
        from PyQt6.QtCore import Qt

        # Get base icon as pixmap
        pixmap = self.micro.pixmap(24, 24)
        painter = QPainter(pixmap)

        # Draw red line at bottom
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 0, 0))  # Red
        painter.drawRect(0, 22, 24, 2)  # 2px red line at bottom

        painter.end()
        return QIcon(pixmap)

    def _get_ready_icon(self):
        """Get microphone icon with green ready indicator"""
        from PyQt6.QtGui import QPixmap, QPainter, QColor
        from PyQt6.QtCore import Qt

        # Get base icon as pixmap
        pixmap = self.micro.pixmap(24, 24)
        painter = QPainter(pixmap)

        # Draw green line at bottom
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 255, 0))  # Green
        painter.drawRect(0, 22, 24, 2)  # 2px green line at bottom

        painter.end()
        return QIcon(pixmap)

    def _get_suspended_icon(self):
        """Get microphone icon with orange suspended indicator"""
        from PyQt6.QtGui import QPixmap, QPainter, QColor
        from PyQt6.QtCore import Qt

        pixmap = self.micro.pixmap(24, 24)
        painter = QPainter(pixmap)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 165, 0))
        painter.drawRect(0, 22, 24, 2)

        painter.end()
        return QIcon(pixmap)

    def _handle_dictation_state(self, state: NerdDictationState) -> None:
        running_states = {
            NerdDictationState.STARTING,
            NerdDictationState.LOADING,
            NerdDictationState.READY,
            NerdDictationState.DICTATING,
            NerdDictationState.SUSPENDED,
        }
        self.dictating = state in running_states
        self.suspended = state == NerdDictationState.SUSPENDED

        if state in (NerdDictationState.STARTING, NerdDictationState.LOADING):
            self.setIcon(self._get_loading_icon())
        elif state in (NerdDictationState.READY, NerdDictationState.DICTATING):
            self.setIcon(self._get_ready_icon())
        elif state == NerdDictationState.SUSPENDED:
            self.setIcon(self._get_suspended_icon())
        elif state in (NerdDictationState.STOPPING, NerdDictationState.IDLE, NerdDictationState.FAILED):
            self.setIcon(self.nomicro)

        if state == NerdDictationState.FAILED:
            logging.error("nerd-dictation process failed")

        self._update_action_states()

    def _handle_dictation_output(self, line: str) -> None:
        logging.info(f"nerd-dictation: {line}")

    def _handle_dictation_exit(self, return_code: int) -> None:
        if return_code != 0:
            logging.warning(f"nerd-dictation exited with code {return_code}")
        if self.dictation_timer.isActive():
            self.dictation_timer.stop()
        self.dictating = False
        self.suspended = False
        self._update_action_states()
        self._update_tooltip()
        self._run_postcommand_once()
        if self.start_cli:
            QCoreApplication.exit()

    def _run_postcommand_once(self) -> None:
        if self._postcommand_ran:
            return

        if hasattr(self.settings, "postcommand") and self.settings.postcommand:
            try:
                Popen(self.settings.postcommand.split())
            except Exception as exc:
                logging.error("Failed to run postcommand: %s", exc)

        self._postcommand_ran = True

    def _update_action_states(self) -> None:
        if hasattr(self, "toggleAction"):
            if self.suspended:
                label = self.tr("Resume dictation")
            elif self.dictation_runner.is_running() or self.dictating:
                label = self.tr("Suspend dictation")
            else:
                label = self.tr("Start dictation")
            self.toggleAction.setText(label)
        if hasattr(self, "suspendAction"):
            self.suspendAction.setEnabled(self.dictation_runner.is_running() and not self.suspended)
        if hasattr(self, "resumeAction"):
            self.resumeAction.setEnabled(self.suspended)

    def _register_global_shortcuts(self):
        """Register global keyboard shortcuts if IPC supports it"""
        if not self.ipc.supports_global_shortcuts():
            logging.debug("IPC does not support global shortcuts")
            return

        # Register begin shortcut
        if self.settings.beginShortcut:
            success = self.ipc.register_global_shortcut(
                "begin",
                self.settings.beginShortcut,
                self.begin
            )
            if success:
                logging.info(f"Global shortcut registered: {self.settings.beginShortcut} -> begin")
            else:
                logging.warning(f"Failed to register global shortcut for 'begin'")

        # Register end shortcut
        if self.settings.endShortcut:
            success = self.ipc.register_global_shortcut(
                "end",
                self.settings.endShortcut,
                self.end
            )
            if success:
                logging.info(f"Global shortcut registered: {self.settings.endShortcut} -> end")
            else:
                logging.warning(f"Failed to register global shortcut for 'end'")

        if self.settings.toggleShortcut:
            success = self.ipc.register_global_shortcut(
                "toggle",
                self.settings.toggleShortcut,
                self.toggle
            )
            if success:
                logging.info(f"Global shortcut registered: {self.settings.toggleShortcut} -> toggle")
            else:
                logging.warning("Failed to register global shortcut for 'toggle'")

        if self.settings.suspendShortcut:
            success = self.ipc.register_global_shortcut(
                "suspend",
                self.settings.suspendShortcut,
                self.suspend
            )
            if success:
                logging.info(f"Global shortcut registered: {self.settings.suspendShortcut} -> suspend")
            else:
                logging.warning("Failed to register global shortcut for 'suspend'")

        if self.settings.resumeShortcut:
            success = self.ipc.register_global_shortcut(
                "resume",
                self.settings.resumeShortcut,
                self.resume
            )
            if success:
                logging.info(f"Global shortcut registered: {self.settings.resumeShortcut} -> resume")
            else:
                logging.warning("Failed to register global shortcut for 'resume'")

    def _handle_ipc_command(self, command: str):
        """
        Handle commands received from other instances via IPC.

        Args:
            command: Command string (e.g., "begin", "end", "exit")
        """
        logging.info(f"Received IPC command: {command}")
        if command == "begin":
            self.begin()
        elif command == "end":
            self.end()
        elif command == "exit":
            self.exit()
        elif command == "suspend":
            self.suspend()
        elif command == "resume":
            self.resume()
        elif command == "toggle":
            self.toggle()
        else:
            logging.warning(f"Unknown IPC command: {command}")

    def currentModel(self) -> Tuple[str, str]:
        """Return currently selected model name and its path, if available."""
        try:
            self.settings.load()
        except Exception as exc:
            logging.warning("Failed to load settings: %s", exc)
        model = ""
        location = ""
        if self.settings.contains("Model/name"):
            model = self.settings.value("Model/name")
            for entry in self.settings.models:
                if entry.get("name") == model:
                    location = entry.get("location", "")
                    break
        if not location:
            for entry in self.settings.models:
                loc = entry.get("location", "")
                if loc:
                    model = entry.get("name", model)
                    location = loc
                    break
        return model, location

    def exit(self) -> None:
        """Clean exit: stop dictation, cleanup IPC, and exit"""
        logging.info("Exiting Elograf...")
        if self.dictating:
            self.stop_dictate()
        # Cleanup resources
        remove_pid_file()
        self.ipc.cleanup()
        QCoreApplication.exit()

    def dictate(self) -> None:
        model, location = self.currentModel()
        if model == "" or not location:
            dialog = ConfigPopup(os.path.basename(model) if model else "")
            if dialog.exec() and dialog.returnValue and dialog.returnValue[0]:
                self.settings.setValue("Model/name", dialog.returnValue[0])
                self.settings.save()
                model, location = self.currentModel()
            else:
                logging.info("No model selected")
                self.dictating = False
                self.suspended = False
                self._update_action_states()
                return
        if not location:
            logging.warning("Selected model has no location configured")
            self.dictating = False
            self.suspended = False
            self._update_action_states()
            self._update_tooltip()
            return
        logging.debug(f"Start dictation with model {model} located in {location}")
        if self.settings.precommand:
            parts = self.settings.precommand.split()
            if parts:
                Popen(parts)
        self._postcommand_ran = False
        try:
            cmd, env = build_dictation_command(self.settings, location)
        except CommandBuildError as exc:
            logging.warning("Failed to build nerd-dictation command: %s", exc)
            self.dictating = False
            self.setIcon(self.nomicro)
            self._postcommand_ran = True
            return
        logging.debug(
            "Starting nerd-dictation with the command {}".format(" ".join(cmd))
        )
        if not self.dictation_runner.start(cmd, env=env):
            self.dictating = False
            self.suspended = False
            self.setIcon(self.nomicro)
            self._postcommand_ran = True
            self._update_action_states()
            self._update_tooltip()
            return

        if not self.dictation_timer.isActive():
            self.dictation_timer.start()
        self._update_tooltip()
        logging.info("Loading model, please wait...")

    def toggle(self) -> None:
        """Toggle dictation: start if idle, suspend if running, resume if suspended."""
        if self.suspended:
            self.resume()
        elif self.dictation_runner.is_running() or self.dictating:
            self.suspend()
        else:
            self.begin()

    def suspend(self) -> None:
        logging.debug("Suspend dictation")
        if self.suspended:
            logging.info("Dictation already suspended")
            return
        if self.dictation_runner.is_running():
            self.dictation_runner.suspend()
            self.suspended = True
            self._update_action_states()
            self._update_tooltip()
        else:
            logging.info("No running dictation to suspend")

    def resume(self) -> None:
        logging.debug("Resume dictation")
        if not self.dictation_runner.is_running():
            logging.info("No dictation process to resume; starting a new one")
            self.suspended = False
            self.dictating = True
            self.dictate()
            return
        self.dictation_runner.resume()
        self.dictating = True
        self.suspended = False
        self._update_action_states()
        self._update_tooltip()
        self._update_tooltip()

    def stop_dictate(self) -> None:
        if self.dictation_runner.is_running():
            logging.debug("Stopping nerd-dictation")
            self.dictation_runner.stop()
        self.dictating = False
        self.suspended = False
        self._update_action_states()
        self._update_tooltip()

    def commute(self, reason) -> None:
        logging.debug(f"Commute dictation {'off' if self.dictating else 'on'}")
        if reason == QSystemTrayIcon.ActivationReason.Context:
            return
        if self.suspended:
            self.resume()
        elif self.dictating:
            self.suspend()
        else:
            self.begin()

    def begin(self) -> None:
        """Start dictation (renamed from 'start' to match nerd-dictation)"""
        logging.debug("Begin dictation")
        if self.suspended:
            self.resume()
            return
        if not self.dictating:
            self.dictating = True
            self.dictate()
        else:
            logging.info("Dictation already started")

    def end(self) -> None:
        """Stop dictation (renamed from 'stop' to match nerd-dictation)"""
        logging.debug("End dictation")
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
        if model == "":
            for entry in self.settings.models:
                if entry.get("location"):
                    model = entry.get("name", "")
                    location = entry.get("location", "")
                    break

    def setModel(self, model: str) -> None:
        self.settings.setValue("Model/name", model)
        if self.dictating:
            logging.debug("Reload dictate process")
            self.stop_dictate()
            self.dictate()

